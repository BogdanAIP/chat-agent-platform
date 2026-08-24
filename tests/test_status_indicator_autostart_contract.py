from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install-chat-platform-supervisor.ps1"
LAUNCHER = ROOT / "scripts" / "chat-platform-tray-launcher.vbs"
SOURCE = INSTALLER.read_text(encoding="utf-8")
LAUNCHER_SOURCE = LAUNCHER.read_text(encoding="utf-8")


class StatusIndicatorAutostartContractTests(unittest.TestCase):
    def test_installer_registers_separate_indicator_task(self):
        self.assertIn("Chat Agent Platform Status Indicator", SOURCE)
        self.assertIn("function Register-TrayTask", SOURCE)
        self.assertIn("Register-ScheduledTask", SOURCE)
        self.assertIn("$TrayTaskName", SOURCE)
        self.assertIn("$InstalledTray", SOURCE)
        self.assertIn("$InstalledTrayLauncher", SOURCE)

    def test_indicator_task_is_current_user_limited_and_uses_gui_host(self):
        self.assertIn("-LogonType Interactive", SOURCE)
        self.assertIn("-RunLevel Limited", SOURCE)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn -User $identity", SOURCE)
        tray_start = SOURCE.index("function Register-TrayTask")
        tray_end = SOURCE.index("function Uninstall-Supervisor", tray_start)
        tray_block = SOURCE[tray_start:tray_end]
        self.assertIn("$wscript = Get-WscriptPath", tray_block)
        self.assertIn("New-ScheduledTaskAction -Execute $wscript", tray_block)
        self.assertNotIn("New-ScheduledTaskAction -Execute $pwsh", tray_block)
        self.assertIn("$InstalledTrayLauncher", tray_block)

    def test_tray_launcher_is_hidden_and_no_console(self):
        self.assertIn('shell.Run command, 0, False', LAUNCHER_SOURCE)
        self.assertIn('" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "', LAUNCHER_SOURCE)
        self.assertIn('" -NoConsoleHost"', LAUNCHER_SOURCE)
        self.assertNotIn("-Action Run", LAUNCHER_SOURCE)

    def test_indicator_is_started_and_stopped_with_supervisor_install_lifecycle(self):
        self.assertIn("Stop-TrayTaskIfPresent", SOURCE)
        self.assertIn("Start-ScheduledTask -TaskName $TrayTaskName", SOURCE)
        self.assertIn("Unregister-ScheduledTask -TaskName $TrayTaskName", SOURCE)

    def test_supervisor_uninstall_does_not_delete_base_tray_asset(self):
        uninstall_start = SOURCE.index("function Uninstall-Supervisor")
        uninstall = SOURCE[uninstall_start:]
        self.assertNotIn("Remove-Item -LiteralPath $InstalledTray ", uninstall)
        self.assertIn("Remove-Item -LiteralPath $InstalledTrayLauncher", uninstall)

    def test_indicator_task_reuses_existing_bootstrapped_tray(self):
        self.assertIn("Installed Chat Agent Platform tray is missing", SOURCE)
        self.assertNotIn("$SourceTray =", SOURCE)
        self.assertNotIn("Copy-VerifiedFile -Source $SourceTray -Destination $InstalledTray", SOURCE)


if __name__ == "__main__":
    unittest.main()
