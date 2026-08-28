from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
DOC_STATUS = ROOT / "project-context" / "DOCUMENT_STATUS.md"
EVIDENCE = ROOT / "project-context" / "EVIDENCE_INDEX.md"


class CiMaintenanceContractTests(unittest.TestCase):
    def test_ci_discovers_all_powershell_scripts_instead_of_stage_allowlist(self) -> None:
        text = CI.read_text(encoding="utf-8")
        self.assertIn("Get-ChildItem -LiteralPath 'scripts' -Filter '*.ps1' -File -Recurse", text)
        self.assertIn("POWERSHELL_PARSE_COUNT", text)
        self.assertNotIn("scripts/stage26-vscode-real-app-e2e.ps1',", text)

    def test_document_status_separates_durable_architecture_from_evidence(self) -> None:
        text = DOC_STATUS.read_text(encoding="utf-8")
        folded = text.casefold()
        self.assertIn("architecture.md / control_plane.md / computer_use_architecture.md", folded)
        self.assertIn("durable product/execution boundaries", folded)
        self.assertIn("evidence_index.md", folded)
        self.assertIn("exact accepted physical/target evidence navigation", folded)
        self.assertIn("current_state.md", folded)
        self.assertIn("roadmap.md", folded)

    def test_evidence_index_keeps_physical_and_nonphysical_acceptance_separate(self) -> None:
        text = EVIDENCE.read_text(encoding="utf-8")
        physical, remainder = text.split("## Accepted non-physical foundations", maxsplit=1)
        nonphysical, not_accepted = remainder.split("## Not yet physically/production accepted", maxsplit=1)

        self.assertIn("Transport console-free Scheduled Task launch", physical)
        self.assertIn("Transport persistent desired-state/runtime-owner split", physical)
        self.assertIn("Stage 26.3A six-tool ordinary-Chat Verified Procedure Runtime", physical)
        self.assertIn("Stage 26.3B Browser stronger source-provenance repeat", physical)

        self.assertIn("PR #124", nonphysical)
        self.assertIn("WorkingState", nonphysical)
        self.assertIn("LoopGuard", nonphysical)
        self.assertNotIn("PR #124", physical)

        self.assertIn("Stage 26.3C **production** WorkingState/restart-reconciliation integration", not_accepted)
        self.assertIn("Track M Agent Session/Delegation runtime", not_accepted)
        self.assertIn("release-grade distribution/maintenance", not_accepted)
        self.assertNotIn("Stage 26.3B advanced verifier/postcondition library", not_accepted)


if __name__ == "__main__":
    unittest.main()
