from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transport-supervisor-network-qualification.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class TransportSupervisorNetworkQualificationContractTests(unittest.TestCase):
    def test_harness_is_observational_and_never_mutates_network_configuration(self):
        self.assertIn("NEVER disables adapters", SOURCE)
        for forbidden in (
            "Disable-NetAdapter",
            "Enable-NetAdapter",
            "New-NetFirewallRule",
            "Remove-NetFirewallRule",
            "netsh advfirewall",
            "rasdial",
        ):
            self.assertNotIn(forbidden, SOURCE)

    def test_harness_requires_manual_disconnect_and_reconnect_confirmation(self):
        self.assertIn("physically disconnect external network now", SOURCE)
        self.assertIn("After the computer is actually offline, press Enter here", SOURCE)
        self.assertIn("restore the external network now", SOURCE)
        self.assertIn("After connectivity is restored, press Enter here", SOURCE)
        self.assertIn("depends on a VPN or proxy", SOURCE)

    def test_offline_acceptance_requires_local_runtime_to_stay_ready_while_openai_is_unready(self):
        self.assertIn("[bool]$status.runtime_ready", SOURCE)
        self.assertIn("(-not [bool]$status.openai_ready)", SOURCE)
        self.assertIn("offline-detected", SOURCE)

    def test_offline_observation_still_rejects_any_pid_churn_or_recovery(self):
        self.assertIn("Direct tunnel process churned during transient network loss", SOURCE)
        self.assertIn("Supervisor process changed or disappeared during offline observation", SOURCE)
        self.assertIn("Supervisor performed runtime recovery during transient network loss", SOURCE)
        self.assertIn("$currentTunnels[0].ProcessId -ne $tunnelPid", SOURCE)
        self.assertIn("$currentSupervisors[0].ProcessId -ne $supervisorPid", SOURCE)
        self.assertIn("$r.total_recoveries -ne $recoveriesBefore", SOURCE)

    def test_reconnect_accepts_seamless_or_one_bounded_supervisor_recovery(self):
        self.assertIn("$recoveryDelta -lt 0 -or $recoveryDelta -gt 1", SOURCE)
        self.assertIn("$reconnectMode = if ($recoveryDelta -eq 0) { 'seamless' } else { 'bounded_recovery' }", SOURCE)
        self.assertIn("Tunnel PID changed without a committed supervisor recovery receipt", SOURCE)
        self.assertIn("Recovery count increased but tunnel PID did not change", SOURCE)
        self.assertIn("Bounded reconnect recovery did not end in healthy supervisor state", SOURCE)
        self.assertIn("Bounded reconnect recovery did not end in READY health", SOURCE)
        self.assertIn("Bounded reconnect recovery left a pending recovery action", SOURCE)
        self.assertIn("Bounded reconnect recovery left non-zero consecutive attempts", SOURCE)
        self.assertIn("Bounded reconnect recovery did not publish last_success_at", SOURCE)

    def test_reconnect_waits_for_coherent_process_and_receipt_pair(self):
        for marker in (
            "$receiptSettleDeadline = (Get-Date).AddSeconds(30)",
            "$coherentSeamless = (",
            "$coherentRecovery = (",
            "Post-reconnect process and recovery receipts did not settle into a coherent state",
        ):
            self.assertIn(marker, SOURCE)

    def test_reconnect_requires_same_supervisor_and_full_ready_state(self):
        self.assertIn("[bool]$status.openai_ready", SOURCE)
        self.assertIn("[int]$currentSupervisors[0].ProcessId -eq $supervisorPid", SOURCE)
        self.assertIn("[int]$candidateSupervisor.supervisor_pid -eq $supervisorPid", SOURCE)
        self.assertIn("Healthy state did not return automatically", SOURCE)

    def test_reconnect_failure_preserves_diagnostic_samples(self):
        for marker in (
            "$reconnectSamples = @()",
            "reconnect-samples.json",
            "remote_tunnel_status = if",
            "control_plane_poll_fresh = if",
            "recovery_total = if ($null -ne $r)",
            "Last sample: runtime_ready=",
        ):
            self.assertIn(marker, SOURCE)

    def test_summary_records_reconnect_mode_and_recovery_delta(self):
        self.assertIn("schema_version = 2", SOURCE)
        self.assertIn("reconnect_mode = $reconnectMode", SOURCE)
        self.assertIn("recovery_count_delta = $recoveryDelta", SOURCE)
        self.assertIn("OLD_TUNNEL_PID", SOURCE)
        self.assertIn("NEW_TUNNEL_PID", SOURCE)
        self.assertIn("RECONNECT_MODE", SOURCE)
        self.assertIn("RECOVERY_COUNT_DELTA", SOURCE)

    def test_success_requires_post_reconnect_heartbeat_and_machine_readable_summary(self):
        self.assertIn("Supervisor heartbeat did not advance after network reconnect", SOURCE)
        self.assertIn("TRANSPORT_SUPERVISOR_NETWORK_QUALIFICATION_RESULT", SOURCE)
        self.assertIn("SUPERVISOR_PID_STABLE", SOURCE)
        self.assertIn("RECOVERY_TOTAL_BEFORE", SOURCE)
        self.assertIn("RECOVERY_TOTAL_AFTER", SOURCE)
        self.assertIn("SUPERVISOR_HEARTBEAT_VERIFIED", SOURCE)
        self.assertIn("Save-JsonEvidence -Name 'summary'", SOURCE)

    def test_failure_captures_receipts_and_log_and_restores_pretest_desired_state(self):
        self.assertIn("supervisor-failure.json", SOURCE)
        self.assertIn("recovery-failure.json", SOURCE)
        self.assertIn("supervisor-log-tail.txt", SOURCE)
        self.assertIn("& $Installer -Uninstall", SOURCE)
        self.assertIn("if ($desiredStateBefore -eq 'running')", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Start", SOURCE)


if __name__ == "__main__":
    unittest.main()
