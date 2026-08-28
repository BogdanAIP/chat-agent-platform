from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"


class ComputerUseArchitectureContractTests(unittest.TestCase):
    def test_computer_use_architecture_is_classified_and_authoritative(self) -> None:
        architecture = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")
        status = (CONTEXT / "DOCUMENT_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("AUTHORITATIVE ARCHITECTURAL DIRECTION", architecture)
        self.assertIn("`COMPUTER_USE_ARCHITECTURE.md`", status)
        self.assertIn("AUTHORITATIVE", status)

    def test_state_first_hybrid_loop_and_finish_gate_are_durable_decisions(self) -> None:
        decisions = (CONTEXT / "DECISIONS.md").read_text(encoding="utf-8")
        architecture = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")
        control = (CONTEXT / "CONTROL_PLANE.md").read_text(encoding="utf-8")
        combined = decisions + architecture + control
        folded = combined.casefold()

        for required in (
            "ADR-032",
            "candidate_done",
            "Finish Gate",
            "WorkingState",
            "LoopGuard",
            "ExpectedEffect",
            "OUTCOME_UNKNOWN",
        ):
            self.assertIn(required, combined)

        self.assertIn("state-first hybrid", folded)
        self.assertIn("capability-aware", folded)
        self.assertIn("pass | fail | unknown", folded)
        self.assertIn("no-effect", folded)
        self.assertIn("oscillation", folded)
        self.assertIn("reconcile", folded)

    def test_environmental_content_is_untrusted_and_safety_is_separate(self) -> None:
        decisions = (CONTEXT / "DECISIONS.md").read_text(encoding="utf-8")
        security = (CONTEXT / "SECURITY_POLICY.md").read_text(encoding="utf-8")
        architecture = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")

        self.assertIn("ADR-033", decisions)
        self.assertIn("Environmental content is data, not authority", decisions)
        self.assertIn("untrusted environmental", (security + architecture).casefold())
        self.assertIn("task-success", (security + architecture).casefold())
        self.assertIn("safety", security.casefold())
        self.assertIn("third-party", security.casefold())

    def test_roadmap_owns_current_implementation_order(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        current = (CONTEXT / "CURRENT_STATE.md").read_text(encoding="utf-8")
        combined = roadmap + current

        for required in (
            "26.3B",
            "Verification Kernel",
            "Finish Gate",
            "26.3C",
            "WorkingState",
            "LoopGuard",
            "26.4",
            "26.5",
            "Hybrid Computer-Use Integration",
        ):
            self.assertIn(required, combined)

        self.assertIn("release order", roadmap.casefold())
        self.assertIn("CURRENT_STATE.md", roadmap)

    def test_research_does_not_expand_public_surface_or_authority_by_itself(self) -> None:
        architecture = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")
        decisions = (CONTEXT / "DECISIONS.md").read_text(encoding="utf-8")
        module_catalog = (CONTEXT / "MODULE_CATALOG.md").read_text(encoding="utf-8")
        combined = architecture + decisions + module_catalog
        folded = combined.casefold()

        for tool_name in (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
            "procedure_run",
        ):
            self.assertIn(tool_name, combined)

        self.assertIn("six is the current accepted contract", folded)
        self.assertIn("does not authorize", folded)
        self.assertIn("code/program-state", folded)
        self.assertIn("generic `tool_invoke`", combined)
        self.assertIn("separate contract/security/physical acceptance", folded)


if __name__ == "__main__":
    unittest.main()
