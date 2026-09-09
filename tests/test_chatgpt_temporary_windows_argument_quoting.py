from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "launch-chatgpt-temporary-worker.ps1"


class ChatGPTTemporaryWindowsArgumentQuotingTests(unittest.TestCase):
    def test_launcher_argument_encoder_preserves_python_argv_on_windows(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command-line parsing semantics are required")
        pwsh = shutil.which("pwsh")
        python = shutil.which("python")
        if pwsh is None or python is None:
            self.skipTest("pwsh/python are unavailable")

        launcher = SCRIPT.read_text(encoding="utf-8")
        function_start = launcher.index("function ConvertTo-WindowsCommandLineArgument {")
        function_end = launcher.index("\nfunction Invoke-SourceGate {", function_start)
        function_text = launcher[function_start:function_end]

        def ps_literal(value: str | Path) -> str:
            return "'" + str(value).replace("'", "''") + "'"

        values = [
            "plain",
            "path with spaces\\child",
            'quote"inside',
            "trailing-backslash\\",
            "spaces and trailing\\",
            "",
        ]
        python_code = (
            "import json,sys;from pathlib import Path;"
            "Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]),encoding='utf-8')"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "argument quoting fixture"
            root.mkdir()
            result = root / "argv result.json"
            arguments = ["-I", "-S", "-c", python_code, str(result), *values]
            ps_arguments = ",\n        ".join(ps_literal(value) for value in arguments)
            script = f"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
{function_text}
$python = Get-Command {ps_literal(python)} -ErrorAction Stop
$arguments = @(
        {ps_arguments}
)
$argumentLine = (($arguments | ForEach-Object {{
    ConvertTo-WindowsCommandLineArgument -Value ([string]$_)
}}) -join ' ')
$process = Start-Process -FilePath $python.Source -ArgumentList $argumentLine -PassThru -Wait -NoNewWindow
if ($process.ExitCode -ne 0) {{ throw "quoted argv fixture failed: $($process.ExitCode)" }}
"""
            completed = subprocess.run(
                [pwsh, "-NoProfile", "-Command", script],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertTrue(result.is_file(), completed.stdout + completed.stderr)
            self.assertEqual(values, json.loads(result.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
