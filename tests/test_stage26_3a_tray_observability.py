from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
SOURCE = TRAY.read_text(encoding="utf-8")


class Stage263ATrayObservabilityTests(unittest.TestCase):
    def test_tray_reads_authoritative_supervisor_projection(self):
        self.assertIn('"supervisor.json"', SOURCE)
        self.assertIn("$SupervisorStateFile", SOURCE)
        self.assertIn("Get-PlatformVisualState", SOURCE)
        self.assertIn("Read-JsonFile -Path $SupervisorStateFile", SOURCE)
        self.assertIn('"desired-state.json"', SOURCE)
        self.assertIn('"settings.json"', SOURCE)
        self.assertNotIn("Invoke-ControllerStatus", SOURCE)
        self.assertNotIn("-Action Status", SOURCE)

    def test_periodic_refresh_does_not_spawn_status_processes(self):
        timer_start = SOURCE.index("$timer = New-Object System.Windows.Forms.Timer")
        timer_block = SOURCE[timer_start:]
        self.assertIn("$timer.Interval = 2000", timer_block)
        self.assertIn("Refresh-VisualState", timer_block)
        self.assertNotIn("Get-Command", timer_block)
        self.assertNotIn("pwsh.exe", timer_block)
        self.assertNotIn("-Action Status", timer_block)

    def test_supervisor_snapshot_has_bounded_freshness(self):
        self.assertIn("$SupervisorSnapshotFreshnessSeconds = 45", SOURCE)
        self.assertIn("Get-SupervisorSnapshotAgeSeconds", SOURCE)
        self.assertIn('"observed_at"', SOURCE)
        self.assertIn('"SUPERVISOR_STATE_STALE"', SOURCE)
        self.assertIn("$age -gt $SupervisorSnapshotFreshnessSeconds", SOURCE)

    def test_snapshot_age_handles_convertfrom_json_datetime_without_culture_round_trip(self):
        start = SOURCE.index("function Get-SupervisorSnapshotAgeSeconds")
        end = SOURCE.index("function Get-PlatformVisualState", start)
        block = SOURCE[start:end]
        self.assertIn("$observedAt -is [datetimeoffset]", block)
        self.assertIn("$observedAt -is [datetime]", block)
        self.assertIn("[DateTimeKind]::Unspecified", block)
        self.assertIn("[DateTimeKind]::Utc", block)
        self.assertIn("[Globalization.CultureInfo]::InvariantCulture", block)
        self.assertIn("[Globalization.DateTimeStyles]::RoundtripKind", block)
        self.assertNotIn("Parse([string]$observedAt)", block)

    def test_tray_does_not_reconstruct_process_ownership(self):
        self.assertNotIn("Win32_Process", SOURCE)
        self.assertNotIn("Get-CimInstance", SOURCE)
        self.assertNotIn("Get-Process", SOURCE)
        self.assertNotIn("server.pid", SOURCE)

    def test_semantic_ready_is_always_six_tools(self):
        self.assertIn('$profile -in @("semantic", "semantic-direct")', SOURCE)
        self.assertIn('{ 6 } else { $null }', SOURCE)
        self.assertIn('"MCP READY | Tunnel READY | $($State.expected_tool_count) tools"', SOURCE)
        self.assertIn('"Индикатор запущен. Зелёный READY для semantic означает единый 6-tool runtime."', SOURCE)
        self.assertNotIn("{ 5 }", SOURCE)
        self.assertNotIn("TOOL_COUNT=5", SOURCE)

    def test_there_is_no_blue_or_qualification_mode(self):
        self.assertNotIn("DodgerBlue", SOURCE)
        self.assertNotIn('"qualification" {', SOURCE)
        self.assertNotIn("owner=qualification", SOURCE)
        self.assertNotIn("Qualification", SOURCE)

    def test_ready_state_keeps_normal_controls_available(self):
        ready_start = SOURCE.index('"on" {')
        ready_end = SOURCE.index('"off" {', ready_start)
        block = SOURCE[ready_start:ready_end]
        self.assertIn("$toggleItem.Enabled = $true", block)
        self.assertIn("$startItem.Enabled = $false", block)
        self.assertIn("$stopItem.Enabled = $true", block)

    def test_user_actions_keep_execution_authority_in_manager(self):
        self.assertIn("Start-ControllerOperation", SOURCE)
        self.assertIn("-File $CommandPath", SOURCE)
        self.assertIn("-Action $Action", SOURCE)
        self.assertIn('[ValidateSet("Start", "Stop")]', SOURCE)

    def test_observability_does_not_gain_execution_authority(self):
        self.assertNotIn("repo_root", SOURCE)
        self.assertNotIn("Invoke-Expression", SOURCE)
        self.assertNotIn("tunnels create", SOURCE)
        self.assertNotIn("tunnels update", SOURCE)
        self.assertNotIn("tunnels delete", SOURCE)


if __name__ == "__main__":
    unittest.main()
