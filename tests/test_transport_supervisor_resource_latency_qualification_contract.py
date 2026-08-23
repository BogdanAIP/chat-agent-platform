from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transport-supervisor-resource-latency-qualification.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class TransportSupervisorResourceLatencyQualificationContractTests(unittest.TestCase):
    def test_gate_is_windows_only_and_has_bounded_sampling_parameters(self):
        self.assertIn("if (-not $IsWindows)", SOURCE)
        self.assertIn("[int]$IdleSampleSeconds = 60", SOURCE)
        self.assertIn("[int]$RecoveryTimeoutSeconds = 120", SOURCE)

    def test_process_sampler_does_not_shadow_read_only_pid_automatic_variable(self):
        self.assertNotRegex(SOURCE, re.compile(r"(?i)\[int\]\$Pid\b"))
        self.assertIn("[int]$ProcessId", SOURCE)
        self.assertIn("Get-Process -Id $ProcessId", SOURCE)
        self.assertIn("-ProcessId $supervisorPid", SOURCE)
        self.assertIn("-ProcessId $tunnelPid", SOURCE)

    def test_idle_phase_is_observational_and_requires_stable_process_ids(self):
        idle_block = SOURCE.split("===== TRANSPORT SUPERVISOR: IDLE RESOURCE SAMPLE =====", 1)[1].split(
            "===== TRANSPORT SUPERVISOR: RECOVERY LATENCY SAMPLE =====", 1
        )[0]
        self.assertIn("Start-Sleep -Seconds $IdleSampleSeconds", idle_block)
        self.assertIn("Supervisor PID changed during the idle measurement window", idle_block)
        self.assertIn("Tunnel PID changed during the idle measurement window", idle_block)
        self.assertNotIn("Stop-Process", idle_block)
        self.assertNotIn("Invoke-ManagerMutation", idle_block)
        self.assertNotIn("Start-ScheduledTask", idle_block)

    def test_idle_metrics_include_cpu_and_memory(self):
        for marker in (
            "cpu_seconds_delta",
            "average_cpu_single_core_percent",
            "average_cpu_machine_percent",
            "working_set_bytes_after",
            "private_memory_bytes_after",
            "idle-resources.csv",
        ):
            self.assertIn(marker, SOURCE)

    def test_fault_injection_is_delegated_to_existing_hard_kill_qualification(self):
        self.assertIn("transport-supervisor-qualification.ps1", SOURCE)
        self.assertIn(
            "& $HardKillQualification -RecoveryTimeoutSeconds $RecoveryTimeoutSeconds -OutputRoot $HardKillRoot",
            SOURCE,
        )
        self.assertNotIn("Stop-Process -Id", SOURCE)

    def test_latency_comes_from_committed_recovery_receipt(self):
        self.assertIn("recovery-after-recovery.json", SOURCE)
        self.assertIn("$recovery.last_attempt_at", SOURCE)
        self.assertIn("$recovery.last_success_at", SOURCE)
        self.assertIn("recovery_transaction_latency_ms", SOURCE)
        self.assertIn("Recovery receipt success timestamp predates attempt timestamp", SOURCE)

    def test_success_requires_hard_kill_pass_and_machine_readable_summary(self):
        self.assertIn("if ([string]$hardKillSummary.result -ne 'PASSED')", SOURCE)
        self.assertIn("TRANSPORT_SUPERVISOR_RESOURCE_LATENCY_QUALIFICATION_RESULT", SOURCE)
        self.assertIn("$summary | ConvertTo-Json", SOURCE)
        self.assertIn("RESULT_DIR", SOURCE)


if __name__ == "__main__":
    unittest.main()
