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

    def test_recovery_timestamps_round_trip_as_canonical_utc(self):
        for marker in (
            "function ConvertTo-UtcIsoString",
            "[DateTimeKind]::Unspecified",
            "[datetime]::SpecifyKind($date, [DateTimeKind]::Utc)",
            "next_retry_at = ConvertTo-UtcIsoString $state.next_retry_at",
            "last_attempt_at = ConvertTo-UtcIsoString $state.last_attempt_at",
            "last_success_at = ConvertTo-UtcIsoString $state.last_success_at",
            "last_success_at = ConvertTo-UtcIsoString $LastSuccessAt",
        ):
            self.assertIn(marker, SUPERVISOR)

    def test_atomic_state_publication_retries_reader_sharing_races(self):
        atomic_start = SUPERVISOR.index("function Write-AtomicJson")
        atomic_end = SUPERVISOR.index("function Write-SupervisorLog", atomic_start)
        atomic_block = SUPERVISOR[atomic_start:atomic_end]
        self.assertIn("for ($attempt = 1; $attempt -le 20; $attempt++)", atomic_block)
        self.assertIn("Start-Sleep -Milliseconds 50", atomic_block)
        self.assertIn("if ($attempt -eq 20) { throw }", atomic_block)

    def test_runtime_failure_is_separate_from_success_receipt_publication(self):
        reconcile_start = SUPERVISOR.index("$attemptNumber = [int]$recovery.consecutive_attempts + 1")
        reconcile_end = SUPERVISOR.index("function Get-SupervisorStatus", reconcile_start)
        recovery_block = SUPERVISOR[reconcile_start:reconcile_end]

        runtime_catch = recovery_block.index("phase=runtime")
        publication_marker = recovery_block.index(
            "Runtime recovery is now complete. Publication errors must not be turned"
        )
        success_save = recovery_block.index("-LastSuccessAt $successAt")
        publication_failure = recovery_block.index("recovery publication failed")

        self.assertLess(runtime_catch, publication_marker)
        self.assertLess(publication_marker, success_save)
        self.assertLess(success_save, publication_failure)

    def test_success_publication_computes_supervisor_state_before_binding_argument(self):
        reconcile_start = SUPERVISOR.index("# Runtime recovery is now complete.")
        reconcile_end = SUPERVISOR.index("function Get-SupervisorStatus", reconcile_start)
        publication_block = SUPERVISOR[reconcile_start:reconcile_end]

        state_assignment = (
            "$postSupervisorState = if ([string]$postHealth.recovery_action -eq 'none') "
            "{ 'healthy' } else { 'degraded' }"
        )
        self.assertIn(state_assignment, publication_block)
        self.assertIn("-SupervisorState $postSupervisorState", publication_block)
        self.assertNotIn("-SupervisorState (if ", publication_block)

    def test_physical_gate_uses_type_safe_utc_timestamp_comparison(self):
        self.assertIn("function ConvertTo-UtcDateTime", QUALIFICATION)
        self.assertIn(
            "$observedAt = ConvertTo-UtcDateTime $candidateSupervisorReceipt.observed_at",
            QUALIFICATION,
        )
        self.assertIn(
            "$lastSuccessAt = ConvertTo-UtcDateTime $candidateRecoveryReceipt.last_success_at",
            QUALIFICATION,
        )
        self.assertIn(
            "$firstObservedAt = ConvertTo-UtcDateTime $supervisorReceipt.observed_at",
            QUALIFICATION,
        )
        self.assertIn(
            "$heartbeatObservedAt = ConvertTo-UtcDateTime $heartbeat.observed_at",
            QUALIFICATION,
        )
        self.assertNotIn(
            "[datetime]::Parse([string]$candidateRecoveryReceipt.last_success_at)",
            QUALIFICATION,
        )

    def test_physical_gate_isolates_old_recovery_state_and_primes_baseline(self):
        for marker in (
            "preexisting-supervisor.json",
            "preexisting-recovery.json",
            "Supervisor did not publish a clean healthy baseline before fault injection.",
            "supervisor-before-fault.json",
            "recovery-before-fault.json",
            "$recoveryCountBeforeFault = [int]$recoveryBaselineReceipt.total_recoveries",
            "[int]$candidateRecoveryReceipt.total_recoveries -gt $recoveryCountBeforeFault",
            "RECOVERY_RECEIPT_TOTAL_BEFORE_FAULT",
        ):
            self.assertIn(marker, QUALIFICATION)

    def test_failure_captures_live_receipts_and_log_before_uninstall(self):
        for marker in (
            "recovery-failure.json",
            "supervisor-failure.json",
            "supervisor-log-tail.txt",
            "Get-Content -LiteralPath $SupervisorLogFile -Tail 200",
        ):
            self.assertIn(marker, QUALIFICATION)

        evidence_index = QUALIFICATION.index("Capture live supervisor evidence before uninstall")
        uninstall_index = QUALIFICATION.index("& $Installer -Uninstall")
        self.assertLess(evidence_index, uninstall_index)

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
