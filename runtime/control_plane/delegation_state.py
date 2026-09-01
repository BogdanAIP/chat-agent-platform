from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ._verified_workspace_artifact_support import _acquire_task_lock, _safe_child


STATE_SCHEMA_VERSION = 1
GENESIS_KIND = "agent-delegation-genesis"
STATE_KIND = "agent-delegation-state"
STATE_DIRECTORY = "agent-delegation-v1"
WORKER_PROFILE = "fresh_readonly_worker_v1"
MAX_GENESIS_BYTES = 32_768
MAX_STATE_BYTES = 2_000_000
MAX_RESULT_BYTES = 256_000
MAX_SESSION_VALUE_CHARS = 1024
MAX_EVIDENCE_REF_CHARS = 2048

_HEX32_RE = re.compile(r"^[0-9a-f]{32}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_KIND_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_ALLOWED_LAUNCH_STATE = {"prepared", "launch-attempted", "child-bound"}
_ALLOWED_DELIVERY_STATE = {"prepared", "claimed", "delivered", "unknown"}
_ALLOWED_RESULT_STATE = {"open", "recorded"}
_ALLOWED_RESULT_STATUS = {"COMPLETED", "ABSTAIN", "ERROR"}

_IDENTITY_KEYS = {
    "parent_task_id",
    "subgoal_id",
    "worker_kind",
    "worker_profile",
    "task_sha256",
    "result_contract_id",
}
_SESSION_KEYS = {
    "adapter_id",
    "session_id",
    "conversation_id",
    "ownership",
    "observation_ref",
}
_RESULT_KEYS = {
    "schema_version",
    "delegation_id",
    "delivery_id",
    "worker_kind",
    "result_contract_id",
    "status",
    "payload",
    "payload_sha256",
}


class DelegationStateError(ValueError):
    pass


@dataclass(frozen=True)
class DelegationIdentity:
    parent_task_id: str
    subgoal_id: str
    worker_kind: str
    worker_profile: str
    task_sha256: str
    result_contract_id: str

    def as_dict(self) -> dict[str, str]:
        return {
            "parent_task_id": self.parent_task_id,
            "subgoal_id": self.subgoal_id,
            "worker_kind": self.worker_kind,
            "worker_profile": self.worker_profile,
            "task_sha256": self.task_sha256,
            "result_contract_id": self.result_contract_id,
        }


@dataclass(frozen=True)
class WorkerSessionRef:
    adapter_id: str
    session_id: str
    conversation_id: str | None
    ownership: str
    observation_ref: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "ownership": self.ownership,
            "observation_ref": self.observation_ref,
        }


@dataclass(frozen=True)
class PreparedDelegation:
    """Trusted Control Plane view. `run_id` is a private local capability."""

    identity: DelegationIdentity
    delegation_id: str
    delivery_id: str
    run_id: str = field(repr=False)
    launch_state: str = "prepared"
    delivery_state: str = "prepared"
    result_state: str = "open"
    created: bool = False


@dataclass(frozen=True)
class DeliveryClaim:
    delegation_id: str
    delivery_id: str
    claimed_now: bool
    delivery_state: str


@dataclass(frozen=True)
class DelegationSnapshot:
    identity: DelegationIdentity
    delegation_id: str
    delivery_id: str
    launch_state: str
    worker_session_ref: WorkerSessionRef | None
    delivery_state: str
    delivery_evidence_ref: str | None
    result_state: str
    result_status: str | None
    result_payload: str | None
    result_sha256: str | None


@dataclass(frozen=True)
class ParsedWorkerResult:
    delegation_id: str
    delivery_id: str
    worker_kind: str
    result_contract_id: str
    status: str
    payload: str
    payload_sha256: str



