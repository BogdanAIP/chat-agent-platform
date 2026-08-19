from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol


class VerificationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VerificationResult:
    """Non-authorizing evidence about an observed postcondition."""

    status: VerificationStatus
    reason: str
    evidence: Mapping[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status is VerificationStatus.PASS


class Verifier(Protocol):
    """A verifier observes evidence; it never authorizes an action."""

    def verify(
        self,
        *,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
        expectation: Mapping[str, Any],
    ) -> VerificationResult: ...


def verify_expected_fields(
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    expectation: Mapping[str, Any],
) -> VerificationResult:
    """Verify explicit top-level postcondition fields.

    This deliberately small baseline does not infer user intent, authorize
    actions, or treat delivery receipts as completion.  Missing evidence is
    UNKNOWN; contradictory observed evidence is FAIL; exact observed matches
    are PASS.
    """

    del before  # Reserved for richer effect verifiers; never used as authority.

    if not expectation:
        return VerificationResult(
            VerificationStatus.UNKNOWN,
            "no explicit postcondition was supplied",
        )

    missing = sorted(key for key in expectation if key not in after)
    if missing:
        return VerificationResult(
            VerificationStatus.UNKNOWN,
            "required postcondition evidence is missing",
            {"missing_fields": missing},
        )

    mismatches = {
        key: {"expected": expected, "observed": after.get(key)}
        for key, expected in expectation.items()
        if after.get(key) != expected
    }
    if mismatches:
        return VerificationResult(
            VerificationStatus.FAIL,
            "observed postcondition contradicts expectation",
            {"mismatches": mismatches},
        )

    return VerificationResult(
        VerificationStatus.PASS,
        "explicit postcondition fields match current observation",
        {"verified_fields": sorted(expectation)},
    )
