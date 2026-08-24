from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
SOURCE = TRAY.read_text(encoding="utf-8")


class Stage263ATrayObservabilityTests(unittest.TestCase):
    def test_tray_uses_only_authoritative_manager_status(self):
        self.assertIn("Invoke-ControllerStatus", SOURCE)
        self.assertIn('"chat-platform.ps1"', SOURCE)
        self.assertIn("-Action Status", SOURCE)
        self.assertNotIn("stage26-3a-procedure-supervised-handoff.json", SOURCE)
        self.assertNotIn("stage26-3a-procedure-direct.json", SOURCE)
        self.assertNotIn("stage26-3a-procedure-direct-health.url", SOURCE)
        self.assertNotIn("procedure-qualification", SOURCE)

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

    def test_observability_does_not_gain_execution_authority(self):
        self.assertNotIn("repo_root", SOURCE)
        self.assertNotIn("Invoke-Expression", SOURCE)
        self.assertNotIn("tunnels create", SOURCE)
        self.assertNotIn("tunnels update", SOURCE)
        self.assertNotIn("tunnels delete", SOURCE)


if __name__ == "__main__":
    unittest.main()
