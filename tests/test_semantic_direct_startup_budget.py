from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts" / "semantic-direct-controller.ps1").read_text(encoding="utf-8")


class SemanticDirectStartupBudgetTests(unittest.TestCase):
    def test_startup_uses_real_wall_clock_budget(self):
        self.assertIn("$StartupReadyTimeoutMilliseconds = 45000", SOURCE)
        self.assertIn("[System.Diagnostics.Stopwatch]::StartNew()", SOURCE)
        self.assertIn("$startupClock.ElapsedMilliseconds -lt $StartupReadyTimeoutMilliseconds", SOURCE)
        self.assertNotIn("for ($i = 0; $i -lt 180; $i++)", SOURCE)

    def test_startup_wait_does_not_repeat_full_status_pipeline(self):
        start = SOURCE.index("function Start-DirectRuntime")
        end = SOURCE.index("Initialize-Directories\n\ntry", start)
        block = SOURCE[start:end]
        wait_start = block.index("$startupClock = [System.Diagnostics.Stopwatch]::StartNew()")
        wait_block = block[wait_start:]
        self.assertIn("Get-LocalHealthProbe", wait_block)
        self.assertIn("$startupProcessProjection", wait_block)
        self.assertIn("Get-SemanticProcesses", wait_block)
        self.assertNotIn("$lastStatus = Get-DirectStatusObject", wait_block)
        self.assertNotIn("$local = Get-DirectStatusObject", wait_block)

    def test_local_health_probe_accepts_bounded_startup_timeout(self):
        start = SOURCE.index("function Get-LocalHealthProbe")
        end = SOURCE.index("function ConvertTo-RemoteTunnelStatus", start)
        block = SOURCE[start:end]
        self.assertIn("[int]$TimeoutMilliseconds = $LocalHealthTimeoutMilliseconds", block)
        self.assertIn("-TimeoutMilliseconds $TimeoutMilliseconds", block)

    def test_transient_control_plane_poll_failure_does_not_block_local_startup(self):
        start = SOURCE.index("function Start-DirectRuntime")
        end = SOURCE.index("Initialize-Directories\n\ntry", start)
        block = SOURCE[start:end]
        wait_start = block.index("$startupClock = [System.Diagnostics.Stopwatch]::StartNew()")
        wait_block = block[wait_start:]

        local_ready_start = wait_block.index("if (\n            [bool]$local.healthz_ok")
        local_ready_end = wait_block.index(") {", local_ready_start)
        local_ready_condition = wait_block[local_ready_start:local_ready_end]

        self.assertIn("[bool]$local.healthz_ok", local_ready_condition)
        self.assertIn("[bool]$local.readyz_ok", local_ready_condition)
        self.assertIn("[bool]$local.process_ok", local_ready_condition)
        self.assertNotIn("[bool]$local.poll_ok", local_ready_condition)
        self.assertIn("$lastHealthCode = if ([bool]$local.poll_ok)", wait_block)
        self.assertIn("'REMOTE_TUNNEL_DISCONNECTED'", wait_block)


if __name__ == "__main__":
    unittest.main()
