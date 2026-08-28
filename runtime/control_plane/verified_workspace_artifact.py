from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import secrets
import stat as stat_module
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .file_artifact_observation import (
    FILE_ARTIFACT_CAPABILITY,
    FileArtifactObservationStream,
    observe_file_state,
)
from .verification import (
    ExpectedEffect,
    FinishStatus,
    ObservationSnapshot,
    StatePredicate,
    VerificationResult,
    VerificationStatus,
    evaluate_finish_gate,
    verify_expected_effect,
)
from .working_state import (
    AttemptIntent,
    BudgetKind,
    FailureCategory,
    FailureReason,
    LoopGuard,
    LoopGuardPolicy,
    MutatingOutcome,
    ReconciliationStatus,
    WorkingState,
    reconciliation_effect_id,
)


PROCEDURE_ID = "verified_workspace_artifact_v1"
PROCEDURE_VERSION = "1"
PROCEDURE_STATUS = "candidate"
QUALIFICATION_ADMISSION = "stage26-3a-qualification"
RESERVED_WORKSPACE_DIR = ".chat-agent-platform/stage26-3a"
MAX_CONTENT_CHARS = 4096
MAX_CONTENT_BYTES = 16384
MAX_ACTIONS = 3
MAX_RUNTIME_SECONDS = 10.0
CHECKPOINT_SCHEMA_VERSION = 2
_WORKING_TASK_BUDGET = 6
_WORKING_PROCEDURE_BUDGET = 6
_WORKING_STRATEGY_BUDGET = 2
_WORKING_ACTOR = f"procedure:{PROCEDURE_ID}"
_WORKING_ENVIRONMENT = "workspace-artifact-runtime"
_TRANSITIONS = ("stage_create", "final_create", "staging_cleanup")
_ARTIFACT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}\.txt$")
_TASK_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_RESUMABLE_NODES = {"preflight", "staged_verified", "final_verified"}
_NODE_TRANSITION = {
    "preflight": "stage_create",
    "staged_verified": "final_create",
    "final_verified": "staging_cleanup",
}
_TRANSITION_NODES = {
    "stage_create": ("preflight", "staged_verified"),
    "final_create": ("staged_verified", "final_verified"),
    "staging_cleanup": ("final_verified", "completed"),
}
_WORKSPACE_GUARD = LoopGuard(LoopGuardPolicy(max_identical_physical_attempts=2))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _evidence(path: Path) -> dict[str, Any]:
    state, complete, ambiguous = observe_file_state(path, max_bytes=MAX_CONTENT_BYTES)
    return {
        "exists": state.get("exists", False),
        "size": state.get("size"),
        "sha256": state.get("sha256") if complete and not ambiguous else None,
    }


def _stat_identity(value: os.stat_result) -> dict[str, int]:
    identity = {"device": int(value.st_dev), "inode": int(value.st_ino)}
    birthtime_ns = getattr(value, "st_birthtime_ns", None)
    if type(birthtime_ns) is int:
        identity["birthtime_ns"] = int(birthtime_ns)
    return identity


def _normalized_identity(value: Any) -> dict[str, int] | None:
    if type(value) is not dict:
        return None
    if set(value) - {"device", "inode", "birthtime_ns"}:
        return None
    if "device" not in value or "inode" not in value:
        return None
    try:
        result = {"device": int(value["device"]), "inode": int(value["inode"])}
        if "birthtime_ns" in value:
            result["birthtime_ns"] = int(value["birthtime_ns"])
    except (TypeError, ValueError):
        return None
    return result


def _file_identity(path: Path) -> dict[str, int] | None:
    try:
        stat = path.lstat()
    except FileNotFoundError:
        return None
    if not stat_module.S_ISREG(stat.st_mode):
        return None
    return _stat_identity(stat)


def _same_file_identity(path: Path, expected: dict[str, Any] | None) -> bool:
    normalized = _normalized_identity(expected)
    if normalized is None:
        return False
    actual = _file_identity(path)
    if actual is None:
        return False
    return all(actual.get(key) == value for key, value in normalized.items())


class _TaskLock:
    """Hold one cooperating-runner lock for the lifetime of a procedure call."""

    def __init__(self, handle: Any, backend: str) -> None:
        self._handle = handle
        self._backend = backend
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            handle.seek(0)
            if self._backend == "windows":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except (OSError, ValueError):
            pass
        finally:
            try:
                handle.close()
            except Exception:
                pass

    def __enter__(self) -> "_TaskLock":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


def _task_lock_path(state_root: Path, task_id: str) -> Path:
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("invalid task id")
    return _safe_child(state_root, state_root / f".{task_id}.lock")


def _acquire_task_lock(state_root: Path, task_id: str) -> _TaskLock:
    state_root.mkdir(parents=True, exist_ok=True)
    path = _task_lock_path(state_root, task_id)
    handle = path.open("a+b")
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\x00")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return _TaskLock(handle, "windows")

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _TaskLock(handle, "posix")
    except (OSError, ImportError) as exc:
        handle.close()
        raise BlockingIOError("task_already_running") from exc


def _file_predicates(
    name: str,
    *,
    size: int,
    sha256: str,
    identity: dict[str, Any] | None = None,
) -> tuple[StatePredicate, ...]:
    predicates = (
        StatePredicate.equals(name, "exists", expected=True),
        StatePredicate.equals(name, "kind", expected="file"),
        StatePredicate.equals(name, "size", expected=size),
        StatePredicate.equals(name, "sha256", expected=sha256),
    )
    if identity is None:
        return predicates + (StatePredicate.present(name, "identity"),)
    return predicates + (StatePredicate.equals(name, "identity", expected=identity),)


def _missing_predicates(name: str) -> tuple[StatePredicate, ...]:
    return (
        StatePredicate.equals(name, "exists", expected=False),
        StatePredicate.equals(name, "kind", expected="missing"),
        StatePredicate.equals(name, "size", expected=None),
        StatePredicate.equals(name, "sha256", expected=None),
        StatePredicate.equals(name, "identity", expected=None),
    )


def _verify_transition(
    *,
    effect_id: str,
    before: ObservationSnapshot,
    after: ObservationSnapshot,
    predicates: tuple[StatePredicate, ...],
    evidence_batch_id: str | None = None,
) -> VerificationResult:
    effect = ExpectedEffect(
        effect_id=effect_id,
        before=before.ref,
        predicates=predicates,
    )
    return verify_expected_effect(effect, after, evidence_batch_id=evidence_batch_id)


def _verify_from_intent(
    *,
    effect_id: str,
    intent: AttemptIntent,
    after: ObservationSnapshot,
    predicates: tuple[StatePredicate, ...],
    evidence_batch_id: str | None = None,
) -> VerificationResult:
    return verify_expected_effect(
        ExpectedEffect(
            effect_id=effect_id,
            before=intent.observation_ref,
            predicates=predicates,
        ),
        after,
        evidence_batch_id=evidence_batch_id,
    )


def _verify_current_state(
    observer: FileArtifactObservationStream,
    *,
    effect_id: str,
    predicates: tuple[StatePredicate, ...],
) -> tuple[VerificationResult, ObservationSnapshot]:
    before = observer.observe()
    after = observer.observe()
    return (
        _verify_transition(
            effect_id=effect_id,
            before=before,
            after=after,
            predicates=predicates,
        ),
        after,
    )


def _observed_evidence(snapshot: ObservationSnapshot, name: str) -> dict[str, Any]:
    value = snapshot.state[name]
    return {
        "exists": value.get("exists", False),
        "size": value.get("size"),
        "sha256": value.get("sha256"),
    }


