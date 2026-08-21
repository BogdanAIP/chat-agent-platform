from __future__ import annotations

import ctypes
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .window_scoped_uia import (
    MAX_WINDOW_CONTROL_SCAN,
    TREE_SCOPE_DESCENDANTS,
    WindowScopedUiaResolver,
    _upstream,
)


SCHEMA_VERSION = 1
COORDINATE_SPACE = "screen_physical_px"
MAX_OBSERVED_CONTROLS = MAX_WINDOW_CONTROL_SCAN
MAX_VISIBLE_TEXT_CHARS = 32_768
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    def to_mapping(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class ControlObservation:
    role: str
    name: str
    automation_id: str
    bounds: Rect | None
    enabled: bool | None
    visible: bool | None
    focused: bool | None
    observation_fingerprint: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "name": self.name,
            "automation_id": self.automation_id,
            "bounds": self.bounds.to_mapping() if self.bounds is not None else None,
            "enabled": self.enabled,
            "visible": self.visible,
            "focused": self.focused,
            "observation_fingerprint": self.observation_fingerprint,
        }


@dataclass(frozen=True)
class EvidenceProvenance:
    source: str
    captured_at: str
    details: Mapping[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class DesktopState:
    schema_version: int
    session_id: str
    application_identity: str
    executable_name: str
    process_id: int
    process_generation: str
    window_handle: int
    window_instance: str
    window_title: str
    window_bounds: Rect
    coordinate_space: str
    focused_control: str | None
    controls: tuple[ControlObservation, ...]
    visible_text: str
    observed_capabilities: tuple[str, ...]
    screenshot_digest: str | None
    frame_digest: str
    observed_at: str
    observation_source: tuple[str, ...]
    provenance: tuple[EvidenceProvenance, ...]
    freshness_evidence: Mapping[str, Any]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "application_identity": self.application_identity,
            "executable_name": self.executable_name,
            "process_id": self.process_id,
            "process_generation": self.process_generation,
            "window_handle": self.window_handle,
            "window_instance": self.window_instance,
            "window_title": self.window_title,
            "window_bounds": self.window_bounds.to_mapping(),
            "coordinate_space": self.coordinate_space,
            "focused_control": self.focused_control,
            "controls": [control.to_mapping() for control in self.controls],
            "visible_text": self.visible_text,
            "observed_capabilities": list(self.observed_capabilities),
            "screenshot_digest": self.screenshot_digest,
            "frame_digest": self.frame_digest,
            "observed_at": self.observed_at,
            "observation_source": list(self.observation_source),
            "provenance": [entry.to_mapping() for entry in self.provenance],
            "freshness_evidence": dict(self.freshness_evidence),
        }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _rect_from_value(value: object) -> Rect | None:
    if value is None:
        return None

    if isinstance(value, Mapping):
        names = (("left", "top", "right", "bottom"), ("Left", "Top", "Right", "Bottom"))
        for keys in names:
            if all(key in value for key in keys):
                left, top, right, bottom = (int(round(float(value[key]))) for key in keys)
                return Rect(left, top, right, bottom)

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) >= 4:
            left, top, right, bottom = (int(round(float(value[index]))) for index in range(4))
            return Rect(left, top, right, bottom)

    for keys in (("left", "top", "right", "bottom"), ("Left", "Top", "Right", "Bottom")):
        if all(hasattr(value, key) for key in keys):
            left, top, right, bottom = (
                int(round(float(getattr(value, key)))) for key in keys
            )
            return Rect(left, top, right, bottom)

    return None


def _control_fingerprint(raw: Mapping[str, Any]) -> str:
    return _digest(
        {
            "role": str(raw.get("role") or ""),
            "name": _normalize_text(raw.get("name")),
            "automation_id": str(raw.get("automation_id") or ""),
            "bounds": raw.get("bounds"),
            "enabled": raw.get("enabled"),
            "visible": raw.get("visible"),
            "focused": raw.get("focused"),
        }
    )


def _make_control(raw: Mapping[str, Any]) -> ControlObservation:
    bounds = _rect_from_value(raw.get("bounds"))
    normalized = {
        "role": str(raw.get("role") or ""),
        "name": _normalize_text(raw.get("name")),
        "automation_id": str(raw.get("automation_id") or ""),
        "bounds": bounds.to_mapping() if bounds is not None else None,
        "enabled": _optional_bool(raw.get("enabled")),
        "visible": _optional_bool(raw.get("visible")),
        "focused": _optional_bool(raw.get("focused")),
    }
    return ControlObservation(
        role=normalized["role"],
        name=normalized["name"],
        automation_id=normalized["automation_id"],
        bounds=bounds,
        enabled=normalized["enabled"],
        visible=normalized["visible"],
        focused=normalized["focused"],
        observation_fingerprint=_control_fingerprint(normalized),
    )


