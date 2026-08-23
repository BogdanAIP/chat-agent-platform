from __future__ import annotations

from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
