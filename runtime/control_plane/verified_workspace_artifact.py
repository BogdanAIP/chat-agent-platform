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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "size": None, "sha256": None}
    data = path.read_bytes()
    return {"exists": True, "size": len(data), "sha256": _sha256(data)}


def _safe_child(root: Path, child: Path) -> Path:
    root = root.resolve()
    resolved = child.resolve(strict=False)
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError("procedure path escaped its configured root")
    return resolved


def _write_checkpoint(state_root: Path, task_state: dict[str, Any]) -> None:
    state_root.mkdir(parents=True, exist_ok=True)
    task_id = str(task_state["task_id"])
    destination = _safe_child(state_root, state_root / f"{task_id}.json")
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


def _rollback_owned_file(path: Path, expected_sha256: str) -> bool:
    """Remove only an exact file created by this run.

    Changed or ambiguous content is deliberately left in place so stale evidence
    can never authorize deletion.
    """

    evidence = _evidence(path)
    if not evidence["exists"]:
        return True
    if evidence["sha256"] != expected_sha256:
        return False
    path.unlink()
    return not path.exists()


def run_verified_workspace_artifact(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    """Run one bounded three-transition qualification procedure.

    The procedure never accepts an arbitrary path or command.  It creates one
    UTF-8 artifact below a reserved workspace directory using three verified
    transitions: staging create, final exclusive create, staging cleanup.
    Existing targets cause ABSTAIN with zero mutation.
    """

    started = time.monotonic()
    workspace_root = workspace_root.resolve()
    state_root = state_root.resolve()
    if not workspace_root.is_dir():
        raise ValueError("configured workspace root is not an existing directory")
    if candidate_admission != QUALIFICATION_ADMISSION:
        raise PermissionError("candidate procedure is not admitted by this profile")
    if set(request) != {"procedure", "artifact_name", "content"}:
        raise ValueError("procedure request must contain exactly procedure, artifact_name, content")
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
    reserved_root.mkdir(parents=True, exist_ok=True)
    task_id = secrets.token_hex(16)
    target = _safe_child(reserved_root, reserved_root / artifact_name)
    staging = _safe_child(reserved_root, reserved_root / f".{artifact_name}.{task_id}.staging")
    relative_target = target.relative_to(workspace_root).as_posix()

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
        "created_at": _utc_now(),
    }

    def checkpoint() -> None:
        if task_state["action_count"] > MAX_ACTIONS:
            raise RuntimeError("action budget exceeded")
        if time.monotonic() - started > MAX_RUNTIME_SECONDS:
            raise RuntimeError("runtime budget exceeded")
        _write_checkpoint(state_root, task_state)

    checkpoint()
    if target.exists():
        task_state["status"] = "abstained"
        task_state["escalation_reason"] = "target_already_exists"
        checkpoint()
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=_evidence(target),
            rollback={"staging_removed": True, "target_removed": False},
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
        )

    staging_owned = False
    target_owned = False
    rollback = {"staging_removed": True, "target_removed": False}
    try:
        # Transition 1: exclusive staging create -> independent digest verifier.
        with staging.open("xb") as handle:
            handle.write(content_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        staging_owned = True
        task_state["action_count"] += 1
        staged = _evidence(staging)
        if staged != {"exists": True, "size": len(content_bytes), "sha256": expected_sha}:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "staging_postcondition_failed"
            raise RuntimeError("staging postcondition failed")
        _record_transition(
            task_state,
            transition_id="stage_create",
            from_node="preflight",
            to_node="staged_verified",
            action="exclusive_create_staging",
            verification=staged,
        )
        checkpoint()

        # Transition 2: exclusive final create. 'x' prevents overwrite races.
        with target.open("xb") as handle:
            handle.write(content_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        target_owned = True
        task_state["action_count"] += 1
        final_after_create = _evidence(target)
        staging_after_final = _evidence(staging)
        expected = {"exists": True, "size": len(content_bytes), "sha256": expected_sha}
        if final_after_create != expected or staging_after_final != expected:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "final_create_postcondition_failed"
            raise RuntimeError("final create postcondition failed")
        _record_transition(
            task_state,
            transition_id="final_create",
            from_node="staged_verified",
            to_node="final_verified",
            action="exclusive_create_final",
            verification={"target": final_after_create, "staging": staging_after_final},
        )
        checkpoint()

        # Transition 3: remove only our exact staging artifact, then verify both.
        if _evidence(staging)["sha256"] != expected_sha:
            task_state["status"] = "abstained"
            task_state["escalation_reason"] = "staging_changed_before_cleanup"
            raise RuntimeError("staging identity changed before cleanup")
        staging.unlink()
        staging_owned = False
        task_state["action_count"] += 1
        final_verification = _evidence(target)
        cleanup_verification = {"staging_exists": staging.exists()}
        if final_verification != expected or cleanup_verification["staging_exists"]:
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
        checkpoint()
        return _result(
            task_state,
            artifact_relative_path=relative_target,
            final_verification=final_verification,
            rollback=rollback,
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
                rollback["staging_removed"] = _rollback_owned_file(staging, expected_sha)
            if target_owned:
                rollback["target_removed"] = _rollback_owned_file(target, expected_sha)
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
    )
