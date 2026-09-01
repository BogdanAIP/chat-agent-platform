from __future__ import annotations

from .claim import claim_send


def dispatch_once(*, quota_remaining: int, send) -> bool:
    """Perform at most one send when the claim is granted."""

    if claim_send(quota_remaining=quota_remaining):
        send()
        return True
    return False