def _observed_identity(snapshot: ObservationSnapshot, name: str) -> dict[str, int] | None:
    return _normalized_identity(snapshot.state[name].get("identity"))


def _kernel_receipt(result: VerificationResult) -> dict[str, Any]:
    return {
        "effect_id": result.effect_id,
        "status": result.status.value,
        "reason": result.reason,
        "observation": result.observation.as_dict() if result.observation is not None else None,
        "evidence_batch_id": result.evidence_batch_id,
    }


def _safe_child(root: Path, child: Path) -> Path:
    root = root.resolve()
    resolved = child.resolve(strict=False)
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError("procedure path escaped its configured root")
    return resolved


def _checkpoint_path(state_root: Path, task_id: str) -> Path:
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("invalid task id")
    return _safe_child(state_root, state_root / f"{task_id}.json")


def _write_checkpoint(state_root: Path, task_state: dict[str, Any]) -> None:
    """Atomically replace process-restart state; this is not a power-loss WAL."""

    state_root.mkdir(parents=True, exist_ok=True)
    task_id = str(task_state["task_id"])
    destination = _checkpoint_path(state_root, task_id)
    temporary = _safe_child(state_root, state_root / f".{task_id}.{secrets.token_hex(4)}.tmp")
    payload = json.dumps(task_state, ensure_ascii=False, indent=2, sort_keys=True)
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _load_checkpoint(state_root: Path, task_id: str) -> dict[str, Any]:
    path = _checkpoint_path(state_root, task_id)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("resume checkpoint does not exist") from exc
    except Exception as exc:
        raise ValueError("resume checkpoint is invalid") from exc
    if not isinstance(value, dict):
        raise ValueError("resume checkpoint must be an object")
    return value


def _record_transition(
    task_state: dict[str, Any],
    *,
    transition_id: str,
    from_node: str,
    to_node: str,
    action: str,
    verification: dict[str, Any],
    kernel_verification: dict[str, Any],
) -> None:
    task_state["current_node"] = to_node
    task_state["transition_receipts"].append(
        {
            "transition_id": transition_id,
            "from_node": from_node,
            "to_node": to_node,
            "action": action,
            "verification": verification,
            "kernel_verification": kernel_verification,
            "verified_at": _utc_now(),
        }
    )


def _result(task_state: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "procedure_id": PROCEDURE_ID,
        "procedure_version": PROCEDURE_VERSION,
        "procedure_status": PROCEDURE_STATUS,
        "task_id": task_state["task_id"],
        "status": task_state["status"],
        "current_node": task_state["current_node"],
        "action_count": task_state["action_count"],
        "transition_receipts": list(task_state["transition_receipts"]),
        "escalation_reason": task_state.get("escalation_reason"),
        **extra,
    }


def _rollback_owned_file(
    path: Path,
    expected_sha256: str,
    expected_file_identity: dict[str, Any] | None,
) -> bool:
    """Remove only the exact file object created by this run."""

    evidence = _evidence(path)
    if not evidence["exists"]:
        return True
    if evidence["sha256"] != expected_sha256:
        return False
    if not _same_file_identity(path, expected_file_identity):
        return False
    path.unlink()
    return not path.exists()


