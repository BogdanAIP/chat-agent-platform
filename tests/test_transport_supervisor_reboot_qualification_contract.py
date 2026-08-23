from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transport-supervisor-reboot-qualification.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class TransportSupervisorRebootQualificationContractTests(unittest.TestCase):
    def test_harness_never_initiates_or_simulates_reboot(self):
        self.assertIn("NEVER initiates reboot, shutdown, sleep, hibernate, or changes power settings", SOURCE)
        for forbidden in (
            "Restart-Computer",
            "Stop-Computer",
            "shutdown.exe",
            "SetSuspendState",
            "rundll32.exe powrprof.dll",
        ):
            self.assertNotIn(forbidden, SOURCE)

    def test_harness_is_explicitly_two_phase(self):
        self.assertIn("[ValidateSet('Prepare', 'Verify')]", SOURCE)
        self.assertIn("PHYSICAL REBOOT / LOGON QUALIFICATION — PREPARE", SOURCE)
        self.assertIn("PHYSICAL REBOOT / LOGON QUALIFICATION — VERIFY", SOURCE)
        self.assertIn("pending.json", SOURCE)
        self.assertIn("prepare.json", SOURCE)

    def test_prepare_pins_exact_source_and_persists_cross_reboot_receipt(self):
        self.assertIn("git -C $RepoRoot rev-parse HEAD", SOURCE)
        self.assertIn("qualification_script_sha256", SOURCE)
        self.assertIn("Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256", SOURCE)
        self.assertIn("boot_time_before", SOURCE)
        self.assertIn("owner-before-reboot", SOURCE)
        self.assertIn("task-before-reboot", SOURCE)
        self.assertIn("recovery-before-reboot", SOURCE)

    def test_prepare_requires_running_semantic_baseline_and_logon_task(self):
        self.assertIn("Reboot qualification requires semantic/direct profile", SOURCE)
        self.assertIn("Baseline did not become fully ready before reboot qualification", SOURCE)
        self.assertIn("Reboot qualification requires desired running owner state before reboot", SOURCE)
        self.assertIn("Expected exactly one supervisor before reboot", SOURCE)
        self.assertIn("Expected exactly one direct tunnel before reboot", SOURCE)
        self.assertIn("MSFT_TaskLogonTrigger", SOURCE)

    def test_task_identity_contract_canonicalizes_principal_and_trigger_by_sid(self):
        self.assertIn("function Convert-AccountIdentityToSid", SOURCE)
        self.assertIn("WindowsIdentity]::GetCurrent().User.Value", SOURCE)
        self.assertIn("principal_sid", SOURCE)
        self.assertIn("current_identity_sid", SOURCE)
        self.assertIn("logon_trigger_sids", SOURCE)
        self.assertIn("principal SID does not match the current Windows identity SID", SOURCE)
        self.assertIn("logon trigger SID does not target the current Windows identity SID", SOURCE)
        self.assertNotIn("[string]$Evidence.principal_user_id -ne [string]$Evidence.current_identity", SOURCE)
        self.assertNotIn("@($Evidence.logon_trigger_users) -notcontains [string]$Evidence.current_identity", SOURCE)

    def test_prepare_failure_is_fail_safe_and_restores_pretest_state(self):
        self.assertIn("phase = 'prepare'", SOURCE)
        self.assertIn("& $Installer -Uninstall", SOURCE)
        self.assertIn("Remove-Item -LiteralPath $PendingFile", SOURCE)
        self.assertIn("if ($desiredStateBefore -eq 'running')", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Start", SOURCE)

    def test_prepare_requires_receipt_from_current_supervisor_pid(self):
        self.assertIn("[int]$candidateSupervisor.supervisor_pid -eq $supervisorPid", SOURCE)
        self.assertIn("current clean baseline reboot qualification receipt", SOURCE)

    def test_operator_must_physically_reboot_and_restore_external_route(self):
        self.assertIn("ACTION REQUIRED: manually restart Windows now", SOURCE)
        self.assertIn("restore any required external VPN/proxy/network path", SOURCE)
        self.assertIn("Do NOT manually start/restart Chat Agent Platform", SOURCE)
        self.assertIn("same exact tested source", SOURCE)

    def test_verify_proves_new_boot_and_surviving_desired_state(self):
        self.assertIn("A new Windows boot was not proven", SOURCE)
        self.assertIn("Windows boot time is not later than the qualification prepare timestamp", SOURCE)
        self.assertIn("Desired running owner state disappeared across Windows reboot", SOURCE)
        self.assertIn("Manager controller ownership changed across reboot/logon", SOURCE)
        self.assertIn("Manager owner receipt was recreated instead of surviving reboot", SOURCE)
        self.assertIn("reboot_verified = $true", SOURCE)

    def test_verify_requires_same_identity_sid_and_logon_trigger_to_have_run_after_boot(self):
        self.assertIn("Windows identity SID changed across reboot/logon qualification", SOURCE)
        self.assertIn("Scheduled Task principal SID changed across reboot/logon qualification", SOURCE)
        self.assertIn("Supervisor Scheduled Task has no post-logon LastRunTime", SOURCE)
        self.assertIn("Supervisor Scheduled Task LastRunTime predates the verified reboot", SOURCE)
        self.assertIn("task_last_run_after_boot", SOURCE)
        self.assertIn("task_logon_trigger_verified", SOURCE)

    def test_verify_requires_supervisor_to_exist_before_observational_verify(self):
        self.assertIn("VERIFY is observational: it does not start or restart Chat Agent Platform", SOURCE)
        self.assertIn("Expected exactly one supervisor already running after logon before VERIFY mutations", SOURCE)
        self.assertIn("Supervisor was not already running when post-logon VERIFY began", SOURCE)
        self.assertIn("supervisor_created_after_boot", SOURCE)

    def test_verify_requires_post_boot_tunnel_and_full_readiness(self):
        self.assertIn("Post-reboot tunnel process creation time predates the verified reboot", SOURCE)
        self.assertIn("Healthy state did not return automatically", SOURCE)
        self.assertIn("runtime_ready_after_logon", SOURCE)
        self.assertIn("openai_ready_after_logon", SOURCE)
        self.assertIn("post-logon-samples.json", SOURCE)

    def test_reboot_recovery_is_bounded_and_receipted(self):
        self.assertIn("$recoveryDelta -lt 0 -or $recoveryDelta -gt 1", SOURCE)
        self.assertIn("consecutive_attempts", SOURCE)
        self.assertIn("recovery-after-logon", SOURCE)
        self.assertIn("RECOVERY_COUNT_DELTA", SOURCE)

    def test_success_requires_later_supervisor_heartbeat(self):
        self.assertIn("Supervisor heartbeat did not advance after reboot/logon recovery", SOURCE)
        self.assertIn("SUPERVISOR_HEARTBEAT_VERIFIED", SOURCE)
        self.assertIn("TRANSPORT_SUPERVISOR_REBOOT_LOGON_QUALIFICATION_RESULT", SOURCE)
        self.assertIn("Save-JsonEvidence -Directory $RunDir -Name 'summary'", SOURCE)

    def test_failure_preserves_cross_reboot_diagnostics(self):
        self.assertIn("supervisor-failure.json", SOURCE)
        self.assertIn("recovery-failure.json", SOURCE)
        self.assertIn("supervisor-log-tail.txt", SOURCE)
        self.assertIn("task-failure", SOURCE)


if __name__ == "__main__":
    unittest.main()
