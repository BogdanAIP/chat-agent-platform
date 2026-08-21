from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "stage26-vscode-uia-ancestor-diagnostic-v2.py"


class Stage262EVSCodeUIAAncestorDiagnosticV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WRAPPER.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(WRAPPER))

    def test_wrapper_retries_only_two_physically_observed_com_hresults(self) -> None:
        self.assertIn("-2147220991", self.source)
        self.assertIn("-2147467261", self.source)
        self.assertIn("TRANSIENT_ANCESTOR_HRESULTS", self.source)
        self.assertIn("exc.args[0] in TRANSIENT_ANCESTOR_HRESULTS", self.source)
        self.assertIn("if not _is_transient_ancestor_com_error(exc):\n                    raise", self.source)

    def test_retry_reenters_full_base_ancestor_function(self) -> None:
        self.assertIn("original = base._focused_ancestor_chain", self.source)
        self.assertIn("return original(*args, **kwargs)", self.source)
        self.assertIn("base._focused_ancestor_chain = resilient_focused_ancestor_chain", self.source)
        self.assertIn("ANCESTOR_RETRY_LIMIT = 8", self.source)
        self.assertIn("ANCESTOR_RETRY_INTERVAL_SECONDS = 0.25", self.source)

    def test_wrapper_has_no_application_input_or_focus_mutation(self) -> None:
        forbidden = (
            "type_text_guarded",
            "arm_guarded_keyboard",
            "guarded_keyboard_frame",
            "require_foreground_hit_target",
            "SetForegroundWindow",
            "pyautogui",
            "pyperclip",
            "clipboard",
            "subprocess.run",
            "shell=True",
            "os.system",
            "act_guarded_coordinate",
            "press_guarded",
            "act_structural",
            "execute_windows",
        )
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.source)

    def test_wrapper_preserves_base_diagnostic_and_reports_retry_evidence(self) -> None:
        self.assertIn('BASE_DIAGNOSTIC = Path(__file__).with_name("stage26-vscode-uia-ancestor-diagnostic.py")', self.source)
        self.assertIn('print(f"ANCESTOR_INNER_RETRY_COUNT={len(retry_events)}")', self.source)
        self.assertIn('print(f"ANCESTOR_INNER_RETRIES={retry_events}")', self.source)
        self.assertIn("exit_code = int(base.main())", self.source)


if __name__ == "__main__":
    unittest.main()
