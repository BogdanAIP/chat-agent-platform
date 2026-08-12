from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

CONTROLLER = ROOT / "scripts" / "chat-platform-controller.ps1"
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"
STATUS_PROFILE = ROOT / "scripts" / "status-chat-profile.ps1"
STOP_LOCAL = ROOT / "scripts" / "stop-local-bridge.ps1"
CI = ROOT / ".github" / "workflows" / "ci.yml"
PROFILE_CI = ROOT / ".github" / "workflows" / "chat-profiles.yml"


class ChatPlatformControllerAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.tray = TRAY.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.status_profile = STATUS_PROFILE.read_text(encoding="utf-8")
        cls.stop_local = STOP_LOCAL.read_text(encoding="utf-8")
        cls.ci = CI.read_text(encoding="utf-8")
        cls.profile_ci = PROFILE_CI.read_text(encoding="utf-8")

    def test_controller_tray_and_bootstrap_exist(self):
        self.assertTrue(CONTROLLER.is_file())
        self.assertTrue(TRAY.is_file())
        self.assertTrue(BOOTSTRAP.is_file())

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
        combined = self.controller + "\n" + self.tray + "\n" + self.bootstrap
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

    def test_profile_status_keeps_conflict_machine_readable(self):
        self.assertIn("conflict = $conflict", self.status_profile)
        self.assertIn("'conflict'", self.status_profile)
        self.assertIn("exit 0", self.status_profile)
        self.assertNotIn("More than one Chat-facing Runtime Scope", self.status_profile)

    def test_stop_scripts_share_idempotent_exit_codes(self):
        self.assertIn("-in @(3, 7)", self.stop_local)
        self.assertIn(
            "-notin @(0, 3, 7)",
            (ROOT / "scripts" / "stop-chat-profile.ps1").read_text(
                encoding="utf-8"
            ),
        )

    def test_tray_uses_authoritative_controller_status_only(self):
        self.assertIn("Invoke-ControllerStatus", self.tray)
        self.assertIn("-Action Status", self.tray)
        self.assertNotIn("Win32_Process", self.tray)
        self.assertNotIn("server.pid", self.tray)
        self.assertNotIn("Get-TunnelProcesses", self.tray)

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
        self.assertIn("ExecutablePath", self.controller)
        self.assertIn("$actualExe -ieq $expectedExe", self.controller)
        self.assertIn("--profile-dir", self.controller)
        self.assertIn("local-1mcp", self.controller)
        self.assertIn("(?=\\s|$)", self.controller)

    def test_tunnel_readiness_uses_official_readyz_probe(self):
        self.assertIn("tunnel-health.url", self.controller)
        self.assertIn("/readyz", self.controller)
        self.assertIn("--health.listen-addr 127.0.0.1:0", self.controller)
        self.assertIn("--health.url-file", self.controller)
        self.assertIn("Wait-TunnelReady", self.controller)
        self.assertIn("tunnel_ready", self.controller)

    def test_tray_green_requires_controller_mcp_and_tunnel_readiness(self):
        self.assertIn("[bool]$state.mcp_ready", self.tray)
        self.assertIn("[bool]$state.tunnel_ready", self.tray)
        self.assertIn('$mode = "on"', self.tray)

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

    def test_expected_profiles_remain_explicit_in_controller(self):
        for profile in (
            "reference",
            "files-readonly",
            "browser-isolated",
        ):
            self.assertIn(profile, self.controller)

    def test_bootstrap_pins_official_tunnel_client_release_and_checksums(self):
        self.assertIn('$AcceptedTunnelClientVersion = "v0.0.11"', self.bootstrap)
        self.assertIn(
            "https://api.github.com/repos/openai/tunnel-client/releases/tags/",
            self.bootstrap,
        )
        self.assertNotIn("/releases/latest", self.bootstrap)
        self.assertIn("SHA256SUMS.txt", self.bootstrap)
        self.assertIn(
            "eb912c86c6ccde90cda805cb17009507176a656725cf86c36fabe1901a12e29b",
            self.bootstrap,
        )
        self.assertIn(
            "38f015a720404c8ccd5976a0d6aed18d931899697eaf208548b5eb3d0f6e8592",
            self.bootstrap,
        )
        self.assertIn("asset_digest", self.bootstrap)
        self.assertIn("Get-FileHash", self.bootstrap)

    def test_bootstrap_uses_official_cli_to_create_local_profile(self):
        for expected in (
            '"init"',
            '"sample_mcp_remote_no_auth"',
            '"--profile-dir"',
            '"--tunnel-id"',
            '"--mcp-server-url"',
            '"http://127.0.0.1:3050/mcp"',
            '"local-1mcp"',
        ):
            self.assertIn(expected, self.bootstrap)
        self.assertIn("Invoke-ControllerProcess -Action Install", self.bootstrap)
        self.assertIn("BOOTSTRAP_SMOKE_TEST=passed", self.bootstrap)

    def test_profile_acceptance_runs_when_manager_changes(self):
        for expected in (
            "scripts/chat-platform-controller.ps1",
            "scripts/chat-platform-tray.ps1",
            "scripts/bootstrap-chat-platform.ps1",
        ):
            self.assertIn(expected, self.profile_ci)
        self.assertIn(
            "Prove controller can observe and clean conflicting runtime scopes",
            self.profile_ci,
        )

    def test_ci_parses_new_lifecycle_scripts_and_runs_python_tests(self):
        self.assertIn("scripts/chat-platform-controller.ps1", self.ci)
        self.assertIn("scripts/chat-platform-tray.ps1", self.ci)
        self.assertIn("scripts/bootstrap-chat-platform.ps1", self.ci)
        self.assertIn("scripts/start-chat-profile.ps1", self.ci)
        self.assertIn(
            'python -m unittest discover -s tests -p "test_*.py"',
            self.ci,
        )


if __name__ == "__main__":
    unittest.main()
