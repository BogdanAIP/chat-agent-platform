from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openadapt_flow.backends.win_agent import server as upstream


TREE_SCOPE_CHILDREN = 2
TREE_SCOPE_DESCENDANTS = 4
_MAX_DIRECT_CANDIDATES = 8
_MAX_WINDOW_CANDIDATES = 32


@dataclass
class ResolverStats:
    window_scoped_find_calls: int = 0
    desktop_fallback_calls: int = 0
    delegated_uia_calls: int = 0
    automation_id_condition_calls: int = 0
    role_name_condition_calls: int = 0


class WindowScopedUiaResolver:
    """Replace only OpenAdapt's desktop-wide UIA candidate walk.

    The typed HTTP contract, request validation, target fingerprinting and
    native action semantics remain upstream. For /uia/find and /uia/act we
    temporarily substitute the candidate resolver used by the pinned upstream
    implementation. Every operation still re-resolves the target and compares
    the fresh fingerprint before actuation.
    """

    def __init__(self) -> None:
        self.stats = ResolverStats()

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
        """Wrap a native IUIAutomationElementArray as uiautomation Controls.

        ``uiautomation.Control`` intentionally does not expose FindAll; its
        ``Element`` property is the raw IUIAutomationElement. Native FindAll
        therefore returns an IUIAutomationElementArray whose entries must be
        wrapped back into Control objects before using OpenAdapt's candidate
        and fingerprint helpers.
        """

        length = int(elements.Length)
        controls: list[Any] = []
        for index in range(min(length, limit)):
            raw = elements.GetElement(index)
            control = auto.Control.CreateControlFromElement(raw)
            if control is not None:
                controls.append(control)
        return controls

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
        root = auto.GetRootControl()

        window_condition = self._and_conditions(
            client,
            [
                client.CreatePropertyCondition(
                    auto.PropertyId.ControlTypeProperty,
                    auto.ControlType.WindowControl,
                ),
                client.CreatePropertyCondition(
                    auto.PropertyId.NameProperty,
                    window_name,
                ),
            ],
        )
        window_elements = root.Element.FindAll(
            TREE_SCOPE_CHILDREN,
            window_condition,
        )
        windows = self._controls_from_element_array(
            auto,
            window_elements,
            limit=_MAX_WINDOW_CANDIDATES,
        )
        if not windows:
            return [], False

        control_conditions: list[Any] = []
        automation_id = locator.get("automation_id")
        role = locator.get("role")
        name = locator.get("name")

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
        if isinstance(name, str) and name:
            control_conditions.append(
                client.CreatePropertyCondition(
                    auto.PropertyId.NameProperty,
                    name,
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
                limit=_MAX_DIRECT_CANDIDATES + 1,
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
