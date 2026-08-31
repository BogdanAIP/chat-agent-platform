from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"
STRATEGY = CONTEXT / "BENCHMARK_EVALUATION_STRATEGY.md"
DOCUMENT_STATUS = CONTEXT / "DOCUMENT_STATUS.md"
REVIEW_RESEARCH = CONTEXT / "AUTOMATIC_REVIEWER_RESEARCH.md"
AGENTS = ROOT / "AGENTS.md"


class BenchmarkEvaluationStrategyContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = STRATEGY.read_text(encoding="utf-8")
        self.document_status = DOCUMENT_STATUS.read_text(encoding="utf-8")
        self.review_research = REVIEW_RESEARCH.read_text(encoding="utf-8")
        self.agents = AGENTS.read_text(encoding="utf-8")
        self.folded = self.strategy.casefold()
        self.review_folded = self.review_research.casefold()

    def test_strategy_is_registered_and_discoverable_cross_capability_owner(self) -> None:
        self.assertIn("AUTHORITATIVE CROSS-CAPABILITY EVALUATION STRATEGY", self.strategy)
        self.assertIn("not a new roadmap stage", self.folded)
        self.assertIn("independent public benchmark", self.folded)
        self.assertIn("immediate implementation priority remains the bounded automatic reviewer", self.folded)
        self.assertIn("BENCHMARK_EVALUATION_STRATEGY.md", self.document_status)
        self.assertIn("AUTHORITATIVE CROSS-CAPABILITY EVALUATION STRATEGY", self.document_status)
        self.assertIn("Evaluation-strategy discovery rule", self.document_status)
        self.assertIn("BENCHMARK_EVALUATION_STRATEGY.md", self.agents)
        self.assertIn("capability becomes honestly externally evaluable", self.agents)
        self.assertIn("capability/stage is being closed with comparative evidence", self.agents)

    def test_external_benchmarks_do_not_replace_project_acceptance(self) -> None:
        for concept in (
            "physical / adversarial / fault-injection gates",
            "benchmark score cannot authorize a consequence",
            "PASS | FAIL | UNKNOWN",
            "source/install/runtime provenance requirements",
            "Finish Gate evidence",
            "Preserve fail-closed behavior",
        ):
            self.assertIn(concept.casefold(), self.folded)
        for policy_phrase in (
            "Benchmark scores are quality/competitive evidence only",
            "Do not create a privileged `benchmark CAP`",
            "fixed external regression subset",
            "official/holdout evidence",
        ):
            self.assertIn(policy_phrase, self.agents)

    def test_harness_is_selected_per_domain_not_forced_through_harbor(self) -> None:
        self.assertIn("There is no requirement to force all benchmarks through one framework", self.strategy)
        for family in ("Harbor", "BrowserGym", "AgentLab", "OSWorld 2.0", "Terminal-Bench", "TheAgentCompany", "METR Time Horizon"):
            self.assertIn(family, self.strategy)

    def test_benchmark_ladder_covers_current_and_future_capability_families(self) -> None:
        for benchmark in (
            "ReviewBench", "SWE-Review-Bench", "CR-Bench", "MiniWoB", "WebArena-Verified",
            "WorkArena", "VisualWebArena", "AssistantBench", "TimeWarp", "OSWorld 2.0",
            "Terminal-Bench", "SWE-bench", "TheAgentCompany", "TH50", "TH80",
        ):
            self.assertIn(benchmark, self.strategy)
        self.assertIn("DEFERRED UNTIL CAPABILITY EXISTS", self.strategy)
        self.assertIn("multi-agent benchmarks remain deferred", self.folded)

    def test_frequency_is_tiered_instead_of_full_suite_per_pr(self) -> None:
        for heading in (
            "Every significant implementation PR",
            "Capability/stage closure or material capability integration",
            "Major release / major architecture change / public comparison",
        ):
            self.assertIn(heading, self.strategy)
        self.assertIn("Do not run every full benchmark after every PR", self.strategy)

    def test_dev_regression_holdout_and_provenance_are_required(self) -> None:
        for phrase in (
            "development set", "fixed regression subset", "official / holdout evaluation",
            "CAP source identity / exact commit or release", "benchmark name + exact release/version/ref",
            "benchmark adapter source/version", "step/action/token budget",
            "number of runs / repetitions / seeds", "known deviations from official evaluation protocol",
        ):
            self.assertIn(phrase, self.strategy)

    def test_benchmark_cap_cannot_gain_hidden_tools(self) -> None:
        self.assertIn("Do not create a privileged `benchmark CAP`", self.strategy)
        self.assertIn("grant extra product authority", self.folded)
        self.assertIn("expose a shell only for evaluation", self.folded)

    def test_reviewer_research_remains_first_specific_application(self) -> None:
        self.assertIn("harbor", self.review_folded)
        self.assertIn("evaluation", self.review_folded)
        self.assertIn("not production", self.review_folded)
        self.assertIn("ReviewBench", self.review_research)
        self.assertIn("SWE-Review-Bench", self.review_research)
        self.assertIn("CR-Bench", self.review_research)
        self.assertIn("Reviewer — first active rung", self.strategy)


if __name__ == "__main__":
    unittest.main()
