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
HEALTH = ROOT / "scripts" / "tunnel-reliability-health.ps1"
CONTROLLER = ROOT / "scripts" / "semantic-direct-controller.ps1"
SUPERVISOR = ROOT / "scripts" / "chat-platform-supervisor.ps1"
INSTALLER = ROOT / "scripts" / "install-chat-platform-supervisor.ps1"


class TransportSupervisorSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.health = HEALTH.read_text(encoding="utf-8")
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.supervisor = SUPERVISOR.read_text(encoding="utf-8")
        cls.installer = INSTALLER.read_text(encoding="utf-8")

    def test_required_assets_exist(self) -> None:
        for path in (HEALTH, CONTROLLER, SUPERVISOR, INSTALLER):
            self.assertTrue(path.is_file(), path)

    def test_health_codes_and_recovery_actions_are_explicit(self) -> None:
        for code in (
            "REMOTE_TUNNEL_RESOURCE_MISSING",
            "REMOTE_TUNNEL_UNAUTHORIZED",
            "REMOTE_TUNNEL_FORBIDDEN",
            "REMOTE_METADATA_RATE_LIMITED",
            "REMOTE_METADATA_UNAVAILABLE",
            "REMOTE_TUNNEL_DISCONNECTED",
            "LOCAL_MCP_PROCESS_MISSING",
            "LOCAL_MCP_UNAVAILABLE",
            "LOCAL_TUNNEL_NOT_HEALTHY",
            "LOCAL_TUNNEL_NOT_RUNNING",
            "LOCAL_RUNTIME_CONFLICT",
        ):
            self.assertIn(code, self.health)
            self.assertIn(code, self.controller)
        for action in ("restart_runtime", "wait_and_probe", "blocked"):
            self.assertIn(action, self.health)
            self.assertIn(action, self.controller)

    def test_remote_authorization_and_resource_failures_outrank_restarts(self) -> None:
        resource = self.health.index("$RemoteStatus -eq 'resource_missing'")
        unauthorized = self.health.index("$RemoteStatus -eq 'unauthorized'")
        forbidden = self.health.index("$RemoteStatus -eq 'forbidden'")
        local_missing = self.health.index("$TunnelProcessCount -eq 0")
        self.assertLess(resource, local_missing)
        self.assertLess(unauthorized, local_missing)
        self.assertLess(forbidden, local_missing)

    def test_controller_uses_official_health_and_read_only_metadata_operations(self) -> None:
        self.assertIn("'health', '--json', '--url-file'", self.controller)
        self.assertIn("'--require-control-plane-poll'", self.controller)
        self.assertIn("@('admin', '--json', 'tunnels', 'get', $TunnelId)", self.controller)
        self.assertIn("OPENAI_ADMIN_KEY = $null", self.controller)
        self.assertNotIn("'tunnels', 'create'", self.controller)
        self.assertNotIn("'tunnels', 'delete'", self.controller)
        self.assertNotIn("'tunnels', 'update'", self.controller)

    def test_remote_probe_cache_does_not_persist_credentials_or_raw_error_bodies(self) -> None:
        cache_block = self.controller[
            self.controller.index("function Save-RemoteProbeCache") :
            self.controller.index("function Get-RemoteTunnelProbe")
        ]
        for forbidden in (
            "CONTROL_PLANE_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_ADMIN_KEY",
            "stderr",
            "message",
            "error =",
        ):
            self.assertNotIn(forbidden, cache_block)
        for required in ("tunnel_id", "status", "status_code", "request_id", "checked_at"):
            self.assertIn(required, cache_block)

    def test_semantic_child_cleanup_uses_well_formed_stop_process(self) -> None:
        self.assertIn(
            "Stop-Process -Id ([int]$_.ProcessId) -Force -ErrorAction SilentlyContinue",
            self.controller,
        )
        self.assertNotIn(
            "Stop-Process -Id ([int]$_.ProcessId -Force",
            self.controller,
        )

    def test_supervisor_is_single_instance_and_serializes_with_manager(self) -> None:
        self.assertIn("Local\\ChatAgentPlatformTransportSupervisor", self.supervisor)
        self.assertIn("Local\\ChatAgentPlatformControllerOperation", self.supervisor)
        self.assertIn("WaitOne($ManagerOperationMutexTimeoutMilliseconds)", self.supervisor)
        self.assertIn("Get-ManagerOwner", self.supervisor)
        self.assertIn("explicit Stop wins", self.supervisor)

    def test_supervisor_recovery_is_limited_to_installed_direct_controller(self) -> None:
        self.assertIn("InstalledDirectControllerPath", self.supervisor)
        self.assertIn("Assert-OwnedDirectControllerPath", self.supervisor)
        self.assertIn("Supervisor refuses non-installed direct controller ownership", self.supervisor)
        recovery = self.supervisor[
            self.supervisor.index("function Invoke-DirectRuntimeRecovery") :
            self.supervisor.index("function New-SupervisorSnapshot")
        ]
        self.assertIn("ControllerAction Stop", recovery)
        self.assertIn("ControllerAction Start", recovery)
        self.assertNotIn("-Action Stop", recovery)
        self.assertNotIn("-Action Start", recovery)

    def test_supervisor_has_burst_then_indefinite_slow_retry(self) -> None:
        self.assertIn("$BurstBackoffSeconds = @(0, 2, 10, 30)", self.supervisor)
        self.assertIn("$SlowRetrySeconds = 300", self.supervisor)
        self.assertIn("Get-Random -Minimum 0 -Maximum 31", self.supervisor)
        self.assertNotIn("RECOVERY_EXHAUSTED", self.supervisor)

    def test_supervisor_never_auto_administers_tunnel_resources(self) -> None:
        combined = self.supervisor + "\n" + self.installer
        for forbidden in (
            "admin tunnels create",
            "admin tunnels update",
            "admin tunnels delete",
            "OPENAI_ADMIN_KEY =",
        ):
            self.assertNotIn(forbidden, combined)

    def test_installer_uses_user_context_scheduled_task_and_no_elevation(self) -> None:
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn -User $identity", self.installer)
        self.assertIn("-LogonType Interactive", self.installer)
        self.assertIn("-RunLevel Limited", self.installer)
        self.assertIn("-MultipleInstances IgnoreNew", self.installer)
        self.assertIn("-RestartCount 3", self.installer)
        self.assertIn("Start-ScheduledTask -TaskName $TaskName", self.installer)
        self.assertNotIn("RunLevel Highest", self.installer)
        self.assertNotIn("LocalSystem", self.installer)


