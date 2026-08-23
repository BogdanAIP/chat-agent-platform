from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / "scripts" / "chat-platform.ps1"
SUPERVISOR = ROOT / "scripts" / "chat-platform-supervisor.ps1"


class DesiredStateSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manager = MANAGER.read_text(encoding="utf-8")
        cls.supervisor = SUPERVISOR.read_text(encoding="utf-8")

    def test_manager_has_independent_persistent_desired_state(self) -> None:
        self.assertIn('desired-state.json', self.manager)
        self.assertIn('function Save-DesiredState', self.manager)
        self.assertIn('function Ensure-DesiredStateMigration', self.manager)
        self.assertIn('"legacy_migration"', self.manager)
        self.assertIn('"user_action"', self.manager)

    def test_manager_records_intent_before_runtime_mutation(self) -> None:
        intent_block = self.manager.index('if ($Action -eq "Start") {\n            Save-DesiredState')
        mutation_block = self.manager.index('if ($Action -eq "Stop" -and $foreignOwner)')
        self.assertLess(intent_block, mutation_block)
        self.assertIn('Save-DesiredState -DesiredState "running" -Source "user_action"', self.manager)
        self.assertIn('Save-DesiredState -DesiredState "stopped" -Source "user_action"', self.manager)
        self.assertIn('$toggleTarget = if (Test-AnySharedRuntime) { "stopped" } else { "running" }', self.manager)

    def test_runtime_owner_remains_a_separate_receipt(self) -> None:
        self.assertIn('$OwnerFile = Join-Path $StateDir "manager-owner.json"', self.manager)
        self.assertIn('$DesiredStateFile = Join-Path $StateDir "desired-state.json"', self.manager)
        self.assertIn('function Save-ManagerOwner', self.manager)
        self.assertIn('function Remove-ManagerOwner', self.manager)

    def test_supervisor_reads_intent_separately_from_owner(self) -> None:
        self.assertIn("$DesiredStateFile = Join-Path $StateDir 'desired-state.json'", self.supervisor)
        self.assertIn('function Get-PersistedDesiredState', self.supervisor)
        self.assertIn('$intent = Get-PersistedDesiredState', self.supervisor)
        self.assertIn('$owner = Get-ManagerOwner', self.supervisor)
        self.assertIn('desired_state = [string]$intent.desired_state', self.supervisor)
        self.assertNotIn("desired_state = if ($null -ne $owner) { 'running' } else { 'stopped' }", self.supervisor)

    def test_recovery_rechecks_persistent_intent_after_mutex(self) -> None:
        recovery = self.supervisor[
            self.supervisor.index('function Invoke-DirectRuntimeRecovery') :
            self.supervisor.index('function New-SupervisorSnapshot')
        ]
        mutex_check = recovery.index('$acquired = $mutex.WaitOne')
        intent_check = recovery.index('$currentIntent = Get-PersistedDesiredState')
        owner_check = recovery.index('$currentOwner = Get-ManagerOwner')
        destructive_stop = recovery.index('ControllerAction Stop')
        self.assertLess(mutex_check, intent_check)
        self.assertLess(intent_check, owner_check)
        self.assertLess(owner_check, destructive_stop)
        self.assertIn("Desired state changed before recovery; explicit Stop wins.", recovery)

    def test_internal_manager_mutations_do_not_spawn_console_windows(self) -> None:
        mutation = self.manager[
            self.manager.index('function Invoke-InternalControllerMutation') :
            self.manager.index('function Get-EffectiveOwnerControllerPath')
        ]
        self.assertIn('$startInfo.CreateNoWindow = $true', mutation)