def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_plain_object(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise DelegationStateError(f"{label} must be a plain object")
    return value


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise DelegationStateError(
            f"{label} keys mismatch: missing={sorted(expected - actual) or 'none'} "
            f"unexpected={sorted(actual - expected) or 'none'}"
        )


def _bounded_identifier(value: Any, label: str) -> str:
    if type(value) is not str or _IDENTIFIER_RE.fullmatch(value) is None:
        raise DelegationStateError(f"{label} must be a bounded identifier")
    return value


def _bounded_kind(value: Any, label: str) -> str:
    if type(value) is not str or _KIND_RE.fullmatch(value) is None:
        raise DelegationStateError(f"{label} must be a bounded lowercase identifier")
    return value


def _hex64(value: Any, label: str) -> str:
    if type(value) is not str or _HEX64_RE.fullmatch(value) is None:
        raise DelegationStateError(f"{label} must be 64 lowercase hex characters")
    return value


def _bounded_text(value: Any, label: str, *, maximum: int, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str or not value or len(value) > maximum:
        raise DelegationStateError(f"{label} must be bounded non-empty text")
    return value


def _timestamp(value: Any, label: str) -> str:
    if type(value) is not str or not value or len(value) > 128:
        raise DelegationStateError(f"{label} must be a bounded ISO-8601 timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise DelegationStateError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise DelegationStateError(f"{label} must include a timezone")
    return value


def parse_delegation_identity(value: Mapping[str, Any]) -> DelegationIdentity:
    value = _require_plain_object(value, "delegation identity")
    _require_exact_keys(value, _IDENTITY_KEYS, "delegation identity")
    parent_task_id = _bounded_identifier(value["parent_task_id"], "parent_task_id")
    subgoal_id = _bounded_identifier(value["subgoal_id"], "subgoal_id")
    worker_kind = _bounded_kind(value["worker_kind"], "worker_kind")
    worker_profile = value["worker_profile"]
    if worker_profile != WORKER_PROFILE:
        raise DelegationStateError(f"worker_profile must be {WORKER_PROFILE}")
    task_sha256 = _hex64(value["task_sha256"], "task_sha256")
    result_contract_id = _bounded_kind(value["result_contract_id"], "result_contract_id")
    return DelegationIdentity(
        parent_task_id=parent_task_id,
        subgoal_id=subgoal_id,
        worker_kind=worker_kind,
        worker_profile=worker_profile,
        task_sha256=task_sha256,
        result_contract_id=result_contract_id,
    )


def delegation_operation_key(identity: DelegationIdentity) -> str:
    canonical = json.dumps(identity.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(("cap-agent-delegation-v1\0" + canonical).encode("ascii")).hexdigest()


def _lock_id(delegation_id: str) -> str:
    _hex64(delegation_id, "delegation_id")
    return delegation_id[:32]


def parse_worker_session_ref(value: Mapping[str, Any]) -> WorkerSessionRef:
    value = _require_plain_object(value, "worker session ref")
    _require_exact_keys(value, _SESSION_KEYS, "worker session ref")
    adapter_id = _bounded_kind(value["adapter_id"], "adapter_id")
    session_id = _bounded_text(
        value["session_id"], "session_id", maximum=MAX_SESSION_VALUE_CHARS
    )
    conversation_id = _bounded_text(
        value["conversation_id"],
        "conversation_id",
        maximum=MAX_SESSION_VALUE_CHARS,
        nullable=True,
    )
    if value["ownership"] != "manager_owned":
        raise DelegationStateError("first worker session ownership must be manager_owned")
    observation_ref = _bounded_text(
        value["observation_ref"],
        "observation_ref",
        maximum=MAX_EVIDENCE_REF_CHARS,
    )
    assert isinstance(session_id, str)
    assert isinstance(observation_ref, str)
    return WorkerSessionRef(
        adapter_id=adapter_id,
        session_id=session_id,
        conversation_id=conversation_id,
        ownership="manager_owned",
        observation_ref=observation_ref,
    )


def parse_worker_result(
    value: Mapping[str, Any],
    *,
    identity: DelegationIdentity,
    delegation_id: str,
    delivery_id: str,
) -> ParsedWorkerResult:
    value = _require_plain_object(value, "worker result")
    _require_exact_keys(value, _RESULT_KEYS, "worker result")
    if value["schema_version"] != 1:
        raise DelegationStateError("worker result schema mismatch")
    if value["delegation_id"] != delegation_id:
        raise DelegationStateError("worker result delegation_id mismatch")
    if value["delivery_id"] != delivery_id:
        raise DelegationStateError("worker result delivery_id mismatch")
    if value["worker_kind"] != identity.worker_kind:
        raise DelegationStateError("worker result worker_kind mismatch")
    if value["result_contract_id"] != identity.result_contract_id:
        raise DelegationStateError("worker result contract mismatch")
    status = value["status"]
    if status not in _ALLOWED_RESULT_STATUS:
        raise DelegationStateError("worker result status is invalid")
    payload = value["payload"]
    if type(payload) is not str or not payload:
        raise DelegationStateError("worker result payload must be non-empty text")
    encoded = payload.encode("utf-8")
    if len(encoded) > MAX_RESULT_BYTES:
        raise DelegationStateError("worker result payload exceeds accepted bound")
    digest = _hex64(value["payload_sha256"], "payload_sha256")
    if hashlib.sha256(encoded).hexdigest() != digest:
        raise DelegationStateError("worker result payload digest mismatch")
    return ParsedWorkerResult(
        delegation_id=delegation_id,
        delivery_id=delivery_id,
        worker_kind=identity.worker_kind,
        result_contract_id=identity.result_contract_id,
        status=status,
        payload=payload,
        payload_sha256=digest,
    )


def _root(state_root: Path) -> Path:
    configured = state_root.resolve()
    root = _safe_child(configured, configured / STATE_DIRECTORY)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _genesis_path(root: Path, delegation_id: str) -> Path:
    return _safe_child(root, root / f"{delegation_id}.genesis.json")


def _state_path(root: Path, delegation_id: str) -> Path:
    return _safe_child(root, root / f"{delegation_id}.state.json")


def _temp_paths(root: Path, delegation_id: str) -> tuple[Path, ...]:
    prefix = f".{delegation_id}.state."
    return tuple(
        sorted(
            (
                candidate
                for candidate in root.iterdir()
                if candidate.name.startswith(prefix) and candidate.name.endswith(".tmp")
            ),
            key=lambda path: path.name,
        )
    )


def _encode_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _exclusive_create(path: Path, payload: bytes) -> None:
    if len(payload) > MAX_GENESIS_BYTES:
        raise DelegationStateError("delegation genesis exceeds accepted bound")
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _write_state(root: Path, delegation_id: str, state: Mapping[str, Any]) -> None:
    payload = _encode_json(state)
    if len(payload) > MAX_STATE_BYTES:
        raise DelegationStateError("delegation state exceeds accepted bound")
    destination = _state_path(root, delegation_id)
    temporary = _safe_child(
        root,
        root / f".{delegation_id}.state.{secrets.token_hex(8)}.tmp",
    )
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _load_json(path: Path, label: str, *, maximum: int) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            raw = handle.read(maximum + 1)
    except FileNotFoundError as exc:
        raise DelegationStateError(f"{label} does not exist") from exc
    if len(raw) > maximum:
        raise DelegationStateError(f"{label} exceeds accepted bound")
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise DelegationStateError(f"{label} is invalid") from exc
    return _require_plain_object(value, label)


def _build_genesis(
    identity: DelegationIdentity,
    delegation_id: str,
    run_id: str,
    delivery_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "kind": GENESIS_KIND,
        "delegation_id": delegation_id,
        "identity": identity.as_dict(),
        "run_id": run_id,
        "delivery_id": delivery_id,
        "created_at": _utc_now(),
    }


def _build_initial_state(
    identity: DelegationIdentity,
    delegation_id: str,
    run_id: str,
    delivery_id: str,
) -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "kind": STATE_KIND,
        "delegation_id": delegation_id,
        "identity": identity.as_dict(),
        "run_id": run_id,
        "delivery_id": delivery_id,
        "revision": 1,
        "launch_state": "prepared",
        "worker_session_ref": None,
        "delivery_state": "prepared",
        "delivery_evidence_ref": None,
        "result_state": "open",
        "result_status": None,
        "result_payload": None,
        "result_sha256": None,
        "result_recorded_at": None,
        "created_at": now,
        "updated_at": now,
    }


def _validate_genesis(
    value: Mapping[str, Any], identity: DelegationIdentity, delegation_id: str
) -> tuple[str, str]:
    expected = {
        "schema_version",
        "kind",
        "delegation_id",
        "identity",
        "run_id",
        "delivery_id",
        "created_at",
    }
    _require_exact_keys(value, expected, "delegation genesis")
    if value["schema_version"] != STATE_SCHEMA_VERSION or value["kind"] != GENESIS_KIND:
        raise DelegationStateError("delegation genesis schema mismatch")
    if value["delegation_id"] != delegation_id:
        raise DelegationStateError("delegation genesis id mismatch")
    if parse_delegation_identity(value["identity"]) != identity:
        raise DelegationStateError("delegation genesis identity mismatch")
    run_id = _hex64(value["run_id"], "run_id")
    delivery_id = _hex64(value["delivery_id"], "delivery_id")
    _timestamp(value["created_at"], "genesis.created_at")
    return run_id, delivery_id


def _validate_state(
    value: Mapping[str, Any],
    identity: DelegationIdentity,
    delegation_id: str,
    run_id: str,
    delivery_id: str,
) -> None:
    expected = {
        "schema_version",
        "kind",
        "delegation_id",
        "identity",
        "run_id",
        "delivery_id",
        "revision",
        "launch_state",
        "worker_session_ref",
        "delivery_state",
        "delivery_evidence_ref",
        "result_state",
        "result_status",
        "result_payload",
        "result_sha256",
        "result_recorded_at",
        "created_at",
        "updated_at",
    }
    _require_exact_keys(value, expected, "delegation state")
    if value["schema_version"] != STATE_SCHEMA_VERSION or value["kind"] != STATE_KIND:
        raise DelegationStateError("delegation state schema mismatch")
    if value["delegation_id"] != delegation_id:
        raise DelegationStateError("delegation state id mismatch")
    if parse_delegation_identity(value["identity"]) != identity:
        raise DelegationStateError("delegation state identity mismatch")
    if _hex64(value["run_id"], "state.run_id") != run_id:
        raise DelegationStateError("delegation state run capability mismatch")
    if _hex64(value["delivery_id"], "state.delivery_id") != delivery_id:
        raise DelegationStateError("delegation state delivery id mismatch")
    if type(value["revision"]) is not int or value["revision"] < 1:
        raise DelegationStateError("delegation state revision is invalid")
    launch_state = value["launch_state"]
    delivery_state = value["delivery_state"]
    result_state = value["result_state"]
    if launch_state not in _ALLOWED_LAUNCH_STATE:
        raise DelegationStateError("delegation launch state is invalid")
    if delivery_state not in _ALLOWED_DELIVERY_STATE:
        raise DelegationStateError("delegation delivery state is invalid")
    if result_state not in _ALLOWED_RESULT_STATE:
        raise DelegationStateError("delegation result state is invalid")
    _timestamp(value["created_at"], "state.created_at")
    _timestamp(value["updated_at"], "state.updated_at")

    session_value = value["worker_session_ref"]
    session_ref = None if session_value is None else parse_worker_session_ref(session_value)
    if launch_state == "child-bound":
        if session_ref is None:
            raise DelegationStateError("child-bound state requires worker session ref")
    elif session_ref is not None:
        raise DelegationStateError("unbound launch state cannot contain worker session ref")

    evidence_ref = value["delivery_evidence_ref"]
    if delivery_state == "prepared":
        if launch_state != "child-bound" and evidence_ref is not None:
            raise DelegationStateError("prepared delivery cannot contain evidence")
        if evidence_ref is not None:
            raise DelegationStateError("prepared delivery cannot contain evidence")
    elif delivery_state == "claimed":
        if launch_state != "child-bound":
            raise DelegationStateError("claimed delivery requires bound child")
        if evidence_ref is not None:
            raise DelegationStateError("claimed delivery cannot contain outcome evidence")
    else:
        if launch_state != "child-bound":
            raise DelegationStateError("delivery outcome requires bound child")
        _bounded_text(
            evidence_ref,
            "delivery_evidence_ref",
            maximum=MAX_EVIDENCE_REF_CHARS,
        )

    if result_state == "open":
        if any(
            value[key] is not None
            for key in ("result_status", "result_payload", "result_sha256", "result_recorded_at")
        ):
            raise DelegationStateError("open delegation cannot contain terminal result evidence")
        return

    if delivery_state != "delivered":
        raise DelegationStateError("terminal worker result requires delivered task")
    if value["result_status"] not in _ALLOWED_RESULT_STATUS:
        raise DelegationStateError("recorded worker result status is invalid")
    payload = value["result_payload"]
    if type(payload) is not str or not payload:
        raise DelegationStateError("recorded worker result payload is invalid")
    encoded = payload.encode("utf-8")
    if len(encoded) > MAX_RESULT_BYTES:
        raise DelegationStateError("recorded worker result exceeds accepted bound")
    digest = _hex64(value["result_sha256"], "result_sha256")
    if hashlib.sha256(encoded).hexdigest() != digest:
        raise DelegationStateError("recorded worker result digest mismatch")
    _timestamp(value["result_recorded_at"], "state.result_recorded_at")


def _load_operation(
    root: Path, identity: DelegationIdentity, delegation_id: str
) -> tuple[str, str, dict[str, Any]]:
    genesis = _load_json(
        _genesis_path(root, delegation_id),
        "delegation genesis",
        maximum=MAX_GENESIS_BYTES,
    )
    run_id, delivery_id = _validate_genesis(genesis, identity, delegation_id)
    state = _load_json(
        _state_path(root, delegation_id),
        "delegation state",
        maximum=MAX_STATE_BYTES,
    )
    _validate_state(state, identity, delegation_id, run_id, delivery_id)
    return run_id, delivery_id, state


def _present(root: Path, delegation_id: str) -> tuple[bool, bool, tuple[Path, ...]]:
    return (
        _genesis_path(root, delegation_id).exists(),
        _state_path(root, delegation_id).exists(),
        _temp_paths(root, delegation_id),
    )


def _bump(state: dict[str, Any]) -> None:
    state["revision"] += 1
    state["updated_at"] = _utc_now()


def _require_run_id(actual: str, supplied: str) -> None:
    if _hex64(supplied, "run_id") != actual:
        raise DelegationStateError("delegation run capability mismatch")


def _snapshot(identity: DelegationIdentity, state: Mapping[str, Any]) -> DelegationSnapshot:
    session_value = state["worker_session_ref"]
    session_ref = None if session_value is None else parse_worker_session_ref(session_value)
    return DelegationSnapshot(
        identity=identity,
        delegation_id=state["delegation_id"],
        delivery_id=state["delivery_id"],
        launch_state=state["launch_state"],
        worker_session_ref=session_ref,
        delivery_state=state["delivery_state"],
        delivery_evidence_ref=state["delivery_evidence_ref"],
        result_state=state["result_state"],
        result_status=state["result_status"],
        result_payload=state["result_payload"],
        result_sha256=state["result_sha256"],
    )


def prepare_delegation(
    identity_value: Mapping[str, Any], *, state_root: Path
) -> PreparedDelegation:
    identity = parse_delegation_identity(identity_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        genesis_exists, state_exists, residues = _present(root, delegation_id)
        if not genesis_exists and not state_exists:
            if residues:
                raise DelegationStateError("delegation residue exists without canonical state")
            run_id = secrets.token_hex(32)
            delivery_id = secrets.token_hex(32)
            _exclusive_create(
                _genesis_path(root, delegation_id),
                _encode_json(_build_genesis(identity, delegation_id, run_id, delivery_id)),
            )
            persisted_run, persisted_delivery, _ = _load_operation_after_genesis(
                root, identity, delegation_id, run_id, delivery_id
            )
            return PreparedDelegation(
                identity=identity,
                delegation_id=delegation_id,
                delivery_id=persisted_delivery,
                run_id=persisted_run,
                created=True,
            )
        if not genesis_exists:
            raise DelegationStateError("delegation state exists without immutable genesis")
        if not state_exists:
            raise DelegationStateError("delegation genesis exists without mutable state")
        if residues:
            raise DelegationStateError("delegation has ambiguous temporary state residue")
        run_id, delivery_id, state = _load_operation(root, identity, delegation_id)
        return PreparedDelegation(
            identity=identity,
            delegation_id=delegation_id,
            delivery_id=delivery_id,
            run_id=run_id,
            launch_state=state["launch_state"],
            delivery_state=state["delivery_state"],
            result_state=state["result_state"],
            created=False,
        )


def _load_operation_after_genesis(
    root: Path,
    identity: DelegationIdentity,
    delegation_id: str,
    expected_run_id: str,
    expected_delivery_id: str,
) -> tuple[str, str, dict[str, Any]]:
    genesis = _load_json(
        _genesis_path(root, delegation_id),
        "delegation genesis",
        maximum=MAX_GENESIS_BYTES,
    )
    run_id, delivery_id = _validate_genesis(genesis, identity, delegation_id)
    if run_id != expected_run_id or delivery_id != expected_delivery_id:
        raise DelegationStateError("new delegation genesis identity changed after persistence")
    _write_state(
        root,
        delegation_id,
        _build_initial_state(identity, delegation_id, run_id, delivery_id),
    )
    state = _load_json(
        _state_path(root, delegation_id),
        "delegation state",
        maximum=MAX_STATE_BYTES,
    )
    _validate_state(state, identity, delegation_id, run_id, delivery_id)
    return run_id, delivery_id, state


def load_delegation(
    identity_value: Mapping[str, Any], *, state_root: Path
) -> DelegationSnapshot:
    identity = parse_delegation_identity(identity_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        _, _, state = _load_operation(root, identity, delegation_id)
        return _snapshot(identity, state)


def mark_launch_attempted(
    identity_value: Mapping[str, Any], *, run_id: str, state_root: Path
) -> DelegationSnapshot:
    identity = parse_delegation_identity(identity_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        actual_run_id, _, state = _load_operation(root, identity, delegation_id)
        _require_run_id(actual_run_id, run_id)
        if state["result_state"] != "open":
            raise DelegationStateError("terminal delegation cannot be launched")
        if state["launch_state"] == "prepared":
            state["launch_state"] = "launch-attempted"
            _bump(state)
            _write_state(root, delegation_id, state)
            _, _, state = _load_operation(root, identity, delegation_id)
        return _snapshot(identity, state)


def bind_worker_session(
    identity_value: Mapping[str, Any],
    *,
    run_id: str,
    session_ref_value: Mapping[str, Any],
    state_root: Path,
) -> DelegationSnapshot:
    identity = parse_delegation_identity(identity_value)
    session_ref = parse_worker_session_ref(session_ref_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        actual_run_id, _, state = _load_operation(root, identity, delegation_id)
        _require_run_id(actual_run_id, run_id)
        if state["launch_state"] == "prepared":
            raise DelegationStateError("worker session cannot bind before launch-attempted")
        existing = state["worker_session_ref"]
        if state["launch_state"] == "child-bound":
            if existing != session_ref.as_dict():
                raise DelegationStateError("delegation is already bound to a different worker")
            return _snapshot(identity, state)
        state["worker_session_ref"] = session_ref.as_dict()
        state["launch_state"] = "child-bound"
        _bump(state)
        _write_state(root, delegation_id, state)
        _, _, state = _load_operation(root, identity, delegation_id)
        return _snapshot(identity, state)


def claim_delivery(
    identity_value: Mapping[str, Any], *, run_id: str, state_root: Path
) -> DeliveryClaim:
    identity = parse_delegation_identity(identity_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        actual_run_id, delivery_id, state = _load_operation(root, identity, delegation_id)
        _require_run_id(actual_run_id, run_id)
        if state["launch_state"] != "child-bound":
            raise DelegationStateError("delivery cannot be claimed before child binding")
        if state["result_state"] != "open":
            return DeliveryClaim(delegation_id, delivery_id, False, state["delivery_state"])
        if state["delivery_state"] != "prepared":
            return DeliveryClaim(delegation_id, delivery_id, False, state["delivery_state"])
        state["delivery_state"] = "claimed"
        _bump(state)
        _write_state(root, delegation_id, state)
        _, _, state = _load_operation(root, identity, delegation_id)
        return DeliveryClaim(delegation_id, delivery_id, True, state["delivery_state"])


def record_delivery_outcome(
    identity_value: Mapping[str, Any],
    *,
    run_id: str,
    outcome: str,
    evidence_ref: str,
    state_root: Path,
) -> DelegationSnapshot:
    if outcome not in {"delivered", "unknown"}:
        raise DelegationStateError("delivery outcome must be delivered or unknown")
    evidence_ref = _bounded_text(
        evidence_ref,
        "delivery_evidence_ref",
        maximum=MAX_EVIDENCE_REF_CHARS,
    )
    assert isinstance(evidence_ref, str)
    identity = parse_delegation_identity(identity_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        actual_run_id, _, state = _load_operation(root, identity, delegation_id)
        _require_run_id(actual_run_id, run_id)
        if state["delivery_state"] == outcome:
            if state["delivery_evidence_ref"] != evidence_ref:
                raise DelegationStateError("delivery outcome already has different evidence")
            return _snapshot(identity, state)
        if state["delivery_state"] != "claimed":
            raise DelegationStateError("delivery outcome requires an active committed claim")
        state["delivery_state"] = outcome
        state["delivery_evidence_ref"] = evidence_ref
        _bump(state)
        _write_state(root, delegation_id, state)
        _, _, state = _load_operation(root, identity, delegation_id)
        return _snapshot(identity, state)


def record_worker_result(
    identity_value: Mapping[str, Any],
    *,
    run_id: str,
    result_value: Mapping[str, Any],
    state_root: Path,
) -> DelegationSnapshot:
    identity = parse_delegation_identity(identity_value)
    delegation_id = delegation_operation_key(identity)
    root = _root(state_root)
    with _acquire_task_lock(root, _lock_id(delegation_id)):
        actual_run_id, delivery_id, state = _load_operation(root, identity, delegation_id)
        _require_run_id(actual_run_id, run_id)
        parsed = parse_worker_result(
            result_value,
            identity=identity,
            delegation_id=delegation_id,
            delivery_id=delivery_id,
        )
        if state["delivery_state"] != "delivered":
            raise DelegationStateError("worker result cannot close an undelivered delegation")
        if state["result_state"] == "recorded":
            if (
                state["result_status"] != parsed.status
                or state["result_payload"] != parsed.payload
                or state["result_sha256"] != parsed.payload_sha256
            ):
                raise DelegationStateError("delegation already has a different terminal result")
            return _snapshot(identity, state)
        state["result_state"] = "recorded"
        state["result_status"] = parsed.status
        state["result_payload"] = parsed.payload
        state["result_sha256"] = parsed.payload_sha256
        state["result_recorded_at"] = _utc_now()
        _bump(state)
        _write_state(root, delegation_id, state)
        _, _, state = _load_operation(root, identity, delegation_id)
        return _snapshot(identity, state)
