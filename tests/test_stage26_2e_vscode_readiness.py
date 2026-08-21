from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "stage26-vscode-real-app-e2e.py"


class Stage262EVSCodeReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = DRIVER.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(DRIVER))
        start = cls.source.index("def _wait_safe_focused_editor_state")
        end = cls.source.index("\ndef main()", start)
        cls.helper = cls.source[start:end]

    def test_isolated_profile_disables_ai_startup_surface(self) -> None:
        self.assertIn('"chat.disableAIFeatures": True', self.source)
        self.assertIn('"editor.accessibilitySupport": "on"', self.source)

    def test_readiness_requires_two_consecutive_safe_editor_observations(self) -> None:
        self.assertIn("READINESS_STABLE_SAMPLES = 2", self.source)
        self.assertIn("focused = _focused_editor_control(state, unique_filename)", self.helper)
        self.assertIn("stable_count += 1", self.helper)
        self.assertIn("stable_count = 1", self.helper)
        self.assertIn(
            "focused is not None and stable_count >= READINESS_STABLE_SAMPLES",
            self.helper,
        )
        self.assertIn(
            "previous_focused.observation_fingerprint\n            == focused.observation_fingerprint",
            self.helper,
        )

    def test_transient_observation_error_resets_stability_without_authorizing(self) -> None:
        self.assertIn("state = observe_bound_window(resolver, window_title)", self.helper)
        self.assertIn("except Exception as exc:", self.helper)
        self.assertIn('"status": "observation_error"', self.helper)
        self.assertIn("stable_count = 0", self.helper)
        self.assertIn("previous_state = None", self.helper)
        self.assertIn("previous_focused = None", self.helper)

        forbidden = (
            "type_text_guarded",
            "arm_guarded_keyboard",
            "guarded_keyboard_frame",
            "require_foreground_hit_target",
            "SetForegroundWindow",
            "pyautogui",
            "pyperclip",
            "clipboard",
            "PostMessageW",
            "WM_CLOSE",
        )
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.helper)

    def test_retry_is_limited_to_physically_observed_com_rebuild(self) -> None:
        self.assertIn("TRANSIENT_UIA_REBUILD_HRESULT = -2147220991", self.source)
        self.assertIn("def _is_transient_uia_rebuild_error", self.source)
        self.assertIn('type(exc).__name__ == "COMError"', self.source)
        self.assertIn(
            "hresult == TRANSIENT_UIA_REBUILD_HRESULT",
            self.source,
        )
        self.assertIn(
            "if not _is_transient_uia_rebuild_error(exc):\n                raise",
            self.helper,
        )

    def test_identity_changes_fail_immediately_outside_retry_block(self) -> None:
        for required in (
            "state.window_handle != expected_hwnd",
            "state.process_id != expected_pid",
            "state.executable_name.casefold() != EXPECTED_EXECUTABLE",
            "state.process_generation != expected_process_generation",
            'raise RuntimeError("VS Code readiness exact PID/HWND identity changed")',
            'raise RuntimeError("VS Code readiness process generation changed")',
        ):
            self.assertIn(required, self.helper)

        try_start = self.helper.index("try:")
        except_end = self.helper.index("continue", self.helper.index("except Exception", try_start))
        identity_index = self.helper.index("state.window_handle != expected_hwnd")
        self.assertGreater(identity_index, except_end)

    def test_bound_process_generation_is_captured_before_readiness(self) -> None:
        query_index = self.source.index(
            ") = _query_process_identity(window_pid)"
        )
        readiness_index = self.source.index(
            "before_state, focused = _wait_safe_focused_editor_state("
        )
        self.assertLess(query_index, readiness_index)
        self.assertIn(
            "expected_process_generation=bound_process_generation",
            self.source,
        )
        self.assertIn("expected_hwnd=bound_hwnd", self.source)
        self.assertIn("expected_pid=window_pid", self.source)

    def test_readiness_precedes_native_guard_and_only_delivery(self) -> None:
        readiness_index = self.source.index(
            "before_state, focused = _wait_safe_focused_editor_state("
        )
        guard_index = self.source.index(
            "require_foreground_hit_target(before_state"
        )
        type_index = self.source.index("backend.type_text_guarded(")
        self.assertLess(readiness_index, guard_index)
        self.assertLess(guard_index, type_index)
        self.assertEqual(self.source.count("backend.type_text_guarded("), 1)

    def test_fresh_direct_observation_still_guards_the_actual_mutation(self) -> None:
        readiness_index = self.source.index(
            "before_state, focused = _wait_safe_focused_editor_state("
        )
        fresh_index = self.source.index(
            "action_state = observe_bound_window(resolver, window_title)"
        )
        type_index = self.source.index("backend.type_text_guarded(")
        self.assertLess(readiness_index, fresh_index)
        self.assertLess(fresh_index, type_index)
        self.assertIn(
            "action_focused.observation_fingerprint == focused.observation_fingerprint",
            self.source,
        )
        self.assertIn("_same_window_identity(before_state, action_state)", self.source)

    def test_readiness_evidence_is_persisted_and_printed(self) -> None:
        self.assertIn('"readiness_evidence": []', self.source)
        self.assertIn('evidence=result["readiness_evidence"]', self.source)
        self.assertIn('"readiness_evidence",', self.source)
        self.assertIn('"control_count": len(state.controls)', self.helper)
        self.assertIn('"focus_evidence": (', self.helper)
        self.assertIn('"focused_controls": _focused_diagnostics(state)', self.helper)
        self.assertIn('"safe_editor": (', self.helper)


if __name__ == "__main__":
    unittest.main()
