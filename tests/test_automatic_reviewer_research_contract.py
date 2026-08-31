from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"
RESEARCH = CONTEXT / "AUTOMATIC_REVIEWER_RESEARCH.md"
CURRENT = CONTEXT / "CURRENT_STATE.md"
REUSE = CONTEXT / "ARCHITECTURE_REUSE_BASELINE.md"
BENCHMARK_STRATEGY = CONTEXT / "BENCHMARK_EVALUATION_STRATEGY.md"
SKILL = ROOT / ".agents" / "skills" / "code-review" / "SKILL.md"


class AutomaticReviewerResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.research = RESEARCH.read_text(encoding="utf-8")
        self.current = CURRENT.read_text(encoding="utf-8")
        self.reuse = REUSE.read_text(encoding="utf-8")
        self.benchmark_strategy = BENCHMARK_STRATEGY.read_text(encoding="utf-8")
        self.skill = SKILL.read_text(encoding="utf-8")
        self.folded = self.research.casefold()

    def test_stage_research_has_required_substantive_sections(self) -> None:
        for heading in (
            "## Goal",
            "## Non-goals",
            "## Problem evidence",
            "## Solution evidence",
            "## Current implementation evidence",
            "## Architecture lineage comparison",
            "## Architecture primitives and adjacent domains",
            "## Source-code evidence",
            "## Best current approaches",
            "## Failure lessons",
            "## Alternatives comparison",
            "## Product / options / ecosystem comparison",
            "## Failure / crash matrix",
            "## Evaluation method",
            "## Acceptance checks",
            "## Stage decision",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.research)

    def test_narrow_is_proposed_until_pr_acceptance_not_preaccepted(self) -> None:
        self.assertIn("NARROW (PROPOSED UNTIL THIS PR IS ACCEPTED)", self.research)
        self.assertIn("Production implementation remains blocked until this research PR", self.research)
        self.assertIn("effective only after this PR is accepted and merged", self.research)
        self.assertIn("AUTOMATIC_REVIEWER_RESEARCH.md", self.current)
        self.assertIn("Production implementation is **still blocked** until #140", self.current)

    def test_first_slice_stays_review_specific(self) -> None:
        for phrase in ("launch_independent_review_v1", "review_run_id", "one top-level PR", "manual fallback"):
            self.assertIn(phrase, self.research)
        self.assertIn("waiting -> wake -> planner continuation", self.folded)
        self.assertIn("same-task-continuation", self.folded)
        self.assertIn("scheduler/event bus", self.folded)
        self.assertIn("automatic wake/resampling", self.folded)

    def test_local_operation_uses_lock_and_separate_crash_atomic_checkpoint(self) -> None:
        for phrase in (
            "Accepted Stage 26.3C cooperating-runner lock",
            "Accepted Stage 26.3C crash-atomic checkpoint persistence",
            "_TaskLock",
            "_write_checkpoint",
            "_load_checkpoint",
            "_checkpoint_matches_program",
            "same-directory sibling temp",
            "flush",
            "os.fsync",
            "os.replace",
            "no unlocked fallback",
        ):
            self.assertIn(phrase, self.research)

    def test_retained_record_corruption_and_temp_residue_fail_closed(self) -> None:
        for phrase in (
            "never recreate/reset it automatically",
            "canonical absent and a matching sibling temp residue exists",
            "fail closed/manual recovery",
            "canonical valid and sibling temp residue exists",
            "temp is never consumed as state",
            "write, flush, `os.fsync` or `os.replace` failure",
            "no external browser launch",
            "canonical disappearance",
        ):
            self.assertIn(phrase, self.research)

    def test_dispatch_transition_is_durable_before_browser_launch(self) -> None:
        for phrase in (
            "dispatch-attempted",
            "successfully replaced into canonical state **before** invoking the OS/browser launch consequence",
            "crash before that replace",
            "crash after successful replace",
            "forbids an automatic relaunch",
        ):
            self.assertIn(phrase, self.research)

    def test_materially_distinct_alternatives_are_recorded(self) -> None:
        for phrase in (
            "SQLite transaction",
            "append-only journal/WAL",
            "raw/in-place JSON write",
            "Web Locks",
            "service-worker in-memory Set",
            "Native Messaging",
            "local callback/result server",
            "user copy/paste",
        ):
            self.assertIn(phrase, self.research)

    def test_source_code_evidence_is_pinned_and_classified(self) -> None:
        for phrase in (
            "harbor-framework/harbor",
            "389bd4f8ce796ef4a97de4b62675021e262c8e76",
            "openai/codex",
            "94cbbddafc1776d5e377bca1b05932c697e82238",
            "OpenHands/OpenHands",
            "1098d73df42351a31b2940557efb9fe8750365c4",
            "classification = OPEN_SOURCE",
            "lesson =",
            "NOT_FOUND",
        ):
            self.assertIn(phrase, self.research)

    def test_browser_claim_remains_atomic_and_separate_from_local_lock(self) -> None:
        for phrase in (
            "MV3 extension service worker",
            "extension-origin IndexedDB",
            "readwrite transaction",
            "review_send_claims",
            "add primary-key record review_run_id",
            "only the caller whose add transaction committed receives claim_status=granted",
        ):
            self.assertIn(phrase, self.research)

    def test_result_handoff_and_final_rescan_fail_closed(self) -> None:
        self.assertIn("top-level PR comment collection", self.research)
        self.assertIn("complete collection again", self.research)
        self.assertIn("matching-comment count == 1", self.research)
        self.assertIn("re-fetches that sole exact comment", self.research)
        self.assertIn("late duplicate", self.research)
        self.assertIn("author mismatch", self.research)

    def test_skill_authorizes_only_bounded_automatic_result_publication(self) -> None:
        self.assertRegex(self.skill, r'(?m)^\s*version:\s*"1\.1"\s*$')
        self.assertIn("## 14. Bounded automatic result-publication envelope", self.skill)
        self.assertIn("top-level PR Conversation comment", self.skill)
        self.assertIn("does not authorize any other GitHub mutation", self.skill)
        self.assertIn("Do not retry", self.skill)

    def test_benchmark_plan_remains_evaluation_only(self) -> None:
        for phrase in ("Harbor", "ReviewBench", "SWE-Review-Bench", "CR-Bench"):
            self.assertIn(phrase, self.research)
        self.assertIn("Do not collapse these planes into one score", self.research)
        self.assertIn("baseline, not a release exam", self.folded)
        self.assertIn("Reviewer — first active rung", self.benchmark_strategy)
        self.assertIn("code-review evaluation harness", self.reuse.casefold())
        self.assertIn("selected_evaluation_only", self.reuse.casefold())


if __name__ == "__main__":
    unittest.main()
