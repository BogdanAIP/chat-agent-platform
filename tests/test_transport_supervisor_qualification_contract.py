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

    def test_fault_injection_kills_only_the_resolved_owned_tunnel_pid(self):
        self.assertIn("Stop-Process -Id $oldTunnelPid -Force -ErrorAction Stop", SOURCE)
        self.assertNotIn("Stop-Process -Name", SOURCE)
        self.assertNotIn("taskkill", SOURCE.lower())

    def test_acceptance_requires_new_tunnel_pid_same_supervisor_and_ready_runtime(self):
        for marker in (
            "TRANSPORT_SUPERVISOR_QUALIFICATION_RESULT",
            "TUNNEL_PID_CHANGED",
            "SUPERVISOR_PID_STABLE",
            "RUNTIME_READY_AFTER_RECOVERY",
            "HEALTH_CODE_AFTER_RECOVERY",
            "OPENAI_CONTROL_READY_AFTER_RECOVERY",
            "RESULT_DIR",
        ):
            self.assertIn(marker, SOURCE)
        self.assertIn("ProcessId -ne $oldTunnelPid", SOURCE)
        self.assertIn("ProcessId -eq $oldSupervisorPid", SOURCE)
        self.assertIn("[bool]$status.runtime_ready", SOURCE)

    def test_qualification_records_machine_readable_evidence_and_resource_use(self):
        self.assertIn("summary.json", SOURCE)
        self.assertIn("resources.csv", SOURCE)
        self.assertIn("WorkingSet64", SOURCE)
        self.assertIn("PrivateMemorySize64", SOURCE)
        self.assertIn("supervisor-after-recovery.json", SOURCE)
        self.assertIn("recovery-after-recovery.json", SOURCE)

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
