from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

CONTROLLER = ROOT / "scripts" / "chat-platform-controller.ps1"
DIRECT = ROOT / "scripts" / "semantic-direct-controller.ps1"
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"
COMMAND = ROOT / "scripts" / "chat-platform.ps1"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"
BOOTSTRAP_TUNNEL = ROOT / "scripts" / "bootstrap-tunnel-runtime.ps1"
BOOTSTRAP_MANAGER = ROOT / "scripts" / "bootstrap-manager-runtime.ps1"
BOOTSTRAP_LIFECYCLE = ROOT / "scripts" / "bootstrap-manager-lifecycle.ps1"
START_LOCAL = ROOT / "scripts" / "start-local-bridge.ps1"
START_SEMANTIC = ROOT / "scripts" / "start-semantic-profile.ps1"
SEMANTIC_RUNTIME = ROOT / "scripts" / "semantic-projection-runtime.ps1"
STATUS_PROFILE = ROOT / "scripts" / "status-chat-profile.ps1"
STOP_LOCAL = ROOT / "scripts" / "stop-local-bridge.ps1"
CI = ROOT / ".github" / "workflows" / "ci.yml"
PROFILE_CI = ROOT / ".github" / "workflows" / "chat-profiles.yml"


class ChatPlatformControllerAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.direct = DIRECT.read_text(encoding="utf-8")
        cls.tray = TRAY.read_text(encoding="utf-8")
        cls.command = COMMAND.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.bootstrap_tunnel = BOOTSTRAP_TUNNEL.read_text(encoding="utf-8")
        cls.bootstrap_manager = BOOTSTRAP_MANAGER.read_text(encoding="utf-8")
        cls.bootstrap_lifecycle = BOOTSTRAP_LIFECYCLE.read_text(encoding="utf-8")
        cls.bootstrap_full = "\n".join(
            (
                cls.bootstrap,
                cls.bootstrap_tunnel,
                cls.bootstrap_manager,
                cls.bootstrap_lifecycle,
            )
        )
        cls.start_local = START_LOCAL.read_text(encoding="utf-8")
        cls.start_semantic = START_SEMANTIC.read_text(encoding="utf-8")
        cls.semantic_runtime = SEMANTIC_RUNTIME.read_text(encoding="utf-8")
        cls.status_profile = STATUS_PROFILE.read_text(encoding="utf-8")
        cls.stop_local = STOP_LOCAL.read_text(encoding="utf-8")
        cls.ci = CI.read_text(encoding="utf-8")
        cls.profile_ci = PROFILE_CI.read_text(encoding="utf-8")

    def test_controller_tray_command_and_modular_bootstrap_exist(self):
        for path in (
            CONTROLLER,
            DIRECT,
            COMMAND,
            TRAY,
            BOOTSTRAP,
            BOOTSTRAP_TUNNEL,
            BOOTSTRAP_MANAGER,
            BOOTSTRAP_LIFECYCLE,
            START_SEMANTIC,
            SEMANTIC_RUNTIME,
        ):
            self.assertTrue(path.is_file(), path)

    def test_controller_uses_persistent_local_appdata_and_dpapi(self):
        self.assertIn('Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"', self.controller)
        self.assertIn('"control-plane-api-key.dpapi"', self.controller)
        self.assertIn("[Security.Cryptography.ProtectedData]::Protect", self.controller)
        self.assertIn("[Security.Cryptography.DataProtectionScope]::CurrentUser", self.controller)

    def test_secret_is_not_embedded_in_source(self):
        combined = "\n".join(
            (self.controller, self.direct, self.command, self.tray, self.bootstrap_full)
        )
        self.assertIsNone(re.search(r"sk-[A-Za-z0-9_-]{20,}", combined))

    def test_controller_uses_pwsh_tray_shortcut(self):
        self.assertIn('"pwsh.exe"', self.controller)
        self.assertIn('"scripts\\chat-platform-tray.ps1"', self.controller)
        self.assertIn("-WindowStyle Hidden", self.controller)

    def test_default_reference_profile_has_supported_start_path(self):
        self.assertIn('profile = "reference"', self.controller)
        self.assertIn("$StartLocalBridgeScript", self.controller)
        self.assertRegex(
            self.controller,
            re.compile(
                r'if \(\$desiredProfile -eq "reference"\).*?& \$StartLocalBridgeScript',
                re.S,
            ),
        )

    def test_controller_uses_authoritative_profile_status_script(self):
        self.assertIn("$StatusChatScript", self.controller)
        self.assertRegex(
            self.controller,
            re.compile(
                r'function Get-ChatProfileStatus.*?-File \$StatusChatScript',
                re.S,
            ),
        )

    def test_public_manager_serializes_mutating_operations(self):
        self.assertIn("Local\\ChatAgentPlatformControllerOperation", self.command)
        self.assertIn("WaitOne($MutexTimeoutMilliseconds)", self.command)
        self.assertIn("AbandonedMutexException", self.command)
        self.assertIn('if ($Action -eq "Status")', self.command)
        self.assertIn('"chat-platform-controller.ps1"', self.command)

    def test_public_manager_waits_on_exact_mutating_child_process(self):
        self.assertIn("System.Diagnostics.ProcessStartInfo", self.command)
        self.assertIn("Invoke-InternalControllerMutation", self.command)
        mutation = re.search(
            r"function Invoke-InternalControllerMutation \{(.*?)\n\}",
            self.command,
            re.S,
        )
        self.assertIsNotNone(mutation)
        body = mutation.group(1)
        self.assertIn("WaitForExit()", body)
        self.assertIn("$process.ExitCode", body)
        self.assertNotIn("& $pwsh", body)

    def test_windows_1mcp_worker_remains_internal_and_console_free(self):
        for expected in (
            "Start-HiddenWindowsWorker",
            "Get-Command 'npx.cmd'",
            "Get-Command 'npm.cmd'",
            "OneMcpLauncherPackage",
            "System.Diagnostics.ProcessStartInfo",
            "$startInfo.FileName = $cmd",
            "$startInfo.CreateNoWindow = $true,
            "$startInfo.UseShellExecute = $false",
            "$startInfo.ArgumentList.Add('/c')",
            "$windowsLauncher",
            "--transport http",
            "--log-file",
        ):
            self.assertIn(expected, self.start_local)
        self.assertNotIn("$ForegroundWorker", self.start_local)

    def test_profile_status_keeps_conflict_machine_readable(self):
        self.assertIn("conflict = $conflict", self.status_profile)
        self.assertIn("'conflict'", self.status_profile)
        self.assertIn("exit 0", self.status_profile)
        self.assertNotIn("More than one Chat-facing Runtime Scope", self.status_profile)

    def test_stop_scripts_share_idempotent_exit_codes(self):
        self.assertIn("-in @(3, 7)", self.stop_local)
        stop_chat = (ROOT / "scripts" / "stop-chat-profile.ps1").read_text(encoding="utf-8")
        self.assertIn("-notin @(0, 3, 7)", stop_chat)

    def test_tray_uses_authoritative_serialized_manager_status_only(self):
        self.assertIn("Invoke-ControllerStatus", self.tray)
        self.assertIn('"chat-platform.ps1"', self.tray)
        self.assertIn("-Action Status", self.tray)
        self.assertNotIn("chat-platform-controller.ps1", self.tray)
        self.assertNotIn("Win32_Process", self.tray)
        self.assertNotIn("server.pid", self.tray)
        self.assertNotIn("Get-TunnelProcesses", self.tray)

    def test_legacy_1mcp_profile_remains_supported_only_by_internal_controller(self):
        self.assertIn('$profileSource = "local-existing"', self.controller)
        self.assertIn('if (-not (Test-Path $TunnelProfile))', self.controller)
        self.assertIn('TUNNEL_PROFILE_SOURCE=$profileSource', self.controller)
        self.assertIn('local-1mcp', self.controller)

    def test_running_binary_is_not_blindly_overwritten(self):
        self.assertIn("local-existing-identical", self.controller)
        self.assertIn("local-running-update-deferred", self.controller)
        self.assertIn("Test-TunnelRunning", self.controller)

    def test_tunnel_process_matching_is_bound_to_installed_binary(self):
        self.assertIn("ExecutablePath", self.controller)
        self.assertIn("$actualExe -ieq $expectedExe", self.controller)
        self.assertIn("(?=\\s|$)", self.controller)

    def test_tunnel_readiness_uses_official_readyz_probe(self):
        self.assertIn("tunnel-health.url", self.controller)
        self.assertIn("/readyz", self.controller)
        self.assertIn("--health.listen-addr 127.0.0.1:0", self.controller)
        self.assertIn("--health.url-file", self.controller)
        self.assertIn("Wait-TunnelReady", self.controller)
        self.assertIn("tunnel_ready", self.controller)

    def test_direct_semantic_uses_neutral_persistent_tunnel_state(self):
        self.assertIn("$TunnelStateFile = Join-Path $StateDir 'tunnel.json'", self.direct)
        self.assertIn("function Get-PersistentTunnelId", self.direct)
        self.assertIn("Persistent tunnel state does not contain a valid tunnel_id", self.direct)
        self.assertIn("return $persistent", self.direct)
        self.assertIn("$LegacyTunnelProfile = Join-Path $TunnelDir 'local-1mcp.yaml'", self.direct)
        self.assertIn("Get-LegacyTunnelId", self.direct)
        self.assertNotIn("Accepted tunnel profile is missing", self.direct)
        self.assertNotIn("accepted local-1mcp profile", self.direct)

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
        self.assertNotIn("DodgerBlue", self.tray)

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
        self.assertRegex(
            self.controller,
            re.compile(
                r'elseif \(\$desiredProfile -in @\("files-readonly", "adaptive"\)\).*?'
                r'-Profile \$desiredProfile.*?-FilesRoot \$root',
                re.S,
            ),
        )
        self.assertIn(
            'if ($Profile -in @("files-readonly", "semantic", "adaptive"))',
            self.controller,
        )

    def test_semantic_profile_uses_fixed_projection_and_scoped_root(self):
        self.assertIn('$StartSemanticScript', self.controller)
        self.assertRegex(
            self.controller,
            re.compile(
                r'elseif \(\$desiredProfile -eq "semantic"\).*?'
                r'& \$StartSemanticScript.*?-FilesRoot \$root',
                re.S,
            ),
        )
        self.assertIn('SEMANTIC_RUNTIME_READY=True', self.controller)
        self.assertIn('Get-SemanticProjectionEntryPath', self.controller)
        self.assertIn('Get-SemanticProjectionEntryPath', self.start_semantic)
        self.assertIn('-EnsureDependencies', self.start_semantic)
        self.assertIn("'semantic'", self.status_profile)
        for forbidden in ('tool_invoke', 'tool_schema', 'mcp_enable'):
            self.assertNotIn(forbidden, self.start_semantic)

    def test_baseline_bootstrap_excludes_optional_adaptive_extension_assets(self):
        install_body = self.bootstrap_manager.split('function Install-ChatManagerBundle', 1)[1]
        for forbidden in (
            "runtime\\chat-profiles\\adaptive\\mcp.json",
            "runtime\\1mcp-adaptive-shim\\package.json",
            "runtime\\1mcp-adaptive-shim\\bin\\1mcp-adaptive.mjs",
            "runtime\\1mcp-adaptive-shim\\scripts\\apply-compatibility-patch.mjs",
        ):
            self.assertNotIn(forbidden, install_body)
        self.assertNotIn("Assert-ChatInstalledAdaptiveRuntime -AppRuntimeDir", install_body)
        self.assertIn("extension_manager_included = $false", install_body)
        self.assertIn("EXTENSION_MANAGER_INCLUDED=False", install_body)
        self.assertIn("runtime_assets", install_body)
        self.assertIn("schema_version = 4", install_body)

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
        self.assertIn("@modelcontextprotocol/server-filesystem", self.bootstrap_manager)
        self.assertIn("@playwright/mcp", self.bootstrap_manager)
        self.assertIn("semantic_public_tool_count = 6", self.bootstrap_manager)
        self.assertIn("SEMANTIC_PUBLIC_TOOL_COUNT=6", self.bootstrap_manager)

    def test_normal_bootstrap_requires_node_python_but_not_1mcp(self):
        self.assertIn('[int]$Matches.major -lt 20', self.bootstrap)
        self.assertIn('Node.js 20 or newer is required', self.bootstrap)
        self.assertIn("Require-Command 'python.exe'", self.bootstrap)
        self.assertIn("Require-Command 'npm.cmd'", self.bootstrap)
        self.assertNotIn("Require-Command 'npx.cmd'", self.bootstrap)
        self.assertNotIn("OneMcpPackage", self.bootstrap)
        self.assertNotIn("Pinned 1MCP dependency failed", self.bootstrap)
        self.assertIn("NORMAL_SEMANTIC_1MCP_REQUIRED=False", self.bootstrap)
        self.assertIn('Stop-ChatInstalledManagerForBundleUpdate', self.bootstrap_manager)

    def test_bootstrap_pins_official_tunnel_client_release_and_checksums(self):
        self.assertIn("$AcceptedTunnelClientVersion = 'v0.0.11'", self.bootstrap)
        self.assertIn("https://api.github.com/repos/openai/tunnel-client/releases/tags/", self.bootstrap)
        self.assertNotIn("/releases/latest", self.bootstrap_full)
        self.assertIn("SHA256SUMS.txt", self.bootstrap_tunnel)
        self.assertIn("eb912c86c6ccde90cda805cb17009507176a656725cf86c36fabe1901a12e29b", self.bootstrap)
        self.assertIn("38f015a720404c8ccd5976a0d6aed18d931899697eaf208548b5eb3d0f6e8592", self.bootstrap)
        self.assertIn("asset_digest", self.bootstrap_tunnel)
        self.assertIn("Get-FileHash", self.bootstrap_tunnel)

    def test_bootstrap_persists_neutral_tunnel_anchor_with_legacy_migration(self):
        self.assertIn("$TunnelStateFile = Join-Path $StateDir 'tunnel.json'", self.bootstrap)
        self.assertIn("Resolve-ChatTunnelId", self.bootstrap)
        self.assertIn("-TunnelStateFile $TunnelStateFile", self.bootstrap)
        self.assertIn("-LegacyTunnelProfile $LegacyTunnelProfile", self.bootstrap)
        self.assertIn("Read-ChatTunnelState", self.bootstrap_tunnel)
        self.assertIn("Save-ChatTunnelState", self.bootstrap_tunnel)
        self.assertIn("legacy-profile-migration", self.bootstrap_tunnel)
        self.assertIn("TUNNEL_ID_SOURCE=state/tunnel.json", self.bootstrap_tunnel)

    def test_extension_manager_profile_helper_is_optional_not_normal_bootstrap(self):
        for expected in (
            "Initialize-ChatExtensionManagerTunnelProfile",
            "'init'",
            "'sample_mcp_remote_no_auth'",
            "'--profile-dir'",
            "'local-1mcp'",
        ):
            self.assertIn(expected, self.bootstrap_tunnel)
        self.assertNotIn("Initialize-ChatExtensionManagerTunnelProfile", self.bootstrap)
        self.assertIn("EXTENSION_MANAGER=optional-1mcp", self.bootstrap)

    def test_bootstrap_keeps_first_key_prompt_interactive(self):
        self.assertRegex(
            self.bootstrap_lifecycle,
            re.compile(
                r"function Install-ChatManager \{.*?& \$pwsh.*?-Action Install",
                re.S,
            ),
        )
        status_capture = re.search(
            r"function Invoke-ChatManagerStatusCapture \{(.*?)\n\}",
            self.bootstrap_lifecycle,
            re.S,
        )
        self.assertIsNotNone(status_capture)
        self.assertNotIn("Install", status_capture.group(1))

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
        self.assertNotIn("-Profile reference", self.bootstrap_lifecycle)
        self.assertIn("System.Diagnostics.ProcessStartInfo", self.bootstrap_lifecycle)
        action = re.search(
            r"function Invoke-ChatManagerAction \{(.*?)\n\}",
            self.bootstrap_lifecycle,
            re.S,
        )
        self.assertIsNotNone(action)
        body = action.group(1)
        self.assertIn("WaitForExit()", body)
        self.assertNotIn("& $pwsh", body)

    def test_profile_acceptance_runs_when_manager_or_bootstrap_module_changes(self):
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
        self.assertIn(
            "Prove public manager can observe and clean conflicting runtime scopes",
            self.profile_ci,
        )

    def test_ci_recursively_parses_scripts_and_runs_python_tests(self):
        self.assertIn("Get-ChildItem -LiteralPath 'scripts' -Filter '*.ps1' -File -Recurse", self.ci)
        self.assertIn("POWERSHELL_PARSE_COUNT", self.ci)
        self.assertIn(
            'python -m unittest discover -s tests -p "test_*.py"',
            self.ci,
        )


if __name__ == "__main__":
    unittest.main()
