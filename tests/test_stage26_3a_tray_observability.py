from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
SOURCE = TRAY.read_text(encoding="utf-8")


class Stage263ATrayObservabilityTests(unittest.TestCase):
    def test_tray_reads_cached_state_projections_only(self):
        for expected in (
            '"supervisor.json"',
            '"manual-status.json"',
            '"operation-mode.json"',
            '"desired-state.json"',
            '"settings.json"',
            "Read-JsonFile -Path $SupervisorStateFile",
            "Read-JsonFile -Path $ManualStatusFile",
        ):
            self.assertIn(expected, SOURCE)
        self.assertNotIn("Invoke-ControllerStatus", SOURCE)
        self.assertNotIn("-Action Status", SOURCE)

    def test_idle_refresh_is_event_driven_not_periodic(self):
        self.assertIn("System.IO.FileSystemWatcher", SOURCE)
        self.assertIn("$watcher.SynchronizingObject = $uiHost", SOURCE)
        self.assertIn("$watcher.EnableRaisingEvents = $true", SOURCE)
        self.assertIn("Refresh-VisualState", SOURCE)
        self.assertNotIn("$timer.Interval = 2000", SOURCE)
        self.assertNotIn("$timer.Start()", SOURCE)

    def test_operation_timer_runs_only_for_explicit_user_lifecycle_action(self):
        self.assertIn("$operationTimer.Interval = 250", SOURCE)
        self.assertIn("$OperationTimeoutSeconds = 120", SOURCE)
        start = SOURCE.index("function Start-ControllerOperation")
        end = SOURCE.index("function Toggle-Platform", start)
        block = SOURCE[start:end]
        self.assertIn("$operationTimer.Start()", block)
        self.assertIn("System.Diagnostics.ProcessStartInfo", block)
        self.assertIn("-File", block)
        self.assertIn("$CommandPath", block)
        self.assertIn('"-Action", $Action', block)
        self.assertNotIn("Start-Job", block)
        self.assertIn("$operationTimer.Stop()", SOURCE)
        self.assertIn("$script:OperationProcess.Kill($true)", SOURCE)

    def test_stale_manual_completion_cannot_override_newer_desired_state(self):
        start = SOURCE.index("function Save-ManualStatusForAction")
        end = SOURCE.index("function Save-ManualStatusFromAutomaticSnapshot", start)
        block = SOURCE[start:end]
        self.assertIn("Read-JsonFile -Path $DesiredStateFile", block)
        self.assertIn("$expectedDesiredState", block)
        self.assertIn("$currentDesiredState -ne $expectedDesiredState", block)
        self.assertIn("return", block)

    def test_automatic_snapshot_freshness_matches_thirty_minute_cadence(self):
        self.assertIn("$AutomaticSnapshotFreshnessSeconds = 2100", SOURCE)
        self.assertIn("Get-SnapshotAgeSeconds", SOURCE)
        self.assertIn('"observed_at"', SOURCE)
        self.assertIn('"SUPERVISOR_STATE_STALE"', SOURCE)
        self.assertIn("$age -gt $AutomaticSnapshotFreshnessSeconds", SOURCE)

    def test_snapshot_age_handles_convertfrom_json_datetime_without_culture_round_trip(self):
        start = SOURCE.index("function Get-SnapshotAgeSeconds")
        end = SOURCE.index("function Get-SettingsProjection", start)
        block = SOURCE[start:end]
        self.assertIn("$observedAt -is [datetimeoffset]", block)
        self.assertIn("$observedAt -is [datetime]", block)
        self.assertIn("[DateTimeKind]::Unspecified", block)
        self.assertIn("[DateTimeKind]::Utc", block)
        self.assertIn("[Globalization.CultureInfo]::InvariantCulture", block)
        self.assertIn("[Globalization.DateTimeStyles]::RoundtripKind", block)
        self.assertNotIn("Parse([string]$observedAt)", block)

    def test_manual_and_automatic_modes_are_explicit_user_controls(self):
        for expected in (
            'ValidateSet("manual", "automatic")',
            '$manualModeItem.Text = "Ручной"',
            '$automaticModeItem.Text = "Автоматический — проверка раз в 30 мин"',
            '$modeMenu.DropDownItems.Add($manualModeItem)',
            '$modeMenu.DropDownItems.Add($automaticModeItem)',
            'Set-PlatformOperationMode -Mode "manual"',
            'Set-PlatformOperationMode -Mode "automatic"',
            'Stop-ScheduledTask -TaskName $SupervisorTaskName',
            'Start-ScheduledTask -TaskName $SupervisorTaskName',
        ):
            self.assertIn(expected, SOURCE)

    def test_manual_mode_has_no_snapshot_freshness_poll(self):
        visual = SOURCE[
            SOURCE.index("function Get-PlatformVisualState") :
            SOURCE.index("$script:RedIcon", SOURCE.index("function Get-PlatformVisualState"))
        ]
        self.assertIn('$operationMode -eq "manual"', visual)
        self.assertIn("Read-JsonFile -Path $ManualStatusFile", visual)
        self.assertIn('$operationMode -eq "automatic"', visual)
        self.assertIn("Get-SnapshotAgeSeconds -Snapshot $snapshot", visual)

    def test_tray_does_not_reconstruct_process_ownership(self):
        self.assertNotIn("Win32_Process", SOURCE)
        self.assertNotIn("Get-CimInstance", SOURCE)
        self.assertNotIn("Get-Process", SOURCE)
        self.assertNotIn("server.pid", SOURCE)

    def test_semantic_ready_is_always_six_tools(self):
        self.assertIn('$profile -in @("semantic", "semantic-direct")', SOURCE)
        self.assertIn('{ 6 } else { $null }', SOURCE)
        self.assertIn('READY · MCP · Tunnel · $($State.expected_tool_count) tools', SOURCE)
        self.assertNotIn("{ 5 }", SOURCE)
        self.assertNotIn("TOOL_COUNT=5", SOURCE)

    def test_simplified_menu_has_one_power_action_and_hides_diagnostics(self):
        self.assertIn('$powerItem = New-Object System.Windows.Forms.ToolStripMenuItem', SOURCE)
        self.assertIn('$menu.Items.Add($powerItem)', SOURCE)
        self.assertIn('$powerItem.Text = "Включить"', SOURCE)
        self.assertIn('$powerItem.Text = "Выключить"', SOURCE)
        self.assertIn('$moreMenu.Text = "Дополнительно"', SOURCE)
        self.assertIn('$moreMenu.DropDownItems.Add($detailsItem)', SOURCE)
        self.assertIn('$moreMenu.DropDownItems.Add($workspaceItem)', SOURCE)
        self.assertIn('$moreMenu.DropDownItems.Add($logItem)', SOURCE)
        self.assertNotIn('$toggleItem = New-Object System.Windows.Forms.ToolStripMenuItem', SOURCE)
        self.assertNotIn('$startItem = New-Object System.Windows.Forms.ToolStripMenuItem', SOURCE)
        self.assertNotIn('$stopItem = New-Object System.Windows.Forms.ToolStripMenuItem', SOURCE)

    def test_there_is_no_blue_or_qualification_mode(self):
        self.assertNotIn("DodgerBlue", SOURCE)
        self.assertNotIn('"qualification" {', SOURCE)
        self.assertNotIn("owner=qualification", SOURCE)
        self.assertNotIn("Qualification", SOURCE)

    def test_user_actions_keep_execution_authority_in_manager(self):
        self.assertIn("Start-ControllerOperation", SOURCE)
        self.assertIn("-File", SOURCE)
        self.assertIn("$CommandPath", SOURCE)
        self.assertIn('"-Action", $Action', SOURCE)
        self.assertIn('[ValidateSet("Start", "Stop")]', SOURCE)

    def test_observability_does_not_gain_execution_authority(self):
        self.assertNotIn("repo_root", SOURCE)
        self.assertNotIn("Invoke-Expression", SOURCE)
        self.assertNotIn("tunnels create", SOURCE)
        self.assertNotIn("tunnels update", SOURCE)
        self.assertNotIn("tunnels delete", SOURCE)


if __name__ == "__main__":
    unittest.main()
