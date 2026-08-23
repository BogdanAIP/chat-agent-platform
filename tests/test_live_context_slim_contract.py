from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "project-context" / "CURRENT_STATE.md"
ARCH = ROOT / "project-context" / "ARCHITECTURE.md"


class LiveContextSlimContractTests(unittest.TestCase):
    def test_live_context_points_exact_evidence_to_evidence_index(self) -> None:
        current = CURRENT.read_text(encoding="utf-8")
        architecture = ARCH.read_text(encoding="utf-8")
        self.assertIn("EVIDENCE_INDEX.md", current)
        self.assertIn("EVIDENCE_INDEX.md", architecture)

    def test_durable_architecture_does_not_embed_acceptance_shas_or_local_result_paths(self) -> None:
        architecture = ARCH.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\b[0-9a-f]{40}\b", architecture))
        self.assertNotIn("C:\\Users\\", architecture)
        self.assertNotIn("PROJECT_HEAD=", architecture)
        self.assertNotIn("QUALIFICATION_EXIT_CODE=", architecture)

    def test_current_state_avoids_raw_physical_result_dumps(self) -> None:
        current = CURRENT.read_text(encoding="utf-8")
        self.assertNotIn("C:\\Users\\", current)
        self.assertNotIn("PROJECT_HEAD=", current)
        self.assertNotIn("WINDOW_BINDING_PASS=", current)
        self.assertNotIn("QUALIFICATION_EXIT_CODE=", current)

    def test_core_live_invariants_remain_explicit(self) -> None:
        combined = (
            CURRENT.read_text(encoding="utf-8")
            + "\n"
            + ARCH.read_text(encoding="utf-8")
        ).casefold()
        for required in (
            "ordinary chatgpt is the only **current general planner/intelligence**",
            "deterministic execution control plane",
            "abstain",
            "action delivery is not task completion",
            "transport supervisor",
            "procedure_run",
        ):
            self.assertIn(required, combined)


if __name__ == "__main__":
    unittest.main()
