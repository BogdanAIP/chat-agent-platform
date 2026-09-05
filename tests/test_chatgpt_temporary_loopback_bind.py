from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

from tests.test_chatgpt_temporary_controller import (
    TASK,
    expected_runtime_attestation,
    identity_dict,
)


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "launch-chatgpt-temporary-worker.ps1"
PINNED_PORT = 3078


def _port_is_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        return probe.connect_ex(("127.0.0.1", PINNED_PORT)) == 0


class ChatGPTTemporaryLoopbackBindTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertFalse(_port_is_open(), "pinned controller port 3078 is already occupied")

    def test_controller_bind_failure_precedes_preflight_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            identity_path = root / "identity.json"
            task_path = root / "task.txt"
            runtime_attestation_path = root / "expected-runtime-attestation.json"
            state_root = root / "private-state"
            output_dir = root / "output"
            identity_path.write_text(json.dumps(identity_dict()), encoding="utf-8")
            task_path.write_text(TASK, encoding="utf-8")
            runtime_attestation_path.write_text(
                json.dumps(expected_runtime_attestation()),
                encoding="utf-8",
            )

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rogue:
                rogue.bind(("127.0.0.1", PINNED_PORT))
                rogue.listen(1)
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "runtime.agent_sessions.chatgpt_temporary_authenticated_controller",
                        "--identity-json",
                        str(identity_path),
                        "--task-file",
                        str(task_path),
                        "--runtime-attestation-json",
                        str(runtime_attestation_path),
                        "--state-root",
                        str(state_root),
                        "--output-dir",
                        str(output_dir),
                        "--port",
                        str(PINNED_PORT),
                        "--timeout-seconds",
                        "60",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=30,
                )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn(
                "adapter loopback bind failed before preflight publication",
                completed.stdout + completed.stderr,
            )
            self.assertFalse((output_dir / "preflight.json").exists())
            self.assertFalse((output_dir / "launch.json").exists())
            self.assertFalse((output_dir / "result.json").exists())

    def test_windows_launcher_rejects_prebound_pinned_port_before_browser_preflight(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows Get-NetTCPConnection launcher proof is required")
        pwsh = shutil.which("pwsh")
        git = shutil.which("git")
        if pwsh is None or git is None:
            self.skipTest("pwsh/git are unavailable")

        head = subprocess.check_output(
            [git, "-C", str(ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip().lower()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task = root / "task.txt"
            task.write_text(
                "Return the bounded fixture fact without changing state.\n",
                encoding="utf-8",
            )
            local_app_data = root / "localappdata"
            local_app_data.mkdir()
            env = dict(os.environ)
            env["LOCALAPPDATA"] = str(local_app_data)
            task_sha = hashlib.sha256(task.read_bytes()).hexdigest()
            output_dir = (
                local_app_data
                / "ChatAgentPlatform"
                / "agent-sessions"
                / "qualification"
                / f"{head[:12]}-{task_sha[:12]}"
            )

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rogue:
                rogue.bind(("127.0.0.1", PINNED_PORT))
                rogue.listen(1)
                completed = subprocess.run(
                    [
                        pwsh,
                        "-NoProfile",
                        "-File",
                        str(LAUNCHER),
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
                    capture_output=True,
                    check=False,
                    timeout=90,
                )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("PINNED_CONTROLLER_PORT_OCCUPIED", completed.stdout + completed.stderr)
            self.assertFalse((output_dir / "preflight.json").exists())
            self.assertFalse((output_dir / "launch.json").exists())
            self.assertFalse((output_dir / "result.json").exists())

            deadline = time.monotonic() + 5
            while _port_is_open() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(_port_is_open(), "pinned port remained occupied after test cleanup")


if __name__ == "__main__":
    unittest.main()
