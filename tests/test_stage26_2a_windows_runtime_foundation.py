import ast
import unittest
from pathlib import Path

from runtime.windows.verifier import (
    VerificationStatus,
    verify_expected_fields,
)


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_RUNTIME = ROOT / "runtime" / "windows"
INIT = WINDOWS_RUNTIME / "__init__.py"
ACTUATION = WINDOWS_RUNTIME / "actuation.py"
RESOLVER = WINDOWS_RUNTIME / "window_scoped_uia.py"
VERIFIER = WINDOWS_RUNTIME / "verifier.py"


class Stage262AWindowsRuntimeFoundationTests(unittest.TestCase):
    def test_runtime_python_assets_parse(self):
        for path in (INIT, ACTUATION, RESOLVER, VERIFIER):
            ast.parse(path.read_text(encoding="utf-8"))

    def test_empty_expectation_is_unknown_not_success(self):
        result = verify_expected_fields(
            before={"state": "old"},
            after={"state": "new"},
            expectation={},
        )
        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertFalse(result.passed)

    def test_missing_postcondition_evidence_is_unknown(self):
        result = verify_expected_fields(
            before={},
            after={"window": "fixture"},
            expectation={"window": "fixture", "saved": True},
        )
        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertEqual(result.evidence["missing_fields"], ["saved"])

    def test_contradictory_postcondition_is_fail(self):
        result = verify_expected_fields(
            before={"saved": False},
            after={"saved": False},
            expectation={"saved": True},
        )
        self.assertEqual(result.status, VerificationStatus.FAIL)
        self.assertFalse(result.passed)
        self.assertEqual(
            result.evidence["mismatches"]["saved"],
            {"expected": True, "observed": False},
        )

    def test_exact_current_postcondition_is_pass(self):
        result = verify_expected_fields(
            before={"saved": False},
            after={"saved": True, "window": "fixture"},
            expectation={"saved": True, "window": "fixture"},
        )
        self.assertEqual(result.status, VerificationStatus.PASS)
        self.assertTrue(result.passed)
        self.assertEqual(result.evidence["verified_fields"], ["saved", "window"])

    def test_verifier_is_explicitly_non_authorizing(self):
        source = VERIFIER.read_text(encoding="utf-8")
        self.assertIn("it never authorizes an action", source)
        self.assertIn("delivery receipts as completion", source)
        for forbidden in (
            "click(",
            "SendInput",
            "subprocess",
            "os.system",
            "workspace_read",
            "workspace_write",
            "web_interact",
        ):
            self.assertNotIn(forbidden, source)

    def test_runtime_package_does_not_add_chat_tool_names(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (INIT, ACTUATION, RESOLVER, VERIFIER)
        )
        for forbidden in (
            "desktop_observe",
            "desktop_interact",
            "procedure_run",
            "tool_invoke",
            "workflow_execute_generic",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
