from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transport-supervisor-sleep-resume-qualification.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class TransportSupervisorSleepResumeQualificationContractTests(unittest.TestCase):
    def test_harness_never_initiates_or_simulates_power_transition(self):
        self.assertIn("NEVER initiates sleep, hibernate, shutdown, reboot, or changes power settings", SOURCE)
        for forbidden in (
            "SetSuspendState",
            "rundll32.exe powrprof.dll",
            "shutdown.exe",
            "Restart-Computer",
            "Stop-Computer",
            "powercfg.exe /hibernate",
            "powercfg.exe -hibernate",
        ):
            self.assertNotIn(forbidden, SOURCE)

    def test_harness_requires_manual_real_windows_sleep(self):
        self.assertIn("put Windows into REAL Sleep now", SOURCE)
        self.assertIn("Use Start -> Power -> Sleep", SOURCE)
        self.assertIn("After Windows and the required external network/VPN/proxy path have resumed, press Enter here", SOURCE)
        self.assertIn("Do NOT close this PowerShell window", SOURCE)

    def test_harness_requires_external_route_restoration_before_resume_timer(self):
        self.assertIn("restore normal network connectivity and any required VPN/proxy path before pressing Enter", SOURCE)
        self.assertIn("Confirm the external path is usable; do NOT manually restart Chat Agent Platform", SOURCE)
        self.assertIn("required external network/VPN/proxy path have resumed", SOURCE)

    def test_harness_preserves_power_capability_and_event_evidence(self):
        self.assertIn("powercfg.exe", SOURCE)
        self.assertIn("powercfg-a.txt", SOURCE)
        self.assertIn("Microsoft-Windows-Kernel-Power", SOURCE)
        self.assertIn("Microsoft-Windows-Power-Troubleshooter", SOURCE)
        for event_id in (42, 107, 506, 507):
            self.assertIn(str(event_id), SOURCE)
        self.assertIn("sleep_evidence_seconds", SOURCE)
        self.assertIn("A real Windows sleep/resume transition was not verified", SOURCE)

    def test_harness_supports_classic_sleep_and_modern_standby_event_pairs(self):
        self.assertIn("$mode in @('classic', 'modern-standby')", SOURCE)
        self.assertIn("$_.event_id -eq 42", SOURCE)
        self.assertIn("$_.event_id -eq 107", SOURCE)
        self.assertIn("$_.event_id -eq 506", SOURCE)
        self.assertIn("$_.event_id -eq 507", SOURCE)
        self.assertIn("$_.event_id -eq 1", SOURCE)

    def test_supervisor_pid_must_survive_ordinary_sleep_resume(self):
        self.assertIn("Expected exactly one supervisor after resume", SOURCE)
        self.assertIn("Supervisor PID changed across ordinary Windows sleep/resume", SOURCE)
        self.assertIn("[int]$currentSupervisors[0].ProcessId -eq $supervisorPid", SOURCE)

    def test_desired_running_owner_must_survive_resume(self):
        self.assertIn("owner-before-sleep", SOURCE)
        self.assertIn("owner-after-resume", SOURCE)
        self.assertIn("Desired running owner state disappeared across sleep/resume", SOURCE)
        self.assertIn("Manager controller ownership changed across sleep/resume", SOURCE)

    def test_tunnel_may_resume_seamlessly_or_with_one_bounded_recovery(self):
        self.assertIn("$candidateDelta -lt 0 -or $candidateDelta -gt 1", SOURCE)
        self.assertIn("$coherentSeamless", SOURCE)
        self.assertIn("$coherentRecovery", SOURCE)
        self.assertIn("$resumeMode = if ($recoveryDelta -eq 0) { 'seamless' } else { 'bounded_recovery' }", SOURCE)
        self.assertIn("Tunnel PID changed after resume without a committed supervisor recovery receipt", SOURCE)
        self.assertIn("Recovery count increased after resume but tunnel PID did not change", SOURCE)

    def test_resume_requires_full_runtime_and_openai_readiness(self):
        self.assertIn("[bool]$status.runtime_ready", SOURCE)
        self.assertIn("[bool]$status.openai_ready", SOURCE)
        self.assertIn("Healthy state did not return automatically", SOURCE)
        self.assertIn("resume-samples.json", SOURCE)

    def test_success_requires_coherent_receipts_and_later_supervisor_heartbeat(self):
        self.assertIn("Post-resume process and recovery receipts did not settle into a coherent state", SOURCE)
        self.assertIn("Supervisor heartbeat did not advance after Windows resume", SOURCE)
        self.assertIn("supervisor-after-resume", SOURCE)
        self.assertIn("recovery-after-resume", SOURCE)
        self.assertIn("TRANSPORT_SUPERVISOR_SLEEP_RESUME_QUALIFICATION_RESULT", SOURCE)
        self.assertIn("SUPERVISOR_HEARTBEAT_VERIFIED", SOURCE)
        self.assertIn("Save-JsonEvidence -Name 'summary'", SOURCE)

    def test_failure_preserves_diagnostics_and_restores_pretest_desired_state(self):
        self.assertIn("supervisor-failure.json", SOURCE)
        self.assertIn("recovery-failure.json", SOURCE)
        self.assertIn("supervisor-log-tail.txt", SOURCE)
        self.assertIn("power-events-failure.json", SOURCE)
        self.assertIn("& $Installer -Uninstall", SOURCE)
        self.assertIn("if ($desiredStateBefore -eq 'running')", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Start", SOURCE)


if __name__ == "__main__":
    unittest.main()
