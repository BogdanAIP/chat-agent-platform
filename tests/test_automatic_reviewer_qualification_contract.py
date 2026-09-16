from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "automatic-reviewer-qualification.py"
HARNESS = ROOT / "scripts" / "qualify-automatic-reviewer.ps1"


class AutomaticReviewerQualificationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = DRIVER.read_text(encoding="utf-8")
        self.harness = HARNESS.read_text(encoding="utf-8")

    def test_driver_parses_and_reuses_review_and_delegation_contracts(self) -> None:
        ast.parse(self.driver)
        self.assertIn("prepare_review_operation", self.driver)
        self.assertIn("mark_dispatch_attempted", self.driver)
        self.assertIn("review_delegation_identity", self.driver)
        self.assertIn("settle_review_from_delegation", self.driver)
        self.assertIn("reconcile_independent_review_result", self.driver)

    def test_harness_reuses_exact_head_generic_temporary_launcher(self) -> None:
        self.assertIn("launch-chatgpt-temporary-worker.ps1", self.harness)
        self.assertIn("-ExpectedHead", self.harness)
        self.assertIn("-WorkerKind", self.harness)
        self.assertIn("-ResultContractId", self.harness)
        self.assertIn("code-review", self.harness)
        self.assertIn("review_result_v1", self.harness)
        self.assertIn("fresh_readonly_worker_v1", self.harness)

    def test_harness_requires_clean_exact_head_before_review_task_creation(self) -> None:
        head_check = self.harness.index("EXACT_HEAD_MISMATCH")
        dirty_check = self.harness.index("Qualification source must be clean")
        prepare = self.harness.index("$prepareRaw =")
        self.assertLess(head_check, prepare)
        self.assertLess(dirty_check, prepare)

    def test_harness_never_adds_manual_send_or_result_copy_path(self) -> None:
        self.assertIn("CAP_REVIEW_MANUAL_SEND_REQUIRED=False", self.harness)
        self.assertIn("CAP_AUTOMATIC_REVIEWER_QUALIFICATION=PASS", self.harness)
        self.assertNotIn("Read-Host", self.harness)
        self.assertNotIn("Set-Clipboard", self.harness)
        self.assertNotIn("Get-Clipboard", self.harness)

    def test_qualification_state_is_separate_but_generic_state_remains_accepted_owner(self) -> None:
        self.assertIn("automatic-reviewer\\qualification", self.harness)
        self.assertIn("review_delegation_state_root", self.driver)
        self.assertNotIn("procedure-runtime", self.driver)


if __name__ == "__main__":
    unittest.main()