def build_desktop_state(
    *,
    session_id: str,
    application_identity: str,
    executable_name: str,
    process_id: int,
    process_generation: str,
    window_handle: int,
    window_title: str,
    window_bounds: Rect,
    controls: Sequence[Mapping[str, Any]],
    screenshot_png: bytes | bytearray | memoryview | None = None,
    screenshot_source: str | None = None,
    observed_at: str | None = None,
    focus_evidence: Mapping[str, Any] | None = None,
) -> DesktopState:
    """Build one deterministic, non-authorizing desktop evidence snapshot.

    Screenshot bytes are accepted only to bind a digest into the state. They
    are never stored in DesktopState. Observation fingerprints are evidence
    digests and must not be confused with executor authorization fingerprints.
    """

    if not session_id:
        raise ValueError("session_id is required")
    if not application_identity:
        raise ValueError("application_identity is required")
    if isinstance(process_id, bool) or not isinstance(process_id, int) or process_id <= 0:
        raise ValueError("process_id must be a positive integer")
    if isinstance(window_handle, bool) or not isinstance(window_handle, int) or window_handle <= 0:
        raise ValueError("window_handle must be a positive integer")
    if len(controls) > MAX_OBSERVED_CONTROLS:
        raise ValueError("control observation exceeds the bounded scan contract")
    if screenshot_source and screenshot_png is None:
        raise ValueError("screenshot_source requires screenshot bytes")

    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    control_items = tuple(_make_control(item) for item in controls)

    visible_names: list[str] = []
    seen_names: set[str] = set()
    focused_control: str | None = None
    for control in control_items:
        if focused_control is None and control.focused is True:
            focused_control = control.observation_fingerprint
        if control.visible is False or not control.name or control.name in seen_names:
            continue
        seen_names.add(control.name)
        visible_names.append(control.name)

    visible_text = "\n".join(visible_names)
    if len(visible_text) > MAX_VISIBLE_TEXT_CHARS:
        visible_text = visible_text[:MAX_VISIBLE_TEXT_CHARS]

    screenshot_digest: str | None = None
    if screenshot_png is not None:
        screenshot_digest = hashlib.sha256(bytes(screenshot_png)).hexdigest()

    window_instance = _digest(
        {
            "process_id": process_id,
            "process_generation": process_generation,
            "window_handle": window_handle,
            "window_title": _normalize_text(window_title),
        }
    )

    sources = ["win32_identity", "uia_structure"]
    capabilities = ["win32_identity", "uia_structure", "uia_focus_state"]
    provenance = [
        EvidenceProvenance(
            source="win32_identity",
            captured_at=observed_at,
            details={
                "process_generation": process_generation,
                "window_handle": window_handle,
            },
        ),
        EvidenceProvenance(
            source="uia_structure",
            captured_at=observed_at,
            details={
                "control_count": len(control_items),
                "focus_evidence": dict(focus_evidence or {}),
            },
        ),
    ]

    if screenshot_digest is not None:
        sources.append("screenshot_digest")
        capabilities.append("screenshot_digest")
        provenance.append(
            EvidenceProvenance(
                source="screenshot_digest",
                captured_at=observed_at,
                details={
                    "sha256": screenshot_digest,
                    "source": screenshot_source or "provided_exact_window_png",
                },
            )
        )

    controls_mapping = [control.to_mapping() for control in control_items]
    frame_digest = _digest(
        {
            "session_id": session_id,
            "application_identity": application_identity,
            "process_id": process_id,
            "process_generation": process_generation,
            "window_handle": window_handle,
            "window_instance": window_instance,
            "window_title": _normalize_text(window_title),
            "window_bounds": window_bounds.to_mapping(),
            "coordinate_space": COORDINATE_SPACE,
            "controls": controls_mapping,
            "screenshot_digest": screenshot_digest,
        }
    )

    freshness = {
        "process_generation": process_generation,
        "window_handle": window_handle,
        "window_instance": window_instance,
        "structural_control_count": len(control_items),
        "screenshot_digest": screenshot_digest,
        "focus_evidence": dict(focus_evidence or {}),
    }

    return DesktopState(
        schema_version=SCHEMA_VERSION,
        session_id=session_id,
        application_identity=application_identity,
        executable_name=executable_name,
        process_id=process_id,
        process_generation=process_generation,
        window_handle=window_handle,
        window_instance=window_instance,
        window_title=_normalize_text(window_title),
        window_bounds=window_bounds,
        coordinate_space=COORDINATE_SPACE,
        focused_control=focused_control,
        controls=control_items,
        visible_text=visible_text,
        observed_capabilities=tuple(capabilities),
        screenshot_digest=screenshot_digest,
        frame_digest=frame_digest,
        observed_at=observed_at,
        observation_source=tuple(sources),
        provenance=tuple(provenance),
        freshness_evidence=freshness,
    )


