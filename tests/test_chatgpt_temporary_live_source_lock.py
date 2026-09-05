from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "launch-chatgpt-temporary-worker.ps1"
PINNED_PORT = 3078


class ChatGPTTemporaryLiveSourceLockTests(unittest.TestCase):
    def test_actual_launcher_holds_exact_source_locks_while_pinned_controller_is_live_on_windows(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows FileShare/controller semantics are required")
        pwsh = shutil.which("pwsh")
        git = shutil.which("git")
        if pwsh is None or git is None:
            self.skipTest("pwsh/git are unavailable")

        launcher_text = SCRIPT.read_text(encoding="utf-8")

        def ps_literal(value: str | Path) -> str:
            return "'" + str(value).replace("'", "''") + "'"

        def port_is_open() -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.5)
                return probe.connect_ex(("127.0.0.1", PINNED_PORT)) == 0

        self.assertFalse(port_is_open(), "pinned controller port 3078 is already occupied")

        repo_root_assignment = "$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path"
        controller_boundary = (
            "        -RedirectStandardError $controllerStderr\n\n"
            "    $healthUri = 'http://127.0.0.1:3078/health'"
        )
        self.assertEqual(1, launcher_text.count(repo_root_assignment))
        self.assertEqual(1, launcher_text.count(controller_boundary))
        self.assertIn("'--port', '3078',", launcher_text)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task = root / "task.txt"
            task.write_text(
                "Return the bounded fixture fact without changing state.\n",
                encoding="utf-8",
            )
            local_app_data = root / "localappdata"
            local_app_data.mkdir()
            ready = root / "launcher-locks-ready.json"
            release = root / "launcher-locks-release.txt"
            instrumented = root / "instrumented-launcher.ps1"

            probe = r'''        -RedirectStandardError $controllerStderr

    $probeReady = [string]$env:CAP_AGENT_SESSION_TEST_LOCK_READY
    $probeRelease = [string]$env:CAP_AGENT_SESSION_TEST_LOCK_RELEASE
    $probeHealthUri = 'http://127.0.0.1:3078/health'
    $probeDeadline = (Get-Date).AddSeconds(20)
    $probeHealth = $null
    while ($true) {
        if ($controller.HasExited) {
            throw ('CAP_AGENT_SESSION_TEST_CONTROLLER_EXITED_BEFORE_HEALTH=' + $controller.ExitCode)
        }
        try {
            $candidate = Invoke-RestMethod -Uri $probeHealthUri -Method Get -TimeoutSec 2
            if (
                [string]$candidate.adapter_id -eq 'chatgpt-temporary' -and
                [string]$candidate.status -eq 'preflight'
            ) {
                $probeHealth = $candidate
                break
            }
        }
        catch {
            # The exact controller may still be starting. Retry only while it remains alive.
        }
        if ((Get-Date) -gt $probeDeadline) {
            throw 'CAP_AGENT_SESSION_TEST_CONTROLLER_HEALTH_TIMEOUT'
        }
        Start-Sleep -Milliseconds 50
    }
    if ($controller.HasExited) {
        throw ('CAP_AGENT_SESSION_TEST_CONTROLLER_EXITED_AFTER_HEALTH=' + $controller.ExitCode)
    }
    Write-JsonUtf8NoBom -Path $probeReady -Value ([ordered]@{
        runtime_archive_path = $runtimeArchivePath
        extension_path = $extensionPath
        preflight_path = $preflightPath
        controller_id = $controller.Id
        controller_adapter_id = [string]$probeHealth.adapter_id
        controller_status = [string]$probeHealth.status
    })
    $probeDeadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $probeRelease -PathType Leaf)) {
        if ($controller.HasExited) {
            throw ('CAP_AGENT_SESSION_TEST_CONTROLLER_EXITED_DURING_LOCK_PROBE=' + $controller.ExitCode)
        }
        if ((Get-Date) -gt $probeDeadline) {
            throw 'CAP_AGENT_SESSION_TEST_LOCK_RELEASE_TIMEOUT'
        }
        Start-Sleep -Milliseconds 50
    }
    if ($controller.HasExited) {
        throw ('CAP_AGENT_SESSION_TEST_CONTROLLER_EXITED_BEFORE_RELEASE=' + $controller.ExitCode)
    }
    throw 'CAP_AGENT_SESSION_TEST_STOP_AFTER_LIVE_CONTROLLER_PROBE'

    $healthUri = 'http://127.0.0.1:3078/health' '''

            instrumented_text = launcher_text.replace(
                repo_root_assignment,
                f"$RepoRoot = {ps_literal(ROOT)}",
                1,
            ).replace(
                controller_boundary,
                probe,
                1,
            )
            self.assertIn("'--port', '3078',", instrumented_text)
            self.assertLess(
                instrumented_text.index("CAP_AGENT_SESSION_TEST_LOCK_READY"),
                instrumented_text.index("Start-Process $preflightUrl"),
            )
            instrumented.write_text(instrumented_text, encoding="utf-8")

            head = subprocess.check_output(
                [git, "-C", str(ROOT), "rev-parse", "HEAD"],
                text=True,
            ).strip().lower()
            env = dict(os.environ)
            env["LOCALAPPDATA"] = str(local_app_data)
            env["CAP_AGENT_SESSION_TEST_LOCK_READY"] = str(ready)
            env["CAP_AGENT_SESSION_TEST_LOCK_RELEASE"] = str(release)

            process = subprocess.Popen(
                [
                    pwsh,
                    "-NoProfile",
                    "-File",
                    str(instrumented),
                    "-TaskFile",
                    str(task),
                    "-ExpectedHead",
                    head,
                    "-TimeoutSeconds",
                    "60",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout = ""
            stderr = ""
            locked_paths: list[Path] = []
            try:
                deadline = time.monotonic() + 35
                while not ready.is_file():
                    if process.poll() is not None:
                        stdout, stderr = process.communicate()
                        self.fail(f"instrumented launcher exited before live-controller probe: {stdout}{stderr}")
                    if time.monotonic() >= deadline:
                        self.fail("timed out waiting for live exact-controller/source-lock probe")
                    time.sleep(0.05)

                probe_state = json.loads(ready.read_text(encoding="utf-8"))
                self.assertEqual("chatgpt-temporary", probe_state["controller_adapter_id"])
                self.assertEqual("preflight", probe_state["controller_status"])
                self.assertGreater(int(probe_state["controller_id"]), 0)

                with urllib.request.urlopen(
                    f"http://127.0.0.1:{PINNED_PORT}/health",
                    timeout=3,
                ) as response:
                    self.assertEqual(200, response.status)
                    health = json.loads(response.read().decode("utf-8"))
                self.assertEqual("chatgpt-temporary", health["adapter_id"])
                self.assertEqual("preflight", health["status"])

                preflight_path = Path(probe_state["preflight_path"])
                self.assertTrue(preflight_path.is_file())
                preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
                self.assertEqual("chatgpt-temporary", preflight["adapter_id"])
                self.assertEqual(head, preflight["expected_runtime_head"])

                runtime_archive = Path(probe_state["runtime_archive_path"])
                extension_asset = Path(probe_state["extension_path"]) / "content.js"
                locked_paths = [runtime_archive, extension_asset]
                self.assertTrue(runtime_archive.is_file())
                self.assertTrue(extension_asset.is_file())
                originals = {path: path.read_bytes() for path in locked_paths}

                for target in locked_paths:
                    with self.assertRaises(OSError, msg=f"live launcher allowed write to {target.name}"):
                        with target.open("r+b") as handle:
                            handle.write(b"mutated")
                    with self.assertRaises(OSError, msg=f"live launcher allowed delete of {target.name}"):
                        target.unlink()
                    self.assertEqual(originals[target], target.read_bytes())

                with urllib.request.urlopen(
                    f"http://127.0.0.1:{PINNED_PORT}/health",
                    timeout=3,
                ) as response:
                    health_after_mutation_attempts = json.loads(response.read().decode("utf-8"))
                self.assertEqual("preflight", health_after_mutation_attempts["status"])
            finally:
                release.write_text("release", encoding="utf-8")
                try:
                    stdout, stderr = process.communicate(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    self.fail(f"instrumented launcher did not terminate: {stdout}{stderr}")

            self.assertNotEqual(0, process.returncode)
            self.assertIn("CAP_AGENT_SESSION_TEST_STOP_AFTER_LIVE_CONTROLLER_PROBE", stdout + stderr)

            for target in locked_paths:
                target.write_bytes(b"changed-after-launcher-finally")
                self.assertEqual(b"changed-after-launcher-finally", target.read_bytes())
                target.unlink()
                self.assertFalse(target.exists())

            deadline = time.monotonic() + 5
            while port_is_open() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(port_is_open(), "pinned controller remained live after launcher cleanup")


if __name__ == "__main__":
    unittest.main()
