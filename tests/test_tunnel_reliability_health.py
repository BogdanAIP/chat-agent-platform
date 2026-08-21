from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "tunnel-reliability-health.ps1"
SOURCE = HELPER.read_text(encoding="utf-8")


class TunnelReliabilitySourceContractTests(unittest.TestCase):
    def test_required_failure_codes_are_explicit(self):
        for code in (
            "REMOTE_TUNNEL_RESOURCE_MISSING",
            "REMOTE_TUNNEL_UNAUTHORIZED",
            "REMOTE_TUNNEL_FORBIDDEN",
            "REMOTE_TUNNEL_DISCONNECTED",
            "LOCAL_MCP_UNAVAILABLE",
            "LOCAL_TUNNEL_NOT_READY",
            "LOCAL_TUNNEL_NOT_RUNNING",
            "LOCAL_RUNTIME_CONFLICT",
        ):
            self.assertIn(code, SOURCE)

    def test_resource_missing_is_classified_before_local_process_failure(self):
        self.assertLess(
            SOURCE.index("$RemoteStatus -eq 'resource_missing'"),
            SOURCE.index("$TunnelProcessCount -eq 0"),
        )

    def test_only_recoverable_transport_or_local_failures_set_recoverable(self):
        resource_block = SOURCE[
            SOURCE.index("$RemoteStatus -eq 'resource_missing'") :
            SOURCE.index("elseif ($Conflict")
        ]
        self.assertNotIn("$recoverable = $true", resource_block)
        self.assertIn("REMOTE_TUNNEL_DISCONNECTED", SOURCE)
        self.assertIn("$recoverable = $true", SOURCE)


@unittest.skipUnless(shutil.which("pwsh") or shutil.which("pwsh.exe"), "PowerShell 7 unavailable")
class TunnelReliabilityPowerShellTests(unittest.TestCase):
    def _classify(
        self,
        *,
        processes: int = 1,
        healthz: bool = True,
        readyz: bool = True,
        poll_ok: bool = True,
        poll_age: float | None = 1,
        remote: str = "ready",
        conflict: bool = False,
    ) -> dict:
        pwsh = shutil.which("pwsh") or shutil.which("pwsh.exe")
        age = "$null" if poll_age is None else str(poll_age)
        command = (
            f". '{HELPER}'; "
            f"Get-TunnelEndToEndHealth -TunnelProcessCount {processes} "
            f"-HealthzOk ${str(healthz).lower()} -ReadyzOk ${str(readyz).lower()} "
            f"-ControlPlanePollOk ${str(poll_ok).lower()} "
            f"-ControlPlanePollAgeSeconds {age} -RemoteStatus '{remote}' "
            f"-Conflict ${str(conflict).lower()} | ConvertTo-Json -Compress"
        )
        completed = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-Command", command],
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(completed.stdout)

    def test_healthy_components_are_distinct_and_green(self):
        state = self._classify()
        self.assertEqual(state["code"], "READY")
        self.assertTrue(state["mcp_ready"])
        self.assertTrue(state["tunnel_local_ready"])
        self.assertTrue(state["openai_ready"])
        self.assertFalse(state["recoverable"])

    def test_404_is_nonrecoverable_even_when_local_process_is_gone(self):
        state = self._classify(processes=0, healthz=False, readyz=False, poll_ok=False, poll_age=None, remote="resource_missing")
        self.assertEqual(state["code"], "REMOTE_TUNNEL_RESOURCE_MISSING")
        self.assertFalse(state["recoverable"])

    def test_401_and_403_are_not_restart_candidates(self):
        for remote, expected in (
            ("unauthorized", "REMOTE_TUNNEL_UNAUTHORIZED"),
            ("forbidden", "REMOTE_TUNNEL_FORBIDDEN"),
        ):
            with self.subTest(remote=remote):
                state = self._classify(remote=remote)
                self.assertEqual(state["code"], expected)
                self.assertFalse(state["recoverable"])

    def test_local_mcp_failure_is_recoverable(self):
        state = self._classify(readyz=False)
        self.assertEqual(state["code"], "LOCAL_MCP_UNAVAILABLE")
        self.assertTrue(state["recoverable"])
        self.assertTrue(state["tunnel_local_ready"])
        self.assertFalse(state["mcp_ready"])

    def test_stale_poll_is_remote_disconnected(self):
        state = self._classify(poll_age=121)
        self.assertEqual(state["code"], "REMOTE_TUNNEL_DISCONNECTED")
        self.assertTrue(state["recoverable"])
        self.assertTrue(state["mcp_ready"])
        self.assertTrue(state["tunnel_local_ready"])
        self.assertFalse(state["openai_ready"])


if __name__ == "__main__":
    unittest.main()