def _exclusive_create_file(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _exclusive_link_file(source: Path, target: Path) -> None:
    """Create target as a second name for the already-verified staging object."""

    source_stat = source.stat()
    parent_stat = target.parent.stat()
    if source_stat.st_dev != parent_stat.st_dev:
        raise OSError(errno.EXDEV, "workspace hard link requires one filesystem")
    os.link(source, target)


def _validate_resume_state(
    task_state: dict[str, Any],
    *,
    task_id: str,
    artifact_name: str,
    expected_sha: str,
    content_size: int,
    relative_target: str,
) -> int:
    required = {
        "schema_version",
        "task_id",
        "procedure_id",
        "procedure_version",
        "procedure_status",
        "artifact_name",
        "artifact_relative_path",
        "content_sha256",
        "content_size",
        "current_node",
        "status",
        "action_count",
        "action_budget",
        "transition_receipts",
    }
    if not required.issubset(task_state):
        raise ValueError("resume checkpoint is missing required fields")
    schema_version = int(task_state["schema_version"])
    if schema_version not in (1, CHECKPOINT_SCHEMA_VERSION):
        raise ValueError("resume checkpoint schema is unsupported")
    if str(task_state["task_id"]) != task_id:
        raise ValueError("resume checkpoint task id mismatch")
    if str(task_state["procedure_id"]) != PROCEDURE_ID:
        raise ValueError("resume checkpoint procedure mismatch")
    if str(task_state["procedure_version"]) != PROCEDURE_VERSION:
        raise ValueError("resume checkpoint version mismatch")
    if str(task_state["procedure_status"]) != PROCEDURE_STATUS:
        raise ValueError("resume checkpoint trust status mismatch")
    if str(task_state["artifact_name"]) != artifact_name:
        raise ValueError("resume checkpoint artifact mismatch")
    if str(task_state["artifact_relative_path"]) != relative_target:
        raise ValueError("resume checkpoint path mismatch")
    if str(task_state["content_sha256"]) != expected_sha:
        raise ValueError("resume checkpoint content digest mismatch")
    if int(task_state["content_size"]) != content_size:
        raise ValueError("resume checkpoint content size mismatch")
    if int(task_state["action_budget"]) != MAX_ACTIONS:
        raise ValueError("resume checkpoint action budget mismatch")
    if int(task_state["action_count"]) < 0 or int(task_state["action_count"]) > MAX_ACTIONS:
        raise ValueError("resume checkpoint action count is invalid")
    if not isinstance(task_state["transition_receipts"], list):
        raise ValueError("resume checkpoint transition receipts are invalid")
    if schema_version == CHECKPOINT_SCHEMA_VERSION:
        if "working_state" not in task_state or "prepared_intent" not in task_state:
            raise ValueError("resume checkpoint is missing Stage 26.3C recovery state")
        if not isinstance(task_state["working_state"], dict):
            raise ValueError("resume checkpoint WorkingState is invalid")
        if task_state["prepared_intent"] is not None and not isinstance(
            task_state["prepared_intent"], dict
        ):
            raise ValueError("resume checkpoint prepared_intent is invalid")
    return schema_version


def _new_working_state(task_id: str, snapshot: ObservationSnapshot) -> WorkingState:
    return WorkingState.create(
        task_id=task_id,
        task_budget=_WORKING_TASK_BUDGET,
        procedure_budget=_WORKING_PROCEDURE_BUDGET,
        strategy_budgets={name: _WORKING_STRATEGY_BUDGET for name in _TRANSITIONS},
        observation_ref=snapshot.ref,
        actor_ref=_WORKING_ACTOR,
        execution_environment_ref=_WORKING_ENVIRONMENT,
        evidence_scope_ref=snapshot.ref.stream_id,
        procedure_ref=PROCEDURE_ID,
        user_constraints=("no-overwrite", "exact-file-identity"),
        subgoal_refs=_TRANSITIONS,
        evidence_refs=(_observation_evidence_ref(snapshot),),
        capability_grant_refs=(QUALIFICATION_ADMISSION,),
    )


def _validate_working_state(state: WorkingState, *, task_id: str) -> None:
    if state.task_id != task_id:
        raise ValueError("WorkingState task id mismatch")
    if state.actor_ref != _WORKING_ACTOR:
        raise ValueError("WorkingState actor mismatch")
    if state.execution_environment_ref != _WORKING_ENVIRONMENT:
        raise ValueError("WorkingState execution environment mismatch")
    if state.procedure_ref != PROCEDURE_ID:
        raise ValueError("WorkingState procedure mismatch")
    if state.evidence_scope_ref != state.observation_ref.stream_id:
        raise ValueError("WorkingState evidence scope mismatch")
    if state.capability_grant_refs != (QUALIFICATION_ADMISSION,):
        raise ValueError("WorkingState capability grant mismatch")
    if state.observation_ref.capability != FILE_ARTIFACT_CAPABILITY:
        raise ValueError("WorkingState observation capability mismatch")
    if state.observation_ref.subject != f"{PROCEDURE_ID}:{task_id}":
        raise ValueError("WorkingState observation subject mismatch")

    expected = {
        (BudgetKind.TASK, task_id): _WORKING_TASK_BUDGET,
        (BudgetKind.PROCEDURE, PROCEDURE_ID): _WORKING_PROCEDURE_BUDGET,
        **{
            (BudgetKind.STRATEGY, name): _WORKING_STRATEGY_BUDGET
            for name in _TRANSITIONS
        },
    }
    actual = {(item.kind, item.scope_id): item.limit for item in state.budgets}
    if actual != expected:
        raise ValueError("WorkingState budget contract mismatch")


def _restore_working_state(task_state: dict[str, Any], *, task_id: str) -> WorkingState:
    try:
        state = WorkingState.from_dict(task_state["working_state"])
    except Exception as exc:
        raise ValueError("resume checkpoint WorkingState is invalid") from exc
    _validate_working_state(state, task_id=task_id)
    return state


def _observation_evidence_ref(snapshot: ObservationSnapshot) -> str:
    return f"observation:{snapshot.ref.stream_id}:{snapshot.ref.sequence}"


def _advance_working_observation(
    state: WorkingState,
    snapshot: ObservationSnapshot,
) -> WorkingState:
    if snapshot.ref == state.observation_ref:
        return state
    if (
        snapshot.ref.capability != state.observation_ref.capability
        or snapshot.ref.subject != state.observation_ref.subject
        or snapshot.ref.stream_id != state.observation_ref.stream_id
    ):
        raise ValueError("fresh workspace observation changed authority stream")
    if snapshot.ref.sequence <= state.observation_ref.sequence:
        raise ValueError("workspace observation did not advance")
    return state.record_observation(
        snapshot.ref,
        expected_revision=state.revision,
    )


def _action_fingerprint(
    *,
    task_id: str,
    transition_id: str,
    relative_target: str,
    expected_sha: str,
    content_size: int,
) -> str:
    payload = {
        "procedure": PROCEDURE_ID,
        "task_id": task_id,
        "transition": transition_id,
        "artifact": relative_target,
        "sha256": expected_sha,
        "size": content_size,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _make_intent(
    state: WorkingState,
    *,
    task_id: str,
    transition_id: str,
    relative_target: str,
    expected_sha: str,
    content_size: int,
) -> AttemptIntent:
    return AttemptIntent(
        operation_id=f"{task_id}:{transition_id}",
        strategy_id=transition_id,
        action_fingerprint=_action_fingerprint(
            task_id=task_id,
            transition_id=transition_id,
            relative_target=relative_target,
            expected_sha=expected_sha,
            content_size=content_size,
        ),
        observation_ref=state.observation_ref,
        actor_ref=_WORKING_ACTOR,
        execution_environment_ref=_WORKING_ENVIRONMENT,
        evidence_scope_ref=state.observation_ref.stream_id,
        evidence_refs=(
            f"observation:{state.observation_ref.stream_id}:{state.observation_ref.sequence}",
        ),
    )


def _prepared_marker(intent: AttemptIntent, *, transition_id: str, action_count: int) -> dict[str, Any]:
    return {
        "transition_id": transition_id,
        "operation_id": intent.operation_id,
        "strategy_id": intent.strategy_id,
        "action_fingerprint": intent.action_fingerprint,
        "observation_ref": intent.observation_ref.as_dict(),
        "actor_ref": intent.actor_ref,
        "execution_environment_ref": intent.execution_environment_ref,
        "evidence_scope_ref": intent.evidence_scope_ref,
        "evidence_refs": list(intent.evidence_refs),
        "action_count_before": action_count,
    }


def _intent_from_marker(
    marker: dict[str, Any],
    state: WorkingState,
    *,
    task_id: str,
    relative_target: str,
    expected_sha: str,
    content_size: int,
    action_count: int,
) -> tuple[str, AttemptIntent]:
    keys = {
        "transition_id",
        "operation_id",
        "strategy_id",
        "action_fingerprint",
        "observation_ref",
        "actor_ref",
        "execution_environment_ref",
        "evidence_scope_ref",
        "evidence_refs",
        "action_count_before",
    }
    if set(marker) != keys:
        raise ValueError("prepared_intent shape is invalid")
    transition_id = marker["transition_id"]
    if transition_id not in _TRANSITIONS:
        raise ValueError("prepared_intent transition is invalid")
    if marker["operation_id"] != f"{task_id}:{transition_id}":
        raise ValueError("prepared_intent operation mismatch")
    if marker["strategy_id"] != transition_id:
        raise ValueError("prepared_intent strategy mismatch")
    expected_fingerprint = _action_fingerprint(
        task_id=task_id,
        transition_id=transition_id,
        relative_target=relative_target,
        expected_sha=expected_sha,
        content_size=content_size,
    )
    if marker["action_fingerprint"] != expected_fingerprint:
        raise ValueError("prepared_intent action fingerprint mismatch")
    if marker["observation_ref"] != state.observation_ref.as_dict():
        raise ValueError("prepared_intent observation mismatch")
    if marker["actor_ref"] != _WORKING_ACTOR:
        raise ValueError("prepared_intent actor mismatch")
    if marker["execution_environment_ref"] != _WORKING_ENVIRONMENT:
        raise ValueError("prepared_intent environment mismatch")
    if marker["evidence_scope_ref"] != state.observation_ref.stream_id:
        raise ValueError("prepared_intent evidence scope mismatch")
    expected_refs = [
        f"observation:{state.observation_ref.stream_id}:{state.observation_ref.sequence}"
    ]
    if marker["evidence_refs"] != expected_refs:
        raise ValueError("prepared_intent evidence refs mismatch")
    if type(marker["action_count_before"]) is not int:
        raise ValueError("prepared_intent action count is invalid")
    if marker["action_count_before"] != action_count:
        raise ValueError("prepared_intent action count drift")
    intent = AttemptIntent(
        operation_id=marker["operation_id"],
        strategy_id=marker["strategy_id"],
        action_fingerprint=marker["action_fingerprint"],
        observation_ref=state.observation_ref,
        actor_ref=marker["actor_ref"],
        execution_environment_ref=marker["execution_environment_ref"],
        evidence_scope_ref=marker["evidence_scope_ref"],
        evidence_refs=tuple(marker["evidence_refs"]),
    )
    return transition_id, intent


def _matches_expected_file(
    snapshot: ObservationSnapshot,
    name: str,
    *,
    size: int,
    sha256: str,
    identity: dict[str, Any] | None = None,
) -> bool:
    if not snapshot.complete or snapshot.ambiguous:
        return False
    value = snapshot.state[name]
    if (
        value.get("exists") is not True
        or value.get("kind") != "file"
        or value.get("size") != size
        or value.get("sha256") != sha256
    ):
        return False
    if identity is not None:
        observed = _normalized_identity(value.get("identity"))
        expected = _normalized_identity(identity)
        if observed is None or expected is None:
            return False
        if not all(observed.get(key) == item for key, item in expected.items()):
            return False
    return True


def _is_missing(snapshot: ObservationSnapshot, name: str) -> bool:
    if not snapshot.complete or snapshot.ambiguous:
        return False
    value = snapshot.state[name]
    return value.get("exists") is False and value.get("kind") == "missing"


def _direct_reconciliation_status(
    transition_id: str,
    snapshot: ObservationSnapshot,
    *,
    content_size: int,
    expected_sha: str,
    staging_identity: dict[str, Any] | None,
) -> ReconciliationStatus:
    if transition_id == "stage_create":
        if _matches_expected_file(
            snapshot,
            "staging",
            size=content_size,
            sha256=expected_sha,
        ):
            return ReconciliationStatus.CONFIRMED_APPLIED
        if _is_missing(snapshot, "staging"):
            return ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return ReconciliationStatus.STILL_UNKNOWN

    if transition_id == "final_create":
        if staging_identity is None:
            return ReconciliationStatus.STILL_UNKNOWN
        staging_ok = _matches_expected_file(
            snapshot,
            "staging",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        )
        if staging_ok and _matches_expected_file(
            snapshot,
            "target",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        ):
            return ReconciliationStatus.CONFIRMED_APPLIED
        if staging_ok and _is_missing(snapshot, "target"):
            return ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return ReconciliationStatus.STILL_UNKNOWN

    if transition_id == "staging_cleanup":
        if staging_identity is None:
            return ReconciliationStatus.STILL_UNKNOWN
        target_ok = _matches_expected_file(
            snapshot,
            "target",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        )
        if target_ok and _is_missing(snapshot, "staging"):
            return ReconciliationStatus.CONFIRMED_APPLIED
        if target_ok and _matches_expected_file(
            snapshot,
            "staging",
            size=content_size,
            sha256=expected_sha,
            identity=staging_identity,
        ):
            return ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return ReconciliationStatus.STILL_UNKNOWN
    raise ValueError("unknown workspace transition")


def _unknown_failure(intent: AttemptIntent) -> FailureReason:
    return FailureReason(
        code="workspace_delivery_outcome_unknown",
        category=FailureCategory.RUNTIME_UNCERTAIN,
        message="Prepared workspace mutation lost its durable delivery outcome.",
        retryable=False,
        reconciliation_required=True,
        operation_id=intent.operation_id,
        strategy_id=intent.strategy_id,
        outcome=MutatingOutcome.OUTCOME_UNKNOWN,
        evidence_refs=intent.evidence_refs,
    )


def _not_applied_failure(intent: AttemptIntent, *, code: str) -> FailureReason:
    return FailureReason(
        code=code,
        category=FailureCategory.ACTION_NO_EFFECT,
        message="Workspace mutation produced no verified direct effect.",
        retryable=True,
        reconciliation_required=False,
        operation_id=intent.operation_id,
        strategy_id=intent.strategy_id,
        outcome=MutatingOutcome.NOT_APPLIED,
        evidence_refs=intent.evidence_refs,
    )


def _reconciliation_verification(
    attempt_revision: int,
    intent: AttemptIntent,
    status: ReconciliationStatus,
    snapshot: ObservationSnapshot,
    *,
    task_id: str,
) -> VerificationResult:
    verification_status = (
        VerificationStatus.UNKNOWN
        if status is ReconciliationStatus.STILL_UNKNOWN
        else VerificationStatus.PASS
    )
    return VerificationResult(
        effect_id=reconciliation_effect_id(
            intent.operation_id,
            attempt_revision,
            status,
        ),
        status=verification_status,
        reason="workspace_artifact_reconciliation",
        observation=snapshot.ref,
        evidence_batch_id=(
            f"{task_id}:reconcile:{attempt_revision}:{snapshot.ref.sequence}"
        ),
    )


def _record_normal_outcome(
    state: WorkingState,
    intent: AttemptIntent,
    status: ReconciliationStatus,
    after: ObservationSnapshot,
    *,
    task_id: str,
) -> WorkingState:
    if status is ReconciliationStatus.CONFIRMED_APPLIED:
        state = state.record_attempt(
            intent,
            MutatingOutcome.VERIFIED_APPLIED,
            None,
            expected_revision=state.revision,
            guard=_WORKSPACE_GUARD,
        )
        return _advance_working_observation(state, after)
    if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
        state = state.record_attempt(
            intent,
            MutatingOutcome.NOT_APPLIED,
            _not_applied_failure(intent, code="workspace_mutation_not_applied"),
            expected_revision=state.revision,
            guard=_WORKSPACE_GUARD,
        )
        return _advance_working_observation(state, after)

    state = state.record_attempt(
        intent,
        MutatingOutcome.OUTCOME_UNKNOWN,
        _unknown_failure(intent),
        expected_revision=state.revision,
        guard=_WORKSPACE_GUARD,
    )
    attempt = state.attempts[-1]
    return state.record_reconciliation(
        operation_id=intent.operation_id,
        attempt_revision=attempt.revision_after,
        status=ReconciliationStatus.STILL_UNKNOWN,
        verification=_reconciliation_verification(
            attempt.revision_after,
            intent,
            ReconciliationStatus.STILL_UNKNOWN,
            after,
            task_id=task_id,
        ),
        expected_revision=state.revision,
    )


def _prepare_transition(
    task_state: dict[str, Any],
    state: WorkingState,
    *,
    task_id: str,
    transition_id: str,
    relative_target: str,
    expected_sha: str,
    content_size: int,
    checkpoint: Callable[[], None],
) -> AttemptIntent:
    if task_state.get("prepared_intent") is not None:
        raise ValueError("another workspace mutation is already prepared")
    if state.unresolved_attempts():
        raise ValueError("unresolved workspace mutation blocks preparation")
    intent = _make_intent(
        state,
        task_id=task_id,
        transition_id=transition_id,
        relative_target=relative_target,
        expected_sha=expected_sha,
        content_size=content_size,
    )
    decision = _WORKSPACE_GUARD.evaluate(
        state,
        intent,
        expected_revision=state.revision,
    )
    if not decision.allowed:
        code = decision.failure.code if decision.failure is not None else "blocked"
        raise ValueError(f"LoopGuard blocked workspace mutation: {code}")
    task_state["prepared_intent"] = _prepared_marker(
        intent,
        transition_id=transition_id,
        action_count=int(task_state["action_count"]),
    )
    task_state["working_state"] = state.as_dict()
    checkpoint()
    return intent


def _record_file_exists_no_effect(
    task_state: dict[str, Any],
    state: WorkingState,
    intent: AttemptIntent,
    after: ObservationSnapshot,
    *,
    checkpoint: Callable[[], None],
) -> WorkingState:
    state = state.record_attempt(
        intent,
        MutatingOutcome.NOT_APPLIED,
        _not_applied_failure(intent, code="exclusive_create_precondition_changed"),
        expected_revision=state.revision,
        guard=_WORKSPACE_GUARD,
    )
    state = _advance_working_observation(state, after)
    task_state["working_state"] = state.as_dict()
    task_state["prepared_intent"] = None
    task_state["status"] = "abstained"
    task_state["escalation_reason"] = "state_changed_during_exclusive_create"
    checkpoint()
    return state


def _commit_recovered_applied_transition(
    task_state: dict[str, Any],
    state: WorkingState,
    intent: AttemptIntent,
    transition_id: str,
    fresh: ObservationSnapshot,
    *,
    marker_action_count: int,
    content_size: int,
    expected_sha: str,
    checkpoint: Callable[[], None],
) -> dict[str, Any] | None:
    from_node, to_node = _TRANSITION_NODES[transition_id]
    task_state["working_state"] = state.as_dict()
    task_state["prepared_intent"] = None
    task_state["action_count"] = marker_action_count + 1
    task_state["status"] = "running"
    task_state["escalation_reason"] = None

    if transition_id == "stage_create":
        identity = _observed_identity(fresh, "staging")
        if identity is None:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_reconciled_stage_identity_unproven"
            checkpoint()
            return {"status": "abstained"}
        result = _verify_from_intent(
            effect_id="stage_create",
            intent=intent,
            after=fresh,
            predicates=(
                *_file_predicates(
                    "staging",
                    size=content_size,
                    sha256=expected_sha,
                    identity=identity,
                ),
                *_missing_predicates("target"),
            ),
        )
        if result.status is not VerificationStatus.PASS:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_reconciled_stage_postcondition_failed"
            checkpoint()
            return {"status": "abstained"}
        task_state["staging_file_identity"] = identity
        _record_transition(
            task_state,
            transition_id=transition_id,
            from_node=from_node,
            to_node=to_node,
            action="exclusive_create_staging",
            verification=_observed_evidence(fresh, "staging"),
            kernel_verification=_kernel_receipt(result),
        )
        checkpoint()
        return None

    if transition_id == "final_create":
        identity = _normalized_identity(task_state.get("staging_file_identity"))
        if identity is None:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_reconciled_final_identity_unproven"
            checkpoint()
            return {"status": "abstained"}
        result = _verify_from_intent(
            effect_id="final_create",
            intent=intent,
            after=fresh,
            predicates=(
                *_file_predicates(
                    "staging",
                    size=content_size,
                    sha256=expected_sha,
                    identity=identity,
                ),
                *_file_predicates(
                    "target",
                    size=content_size,
                    sha256=expected_sha,
                    identity=identity,
                ),
            ),
        )
        if result.status is not VerificationStatus.PASS:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_reconciled_final_postcondition_failed"
            checkpoint()
            return {"status": "abstained"}
        task_state["target_file_identity"] = identity
        _record_transition(
            task_state,
            transition_id=transition_id,
            from_node=from_node,
            to_node=to_node,
            action="hardlink_verified_staging_to_final",
            verification={
                "target": _observed_evidence(fresh, "target"),
                "staging": _observed_evidence(fresh, "staging"),
            },
            kernel_verification=_kernel_receipt(result),
        )
        checkpoint()
        return None

    identity = _normalized_identity(task_state.get("target_file_identity"))
    if identity is None:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "resume_reconciled_cleanup_identity_unproven"
        checkpoint()
        return {"status": "abstained"}
    evidence_batch_id = f"{task_state['task_id']}:completion:{task_state['action_count']}"
    goal_result = _verify_from_intent(
        effect_id="completion_target",
        intent=intent,
        after=fresh,
        predicates=_file_predicates(
            "target",
            size=content_size,
            sha256=expected_sha,
            identity=identity,
        ),
        evidence_batch_id=evidence_batch_id,
    )
    safety_result = _verify_from_intent(
        effect_id="completion_staging_absent",
        intent=intent,
        after=fresh,
        predicates=_missing_predicates("staging"),
        evidence_batch_id=evidence_batch_id,
    )
    finish_gate = evaluate_finish_gate(
        evidence_batch_id=evidence_batch_id,
        candidate_done=True,
        goal_results=(goal_result,),
        safety_results=(safety_result,),
    )
    if finish_gate.status is not FinishStatus.DONE:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "resume_reconciled_completion_postcondition_failed"
        checkpoint()
        return {"status": "abstained"}
    final_verification = _observed_evidence(fresh, "target")
    _record_transition(
        task_state,
        transition_id=transition_id,
        from_node=from_node,
        to_node=to_node,
        action="remove_verified_staging",
        verification={"target": final_verification, "staging_exists": False},
        kernel_verification={
            "goal": _kernel_receipt(goal_result),
            "safety": _kernel_receipt(safety_result),
            "finish_gate": finish_gate.as_dict(),
        },
    )
    task_state["status"] = "completed"
    task_state["completed_at"] = _utc_now()
    task_state["rollback"] = {"staging_removed": True, "target_removed": False}
    checkpoint()
    return {"status": "completed", "final_verification": final_verification}


def _recover_prepared_intent(
    task_state: dict[str, Any],
    state: WorkingState,
    observer: FileArtifactObservationStream,
    *,
    task_id: str,
    relative_target: str,
    expected_sha: str,
    content_size: int,
    checkpoint: Callable[[], None],
) -> tuple[WorkingState, dict[str, Any] | None]:
    marker = task_state.get("prepared_intent")
    if marker is None:
        return state, None
    if not isinstance(marker, dict):
        raise ValueError("prepared_intent is invalid")
    transition_id, intent = _intent_from_marker(
        marker,
        state,
        task_id=task_id,
        relative_target=relative_target,
        expected_sha=expected_sha,
        content_size=content_size,
        action_count=int(task_state["action_count"]),
    )
    state = state.record_attempt(
        intent,
        MutatingOutcome.OUTCOME_UNKNOWN,
        _unknown_failure(intent),
        expected_revision=state.revision,
        guard=_WORKSPACE_GUARD,
    )
    attempt = state.attempts[-1]
    fresh = observer.observe()
    status = _direct_reconciliation_status(
        transition_id,
        fresh,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=task_state.get("staging_file_identity"),
    )
    verification = _reconciliation_verification(
        attempt.revision_after,
        intent,
        status,
        fresh,
        task_id=task_id,
    )
    state = state.record_reconciliation(
        operation_id=intent.operation_id,
        attempt_revision=attempt.revision_after,
        status=status,
        verification=verification,
        expected_revision=state.revision,
    )
    task_state["working_state"] = state.as_dict()

    if status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
        task_state["prepared_intent"] = None
        checkpoint()
        return state, None

    if status is ReconciliationStatus.CONFIRMED_APPLIED:
        recovery_result = _commit_recovered_applied_transition(
            task_state,
            state,
            intent,
            transition_id,
            fresh,
            marker_action_count=int(marker["action_count_before"]),
            content_size=content_size,
            expected_sha=expected_sha,
            checkpoint=checkpoint,
        )
        return state, recovery_result

    task_state["prepared_intent"] = None
    task_state["status"] = "abstained"
    task_state["escalation_reason"] = "resume_reconciliation_unknown"
    checkpoint()
    return state, {
        "status": task_state["status"],
        "escalation_reason": task_state["escalation_reason"],
    }


def _reconcile_exceptional_delivery(
    task_state: dict[str, Any],
    state: WorkingState,
    intent: AttemptIntent,
    observer: FileArtifactObservationStream,
    *,
    transition_id: str,
    task_id: str,
    content_size: int,
    expected_sha: str,
    checkpoint: Callable[[], None],
) -> WorkingState:
    state = state.record_attempt(
        intent,
        MutatingOutcome.OUTCOME_UNKNOWN,
        _unknown_failure(intent),
        expected_revision=state.revision,
        guard=_WORKSPACE_GUARD,
    )
    attempt = state.attempts[-1]
    fresh = observer.observe()
    status = _direct_reconciliation_status(
        transition_id,
        fresh,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=task_state.get("staging_file_identity"),
    )
    state = state.record_reconciliation(
        operation_id=intent.operation_id,
        attempt_revision=attempt.revision_after,
        status=status,
        verification=_reconciliation_verification(
            attempt.revision_after,
            intent,
            status,
            fresh,
            task_id=task_id,
        ),
        expected_revision=state.revision,
    )
    task_state["working_state"] = state.as_dict()
    task_state["prepared_intent"] = None
    if status is ReconciliationStatus.CONFIRMED_APPLIED:
        task_state["action_count"] = int(task_state["action_count"]) + 1
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "delivery_error_reconciled_applied"
    elif status is ReconciliationStatus.CONFIRMED_NOT_APPLIED:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "delivery_error_confirmed_not_applied"
    else:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "delivery_error_reconciliation_unknown"
    checkpoint()
    return state


def _same_node_applied_operation(state: WorkingState, *, task_id: str, node: str) -> bool:
    transition = _NODE_TRANSITION[node]
    latest = state.latest_attempt(f"{task_id}:{transition}")
    if latest is None:
        return False
    if latest.outcome is MutatingOutcome.VERIFIED_APPLIED:
        return True
    reconciliation = state.reconciliation_for(latest)
    return (
        reconciliation is not None
        and reconciliation.status is ReconciliationStatus.CONFIRMED_APPLIED
    )


def run_verified_workspace_artifact(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    """Run or resume the bounded verified workspace-artifact procedure."""

    started = time.monotonic()
    workspace_root = workspace_root.resolve()
    state_root = state_root.resolve()
    if not workspace_root.is_dir():
        raise ValueError("configured workspace root is not an existing directory")
    if candidate_admission != QUALIFICATION_ADMISSION:
        raise PermissionError("candidate procedure is not admitted by this profile")

    keys = set(request)
    required_keys = {"procedure", "artifact_name", "content"}
    allowed_keys = required_keys | {"resume_task_id"}
    if not required_keys.issubset(keys) or not keys.issubset(allowed_keys):
        raise ValueError(
            "procedure request must contain procedure, artifact_name, content and optional resume_task_id"
        )
    if request.get("procedure") != PROCEDURE_ID:
        raise ValueError("unknown or unregistered procedure")

    artifact_name = request.get("artifact_name")
    content = request.get("content")
    if not isinstance(artifact_name, str) or not _ARTIFACT_RE.fullmatch(artifact_name):
        raise ValueError("artifact_name must be a simple .txt file name")
    if not isinstance(content, str) or not content or len(content) > MAX_CONTENT_CHARS:
        raise ValueError("content must contain 1..4096 Unicode characters")
    if "\x00" in content:
        raise ValueError("content must not contain NUL")

    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_CONTENT_BYTES:
        raise ValueError("UTF-8 content exceeds the procedure byte budget")
    expected_sha = _sha256(content_bytes)

    reserved_root = _safe_child(
        workspace_root,
        workspace_root / Path(*RESERVED_WORKSPACE_DIR.split("/")),
    )
    target = _safe_child(reserved_root, reserved_root / artifact_name)
    relative_target = target.relative_to(workspace_root).as_posix()

    resume_task_id = request.get("resume_task_id")
    if resume_task_id is not None and (
        not isinstance(resume_task_id, str) or not _TASK_ID_RE.fullmatch(resume_task_id)
    ):
        raise ValueError("resume_task_id must be a 32-character lowercase hex task id")

    task_id = resume_task_id if resume_task_id is not None else secrets.token_hex(16)
    task_lock = _acquire_task_lock(state_root, task_id)
    if task_lock is None:  # defensive: retain a live local reference for the whole call
        raise RuntimeError("task lock acquisition failed")

    staging = _safe_child(reserved_root, reserved_root / f".{artifact_name}.{task_id}.staging")
    schema_version = CHECKPOINT_SCHEMA_VERSION
    working_state: WorkingState | None = None
    if resume_task_id is None:
        task_state: dict[str, Any] = {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "task_id": task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": artifact_name,
            "artifact_relative_path": relative_target,
            "content_sha256": expected_sha,
            "content_size": len(content_bytes),
            "current_node": "preflight",
            "status": "running",
            "action_count": 0,
            "action_budget": MAX_ACTIONS,
            "runtime_budget_seconds": MAX_RUNTIME_SECONDS,
            "transition_receipts": [],
            "escalation_reason": None,
            "staging_file_identity": None,
            "target_file_identity": None,
            "working_state": None,
            "prepared_intent": None,
            "created_at": _utc_now(),
        }
    else:
        task_state = _load_checkpoint(state_root, task_id)
        schema_version = _validate_resume_state(
            task_state,
            task_id=task_id,
            artifact_name=artifact_name,
            expected_sha=expected_sha,
            content_size=len(content_bytes),
            relative_target=relative_target,
        )
        task_state.setdefault("staging_file_identity", None)
        task_state.setdefault("target_file_identity", None)
        task_state["resumed_at"] = _utc_now()
        if schema_version == CHECKPOINT_SCHEMA_VERSION:
            working_state = _restore_working_state(task_state, task_id=task_id)

    if working_state is None:
        observer = FileArtifactObservationStream(
            root=workspace_root,
            subject=f"{PROCEDURE_ID}:{task_id}",
            paths={"staging": staging, "target": target},
            max_bytes=MAX_CONTENT_BYTES,
        )
    else:
        observer = FileArtifactObservationStream(
            root=workspace_root,
            subject=f"{PROCEDURE_ID}:{task_id}",
            paths={"staging": staging, "target": target},
            max_bytes=MAX_CONTENT_BYTES,
            stream_id=working_state.observation_ref.stream_id,
            initial_sequence=working_state.observation_ref.sequence,
        )

    def checkpoint() -> None:
        nonlocal working_state
        if int(task_state["action_count"]) > MAX_ACTIONS:
            raise RuntimeError("action budget exceeded")
        if time.monotonic() - started > MAX_RUNTIME_SECONDS:
            raise RuntimeError("runtime budget exceeded")
        if working_state is not None:
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            durable = task_state.get("working_state")
            durable_revision = (
                durable.get("revision", -1)
                if isinstance(durable, dict) and type(durable.get("revision")) is int
                else -1
            )
            if working_state.revision >= durable_revision:
                task_state["working_state"] = working_state.as_dict()
            task_state.setdefault("prepared_intent", None)
        _write_checkpoint(state_root, task_state)

    if task_state["status"] == "completed":
        completed_result, completed_snapshot = _verify_current_state(
            observer,
            effect_id="completed_checkpoint_current_state",
            predicates=(
                *_file_predicates(
                    "target",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=task_state.get("target_file_identity"),
                ),
                *_missing_predicates("staging"),
            ),
        )
        if completed_result.status is not VerificationStatus.PASS:
            raise ValueError("completed checkpoint no longer matches current target identity")
        final = _observed_evidence(completed_snapshot, "target")
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=final,
            rollback=task_state.get("rollback", {"staging_removed": True, "target_removed": False}),
            resumed=True,
        )

    if task_state["status"] != "running":
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback=task_state.get(
                "rollback",
                {"staging_removed": not staging.exists(), "target_removed": False},
            ),
            resumed=True,
        )

    node = str(task_state["current_node"])
    if node not in _RESUMABLE_NODES:
        raise ValueError("resume checkpoint node is not safely resumable")

    if working_state is not None and task_state.get("prepared_intent") is not None:
        working_state, recovery_result = _recover_prepared_intent(
            task_state,
            working_state,
            observer,
            task_id=task_id,
            relative_target=relative_target,
            expected_sha=expected_sha,
            content_size=len(content_bytes),
            checkpoint=checkpoint,
        )
        if recovery_result is not None:
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=recovery_result.get("final_verification", _evidence(target)),
                rollback=task_state.get(
                    "rollback",
                    {"staging_removed": not staging.exists(), "target_removed": False},
                ),
                resumed=True,
            )
        node = str(task_state["current_node"])

    if working_state is not None and working_state.unresolved_attempts():
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "resume_reconciliation_required"
        checkpoint()
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback={"staging_removed": not staging.exists(), "target_removed": False},
            resumed=resume_task_id is not None,
        )

    if working_state is not None and _same_node_applied_operation(
        working_state,
        task_id=task_id,
        node=node,
    ):
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "resume_verified_effect_without_transition_receipt"
        checkpoint()
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback={"staging_removed": not staging.exists(), "target_removed": False},
            resumed=resume_task_id is not None,
        )

    migrated_snapshot: ObservationSnapshot | None = None

    if node == "preflight":
        preflight = observer.observe()
        if working_state is None:
            working_state = _new_working_state(task_id, preflight)
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
        else:
            working_state = _advance_working_observation(working_state, preflight)
        migrated_snapshot = preflight
        if preflight.ambiguous:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "preflight_observation_unknown"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_observed_evidence(preflight, "target"),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        if preflight.state["target"].get("exists") is True:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "target_already_exists"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_observed_evidence(preflight, "target"),
                rollback={"staging_removed": True, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        if preflight.state["staging"].get("exists") is True:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "unexpected_staging_state"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_observed_evidence(preflight, "target"),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        checkpoint()
    elif node == "staged_verified":
        legacy_identity = task_state.get("staging_file_identity")
        resume_staged, resume_staged_snapshot = _verify_current_state(
            observer,
            effect_id="resume_staged_current_state",
            predicates=(
                *_file_predicates(
                    "staging",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=(legacy_identity if working_state is not None else None),
                ),
                *_missing_predicates("target"),
            ),
        )
        if (
            resume_staged.status is not VerificationStatus.PASS
            or (working_state is None and not _same_file_identity(staging, legacy_identity))
        ):
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = (
                "resume_unexpected_target_state"
                if resume_staged_snapshot.state["target"].get("exists") is True
                else "resume_staging_identity_mismatch"
            )
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=True,
            )
        upgraded_staging_identity = _observed_identity(resume_staged_snapshot, "staging")
        if upgraded_staging_identity is None:
            raise ValueError("resume staging identity is unavailable")
        task_state["staging_file_identity"] = upgraded_staging_identity
        migrated_snapshot = resume_staged_snapshot
        if working_state is None:
            working_state = _new_working_state(task_id, resume_staged_snapshot)
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            task_state["prepared_intent"] = None
        else:
            working_state = _advance_working_observation(
                working_state,
                resume_staged_snapshot,
            )
        checkpoint()
    elif node == "final_verified":
        legacy_staging_identity = task_state.get("staging_file_identity")
        legacy_target_identity = task_state.get("target_file_identity")
        resume_final, resume_final_snapshot = _verify_current_state(
            observer,
            effect_id="resume_final_current_state",
            predicates=(
                *_file_predicates(
                    "staging",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=(legacy_staging_identity if working_state is not None else None),
                ),
                *_file_predicates(
                    "target",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=(legacy_target_identity if working_state is not None else None),
                ),
            ),
        )
        if (
            resume_final.status is not VerificationStatus.PASS
            or (
                working_state is None
                and (
                    not _same_file_identity(staging, legacy_staging_identity)
                    or not _same_file_identity(target, legacy_target_identity)
                )
            )
        ):
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_final_identity_mismatch"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=True,
            )
        upgraded_staging_identity = _observed_identity(resume_final_snapshot, "staging")
        upgraded_target_identity = _observed_identity(resume_final_snapshot, "target")
        if upgraded_staging_identity is None or upgraded_target_identity is None:
            raise ValueError("resume final identity is unavailable")
        task_state["staging_file_identity"] = upgraded_staging_identity
        task_state["target_file_identity"] = upgraded_target_identity
        migrated_snapshot = resume_final_snapshot
        if working_state is None:
            working_state = _new_working_state(task_id, resume_final_snapshot)
            task_state["schema_version"] = CHECKPOINT_SCHEMA_VERSION
            task_state["prepared_intent"] = None
        else:
            working_state = _advance_working_observation(
                working_state,
                resume_final_snapshot,
            )
        checkpoint()

    if working_state is None or migrated_snapshot is None:
        raise RuntimeError("WorkingState initialization failed")

    reserved_root.mkdir(parents=True, exist_ok=True)
    staging_owned = False
    target_owned = False
    rollback = {"staging_removed": not staging.exists(), "target_removed": False}

    try:
        if node == "preflight":
            stage_before = observer.observe()
            working_state = _advance_working_observation(working_state, stage_before)
            intent = _prepare_transition(
                task_state,
                working_state,
                task_id=task_id,
                transition_id="stage_create",
                relative_target=relative_target,
                expected_sha=expected_sha,
                content_size=len(content_bytes),
                checkpoint=checkpoint,
            )
            try:
                _exclusive_create_file(staging, content_bytes)
            except FileExistsError:
                stage_after = observer.observe()
                working_state = _record_file_exists_no_effect(
                    task_state,
                    working_state,
                    intent,
                    stage_after,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )
            except Exception:
                working_state = _reconcile_exceptional_delivery(
                    task_state,
                    working_state,
                    intent,
                    observer,
                    transition_id="stage_create",
                    task_id=task_id,
                    content_size=len(content_bytes),
                    expected_sha=expected_sha,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )

            stage_after = observer.observe()
            direct_status = _direct_reconciliation_status(
                "stage_create",
                stage_after,
                content_size=len(content_bytes),
                expected_sha=expected_sha,
                staging_identity=None,
            )
            staging_identity = _observed_identity(stage_after, "staging")
            stage_result = _verify_transition(
                effect_id="stage_create",
                before=stage_before,
                after=stage_after,
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=staging_identity,
                    ),
                    *_missing_predicates("target"),
                ),
            )
            working_state = _record_normal_outcome(
                working_state,
                intent,
                direct_status,
                stage_after,
                task_id=task_id,
            )
            task_state["action_count"] = int(task_state["action_count"]) + 1
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
            if (
                direct_status is not ReconciliationStatus.CONFIRMED_APPLIED
                or stage_result.status is not VerificationStatus.PASS
                or staging_identity is None
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "staging_postcondition_failed"
                checkpoint()
                raise RuntimeError("staging postcondition failed")
            task_state["staging_file_identity"] = staging_identity
            staging_owned = True
            _record_transition(
                task_state,
                transition_id="stage_create",
                from_node="preflight",
                to_node="staged_verified",
                action="exclusive_create_staging",
                verification=_observed_evidence(stage_after, "staging"),
                kernel_verification=_kernel_receipt(stage_result),
            )
            checkpoint()
            node = "staged_verified"

        if node == "staged_verified":
            final_before_check, final_before = _verify_current_state(
                observer,
                effect_id="final_create_precondition",
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=task_state.get("staging_file_identity"),
                    ),
                    *_missing_predicates("target"),
                ),
            )
            working_state = _advance_working_observation(working_state, final_before)
            if final_before_check.status is not VerificationStatus.PASS:
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "final_create_precondition_failed"
                checkpoint()
                raise RuntimeError("final create precondition failed")
            intent = _prepare_transition(
                task_state,
                working_state,
                task_id=task_id,
                transition_id="final_create",
                relative_target=relative_target,
                expected_sha=expected_sha,
                content_size=len(content_bytes),
                checkpoint=checkpoint,
            )
            try:
                _exclusive_link_file(staging, target)
            except FileExistsError:
                final_after = observer.observe()
                working_state = _record_file_exists_no_effect(
                    task_state,
                    working_state,
                    intent,
                    final_after,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )
            except Exception:
                working_state = _reconcile_exceptional_delivery(
                    task_state,
                    working_state,
                    intent,
                    observer,
                    transition_id="final_create",
                    task_id=task_id,
                    content_size=len(content_bytes),
                    expected_sha=expected_sha,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )

            final_after = observer.observe()
            staging_identity = _normalized_identity(task_state.get("staging_file_identity"))
            direct_status = _direct_reconciliation_status(
                "final_create",
                final_after,
                content_size=len(content_bytes),
                expected_sha=expected_sha,
                staging_identity=staging_identity,
            )
            final_result = _verify_transition(
                effect_id="final_create",
                before=final_before,
                after=final_after,
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=staging_identity,
                    ),
                    *_file_predicates(
                        "target",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=staging_identity,
                    ),
                ),
            )
            target_identity = _observed_identity(final_after, "target")
            working_state = _record_normal_outcome(
                working_state,
                intent,
                direct_status,
                final_after,
                task_id=task_id,
            )
            task_state["action_count"] = int(task_state["action_count"]) + 1
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
            if (
                direct_status is not ReconciliationStatus.CONFIRMED_APPLIED
                or final_result.status is not VerificationStatus.PASS
                or staging_identity is None
                or target_identity != staging_identity
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "final_create_postcondition_failed"
                checkpoint()
                raise RuntimeError("final create postcondition failed")
            task_state["target_file_identity"] = staging_identity
            target_owned = True
            _record_transition(
                task_state,
                transition_id="final_create",
                from_node="staged_verified",
                to_node="final_verified",
                action="hardlink_verified_staging_to_final",
                verification={
                    "target": _observed_evidence(final_after, "target"),
                    "staging": _observed_evidence(final_after, "staging"),
                },
                kernel_verification=_kernel_receipt(final_result),
            )
            checkpoint()
            node = "final_verified"

        if node == "final_verified":
            cleanup_before_check, cleanup_before = _verify_current_state(
                observer,
                effect_id="staging_cleanup_precondition",
                predicates=(
                    *_file_predicates(
                        "staging",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=task_state.get("staging_file_identity"),
                    ),
                    *_file_predicates(
                        "target",
                        size=len(content_bytes),
                        sha256=expected_sha,
                        identity=task_state.get("target_file_identity"),
                    ),
                ),
            )
            working_state = _advance_working_observation(working_state, cleanup_before)
            if cleanup_before_check.status is not VerificationStatus.PASS:
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "cleanup_precondition_failed"
                checkpoint()
                raise RuntimeError("cleanup precondition failed")
            intent = _prepare_transition(
                task_state,
                working_state,
                task_id=task_id,
                transition_id="staging_cleanup",
                relative_target=relative_target,
                expected_sha=expected_sha,
                content_size=len(content_bytes),
                checkpoint=checkpoint,
            )
            try:
                staging.unlink()
            except Exception:
                working_state = _reconcile_exceptional_delivery(
                    task_state,
                    working_state,
                    intent,
                    observer,
                    transition_id="staging_cleanup",
                    task_id=task_id,
                    content_size=len(content_bytes),
                    expected_sha=expected_sha,
                    checkpoint=checkpoint,
                )
                return _result(
                    task_state,
                    artifact_relative_path=relative_target,
                    final_verification=_evidence(target),
                    rollback=rollback,
                    resumed=resume_task_id is not None,
                )

            completion_after = observer.observe()
            identity = _normalized_identity(task_state.get("target_file_identity"))
            direct_status = _direct_reconciliation_status(
                "staging_cleanup",
                completion_after,
                content_size=len(content_bytes),
                expected_sha=expected_sha,
                staging_identity=identity,
            )
            evidence_batch_id = f"{task_id}:completion:{int(task_state['action_count']) + 1}"
            goal_result = _verify_transition(
                effect_id="completion_target",
                before=cleanup_before,
                after=completion_after,
                predicates=_file_predicates(
                    "target",
                    size=len(content_bytes),
                    sha256=expected_sha,
                    identity=identity,
                ),
                evidence_batch_id=evidence_batch_id,
            )
            safety_result = _verify_transition(
                effect_id="completion_staging_absent",
                before=cleanup_before,
                after=completion_after,
                predicates=_missing_predicates("staging"),
                evidence_batch_id=evidence_batch_id,
            )
            finish_gate = evaluate_finish_gate(
                evidence_batch_id=evidence_batch_id,
                candidate_done=True,
                goal_results=(goal_result,),
                safety_results=(safety_result,),
            )
            working_state = _record_normal_outcome(
                working_state,
                intent,
                direct_status,
                completion_after,
                task_id=task_id,
            )
            task_state["action_count"] = int(task_state["action_count"]) + 1
            task_state["working_state"] = working_state.as_dict()
            task_state["prepared_intent"] = None
            staging_owned = False
            final_verification = _observed_evidence(completion_after, "target")
            if (
                direct_status is not ReconciliationStatus.CONFIRMED_APPLIED
                or finish_gate.status is not FinishStatus.DONE
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "completion_postcondition_failed"
                checkpoint()
                raise RuntimeError("completion postcondition failed")
            _record_transition(
                task_state,
                transition_id="staging_cleanup",
                from_node="final_verified",
                to_node="completed",
                action="remove_verified_staging",
                verification={"target": final_verification, "staging_exists": False},
                kernel_verification={
                    "goal": _kernel_receipt(goal_result),
                    "safety": _kernel_receipt(safety_result),
                    "finish_gate": finish_gate.as_dict(),
                },
            )
            task_state["status"] = "completed"
            task_state["completed_at"] = _utc_now()
            task_state["rollback"] = dict(rollback)
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=final_verification,
                rollback=rollback,
                resumed=resume_task_id is not None,
            )
    except Exception as exc:
        if task_state["status"] != "abstained":
            task_state["status"] = "failed"
            task_state["escalation_reason"] = f"runtime_error:{type(exc).__name__}"
    finally:
        if task_state["status"] != "completed":
            safe_to_compensate = (
                task_state.get("prepared_intent") is None
                and working_state is not None
                and not working_state.unresolved_attempts()
            )
            changed = False
            if safe_to_compensate and staging_owned:
                rollback["staging_removed"] = _rollback_owned_file(
                    staging,
                    expected_sha,
                    task_state.get("staging_file_identity"),
                )
                changed = changed or rollback["staging_removed"]
            if safe_to_compensate and target_owned:
                rollback["target_removed"] = _rollback_owned_file(
                    target,
                    expected_sha,
                    task_state.get("target_file_identity"),
                )
                changed = changed or rollback["target_removed"]
            if changed and working_state is not None:
                try:
                    rollback_snapshot = observer.observe()
                    working_state = _advance_working_observation(
                        working_state,
                        rollback_snapshot,
                    )
                    task_state["working_state"] = working_state.as_dict()
                except Exception:
                    pass
            task_state["rollback"] = dict(rollback)
            task_state["finished_at"] = _utc_now()
            try:
                checkpoint()
            except Exception:
                pass

    return _result(
        task_state,
        artifact_relative_path=relative_target,
        final_verification=_evidence(target),
        rollback=rollback,
        resumed=resume_task_id is not None,
    )
