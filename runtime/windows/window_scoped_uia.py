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
    last_failure_stage: str | None = None
    last_failure_detail: str | None = None


class WindowScopedUiaResolver:
    """Bound structural UIA lookup to one exact process/window.

    This promotes the physically accepted Stage 26.1E resolver into runtime
    code.  Window binding uses Win32 top-level HWND enumeration narrowed by the
    expected process id before UIA conversion.  Target lookup remains native
    UIA FindAll inside the exact bound window.  Upstream candidate/fingerprint
    semantics and independent /uia/act re-resolution remain authoritative.
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

    def perform(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        upstream = _upstream()
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
                # module-global helper.  Serialize this narrow replacement so
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
