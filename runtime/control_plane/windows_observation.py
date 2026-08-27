from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Any

from .verification import ObservationRef, ObservationSnapshot


WINDOWS_DESKTOP_CAPABILITY = "windows.desktop"
MAX_WINDOWS_CONTROLS = 512
MAX_WINDOWS_VISIBLE_TEXT_CHARS = 32_768
MAX_WINDOWS_TEXT_CHARS = 4096
MAX_WINDOWS_ID_CHARS = 512

_REQUIRED_TOP_LEVEL = {
    "schema_version",
    "session_id",
    "application_identity",
    "executable_name",
    "process_id",
    "process_generation",
    "window_handle",
    "window_instance",
    "window_title",
    "window_bounds",
    "coordinate_space",
    "focused_control",
    "controls",
    "visible_text",
    "observed_capabilities",
    "screenshot_digest",
    "frame_digest",
    "observed_at",
    "observation_source",
    "provenance",
    "freshness_evidence",
}
_REQUIRED_CONTROL_FIELDS = {
    "role",
    "name",
    "automation_id",
    "bounds",
    "enabled",
    "visible",
    "focused",
    "observation_fingerprint",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _bounded_text(
    value: Any,
    *,
    name: str,
    max_chars: int = MAX_WINDOWS_TEXT_CHARS,
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


def _positive_int(value: Any, *, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _bounded_bool_or_none(value: Any, *, name: str) -> bool | None:
    if value is None:
        return None
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool or null")
    return value


def _sha256_text(value: Any, *, name: str, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    text = _bounded_text(value, name=name, max_chars=64, allow_empty=False)
    assert text is not None
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return text


def _application_identity(value: Any) -> str:
    text = _bounded_text(
        value,
        name="application_identity",
        max_chars=80,
        allow_empty=False,
    )
    assert text is not None
    if not text.startswith("sha256:"):
        raise ValueError("application_identity must use sha256: identity")
    _sha256_text(text.removeprefix("sha256:"), name="application_identity digest")
    return text


def _rect(raw: Any, *, name: str, allow_none: bool = False) -> dict[str, int] | None:
    if raw is None and allow_none:
        return None
    if type(raw) is not dict:
        raise TypeError(f"{name} must be a plain dict")
    allowed = {"left", "top", "right", "bottom", "width", "height"}
    if set(raw) - allowed:
        raise ValueError(f"{name} contains unsupported fields")
    required = {"left", "top", "right", "bottom"}
    if required - set(raw):
        raise ValueError(f"{name} is missing rectangle edges")
    edges: dict[str, int] = {}
    for key in ("left", "top", "right", "bottom"):
        value = raw[key]
        if type(value) is not int:
            raise TypeError(f"{name}.{key} must be int")
        edges[key] = value
    width = max(0, edges["right"] - edges["left"])
    height = max(0, edges["bottom"] - edges["top"])
    if "width" in raw and (type(raw["width"]) is not int or raw["width"] != width):
        raise ValueError(f"{name}.width is inconsistent with rectangle edges")
    if "height" in raw and (type(raw["height"]) is not int or raw["height"] != height):
        raise ValueError(f"{name}.height is inconsistent with rectangle edges")
    return {**edges, "width": width, "height": height}


def _string_list(value: Any, *, name: str, max_items: int = 64) -> list[str]:
    if type(value) is not list:
        raise TypeError(f"{name} must be a plain list")
    if len(value) > max_items:
        raise ValueError(f"{name} exceeds {max_items} items")
    result: list[str] = []
    for item in value:
        text = _bounded_text(item, name=f"{name} item", max_chars=256, allow_empty=False)
        assert text is not None
        result.append(text)
    return result


def _normalize_control(raw: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if type(raw) is not dict:
        raise TypeError("desktop control must be a plain dict")
    if set(raw) != _REQUIRED_CONTROL_FIELDS:
        raise ValueError("desktop control fields do not match DesktopState contract")

    fingerprint = _sha256_text(
        raw["observation_fingerprint"],
        name="desktop control observation_fingerprint",
    )
    assert fingerprint is not None
    role = _bounded_text(raw["role"], name="desktop control role", max_chars=256)
    name = _bounded_text(raw["name"], name="desktop control name")
    automation_id = _bounded_text(
        raw["automation_id"],
        name="desktop control automation_id",
        max_chars=MAX_WINDOWS_ID_CHARS,
    )
    assert role is not None and name is not None and automation_id is not None
    normalized_name = " ".join(name.split())
    if name != normalized_name:
        raise ValueError("desktop control name is not normalized DesktopState text")

    state = {
        "role": role,
        "name": name,
        "automation_id": automation_id,
        "bounds": _rect(raw["bounds"], name="desktop control bounds", allow_none=True),
        "enabled": _bounded_bool_or_none(raw["enabled"], name="desktop control enabled"),
        "visible": _bounded_bool_or_none(raw["visible"], name="desktop control visible"),
        "focused": _bounded_bool_or_none(raw["focused"], name="desktop control focused"),
    }
    if _digest(state) != fingerprint:
        raise ValueError("desktop control observation_fingerprint contradicts control state")
    full_mapping = {**state, "observation_fingerprint": fingerprint}
    return fingerprint, state, full_mapping


def normalize_windows_desktop_observation(raw: Any) -> tuple[dict[str, Any], bool, bool, str]:
    """Normalize one accepted DesktopState mapping for the shared verifier.

    This adapter consumes data only. It cannot enumerate windows, invoke UIA,
    deliver input, run a process, or authorize any mutation. Exact live evidence
    remains the responsibility of runtime.windows.observation.
    """

    if type(raw) is not dict:
        raise TypeError("Windows desktop observation must be a plain dict")
    if set(raw) != _REQUIRED_TOP_LEVEL:
        missing = sorted(_REQUIRED_TOP_LEVEL - set(raw))
        extra = sorted(set(raw) - _REQUIRED_TOP_LEVEL)
        raise ValueError(f"Windows desktop observation shape mismatch missing={missing} extra={extra}")
    if raw["schema_version"] != 1:
        raise ValueError("unsupported DesktopState schema_version")

    session_id = _bounded_text(
        raw["session_id"], name="session_id", max_chars=MAX_WINDOWS_ID_CHARS, allow_empty=False
    )
    application_identity = _application_identity(raw["application_identity"])
    executable_name = _bounded_text(
        raw["executable_name"], name="executable_name", max_chars=512, allow_empty=False
    )
    process_id = _positive_int(raw["process_id"], name="process_id")
    process_generation = _bounded_text(
        raw["process_generation"],
        name="process_generation",
        max_chars=MAX_WINDOWS_ID_CHARS,
        allow_empty=False,
    )
    window_handle = _positive_int(raw["window_handle"], name="window_handle")
    window_instance = _sha256_text(raw["window_instance"], name="window_instance")
    window_title = _bounded_text(raw["window_title"], name="window_title")
    window_bounds = _rect(raw["window_bounds"], name="window_bounds")
    coordinate_space = _bounded_text(
        raw["coordinate_space"], name="coordinate_space", max_chars=64, allow_empty=False
    )
    if coordinate_space != "screen_physical_px":
        raise ValueError("DesktopState coordinate_space must be screen_physical_px")

    focused_control = _sha256_text(
        raw["focused_control"], name="focused_control", allow_none=True
    )
    screenshot_digest = _sha256_text(
        raw["screenshot_digest"], name="screenshot_digest", allow_none=True
    )
    frame_digest = _sha256_text(raw["frame_digest"], name="frame_digest")
    observed_at = _bounded_text(
        raw["observed_at"], name="observed_at", max_chars=256, allow_empty=False
    )
    assert session_id is not None
    assert executable_name is not None
    assert process_generation is not None
    assert window_instance is not None
    assert window_title is not None
    assert window_bounds is not None
    assert coordinate_space is not None
    assert frame_digest is not None
    assert observed_at is not None

    normalized_title = " ".join(window_title.split())
    if window_title != normalized_title:
        raise ValueError("window_title is not normalized DesktopState text")
    expected_window_instance = _digest(
        {
            "process_id": process_id,
            "process_generation": process_generation,
            "window_handle": window_handle,
            "window_title": window_title,
        }
    )
    if window_instance != expected_window_instance:
        raise ValueError("window_instance contradicts process/HWND/title evidence")

    visible_text = _bounded_text(
        raw["visible_text"],
        name="visible_text",
        max_chars=MAX_WINDOWS_VISIBLE_TEXT_CHARS,
    )
    assert visible_text is not None
    observed_capabilities = _string_list(raw["observed_capabilities"], name="observed_capabilities")
    observation_source = _string_list(raw["observation_source"], name="observation_source")
    if type(raw["provenance"]) is not list or len(raw["provenance"]) > 64:
        raise ValueError("provenance must be a bounded plain list")

    raw_controls = raw["controls"]
    if type(raw_controls) is not list:
        raise TypeError("DesktopState controls must be a plain list")
    if len(raw_controls) > MAX_WINDOWS_CONTROLS:
        raise ValueError(f"DesktopState controls exceed {MAX_WINDOWS_CONTROLS} items")

    controls: dict[str, dict[str, Any]] = {}
    collisions: set[str] = set()
    full_controls: list[dict[str, Any]] = []
    for raw_control in raw_controls:
        control_id, control, full_control = _normalize_control(raw_control)
        full_controls.append(full_control)
        if control_id in collisions:
            continue
        if control_id in controls:
            controls.pop(control_id, None)
            collisions.add(control_id)
            continue
        controls[control_id] = control
    controls = {key: controls[key] for key in sorted(controls)}

    expected_frame_digest = _digest(
        {
            "session_id": session_id,
            "application_identity": application_identity,
            "process_id": process_id,
            "process_generation": process_generation,
            "window_handle": window_handle,
            "window_instance": window_instance,
            "window_title": window_title,
            "window_bounds": window_bounds,
            "coordinate_space": coordinate_space,
            "controls": full_controls,
            "screenshot_digest": screenshot_digest,
        }
    )
    if frame_digest != expected_frame_digest:
        raise ValueError("frame_digest contradicts normalized DesktopState evidence")

    freshness = raw["freshness_evidence"]
    if type(freshness) is not dict:
        raise TypeError("freshness_evidence must be a plain dict")
    required_freshness = {
        "process_generation",
        "window_handle",
        "window_instance",
        "structural_control_count",
        "screenshot_digest",
    }
    if required_freshness - set(freshness):
        raise ValueError("freshness_evidence is missing required identity fields")
    if freshness["process_generation"] != process_generation:
        raise ValueError("freshness process_generation contradicts DesktopState identity")
    if freshness["window_handle"] != window_handle:
        raise ValueError("freshness window_handle contradicts DesktopState identity")
    if freshness["window_instance"] != window_instance:
        raise ValueError("freshness window_instance contradicts DesktopState identity")
    if freshness["structural_control_count"] != len(raw_controls):
        raise ValueError("freshness structural_control_count contradicts controls")
    if freshness["screenshot_digest"] != screenshot_digest:
        raise ValueError("freshness screenshot_digest contradicts DesktopState evidence")

    state = {
        "identity": {
            "session_id": session_id,
            "application_identity": application_identity,
            "executable_name": executable_name,
            "process_id": process_id,
            "process_generation": process_generation,
            "window_handle": window_handle,
            "window_instance": window_instance,
        },
        "window": {
            "title": window_title,
            "bounds": window_bounds,
            "coordinate_space": coordinate_space,
            "focused_control": focused_control,
        },
        "controls": controls,
        "control_collisions": sorted(collisions),
        "control_count": len(raw_controls),
        "evidence": {
            "visible_text_sha256": hashlib.sha256(visible_text.encode("utf-8")).hexdigest(),
            "screenshot_digest": screenshot_digest,
            "frame_digest": frame_digest,
            "observed_capabilities": observed_capabilities,
            "observation_source": observation_source,
        },
        "freshness": {
            "process_generation": process_generation,
            "window_handle": window_handle,
            "window_instance": window_instance,
            "structural_control_count": len(raw_controls),
            "screenshot_digest": screenshot_digest,
        },
    }
    state["desktop_state_sha256"] = _digest(state)
    return state, True, bool(collisions), observed_at


class WindowsDesktopObservationStream:
    """Monotonic verifier stream for one logical bound Windows target."""

    def __init__(self, *, subject: str, stream_id: str | None = None) -> None:
        normalized_subject = _bounded_text(
            subject,
            name="Windows observation subject",
            max_chars=MAX_WINDOWS_ID_CHARS,
            allow_empty=False,
        )
        assert normalized_subject is not None
        self._subject = normalized_subject
        self._stream_id = stream_id or secrets.token_hex(16)
        _bounded_text(
            self._stream_id,
            name="Windows observation stream_id",
            max_chars=MAX_WINDOWS_ID_CHARS,
            allow_empty=False,
        )
        self._sequence = 0

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def stream_id(self) -> str:
        return self._stream_id

    def observe(self, raw: dict[str, Any]) -> ObservationSnapshot:
        state, complete, ambiguous, observed_at = normalize_windows_desktop_observation(raw)
        self._sequence += 1
        fingerprint = _digest(
            {"state": state, "complete": complete, "ambiguous": ambiguous}
        )
        return ObservationSnapshot(
            ref=ObservationRef(
                capability=WINDOWS_DESKTOP_CAPABILITY,
                subject=self._subject,
                stream_id=self._stream_id,
                sequence=self._sequence,
                fingerprint=fingerprint,
                observed_at=observed_at or _utc_now(),
            ),
            state=state,
            complete=complete,
            ambiguous=ambiguous,
        )