@unittest.skipUnless(shutil.which("pwsh") or shutil.which("pwsh.exe"), "PowerShell 7 unavailable")
class DesiredStatePowerShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pwsh = shutil.which("pwsh") or shutil.which("pwsh.exe")

    def _write_fake_manager(self, root: Path, payload: dict) -> Path:
        path = root / "fake-manager.ps1"
        payload_json = json.dumps(payload, separators=(",", ":"))
        path.write_text(
            textwrap.dedent(
                f"""
                param([string]$Action = 'Status', [switch]$NoNotify)
                if ($Action -ne 'Status') {{ exit 3 }}
                @'
                {payload_json}
                '@ | Write-Output
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return path

    def _reconcile(self, local_app_data: Path, manager: Path) -> dict:
        env = os.environ.copy()
        env["LOCALAPPDATA"] = str(local_app_data)
        completed = subprocess.run(
            [
                self.pwsh,
                "-NoLogo",
                "-NoProfile",
                "-File",
                str(SUPERVISOR),
                "-Action",
                "Reconcile",
                "-NoRecovery",
                "-ManagerCommandPath",
                str(manager),
            ],
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )
        return json.loads(completed.stdout)

    @staticmethod
    def _state_dir(local: Path) -> Path:
        state_dir = local / "ChatAgentPlatform" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir

    def test_stopped_intent_outranks_present_owner_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "local"
            state_dir = self._state_dir(local)
            (state_dir / "desired-state.json").write_text(
                json.dumps({"schema_version": 1, "desired_state": "stopped", "source": "user_action"}),
                encoding="utf-8",
            )
            (state_dir / "manager-owner.json").write_text(
                json.dumps({"controller_path": r"C:\placeholder\semantic-direct-controller.ps1"}),
                encoding="utf-8",
            )
            manager = self._write_fake_manager(
                root,
                {
                    "active_count": 0,
                    "tunnel_running": False,
                    "mcp_ready": False,
                    "tunnel_ready": False,
                    "tunnel_binding": "direct-stdio",
                    "settings": {"profile": "semantic"},
                },
            )
            state = self._reconcile(local, manager)
            self.assertEqual(state["desired_state"], "stopped")
            self.assertEqual(state["supervisor_state"], "stopped")
            self.assertEqual(state["health_code"], "STOPPED")

    def test_running_intent_does_not_depend_on_owner_presence_when_runtime_is_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "local"
            state_dir = self._state_dir(local)
            (state_dir / "desired-state.json").write_text(
                json.dumps({"schema_version": 1, "desired_state": "running", "source": "user_action"}),
                encoding="utf-8",
            )
            manager = self._write_fake_manager(
                root,
                {
                    "active_count": 1,
                    "tunnel_running": True,
                    "mcp_ready": True,
                    "tunnel_ready": True,
                    "runtime_ready": True,
                    "openai_ready": True,
                    "health_code": "READY",
                    "recovery_action": "none",
                    "tunnel_binding": "direct-stdio",
                    "remote_tunnel_status": "ready",
                    "control_plane_poll_fresh": True,
                    "settings": {"profile": "semantic"},
                },
            )
            state = self._reconcile(local, manager)
            self.assertEqual(state["desired_state"], "running")
            self.assertEqual(state["supervisor_state"], "healthy")
            self.assertEqual(state["health_code"], "READY")

    def test_legacy_owner_migrates_to_running_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "local"
            state_dir = self._state_dir(local)
            (state_dir / "manager-owner.json").write_text(
                json.dumps({"controller_path": r"C:\placeholder\semantic-direct-controller.ps1"}),
                encoding="utf-8",
            )
            manager = self._write_fake_manager(
                root,
                {
                    "active_count": 1,
                    "tunnel_running": True,
                    "mcp_ready": True,
                    "tunnel_ready": True,
                    "runtime_ready": True,
                    "openai_ready": True,
                    "health_code": "READY",
                    "recovery_action": "none",
                    "tunnel_binding": "direct-stdio",
                    "remote_tunnel_status": "ready",
                    "control_plane_poll_fresh": True,
                    "settings": {"profile": "semantic"},
                },
            )
            state = self._reconcile(local, manager)
            desired = json.loads((state_dir / "desired-state.json").read_text(encoding="utf-8-sig"))
            self.assertEqual(state["desired_state"], "running")
            self.assertEqual(desired["desired_state"], "running")
            self.assertEqual(desired["source"], "legacy_migration")


if __name__ == "__main__":
    unittest.main()
