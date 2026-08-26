from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.control_plane.browser_transition import (  # noqa: E402
    verify_interaction_transition,
    verify_navigation_transition,
)


MAX_REQUEST_BYTES = 2_400_000


def _error(reason: str, *, operation: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "operation": operation or "unknown",
        "status": "error",
        "reason": reason,
    }


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
    if type(request) is not dict:
        print(json.dumps(_error("request_must_be_object"), sort_keys=True))
        return 2

    operation = request.get("operation")
    if type(operation) is not str:
        print(json.dumps(_error("operation_must_be_string"), sort_keys=True))
        return 2
    if operation not in {"verify_navigation", "verify_interaction"}:
        print(json.dumps(_error("unsupported_operation", operation=operation), sort_keys=True))
        return 2

    common_allowed = {"operation", "subject", "before", "after"}
    operation_allowed = {
        "verify_navigation": common_allowed | {"expected_url"},
        "verify_interaction": common_allowed | {"expected"},
    }[operation]
    if set(request) - operation_allowed:
        print(json.dumps(_error("unsupported_request_fields", operation=operation), sort_keys=True))
        return 2
    if type(request.get("before")) is not dict or type(request.get("after")) is not dict:
        print(json.dumps(_error("before_after_must_be_objects", operation=operation), sort_keys=True))
        return 2

    subject = request.get("subject")
    if subject is not None and type(subject) is not str:
        print(json.dumps(_error("subject_must_be_string", operation=operation), sort_keys=True))
        return 2

    try:
        if operation == "verify_navigation":
            if type(request.get("expected_url")) is not str:
                print(json.dumps(_error("expected_url_must_be_string", operation=operation), sort_keys=True))
                return 2
            result = verify_navigation_transition(
                before_raw=request["before"],
                after_raw=request["after"],
                expected_url=request["expected_url"],
                **({"subject": subject} if subject is not None else {}),
            )
        else:
            if type(request.get("expected")) is not dict:
                print(json.dumps(_error("expected_must_be_object", operation=operation), sort_keys=True))
                return 2
            result = verify_interaction_transition(
                before_raw=request["before"],
                after_raw=request["after"],
                expected=request["expected"],
                **({"subject": subject} if subject is not None else {}),
            )
    except (TypeError, ValueError) as exc:
        result = _error(f"invalid_request:{exc}", operation=operation)
    except Exception as exc:
        result = _error(f"runtime_unavailable:{type(exc).__name__}", operation=operation)

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {"pass", "fail", "unknown"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
