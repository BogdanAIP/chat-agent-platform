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


if __name__ == "__main__":
    unittest.main()
