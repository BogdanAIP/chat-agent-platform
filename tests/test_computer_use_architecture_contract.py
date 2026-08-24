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

        for required in (
            "ADR-032",
            "State-first hybrid computer-use control loop",
            "candidate_done",
            "Finish Gate",
            "WorkingState",
            "LoopGuard",
            "capability-aware",
        ):
            self.assertIn(required, decisions + architecture + control)

        self.assertIn("PASS | FAIL | UNKNOWN", architecture)
        self.assertIn("expected_effect", architecture)
        self.assertIn("action_no_effect", architecture)
        self.assertIn("oscillation", architecture.casefold())

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

    def test_roadmap_promotes_research_into_implementation_order(self) -> None:
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

    def test_research_does_not_expand_public_surface_or_authority_by_itself(self) -> None:
        architecture = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")
        decisions = (CONTEXT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("current six-tool public surface remains accepted", architecture)
        self.assertIn("does not authorize new public tool names", decisions)
        self.assertIn("unrestricted code/program-state access", architecture)
        self.assertIn("generic `tool_invoke`", architecture)


if __name__ == "__main__":
    unittest.main()
