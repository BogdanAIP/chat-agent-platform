from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.control_plane.authorization import (  # noqa: E402
    AuthorizationRequest,
    CapabilityGrant,
    authorize_request,
)
from runtime.control_plane.file_artifact_observation import (  # noqa: E402
    FILE_ARTIFACT_CAPABILITY,
    FileArtifactObservationStream,
)
from runtime.control_plane.verification import (  # noqa: E402
    ExpectedEffect,
    ObservationRef,
    StatePredicate,
    VerificationStatus,
    verify_expected_effect,
)


SCHEMA_VERSION = 1
ACTION_REF = "workspace.write"
PRINCIPAL_REF = "semantic-profile:active-caller-v1"
ACTIVATION_VERSION = "semantic-activation-v1"
MAX_REQUEST_BYTES = 64 * 1024
MAX_CONTENT_BYTES = 16 * 1024 * 1024
MAX_RELATIVE_PATH_CHARS = 2048
_ACTIVATION_RE = re.compile(r"^[0-9a-f]{32}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_COMMON = {
    "operation",
    "activation_ref",
    "workspace_root",
    "relative_path",
    "content_sha256",
    "content_size",
}
_ALLOWED_BY_OPERATION = {
    "prepare": _ALLOWED_COMMON,
    "verify": _ALLOWED_COMMON | {"before"},
}


def _error(reason: str, *, operation: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": operation or "unknown",
        "status": "error",
        "reason": reason,
    }


def _bounded_text(value: Any, *, name: str, max_chars: int) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def _canonical_workspace_root(value: Any) -> Path:
    raw = _bounded_text(value, name="workspace_root", max_chars=4096)
    root = Path(raw).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("workspace_root must be an existing directory")
    return root


def _relative_path(value: Any) -> str:
    relative = _bounded_text(
        value,
        name="relative_path",
        max_chars=MAX_RELATIVE_PATH_CHARS,
    )
    if PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).is_absolute():
        raise ValueError("relative_path must not be absolute")
    parts = tuple(part for part in relative.replace("\\", "/").split("/") if part)
    if not parts or any(part in {".", ".."} for part in parts):
        raise ValueError("relative_path contains unsupported traversal components")
    return relative


def _expected_content(value: Any, size: Any) -> tuple[str, int]:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError("content_sha256 must be a lowercase SHA-256 digest")
    if type(size) is not int or size < 0 or size > MAX_CONTENT_BYTES:
        raise ValueError("content_size is outside the bounded UTF-8 byte range")
    return value, size


def _activation_ref(value: Any) -> str:
    if type(value) is not str or _ACTIVATION_RE.fullmatch(value) is None:
        raise ValueError("activation_ref must be a 32-character lowercase hex identity")
    return value