@unittest.skipUnless(shutil.which("pwsh") or shutil.which("pwsh.exe"), "PowerShell 7 unavailable")
class TunnelHealthPowerShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pwsh = shutil.which("pwsh") or shutil.which("pwsh.exe")

    def _classify(
        self,
        *,
        tunnel_processes: int = 1,
        semantic_processes: int = 1,
        healthz: bool = True,
        readyz: bool = True,
        poll_ok: bool = True,
        poll_age: float | None = 1,
        remote: str = "ready",
        conflict: bool = False,
    ) -> dict:
        age = "$null" if poll_age is None else str(poll_age)
        command = (
            f". '{HEALTH}'; "
            f"Get-TunnelEndToEndHealth -TunnelProcessCount {tunnel_processes} "
            f"-SemanticProcessCount {semantic_processes} "
            f"-HealthzOk ${str(healthz).lower()} -ReadyzOk ${str(readyz).lower()} "
            f"-ControlPlanePollOk ${str(poll_ok).lower()} "
            f"-ControlPlanePollAgeSeconds {age} -RemoteStatus '{remote}' "
            f"-Conflict ${str(conflict).lower()} | ConvertTo-Json -Compress"
        )
        completed = subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-Command", command],
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(completed.stdout)

    def test_healthy_is_fully_ready(self) -> None:
        state = self._classify()
        self.assertEqual(state["code"], "READY")
        self.assertEqual(state["recovery_action"], "none")
        self.assertTrue(state["runtime_ready"])
        self.assertTrue(state["mcp_ready"])
        self.assertTrue(state["tunnel_local_ready"])
        self.assertTrue(state["openai_control_ready"])

    def test_404_is_blocked_even_if_local_process_is_dead(self) -> None:
        state = self._classify(
            tunnel_processes=0,
            semantic_processes=0,
            healthz=False,
            readyz=False,
            poll_ok=False,
            poll_age=None,
            remote="resource_missing",
        )
        self.assertEqual(state["code"], "REMOTE_TUNNEL_RESOURCE_MISSING")
        self.assertEqual(state["recovery_action"], "blocked")
        self.assertFalse(state["recoverable"])

    def test_401_and_403_never_restart(self) -> None:
        for remote, expected in (
            ("unauthorized", "REMOTE_TUNNEL_UNAUTHORIZED"),
            ("forbidden", "REMOTE_TUNNEL_FORBIDDEN"),
        ):
            with self.subTest(remote=remote):
                state = self._classify(remote=remote)
                self.assertEqual(state["code"], expected)
                self.assertEqual(state["recovery_action"], "blocked")

    def test_local_process_failures_request_runtime_restart(self) -> None:
        cases = (
            (dict(tunnel_processes=0), "LOCAL_TUNNEL_NOT_RUNNING"),
            (dict(healthz=False), "LOCAL_TUNNEL_NOT_HEALTHY"),
            (dict(semantic_processes=0), "LOCAL_MCP_PROCESS_MISSING"),
            (dict(readyz=False), "LOCAL_MCP_UNAVAILABLE"),
        )
        for kwargs, expected in cases:
            with self.subTest(expected=expected):
                state = self._classify(**kwargs)
                self.assertEqual(state["code"], expected)
                self.assertEqual(state["recovery_action"], "restart_runtime")

    def test_stale_poll_requests_restart_but_transient_metadata_does_not(self) -> None:
        stale = self._classify(poll_age=121)
        self.assertEqual(stale["code"], "REMOTE_TUNNEL_DISCONNECTED")
        self.assertEqual(stale["recovery_action"], "restart_runtime")

        for remote, expected in (
            ("rate_limited", "REMOTE_METADATA_RATE_LIMITED"),
            ("service_unavailable", "REMOTE_METADATA_UNAVAILABLE"),
            ("unavailable", "REMOTE_METADATA_UNAVAILABLE"),
            ("unknown", "REMOTE_METADATA_UNKNOWN"),
        ):
            with self.subTest(remote=remote):
                state = self._classify(remote=remote)
                self.assertEqual(state["code"], expected)
                self.assertEqual(state["recovery_action"], "wait_and_probe")


