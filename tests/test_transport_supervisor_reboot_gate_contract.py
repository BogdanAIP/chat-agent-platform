from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "transport-supervisor-reboot-gate.ps1"
SOURCE = SCRIPT.read_text(encoding="utf-8")


class TransportSupervisorRebootGateContractTests(unittest.TestCase):
    def test_gate_is_two_phase_and_never_initiates_reboot(self):
        self.assertIn("[ValidateSet('Prepare', 'Verify')]", SOURCE)
        for forbidden in (
            "Restart-Computer",
            "Stop-Computer",
            "shutdown.exe",
            "SetSuspendState",
            "rundll32.exe powrprof.dll",
        ):
            self.assertNotIn(forbidden, SOURCE)

    def test_prepare_bootstraps_transport_health_surface_before_core(self):
        install_at = SOURCE.index("& $Installer -NoStart")
        core_at = SOURCE.index("Invoke-CoreProcess", SOURCE.index("REBOOT_GATE_MODE=prepare-bootstrap"))
        self.assertLess(install_at, core_at)
        self.assertIn("Installing the qualification transport health surface before baseline evaluation", SOURCE)

    def test_core_runs_in_child_process_so_core_exit_cannot_bypass_gate_cleanup(self):
        self.assertIn("[System.Diagnostics.ProcessStartInfo]::new()", SOURCE)
        self.assertIn("'-Command', $coreCommand", SOURCE)
        self.assertIn("Reboot qualification core failed with exit code", SOURCE)
        self.assertNotIn("& $Core @", SOURCE)

    def test_core_output_inherits_console_instead_of_redirected_pipes(self):
        core_block = SOURCE.split("function Invoke-CoreProcess", 1)[1].split("if ($Phase -eq 'Verify')", 1)[0]
        self.assertIn("$startInfo.CreateNoWindow = $false", core_block)
        self.assertNotIn("RedirectStandardOutput", core_block)
        self.assertNotIn("RedirectStandardError", core_block)
        self.assertNotIn("ReadToEndAsync", core_block)
        self.assertNotIn("StandardOutput", core_block)
        self.assertNotIn("StandardError", core_block)

    def test_core_runs_with_deterministic_culture(self):
        core_block = SOURCE.split("function Invoke-CoreProcess", 1)[1].split("if ($Phase -eq 'Verify')", 1)[0]
        self.assertIn("CultureInfo]::InvariantCulture", core_block)
        self.assertIn("CurrentThread.CurrentCulture = $culture", core_block)
        self.assertIn("CurrentThread.CurrentUICulture = $culture", core_block)

    def test_verify_is_observational_and_does_not_install_or_mutate_manager(self):
        verify_block = SOURCE.split("if ($Phase -eq 'Verify')", 1)[1].split("$desiredStateBefore", 1)[0]
        self.assertIn("REBOOT_GATE_MODE=verify-observational", verify_block)
        self.assertIn("Invoke-CoreProcess", verify_block)
        self.assertNotIn("$Installer", verify_block)
        self.assertNotIn("Invoke-ManagerMutation", verify_block)

    def test_failed_prepare_rolls_back_install_and_restores_prior_desired_state(self):
        self.assertIn("REBOOT_GATE_PREPARE_ROLLBACK=True", SOURCE)
        self.assertIn("& $Installer -Uninstall", SOURCE)
        self.assertIn("if ($desiredStateBefore -eq 'running')", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Stop", SOURCE)
        self.assertIn("Invoke-ManagerMutation -Action Start", SOURCE)
        self.assertIn("REBOOT_GATE_PREPARE_RESULT=FAILED", SOURCE)

    def test_success_is_only_printed_after_child_core_exit_zero(self):
        success_at = SOURCE.index("REBOOT_GATE_PREPARE_RESULT=PASSED")
        core_at = SOURCE.index("Invoke-CoreProcess", SOURCE.index("REBOOT_GATE_MODE=prepare-bootstrap"))
        self.assertGreater(success_at, core_at)


if __name__ == "__main__":
    unittest.main()
