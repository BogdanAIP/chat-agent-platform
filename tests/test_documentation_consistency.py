from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"


class DocumentationConsistencyTests(unittest.TestCase):
    def test_authoritative_project_context_documents_are_classified_and_default_is_explicit(self) -> None:
        status = (CONTEXT / "DOCUMENT_STATUS.md").read_text(encoding="utf-8")
        required = (
            "CONTINUATION_CONTEXT.md",
            "START_HERE.md",
            "CURRENT_STATE.md",
            "PROJECT_RISKS.md",
            "ARCHITECTURE.md",
            "CONTROL_PLANE.md",
            "COMPUTER_USE_ARCHITECTURE.md",
            "SECURITY_POLICY.md",
            "ROADMAP.md",
            "DOCUMENT_STATUS.md",
            "EVIDENCE_INDEX.md",
            "STAGE26_3B_VERIFICATION_KERNEL.md",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertIn(f"`{name}`", status)

        # Do not force DOCUMENT_STATUS to enumerate every historical/research
        # markdown file forever. Unlisted project-context documents are
        # deliberately non-authoritative until explicitly promoted.
        self.assertIn("not explicitly listed", status)
        self.assertIn("HISTORICAL / REFERENCE by default", status)

    def test_authoritative_docs_use_current_planner_control_plane_boundary(self) -> None:
        files = [
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            CONTEXT / "CONTINUATION_CONTEXT.md",
            CONTEXT / "START_HERE.md",
            CONTEXT / "CURRENT_STATE.md",
            CONTEXT / "PROJECT_RISKS.md",
            CONTEXT / "ARCHITECTURE.md",
            CONTEXT / "CONTROL_PLANE.md",
            CONTEXT / "COMPUTER_USE_ARCHITECTURE.md",
            CONTEXT / "ROADMAP.md",
            CONTEXT / "CONSTRAINTS.md",
            CONTEXT / "DECISIONS.md",
            CONTEXT / "DEVELOPMENT_PRINCIPLES.md",
            CONTEXT / "SECURITY_POLICY.md",
            CONTEXT / "MODULE_CATALOG.md",
            CONTEXT / "MODULE_SELECTION_POLICY.md",
            CONTEXT / "VISION.md",
        ]
        for path in files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Control Plane", text)

        control_plane = (CONTEXT / "CONTROL_PLANE.md").read_text(encoding="utf-8")
        self.assertIn("only current general planner", control_plane)
        self.assertIn("deterministic", control_plane.casefold())
        self.assertIn("Track P", control_plane)
        self.assertIn("shadow planner", control_plane)
        self.assertIn("ABSTAIN", control_plane)

    def test_obsolete_architecture_phrases_do_not_return_to_live_docs(self) -> None:
        live_files = [
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            CONTEXT / "CONTINUATION_CONTEXT.md",
            CONTEXT / "START_HERE.md",
            CONTEXT / "CURRENT_STATE.md",
            CONTEXT / "ARCHITECTURE.md",
            CONTEXT / "CONTROL_PLANE.md",
            CONTEXT / "COMPUTER_USE_ARCHITECTURE.md",
            CONTEXT / "ROADMAP.md",
            CONTEXT / "CONSTRAINTS.md",
            CONTEXT / "DEVELOPMENT_PRINCIPLES.md",
            CONTEXT / "KNOWN_ISSUES.md",
            CONTEXT / "STAGE26_PROCEDURAL_MEMORY.md",
        ]
        forbidden = [
            "no second local planner/Agent Control Plane",
            "Do not insert a local generic Agent Control Plane/Planner",
            "Stage 26.3 must separately establish",
            "Stage 26.3 desktop surface",
            "Codex/automation should perform",
            "fresh ChatGPT/Codex session",
        ]
        for path in live_files:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_release_order_has_one_authoritative_owner(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        current = (CONTEXT / "CURRENT_STATE.md").read_text(encoding="utf-8")
        continuation = (CONTEXT / "CONTINUATION_CONTEXT.md").read_text(encoding="utf-8")

        # ROADMAP owns the explicit release order. Current-state/continuation
        # docs should point to it rather than duplicating a brittle stage list.
        ordered_sequence = re.compile(
            r"26\.3B[\s\S]{0,3000}?26\.3C[\s\S]{0,3000}?26\.4[\s\S]{0,3000}?26\.5",
            re.IGNORECASE,
        )
        self.assertRegex(roadmap, ordered_sequence)
        self.assertIn("ROADMAP.md", current)
        self.assertIn("ROADMAP.md", continuation)

    def test_future_local_planner_is_explicitly_non_release_critical(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        control = (CONTEXT / "CONTROL_PLANE.md").read_text(encoding="utf-8")
        self.assertIn("Optional Track P", roadmap)
        self.assertIn("future only", roadmap.casefold())
        self.assertIn("shadow/proposal-only", roadmap)
        self.assertIn("deterministic Control Plane", roadmap)
        self.assertIn("not part of the current release-critical path", control)

    def test_computer_use_architecture_preserves_small_surface_and_independent_completion(self) -> None:
        computer_use = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("current six-tool public surface remains accepted", computer_use)
        self.assertIn("state first", computer_use.casefold())
        self.assertIn("Finish Gate", computer_use)
        self.assertIn("LoopGuard", computer_use)
        self.assertIn("environmental data", computer_use.casefold())
        self.assertIn("Control Plane", computer_use)

    def test_stage26_2e_document_matches_current_guard_contract(self) -> None:
        stage = (CONTEXT / "STAGE26_2E_REAL_APPLICATION_E2E.md").read_text(encoding="utf-8")
        required = [
            "FRESH_PRE_ACTION_STATE_PASS=True",
            "CLI_PROCESS_RETURNCODE=0",
            "CLI_PROCESS_EXIT_PASS=True",
            "FORCED_CLI_CLEANUP=False",
            "same focused-editor observation fingerprint",
            "failure cleanup",
        ]
        for item in required:
            self.assertIn(item, stage)


if __name__ == "__main__":
    unittest.main()