@unittest.skipUnless(shutil.which("pwsh") or shutil.which("pwsh.exe"), "PowerShell 7 unavailable")
class SupervisorPowerShellTests(unittest.TestCase):
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

    def test_absent_owner_means_explicit_stopped_desired_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "local"
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

    def test_running_owner_and_healthy_direct_status_stays_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "local"
            state_dir = local / "ChatAgentPlatform" / "state"
            state_dir.mkdir(parents=True)
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
            self.assertEqual(state["desired_state"], "running")
            self.assertEqual(state["supervisor_state"], "healthy")
            self.assertEqual(state["health_code"], "READY")
            self.assertTrue(state["runtime_ready"])
            self.assertTrue(state["openai_control_ready"])
            self.assertEqual(state["chatgpt_route_status"], "not_checked")

    def test_remote_403_is_blocked_without_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            local = root / "local"
            state_dir = local / "ChatAgentPlatform" / "state"
            state_dir.mkdir(parents=True)
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
                    "openai_ready": False,
                    "health_code": "REMOTE_TUNNEL_FORBIDDEN",
                    "recovery_action": "blocked",
                    "tunnel_binding": "direct-stdio",
                    "remote_tunnel_status": "forbidden",
                    "control_plane_poll_fresh": True,
                    "settings": {"profile": "semantic"},
                },
            )
            state = self._reconcile(local, manager)
            self.assertEqual(state["supervisor_state"], "blocked")
            self.assertEqual(state["health_code"], "REMOTE_TUNNEL_FORBIDDEN")
            self.assertEqual(state["recovery_action"], "blocked")


if __name__ == "__main__":
    unittest.main()
