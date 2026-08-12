from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRAY = ROOT / "scripts" / "chat-platform-tray.ps1"


class TrayNoConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tray = TRAY.read_text(encoding="utf-8")

    def test_tray_self_handoff_prevents_persistent_console_host(self):
        self.assertIn("$NoConsoleHost", self.tray)
        self.assertIn("System.Diagnostics.ProcessStartInfo", self.tray)
        self.assertIn("$startInfo.UseShellExecute = $false", self.tray)
        self.assertIn("$startInfo.CreateNoWindow = $true", self.tray)
        self.assertIn('"-NoConsoleHost"', self.tray)
        self.assertIn("$PSCommandPath", self.tray)
        self.assertRegex(
            self.tray,
            re.compile(
                r"if \(\$IsWindows -and -not \$NoConsoleHost\).*?"
                r"CreateNoWindow = \$true.*?exit 0",
                re.S,
            ),
        )

    def test_tray_mutex_is_acquired_only_after_no_console_handoff(self):
        handoff = self.tray.index("if ($IsWindows -and -not $NoConsoleHost)")
        mutex = self.tray.index("Local\\ChatAgentPlatformTray")
        self.assertLess(handoff, mutex)


if __name__ == "__main__":
    unittest.main()
