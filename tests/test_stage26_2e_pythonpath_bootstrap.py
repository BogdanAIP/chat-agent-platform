from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "stage26-vscode-real-app-e2e.ps1"


class Stage262EPythonPathBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = HARNESS.read_text(encoding="utf-8")

    def test_harness_bootstraps_repo_root_for_direct_driver_execution(self) -> None:
        required = (
            "$previousPythonPath = [Environment]::GetEnvironmentVariable('PYTHONPATH', 'Process')",
            "$env:PYTHONPATH = if ([string]::IsNullOrWhiteSpace($previousPythonPath))",
            "$repoRoot + [IO.Path]::PathSeparator + $previousPythonPath",
            "& $pythonExe $driverPath",
        )
        for item in required:
            self.assertIn(item, self.harness)

        capture = self.harness.index("$previousPythonPath =")
        assign = self.harness.index("$env:PYTHONPATH = if", capture)
        invoke = self.harness.index("& $pythonExe $driverPath", assign)
        restore = self.harness.index("Remove-Item Env:PYTHONPATH", invoke)
        result_read = self.harness.index("$driver = Get-Content", restore)
        self.assertLess(capture, assign)
        self.assertLess(assign, invoke)
        self.assertLess(invoke, restore)
        self.assertLess(restore, result_read)

    def test_harness_restores_existing_or_absent_process_pythonpath(self) -> None:
        for required in (
            "if ($null -eq $previousPythonPath)",
            "Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue",
            "$env:PYTHONPATH = $previousPythonPath",
        ):
            self.assertIn(required, self.harness)

        self.assertNotIn("SetEnvironmentVariable('PYTHONPATH',", self.harness)
        self.assertNotIn('SetEnvironmentVariable("PYTHONPATH",', self.harness)


if __name__ == "__main__":
    unittest.main()
