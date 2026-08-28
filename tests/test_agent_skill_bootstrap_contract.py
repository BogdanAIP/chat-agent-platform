from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
SKILLS_ROOT = ROOT / ".agents" / "skills"


class AgentSkillBootstrapContractTests(unittest.TestCase):
    def test_fresh_session_resolves_repository_skills_before_planning(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")

        bootstrap_heading = "## Mandatory session bootstrap — resolve repository skills before planning"
        read_first_heading = "## Read first"
        development_heading = "## Development method"

        self.assertIn(bootstrap_heading, agents)
        self.assertIn(read_first_heading, agents)
        self.assertIn(development_heading, agents)
        self.assertLess(agents.index(bootstrap_heading), agents.index(read_first_heading))
        self.assertLess(agents.index(bootstrap_heading), agents.index(development_heading))

        required_contract = (
            ".agents/skills/*/SKILL.md",
            "before proposing an implementation plan or editing production code",
            "Never rely on remembered or cached skill text",
            "current source ref/head",
            "Stage Research Brief",
            "PROCEED",
            "NARROW",
            "DEFER",
            "fail closed",
            "next development invocation reruns this bootstrap",
        )
        for phrase in required_contract:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agents)

    def test_repository_skills_have_discoverable_frontmatter_and_stage_research_is_bound(self) -> None:
        skills = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
        self.assertTrue(skills, "Repository must contain at least one discoverable skill")

        for skill in skills:
            text = skill.read_text(encoding="utf-8")
            with self.subTest(skill=skill.parent.name):
                self.assertTrue(text.startswith("---\n"))
                self.assertIn("\nname:", text)
                self.assertIn("\ndescription:", text)

        agents = AGENTS.read_text(encoding="utf-8")
        stage_research = SKILLS_ROOT / "stage-research" / "SKILL.md"
        self.assertTrue(stage_research.is_file())
        self.assertIn(".agents/skills/stage-research/SKILL.md", agents)

    def test_bootstrap_does_not_create_runtime_or_post_merge_authority(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")
        bootstrap = agents.split("## Read first", 1)[0]

        self.assertIn("does **not** autonomously start the next stage", bootstrap)
        self.assertIn("Do not create a post-merge daemon", bootstrap)
        self.assertIn("runtime `SkillGate`", bootstrap)
        self.assertIn("Control Plane authority", bootstrap)

    def test_stage_research_requires_solution_depth_not_only_problem_research(self) -> None:
        skill = (SKILLS_ROOT / "stage-research" / "SKILL.md").read_text(encoding="utf-8")

        required = (
            "## 3. Research Scope Expansion Gate",
            "architecture primitive/mechanism",
            "mature engineering domain",
            "## 6. Separate problem evidence from solution evidence",
            "### Problem evidence",
            "### Solution evidence",
            "three materially distinct architecture approaches",
            "## 9. Failure/Crash Matrix Gate",
            "concurrent resume / duplicate worker / duplicate caller",
            "identity replacement or ABA-style state reuse",
            "## 14. Design-change invalidation and re-entry",
            "invalid for implementation authority",
            "PR-body edit that merely restates the new design",
            "`NARROW` means a narrower **implementation scope**, not a lower research standard",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill)

    def test_material_architecture_change_reenters_research_before_more_production_code(self) -> None:
        agents = AGENTS.read_text(encoding="utf-8")

        required = (
            "materially new architecture primitive",
            "treat the prior Stage Research Brief as invalid",
            "re-enter the applicable research skill before continuing production implementation",
            "`NARROW` narrows implementation scope only",
            "separate evidence that the problem exists from evidence that the proposed mechanism is an appropriate solution",
            "failure/crash matrix",
            "Merely editing the PR body to describe the new design does not satisfy this requirement",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
