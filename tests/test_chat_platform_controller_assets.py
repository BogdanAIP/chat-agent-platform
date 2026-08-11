from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

CONTROLLER = ROOT / "scripts" / "chat-platform-controller.ps1"
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
CI = ROOT / ".github" / "workflows" / "ci.yml"


class ChatPlatformControllerAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.tray = TRAY.read_text(encoding="utf-8")
        cls.ci = CI.read_text(encoding="utf-8")

    def test_controller_and_tray_exist(self):
        self.assertTrue(CONTROLLER.is_file())
        self.assertTrue(TRAY.is_file())

    def test_controller_uses_persistent_local_appdata_and_dpapi(self):
        self.assertIn(
            'Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"',
            self.controller,
        )
        self.assertIn('"control-plane-api-key.dpapi"', self.controller)
        self.assertIn(
            "[Security.Cryptography.ProtectedData]::Protect",
            self.controller,
        )
        self.assertIn(
            "[Security.Cryptography.DataProtectionScope]::CurrentUser",
            self.controller,
        )

    def test_secret_is_not_embedded_in_source(self):
        combined = self.controller + "\n" + self.tray
        self.assertIsNone(
            re.search(r"sk-[A-Za-z0-9_-]{20,}", combined)
        )

    def test_controller_uses_pwsh_tray_shortcut(self):
        self.assertIn('"pwsh.exe"', self.controller)
        self.assertIn(
            '"scripts\\chat-platform-tray.ps1"',
            self.controller,
        )
        self.assertIn("-WindowStyle Hidden", self.controller)

    def test_default_reference_profile_has_supported_start_path(self):
        self.assertIn('profile = "reference"', self.controller)
        self.assertIn("$StartLocalBridgeScript", self.controller)
        self.assertRegex(
            self.controller,
            re.compile(
                r'if \(\$desiredProfile -eq "reference"\).*?'
                r'& \$StartLocalBridgeScript',
                re.S,
            ),
        )

    def test_controller_uses_authoritative_profile_status_script(self):
        self.assertIn("$StatusChatScript", self.controller)
        self.assertRegex(
            self.controller,
            re.compile(
                r'function Get-ChatProfileStatus.*?'
                r'-File \$StatusChatScript',
                re.S,
            ),
        )

    def test_tray_resolves_reference_pid_from_runtime_root(self):
        self.assertIn('"runtime\\server.pid"', self.tray)
        self.assertIn(
            '"runtime\\chat-profiles\\$ProfileName\\server.pid"',
            self.tray,
        )
        self.assertNotIn(
            '"runtime\\chat-profiles\\$profile\\server.pid"',
            self.tray,
        )

    def test_tunnel_profile_is_persistent_after_migration(self):
        self.assertIn(
            '$profileSource = "local-existing"',
            self.controller,
        )
        self.assertIn(
            'if (-not (Test-Path $TunnelProfile))',
            self.controller,
        )
        self.assertIn(
            'TUNNEL_PROFILE_SOURCE=$profileSource',
            self.controller,
        )

    def test_running_binary_is_not_blindly_overwritten(self):
        self.assertIn("local-existing-identical", self.controller)
        self.assertIn("local-running-update-deferred", self.controller)
        self.assertIn("Test-TunnelRunning", self.controller)

    def test_tunnel_process_matching_is_bound_to_installed_binary(self):
        for source in (self.controller, self.tray):
            self.assertIn("ExecutablePath", source)
            self.assertIn("$actualExe -ieq $expectedExe", source)
            self.assertIn("--profile-dir", source)
            self.assertIn("local-1mcp", source)

    def test_tunnel_readiness_uses_official_readyz_probe(self):
        for source in (self.controller, self.tray):
            self.assertIn("tunnel-health.url", source)
            self.assertIn("/readyz", source)

        self.assertIn("--health.listen-addr 127.0.0.1:0", self.controller)
        self.assertIn("--health.url-file", self.controller)
        self.assertIn("Wait-TunnelReady", self.controller)
        self.assertIn("tunnel_ready", self.controller)

    def test_mcp_health_requires_ready_payload_not_only_http_200(self):
        self.assertIn("Invoke-RestMethod", self.tray)
        self.assertIn(
            '([string]$response.state -eq "ready")',
            self.tray,
        )

    def test_green_requires_mcp_ready_and_tunnel_ready(self):
        self.assertRegex(
            self.tray,
            re.compile(
                r'\$mcp\.healthy -and\s*\$tunnel\.ready',
                re.S,
            ),
        )

    def test_platform_start_rolls_back_on_partial_failure(self):
        match = re.search(
            r"function Start-Platform \{(.*?)\n\}\n\n\nfunction Stop-Platform",
            self.controller,
            re.S,
        )
        self.assertIsNotNone(match)
        body = match.group(1)
        self.assertIn("catch", body)
        self.assertIn("Stop-Tunnel", body)
        self.assertIn("Stop-ChatProfile", body)

    def test_tray_has_three_state_colors(self):
        self.assertIn("System.Drawing.Color]::Crimson", self.tray)
        self.assertIn("System.Drawing.Color]::Goldenrod", self.tray)
        self.assertIn("System.Drawing.Color]::LimeGreen", self.tray)

    def test_tray_exposes_explicit_controls(self):
        for expected in (
            "Переключить ВКЛ / ВЫКЛ",
            "Включить",
            "Выключить",
            "Открыть журнал",
            "Закрыть индикатор",
        ):
            self.assertIn(expected, self.tray)
        self.assertIn("add_DoubleClick", self.tray)

    def test_expected_profiles_remain_explicit(self):
        for profile in (
            "reference",
            "files-readonly",
            "browser-isolated",
        ):
            self.assertIn(profile, self.controller)
            self.assertIn(profile, self.tray)

    def test_ci_parses_new_lifecycle_scripts_and_runs_python_tests(self):
        self.assertIn("scripts/chat-platform-controller.ps1", self.ci)
        self.assertIn("scripts/chat-platform-tray.ps1", self.ci)
        self.assertIn("scripts/start-chat-profile.ps1", self.ci)
        self.assertIn(
            'python -m unittest discover -s tests -p "test_*.py"',
            self.ci,
        )


if __name__ == "__main__":
    unittest.main()
