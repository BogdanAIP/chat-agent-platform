from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUNTIME = ROOT / "runtime"


class ChatPlatformControllerAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = (SCRIPTS / "chat-platform.ps1").read_text(encoding="utf-8")
        cls.controller = (SCRIPTS / "chat-platform-controller.ps1").read_text(encoding="utf-8")
        cls.direct = (SCRIPTS / "semantic-direct-controller.ps1").read_text(encoding="utf-8")
        cls.tray = (SCRIPTS / "chat-platform-tray.ps1").read_text(encoding="utf-8")
        cls.bootstrap = (SCRIPTS / "bootstrap-chat-platform.ps1").read_text(encoding="utf-8")
        cls.bootstrap_manager = (SCRIPTS / "bootstrap-manager-runtime.ps1").read_text(encoding="utf-8")
        cls.bootstrap_lifecycle = (SCRIPTS / "bootstrap-manager-lifecycle.ps1").read_text(encoding="utf-8")
        cls.bootstrap_tunnel = (SCRIPTS / "bootstrap-tunnel-runtime.ps1").read_text(encoding="utf-8")
        cls.bootstrap_full = cls.bootstrap + "\n" + cls.bootstrap_tunnel
        cls.profile_ci = (ROOT / ".github" / "workflows" / "chat-profile-acceptance.yml").read_text(encoding="utf-8")
        cls.ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        cls.start_semantic = (SCRIPTS / "start-semantic-profile.ps1").read_text(encoding="utf-8")
        cls.status_profile = (SCRIPTS / "status-chat-profile.ps1").read_text(encoding="utf-8")
        cls.stop_local = (SCRIPTS / "stop-local-bridge.ps1").read_text(encoding="utf-8")
        cls.start_local = (SCRIPTS / "start-local-bridge.ps1").read_text(encoding="utf-8")

    def test_tray_uses_authoritative_supervisor_projection_only(self):
        self.assertIn('"supervisor.json"', self.tray)
        self.assertIn("Read-JsonFile -Path $SupervisorStateFile", self.tray)
        self.assertIn('"desired-state.json"', self.tray)
        self.assertIn('"settings.json"', self.tray)
        self.assertNotIn("Invoke-ControllerStatus", self.tray)
        self.assertNotIn("-Action Status", self.tray)
        self.assertNotIn("chat-platform-controller.ps1", self.tray)
        self.assertNotIn("Win32_Process", self.tray)
        self.assertNotIn("server.pid", self.tray)
        self.assertNotIn("Get-TunnelProcesses", self.tray)

    def test_tray_green_requires_runtime_mcp_and_tunnel_readiness(self):
        self.assertIn('"runtime_ready" -DefaultValue $false', self.tray)
        self.assertIn('"mcp_ready" -DefaultValue $false', self.tray)
        self.assertIn('"tunnel_local_ready" -DefaultValue $false', self.tray)
        self.assertIn("$runtimeReady -and $mcpReady -and $tunnelReady", self.tray)
        self.assertIn('$mode = "on"', self.tray)

    def test_tray_has_three_state_colors(self):
        self.assertIn("System.Drawing.Color]::Crimson", self.tray)
        self.assertIn("System.Drawing.Color]::Goldenrod", self.tray)
        self.assertIn("System.Drawing.Color]::LimeGreen", self.tray)
        self.assertNotIn("DodgerBlue", self.tray)

    def test_tray_exposes_simple_operator_controls(self):
        for expected in (
            '"Режим: Ручной"',
            '"Режим: Автоматический"',
            '"Автоматический — проверка раз в 30 мин"',
            '"Включить"',
            '"Выключить"',
            '"Дополнительно"',
            '"Открыть журнал"',
            '"Закрыть индикатор"',
        ):
            self.assertIn(expected, self.tray)
        self.assertIn("add_DoubleClick", self.tray)
        self.assertNotIn('$toggleItem = New-Object System.Windows.Forms.ToolStripMenuItem', self.tray)
        self.assertNotIn('$startItem = New-Object System.Windows.Forms.ToolStripMenuItem', self.tray)
        self.assertNotIn('$stopItem = New-Object System.Windows.Forms.ToolStripMenuItem', self.tray)

    def test_tray_diagnostics_are_nested_under_more_menu(self):
        self.assertIn('$moreMenu.DropDownItems.Add($detailsItem)', self.tray)
        self.assertIn('$moreMenu.DropDownItems.Add($workspaceItem)', self.tray)
        self.assertIn('$moreMenu.DropDownItems.Add($logItem)', self.tray)

    def test_direct_semantic_uses_neutral_persistent_tunnel_state(self):
        self.assertIn("$TunnelStateFile = Join-Path $StateDir 'tunnel.json'", self.direct)
        self.assertIn("function Get-PersistentTunnelId", self.direct)
        self.assertIn("Persistent tunnel state does not contain a valid tunnel_id", self.direct)
        self.assertIn("return $persistent", self.direct)
        self.assertIn("$LegacyTunnelProfile = Join-Path $TunnelDir 'local-1mcp.yaml'", self.direct)
        self.assertIn("Get-LegacyTunnelId", self.direct)

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

    def test_expected_internal_profiles_remain_explicit(self):
        for profile in ("reference", "files-readonly", "browser-isolated", "semantic", "adaptive"):
            self.assertIn(profile, self.controller)

    def test_adaptive_profile_uses_scoped_files_root_and_shared_lifecycle(self):
        expected_validate = (
            '[ValidateSet("reference", "files-readonly", '
            '"browser-isolated", "semantic", "adaptive")]'
        )
        self.assertIn(expected_validate, self.controller)
        self.assertIn(expected_validate, self.command)
        self.assertIn("adaptive", self.bootstrap_manager)

    def test_bootstrap_installs_canonical_six_tool_semantic_runtime(self):
        for expected in (
            "start-semantic-profile.ps1",
            "semantic-projection-runtime.ps1",
            "runtime\\chat-profiles\\semantic\\mcp.json",
            "runtime\\semantic-projection\\package.json",
            "runtime\\semantic-projection\\bin\\semantic-control-plane-projection.mjs",
            "runtime\\control_plane\\cli.py",
            "runtime\\control_plane\\verified_workspace_artifact.py",
        ):
            self.assertIn(expected, self.bootstrap_manager)
        self.assertIn("Assert-ChatInstalledSixToolSemanticRuntime", self.bootstrap_manager)
        self.assertIn("semantic_public_tool_count = 6", self.bootstrap_manager)
        self.assertIn("SEMANTIC_PUBLIC_TOOL_COUNT=6", self.bootstrap_manager)

    def test_normal_bootstrap_requires_node_python_but_not_1mcp(self):
        self.assertIn('Node.js 20 or newer is required', self.bootstrap)
        self.assertIn("Require-Command 'python.exe'", self.bootstrap)
        self.assertIn("Require-Command 'npm.cmd'", self.bootstrap)
        self.assertNotIn("Require-Command 'npx.cmd'", self.bootstrap)
        self.assertNotIn("OneMcpPackage", self.bootstrap)
        self.assertIn("NORMAL_SEMANTIC_1MCP_REQUIRED=False", self.bootstrap)

    def test_bootstrap_pins_official_tunnel_client_release_and_checksums(self):
        self.assertIn("$AcceptedTunnelClientVersion = 'v0.0.11'", self.bootstrap)
        self.assertNotIn("/releases/latest", self.bootstrap_full)
        self.assertIn("SHA256SUMS.txt", self.bootstrap_tunnel)
        self.assertIn("Get-FileHash", self.bootstrap_tunnel)

    def test_bootstrap_persists_neutral_tunnel_anchor_with_legacy_migration(self):
        self.assertIn("$TunnelStateFile = Join-Path $StateDir 'tunnel.json'", self.bootstrap)
        self.assertIn("Resolve-ChatTunnelId", self.bootstrap)
        self.assertIn("Read-ChatTunnelState", self.bootstrap_tunnel)
        self.assertIn("Save-ChatTunnelState", self.bootstrap_tunnel)
        self.assertIn("legacy-profile-migration", self.bootstrap_tunnel)
        self.assertIn("TUNNEL_ID_SOURCE=state/tunnel.json", self.bootstrap_tunnel)

    def test_bootstrap_initializes_semantic_core_and_dpapi_without_legacy_install(self):
        for expected in (
            "Save-ChatProtectedApiKeyIfMissing",
            "[Security.Cryptography.ProtectedData]::Protect",
            "Initialize-ChatSemanticCore",
            "-Action SetProfile",
            "-Profile semantic",
            "DEFAULT_TUNNEL_BINDING=direct-stdio",
            "LEGACY_1MCP_INSTALL_PATH_USED=False",
        ):
            self.assertIn(expected, self.bootstrap_lifecycle)
        self.assertIn("Initialize-ChatSemanticCore", self.bootstrap)

    def test_bootstrap_smoke_uses_normal_six_tool_direct_semantic(self):
        for expected in (
            "-Profile semantic",
            "-FilesRoot $smokeRoot",
            "BOOTSTRAP_SMOKE_PROFILE=semantic",
            "BOOTSTRAP_SMOKE_BINDING=direct-stdio",
            "BOOTSTRAP_SMOKE_PUBLIC_TOOL_COUNT=6",
            "BOOTSTRAP_SMOKE_1MCP_REQUIRED=False",
        ):
            self.assertIn(expected, self.bootstrap_lifecycle)

    def test_profile_acceptance_is_direct_semantic_and_1mcp_runtime_free(self):
        for expected in (
            "scripts/chat-platform-controller.ps1",
            "scripts/chat-platform.ps1",
            "scripts/chat-platform-tray.ps1",
            "scripts/bootstrap-chat-platform.ps1",
            "scripts/bootstrap-tunnel-runtime.ps1",
            "scripts/bootstrap-manager-runtime.ps1",
            "scripts/bootstrap-manager-lifecycle.ps1",
        ):
            self.assertIn(expected, self.profile_ci)
        self.assertIn("SEMANTIC_PUBLIC_MANAGER_1MCP_REQUIRED=False", self.profile_ci)

    def test_ci_recursively_parses_scripts_and_runs_python_tests(self):
        self.assertIn("Get-ChildItem -LiteralPath 'scripts' -Filter '*.ps1' -File -Recurse", self.ci)
        self.assertIn("POWERSHELL_PARSE_COUNT", self.ci)
        self.assertIn('python -m unittest discover -s tests -p "test_*.py"', self.ci)


if __name__ == "__main__":
    unittest.main()
