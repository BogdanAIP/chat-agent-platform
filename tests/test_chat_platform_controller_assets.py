from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

CONTROLLER = ROOT / "scripts" / "chat-platform-controller.ps1"
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"


class ChatPlatformControllerAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.tray = TRAY.read_text(encoding="utf-8")

    def test_controller_and_tray_exist(self):
        self.assertTrue(CONTROLLER.is_file())
        self.assertTrue(TRAY.is_file())

    def test_controller_uses_persistent_local_appdata(self):
        self.assertIn(
            'Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"',
            self.controller,
        )

        self.assertIn(
            '"control-plane-api-key.dpapi"',
            self.controller,
        )

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
            re.search(
                r"sk-[A-Za-z0-9_-]{20,}",
                combined,
            )
        )

    def test_controller_uses_pwsh_tray_shortcut(self):
        self.assertIn(
            '"pwsh.exe"',
            self.controller,
        )

        self.assertIn(
            '"scripts\\chat-platform-tray.ps1"',
            self.controller,
        )

        self.assertIn(
            "-WindowStyle Hidden",
            self.controller,
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
        self.assertIn(
            'local-existing-identical',
            self.controller,
        )

        self.assertIn(
            'local-running-update-deferred',
            self.controller,
        )

        self.assertIn(
            '$runningTunnel = @(',
            self.controller,
        )

    def test_tray_has_three_state_colors(self):
        self.assertIn(
            "System.Drawing.Color]::Crimson",
            self.tray,
        )

        self.assertIn(
            "System.Drawing.Color]::Goldenrod",
            self.tray,
        )

        self.assertIn(
            "System.Drawing.Color]::LimeGreen",
            self.tray,
        )

    def test_green_requires_mcp_health_and_tunnel(self):
        self.assertIn(
            "$mcp.running -and",
            self.tray,
        )

        self.assertIn(
            "$mcp.healthy -and",
            self.tray,
        )

        self.assertIn(
            "$tunnel",
            self.tray,
        )

        self.assertIn(
            "Invoke-WebRequest",
            self.tray,
        )

        self.assertIn(
            "/health/mcp/{0}",
            self.tray,
        )

    def test_tray_exposes_explicit_controls(self):
        for expected in (
            "Переключить ВКЛ / ВЫКЛ",
            "Включить",
            "Выключить",
            "Открыть журнал",
            "Закрыть индикатор",
        ):
            self.assertIn(expected, self.tray)

        self.assertIn(
            "add_DoubleClick",
            self.tray,
        )

    def test_expected_profiles_remain_explicit(self):
        for profile in (
            "reference",
            "files-readonly",
            "browser-isolated",
        ):
            self.assertIn(profile, self.controller)

        for profile in (
            "reference",
            "files-readonly",
            "browser-isolated",
        ):
            self.assertIn(profile, self.tray)


if __name__ == "__main__":
    unittest.main()
