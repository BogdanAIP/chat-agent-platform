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
INTERACTION_EFFECT_ID = "browser.interaction.final_state"
DEFAULT_BROWSER_SUBJECT = "isolated-playwright-primary-page"
MAX_EXPECTED_CONTROL_ID_CHARS = 512
MAX_EXPECTED_CONTROL_VALUE_CHARS = 4096

_ALLOWED_INTERACTION_EXPECTED = {"url", "control"}
_ALLOWED_CONTROL_EXPECTED = {
    "control_id",
    "present",
    "value",
    "checked",
    "selected",
    "enabled",
}


def _verification_payload(result: VerificationResult) -> dict[str, Any]:
    return {
        "effect_id": result.effect_id,
        "status": result.status.value,
        "reason": result.reason,
        "observation": result.observation.as_dict() if result.observation is not None else None,
        "evidence_batch_id": result.evidence_batch_id,
    }


def _bounded_text(value: Any, *, name: str, max_chars: int, allow_empty: bool = False) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def _normalize_interaction_expected(raw: Any) -> tuple[dict[str, Any], tuple[StatePredicate, ...]]:
    """Validate one bounded declarative interaction postcondition.

    This deliberately does not support arbitrary expressions, selectors,
    JavaScript or "page changed" heuristics. The caller must name a concrete
    observable result: final URL and/or one control-ref state.
    """

    if type(raw) is not dict:
        raise TypeError("interaction expected must be a plain dict")
    extra = set(raw) - _ALLOWED_INTERACTION_EXPECTED
    if extra:
        raise ValueError(f"interaction expected contains unsupported fields: {sorted(extra)}")
    if not raw:
        raise ValueError("interaction expected requires at least one postcondition")

    normalized: dict[str, Any] = {}
    predicates: list[StatePredicate] = []

    if "url" in raw:
        expected_url = _bounded_text(raw["url"], name="interaction expected url", max_chars=4096)
        canonical_url, _ = canonicalize_browser_url(expected_url)
        if canonical_url == "about:blank":
            raise ValueError("interaction expected url must be HTTP or HTTPS")
        normalized["url"] = canonical_url
        predicates.append(StatePredicate.equals("url", expected=canonical_url))

    if "control" in raw:
        control = raw["control"]
        if type(control) is not dict:
            raise TypeError("interaction expected control must be a plain dict")
        extra_control = set(control) - _ALLOWED_CONTROL_EXPECTED
        if extra_control:
            raise ValueError(
                f"interaction expected control contains unsupported fields: {sorted(extra_control)}"
            )
        if "control_id" not in control:
            raise ValueError("interaction expected control requires control_id")
        control_id = _bounded_text(
            control["control_id"],
            name="interaction expected control_id",
            max_chars=MAX_EXPECTED_CONTROL_ID_CHARS,
        )

        state_fields = tuple(
            field for field in ("value", "checked", "selected", "enabled") if field in control
        )
        present = control.get("present")
        if present is not None and type(present) is not bool:
            raise TypeError("interaction expected control present must be bool")
        if present is False and state_fields:
            raise ValueError("absent control cannot also declare value/checked/selected/enabled")
        if present is None and not state_fields:
            raise ValueError("interaction expected control requires present or one state field")

        normalized_control: dict[str, Any] = {"control_id": control_id}
        if present is not None:
            normalized_control["present"] = present
            predicates.append(
                StatePredicate.present("controls", control_id)
                if present
                else StatePredicate.absent("controls", control_id)
            )
        elif state_fields:
            # State equality is meaningful only if the same bound control-ref is
            # still present in the fresh post-action observation.
            predicates.append(StatePredicate.present("controls", control_id))

        for field in state_fields:
            value = control[field]
            if field == "value":
                value = _bounded_text(
                    value,
                    name="interaction expected control value",
                    max_chars=MAX_EXPECTED_CONTROL_VALUE_CHARS,
                    allow_empty=True,
                )
            elif type(value) is not bool:
                raise TypeError(f"interaction expected control {field} must be bool")
            normalized_control[field] = value
            predicates.append(
                StatePredicate.equals("controls", control_id, field, expected=value)
            )

        normalized["control"] = normalized_control

    if not predicates:
        raise ValueError("interaction expected produced no verifiable predicates")

    # A complete Playwright snapshot should represent a settled state before we
    # accept any declared interaction postcondition.
    predicates.append(StatePredicate.equals("settled", expected=True))
    return normalized, tuple(predicates)


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


def verify_interaction_transition(
    *,
    before_raw: dict[str, Any],
    after_raw: dict[str, Any],
    expected: dict[str, Any],
    subject: str = DEFAULT_BROWSER_SUBJECT,
) -> dict[str, Any]:
    """Verify a delivered browser interaction against declared fresh state.

    The verifier never guesses intent from generic DOM/page change. The caller
    supplies a small declarative expected result (URL and/or one control state),
    while this module binds it to a concrete before observation and evaluates it
    against a strictly newer observation from the same stream.
    """

    normalized_expected, predicates = _normalize_interaction_expected(expected)
    stream = BrowserObservationStream(subject=subject)
    before = stream.observe(before_raw)
    after = stream.observe(after_raw)
    effect = ExpectedEffect(
        effect_id=INTERACTION_EFFECT_ID,
        before=before.ref,
        predicates=predicates,
    )
    result = verify_expected_effect(effect, after)
    return {
        "schema_version": 1,
        "operation": "verify_interaction",
        "status": result.status.value,
        "expected": normalized_expected,
        "before": before.ref.as_dict(),
        "after": after.ref.as_dict(),
        "verification": _verification_payload(result),
    }
