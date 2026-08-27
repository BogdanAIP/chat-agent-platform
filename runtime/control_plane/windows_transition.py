from __future__ import annotations

from datetime import datetime
from typing import Any

from .verification import (
    ExpectedEffect,
    StatePredicate,
    VerificationResult,
    VerificationStatus,
    verify_expected_effect,
)
from .windows_observation import WindowsDesktopObservationStream


WINDOWS_DESKTOP_EFFECT_ID = "windows.desktop.final_state"
DEFAULT_WINDOWS_SUBJECT = "bound-windows-application"

_IDENTITY_CONTINUITY_PATHS = (
    ("identity", "session_id"),
    ("identity", "application_identity"),
    ("identity", "executable_name"),
    ("identity", "process_id"),
    ("identity", "process_generation"),
    ("identity", "window_handle"),
    ("window", "coordinate_space"),
)
_ALLOWED_EXPECTED = {"window", "evidence"}
_ALLOWED_WINDOW_EXPECTED = {"title", "focused_control", "bounds"}
_ALLOWED_EVIDENCE_EXPECTED = {
    "frame_digest",
    "screenshot_digest",
    "visible_text_sha256",
}


def _text(
    value: Any,
    *,
    name: str,
    max_chars: int = 4096,
    allow_none: bool = False,
    allow_empty: bool = True,
) -> str | None:
    if value is None and allow_none:
        return None
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def _digest(value: Any, *, name: str, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    text = _text(value, name=name, max_chars=64, allow_empty=False)
    assert text is not None
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _bounds(value: Any) -> dict[str, int]:
    if type(value) is not dict:
        raise TypeError("expected window bounds must be a plain dict")
    if set(value) != {"left", "top", "right", "bottom", "width", "height"}:
        raise ValueError("expected window bounds must contain the canonical rectangle fields")
    result: dict[str, int] = {}
    for key in ("left", "top", "right", "bottom", "width", "height"):
        if type(value[key]) is not int:
            raise TypeError(f"expected window bounds {key} must be int")
        result[key] = value[key]
    if result["width"] != max(0, result["right"] - result["left"]):
        raise ValueError("expected window bounds width is inconsistent")
    if result["height"] != max(0, result["bottom"] - result["top"]):
        raise ValueError("expected window bounds height is inconsistent")
    return result


def _observation_time(value: str | None, *, name: str) -> datetime:
    if value is None:
        raise ValueError(f"{name} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return parsed


def normalize_windows_expected(raw: Any) -> tuple[dict[str, Any], tuple[StatePredicate, ...]]:
    """Validate bounded caller postconditions; stable identity is added separately."""

    if type(raw) is not dict:
        raise TypeError("Windows expected state must be a plain dict")
    extra = set(raw) - _ALLOWED_EXPECTED
    if extra:
        raise ValueError(f"Windows expected state contains unsupported fields: {sorted(extra)}")
    if not raw:
        raise ValueError("Windows expected state requires at least one final-state postcondition")

    normalized: dict[str, Any] = {}
    predicates: list[StatePredicate] = []

    if "window" in raw:
        window = raw["window"]
        if type(window) is not dict:
            raise TypeError("Windows expected window must be a plain dict")
        extra_window = set(window) - _ALLOWED_WINDOW_EXPECTED
        if extra_window:
            raise ValueError(f"Windows expected window contains unsupported fields: {sorted(extra_window)}")
        if not window:
            raise ValueError("Windows expected window must contain a postcondition")
        normalized_window: dict[str, Any] = {}
        if "title" in window:
            title = _text(window["title"], name="expected window title")
            assert title is not None
            normalized_window["title"] = title
            predicates.append(StatePredicate.equals("window", "title", expected=title))
        if "focused_control" in window:
            focused = _digest(
                window["focused_control"],
                name="expected focused_control",
                allow_none=True,
            )
            normalized_window["focused_control"] = focused
            predicates.append(
                StatePredicate.equals("window", "focused_control", expected=focused)
            )
        if "bounds" in window:
            bounds = _bounds(window["bounds"])
            normalized_window["bounds"] = bounds
            predicates.append(StatePredicate.equals("window", "bounds", expected=bounds))
        normalized["window"] = normalized_window

    if "evidence" in raw:
        evidence = raw["evidence"]
        if type(evidence) is not dict:
            raise TypeError("Windows expected evidence must be a plain dict")
        extra_evidence = set(evidence) - _ALLOWED_EVIDENCE_EXPECTED
        if extra_evidence:
            raise ValueError(
                f"Windows expected evidence contains unsupported fields: {sorted(extra_evidence)}"
            )
        if not evidence:
            raise ValueError("Windows expected evidence must contain a postcondition")
        normalized_evidence: dict[str, Any] = {}
        for field in ("frame_digest", "screenshot_digest", "visible_text_sha256"):
            if field not in evidence:
                continue
            value = _digest(
                evidence[field],
                name=f"expected {field}",
                allow_none=field == "screenshot_digest",
            )
            normalized_evidence[field] = value
            predicates.append(StatePredicate.equals("evidence", field, expected=value))
        normalized["evidence"] = normalized_evidence

    if not predicates:
        raise ValueError("Windows expected state produced no verifiable postconditions")
    return normalized, tuple(predicates)


def build_windows_desktop_effect(
    *,
    before: Any,
    expected: dict[str, Any],
    effect_id: str = WINDOWS_DESKTOP_EFFECT_ID,
) -> tuple[ExpectedEffect, dict[str, Any]]:
    """Bind caller postconditions plus stable process/native-window continuity.

    `window_instance` is intentionally not a continuity predicate because the
    accepted DesktopState definition includes window title in that digest. A
    legitimate title change on the same PID/process-generation/HWND therefore
    changes `window_instance`. The observation adapter independently recomputes
    and validates that digest against each snapshot.
    """

    normalized_expected, caller_predicates = normalize_windows_expected(expected)
    continuity = tuple(
        StatePredicate.equals(*path, expected=_lookup(before.state, path))
        for path in _IDENTITY_CONTINUITY_PATHS
    )
    return (
        ExpectedEffect(
            effect_id=effect_id,
            before=before.ref,
            predicates=continuity + caller_predicates,
        ),
        normalized_expected,
    )


def _lookup(state: Any, path: tuple[str, ...]) -> Any:
    current = state
    for part in path:
        current = current[part]
    return current


def verify_windows_desktop_transition(
    *,
    before_raw: dict[str, Any],
    after_raw: dict[str, Any],
    expected: dict[str, Any],
    subject: str = DEFAULT_WINDOWS_SUBJECT,
    stream_id: str | None = None,
    evidence_batch_id: str | None = None,
) -> dict[str, Any]:
    """Verify one bound Windows transition with the shared Verification Kernel.

    Stable live application/process/native-window identity is mandatory. A
    process restart, PID/process-generation drift, HWND drift, different
    executable identity, stale observation, or ambiguous evidence cannot PASS.
    Snapshot-local `window_instance`/frame/control digests are independently
    checked for internal consistency by the observation adapter.

    The adapter also requires AFTER.observed_at to be strictly later than
    BEFORE.observed_at. Sequence freshness alone is not enough because callers
    could otherwise relabel two historical DesktopState payloads as a new
    stream merely by supplying them in order. A non-advancing observation time
    returns UNKNOWN before any postcondition can PASS.
    """

    stream = WindowsDesktopObservationStream(subject=subject, stream_id=stream_id)
    before = stream.observe(before_raw)
    after = stream.observe(after_raw)
    effect, normalized_expected = build_windows_desktop_effect(
        before=before,
        expected=expected,
    )

    before_time = _observation_time(before.ref.observed_at, name="before observed_at")
    after_time = _observation_time(after.ref.observed_at, name="after observed_at")
    if after_time <= before_time:
        result = VerificationResult(
            effect_id=effect.effect_id,
            status=VerificationStatus.UNKNOWN,
            reason="stale_observation_time",
            observation=after.ref,
            evidence_batch_id=evidence_batch_id,
        )
    else:
        result = verify_expected_effect(
            effect,
            after,
            evidence_batch_id=evidence_batch_id,
        )
    return {
        "schema_version": 1,
        "operation": "verify_windows_desktop_transition",
        "status": result.status.value,
        "expected": normalized_expected,
        "before": before.ref.as_dict(),
        "after": after.ref.as_dict(),
        "verification": result.as_dict(),
    }
