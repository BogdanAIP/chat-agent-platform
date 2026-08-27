from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-windows-case-l3.ps1"


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


if __name__ == "__main__":
    unittest.main()
