from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"


class LiveContextStageStatusTests(unittest.TestCase):
    def test_live_context_marks_26_3b_and_26_3c_accepted_current(self) -> None:
        files = (
            "CURRENT_STATE.md",
            "CONTINUATION_CONTEXT.md",
            "START_HERE.md",
            "ROADMAP.md",
            "PROJECT_RISKS.md",
            "DOCUMENT_STATUS.md",
        )
        combined = "\n".join((CONTEXT / name).read_text(encoding="utf-8") for name in files)
        folded = combined.casefold()
        self.assertIn("26.3b", folded)
        self.assertIn("accepted", folded)
        self.assertIn("closed", folded)
        self.assertIn("26.3c", folded)
        self.assertIn("workingstate", folded)
        self.assertIn("loopguard", folded)
        self.assertIn("l1 foundation", folded)
        self.assertIn("production", folded)
        self.assertNotIn("active architecture/docs pr = #116", folded)
        self.assertNotIn("active — final provenance gap", folded)
        self.assertNotIn("pr #114 fresh hosted checks", folded)

    def test_live_context_does_not_pin_old_main_snapshots_or_raw_local_evidence(self) -> None:
        files = (
            "CURRENT_STATE.md",
            "CONTINUATION_CONTEXT.md",
            "START_HERE.md",
            "PROJECT_RISKS.md",
        )
        for name in files:
            text = (CONTEXT / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertNotIn("500bfc646a14892ea655369c20c8f8d725fccfeb", text)
                self.assertNotIn("C:\\Users\\", text)
                self.assertIn("EVIDENCE_INDEX.md", text)

    def test_exact_browser_provenance_evidence_lives_in_evidence_index(self) -> None:
        evidence = (CONTEXT / "EVIDENCE_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("Stage 26.3B Browser stronger source-provenance repeat", evidence)
        self.assertIn("e29517fdf1c940d36bc822cfcc1a729ed7dd9574", evidence)
        self.assertIn("SAVE_COUNT=1", evidence)
        self.assertIn("AUDIT_COUNT=1", evidence)
        self.assertIn("EXTERNAL_FINISH_GATE=DONE", evidence)
        self.assertIn("headless Playwright/Chrome", evidence)

    def test_post_26_3c_risk_and_evidence_owners_match_accepted_boundary(self) -> None:
        risks = (CONTEXT / "PROJECT_RISKS.md").read_text(encoding="utf-8")
        evidence = (CONTEXT / "EVIDENCE_INDEX.md").read_text(encoding="utf-8")
        continuation = (CONTEXT / "CONTINUATION_CONTEXT.md").read_text(encoding="utf-8")
        constraints = (CONTEXT / "CONSTRAINTS.md").read_text(encoding="utf-8")

        self.assertIn("Stage 26.3C is **accepted/closed", risks)
        self.assertNotIn(
            "finish Stage 26.3C production WorkingState/restart-reconciliation integration",
            risks,
        )

        self.assertIn(
            "Stage 26.3C production WorkingState/restart reconciliation (#126)",
            evidence,
        )
        self.assertIn(
            "d53e65d8804b28af0da6902e9beee3991bb26802",
            evidence,
        )
        not_accepted = evidence.split("## Not yet physically/production accepted", 1)[1]
        self.assertNotIn(
            "Stage 26.3C **production** WorkingState/restart-reconciliation integration",
            not_accepted,
        )
        self.assertIn("broader cross-capability WorkingState/reconciliation/recovery", not_accepted)

        self.assertIn("intentionally does **not** duplicate the active stage", continuation)
        self.assertNotIn(
            "first consequence-bearing production/restart integration",
            continuation,
        )

        self.assertIn("Stage 26.3C WorkingState/reconciliation/budget/LoopGuard is accepted/closed", constraints)
        self.assertIn("`CURRENT_STATE.md` owns immediate work", constraints)
        self.assertNotIn(
            "current release-critical work is its consequence-bearing production/restart integration",
            constraints,
        )

    def test_26_3b_stage_contract_is_no_longer_classified_active(self) -> None:
        status = (CONTEXT / "DOCUMENT_STATUS.md").read_text(encoding="utf-8")
        line = next(
            line for line in status.splitlines()
            if "`STAGE26_3B_VERIFICATION_KERNEL.md`" in line
        )
        folded = line.casefold()
        self.assertIn("accepted", folded)
        self.assertNotIn("active", folded)

    def test_browser_runtime_output_ownership_debt_is_explicit(self) -> None:
        debt = (CONTEXT / "TECH_DEBT.md").read_text(encoding="utf-8")
        assurance = (CONTEXT / "MUTATION_ASSURANCE.md").read_text(encoding="utf-8")
        self.assertIn("TD-010", debt)
        self.assertIn("Playwright", debt)
        self.assertIn("runtime output", debt.casefold())
        self.assertIn("SRC-003", assurance)
        self.assertIn("runtime", assurance.casefold())
        self.assertIn("source worktree", assurance.casefold())

    def test_current_state_keeps_exact_evidence_out_of_live_status(self) -> None:
        current = (CONTEXT / "CURRENT_STATE.md").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\b[0-9a-f]{40}\b", current))
        self.assertNotIn("QUALIFICATION_ROOT=", current)
        self.assertNotIn("PROJECT_HEAD=", current)


if __name__ == "__main__":
    unittest.main()
