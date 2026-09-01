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
        self.assertGreaterEqual(self.text.count("Invoke-SourceGate"), 3)  # definition + before + after
        for asset in (
            "runtime/control_plane/delegation_state.py",
            "runtime/agent_sessions/source_attestation.py",
            "runtime/agent_sessions/chatgpt_temporary.py",
            "runtime/agent_sessions/chatgpt_temporary_controller.py",
            "runtime/agent_sessions/chatgpt_temporary_extension/manifest.json",
            "runtime/agent_sessions/chatgpt_temporary_extension/policy.js",
            "runtime/agent_sessions/chatgpt_temporary_extension/background.js",
            "runtime/agent_sessions/chatgpt_temporary_extension/content.js",
        ):
            self.assertIn(asset, self.text)

    def test_launcher_builds_exact_expected_installed_extension_attestation(self) -> None:
        self.assertIn("expected-runtime-attestation.json", self.text)
        self.assertIn("expected_head = $ExpectedHead", self.text)
        self.assertIn("adapter_id = 'chatgpt-temporary'", self.text)
        for asset in ("manifest.json", "policy.js", "background.js", "content.js"):
            self.assertIn(f"'{asset}' = Get-Sha256", self.text)
        self.assertIn("--runtime-attestation-json", self.text)
        self.assertIn("$runtimeAttestationPath", self.text)
        self.assertIn("CAP_AGENT_SESSION_EXPECTED_EXTENSION_ATTESTATION", self.text)
        self.assertIn("Controller runtime-attestation head mismatch", self.text)

    def test_launcher_keeps_state_and_evidence_outside_repository(self) -> None:
        self.assertIn("$env:LOCALAPPDATA", self.text)
        self.assertIn("ChatAgentPlatform\\agent-sessions\\private-state", self.text)
        self.assertIn("ChatAgentPlatform\\agent-sessions\\qualification", self.text)
        self.assertNotIn("Set-Content -Path $RepoRoot", self.text)

    def test_browser_launch_requires_durable_launch_now_and_has_no_retry_loop(self) -> None:
        launch_gate = self.text.index("if ([bool]$launch.launch_now)")
        start = self.text.index("Start-Process ([string]$launch.launch_url)", launch_gate)
        self.assertGreater(start, launch_gate)
        post_gate = self.text[launch_gate:]
        self.assertEqual(1, post_gate.count("Start-Process ([string]$launch.launch_url)"))
        self.assertIn("blocked-existing-delegation-monitor-only", post_gate)

    def test_result_must_match_exact_delegation_and_delivery(self) -> None:
        self.assertIn("Result delegation correlation mismatch", self.text)
        self.assertIn("Result delivery correlation mismatch", self.text)
        self.assertIn("CAP_AGENT_SESSION_PHYSICAL=PASS", self.text)
        self.assertIn("CAP_AGENT_SESSION_RESULT_SHA256", self.text)

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
