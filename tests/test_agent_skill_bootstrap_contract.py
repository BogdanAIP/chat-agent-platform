from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
SKILLS_ROOT = ROOT / ".agents" / "skills"
REUSE_BASELINE = ROOT / "project-context" / "ARCHITECTURE_REUSE_BASELINE.md"


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

    def test_stage_research_compares_against_canonical_architecture_reuse_lineage(self) -> None:
        self.assertTrue(REUSE_BASELINE.is_file())
        skill = (SKILLS_ROOT / "stage-research" / "SKILL.md").read_text(encoding="utf-8")
        baseline = REUSE_BASELINE.read_text(encoding="utf-8")
        agents = AGENTS.read_text(encoding="utf-8")

        for phrase in (
            "## 2A. Architecture Lineage Gate — compare with canonical reuse baseline",
            "project-context/ARCHITECTURE_REUSE_BASELINE.md",
            "### Architecture lineage comparison",
            "KEEP",
            "REUSE_MORE",
            "REFINE",
            "REPLACE",
            "DEFER",
            "REJECT",
            "custom code duplicates mechanics that the project had already selected for upstream reuse",
            "previously selected baseline component",
            "Role-level `DEFER` is distinct from the top-level Stage Research decision `DEFER`",
            "cannot return `PROCEED` or `NARROW` while leaving it deferred",
        ):
            with self.subTest(skill_phrase=phrase):
                self.assertIn(phrase, skill)

        for phrase in (
            "AUTHORITATIVE RESEARCH COMPARISON BASELINE",
            "canonical baseline for comparing new research with prior design choices",
            "Procedure-local checkpoint / durable resume mechanics",
            "OpenAdapt Flow 1.31.0",
            "Capability-spanning operational state",
            "project-owned `WorkingState`",
            "Transition verification authority",
            "project Verification Kernel",
            "Task completion authority",
            "project independent Finish Gate",
            "REPLACE` and `REJECT` require explicit evidence",
            "Role-level `DEFER` is distinct from the top-level Stage Research decision `DEFER`",
        ):
            with self.subTest(baseline_phrase=phrase):
                self.assertIn(phrase, baseline)

        for phrase in (
            "Read `project-context/ARCHITECTURE_REUSE_BASELINE.md` when `stage-research` applies",
            "canonical prior-decision comparison baseline",
            "KEEP`, `REUSE_MORE`, `REFINE`, `REPLACE`, `DEFER`, or `REJECT`",
            "accepted lineage change must update the baseline before or with merge",
            "A role-level lineage `DEFER` is not permission to continue past an unresolved requirement",
        ):
            with self.subTest(agent_phrase=phrase):
                self.assertIn(phrase, agents)

    def test_initial_material_persistence_or_concurrency_change_triggers_stage_research(self) -> None:
        skill = (SKILLS_ROOT / "stage-research" / "SKILL.md").read_text(encoding="utf-8")
        agents = AGENTS.read_text(encoding="utf-8")

        for phrase in (
            "material change to persistence ordering/ownership",
            "retry/reconciliation",
            "concurrency",
            "identity/correlation",
            "including inside an existing subsystem",
        ):
            with self.subTest(skill_phrase=phrase):
                self.assertIn(phrase, skill)

        self.assertIn("material release-critical change to persistence ordering/ownership", agents)
        self.assertIn("because the change occurs inside an existing subsystem", agents)

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

    def test_defer_is_fail_closed_and_never_opens_implementation(self) -> None:
        skill = (SKILLS_ROOT / "stage-research" / "SKILL.md").read_text(encoding="utf-8")
        agents = AGENTS.read_text(encoding="utf-8")

        for phrase in (
            "`DEFER` is fail-closed",
            "resume production implementation only after `PROCEED` or `NARROW`",
            "if the fresh decision is `DEFER`, keep implementation stopped",
            "`DEFER` never opens or resumes production implementation",
        ):
            with self.subTest(skill_phrase=phrase):
                self.assertIn(phrase, skill)

        self.assertIn("only `PROCEED` or `NARROW` opens implementation", agents)
        self.assertIn("`DEFER` keeps implementation stopped", agents)


if __name__ == "__main__":
    unittest.main()
