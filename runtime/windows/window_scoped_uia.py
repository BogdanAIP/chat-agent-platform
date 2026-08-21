from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any


TREE_SCOPE_DESCENDANTS = 4
MAX_DIRECT_CANDIDATES = 8
MAX_WINDOW_CONTROL_SCAN = 512
MAX_ENUM_WINDOWS = 4096
MAX_DIAGNOSTIC_CHARS = 240
_PATCH_LOCK = threading.RLock()


def _upstream():
    from openadapt_flow.backends.win_agent import server

    return server


@dataclass
class ResolverStats:
    window_scoped_find_calls: int = 0
    desktop_fallback_calls: int = 0
    delegated_uia_calls: int = 0
    automation_id_condition_calls: int = 0
    role_name_condition_calls: int = 0
    window_enum_calls: int = 0
    window_enum_handles_seen: int = 0
    process_window_handles_seen: int = 0
    window_uia_convertible_count: int = 0
    window_name_match_count: int = 0
    window_binding_failures: int = 0
    window_binding_ambiguities: int = 0
    keyboard_focus_guard_arms: int = 0
    keyboard_focus_guard_calls: int = 0
    keyboard_focus_guard_passes: int = 0
    keyboard_focus_guard_failures: int = 0
    last_failure_stage: str | None = None
    last_failure_detail: str | None = None


@dataclass(frozen=True)
class _ArmedKeyboardFocus:
    window_title: str
    window_handle: int
    process_generation: str
    focused_fingerprint: str
    role: str
    name: str


