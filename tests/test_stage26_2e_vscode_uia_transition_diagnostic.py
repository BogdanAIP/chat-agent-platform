from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "scripts" / "stage26-vscode-uia-transition-diagnostic.py"


class Stage262EVSCodeUiaTransitionDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = DIAGNOSTIC.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(DIAGNOSTIC))

    def test_transition_diagnostic_is_application_input_read_only(self) -> None:
        forbidden = (
            "type_text_guarded",
            "arm_guarded_keyboard",
            "act_guarded_coordinate",
            "press_guarded",
            "act_structural",
            "bounded_input",
            "SetForegroundWindow",
            "pyautogui",
            "pyperclip",
            "clipboard",
            "shell=True",
            "os.system",
            "subprocess.run",
            "execute_windows",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, self.source)
        self.assertIn('"keyboard_action_count": 0', self.source)
        self.assertIn('"pointer_action_count": 0', self.source)

    def test_transition_diagnostic_uses_same_isolated_vscode_profile(self) -> None:
        for required in (
            '"--wait"',
            '"--new-window"',
            '"--disable-extensions"',
            '"--user-data-dir"',
            '"--extensions-dir"',
            '"--goto"',
            '"editor.accessibilitySupport": "on"',
            '"security.workspace.trust.enabled": False',
            "QUALIFICATION_PREFIX",
            "tempfile.gettempdir()",
        ):
            self.assertIn(required, self.source)

    def test_each_uia_sample_is_independently_caught_and_series_continues(self) -> None:
        for required in (
            "SAMPLE_COUNT = 6",
            "for ordinal in range(1, SAMPLE_COUNT + 1):",
            "state = observe_bound_window(resolver, window_title)",
            'result["sample_errors"].append(',
            "traceback.format_exc()",
            "time.sleep(SAMPLE_INTERVAL_SECONDS)",
            'result["successful_sample_count"] += 1',
        ):
            self.assertIn(required, self.source)
        self.assertIn('result["successful_sample_count"] >= 1', self.source)

    def test_samples_remain_bound_to_exact_window_process_generation(self) -> None:
        for required in (
            "resolver.set_expected_process_id(bound_pid)",
            "state.window_handle != bound_hwnd",
            "state.process_id != bound_pid",
            "state.executable_name.casefold() != EXPECTED_EXECUTABLE",
            "state.process_generation != process_generation",
        ):
            self.assertIn(required, self.source)
        self.assertNotIn("GetRootControl", self.source)

    def test_diagnostic_records_semantic_candidates_and_role_counts(self) -> None:
        for required in (
            '"role_counts": dict(sorted(role_counts.items()))',
            '"semantic_candidates": _semantic_candidates(state, unique_filename)',
            '"named_controls": [',
            "SAMPLE_{ordinal}_SEMANTIC_CANDIDATES",
            "SAMPLE_{ordinal}_ROLE_COUNTS",
        ):
            self.assertIn(required, self.source)

    def test_cleanup_revalidates_randomized_window_identity(self) -> None:
        for required in (
            "driver._validated_cleanup_matches(",
            "expected_hwnd=bound_hwnd",
            "expected_pid=bound_pid",
            "expected_process_generation=process_generation",
            'driver._post_close(int(validated[0]["hwnd"]))',
            "len(matches) == 1 and len(validated) == 1",
            "app_root.is_relative_to(temp_root)",
        ):
            self.assertIn(required, self.source)


if __name__ == "__main__":
    unittest.main()
