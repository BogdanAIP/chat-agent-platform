import shutil
import subprocess
import unittest
from pathlib import Path


class Stage4PowerShellSyntaxTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell is required for Stage 4 script syntax validation")
    def test_stage4_entrypoints_parse_without_errors(self):
        repo = Path(__file__).resolve().parents[1]
        scripts = [
            repo / "scripts" / "deploy-stage4-yandex.ps1",
            repo / "scripts" / "provision-stage4-yandex.ps1",
        ]
        for script in scripts:
            self.assertTrue(script.is_file(), f"missing Stage 4 script: {script}")
            command = (
                "$tokens=$null; $errors=$null; "
                "[System.Management.Automation.Language.Parser]::ParseFile(" 
                "'" + str(script).replace("'", "''") + "',[ref]$tokens,[ref]$errors) | Out-Null; "
                "if ($errors.Count -ne 0) { "
                "$errors | ForEach-Object { Write-Error $_.Message }; exit 1 }"
            )
            completed = subprocess.run(
                ["pwsh", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"PowerShell syntax failed for {script.name}:\nstdout={completed.stdout}\nstderr={completed.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
