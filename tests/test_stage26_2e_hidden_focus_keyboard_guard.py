from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "runtime" / "windows" / "window_scoped_uia.py"
DRIVER = ROOT / "scripts" / "stage26-vscode-real-app-e2e.py"
HARNESS = ROOT / "scripts" / "stage26-vscode-real-app-e2e.ps1"


class Stage262EHiddenFocusKeyboardGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolver = RESOLVER.read_text(encoding="utf-8")
        cls.driver = DRIVER.read_text(encoding="utf-8")
        cls.harness = HARNESS.read_text(encoding="utf-8")
        ast.parse(cls.resolver, filename=str(RESOLVER))
        ast.parse(cls.driver, filename=str(DRIVER))

    def test_guard_is_explicitly_armed_and_one_shot(self) -> None:
        for required in (
            "class _ArmedKeyboardFocus",
            "self._armed_keyboard_focus",
            "def arm_focused_keyboard_target",
            "def _consume_focused_keyboard_target",
            "self._armed_keyboard_focus = None",
            'raise RuntimeError("keyboard focus guard is already armed")',
            "keyboard_focus_guard_arms",
            "keyboard_focus_guard_calls",
            "keyboard_focus_guard_passes",
            "keyboard_focus_guard_failures",
        ):
            self.assertIn(required, self.resolver)

    def test_armed_guard_uses_fresh_window_scoped_desktop_observation(self) -> None:
        start = self.resolver.index("def _perform_armed_keyboard_focus")
        end = self.resolver.index("\n    def perform", start)
        helper = self.resolver[start:end]
        for required in (
            "from .observation import observe_bound_window",
            "state = observe_bound_window(self, armed.window_title)",
            "state.process_id == self.expected_process_id",
            "state.window_handle == armed.window_handle",
            "state.process_generation == armed.process_generation",
            "state.window_title == armed.window_title",
            "state.focused_control == armed.focused_fingerprint",
            "control.observation_fingerprint == armed.focused_fingerprint",
            "matches[0].focused is True",
            "matches[0].enabled is True",
            "matches[0].role.casefold() == armed.role",
            "self._normalize_name(matches[0].name) == armed.name",
        ):
            self.assertIn(required, helper)

    def test_hidden_focus_guard_does_not_use_point_to_control_or_parent_walk(self) -> None:
        start = self.resolver.index("def _perform_armed_keyboard_focus")
        end = self.resolver.index("\n    def perform", start)
        helper = self.resolver[start:end]
        for forbidden in (
            "ControlFromPoint",
            "GetFocusedControl",
            "GetParentControl",
            "GetParentElement",
            "ControlViewWalker",
            "SetFocus",
            "TreeWalker",
        ):
            self.assertNotIn(forbidden, helper)
        self.assertIn("bounds.left <= x < bounds.right", helper)
        self.assertIn("bounds.top <= y < bounds.bottom", helper)

    def test_unarmed_focused_at_point_preserves_upstream_behavior(self) -> None:
        start = self.resolver.index("def _perform_armed_keyboard_focus")
        end = self.resolver.index("\n    def perform", start)
        helper = self.resolver[start:end]
        self.assertIn('return upstream._perform_uia("focused-at-point", payload)', helper)
        perform_start = self.resolver.index("def perform")
        perform = self.resolver[perform_start:]
        self.assertIn('if operation == "focused-at-point":', perform)
        self.assertIn("return self._perform_armed_keyboard_focus(payload)", perform)
        self.assertIn('if operation not in {"find", "act"}', perform)
        self.assertIn("return upstream._perform_uia(operation, payload)", perform)

    def test_action_guard_has_no_retry_or_focus_mutation(self) -> None:
        start = self.resolver.index("def _perform_armed_keyboard_focus")
        end = self.resolver.index("\n    def perform", start)
        helper = self.resolver[start:end]
        self.assertNotIn("while ", helper)
        self.assertNotIn("time.sleep", helper)
        self.assertNotIn("SetForegroundWindow", helper)
        self.assertNotIn("SetFocus", helper)
        self.assertNotIn("SendInput", helper)

    def test_driver_arms_exact_fresh_hidden_focus_before_only_typing_action(self) -> None:
        arm = self.driver.index("resolver.arm_focused_keyboard_target(")
        backend_arm = self.driver.index("backend.arm_guarded_keyboard(")
        type_index = self.driver.index("backend.type_text_guarded(")
        self.assertLess(arm, backend_arm)
        self.assertLess(backend_arm, type_index)
        self.assertEqual(self.driver.count("backend.type_text_guarded("), 1)
        for required in (
            "focused_fingerprint=action_focused.observation_fingerprint",
            "window_handle=action_state.window_handle",
            "process_generation=action_state.process_generation",
            "role=action_focused.role",
            "name=action_focused.name",
        ):
            self.assertIn(required, self.driver)

    def test_driver_retains_independent_top_level_native_window_guard(self) -> None:
        self.assertIn("action_point = _window_guard_point(action_state)", self.driver)
        self.assertIn("require_foreground_hit_target(action_state, *action_point)", self.driver)
        self.assertIn("backend.arm_guarded_keyboard(*action_point)", self.driver)
        self.assertNotIn("_control_center", self.driver)

    def test_outer_harness_independently_requires_hidden_focus_guard(self) -> None:
        for required in (
            "keyboard_focus_guard_mode = $null",
            "keyboard_focus_guard_armed_pass = $false",
            "keyboard_focus_guard_pass = $false",
            "'keyboard_focus_guard_armed_pass', 'keyboard_focus_guard_pass'",
            "'KEYBOARD_FOCUS_GUARD_MODE'",
            "'KEYBOARD_FOCUS_GUARD_ARMED_PASS'",
            "'KEYBOARD_FOCUS_GUARD_PASS'",
            "$result.keyboard_focus_guard_armed_pass -and",
            "$result.keyboard_focus_guard_pass -and",
        ):
            self.assertIn(required, self.harness)


if __name__ == "__main__":
    unittest.main()
