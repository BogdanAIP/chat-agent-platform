from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install-chat-platform-supervisor.ps1"
SOURCE = INSTALLER.read_text(encoding="utf-8")


class TransportSupervisorInstallerRollbackTests(unittest.TestCase):
    def test_existing_direct_controller_is_backed_up_before_qualification_replace(self):
        self.assertIn("transport-supervisor-backup", SOURCE)
        self.assertIn("$DirectControllerBackup", SOURCE)
        self.assertIn("Backup-InstalledDirectControllerIfNeeded", SOURCE)
        self.assertIn(
            "Copy-VerifiedFile -Source $InstalledDirectController -Destination $DirectControllerBackup",
            SOURCE,
        )

    def test_uninstall_restores_backup_and_does_not_delete_controller_without_one(self):
        self.assertIn("Restore-DirectControllerBackupIfPresent", SOURCE)
        self.assertIn(
            "Copy-VerifiedFile -Source $DirectControllerBackup -Destination $InstalledDirectController",
            SOURCE,
        )
        uninstall = SOURCE[
            SOURCE.index("function Uninstall-Supervisor") :
            SOURCE.index("New-Item -ItemType Directory")
        ]
        self.assertNotIn("Remove-Item -LiteralPath $InstalledDirectController", uninstall)

    def test_backup_and_restore_share_public_manager_mutation_mutex(self):
        self.assertIn("function Invoke-WithManagerMutex", SOURCE)
        self.assertIn("Local\\ChatAgentPlatformControllerOperation", SOURCE)
        install = SOURCE[
            SOURCE.index("function Install-SupervisorAssets") :
            SOURCE.index("function Register-SupervisorTask")
        ]
        uninstall = SOURCE[
            SOURCE.index("function Uninstall-Supervisor") :
            SOURCE.index("New-Item -ItemType Directory")
        ]
        self.assertIn("Invoke-WithManagerMutex", install)
        self.assertIn("Invoke-WithManagerMutex", uninstall)


if __name__ == "__main__":
    unittest.main()
