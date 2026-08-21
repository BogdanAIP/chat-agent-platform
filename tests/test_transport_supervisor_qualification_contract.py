from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transport-supervisor-qualification.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class TransportSupervisorQualificationContractTests(unittest.TestCase):
    def test_qualification_is_windows_bounded_and_uses_owned_process_matching(self):
        self.assertIn("supports Windows only", SOURCE)
        self.assertIn("Get-DirectTunnelProcesses", SOURCE)
        self.assertIn("Get-ExactSupervisorProcesses", SOURCE)
        self.assertIn("semantic-direct-health.url", SOURCE)
        self.assertIn("tunnel-client.exe", SOURCE)

    def test_manager_calls_are_time_bounded_and_kill_only_the_test_process_tree_on_timeout(self):
        self.assertIn("function Invoke-BoundedManagerProcess", SOURCE)
        self.assertIn("WaitForExit($timeoutMilliseconds)", SOURCE)
        self.assertIn("$process.Kill($true)", SOURCE)
        self.assertIn("Manager $Action timed out after $TimeoutSeconds seconds", SOURCE)
        self.assertIn("-Action Status -TimeoutSeconds 30", SOURCE)
        self.assertIn("if ($Action -eq 'Start') { 150 } else { 60 }", SOURCE)

    def test_manager_mutations_do_not_wait_on_inheritable_redirected_pipes(self):
        self.assertIn("$captureOutput = ($Action -eq 'Status')", SOURCE)
        self.assertIn("$startInfo.RedirectStandardOutput = $captureOutput", SOURCE)
        self.assertIn("$startInfo.RedirectStandardError = $captureOutput", SOURCE)
        self.assertIn("$stdoutTask = if ($captureOutput)", SOURCE)
        self.assertIn("$stderrTask = if ($captureOutput)", SOURCE)
        self.assertIn("stdout = if ($captureOutput)", SOURCE)
        self.assertIn("stderr = if ($captureOutput)", SOURCE)

    def test_fault_injection_kills_only_the_resolved_owned_tunnel_pid(self):
        self.assertIn("Stop-Process -Id $oldTunnelPid -Force -ErrorAction Stop", SOURCE)
        self.assertNotIn("Stop-Process -Name", SOURCE)
        self.assertNotIn("taskkill", SOURCE.lower())

    def test_baseline_is_prepared_before_supervisor_is_started(self):
        self.assertIn("& $Installer -NoStart", SOURCE)
        self.assertIn("Start-QualificationSupervisor", SOURCE)
        install_index = SOURCE.index("& $Installer -NoStart")
        reset_index = SOURCE.index("Invoke-ManagerMutation -Action Stop", install_index)
        start_supervisor_index = SOURCE.index("Start-QualificationSupervisor", reset_index)
        fault_index = SOURCE.index("Stop-Process -Id $oldTunnelPid", start_supervisor_index)
        self.assertLess(install_index, reset_index)
        self.assertLess(reset_index, start_supervisor_index)
        self.assertLess(start_supervisor_index, fault_index)
        self.assertIn("unexpectedly left a supervisor process running", SOURCE)

    def test_powershell_installer_invocation_does_not_depend_on_lastexitcode(self):
        self.assertIn("& $Installer -NoStart", SOURCE)
        self.assertIn("& $Installer -Uninstall", SOURCE)
        self.assertNotIn("$LASTEXITCODE", SOURCE)

    def test_acceptance_requires_new_tunnel_pid_same_supervisor_and_ready_runtime(self):
        for marker in (
            "TRANSPORT_SUPERVISOR_QUALIFICATION_RESULT",
            "TUNNEL_PID_CHANGED",
            "SUPERVISOR_PID_STABLE",
            "RUNTIME_READY_AFTER_RECOVERY",
            "HEALTH_CODE_AFTER_RECOVERY",
            "OPENAI_CONTROL_READY_AFTER_RECOVERY",
            "DESIRED_STATE_BEFORE",
            "DESIRED_STATE_RESTORED",
            "RESULT_DIR",
        ):
            self.assertIn(marker, SOURCE)
        self.assertIn("ProcessId -ne $oldTunnelPid", SOURCE)
        self.assertIn("ProcessId -eq $oldSupervisorPid", SOURCE)
        self.assertIn("[bool]$status.runtime_ready", SOURCE)

    def test_qualification_records_machine_readable_evidence_and_resource_use(self):
        self.assertIn("Save-JsonEvidence -Name 'summary'", SOURCE)
        self.assertIn("resources.csv", SOURCE)
        self.assertIn("WorkingSet64", SOURCE)
        self.assertIn("PrivateMemorySize64", SOURCE)
        self.assertIn("supervisor-after-recovery.json", SOURCE)
        self.assertIn("recovery-after-recovery.json", SOURCE)
        self.assertIn("failure.json", SOURCE)

    def test_failure_uninstalls_qualification_assets_and_restores_desired_state(self):
        self.assertIn("& $Installer -Uninstall", SOURCE)
        self.assertIn("if ($desiredStateBefore -eq 'running')", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Stop", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Start", SOURCE)
        self.assertIn("desired_state_before", SOURCE)
        self.assertIn("desired_state_restored", SOURCE)

    def test_stopped_desired_state_stops_supervisor_around_manager_stop(self):
        block_start = SOURCE.index("if ($desiredStateBefore -eq 'stopped')")
        block = SOURCE[block_start : SOURCE.index("$summary = [ordered]@{", block_start)]
        self.assertIn("Stop-QualificationSupervisor", block)
        self.assertIn("Invoke-ManagerMutation -Action Stop", block)
        self.assertIn("Start-QualificationSupervisor", block)
        self.assertLess(block.index("Stop-QualificationSupervisor"), block.index("Invoke-ManagerMutation -Action Stop"))
        self.assertLess(block.index("Invoke-ManagerMutation -Action Stop"), block.index("Start-QualificationSupervisor"))

    def test_first_gate_does_not_disable_network_sleep_or_reboot_machine(self):
        forbidden = (
            "Disable-NetAdapter",
            "Restart-Computer",
            "shutdown.exe",
            "rundll32.exe powrprof",
            "Set-SuspendState",
        )
        for value in forbidden:
            self.assertNotIn(value, SOURCE)


if __name__ == "__main__":
    unittest.main()