class WindowScopedUiaResolver:
    """Bound structural UIA lookup and guarded keyboard focus to one window.

    Window binding uses Win32 top-level HWND enumeration narrowed by the
    expected process id before UIA conversion. Target lookup remains native
    UIA FindAll inside the exact bound window. Upstream candidate/fingerprint
    semantics and independent /uia/act re-resolution remain authoritative.

    Keyboard input has one additional opt-in guard for applications such as
    Monaco where the true focused input is intentionally hidden and therefore
    cannot be recovered through ControlFromPoint. The caller arms one exact
    DesktopState focused-control fingerprint. The next focused-at-point request
    consumes that arm and performs a completely fresh, window-scoped
    observation. The screen point remains a top-level window/context guard; it
    is never treated as geometry for the hidden focused control.
    """

    def __init__(self) -> None:
        self.stats = ResolverStats()
        self.expected_process_id: int | None = None
        self._keyboard_focus_lock = threading.RLock()
        self._armed_keyboard_focus: _ArmedKeyboardFocus | None = None

    def set_expected_process_id(self, process_id: int) -> None:
        if isinstance(process_id, bool) or not isinstance(process_id, int) or process_id <= 0:
            raise ValueError("expected process id must be a positive integer")
        if self.expected_process_id is not None and self.expected_process_id != process_id:
            raise ValueError("expected process id is already bound")
        self.expected_process_id = process_id

    def arm_focused_keyboard_target(
        self,
        *,
        window_title: str,
        window_handle: int,
        process_generation: str,
        focused_fingerprint: str,
        role: str,
        name: str,
    ) -> None:
        """Arm one fresh exact focused-control identity for keyboard delivery."""

        if self.expected_process_id is None:
            raise ValueError("expected process id must be bound before keyboard focus")
        normalized_title = self._normalize_name(window_title)
        normalized_name = self._normalize_name(name)
        normalized_role = str(role or "").casefold()
        fingerprint = str(focused_fingerprint or "").casefold()
        if not normalized_title:
            raise ValueError("keyboard focus window title is required")
        if isinstance(window_handle, bool) or not isinstance(window_handle, int) or window_handle <= 0:
            raise ValueError("keyboard focus window handle must be positive")
        if not process_generation:
            raise ValueError("keyboard focus process generation is required")
        if (
            len(fingerprint) != 64
            or any(char not in "0123456789abcdef" for char in fingerprint)
        ):
            raise ValueError("keyboard focus fingerprint must be lowercase SHA-256")
        if not normalized_role or not normalized_name:
            raise ValueError("keyboard focus role and name are required")

        arm = _ArmedKeyboardFocus(
            window_title=normalized_title,
            window_handle=window_handle,
            process_generation=str(process_generation),
            focused_fingerprint=fingerprint,
            role=normalized_role,
            name=normalized_name,
        )
        with self._keyboard_focus_lock:
            if self._armed_keyboard_focus is not None:
                raise RuntimeError("keyboard focus guard is already armed")
            self._armed_keyboard_focus = arm
            self.stats.keyboard_focus_guard_arms += 1

    def cancel_focused_keyboard_target(self) -> None:
        with self._keyboard_focus_lock:
            self._armed_keyboard_focus = None

    def _consume_focused_keyboard_target(self) -> _ArmedKeyboardFocus | None:
        with self._keyboard_focus_lock:
            armed = self._armed_keyboard_focus
            self._armed_keyboard_focus = None
            return armed

    @staticmethod
    def _normalize_name(value: object) -> str:
        return " ".join(str(value or "").split())

    def _record_failure(self, stage: str, detail: object) -> None:
        self.stats.last_failure_stage = stage
        self.stats.last_failure_detail = str(detail)[:MAX_DIAGNOSTIC_CHARS]

    def _clear_failure(self) -> None:
        self.stats.last_failure_stage = None
        self.stats.last_failure_detail = None

    @staticmethod
    def _and_conditions(client: Any, conditions: list[Any]) -> Any:
        if not conditions:
            return client.CreateTrueCondition()
        result = conditions[0]
        for condition in conditions[1:]:
            result = client.CreateAndCondition(result, condition)
        return result

    @staticmethod
    def _role_control_type(auto: Any, role: str | None) -> int | None:
        mapping = {
            "button": auto.ControlType.ButtonControl,
            "link": auto.ControlType.HyperlinkControl,
            "menuitem": auto.ControlType.MenuItemControl,
            "tab": auto.ControlType.TabItemControl,
            "listitem": auto.ControlType.ListItemControl,
            "checkbox": auto.ControlType.CheckBoxControl,
            "radio": auto.ControlType.RadioButtonControl,
            "textbox": auto.ControlType.EditControl,
        }
        return mapping.get(role or "")

    @staticmethod
    def _controls_from_element_array(
        auto: Any,
        elements: Any,
        *,
        limit: int,
    ) -> list[Any]:
        length = int(elements.Length)
        controls: list[Any] = []
        for index in range(min(length, limit)):
            raw = elements.GetElement(index)
            control = auto.Control.CreateControlFromElement(raw)
            if control is not None:
                controls.append(control)
        return controls

    def _find_target_windows(self, auto: Any, window_name: str) -> list[Any]:
        upstream = _upstream()
        if self.expected_process_id is None:
            self.stats.window_binding_failures += 1
            self._record_failure("window_context", "expected process id is not bound")
            raise upstream.AgentRequestError(
                409,
                "window_context_unbound",
                "expected process id is required for window-scoped UIA",
            )

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        enum_proc_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM,
        )
        user32.EnumWindows.argtypes = [enum_proc_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD

        all_count = 0
        process_handles: list[int] = []

        @enum_proc_type
        def collect(hwnd: int, _lparam: int) -> bool:
            nonlocal all_count
            all_count += 1
            if all_count > MAX_ENUM_WINDOWS:
                return False
            pid = wintypes.DWORD()
            if user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)):
                if int(pid.value) == self.expected_process_id:
                    process_handles.append(int(hwnd))
            return True

        self.stats.window_enum_calls += 1
        ctypes.set_last_error(0)
        completed = bool(user32.EnumWindows(collect, 0))
        if not completed and all_count <= MAX_ENUM_WINDOWS:
            error = ctypes.get_last_error()
            self.stats.window_binding_failures += 1
            self._record_failure("enum_windows", f"EnumWindows failed ({error})")
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                f"EnumWindows failed ({error})",
            )
        if all_count > MAX_ENUM_WINDOWS:
            self.stats.window_binding_failures += 1
            self._record_failure(
                "enum_windows",
                f"enumeration exceeded {MAX_ENUM_WINDOWS} top-level HWNDs",
            )
            raise upstream.AgentRequestError(
                409,
                "window_enumeration_truncated",
                "top-level window enumeration exceeded its bound",
            )

        self.stats.window_enum_handles_seen += all_count
        self.stats.process_window_handles_seen += len(process_handles)
        expected_name = self._normalize_name(window_name)
        matches: list[Any] = []
        conversion_errors: list[str] = []

        for hwnd in process_handles:
            try:
                control = auto.ControlFromHandle(hwnd)
            except Exception as exc:
                conversion_errors.append(
                    f"hwnd={hwnd}: {type(exc).__name__}: {exc}"
                )
                continue
            if control is None:
                continue
            self.stats.window_uia_convertible_count += 1
            if str(upstream._control_value(control, "ControlTypeName", "")) != "WindowControl":
                continue
            observed_name = self._normalize_name(
                upstream._control_value(control, "Name", "")
            )
            if observed_name == expected_name:
                matches.append(control)

        self.stats.window_name_match_count += len(matches)
        if not matches:
            self.stats.window_binding_failures += 1
            detail = (
                f"pid={self.expected_process_id} all_hwnds={all_count} "
                f"pid_hwnds={len(process_handles)} "
                f"uia_convertible={self.stats.window_uia_convertible_count} "
                f"expected_name={expected_name!r}"
            )
            if conversion_errors:
                detail += f" conversion_error={conversion_errors[0]}"
            self._record_failure("window_match", detail)
        if len(matches) > 1:
            self.stats.window_binding_ambiguities += 1
            self._record_failure(
                "window_match",
                f"expected one window for pid={self.expected_process_id}, found {len(matches)}",
            )
        return matches

    def _direct_find_candidates(
        self,
        locator: dict[str, Any],
        auto: Any,
    ) -> tuple[list[tuple[Any, dict[str, Any]]], bool]:
        upstream = _upstream()
        window_name = locator.get("window_name")
        if not isinstance(window_name, str) or not window_name:
            self.stats.desktop_fallback_calls += 1
            return upstream._find_candidates(locator, auto)

        self.stats.window_scoped_find_calls += 1
        self._clear_failure()

        windows = self._find_target_windows(auto, window_name)
        if not windows:
            return [], False

        try:
            from uiautomation import uiautomation as auto_impl

            client = auto_impl._AutomationClient.instance().IUIAutomation
        except Exception as exc:
            self._record_failure(
                "automation_client",
                f"{type(exc).__name__}: {exc}",
            )
            raise

        control_conditions: list[Any] = []
        automation_id = locator.get("automation_id")
        role = locator.get("role")

        if isinstance(automation_id, str) and automation_id:
            self.stats.automation_id_condition_calls += 1
            control_conditions.append(
                client.CreatePropertyCondition(
                    auto.PropertyId.AutomationIdProperty,
                    automation_id,
                )
            )
        else:
            self.stats.role_name_condition_calls += 1

        control_type = self._role_control_type(auto, role)
        if control_type is not None:
            control_conditions.append(
                client.CreatePropertyCondition(
                    auto.PropertyId.ControlTypeProperty,
                    control_type,
                )
            )

        condition = self._and_conditions(client, control_conditions)
        found: list[tuple[Any, dict[str, Any]]] = []
        truncated = False
        scanned_controls = 0

        for window in windows:
            try:
                control_elements = window.Element.FindAll(
                    TREE_SCOPE_DESCENDANTS,
                    condition,
                )
            except Exception as exc:
                self._record_failure(
                    "target_findall",
                    f"{type(exc).__name__}: {exc}",
                )
                raise
            scanned_controls += min(
                int(control_elements.Length),
                MAX_WINDOW_CONTROL_SCAN,
            )
            controls = self._controls_from_element_array(
                auto,
                control_elements,
                limit=MAX_WINDOW_CONTROL_SCAN,
            )
            for control in controls:
                candidate = upstream._candidate(control)
                if candidate is None:
                    continue
                if any(
                    expected is not None and candidate.get(key) != expected
                    for key, expected in locator.items()
                    if key in {"automation_id", "role", "name", "window_name"}
                ):
                    continue
                found.append((control, candidate))
                if len(found) >= MAX_DIRECT_CANDIDATES:
                    truncated = True
                    return found, truncated

            if int(control_elements.Length) > MAX_WINDOW_CONTROL_SCAN:
                truncated = True

        if not found:
            self._record_failure(
                "target_candidate_match",
                f"role={role!r} name={locator.get('name')!r} scanned={scanned_controls}",
            )
        return found, truncated

    def _perform_armed_keyboard_focus(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        upstream = _upstream()
        armed = self._consume_focused_keyboard_target()
        if armed is None:
            self.stats.delegated_uia_calls += 1
            return upstream._perform_uia("focused-at-point", payload)

        self.stats.keyboard_focus_guard_calls += 1
        data = upstream._exact_object(
            payload,
            required=frozenset({"x", "y"}),
            label="focused-at-point",
        )
        x = upstream._bounded_int(data["x"], "x")
        y = upstream._bounded_int(data["y"], "y")

        try:
            from .observation import observe_bound_window

            state = observe_bound_window(self, armed.window_title)
        except upstream.AgentRequestError:
            self.stats.keyboard_focus_guard_failures += 1
            raise
        except Exception as exc:
            self.stats.keyboard_focus_guard_failures += 1
            self._record_failure(
                "keyboard_focus_observation",
                f"{type(exc).__name__}: {exc}",
            )
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                "window-scoped keyboard focus is unavailable",
            ) from exc

        bounds = state.window_bounds
        matches = [
            control
            for control in state.controls
            if control.observation_fingerprint == armed.focused_fingerprint
        ]
        valid = bool(
            state.process_id == self.expected_process_id
            and state.window_handle == armed.window_handle
            and state.process_generation == armed.process_generation
            and state.window_title == armed.window_title
            and bounds.left <= x < bounds.right
            and bounds.top <= y < bounds.bottom
            and state.focused_control == armed.focused_fingerprint
            and len(matches) == 1
            and matches[0].focused is True
            and matches[0].enabled is True
            and matches[0].role.casefold() == armed.role
            and self._normalize_name(matches[0].name) == armed.name
        )
        if not valid:
            self.stats.keyboard_focus_guard_failures += 1
            self._record_failure(
                "keyboard_focus_guard",
                "fresh focused control/window identity did not match the armed target",
            )
            return {"status": "ok", "focused": False}

        self.stats.keyboard_focus_guard_passes += 1
        self._clear_failure()
        return {
            "status": "ok",
            "focused": True,
            "target_fingerprint": armed.focused_fingerprint,
        }

    def perform(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        upstream = _upstream()
        if operation == "focused-at-point":
            return self._perform_armed_keyboard_focus(payload)
        if operation not in {"find", "act"}:
            self.stats.delegated_uia_calls += 1
            return upstream._perform_uia(operation, payload)

        try:
            import uiautomation as auto
        except Exception as exc:
            self._record_failure("uia_import", f"{type(exc).__name__}: {exc}")
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                "UI Automation is unavailable",
            ) from exc

        if os.name == "nt":
            import comtypes.client

            comtypes.client.gen_dir = None

        try:
            with auto.UIAutomationInitializerInThread():
                # Pinned upstream routes structural resolution through one
                # module-global helper. Serialize this narrow replacement so
                # concurrent calls cannot observe another resolver instance.
                with _PATCH_LOCK:
                    original = upstream._find_candidates
                    upstream._find_candidates = self._direct_find_candidates
                    try:
                        return upstream._perform_uia_initialized(
                            auto,
                            operation,
                            payload,
                        )
                    finally:
                        upstream._find_candidates = original
        except upstream.AgentRequestError:
            raise
        except Exception as exc:
            if self.stats.last_failure_stage is None:
                self._record_failure(
                    "uia_operation",
                    f"{type(exc).__name__}: {exc}",
                )
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                "UI Automation is unavailable",
            ) from exc