def _canonical_json_digest(prefix: str, value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(prefix.encode("ascii") + b"\0" + payload).hexdigest()


def _resource_scope_ref(
    *,
    root: Path,
    relative_path: str,
    content_sha256: str,
    content_size: int,
) -> str:
    digest = _canonical_json_digest(
        "cap-semantic-workspace-resource-v1",
        {
            "workspace_root": str(root),
            "relative_path": relative_path.replace("\\", "/"),
            "content_sha256": content_sha256,
            "content_size": content_size,
        },
    )
    return f"semantic-workspace-resource:{digest}"


def _subject(*, activation_ref: str, resource_scope_ref: str) -> str:
    digest = _canonical_json_digest(
        "cap-semantic-workspace-subject-v1",
        {
            "activation_ref": activation_ref,
            "resource_scope_ref": resource_scope_ref,
        },
    )
    return f"semantic-workspace-write:{digest}"


def _attempt_fingerprint(
    *,
    activation_ref: str,
    resource_scope_ref: str,
    before: ObservationRef,
) -> str:
    return _canonical_json_digest(
        "cap-semantic-workspace-attempt-v1",
        {
            "activation_ref": activation_ref,
            "action_ref": ACTION_REF,
            "resource_scope_ref": resource_scope_ref,
            "before": before.as_dict(),
        },
    )


def _observer(
    *,
    root: Path,
    relative_path: str,
    subject: str,
    content_size: int,
    stream_id: str | None = None,
    initial_sequence: int = -1,
) -> FileArtifactObservationStream:
    return FileArtifactObservationStream(
        root=root,
        subject=subject,
        paths={"target": root / relative_path},
        max_bytes=max(1, content_size),
        stream_id=stream_id,
        initial_sequence=initial_sequence,
    )


def _grant_and_request(
    *,
    activation_ref: str,
    resource_scope_ref: str,
    before: ObservationRef,
) -> tuple[CapabilityGrant, AuthorizationRequest]:
    evidence_scope_ref = before.stream_id
    task_ref = f"semantic-activation:{activation_ref}"
    execution_environment_ref = f"{ACTIVATION_VERSION}:{activation_ref}"
    grant_digest = _canonical_json_digest(
        "cap-semantic-workspace-grant-v1",
        {
            "activation_ref": activation_ref,
            "resource_scope_ref": resource_scope_ref,
            "evidence_scope_ref": evidence_scope_ref,
        },
    )
    grant = CapabilityGrant(
        grant_ref=f"grant:semantic-workspace:{grant_digest}",
        task_ref=task_ref,
        principal_ref=PRINCIPAL_REF,
        capability=FILE_ARTIFACT_CAPABILITY,
        allowed_action_refs=(ACTION_REF,),
        resource_scope_ref=resource_scope_ref,
        execution_environment_ref=execution_environment_ref,
        evidence_scope_ref=evidence_scope_ref,
    )
    request = AuthorizationRequest(
        task_ref=task_ref,
        principal_ref=PRINCIPAL_REF,
        capability=FILE_ARTIFACT_CAPABILITY,
        action_ref=ACTION_REF,
        resource_scope_ref=resource_scope_ref,
        attempt_authorization_fingerprint=_attempt_fingerprint(
            activation_ref=activation_ref,
            resource_scope_ref=resource_scope_ref,
            before=before,
        ),
        execution_environment_ref=execution_environment_ref,
        evidence_scope_ref=evidence_scope_ref,
    )
    return grant, request


def _exact_target_state(
    snapshot_state: Any,
    *,
    content_sha256: str,
    content_size: int,
) -> bool:
    target = snapshot_state.get("target") if hasattr(snapshot_state, "get") else None
    if target is None or not hasattr(target, "get"):
        return False
    return (
        target.get("exists") is True
        and target.get("kind") == "file"
        and target.get("size") == content_size
        and target.get("sha256") == content_sha256
    )


def _parse_before(raw: Any) -> ObservationRef:
    if type(raw) is not dict:
        raise TypeError("before must be an observation-ref object")
    expected = {
        "capability",
        "subject",
        "stream_id",
        "sequence",
        "fingerprint",
        "observed_at",
    }
    if set(raw) != expected:
        raise ValueError("before observation-ref fields are invalid")
    return ObservationRef(
        capability=raw["capability"],
        subject=raw["subject"],
        stream_id=raw["stream_id"],
        sequence=raw["sequence"],
        fingerprint=raw["fingerprint"],
        observed_at=raw["observed_at"],
    )


def _normalized_inputs(request: dict[str, Any]) -> tuple[str, Path, str, str, int, str]:
    activation_ref = _activation_ref(request.get("activation_ref"))
    root = _canonical_workspace_root(request.get("workspace_root"))
    relative_path = _relative_path(request.get("relative_path"))
    content_sha256, content_size = _expected_content(
        request.get("content_sha256"),
        request.get("content_size"),
    )
    resource_scope_ref = _resource_scope_ref(
        root=root,
        relative_path=relative_path,
        content_sha256=content_sha256,
        content_size=content_size,
    )
    return (
        activation_ref,
        root,
        relative_path,
        content_sha256,
        content_size,
        resource_scope_ref,
    )


def prepare_workspace_write(request: dict[str, Any]) -> dict[str, Any]:
    (
        activation_ref,
        root,
        relative_path,
        content_sha256,
        content_size,
        resource_scope_ref,
    ) = _normalized_inputs(request)
    subject = _subject(
        activation_ref=activation_ref,
        resource_scope_ref=resource_scope_ref,
    )
    observer = _observer(
        root=root,
        relative_path=relative_path,
        subject=subject,
        content_size=content_size,
    )
    before = observer.observe()
    grant, authorization_request = _grant_and_request(
        activation_ref=activation_ref,
        resource_scope_ref=resource_scope_ref,
        before=before.ref,
    )
    decision = authorize_request(authorization_request, grant)
    if not decision.authorized:
        return {
            "schema_version": SCHEMA_VERSION,
            "operation": "prepare",
            "status": "blocked",
            "reason": decision.reason,
            "authorization": decision.as_dict(),
        }

    already_satisfied = (
        before.complete
        and not before.ambiguous
        and _exact_target_state(
            before.state,
            content_sha256=content_sha256,
            content_size=content_size,
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "prepare",
        "status": "authorized",
        "reason": "exact_grant_match",
        "already_satisfied": already_satisfied,
        "resource_scope_ref": resource_scope_ref,
        "authorization": decision.as_dict(),
        "before": before.ref.as_dict(),
    }


def verify_workspace_write(request: dict[str, Any]) -> dict[str, Any]:
    (
        activation_ref,
        root,
        relative_path,
        content_sha256,
        content_size,
        resource_scope_ref,
    ) = _normalized_inputs(request)
    before = _parse_before(request.get("before"))
    expected_subject = _subject(
        activation_ref=activation_ref,
        resource_scope_ref=resource_scope_ref,
    )
    if before.capability != FILE_ARTIFACT_CAPABILITY:
        raise ValueError("before observation capability mismatch")
    if before.subject != expected_subject:
        raise ValueError("before observation subject mismatch")

    grant, authorization_request = _grant_and_request(
        activation_ref=activation_ref,
        resource_scope_ref=resource_scope_ref,
        before=before,
    )
    decision = authorize_request(authorization_request, grant)
    if not decision.authorized:
        return {
            "schema_version": SCHEMA_VERSION,
            "operation": "verify",
            "status": "blocked",
            "reason": decision.reason,
            "authorization": decision.as_dict(),
        }

    observer = _observer(
        root=root,
        relative_path=relative_path,
        subject=expected_subject,
        content_size=content_size,
        stream_id=before.stream_id,
        initial_sequence=before.sequence,
    )
    after = observer.observe()
    effect = ExpectedEffect(
        effect_id="semantic.workspace_write.final_state",
        before=before,
        predicates=(
            StatePredicate.equals("target", "exists", expected=True),
            StatePredicate.equals("target", "kind", expected="file"),
            StatePredicate.equals("target", "size", expected=content_size),
            StatePredicate.equals("target", "sha256", expected=content_sha256),
        ),
    )
    verification = verify_expected_effect(effect, after)
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": "verify",
        "status": verification.status.value,
        "reason": verification.reason,
        "authorization": decision.as_dict(),
        "verification": verification.as_dict(),
    }


def handle_request(request: Any) -> dict[str, Any]:
    if type(request) is not dict:
        raise TypeError("request must be an object")
    operation = request.get("operation")
    if operation not in _ALLOWED_BY_OPERATION:
        raise ValueError("unsupported operation")
    extra = set(request) - _ALLOWED_BY_OPERATION[operation]
    if extra:
        raise ValueError(f"unsupported request fields: {sorted(extra)}")
    if operation == "prepare":
        return prepare_workspace_write(request)
    return verify_workspace_write(request)


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

    operation = request.get("operation") if type(request) is dict else None
    try:
        result = handle_request(request)
    except (TypeError, ValueError, OSError) as exc:
        result = _error(f"invalid_request:{exc}", operation=operation)
    except Exception as exc:
        result = _error(
            f"runtime_unavailable:{type(exc).__name__}",
            operation=operation,
        )

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") in {
        "authorized",
        "blocked",
        VerificationStatus.PASS.value,
        VerificationStatus.FAIL.value,
        VerificationStatus.UNKNOWN.value,
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
