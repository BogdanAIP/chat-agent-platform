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
        self.assertIn("EVIDENCE_INDEX.md", text)
        self.assertIn("durable boundaries and invariants", text)
        self.assertIn("exact accepted heads", text)

    def test_evidence_index_keeps_unaccepted_tracks_out_of_accepted_table(self) -> None:
        text = EVIDENCE.read_text(encoding="utf-8")
        accepted, not_accepted = text.split("## Not yet accepted", maxsplit=1)
        self.assertNotIn("Transport Supervisor v1 (#94)", accepted)
        self.assertNotIn("Stage 26.3 Verified Procedure Runtime", accepted)
        self.assertIn("Transport Supervisor v1 (#94)", not_accepted)
        self.assertIn("Stage 26.3 Verified Procedure Runtime", not_accepted)


if __name__ == "__main__":
    unittest.main()
