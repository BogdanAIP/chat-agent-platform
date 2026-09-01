from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from runtime.control_plane.delegation_state import DelegationStateError


ADAPTER_ID = "chatgpt-temporary"
RUNTIME_ASSETS = (
    "manifest.json",
    "policy.js",
    "background.js",
    "content.js",
)

_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_KEYS = {"schema_version", "adapter_id", "expected_head", "assets"}
_REPORT_KEYS = {"schema_version", "adapter_id", "assets"}


@dataclass(frozen=True)
class ExpectedRuntimeAttestation:
    expected_head: str
    assets: dict[str, str]


def _plain(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise DelegationStateError(f"{label} must be a plain object")
    return value


def _exact(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise DelegationStateError(
            f"{label} keys mismatch: missing={sorted(expected - actual) or 'none'} "
            f"unexpected={sorted(actual - expected) or 'none'}"
        )


def _parse_assets(value: Any, label: str) -> dict[str, str]:
    assets = _plain(value, f"{label} assets")
    expected_names = set(RUNTIME_ASSETS)
    _exact(assets, expected_names, f"{label} assets")
    parsed: dict[str, str] = {}
    for name in RUNTIME_ASSETS:
        digest = assets[name]
        if type(digest) is not str or _HEX64_RE.fullmatch(digest) is None:
            raise DelegationStateError(f"{label} asset digest is invalid: {name}")
        parsed[name] = digest
    return parsed


def parse_expected_runtime_attestation(value: Mapping[str, Any]) -> ExpectedRuntimeAttestation:
    expected = _plain(value, "expected runtime attestation")
    _exact(expected, _EXPECTED_KEYS, "expected runtime attestation")
    if expected["schema_version"] != 1 or expected["adapter_id"] != ADAPTER_ID:
        raise DelegationStateError("expected runtime attestation schema or adapter mismatch")
    head = expected["expected_head"]
    if type(head) is not str or _HEX40_RE.fullmatch(head) is None:
        raise DelegationStateError("expected runtime attestation head is invalid")
    return ExpectedRuntimeAttestation(
        expected_head=head,
        assets=_parse_assets(expected["assets"], "expected runtime attestation"),
    )


def validate_runtime_attestation(
    value: Mapping[str, Any],
    *,
    expected: ExpectedRuntimeAttestation,
) -> str:
    report = _plain(value, "runtime attestation")
    _exact(report, _REPORT_KEYS, "runtime attestation")
    if report["schema_version"] != 1 or report["adapter_id"] != ADAPTER_ID:
        raise DelegationStateError("runtime attestation schema or adapter mismatch")
    assets = _parse_assets(report["assets"], "runtime attestation")
    for name in RUNTIME_ASSETS:
        if not hmac.compare_digest(assets[name], expected.assets[name]):
            raise DelegationStateError(f"runtime attestation mismatch: {name}")
    canonical = json.dumps(
        {
            "schema_version": 1,
            "adapter_id": ADAPTER_ID,
            "expected_head": expected.expected_head,
            "assets": assets,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
