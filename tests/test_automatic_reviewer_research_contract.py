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

    def test_research_decision_is_narrow_and_current_state_uses_it(self) -> None:
        self.assertIn("Status: **STAGE RESEARCH — NARROW**", self.research)
        self.assertIn("**NARROW.**", self.research)
        self.assertIn("AUTOMATIC_REVIEWER_RESEARCH.md", self.current)
        self.assertIn("decision **NARROW**", self.current)

    def test_first_slice_stays_review_specific(self) -> None:
        for phrase in (
            "launch_independent_review_v1",
            "review_run_id",
            "one top-level PR conversation comment",
            "one automatic Send attempt",
            "manual fresh-review path",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

        folded = self.research.casefold()
        self.assertIn("waiting -> wake -> planner continuation", folded)
        self.assertIn("same-task-continuation", folded)
        self.assertIn("generic scheduler/event bus", folded)
        self.assertIn("automatic wake/resampling", folded)

    def test_atomic_operation_claim_reuses_accepted_os_lock_before_record_access(self) -> None:
        for phrase in (
            "Accepted Stage 26.3C cooperating-runner lock",
            "OS-backed nonblocking task lock",
            "acquire existing project OS-backed exclusive lock",
            "before any durable review record is read, created or assigned a nonce",
            "hold it across the irreversible dispatch-attempt transition and one OS/browser launch decision",
            "two concurrent same-operation callers before record exists",
            "exactly one acquires OS lock",
            "process dies while holding lock before record creation",
            "OS releases lock",
            "no unlocked fallback",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

        self.assertIn("**REUSE_MORE**", self.research)
        self.assertIn("new concurrency/lease/database framework", self.research)

    def test_dispatch_mark_is_written_under_lock_before_external_launch(self) -> None:
        for phrase in (
            "persist irreversible dispatch-attempted state",
            "invoke the one OS/browser launch consequence",
            "while the operation lock is held and before",
            "durable `dispatch-attempted` state forbids a second automatic launch",
            "crash after durable record/nonce creation but before dispatch-attempted",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

    def test_result_handoff_is_private_nonce_bound_and_fail_closed(self) -> None:
        for phrase in (
            "high-entropy random nonce generated exactly once",
            "not published to the PR before the result comment",
            "comment.author == configured expected result principal",
            "comment was not edited after creation",
            "Any second result comment carrying the same expected `review_run_id`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

        folded = self.research.casefold()
        self.assertIn("duplicate/ambiguous", folded)
        self.assertIn("fail closed", folded)

    def test_final_merge_gate_rescans_all_matching_result_comments(self) -> None:
        for phrase in (
            "Final automatic-result merge gate",
            "query the complete top-level PR Conversation-comment collection again",
            "all pages, not only the saved comment",
            "matching-comment count == 1",
            "matching comment id == originally accepted comment id",
            "body digest == originally accepted body digest",
            "re-fetches that sole exact comment by id",
            "late second matching comment",
            "final full collection rescan",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

    def test_skill_authorizes_only_bounded_automatic_result_publication(self) -> None:
        self.assertRegex(self.skill, r'(?m)^\s*version:\s*"1\.1"\s*$')
        self.assertIn("## 14. Bounded automatic result-publication envelope", self.skill)
        self.assertIn("exactly one", self.skill)
        self.assertIn("top-level PR Conversation comment", self.skill)
        self.assertIn("does not authorize any other GitHub mutation", self.skill)
        self.assertIn("Do not retry", self.skill)
        self.assertIn("review_run_id=<same value received in REVIEW_REQUEST_V1>", self.skill)

    def test_reviewer_benchmark_plan_remains_first_specific_application(self) -> None:
        for phrase in (
            "Harbor",
            "ReviewBench",
            "SWE-Review-Bench",
            "CR-Bench",
            "Plane A — reviewer semantic quality",
            "Plane B — CAP reviewer lifecycle reliability",
            "development set",
            "holdout set",
            "CAP Review Regression Set",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

        self.assertIn("Do not collapse these planes into one score", self.research)
        self.assertIn("baseline, not a release exam", self.research)
        self.assertIn("Reviewer — first active rung", self.benchmark_strategy)

    def test_harbor_is_evaluation_only_for_reviewer(self) -> None:
        research_folded = self.research.casefold()
        reuse_folded = self.reuse.casefold()
        strategy_folded = self.benchmark_strategy.casefold()

        self.assertIn("harbor is not production authority", research_folded)
        self.assertIn("harbor is selected as the **evaluation harness**", research_folded)
        self.assertIn("not as the reviewer launch/control plane", research_folded)
        self.assertIn("code-review evaluation harness", reuse_folded)
        self.assertIn("selected_evaluation_only", reuse_folded)
        self.assertIn("automatic independent-review launch / correlation / result publication", reuse_folded)
        self.assertIn("no requirement to force all benchmarks through one framework", strategy_folded)

    def test_quality_threshold_is_evidence_based_not_prebaked(self) -> None:
        folded = self.research.casefold()
        self.assertIn("first benchmark run is a **baseline, not a release exam**", folded)
        self.assertIn("do not invent an arbitrary target", folded)
        self.assertIn("semantic quality must not materially regress", folded)


if __name__ == "__main__":
    unittest.main()
