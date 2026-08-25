from __future__ import annotations

from typing import Any

from .browser_observation import BrowserObservationStream, canonicalize_browser_url
from .verification import (
    ExpectedEffect,
    StatePredicate,
    VerificationResult,
    verify_expected_effect,
)


NAVIGATION_EFFECT_ID = "browser.navigation.final_state"
DEFAULT_BROWSER_SUBJECT = "isolated-playwright-primary-page"


def _verification_payload(result: VerificationResult) -> dict[str, Any]:
    return {
        "effect_id": result.effect_id,
        "status": result.status.value,
        "reason": result.reason,
        "observation": result.observation.as_dict() if result.observation is not None else None,
        "evidence_batch_id": result.evidence_batch_id,
    }


def verify_navigation_transition(
    *,
    before_raw: dict[str, Any],
    after_raw: dict[str, Any],
    expected_url: str,
    subject: str = DEFAULT_BROWSER_SUBJECT,
) -> dict[str, Any]:
    """Verify one delivered browser navigation against fresh final page state.

    The caller collects both browser observations from one isolated Playwright
    session. This function owns no browser and performs no action. Redirects are
    intentionally not promoted yet: the final canonical URL must equal the
    requested canonical URL. A later reviewed redirect policy can widen this
    without weakening the current fail-closed contract.
    """

    canonical_expected, _ = canonicalize_browser_url(expected_url)
    if canonical_expected == "about:blank":
        raise ValueError("expected navigation URL must be HTTP or HTTPS")

    stream = BrowserObservationStream(subject=subject)
    before = stream.observe(before_raw)
    after = stream.observe(after_raw)
    effect = ExpectedEffect(
        effect_id=NAVIGATION_EFFECT_ID,
        before=before.ref,
        predicates=(
            StatePredicate.equals("url", expected=canonical_expected),
            StatePredicate.present("document", "snapshot_sha256"),
            StatePredicate.equals("settled", expected=True),
        ),
    )
    result = verify_expected_effect(effect, after)
    return {
        "schema_version": 1,
        "operation": "verify_navigation",
        "status": result.status.value,
        "expected_url": canonical_expected,
        "before": before.ref.as_dict(),
        "after": after.ref.as_dict(),
        "verification": _verification_payload(result),
    }
