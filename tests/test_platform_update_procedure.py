from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import runtime.control_plane.platform_update as platform_update


class PlatformUpdateProcedureTests(unittest.TestCase):
    def _layout(self, root: Path) -> Path:
        local_app_data = root / "Local"
        updater = (
            local_app_data
            / "ChatAgentPlatform"
            / "app"
            / "scripts"
            / "chat-platform-update.ps1"
        )
        updater.parent.mkdir(parents=True)
        updater.write_text("# fixture\n", encoding="utf-8")
        return local_app_data

    def test_request_schema_is_closed(self) -> None:
        with (
            patch.object(platform_update.os, "name", "nt"),
            tempfile.TemporaryDirectory() as temporary,
        ):
            local = self._layout(Path(temporary))
            with self.assertRaisesRegex(ValueError, "only procedure and action"):
                platform_update.run_platform_update(
                    {
                        "procedure": platform_update.PROCEDURE_ID,
                        "action": "status",
                        "command": "whoami",
                    },
                    local_app_data=local,
                )
            with self.assertRaisesRegex(ValueError, "unsupported"):
                platform_update.run_platform_update(
                    {
                        "procedure": platform_update.PROCEDURE_ID,
                        "action": "arbitrary",
                    },
                    local_app_data=local,
                )

    def test_check_invokes_only_installed_updater_with_fixed_argv(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "schema_version": 1,
                    "action": "check",
                    "status": "current",
                    "repository": "BogdanAIP/chat-agent-platform",
                    "branch": "main",
                }
            )
            + "\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            with (
                patch.object(platform_update.os, "name", "nt"),
                patch.object(platform_update.shutil, "which", return_value=r"C:\Program Files\PowerShell\7\pwsh.exe"),
                patch.object(platform_update.subprocess, "run", return_value=completed) as run,
            ):
                result = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "check"},
                    local_app_data=local,
                )

        self.assertEqual("completed", result["status"])
        self.assertEqual("current", result["updater"]["status"])
        argv = run.call_args.args[0]
        self.assertEqual(r"C:\Program Files\PowerShell\7\pwsh.exe", argv[0])
        self.assertEqual(
            ["-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"],
            argv[1:6],
        )
        self.assertTrue(argv[6].endswith("ChatAgentPlatform\\app\\scripts\\chat-platform-update.ps1")
                        or argv[6].endswith("ChatAgentPlatform/app/scripts/chat-platform-update.ps1"))
        self.assertEqual(["-Action", "Check"], argv[-2:])
        self.assertIs(run.call_args.kwargs["shell"], False)

    def test_request_update_detaches_fixed_updater_and_reports_only_acceptance(self) -> None:
        process = Mock()
        process.pid = 4242
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            with (
                patch.object(platform_update.os, "name", "nt"),
                patch.object(platform_update.shutil, "which", return_value=r"C:\Program Files\PowerShell\7\pwsh.exe"),
                patch.object(platform_update.subprocess, "Popen", return_value=process) as popen,
            ):
                result = platform_update.run_platform_update(
                    {
                        "procedure": platform_update.PROCEDURE_ID,
                        "action": "request_update",
                    },
                    local_app_data=local,
                )

        self.assertEqual(
            {
                "schema_version": 1,
                "status": "accepted",
                "action": "request_update",
                "process_id": 4242,
                "outcome_verified": False,
                "reconcile_with": "platform_update_v1:status",
            },
            result,
        )
        argv = popen.call_args.args[0]
        self.assertEqual(["-Action", "Update"], argv[-2:])
        self.assertIs(popen.call_args.kwargs["shell"], False)
        self.assertIs(popen.call_args.kwargs["close_fds"], True)
        self.assertIs(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
        self.assertIs(popen.call_args.kwargs["stderr"], subprocess.DEVNULL)
        flags = popen.call_args.kwargs["creationflags"]
        self.assertNotEqual(0, flags & getattr(subprocess, "DETACHED_PROCESS", 0x00000008))
        self.assertNotEqual(0, flags & getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200))
        self.assertNotEqual(0, flags & getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000))

    def test_status_reads_only_fixed_bounded_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            state_dir = local / "ChatAgentPlatform" / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "platform-update.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "repository": "BogdanAIP/chat-agent-platform",
                        "branch": "main",
                        "status": "installing",
                    }
                ),
                encoding="utf-8",
            )
            (state_dir / "platform-update-result.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "action": "update",
                        "status": "updated",
                        "process_id": 101,
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(platform_update.os, "name", "nt"):
                result = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status"},
                    local_app_data=local,
                )

        self.assertEqual("completed", result["status"])
        self.assertEqual("installing", result["state"]["status"])
        self.assertEqual("updated", result["result"]["status"])

    def test_status_fails_closed_on_malformed_or_oversized_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            state_dir = local / "ChatAgentPlatform" / "state"
            state_dir.mkdir(parents=True)
            path = state_dir / "platform-update.json"
            path.write_text("{not-json", encoding="utf-8")
            with (
                patch.object(platform_update.os, "name", "nt"),
                self.assertRaisesRegex(RuntimeError, "invalid JSON"),
            ):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status"},
                    local_app_data=local,
                )

            path.write_text("x" * (platform_update._MAX_JSON_BYTES + 1), encoding="utf-8")
            with (
                patch.object(platform_update.os, "name", "nt"),
                self.assertRaisesRegex(RuntimeError, "exceeds"),
            ):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status"},
                    local_app_data=local,
                )


if __name__ == "__main__":
    unittest.main()
