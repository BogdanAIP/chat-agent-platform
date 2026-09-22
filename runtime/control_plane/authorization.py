from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


_MAX_REF_CHARS = 512
_MAX_ACTIONS = 64
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _ref(value: Any, *, name: str, optional: bool = False) -> str | None:
    if value is None:
        if optional:
            return None
        raise TypeError(f"{name} must be a string")
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must be non-empty")
    if len(value) > _MAX_REF_CHARS:
        raise ValueError(f"{name} exceeds {_MAX_REF_CHARS} characters")
    return value


def _optional_ref(value: Any, *, name: str) -> str | None:
    return _ref(value, name=name, optional=True)


def _actions(value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError("allowed_action_refs must be a tuple")
    if not value:
        raise ValueError("allowed_action_refs must be non-empty")
    if len(value) > _MAX_ACTIONS:
        raise ValueError(f"allowed_action_refs exceeds {_MAX_ACTIONS} entries")
    normalized = tuple(_ref(item, name="allowed action ref") for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("allowed_action_refs must not contain duplicates")
    return tuple(sorted(normalized))


def _fingerprint(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(prefix.encode("ascii") + b"\0" + encoded).hexdigest()


class AuthorizationStatus(StrEnum):
    AUTHORIZED = "authorized"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    """Provider-neutral exact-match authority admitted by trusted CAP policy.

    Capability adapters define the semantic action/resource identifiers. Core
    deliberately does not parse provider paths, selectors, HWNDs, URLs or OAuth
    scopes.
    """

    grant_ref: str
    task_ref: str
    principal_ref: str
    capability: str
    allowed_action_refs: tuple[str, ...]
    resource_scope_ref: str
    delegation_ref: str | None = None
    execution_environment_ref: str | None = None
    evidence_scope_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "grant_ref", _ref(self.grant_ref, name="grant_ref"))
        object.__setattr__(self, "task_ref", _ref(self.task_ref, name="task_ref"))
        object.__setattr__(self, "principal_ref", _ref(self.principal_ref, name="principal_ref"))
        object.__setattr__(self, "capability", _ref(self.capability, name="capability"))
        object.__setattr__(self, "allowed_action_refs", _actions(self.allowed_action_refs))
        object.__setattr__(
            self,
            "resource_scope_ref",
            _ref(self.resource_scope_ref, name="resource_scope_ref"),
        )
        for name in (
            "delegation_ref",
            "execution_environment_ref",
            "evidence_scope_ref",
        ):
            object.__setattr__(
                self,
                name,
                _optional_ref(getattr(self, name), name=name),
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "grant_ref": self.grant_ref,
            "task_ref": self.task_ref,
            "principal_ref": self.principal_ref,
            "capability": self.capability,
            "allowed_action_refs": list(self.allowed_action_refs),
            "resource_scope_ref": self.resource_scope_ref,
            "delegation_ref": self.delegation_ref,
            "execution_environment_ref": self.execution_environment_ref,
            "evidence_scope_ref": self.evidence_scope_ref,
        }

    @property
    def fingerprint(self) -> str:
        return _fingerprint("cap-capability-grant-v1", self.as_dict())


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    """One exact action/resource/context request bound to one AttemptIntent."""

    task_ref: str
    principal_ref: str
    capability: str
    action_ref: str
    resource_scope_ref: str
    attempt_authorization_fingerprint: str
    delegation_ref: str | None = None
    execution_environment_ref: str | None = None
    evidence_scope_ref: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "task_ref",
            "principal_ref",
            "capability",
            "action_ref",
            "resource_scope_ref",
        ):
            object.__setattr__(self, name, _ref(getattr(self, name), name=name))
        if (
            type(self.attempt_authorization_fingerprint) is not str
            or _SHA256_RE.fullmatch(self.attempt_authorization_fingerprint) is None
        ):
            raise ValueError(
                "attempt_authorization_fingerprint must be a lowercase SHA-256 digest"
            )
        for name in (
            "delegation_ref",
            "execution_environment_ref",
            "evidence_scope_ref",
        ):
            object.__setattr__(
                self,
                name,
                _optional_ref(getattr(self, name), name=name),
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_ref": self.task_ref,
            "principal_ref": self.principal_ref,
            "capability": self.capability,
            "action_ref": self.action_ref,
            "resource_scope_ref": self.resource_scope_ref,
            "attempt_authorization_fingerprint": self.attempt_authorization_fingerprint,
            "delegation_ref": self.delegation_ref,
            "execution_environment_ref": self.execution_environment_ref,
            "evidence_scope_ref": self.evidence_scope_ref,
        }

    @property
    def fingerprint(self) -> str:
        return _fingerprint("cap-authorization-request-v1", self.as_dict())


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    status: AuthorizationStatus
    reason: str
    grant_ref: str | None
    grant_fingerprint: str | None
    request_fingerprint: str
    attempt_authorization_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, AuthorizationStatus):
            raise TypeError("authorization status must be AuthorizationStatus")
        _ref(self.reason, name="authorization reason")
        if self.grant_ref is not None:
            _ref(self.grant_ref, name="grant_ref")
        for name in (
            "grant_fingerprint",
            "request_fingerprint",
            "attempt_authorization_fingerprint",
        ):
            value = getattr(self, name)
            if value is None and name == "grant_fingerprint":
                continue
            if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        if self.status is AuthorizationStatus.AUTHORIZED:
            if self.grant_ref is None or self.grant_fingerprint is None:
                raise ValueError("authorized decision requires exact grant identity")

    @property
    def authorized(self) -> bool:
        return self.status is AuthorizationStatus.AUTHORIZED

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "grant_ref": self.grant_ref,
            "grant_fingerprint": self.grant_fingerprint,
            "request_fingerprint": self.request_fingerprint,
            "attempt_authorization_fingerprint": self.attempt_authorization_fingerprint,
        }


