from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts" / "chat-platform.ps1"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"


class ManagerSingleInstanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = COMMAND.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    def test_owner_state_is_shared_in_local_appdata(self):
        self.assertIn(
            'Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"',
            self.command,
        )
        self.assertIn('"manager-owner.json"', self.command)
        self.assertIn('schema_version = 1', self.command)
        self.assertIn('controller_path =', self.command)
        self.assertIn('repo_root =', self.command)

    def test_status_delegates_to_the_recorded_owner(self):
        self.assertIn('function Get-EffectiveOwnerControllerPath', self.command)
        self.assertIn('function Invoke-ControllerStatusAt', self.command)
        self.assertIn('if ($Action -eq "Status")', self.command)
        self.assertIn(
            'Invoke-ControllerStatusAt -TargetControllerPath $ownerController',
            self.command,
        )

    def test_start_stops_a_foreign_owner_before_switching_copies(self):
        self.assertIn('function Stop-ForeignManagerIfNeeded', self.command)
        self.assertIn('$null = Stop-ForeignManagerIfNeeded', self.command)
        self.assertIn('-TargetAction "Stop"', self.command)
        self.assertIn('Wait-McpPortFree -TimeoutSeconds 15', self.command)

    def test_unowned_port_is_fail_closed(self):
        self.assertIn('function Assert-McpPortFree', self.command)
        self.assertIn('Get-NetTCPConnection', self.command)
        self.assertIn('Refusing to accept another process', self.command)
        self.assertIn('health endpoint', self.command)

    def test_toggle_of_foreign_owner_stops_instead_of_double_start(self):
        self.assertIn('elseif ($Action -eq "Toggle" -and $foreignOwner)', self.command)
        self.assertIn(
            'Toggle therefore means stop that one, not start a second copy.',
            self.command,
        )

    def test_set_profile_uses_authoritative_owner_runtime(self):
        self.assertIn('elseif ($Action -eq "SetProfile" -and $foreignOwner)', self.command)
        self.assertIn(
            'Let the actual owner enforce its active-profile rule',
            self.command,
        )

    def test_bootstrap_propagates_public_manager_into_installed_bundle(self):
        self.assertIn('"chat-platform.ps1"', self.bootstrap)
        self.assertIn('Copy-VerifiedManagerFile', self.bootstrap)
        self.assertIn('Join-Path $LocalRoot "app"', self.bootstrap)


if __name__ == "__main__":
    unittest.main()
