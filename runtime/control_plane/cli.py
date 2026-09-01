from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.control_plane import verified_workspace_artifact as workspace_artifact  # noqa: E402
from runtime.control_plane.independent_review_procedures import (  # noqa: E402
    LAUNCH_PROCEDURE_ID as REVIEW_LAUNCH_PROCEDURE_ID,
    RECONCILE_PROCEDURE_ID as REVIEW_RECONCILE_PROCEDURE_ID,
    SUBMIT_PROCEDURE_ID as REVIEW_SUBMIT_PROCEDURE_ID,
    run_launch_independent_review,
    run_reconcile_independent_review_result,
    run_submit_independent_review_result,
)
from runtime.control_plane.independent_review_state import (  # noqa: E402
    MAX_RESULT_BYTES,
    STATE_DIRECTORY as REVIEW_STATE_DIRECTORY,
)
from runtime.control_plane.windows_case_update import (  # noqa: E402
    PROCEDURE_ID as WINDOWS_CASE_PROCEDURE_ID,
    run_windows_case_update,
)


WORKSPACE_ARTIFACT_PROCEDURE_ID = workspace_artifact.PROCEDURE_ID
# A valid decoded review result may expand by up to six times when represented
# as JSON because ASCII control bytes become \u00XX escapes. Keep the stdin
# transport bound coherent with the accepted result/state bound while remaining
# finite before json.loads allocates an unbounded request.
MAX_REQUEST_BYTES = MAX_RESULT_BYTES * 6 + 65_536
_ASSIGNED_TASK_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_MIN_WORKSPACE_PYTHON = (3, 12)
_REVIEW_PROCEDURE_IDS = {
    REVIEW_LAUNCH_PROCEDURE_ID,
    REVIEW_SUBMIT_PROCEDURE_ID,
    REVIEW_RECONCILE_PROCEDURE_ID,
}
_SUCCESS_STATUSES = {
    "completed",
    "abstained",
    "recorded",
    "already_recorded",
    "pending",
    "manual_recovery_required",
}


def _error(reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "error",
        "reason": reason,
        "action_count": 0,
    }


def _require_workspace_python() -> None:
    # Schema-2 restart identity relies on st_birthtime_ns, which is available on
    # the supported Windows path in CPython 3.12+. Reject an incompatible
    # interpreter before the procedure can create durable state or a file effect.
    if sys.version_info < _MIN_WORKSPACE_PYTHON:
        raise RuntimeError("workspace procedure requires Python 3.12 or newer")


def _require_private_review_state_root(
    procedure: Any,
    *,
    workspace_root: Path,
    state_root: Path,
) -> None:
    """Keep the private review capability path-disjoint from the readable workspace."""

    if procedure not in _REVIEW_PROCEDURE_IDS:
        return
    resolved_workspace = workspace_root.resolve()
    resolved_review_root = (state_root.resolve() / REVIEW_STATE_DIRECTORY).resolve()
    if (
        resolved_review_root == resolved_workspace
        or resolved_review_root.is_relative_to(resolved_workspace)
        or resolved_workspace.is_relative_to(resolved_review_root)
    ):
        raise ValueError(
            "independent-review state directory must be path-disjoint from the readable workspace"
        )


class _AssignedTaskIdSecrets:
    """Narrow one-shot adapter for the built-in procedure's existing id source.

    The semantic parent owns new-run correlation and passes the chosen id through
    a private environment variable.  This child process handles exactly one
    request, so replacing the procedure module's local `secrets` reference is
    bounded to this dispatch and is always restored before the CLI exits.
    """

    def __init__(self, delegate: Any, task_id: str) -> None:
        self._delegate = delegate
        self._task_id = task_id
        self._used = False

    def token_hex(self, nbytes: int | None = None) -> str:
        if nbytes == 16:
            if self._used:
                raise RuntimeError("assigned procedure task id requested more than once")
            self._used = True
            return self._task_id
        return self._delegate.token_hex(nbytes)


class _AssignedTaskIdLockGuard:
    """Bind new-task durable ownership to the procedure's existing task lock."""

    def __init__(self, delegate: Any, task_id: str) -> None:
        self._delegate = delegate
        self._task_id = task_id

    def __call__(self, state_root: Path, task_id: str) -> Any:
        task_lock = self._delegate(state_root, task_id)
        try:
            if task_id != self._task_id:
                raise RuntimeError("workspace procedure requested an unexpected assigned task id")
            if (state_root / f"{task_id}.json").exists():
                raise ValueError("assigned task id already has durable procedure state")
            return task_lock
        except Exception:
            task_lock.close()
            raise