def _decision(
    request: AuthorizationRequest,
    *,
    status: AuthorizationStatus,
    reason: str,
    grant: CapabilityGrant | None,
) -> AuthorizationDecision:
    return AuthorizationDecision(
        status=status,
        reason=reason,
        grant_ref=grant.grant_ref if grant is not None else None,
        grant_fingerprint=grant.fingerprint if grant is not None else None,
        request_fingerprint=request.fingerprint,
        attempt_authorization_fingerprint=request.attempt_authorization_fingerprint,
    )


def authorize_request(
    request: AuthorizationRequest,
    grant: CapabilityGrant | None,
) -> AuthorizationDecision:
    """Evaluate one exact bounded grant without provider-specific policy logic."""

    if not isinstance(request, AuthorizationRequest):
        raise TypeError("request must be AuthorizationRequest")
    if grant is not None and not isinstance(grant, CapabilityGrant):
        raise TypeError("grant must be CapabilityGrant or None")

    if grant is None:
        return _decision(
            request,
            status=AuthorizationStatus.BLOCKED,
            reason="grant_missing",
            grant=None,
        )

    checks = (
        ("task_ref", request.task_ref, grant.task_ref),
        ("principal_ref", request.principal_ref, grant.principal_ref),
        ("capability", request.capability, grant.capability),
        ("resource_scope_ref", request.resource_scope_ref, grant.resource_scope_ref),
        ("delegation_ref", request.delegation_ref, grant.delegation_ref),
        (
            "execution_environment_ref",
            request.execution_environment_ref,
            grant.execution_environment_ref,
        ),
        ("evidence_scope_ref", request.evidence_scope_ref, grant.evidence_scope_ref),
    )
    for name, requested, admitted in checks:
        if requested != admitted:
            return _decision(
                request,
                status=AuthorizationStatus.BLOCKED,
                reason=f"{name}_mismatch",
                grant=grant,
            )

    if request.action_ref not in grant.allowed_action_refs:
        return _decision(
            request,
            status=AuthorizationStatus.BLOCKED,
            reason="action_not_granted",
            grant=grant,
        )

    return _decision(
        request,
        status=AuthorizationStatus.AUTHORIZED,
        reason="exact_grant_match",
        grant=grant,
    )
