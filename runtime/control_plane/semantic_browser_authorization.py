from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any


REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.control_plane.authorization import (  # noqa: E402
    AuthorizationRequest,
    CapabilityGrant,
    authorize_request,
)


SCHEMA_VERSION = 1
CAPABILITY = "browser.semantic"
PRINCIPAL_REF = "semantic-profile:active-caller-v1"
ACTIVATION_VERSION = "semantic-activation-v1"
BROWSER_POLICY_REF = "isolated-playwright-public-http-loopback-v1"
_ALLOWED_ACTIONS = {
    "browser.navigate",
    "browser.click",
    "browser.type",
}
_ACTIVATION_RE = re.compile(r"^[0-9a-f]{32}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_REQUEST_BYTES = 256 * 1024
MAX_RESOURCE_JSON_BYTES = 220 * 1024


def _error(reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "error",
        "reason": reason,
    }


def _require_text(
    value: Any,
    *,
    name: str,
    max_chars: int,
) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def _activation_ref(value: Any) -> str:
    if type(value) is not str or _ACTIVATION_RE.fullmatch(value) is None:
        raise ValueError("activation_ref must be a 32-character lowercase hex identity")
    return value


def _sha256(value: Any, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _canonical_json(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ValueError("resource payload must be bounded plain JSON") from exc
    if len(encoded) > MAX_RESOURCE_JSON_BYTES:
        raise ValueError("resource payload exceeds bounded JSON size")
    return encoded


def _fingerprint(prefix: str, value: Any) -> str:
    return hashlib.sha256(
        prefix.encode("ascii") + b"\0" + _canonical_json(value)
    ).hexdigest()


def authorize_browser_request(request: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "activation_ref",
        "browser_policy_ref",
        "action_ref",
        "before_fingerprint",
        "resource",
    }
    extra = set(request) - allowed
    missing = allowed - set(request)
    if extra:
        raise ValueError(f"unsupported request fields: {sorted(extra)}")
    if missing:
        raise ValueError(f"missing request fields: {sorted(missing)}")

    activation_ref = _activation_ref(request["activation_ref"])
    browser_policy_ref = _require_text(
        request["browser_policy_ref"],
        name="browser_policy_ref",
        max_chars=256,
    )
    if browser_policy_ref != BROWSER_POLICY_REF:
        raise ValueError("browser policy ref mismatch")

    action_ref = _require_text(
        request["action_ref"],
        name="action_ref",
        max_chars=128,
    )
    if action_ref not in _ALLOWED_ACTIONS:
        raise ValueError("unsupported browser action_ref")

    before_fingerprint = _sha256(
        request["before_fingerprint"],
        name="before_fingerprint",
    )
    resource = request["resource"]
    if type(resource) is not dict:
        raise TypeError("resource must be a plain object")
    resource_bytes = _canonical_json(resource)
    resource_scope_ref = "semantic-browser-resource:" + hashlib.sha256(
        b"cap-semantic-browser-resource-v1\0" + resource_bytes
    ).hexdigest()

    task_ref = f"semantic-activation:{activation_ref}"
    execution_environment_ref = (
        f"{ACTIVATION_VERSION}:{activation_ref}:{browser_policy_ref}"
    )
    evidence_scope_ref = f"browser-before:{before_fingerprint}"

    grant_digest = _fingerprint(
        "cap-semantic-browser-grant-v1",
        {
            "activation_ref": activation_ref,
            "browser_policy_ref": browser_policy_ref,
            "action_ref": action_ref,
            "resource_scope_ref": resource_scope_ref,
            "before_fingerprint": before_fingerprint,
        },
    )
    attempt_fingerprint = _fingerprint(
        "cap-semantic-browser-attempt-v1",
        {
            "activation_ref": activation_ref,
            "browser_policy_ref": browser_policy_ref,
            "action_ref": action_ref,
            "resource_scope_ref": resource_scope_ref,
            "before_fingerprint": before_fingerprint,
        },
    )

    grant = CapabilityGrant(
        grant_ref=f"grant:semantic-browser:{grant_digest}",
        task_ref=task_ref,
        principal_ref=PRINCIPAL_REF,
        capability=CAPABILITY,
        allowed_action_refs=(action_ref,),
        resource_scope_ref=resource_scope_ref,
        execution_environment_ref=execution_environment_ref,
        evidence_scope_ref=evidence_scope_ref,
    )
    authorization_request = AuthorizationRequest(
        task_ref=task_ref,
        principal_ref=PRINCIPAL_REF,
        capability=CAPABILITY,
        action_ref=action_ref,
        resource_scope_ref=resource_scope_ref,
        attempt_authorization_fingerprint=attempt_fingerprint,
        execution_environment_ref=execution_environment_ref,
        evidence_scope_ref=evidence_scope_ref,
    )
    decision = authorize_request(authorization_request, grant)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": decision.status.value,
        "reason": decision.reason,
        "action_ref": action_ref,
        "resource_scope_ref": resource_scope_ref,
        "before_fingerprint": before_fingerprint,
        "authorization": decision.as_dict(),
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
    try:
        if type(request) is not dict:
            raise TypeError("request must be an object")
        result = authorize_browser_request(request)
    except (TypeError, ValueError) as exc:
        result = _error(f"invalid_request:{exc}")
    except Exception as exc:
        result = _error(f"runtime_unavailable:{type(exc).__name__}")

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {"authorized", "blocked"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
