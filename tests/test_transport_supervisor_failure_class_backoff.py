from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "scripts" / "chat-platform-supervisor.ps1"


class TransportSupervisorFailureClassBackoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SUPERVISOR.read_text(encoding="utf-8")

    def test_local_restart_preempts_prior_wait_and_probe_backoff(self) -> None:
        block = self.source[
            self.source.index("function Test-RecoveryDue") :
            self.source.index("function Get-NextRecoveryDelaySeconds")
        ]
        self.assertIn("[Parameter(Mandatory)] [string]$CurrentAction", block)
        self.assertIn("$CurrentAction -eq 'restart_runtime'", block)
        self.assertIn("[string]$RecoveryState.last_action -eq 'wait_and_probe'", block)
        self.assertIn("return $true", block)

    def test_restart_backoff_still_uses_existing_retry_deadline(self) -> None:
        block = self.source[
            self.source.index("function Test-RecoveryDue") :
            self.source.index("function Get-NextRecoveryDelaySeconds")
        ]
        self.assertIn("$RecoveryState.next_retry_at", block)
        self.assertIn("[datetime]::Parse", block)
        self.assertNotIn("last_action -eq 'restart_runtime'", block)

    def test_reconcile_passes_current_recovery_action_to_due_policy(self) -> None:
        self.assertIn(
            "Test-RecoveryDue -RecoveryState $recovery -CurrentAction ([string]$health.recovery_action)",
            self.source,
        )


@unittest.skipUnless(shutil.which("pwsh") or shutil.which("pwsh.exe"), "PowerShell 7 unavailable")
class TransportSupervisorFailureClassBackoffPowerShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pwsh = shutil.which("pwsh") or shutil.which("pwsh.exe")

    def _invoke_policy(self, *, last_action: str, current_action: str) -> bool:
        source = str(SUPERVISOR).replace("'", "''")
        command = f"""
$raw = Get-Content -LiteralPath '{source}' -Raw
$start = $raw.IndexOf('function Test-RecoveryDue')
$end = $raw.IndexOf('function Get-NextRecoveryDelaySeconds', $start)
$block = $raw.Substring($start, $end - $start)
Invoke-Expression $block
$state = [pscustomobject]@{{
    next_retry_at = (Get-Date).ToUniversalTime().AddMinutes(5).ToString('o')
    last_action = '{last_action}'
}}
$result = Test-RecoveryDue -RecoveryState $state -CurrentAction '{current_action}'
if ($result) {{ 'true' }} else {{ 'false' }}
"""
        completed = subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-Command", command],
            check=True,
            text=True,
            capture_output=True,
        )
        return completed.stdout.strip().lower() == "true"

    def test_future_wait_probe_deadline_is_preempted_by_local_restart(self) -> None:
        self.assertTrue(
            self._invoke_policy(last_action="wait_and_probe", current_action="restart_runtime")
        )

    def test_future_restart_deadline_is_not_preempted_by_another_restart(self) -> None:
        self.assertFalse(
            self._invoke_policy(last_action="restart_runtime", current_action="restart_runtime")
        )


if __name__ == "__main__":
    unittest.main()
