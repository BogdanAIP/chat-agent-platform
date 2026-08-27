from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-windows-case-l3.ps1"
PREPARE = ROOT / "scripts" / "prepare-windows-case-l3.ps1"
RECHECK = ROOT / "scripts" / "stage26-windows-l3-provenance-recheck.py"


class WindowsApplicationL3FinishGateTests(unittest.TestCase):
    def test_finish_gate_requires_live_case_desk_before_cleanup(self) -> None:
        source = CHECKER.read_text(encoding="utf-8")
        self.assertIn("fixture_process_was_live = $false", source)
        self.assertIn("$result.fixture_process_was_live = -not $fixtureProcess.HasExited", source)
        done_block = source[
            source.index("$done = [bool](") : source.index("$result.finish_gate =", source.index("$done = [bool]("))
        ]
        self.assertIn("$result.fixture_process_was_live", done_block)
        self.assertIn('Write-Host "FIXTURE_PROCESS_WAS_LIVE=$($result.fixture_process_was_live)"', source)

    def test_external_done_is_decided_before_fixture_cleanup(self) -> None:
        source = CHECKER.read_text(encoding="utf-8")
        finish_index = source.index("$result.finish_gate = if ($done) { 'done' } else { 'not_done' }")
        cleanup_index = source.index("Set-Content -LiteralPath ([string]$manifest.close_path)")
        self.assertLess(finish_index, cleanup_index)

    def test_finish_gate_revalidates_exact_source_installed_runtime_and_openadapt(self) -> None:
        source = CHECKER.read_text(encoding="utf-8")
        done_block = source[
            source.index("$done = [bool](") : source.index("$result.finish_gate =", source.index("$done = [bool]("))
        ]
        for required in (
            "frozen_finish_gate_code_pass",
            "source_provenance_revalidated",
            "installed_runtime_provenance_revalidated",
            "runtime_attestation_revalidated",
            "provenance_revalidation_pass",
            "frozen_provenance_recheck_path",
            "windows_python_path",
        ):
            self.assertIn(required, source)
        self.assertIn("$result.frozen_finish_gate_code_pass", done_block)
        self.assertIn("$result.provenance_revalidation_pass", done_block)

        recheck = RECHECK.read_text(encoding="utf-8")
        for required in (
            '"status", "--porcelain=v1", "--untracked-files=all"',
            'metadata.version("openadapt-flow")',
            "win_agent_server_sha256",
            "source_hashes_pass",
            "installed_hashes_pass",
            "runtime_server_hash_pass",
            "runtime_lock_hash_pass",
        ):
            self.assertIn(required, recheck)

    def test_prepare_freezes_finish_gate_outside_chat_workspace(self) -> None:
        source = PREPARE.read_text(encoding="utf-8")
        self.assertIn("$frozenGateRoot = Join-Path $qualificationRoot 'frozen-gate'", source)
        self.assertIn("Copy-Item -LiteralPath $checkerScript -Destination $frozenCheckerPath", source)
        self.assertIn("Copy-Item -LiteralPath $provenanceRecheckScript -Destination $frozenRecheckPath", source)
        self.assertIn("'scripts/stage26-windows-l3-provenance-recheck.py'", source)
        self.assertIn("frozen_checker_path = $frozenCheckerPath", source)
        self.assertIn("frozen_provenance_recheck_path = $frozenRecheckPath", source)
        self.assertIn("windows_python_path = $windowsPython", source)
        self.assertIn('Write-Host "CHECK_COMMAND=& \'$frozenCheckerPath\' -QualificationRoot \'$qualificationRoot\'"', source)


if __name__ == "__main__":
    unittest.main()
