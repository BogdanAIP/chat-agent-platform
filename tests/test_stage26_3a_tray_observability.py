from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
SOURCE = TRAY.read_text(encoding="utf-8")


class Stage263ATrayObservabilityTests(unittest.TestCase):
    def test_tray_recognizes_known_stage26_3a_state_files(self):
        self.assertIn("stage26-3a-procedure-supervised-handoff.json", SOURCE)
        self.assertIn("stage26-3a-procedure-direct.json", SOURCE)
        self.assertIn("stage26-3a-procedure-direct-health.url", SOURCE)
        self.assertIn("desired-state.json", SOURCE)

    def test_qualification_ready_requires_serialized_handoff_suspend_receipt_and_health(self):
        self.assertIn('[string]$handoff.phase -eq "running"', SOURCE)
        self.assertIn('[string]$desired.desired_state -eq "stopped"', SOURCE)
        self.assertIn("$directReceiptPresent", SOURCE)
        self.assertIn("$ready = Test-QualificationReady", SOURCE)
        self.assertIn(
            "$fullyReady = ($handoffRunning -and $normalSuspended -and $directReceiptPresent -and $ready)",
            SOURCE,
        )

    def test_tray_does_not_reconstruct_process_ownership(self):
        self.assertNotIn("Win32_Process", SOURCE)
        self.assertNotIn("Get-CimInstance", SOURCE)
        self.assertNotIn("Get-Process", SOURCE)
        self.assertNotIn("server.pid", SOURCE)

    def test_health_probe_is_loopback_only(self):
        self.assertIn("'^https?://127\\.0\\.0\\.1(?::\\d+)?$'", SOURCE)
        self.assertIn('-Uri "$base/readyz"', SOURCE)
        self.assertIn("-TimeoutSec 2", SOURCE)

    def test_blue_state_is_explicitly_six_tool_qualification(self):
        self.assertIn("System.Drawing.Color]::DodgerBlue", SOURCE)
        self.assertIn('mode = if ($fullyReady) { "qualification" } else { "partial" }', SOURCE)
        self.assertIn('expected_tool_count = 6', SOURCE)
        self.assertIn('route_owner = "qualification"', SOURCE)
        self.assertIn('"🔵 Qualification - 6 tools READY"', SOURCE)
        self.assertIn('"MCP READY | Tunnel READY | owner=qualification"', SOURCE)

    def test_normal_controls_are_locked_while_qualification_owns_route(self):
        qualification_start = SOURCE.index('"qualification" {')
        qualification_end = SOURCE.index('"on" {', qualification_start)
        block = SOURCE[qualification_start:qualification_end]
        self.assertIn("$toggleItem.Enabled = $false", block)
        self.assertIn("$startItem.Enabled = $false", block)
        self.assertIn("$stopItem.Enabled = $false", block)
        self.assertGreaterEqual(SOURCE.count('$state.route_owner -eq "qualification"'), 2)

    def test_observability_does_not_execute_paths_from_state(self):
        self.assertNotIn("repo_root", SOURCE)
        self.assertNotIn("Invoke-Expression", SOURCE)
        self.assertNotIn("stage26-3a-procedure-supervised-handoff.ps1", SOURCE)


if __name__ == "__main__":
    unittest.main()
