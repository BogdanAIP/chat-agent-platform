from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROCEDURE_ID = "verified_workspace_artifact_v1"
PROCEDURE_VERSION = "1"
PROCEDURE_STATUS = "candidate"
QUALIFICATION_ADMISSION = "stage26-3a-qualification"
RESERVED_WORKSPACE_DIR = ".chat-agent-platform/stage26-3a"
MAX_CONTENT_CHARS = 4096
MAX_CONTENT_BYTES = 16384
MAX_ACTIONS = 3
MAX_RUNTIME_SECONDS = 10.0
_ARTIFACT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}\.txt$")
_TASK_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_RESUMABLE_NODES = {"preflight", "staged_verified", "final_verified"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "size": None, "sha256": None}
    data = path.read_bytes()
    return {"exists": True, "size": len(data), "sha256": _sha256(data)}


def _file_identity(path: Path) -> dict[str, int] | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    if not path.is_file():
        return None
    return {"device": int(stat.st_dev), "inode": int(stat.st_ino)}


def _same_file_identity(path: Path, expected: dict[str, Any] | None) -> bool:
    if not isinstance(expected, dict):
        return False
    actual = _file_identity(path)
    if actual is None:
        return False
    try:
        return (
            actual["device"] == int(expected["device"])
            and actual["inode"] == int(expected["inode"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def _expected_evidence(size: int, sha256: str) -> dict[str, Any]:
    return {"exists": True, "size": size, "sha256": sha256}


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
) -> None:
    task_state["current_node"] = to_node
    task_state["transition_receipts"].append(
        {
            "transition_id": transition_id,
            "from_node": from_node,
            "to_node": to_node,
            "action": action,
            "verification": verification,
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
    """Remove only the exact file object created by this run.

    Digest equality alone is not ownership: another actor could replace the path
    with a new file containing identical bytes.  In-process rollback therefore
    requires both the expected digest and the recorded filesystem object identity.
    """

    evidence = _evidence(path)
    if not evidence["exists"]:
        return True
    if evidence["sha256"] != expected_sha256:
        return False
    if not _same_file_identity(path, expected_file_identity):
        return False
    path.unlink()
    return not path.exists()


def _validate_resume_state(
    task_state: dict[str, Any],
    *,
    task_id: str,
    artifact_name: str,
    expected_sha: str,
    content_size: int,
    relative_target: str,
) -> None:
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
    if int(task_state["schema_version"]) != 1:
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


def run_verified_workspace_artifact(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    """Run or resume one bounded qualification procedure.

    New execution performs three verified transitions: staging create, final
    exclusive create, and staging cleanup.  A caller may resume only from a
    durable checkpoint by supplying ``resume_task_id`` together with the same
    procedure/artifact/content.  Resume never guesses across an ambiguous state.
    """

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
    expected = _expected_evidence(len(content_bytes), expected_sha)

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

    if resume_task_id is None:
        task_id = secrets.token_hex(16)
        staging = _safe_child(reserved_root, reserved_root / f".{artifact_name}.{task_id}.staging")
        task_state: dict[str, Any] = {
            "schema_version": 1,
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
            "created_at": _utc_now(),
        }
    else:
        task_id = resume_task_id
        staging = _safe_child(reserved_root, reserved_root / f".{artifact_name}.{task_id}.staging")
        task_state = _load_checkpoint(state_root, task_id)
        _validate_resume_state(
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

    def checkpoint() -> None:
        if int(task_state["action_count"]) > MAX_ACTIONS:
            raise RuntimeError("action budget exceeded")
        if time.monotonic() - started > MAX_RUNTIME_SECONDS:
            raise RuntimeError("runtime budget exceeded")
        _write_checkpoint(state_root, task_state)

    if task_state["status"] == "completed":
        final = _evidence(target)
        if final != expected or not _same_file_identity(target, task_state.get("target_file_identity")):
            raise ValueError("completed checkpoint no longer matches current target identity")
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
            rollback=task_state.get("rollback", {"staging_removed": not staging.exists(), "target_removed": False}),
            resumed=True,
        )

    node = str(task_state["current_node"])
    if node not in _RESUMABLE_NODES:
        raise ValueError("resume checkpoint node is not safely resumable")

    if resume_task_id is None:
        checkpoint()

    # New execution preflight.  Internal checkpoint persistence is allowed, but
    # no workspace artifact or reserved directory is created on an abstaining
    # precondition path.
    if node == "preflight":
        if target.exists():
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "target_already_exists"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": True, "target_removed": False},
                resumed=resume_task_id is not None,
            )
        if staging.exists():
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "unexpected_staging_state"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=resume_task_id is not None,
            )
    elif node == "staged_verified":
        if _evidence(staging) != expected or not _same_file_identity(
            staging, task_state.get("staging_file_identity")
        ):
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_staging_identity_mismatch"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=True,
            )
        if target.exists():
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "resume_unexpected_target_state"
            checkpoint()
            return _result(
                task_state,
                artifact_relative_path=relative_target,
                final_verification=_evidence(target),
                rollback={"staging_removed": False, "target_removed": False},
                resumed=True,
            )
    elif node == "final_verified":
        if (
            _evidence(staging) != expected
            or not _same_file_identity(staging, task_state.get("staging_file_identity"))
            or _evidence(target) != expected
            or not _same_file_identity(target, task_state.get("target_file_identity"))
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

    reserved_root.mkdir(parents=True, exist_ok=True)
    staging_owned = False
    target_owned = False
    rollback = {"staging_removed": not staging.exists(), "target_removed": False}

    try:
        if node == "preflight":
            # Transition 1: exclusive staging create -> exact digest + file identity.
            with staging.open("xb") as handle:
                handle.write(content_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            staging_owned = True
            task_state["action_count"] = int(task_state["action_count"]) + 1
            staged = _evidence(staging)
            staging_identity = _file_identity(staging)
            if staged != expected or staging_identity is None:
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "staging_postcondition_failed"
                raise RuntimeError("staging postcondition failed")
            task_state["staging_file_identity"] = staging_identity
            _record_transition(
                task_state,
                transition_id="stage_create",
                from_node="preflight",
                to_node="staged_verified",
                action="exclusive_create_staging",
                verification=staged,
            )
            checkpoint()
            node = "staged_verified"

        if node == "staged_verified":
            # Transition 2: exclusive final create. 'x' prevents overwrite races.
            with target.open("xb") as handle:
                handle.write(content_bytes)
                handle.flush()
                os.fsync(handle.fileno())
            target_owned = True
            task_state["action_count"] = int(task_state["action_count"]) + 1
            final_after_create = _evidence(target)
            staging_after_final = _evidence(staging)
            target_identity = _file_identity(target)
            if (
                final_after_create != expected
                or staging_after_final != expected
                or target_identity is None
                or not _same_file_identity(staging, task_state.get("staging_file_identity"))
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "final_create_postcondition_failed"
                raise RuntimeError("final create postcondition failed")
            task_state["target_file_identity"] = target_identity
            _record_transition(
                task_state,
                transition_id="final_create",
                from_node="staged_verified",
                to_node="final_verified",
                action="exclusive_create_final",
                verification={"target": final_after_create, "staging": staging_after_final},
            )
            checkpoint()
            node = "final_verified"

        if node == "final_verified":
            # Transition 3: remove only our exact staging object, then verify both.
            if (
                _evidence(staging) != expected
                or not _same_file_identity(staging, task_state.get("staging_file_identity"))
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "staging_changed_before_cleanup"
                raise RuntimeError("staging identity changed before cleanup")
            if (
                _evidence(target) != expected
                or not _same_file_identity(target, task_state.get("target_file_identity"))
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "target_changed_before_cleanup"
                raise RuntimeError("target identity changed before cleanup")
            staging.unlink()
            staging_owned = False
            task_state["action_count"] = int(task_state["action_count"]) + 1
            final_verification = _evidence(target)
            cleanup_verification = {"staging_exists": staging.exists()}
            if (
                final_verification != expected
                or cleanup_verification["staging_exists"]
                or not _same_file_identity(target, task_state.get("target_file_identity"))
            ):
                task_state["status"] = "abstained"
                task_state["escalation_reason"] = "completion_postcondition_failed"
                raise RuntimeError("completion postcondition failed")
            _record_transition(
                task_state,
                transition_id="staging_cleanup",
                from_node="final_verified",
                to_node="completed",
                action="remove_verified_staging",
                verification={"target": final_verification, **cleanup_verification},
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
    except FileExistsError:
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "state_changed_during_exclusive_create"
    except Exception as exc:
        if task_state["status"] != "abstained":
            task_state["status"] = "failed"
            task_state["escalation_reason"] = f"runtime_error:{type(exc).__name__}"
    finally:
        if task_state["status"] != "completed":
            if staging_owned:
                rollback["staging_removed"] = _rollback_owned_file(
                    staging,
                    expected_sha,
                    task_state.get("staging_file_identity"),
                )
            if target_owned:
                rollback["target_removed"] = _rollback_owned_file(
                    target,
                    expected_sha,
                    task_state.get("target_file_identity"),
                )
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
