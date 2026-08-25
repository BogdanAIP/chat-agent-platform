from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = (ROOT / "scripts" / "install-chat-platform-supervisor.ps1").read_text(encoding="utf-8")
LAUNCHER = (ROOT / "scripts" / "chat-platform-supervisor-launcher.vbs").read_text(encoding="utf-8")


class TransportSupervisorConsoleFreeLauncherContractTests(unittest.TestCase):
    def test_scheduled_task_uses_gui_subsystem_wscript_host(self):
        self.assertIn("System32\\wscript.exe", INSTALLER)
        self.assertIn("New-ScheduledTaskAction -Execute $wscript", INSTALLER)
        self.assertNotIn("New-ScheduledTaskAction -Execute $pwsh", INSTALLER)

    def test_launcher_is_installed_and_hash_verified(self):
        self.assertIn("chat-platform-supervisor-launcher.vbs", INSTALLER)
        self.assertIn("Copy-VerifiedFile -Source $SourceSupervisorLauncher -Destination $InstalledSupervisorLauncher", INSTALLER)
        self.assertIn("@($SourceSupervisorLauncher, $InstalledSupervisorLauncher)", INSTALLER)
        self.assertIn("Remove-Item -LiteralPath $InstalledSupervisorLauncher", INSTALLER)

    def test_launcher_uses_one_shot_reconcile_and_thirty_minute_sleep(self):
        self.assertIn('shell.Run(command, 0, True)', LAUNCHER)
        self.assertIn('" -Action Reconcile"', LAUNCHER)
        self.assertIn("AutomaticHealthIntervalMilliseconds = 1800000", LAUNCHER)
        self.assertIn("WScript.Sleep AutomaticHealthIntervalMilliseconds", LAUNCHER)
        self.assertNotIn('" -Action Run"', LAUNCHER)
        self.assertIn("WScript.Arguments.Count <> 2", LAUNCHER)

    def test_manual_mode_exits_without_starting_supervisor_loop(self):
        first_manual_gate = LAUNCHER.index("If IsManualMode(modePath) Then")
        first_reconcile = LAUNCHER.index('" -Action Reconcile"')
        self.assertLess(first_manual_gate, first_reconcile)
        self.assertIn('operation-mode.json', LAUNCHER)
        self.assertIn('"manual"', LAUNCHER)
        self.assertIn("WScript.Quit 0", LAUNCHER)

    def test_task_keeps_current_user_limited_context(self):
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn -User $identity", INSTALLER)
        self.assertIn("-LogonType Interactive", INSTALLER)
        self.assertIn("-RunLevel Limited", INSTALLER)
        self.assertNotIn("RunLevel Highest", INSTALLER)
        self.assertNotIn("LocalSystem", INSTALLER)


if __name__ == "__main__":
    unittest.main()
