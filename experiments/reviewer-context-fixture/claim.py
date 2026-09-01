from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClaimResult:
    granted: bool
    reason: str


def claim_send(*, quota_remaining: int) -> ClaimResult:
    """Return structured claim evidence for one outbound send attempt."""

    if quota_remaining > 0:
        return ClaimResult(granted=True, reason="granted")
    return ClaimResult(granted=False, reason="quota_exhausted")
