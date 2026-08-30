from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"
RESEARCH = CONTEXT / "AUTOMATIC_REVIEWER_RESEARCH.md"
CURRENT = CONTEXT / "CURRENT_STATE.md"
REUSE = CONTEXT / "ARCHITECTURE_REUSE_BASELINE.md"


class AutomaticReviewerResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.research = RESEARCH.read_text(encoding="utf-8")
        self.current = CURRENT.read_text(encoding="utf-8")
        self.reuse = REUSE.read_text(encoding="utf-8")

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
        self.assertIn("general same-task continuation", folded)
        self.assertIn("generic scheduler/event bus", folded)
        self.assertIn("automatic wake/resampling of the unfinished development conversation", folded)

    def test_result_handoff_is_private_nonce_bound_and_fail_closed(self) -> None:
        for phrase in (
            "high-entropy random nonce generated exactly once",
            "not published to the PR before the result comment",
            "comment.author == configured expected result principal",
            "comment was not edited after creation",
            "Any second result comment carrying the same expected `review_run_id`",
            "body digest/observed metadata",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

        folded = self.research.casefold()
        self.assertIn("duplicate/ambiguous", folded)
        self.assertIn("fail closed", folded)

    def test_benchmark_plan_keeps_external_and_internal_quality_planes_separate(self) -> None:
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

    def test_harbor_is_evaluation_only_in_research_and_reuse_baseline(self) -> None:
        research_folded = self.research.casefold()
        reuse_folded = self.reuse.casefold()

        self.assertIn("harbor is not production authority", research_folded)
        self.assertIn("harbor is selected as the **evaluation harness**", research_folded)
        self.assertIn("not as the reviewer launch/control plane", research_folded)
        self.assertIn("code-review evaluation harness", reuse_folded)
        self.assertIn("selected_evaluation_only", reuse_folded)
        self.assertIn("automatic independent-review launch / correlation / result publication", reuse_folded)

    def test_quality_threshold_is_evidence_based_not_prebaked(self) -> None:
        folded = self.research.casefold()
        self.assertIn("first benchmark run is a **baseline, not a release exam**", folded)
        self.assertIn("do not invent an arbitrary target", folded)
        self.assertIn("semantic quality must not materially regress", folded)


if __name__ == "__main__":
    unittest.main()
