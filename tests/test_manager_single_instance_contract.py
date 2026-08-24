import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts" / "chat-platform.ps1"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"
BOOTSTRAP_MANAGER = ROOT / "scripts" / "bootstrap-manager-runtime.ps1"
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


class ManagerSingleInstanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = COMMAND.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.bootstrap_manager = BOOTSTRAP_MANAGER.read_text(encoding="utf-8")

    def test_owner_state_is_shared_in_local_appdata(self):
        self.assertIn('Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"', self.command)
        self.assertIn('"manager-owner.json"', self.command)
        self.assertIn('schema_version = 1', self.command)
        self.assertIn('controller_path =', self.command)
        self.assertIn('repo_root =', self.command)

    def test_status_delegates_to_the_recorded_owner(self):
        self.assertIn('function Get-EffectiveOwnerControllerPath', self.command)
        self.assertIn('function Invoke-ControllerStatusAt', self.command)
        self.assertIn('if ($Action -eq "Status")', self.command)
        self.assertIn('Invoke-ControllerStatusAt -TargetControllerPath $ownerController', self.command)

    def test_start_stops_a_foreign_owner_before_switching_copies(self):
        self.assertIn('function Stop-ForeignManagerIfNeeded', self.command)
        self.assertIn('$null = Stop-ForeignManagerIfNeeded', self.command)
        self.assertIn('-TargetAction "Stop"', self.command)
        self.assertIn('Wait-SharedRuntimeFree -TimeoutSeconds 15', self.command)
        self.assertIn('Get-McpPortDiagnostic', self.command)
        self.assertIn('Get-DirectTunnelDiagnostic', self.command)

    def test_unowned_runtime_is_fail_closed(self):
        self.assertIn('function Assert-SharedRuntimeFree', self.command)
        self.assertIn('Get-NetTCPConnection', self.command)
        self.assertIn('Get-DirectTunnelProcesses', self.command)
        self.assertIn('A shared Chat Agent Platform runtime is already active', self.command)
        self.assertIn('Refusing ambiguous startup', self.command)
        self.assertIn('$diagnosticLine = (', self.command)
        self.assertIn('$lines.Add($diagnosticLine)', self.command)

    @unittest.skipUnless(
        os.name == "nt" and shutil.which("pwsh.exe"),
        "Windows PowerShell runtime acceptance only",
    )
    def test_unowned_port_runtime_refuses_foreign_listener(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

        try:
            listener.bind(("127.0.0.1", 3050))
            listener.listen(1)

            with tempfile.TemporaryDirectory(prefix="chat-agent-platform-owner-test-") as local_app_data:
                env = os.environ.copy()
                env["LOCALAPPDATA"] = local_app_data

                completed = subprocess.run(
                    [
                        shutil.which("pwsh.exe"),
                        "-NoLogo",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(COMMAND),
                        "-Action",
                        "Start",
                        "-Profile",
                        "reference",
                        "-NoNotify",
                    ],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=20,
                    check=False,
                )

                plain_output = ANSI_ESCAPE.sub("", f"{completed.stdout}\n{completed.stderr}")
                combined = re.sub(r"\s+", " ", plain_output).strip()

                self.assertNotEqual(completed.returncode, 0, combined)
                self.assertIn("A shared Chat Agent Platform runtime is already active", combined)
                self.assertIn("Refusing", combined)
                self.assertIn("ambiguous startup", combined)
                self.assertIn("port 3050", combined)
                self.assertIn("python.exe", combined)
                self.assertNotIn("Error formatting a string", combined)

                owner_file = (
                    Path(local_app_data)
                    / "ChatAgentPlatform"
                    / "state"
                    / "manager-owner.json"
                )
                self.assertFalse(owner_file.exists())
                self.assertGreaterEqual(listener.fileno(), 0)
        finally:
            listener.close()

    def test_toggle_of_foreign_owner_stops_instead_of_double_start(self):
        self.assertIn('elseif ($Action -eq "Toggle" -and $foreignOwner)', self.command)
        self.assertRegex(
            self.command,
            re.compile(
                r'elseif \(\$Action -eq "Toggle" -and \$foreignOwner\).*?'
                r'Invoke-InternalControllerMutation.*?'
                r'-TargetAction "Stop"',
                re.S,
            ),
        )

    def test_set_profile_checks_authoritative_owner_runtime(self):
        self.assertIn('function Assert-ProfileCanChange', self.command)
        self.assertIn('Get-ControllerStatusObjectAt -TargetControllerPath $ownerController', self.command)
        self.assertIn('Stop the platform before changing its default profile.', self.command)
        self.assertIn('Set-SharedProfile', self.command)

    def test_direct_runtime_is_part_of_single_owner_fail_closed_scope(self):
        self.assertIn('function Get-DirectTunnelProcesses', self.command)
        self.assertIn('function Test-AnySharedRuntime', self.command)
        self.assertIn('@(Get-McpPortListeners).Count -gt 0', self.command)
        self.assertIn('@(Get-DirectTunnelProcesses).Count -gt 0', self.command)
        self.assertIn('semantic-direct', self.command)
        self.assertIn('direct-stdio', self.command)

    def test_bootstrap_propagates_public_manager_into_installed_bundle(self):
        self.assertIn("bootstrap-manager-runtime.ps1", self.bootstrap)
        self.assertIn("Install-ChatManagerBundle", self.bootstrap)
        self.assertIn("'chat-platform.ps1'", self.bootstrap_manager)
        self.assertIn('Copy-ChatVerifiedFile', self.bootstrap_manager)
        self.assertIn("Join-Path $LocalRoot 'app'", self.bootstrap)
        self.assertIn("semantic_public_tool_count = 6", self.bootstrap_manager)


if __name__ == "__main__":
    unittest.main()
