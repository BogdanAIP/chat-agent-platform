from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare-windows-case-l3.ps1"


class WindowsCaseSeedCardinalityTests(unittest.TestCase):
    def test_prepare_uses_explicit_four_case_cardinality_guards(self) -> None:
        source = PREPARE.read_text(encoding="utf-8")
        self.assertNotIn(
            "$suffixes = @($baseSuffix, $baseSuffix + 1, $baseSuffix + 10, $baseSuffix + 11)",
            source,
        )
        self.assertIn("$suffixes = [int[]]@(", source)
        self.assertIn("Case Desk suffix cardinality invariant failed", source)
        self.assertIn("Case Desk fixture cardinality invariant failed", source)
        self.assertIn('Write-Host "CASE_FIXTURE_CARDINALITY=$(@($cases).Count)"', source)

    def test_actual_prepare_suffix_block_executes_as_exactly_four_items(self) -> None:
        pwsh = shutil.which("pwsh") or shutil.which("pwsh.exe")
        if pwsh is None:
            self.skipTest("PowerShell is unavailable on this runner")

        source = PREPARE.read_text(encoding="utf-8")
        start = source.index("$baseSuffix = Get-Random")
        end = source.index("$targetIndex =", start)
        suffix_block = source[start:end]
        probe = (
            "Set-StrictMode -Version Latest\n"
            "$ErrorActionPreference = 'Stop'\n"
            + suffix_block
            + "\nif (@($suffixes).Count -ne 4) { throw 'runtime-cardinality-mismatch' }\n"
            + "$unique = @($suffixes | Sort-Object -Unique)\n"
            + "if (@($unique).Count -ne 4) { throw 'runtime-cardinality-not-unique' }\n"
            + "Write-Output 'WINDOWS_CASE_SEED_CARDINALITY_RUNTIME=PASS'\n"
        )
        completed = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", probe],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=f"stdout={completed.stdout}\nstderr={completed.stderr}",
        )
        self.assertIn("WINDOWS_CASE_SEED_CARDINALITY_RUNTIME=PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
