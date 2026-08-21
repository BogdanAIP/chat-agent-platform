from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "scripts" / "stage26-vscode-uia-diagnostic.py"


class Stage262EVSCodeUiaDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = DIAGNOSTIC.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(DIAGNOSTIC))

    def test_diagnostic_is_read_only_with_respect_to_application_input(self) -> None:
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
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.source)
        self.assertIn('"keyboard_action_count": 0', self.source)
        self.assertIn('"pointer_action_count": 0', self.source)

    def test_diagnostic_uses_same_isolated_vscode_contract(self) -> None:
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

    def test_diagnostic_samples_only_the_exact_bound_window(self) -> None:
        for required in (
            "resolver.set_expected_process_id(bound_pid)",
            "state = observe_bound_window(resolver, window_title)",
            "state.window_handle != bound_hwnd",
            "state.process_id != bound_pid",
            "state.executable_name.casefold() != EXPECTED_EXECUTABLE",
            "SAMPLE_COUNT = 4",
        ):
            self.assertIn(required, self.source)
        self.assertNotIn("GetRootControl", self.source)

    def test_diagnostic_records_focus_and_editor_candidate_evidence_without_authorizing(self) -> None:
        for required in (
            '"focus_evidence": _focus_evidence(state)',
            '"focused_controls": _focused_controls(state)',
            '"editor_candidates": _editor_candidates(state, unique_filename)',
            '"named_controls": _named_controls(state)',
            "SAMPLE_{sample['sample']}_EDITOR_CANDIDATES",
            "SAMPLE_{sample['sample']}_NAMED_CONTROLS",
        ):
            self.assertIn(required, self.source)
        self.assertNotIn("_focused_editor_control(", self.source)

    def test_cleanup_is_randomized_and_identity_revalidated(self) -> None:
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
