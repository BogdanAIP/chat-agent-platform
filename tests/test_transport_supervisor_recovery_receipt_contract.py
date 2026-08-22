from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = (ROOT / "scripts" / "chat-platform-supervisor.ps1").read_text(encoding="utf-8")
QUALIFICATION = (ROOT / "scripts" / "transport-supervisor-qualification.ps1").read_text(encoding="utf-8")


class TransportSupervisorRecoveryReceiptContractTests(unittest.TestCase):
    def test_supervisor_controller_mutations_do_not_capture_inheritable_pipes(self):
        self.assertIn("[bool]$CaptureOutput = $true", SUPERVISOR)
        self.assertIn("$info.RedirectStandardOutput = $CaptureOutput", SUPERVISOR)
        self.assertIn("$info.RedirectStandardError = $CaptureOutput", SUPERVISOR)

        status_start = SUPERVISOR.index("function Get-ManagerStatus")
        status_end = SUPERVISOR.index("function Get-ManagerOwner", status_start)
        status_block = SUPERVISOR[status_start:status_end]
        self.assertIn("-CaptureOutput $true", status_block)

        mutation_start = SUPERVISOR.index("function Invoke-OwnedDirectControllerAction")
        mutation_end = SUPERVISOR.index("function Invoke-DirectRuntimeRecovery", mutation_start)
        mutation_block = SUPERVISOR[mutation_start:mutation_end]
        self.assertIn("-CaptureOutput $false", mutation_block)

    def test_physical_gate_requires_post_fault_receipts_and_heartbeat(self):
        for marker in (
            "$faultInjectedAt = (Get-Date).ToUniversalTime()",
            "Supervisor did not publish a verified post-recovery receipt.",
            "Supervisor heartbeat did not advance after recovery.",
            "SUPERVISOR_RECEIPT_VERIFIED",
            "SUPERVISOR_HEARTBEAT_VERIFIED",
            "RECOVERY_RECEIPT_TOTAL_RECOVERIES",
            "supervisor_receipt_verified",
            "supervisor_heartbeat_verified",
            "recovery_receipt_total_recoveries",
            "$lastSuccessAt -ge $faultInjectedAt",
        ):
            self.assertIn(marker, QUALIFICATION)

        receipt_index = QUALIFICATION.index(
            "Supervisor did not publish a verified post-recovery receipt."
        )
        summary_index = QUALIFICATION.index("$summary = [ordered]@{")
        self.assertLess(receipt_index, summary_index)

    def test_gate_still_requires_pid_change_same_supervisor_and_runtime_ready(self):
        self.assertIn("ProcessId -ne $oldTunnelPid", QUALIFICATION)
        self.assertIn("ProcessId -eq $oldSupervisorPid", QUALIFICATION)
        self.assertIn("[bool]$status.runtime_ready", QUALIFICATION)


if __name__ == "__main__":
    unittest.main()
