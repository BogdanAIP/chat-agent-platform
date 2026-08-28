from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "source-code-research" / "SKILL.md"
BASELINE = ROOT / "project-context" / "ARCHITECTURE_REUSE_BASELINE.md"


class SourceCodeResearchContractTests(unittest.TestCase):
    def test_source_code_research_is_discoverable_and_requires_exact_ref_evidence(self) -> None:
        self.assertTrue(SKILL.is_file())
        text = SKILL.read_text(encoding="utf-8")

        required = (
            "name: source-code-research",
            "README-only/product-description review does not count as implementation evidence",
            "bind the repository to an exact commit SHA or immutable tag",
            "trace the relevant execution/state path",
            "inspect tests for the claimed invariant or lifecycle",
            "OPEN_IMPLEMENTED",
            "OPEN_PARTIAL",
            "DOCUMENTED_ONLY",
            "CLOSED_OR_UNKNOWN",
            "NOT_FOUND_AFTER_TARGETED_SEARCH",
            "### Source-code evidence",
            "A Stage Research Brief that relies on a public implementation but contains only README/docs-level evidence is incomplete",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_agent_harness_research_compares_codex_and_an_independent_implementation(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("`openai/codex` is a mandatory comparison reference", text)
        self.assertIn("at least **one independent mature open agent/harness implementation**", text)
        self.assertIn("Examples of currently relevant public repositories include", text)
        self.assertIn("`OpenHands/OpenHands`", text)
        self.assertIn("`aaif-goose/goose`", text)
        self.assertIn("`cline/cline`", text)
        self.assertIn("research candidates, not selected dependencies", text)

    def test_code_research_does_not_replace_domain_evidence_or_project_authority(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        for phrase in (
            "Source-code study complements domain evidence rather than replacing it",
            "A strong reference implementation is not automatically a dependency",
            "deterministic Control Plane authority",
            "project `WorkingState`",
            "Verification Kernel and independent Finish Gate",
            "bounded public semantic tool surface",
            "physical Browser/Windows verification guarantees",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_reuse_baseline_records_codex_as_reference_not_runtime_dependency(self) -> None:
        baseline = BASELINE.read_text(encoding="utf-8")

        self.assertIn("Agent session / long-lived host lifecycle and orchestration", baseline)
        self.assertIn("`openai/codex` as a source-code reference implementation, not a selected runtime dependency", baseline)
        self.assertIn("App Server/thread lifecycle", baseline)
        self.assertIn("agent-graph ownership", baseline)
        self.assertIn("project Control Plane authority", baseline)
        self.assertIn("unproven wake/scheduler semantics", baseline)
        self.assertIn("`REFERENCE_REVALIDATE_PER_STAGE`", baseline)
        self.assertIn(".agents/skills/source-code-research/SKILL.md", baseline)
        self.assertIn("exact upstream ref, concrete implementation paths/symbols", baseline)


if __name__ == "__main__":
    unittest.main()
