from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "launch-chatgpt-temporary-worker.ps1"


class ChatGPTTemporaryPhysicalLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SCRIPT.read_text(encoding="utf-8")

    def test_launcher_requires_exact_head_and_rechecks_source_after_result(self) -> None:
        self.assertIn("[string]$ExpectedHead", self.text)
        self.assertIn("EXACT_HEAD_MISMATCH", self.text)
        self.assertIn("source-provenance-before.json", self.text)
        self.assertIn("source-provenance-after.json", self.text)
        self.assertGreaterEqual(self.text.count("Invoke-SourceGate"), 3)
        for asset in (
            "runtime/control_plane/delegation_state.py",
            "runtime/agent_sessions/source_attestation.py",
            "runtime/agent_sessions/chatgpt_temporary.py",
            "runtime/agent_sessions/chatgpt_temporary_controller.py",
            "runtime/agent_sessions/chatgpt_temporary_extension/manifest.json",
            "runtime/agent_sessions/chatgpt_temporary_extension/execution_generation.js",
            "runtime/agent_sessions/chatgpt_temporary_extension/policy.js",
            "runtime/agent_sessions/chatgpt_temporary_extension/background.js",
            "runtime/agent_sessions/chatgpt_temporary_extension/content.js",
        ):
            self.assertIn(asset, self.text)

    def test_launcher_builds_exact_expected_installed_extension_attestation(self) -> None:
        self.assertIn("expected-runtime-attestation.json", self.text)
        self.assertIn("expected_head = $ExpectedHead", self.text)
        self.assertIn("execution_generation = $executionGeneration", self.text)
        self.assertIn("adapter_id = 'chatgpt-temporary'", self.text)
        self.assertIn("CAPChatGPTTemporaryExecutionGeneration", self.text)
        for asset in (
            "manifest.json",
            "execution_generation.js",
            "policy.js",
            "background.js",
            "content.js",
        ):
            self.assertIn(f"'{asset}' = Get-Sha256", self.text)
        self.assertIn("--runtime-attestation-json", self.text)
        self.assertIn("$runtimeAttestationPath", self.text)
        self.assertIn("CAP_AGENT_SESSION_EXPECTED_EXTENSION_ATTESTATION", self.text)
        self.assertIn("CAP_AGENT_SESSION_EXECUTION_GENERATION", self.text)
        self.assertIn("Controller runtime-attestation head mismatch", self.text)
        self.assertIn("Controller execution-generation mismatch", self.text)

    def test_launcher_keeps_state_and_evidence_outside_repository(self) -> None:
        self.assertIn("$env:LOCALAPPDATA", self.text)
        self.assertIn("ChatAgentPlatform\\agent-sessions\\private-state", self.text)
        self.assertIn("ChatAgentPlatform\\agent-sessions\\qualification", self.text)
        self.assertNotIn("Set-Content -Path $RepoRoot", self.text)

    def test_neutral_preflight_is_opened_before_one_task_launch_and_contains_no_task_material(self) -> None:
        preflight_gate = self.text.index("if ($phase -eq 'preflight')")
        preflight_start = self.text.index("Start-Process $preflightUrl", preflight_gate)
        launch_gate = self.text.index("if ([bool]$launch.launch_now)", preflight_start)
        task_start = self.text.index("Start-Process $taskLaunchUrl", launch_gate)
        self.assertLess(preflight_start, task_start)
        self.assertIn("cap_agent_preflight=1#cap_preflight_id=", self.text)
        self.assertIn("Preflight URL contains task/private launch material", self.text)
        self.assertEqual(1, self.text[launch_gate:].count("Start-Process $taskLaunchUrl"))
        self.assertIn("blocked-existing-delegation-monitor-only", self.text[launch_gate:])

    def test_stale_preflight_projection_is_removed_before_controller_start(self) -> None:
        controller_start = self.text.index("$controller = Start-Process")
        cleanup = self.text[:controller_start]
        self.assertIn(
            "$controllerStdout, $controllerStderr, $preflightPath, $launchPath, $resultPath",
            cleanup,
        )

    def test_result_must_match_exact_delegation_delivery_and_success_status(self) -> None:
        self.assertIn("Result delegation correlation mismatch", self.text)
        self.assertIn("Result delivery correlation mismatch", self.text)
        self.assertIn("Physical qualification requires COMPLETED worker result", self.text)
        completion_gate = self.text.index("if ([string]$result.status -ne 'COMPLETED')")
        pass_marker = self.text.index("CAP_AGENT_SESSION_PHYSICAL=PASS")
        self.assertLess(completion_gate, pass_marker)
        self.assertIn("CAP_AGENT_SESSION_RESULT_SHA256", self.text)

    def test_terminal_restart_uses_only_fresh_controller_projections(self) -> None:
        terminal_gate = self.text.index("$terminalSnapshotReady = $false")
        launch_parse = self.text.index(
            "if (-not (Test-Path -LiteralPath $launchPath -PathType Leaf))",
            terminal_gate,
        )
        terminal_block = self.text[terminal_gate:launch_parse]
        self.assertIn("$controller.HasExited", terminal_block)
        self.assertIn("$controller.ExitCode -eq 0", terminal_block)
        self.assertIn("Test-Path -LiteralPath $launchPath -PathType Leaf", terminal_block)
        self.assertIn("Test-Path -LiteralPath $resultPath -PathType Leaf", terminal_block)
        self.assertIn("CAP_AGENT_SESSION_CONTROLLER=terminal-readback", terminal_block)

    def test_empty_controller_stderr_cannot_mask_the_real_launcher_error(self) -> None:
        self.assertIn("function Get-LogText", self.text)
        self.assertIn("if ($null -eq $raw) { return '' }", self.text)
        self.assertNotIn(
            "(Get-Content -LiteralPath $controllerStderr -Raw -Encoding utf8).Trim()",
            self.text,
        )

    def test_validate_only_runs_provenance_without_starting_controller(self) -> None:
        marker = self.text.index("if ($ValidateOnly)")
        controller = self.text.index("$controller = Start-Process", marker)
        self.assertLess(marker, controller)
        validate_block = self.text[marker:controller]
        self.assertIn("CAP_AGENT_SESSION_VALIDATE_ONLY=PASS", validate_block)
        self.assertIn("expected-runtime-attestation.json", self.text[:marker])
        self.assertIn("return", validate_block)

    def test_powershell_syntax_when_available(self) -> None:
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            self.skipTest("pwsh is unavailable")
        command = (
            "$errors=$null; "
            f"[System.Management.Automation.Language.Parser]::ParseFile('{SCRIPT.as_posix()}',[ref]$null,[ref]$errors)|Out-Null; "
            "if($errors.Count){$errors|ForEach-Object{$_.ToString()}; exit 1}"
        )
        completed = subprocess.run(
            [pwsh, "-NoProfile", "-Command", command],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
