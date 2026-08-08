import shutil
import subprocess
import unittest
from pathlib import Path


class Stage4PowerShellSyntaxTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.deploy = self.repo / "scripts" / "deploy-stage4-yandex.ps1"
        self.provision = self.repo / "scripts" / "provision-stage4-yandex.ps1"

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell is required for Stage 4 script syntax validation")
    def test_stage4_entrypoints_parse_without_errors(self):
        for script in [self.deploy, self.provision]:
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

    def test_provision_and_deploy_remote_auth_contract_stays_aligned(self):
        deploy = self.deploy.read_text(encoding="utf-8")
        provision = self.provision.read_text(encoding="utf-8")
        template = (self.repo / "gateway" / "actions-openapi.template.json").read_text(
            encoding="utf-8"
        )

        self.assertIn("[switch]$CopyActionTokenToClipboard", deploy)
        self.assertIn("MCP_TOKEN=$remoteToken", deploy)
        self.assertIn("runtime/relay/actions-openapi.json", deploy.replace("\\", "/"))
        self.assertIn("Set-Clipboard -Value $remoteToken", deploy)
        self.assertIn("CopyActionTokenToClipboard = $true", provision)
        self.assertIn("Get-Clipboard -Raw", provision)
        self.assertIn("__FUNCTION_URL__", template)
        self.assertIn("remote_bearer_returned = $false", deploy)
        self.assertIn("agent_token_returned = $false", deploy)


if __name__ == "__main__":
    unittest.main()
