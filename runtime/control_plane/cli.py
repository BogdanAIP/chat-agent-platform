from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.control_plane.verified_workspace_artifact import (  # noqa: E402
    PROCEDURE_ID as WORKSPACE_ARTIFACT_PROCEDURE_ID,
    run_verified_workspace_artifact,
)
from runtime.control_plane.windows_case_update import (  # noqa: E402
    PROCEDURE_ID as WINDOWS_CASE_PROCEDURE_ID,
    run_windows_case_update,
)


MAX_REQUEST_BYTES = 32_768


def _error(reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "error",
        "reason": reason,
        "action_count": 0,
    }


def _dispatch_registered_procedure(
    request: dict[str, Any],
    *,
    workspace_root: Path,
    state_root: Path,
    candidate_admission: str | None,
) -> dict[str, Any]:
    procedure = request.get("procedure")
    if procedure == WORKSPACE_ARTIFACT_PROCEDURE_ID:
        return run_verified_workspace_artifact(
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
    return 0 if result.get("status") in {"completed", "abstained"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
