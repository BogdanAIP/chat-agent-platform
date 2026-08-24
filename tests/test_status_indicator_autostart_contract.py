from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install-chat-platform-supervisor.ps1"
SOURCE = INSTALLER.read_text(encoding="utf-8")


class StatusIndicatorAutostartContractTests(unittest.TestCase):
    def test_installer_registers_separate_indicator_task(self):
        self.assertIn("Chat Agent Platform Status Indicator", SOURCE)
        self.assertIn("function Register-TrayTask", SOURCE)
        self.assertIn("Register-ScheduledTask", SOURCE)
        self.assertIn("$TrayTaskName", SOURCE)
        self.assertIn("$InstalledTray", SOURCE)

    def test_indicator_task_is_current_user_limited_and_console_free(self):
        self.assertIn("-LogonType Interactive", SOURCE)
        self.assertIn("-RunLevel Limited", SOURCE)
        self.assertIn("'-WindowStyle', 'Hidden'", SOURCE)
        self.assertIn("'-NoConsoleHost'", SOURCE)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn -User $identity", SOURCE)

    def test_indicator_is_started_and_stopped_with_supervisor_install_lifecycle(self):
        self.assertIn("Stop-TrayTaskIfPresent", SOURCE)
        self.assertIn("Start-ScheduledTask -TaskName $TrayTaskName", SOURCE)
        self.assertIn("Unregister-ScheduledTask -TaskName $TrayTaskName", SOURCE)

    def test_supervisor_uninstall_does_not_delete_base_tray_asset(self):
        uninstall_start = SOURCE.index("function Uninstall-Supervisor")
        uninstall = SOURCE[uninstall_start:]
        self.assertNotIn("Remove-Item -LiteralPath $InstalledTray", uninstall)

    def test_indicator_task_reuses_existing_bootstrapped_tray(self):
        self.assertIn("Installed Chat Agent Platform tray is missing", SOURCE)
        self.assertNotIn("Copy-VerifiedFile -Source $SourceTray", SOURCE)


if __name__ == "__main__":
    unittest.main()