def _query_process_identity(process_id: int) -> tuple[str, str, str, str]:
    if os.name != "nt":
        raise RuntimeError("Windows process identity requires Windows")

    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel32.ProcessIdToSessionId.restype = wintypes.BOOL
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    session = wintypes.DWORD()
    if not kernel32.ProcessIdToSessionId(process_id, ctypes.byref(session)):
        error = ctypes.get_last_error()
        raise OSError(error, "ProcessIdToSessionId failed")

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
    if not handle:
        error = ctypes.get_last_error()
        raise OSError(error, "OpenProcess failed for observed process")

    try:
        size = wintypes.DWORD(32_768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            error = ctypes.get_last_error()
            raise OSError(error, "QueryFullProcessImageNameW failed")
        image_path = buffer.value

        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            error = ctypes.get_last_error()
            raise OSError(error, "GetProcessTimes failed")
    finally:
        kernel32.CloseHandle(handle)

    creation_100ns = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
    executable_name = Path(image_path).name
    application_identity = "sha256:" + hashlib.sha256(
        image_path.casefold().encode("utf-8")
    ).hexdigest()
    return (
        f"windows-session:{int(session.value)}",
        application_identity,
        executable_name,
        str(creation_100ns),
    )


def _role_from_control_type(control_type_name: str) -> str:
    mapping = {
        "ButtonControl": "button",
        "HyperlinkControl": "link",
        "MenuItemControl": "menuitem",
        "TabItemControl": "tab",
        "ListItemControl": "listitem",
        "CheckBoxControl": "checkbox",
        "RadioButtonControl": "radio",
        "EditControl": "textbox",
        "WindowControl": "window",
        "TextControl": "text",
        "ListControl": "list",
        "ComboBoxControl": "combobox",
        "TreeItemControl": "treeitem",
    }
    return mapping.get(control_type_name, control_type_name.removesuffix("Control").casefold())


def _global_focus_match(
    client: Any,
    elements: Any,
) -> tuple[int | None, str]:
    """Match global UIA focus only against the already bounded window subtree.

    GetFocusedElement is global desktop evidence, so it is never trusted by
    itself.  A positive result is accepted only when CompareElements proves
    exact identity with one descendant returned by FindAll on the bound
    PID/HWND window.  Outside-window, ambiguous, and comparison-error states
    remain non-authorizing evidence.
    """

    try:
        focused_element = client.GetFocusedElement()
    except Exception:
        return None, "unavailable"
    if focused_element is None:
        return None, "none"

    matched_index: int | None = None
    for index in range(int(elements.Length)):
        try:
            same = bool(
                client.CompareElements(
                    focused_element,
                    elements.GetElement(index),
                )
            )
        except Exception:
            return None, "compare_error"
        if not same:
            continue
        if matched_index is not None:
            return None, "ambiguous"
        matched_index = index

    if matched_index is None:
        return None, "outside_bound_window"
    return matched_index, "exact_descendant"


def observe_bound_window(
    resolver: WindowScopedUiaResolver,
    window_name: str,
    *,
    screenshot_png: bytes | bytearray | memoryview | None = None,
    screenshot_source: str | None = None,
) -> DesktopState:
    """Observe one resolver-bound Windows window without authorizing an action.

    The exact PID/HWND binding reuses the Stage 26.1E production resolver. UIA
    descendants are bounded to the same 512-control ceiling. The function
    performs no clicks, typing, scrolling, shell execution or model inference.
    """

    if os.name != "nt":
        raise RuntimeError("Desktop observation requires Windows")
    if not isinstance(window_name, str) or not window_name.strip():
        raise ValueError("window_name is required")

    process_id = resolver.expected_process_id
    if process_id is None:
        raise ValueError("resolver expected_process_id must be bound before observation")

    upstream = _upstream()

    try:
        import uiautomation as auto
        from uiautomation import uiautomation as auto_impl
    except Exception as exc:
        raise upstream.AgentRequestError(
            503,
            "uia_unavailable",
            "UI Automation is unavailable",
        ) from exc

    import comtypes.client

    comtypes.client.gen_dir = None

    with auto.UIAutomationInitializerInThread():
        windows = resolver._find_target_windows(auto, window_name)
        if len(windows) != 1:
            raise upstream.AgentRequestError(
                409,
                "window_not_unique",
                f"expected one bound window, found {len(windows)}",
            )
        window = windows[0]

        def control_value(control: Any, key: str, default: object = None) -> object:
            return upstream._control_value(control, key, default)

        window_title = _normalize_text(control_value(window, "Name", window_name))
        window_handle = int(control_value(window, "NativeWindowHandle", 0) or 0)
        window_bounds = _rect_from_value(control_value(window, "BoundingRectangle", None))
        if window_handle <= 0:
            raise RuntimeError("bound UIA window did not expose a native handle")
        if window_bounds is None:
            raise RuntimeError("bound UIA window did not expose physical bounds")

        client = auto_impl._AutomationClient.instance().IUIAutomation
        elements = window.Element.FindAll(
            TREE_SCOPE_DESCENDANTS,
            client.CreateTrueCondition(),
        )
        if int(elements.Length) > MAX_OBSERVED_CONTROLS:
            raise upstream.AgentRequestError(
                409,
                "observation_truncated",
                "window UIA observation exceeds the bounded control ceiling",
            )

        global_focus_index, global_focus_status = _global_focus_match(client, elements)
        raw_controls: list[dict[str, Any]] = []
        property_focused_indices: list[int] = []
        materialized_indices: set[int] = set()
        for index in range(int(elements.Length)):
            raw_element = elements.GetElement(index)
            control = auto.Control.CreateControlFromElement(raw_element)
            if control is None:
                continue
            materialized_indices.add(index)
            control_type = str(control_value(control, "ControlTypeName", "") or "")
            bounds = _rect_from_value(control_value(control, "BoundingRectangle", None))
            offscreen = control_value(control, "IsOffscreen", None)
            visible = None if offscreen is None else not bool(offscreen)
            if bounds is not None and (bounds.width == 0 or bounds.height == 0):
                visible = False
            property_focused = _optional_bool(
                control_value(control, "HasKeyboardFocus", None)
            )
            if property_focused is True:
                property_focused_indices.append(index)
            raw_controls.append(
                {
                    "role": _role_from_control_type(control_type),
                    "name": _normalize_text(control_value(control, "Name", "")),
                    "automation_id": str(control_value(control, "AutomationId", "") or ""),
                    "bounds": bounds.to_mapping() if bounds is not None else None,
                    "enabled": _optional_bool(control_value(control, "IsEnabled", None)),
                    "visible": visible,
                    "focused": property_focused,
                    "_source_index": index,
                }
            )

        if len(property_focused_indices) > 1:
            raise upstream.AgentRequestError(
                409,
                "focus_not_unique",
                "multiple descendants reported HasKeyboardFocus in the bound window",
            )
        if global_focus_status == "ambiguous":
            raise upstream.AgentRequestError(
                409,
                "focus_not_unique",
                "global UIA focus matched multiple descendants of the bound window",
            )
        if global_focus_status == "exact_descendant":
            if global_focus_index not in materialized_indices:
                raise upstream.AgentRequestError(
                    409,
                    "focus_unmaterialized",
                    "focused descendant could not be represented as a control observation",
                )
            if (
                property_focused_indices
                and property_focused_indices != [global_focus_index]
            ):
                raise upstream.AgentRequestError(
                    409,
                    "focus_evidence_conflict",
                    "GetFocusedElement conflicts with descendant HasKeyboardFocus evidence",
                )
            for item in raw_controls:
                item["focused"] = item["_source_index"] == global_focus_index
        elif global_focus_status == "outside_bound_window" and property_focused_indices:
            raise upstream.AgentRequestError(
                409,
                "focus_evidence_conflict",
                "bound-window HasKeyboardFocus conflicts with global focus outside the window",
            )

        focus_evidence = {
            "global_uia_status": global_focus_status,
            "global_uia_exact_descendant_index": global_focus_index,
            "has_keyboard_focus_indices": list(property_focused_indices),
            "selected_source": (
                "get_focused_element_exact_descendant"
                if global_focus_status == "exact_descendant"
                else "has_keyboard_focus"
                if property_focused_indices
                else "none"
            ),
        }
        for item in raw_controls:
            item.pop("_source_index", None)

    session_id, application_identity, executable_name, process_generation = (
        _query_process_identity(process_id)
    )
    return build_desktop_state(
        session_id=session_id,
        application_identity=application_identity,
        executable_name=executable_name,
        process_id=process_id,
        process_generation=process_generation,
        window_handle=window_handle,
        window_title=window_title,
        window_bounds=window_bounds,
        controls=raw_controls,
        screenshot_png=screenshot_png,
        screenshot_source=screenshot_source,
        focus_evidence=focus_evidence,
    )
