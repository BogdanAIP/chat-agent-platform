from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openadapt_flow.backends.win_agent import server as upstream


TREE_SCOPE_DESCENDANTS = 4
_MAX_DIRECT_CANDIDATES = 8
_MAX_WINDOW_CONTROL_SCAN = 512
_MAX_ENUM_WINDOWS = 4096


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


class WindowScopedUiaResolver:
    """Replace only OpenAdapt's desktop-wide UIA candidate walk.

    The typed HTTP contract, request validation, target fingerprinting and
    native action semantics remain upstream. Window binding uses Win32
    top-level HWND enumeration narrowed by the expected process id, then
    converts only those HWNDs to UIA controls. Target lookup remains native
    UIA FindAll inside the exact bound window. Every /uia/act still
    independently re-resolves the target and compares the fresh fingerprint.
    """

    def __init__(self) -> None:
        self.stats = ResolverStats()
        self.expected_process_id: int | None = None

    def set_expected_process_id(self, process_id: int) -> None:
        if isinstance(process_id, bool) or not isinstance(process_id, int) or process_id <= 0:
            raise ValueError("expected process id must be a positive integer")
        if self.expected_process_id is not None and self.expected_process_id != process_id:
            raise ValueError("expected process id is already bound")
        self.expected_process_id = process_id

    @staticmethod
    def _normalize_name(value: object) -> str:
        return " ".join(str(value or "").split())

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
        """Wrap a native IUIAutomationElementArray as uiautomation Controls."""

        length = int(elements.Length)
        controls: list[Any] = []
        for index in range(min(length, limit)):
            raw = elements.GetElement(index)
            control = auto.Control.CreateControlFromElement(raw)
            if control is not None:
                controls.append(control)
        return controls

    def _find_target_windows(self, auto: Any, window_name: str) -> list[Any]:
        """Bind one top-level HWND without traversing the desktop UIA tree."""

        if self.expected_process_id is None:
            self.stats.window_binding_failures += 1
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
            if all_count > _MAX_ENUM_WINDOWS:
                return False
            pid = wintypes.DWORD()
            if user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)):
                if int(pid.value) == self.expected_process_id:
                    process_handles.append(int(hwnd))
            return True

        self.stats.window_enum_calls += 1
        ctypes.set_last_error(0)
        completed = bool(user32.EnumWindows(collect, 0))
        if not completed and all_count <= _MAX_ENUM_WINDOWS:
            error = ctypes.get_last_error()
            self.stats.window_binding_failures += 1
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                f"EnumWindows failed ({error})",
            )
        if all_count > _MAX_ENUM_WINDOWS:
            self.stats.window_binding_failures += 1
            raise upstream.AgentRequestError(
                409,
                "window_enumeration_truncated",
                "top-level window enumeration exceeded its bound",
            )

        self.stats.window_enum_handles_seen += all_count
        self.stats.process_window_handles_seen += len(process_handles)
        expected_name = self._normalize_name(window_name)
        matches: list[Any] = []

        for hwnd in process_handles:
            try:
                control = auto.ControlFromHandle(hwnd)
            except Exception:
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
        if len(matches) > 1:
            self.stats.window_binding_ambiguities += 1
        return matches

    def _direct_find_candidates(
        self,
        locator: dict[str, Any],
        auto: Any,
    ) -> tuple[list[tuple[Any, dict[str, Any]]], bool]:
        window_name = locator.get("window_name")
        if not isinstance(window_name, str) or not window_name:
            self.stats.desktop_fallback_calls += 1
            return upstream._find_candidates(locator, auto)

        self.stats.window_scoped_find_calls += 1
        client = auto._AutomationClient.instance().IUIAutomation
        windows = self._find_target_windows(auto, window_name)
        if not windows:
            return [], False

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
            # Provider-tolerant fallback: native search narrows by control type
            # inside the already-bound window. Exact normalized Name remains a
            # hard check in the upstream candidate comparison below. This
            # avoids relying on raw UIA NameProperty matching after the physical
            # WinForms top-level NameProperty mismatch was observed.
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

        for window in windows:
            control_elements = window.Element.FindAll(
                TREE_SCOPE_DESCENDANTS,
                condition,
            )
            controls = self._controls_from_element_array(
                auto,
                control_elements,
                limit=_MAX_WINDOW_CONTROL_SCAN,
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
                if len(found) >= _MAX_DIRECT_CANDIDATES:
                    truncated = True
                    return found, truncated

            if int(control_elements.Length) > _MAX_WINDOW_CONTROL_SCAN:
                truncated = True

        return found, truncated

    def perform(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation not in {"find", "act"}:
            self.stats.delegated_uia_calls += 1
            return upstream._perform_uia(operation, payload)

        try:
            import uiautomation as auto
        except Exception as exc:
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                "UI Automation is unavailable",
            ) from exc

        if upstream.os.name == "nt":
            import comtypes.client

            comtypes.client.gen_dir = None

        try:
            with auto.UIAutomationInitializerInThread():
                original = upstream._find_candidates
                upstream._find_candidates = self._direct_find_candidates
                try:
                    return upstream._perform_uia_initialized(auto, operation, payload)
                finally:
                    upstream._find_candidates = original
        except upstream.AgentRequestError:
            raise
        except Exception as exc:
            raise upstream.AgentRequestError(
                503,
                "uia_unavailable",
                "UI Automation is unavailable",
            ) from exc