def _run_workspace_artifact(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    _require_workspace_python()

    assigned_task_id = os.environ.get("CHAT_PROCEDURE_ASSIGNED_TASK_ID")
    if assigned_task_id is None:
        return workspace_artifact.run_verified_workspace_artifact(
            request,
            workspace_root=workspace_root,
            state_root=state_root,
            candidate_admission=candidate_admission,
        )

    if request.get("resume_task_id") is not None:
        raise ValueError("assigned task id is only valid for a new procedure run")
    if _ASSIGNED_TASK_ID_RE.fullmatch(assigned_task_id) is None:
        raise ValueError("assigned task id must be a 32-character lowercase hex task id")
    if (state_root / f"{assigned_task_id}.json").exists():
        raise ValueError("assigned task id already has durable procedure state")

    original_secrets = workspace_artifact.secrets
    original_acquire_task_lock = workspace_artifact._acquire_task_lock
    workspace_artifact.secrets = _AssignedTaskIdSecrets(original_secrets, assigned_task_id)
    workspace_artifact._acquire_task_lock = _AssignedTaskIdLockGuard(
        original_acquire_task_lock,
        assigned_task_id,
    )
    try:
        result = workspace_artifact.run_verified_workspace_artifact(
            request,
            workspace_root=workspace_root,
            state_root=state_root,
            candidate_admission=candidate_admission,
        )
    finally:
        workspace_artifact._acquire_task_lock = original_acquire_task_lock
        workspace_artifact.secrets = original_secrets

    if result.get("task_id") != assigned_task_id:
        raise RuntimeError("workspace procedure did not retain parent-assigned task id")
    return result


def _dispatch_registered_procedure(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    procedure = request.get("procedure")
    _require_private_review_state_root(
        procedure,
        workspace_root=workspace_root,
        state_root=state_root,
    )
    if procedure == WORKSPACE_ARTIFACT_PROCEDURE_ID:
        return _run_workspace_artifact(
            request,
            workspace_root=workspace_root,
            state_root=state_root,
            candidate_admission=candidate_admission,
        )
    if procedure == WINDOWS_CASE_PROCEDURE_ID:
        return run_windows_case_update(
            request,
            workspace_root=workspace_root,
            state_root=state_root,
            candidate_admission=candidate_admission,
        )
    if procedure == REVIEW_LAUNCH_PROCEDURE_ID:
        return run_launch_independent_review(request, state_root=state_root)
    if procedure == REVIEW_SUBMIT_PROCEDURE_ID:
        return run_submit_independent_review_result(request, state_root=state_root)
    if procedure == REVIEW_RECONCILE_PROCEDURE_ID:
        return run_reconcile_independent_review_result(request, state_root=state_root)
    raise ValueError("unknown or unregistered procedure")


def main() -> int:
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        print(json.dumps(_error("request_too_large"), sort_keys=True))
        return 2
    try:
        request = json.loads(raw.decode("utf-8"))
    except Exception:
        print(json.dumps(_error("invalid_json"), sort_keys=True))
        return 2
    if not isinstance(request, dict):
        print(json.dumps(_error("request_must_be_object"), sort_keys=True))
        return 2

    workspace = os.environ.get("CHAT_LOCAL_FILES_ROOT")
    state_root = os.environ.get("CHAT_PROCEDURE_STATE_ROOT")
    admission = os.environ.get("CHAT_PROCEDURE_ALLOW_CANDIDATE")
    if not workspace or not state_root:
        print(json.dumps(_error("procedure_runtime_not_configured"), sort_keys=True))
        return 2

    try:
        result = _dispatch_registered_procedure(
            request,
            workspace_root=Path(workspace),
            state_root=Path(state_root),
            candidate_admission=admission,
        )
    except PermissionError:
        result = _error("candidate_not_admitted")
    except ValueError as exc:
        result = _error(f"invalid_request:{exc}")
    except Exception as exc:
        result = _error(f"runtime_unavailable:{type(exc).__name__}")

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in _SUCCESS_STATUSES else 2


if __name__ == "__main__":
    raise SystemExit(main())
