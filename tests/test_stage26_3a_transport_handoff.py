from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "scripts" / "stage26-3a-procedure-supervised-handoff.ps1"
DIRECT = ROOT / "scripts" / "stage26-3a-procedure-direct-tunnel.ps1"


class Stage263ATransportHandoffTests(unittest.TestCase):
    def test_supervised_handoff_uses_installed_public_manager_and_persistent_desired_state(self) -> None:
        source = HANDOFF.read_text(encoding="utf-8")
        self.assertIn("app\\scripts\\chat-platform.ps1", source)
        self.assertIn("desired-state.json", source)
        self.assertIn("previous_desired_state", source)
        self.assertIn("ValidateSet('running', 'stopped')", source)
        self.assertIn("Invoke-InstalledManagerAction -ManagerAction Stop", source)
        self.assertIn("Invoke-InstalledManagerAction -ManagerAction Start", source)
        self.assertIn("-NoNotify", source)

    def test_handoff_persists_restore_intent_before_stopping_accepted_platform(self) -> None:
        source = HANDOFF.read_text(encoding="utf-8")
        start = source[source.index("function Start-SupervisedQualification") : source.index("function Stop-SupervisedQualification")]
        receipt_pos = start.index("Save-HandoffState")
        manager_stop_pos = start.index("Invoke-InstalledManagerAction -ManagerAction Stop")
        direct_start_pos = start.index("-DirectAction Start")
        self.assertLess(receipt_pos, manager_stop_pos)
        self.assertLess(manager_stop_pos, direct_start_pos)
        self.assertIn("Restore-AcceptedPlatform -PreviousDesiredState $previousDesiredState", start)

    def test_stop_kills_qualification_route_before_restoring_platform(self) -> None:
        source = HANDOFF.read_text(encoding="utf-8")
        stop = source[source.index("function Stop-SupervisedQualification") : source.index("function Get-SupervisedQualificationStatus")]
        self.assertLess(stop.index("Invoke-DirectHarness -DirectAction Stop"), stop.index("Restore-AcceptedPlatform"))
        self.assertIn("stopped-no-restore-receipt", stop)

    def test_handoff_does_not_gain_tunnel_admin_or_generic_execution_authority(self) -> None:
        source = HANDOFF.read_text(encoding="utf-8")
        for forbidden in (
            "OPENAI_ADMIN_KEY",
            "OPENAI_API_KEY",
            "CONTROL_PLANE_API_KEY",
            "tunnels create",
            "tunnels update",
            "tunnels delete",
            "Invoke-Expression",
            "Start-Process cmd",
            "powershell.exe",
        ):
            self.assertNotIn(forbidden, source)

    def test_direct_tunnel_remains_the_only_qualification_route_implementation(self) -> None:
        source = HANDOFF.read_text(encoding="utf-8")
        direct = DIRECT.read_text(encoding="utf-8")
        self.assertIn("stage26-3a-procedure-direct-tunnel.ps1", source)
        self.assertIn("--control-plane.tunnel-id", direct)
        self.assertNotIn("--control-plane.tunnel-id", source)
        self.assertNotIn("tunnel-client.exe", source)


if __name__ == "__main__":
    unittest.main()
