from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import time
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

    def test_launcher_builds_expected_extension_attestation_from_exact_git_archive(self) -> None:
        self.assertIn("expected-runtime-attestation.json", self.text)
        self.assertIn("expected_head = $ExpectedHead", self.text)
        self.assertIn("execution_generation = $executionGeneration", self.text)
        self.assertIn("adapter_id = 'chatgpt-temporary'", self.text)
        self.assertIn("git-archive-exact-head", self.text)
        self.assertIn("Get-ZipEntrySha256", self.text)
        self.assertIn("$runtimeAssets[$assetName] = Get-ZipEntrySha256", self.text)
        self.assertIn("CAPChatGPTTemporaryExecutionGeneration", self.text)
        for asset in (
            "manifest.json",
            "execution_generation.js",
            "policy.js",
            "background.js",
            "content.js",
        ):
            self.assertIn(f"'{asset}'", self.text)
        self.assertIn("--runtime-attestation-json", self.text)
        self.assertIn("$runtimeAttestationPath", self.text)
        self.assertIn("CAP_AGENT_SESSION_EXPECTED_EXTENSION_ATTESTATION", self.text)
        self.assertIn("CAP_AGENT_SESSION_EXECUTION_GENERATION", self.text)
        self.assertIn("Controller runtime-attestation head mismatch", self.text)
        self.assertIn("Controller execution-generation mismatch", self.text)

    def test_launcher_executes_controller_from_locked_isolated_archive(self) -> None:
        self.assertIn("[System.IO.FileShare]::Read", self.text)
        self.assertIn("runtime_archive_sha256 = $runtimeArchiveSha256", self.text)
        self.assertIn("python_mode = 'isolated-zipimport'", self.text)
        self.assertIn("'-I'", self.text)
        self.assertIn("'-B'", self.text)
        self.assertIn("'-S'", self.text)
        self.assertIn(
            'runpy.run_module("runtime.agent_sessions.chatgpt_temporary_controller",run_name="__main__")',
            self.text,
        )
        self.assertIn("-WorkingDirectory $outputRoot", self.text)
        self.assertNotIn("'-m', 'runtime.agent_sessions.chatgpt_temporary_controller'", self.text)
        self.assertNotIn("-WorkingDirectory $RepoRoot", self.text)

    def test_source_locks_enclose_controller_and_effect_window(self) -> None:
        lock_list = self.text.index("$sourceLocks = [System.Collections.Generic.List[System.IDisposable]]::new()")
        archive_lock = self.text.index(
            "$sourceLocks.Add((Open-ReadShareOnly -Path $runtimeArchivePath))",
            lock_list,
        )
        extension_lock = self.text.index(
            "$sourceLocks.Add((Open-ReadShareOnly -Path $snapshotAsset))",
            archive_lock,
        )
        controller_start = self.text.index("$controller = Start-Process", extension_lock)
        physical_pass = self.text.index("CAP_AGENT_SESSION_PHYSICAL=PASS", controller_start)
        finally_start = self.text.index("\nfinally {", physical_pass)
        lock_dispose = self.text.index("$sourceLocks[$index].Dispose()", finally_start)

        self.assertLess(lock_list, archive_lock)
        self.assertLess(archive_lock, extension_lock)
        self.assertLess(extension_lock, controller_start)
        self.assertLess(controller_start, physical_pass)
        self.assertLess(physical_pass, finally_start)
        self.assertLess(finally_start, lock_dispose)
        self.assertNotIn("$sourceLocks[$index].Dispose()", self.text[archive_lock:finally_start])
        self.assertNotIn("$sourceLocks.Clear()", self.text[archive_lock:finally_start])

    def test_read_share_only_denies_concurrent_write_and_delete_until_release_on_windows(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows FileShare semantics are required")
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            self.skipTest("pwsh is unavailable")

        function_start = self.text.index("function Open-ReadShareOnly {")
        function_end_marker = "\n}\n\nfunction Write-JsonUtf8NoBom"
        function_end = self.text.index(function_end_marker, function_start) + 2
        function_text = self.text[function_start:function_end]

        def ps_literal(path: Path) -> str:
            return "'" + str(path).replace("'", "''") + "'"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime_archive = root / "exact-head-runtime.zip"
            extension_asset = root / "content.js"
            ready = root / "locks-ready.txt"
            release = root / "locks-release.txt"
            runtime_archive.write_bytes(b"exact-head-runtime")
            extension_asset.write_bytes(b"exact-extension-asset")

            script = f"""
{function_text}
$locks = [System.Collections.Generic.List[System.IDisposable]]::new()
try {{
    $null = $locks.Add((Open-ReadShareOnly -Path {ps_literal(runtime_archive)}))
    $null = $locks.Add((Open-ReadShareOnly -Path {ps_literal(extension_asset)}))
    [System.IO.File]::WriteAllText({ps_literal(ready)}, 'ready')
    $deadline = (Get-Date).AddSeconds(20)
    while (-not (Test-Path -LiteralPath {ps_literal(release)} -PathType Leaf)) {{
        if ((Get-Date) -gt $deadline) {{ throw 'source-lock test release timeout' }}
        Start-Sleep -Milliseconds 50
    }}
}}
finally {{
    for ($index = $locks.Count - 1; $index -ge 0; $index--) {{
        $locks[$index].Dispose()
    }}
}}
"""
            process = subprocess.Popen(
                [pwsh, "-NoProfile", "-Command", script],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout = ""
            stderr = ""
            try:
                deadline = time.monotonic() + 10
                while not ready.is_file():
                    if process.poll() is not None:
                        stdout, stderr = process.communicate()
                        self.fail(f"lock holder exited before readiness: {stdout}{stderr}")
                    if time.monotonic() >= deadline:
                        self.fail("timed out waiting for read-share-only lock readiness")
                    time.sleep(0.05)

                for target, original in (
                    (runtime_archive, b"exact-head-runtime"),
                    (extension_asset, b"exact-extension-asset"),
                ):
                    with self.assertRaises(OSError, msg=f"write unexpectedly opened {target.name}"):
                        with target.open("r+b") as handle:
                            handle.write(b"mutated")
                    with self.assertRaises(OSError, msg=f"delete unexpectedly succeeded for {target.name}"):
                        target.unlink()
                    self.assertEqual(original, target.read_bytes())
            finally:
                release.write_text("release", encoding="utf-8")
                try:
                    stdout, stderr = process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    self.fail(f"lock holder did not terminate: {stdout}{stderr}")

            self.assertEqual(0, process.returncode, stdout + stderr)
            runtime_archive.write_bytes(b"changed-after-release")
            extension_asset.write_bytes(b"changed-after-release")
            self.assertEqual(b"changed-after-release", runtime_archive.read_bytes())
            self.assertEqual(b"changed-after-release", extension_asset.read_bytes())
            runtime_archive.unlink()
            extension_asset.unlink()
            self.assertFalse(runtime_archive.exists())
            self.assertFalse(extension_asset.exists())

    def test_launcher_keeps_state_and_evidence_outside_repository(self) -> None:
        self.assertIn("$env:LOCALAPPDATA", self.text)
        self.assertIn("ChatAgentPlatform\\agent-sessions\\private-state", self.text)
        self.assertIn("ChatAgentPlatform\\agent-sessions\\qualification", self.text)
        self.assertNotIn("Set-Content -Path $RepoRoot", self.text)

    def test_launcher_opens_only_neutral_preflight_and_never_task_url(self) -> None:
        preflight_gate = self.text.index("if ($phase -eq 'preflight')")
        preflight_start = self.text.index("Start-Process $preflightUrl", preflight_gate)
        self.assertIn("cap_agent_preflight=1#cap_preflight_id=", self.text)
        self.assertIn("Preflight URL contains task/private launch material", self.text)
        self.assertEqual(1, self.text.count("Start-Process $preflightUrl"))
        self.assertNotIn("Start-Process $taskLaunchUrl", self.text)
        self.assertNotIn("CAP_AGENT_SESSION_LAUNCHING=fresh-temporary-chat", self.text)
        self.assertIn("CAP_AGENT_SESSION_TASK_NAVIGATION_OWNER=preflight-tab", self.text[preflight_start:])
        self.assertIn("location.replace(task_url)", self.text[preflight_start:])

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
        self.assertIn("CAP_AGENT_SESSION_EXTENSION_PATH", self.text[:marker])
        self.assertIn("source-execution-snapshot.json", self.text[:marker])
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
