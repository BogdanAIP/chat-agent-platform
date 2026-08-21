from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"


class DocumentationConsistencyTests(unittest.TestCase):
    def test_every_project_context_markdown_file_is_classified(self) -> None:
        status = (CONTEXT / "DOCUMENT_STATUS.md").read_text(encoding="utf-8")
        names = sorted(path.name for path in CONTEXT.glob("*.md"))
        self.assertGreater(len(names), 20)
        missing = [name for name in names if f"`{name}`" not in status]
        self.assertEqual(missing, [], f"unclassified project-context docs: {missing}")

    def test_authoritative_docs_use_current_planner_control_plane_boundary(self) -> None:
        files = [
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            CONTEXT / "CONTINUATION_CONTEXT.md",
            CONTEXT / "START_HERE.md",
            CONTEXT / "CURRENT_STATE.md",
            CONTEXT / "ARCHITECTURE.md",
            CONTEXT / "CONTROL_PLANE.md",
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

    def test_current_stage_order_is_consistent(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        current = (CONTEXT / "CURRENT_STATE.md").read_text(encoding="utf-8")
        continuation = (CONTEXT / "CONTINUATION_CONTEXT.md").read_text(encoding="utf-8")
        for text in (roadmap, current, continuation):
            self.assertIn("26.2E", text)
            self.assertIn("26.3", text)
            self.assertIn("26.4", text)
            self.assertLess(text.index("26.2E"), text.index("26.3"))
            self.assertLess(text.index("26.3"), text.index("26.4"))

    def test_future_local_planner_is_explicitly_non_release_critical(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        control = (CONTEXT / "CONTROL_PLANE.md").read_text(encoding="utf-8")
        self.assertIn("Optional Future Track P", roadmap)
        self.assertIn("not part of the current release-critical path", control)
        self.assertIn("P0 shadow planner", roadmap)
        self.assertIn("proposal only", roadmap)
        self.assertIn("deterministic Control Plane", roadmap)

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
