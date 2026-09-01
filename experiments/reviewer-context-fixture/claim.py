from __future__ import annotations


def claim_send(*, quota_remaining: int) -> bool:
    """Return whether one outbound send may be performed."""

    return quota_remaining > 0
