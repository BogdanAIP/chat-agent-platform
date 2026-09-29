from __future__ import annotations

from datetime import datetime, timezone
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
        updater = local_app_data / "ChatAgentPlatform" / "app" / "scripts" / "chat-platform-update.ps1"
        updater.parent.mkdir(parents=True)
        updater.write_text("# fixture\n", encoding="utf-8")
        return local_app_data

    def _request_record(self, local: Path, request_id: str, accepted_at: str) -> None:
        paths = platform_update._paths(local)
        platform_update._write_atomic_json(
            platform_update._request_path(paths, request_id),
            {
                "schema_version": 1,
                "request_id": request_id,
                "status": "accepted",
                "accepted_at": accepted_at,
                "repository": "BogdanAIP/chat-agent-platform",
                "branch": "main",
            },
        )

    def test_request_schema_is_closed_and_status_requires_request_id(self) -> None:
        request_id = "a" * 32
        with patch.object(platform_update.os, "name", "nt"), tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            with self.assertRaisesRegex(ValueError, "only procedure and action"):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "check", "request_id": request_id},
                    local_app_data=local,
                )
            with self.assertRaisesRegex(ValueError, "request_id"):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status"},
                    local_app_data=local,
                )
            with self.assertRaisesRegex(ValueError, "unsupported"):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "arbitrary"},
                    local_app_data=local,
                )

    def test_check_invokes_only_installed_updater_with_fixed_argv(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"schema_version": 1, "action": "check", "status": "current", "repository": "BogdanAIP/chat-agent-platform", "branch": "main"}) + "\n",
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
        self.assertEqual(["-Action", "Check"], argv[-2:])
        self.assertIs(run.call_args.kwargs["shell"], False)

    def test_request_update_persists_random_correlation_and_detaches_trampoline(self) -> None:
        process = Mock()
        process.pid = 4242
        request_id = "b" * 32
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            with (
                patch.object(platform_update.os, "name", "nt"),
                patch.object(platform_update, "_python", return_value=r"C:\Python\python.exe"),
                patch.object(platform_update.secrets, "token_hex", return_value=request_id),
                patch.object(platform_update.subprocess, "Popen", return_value=process) as popen,
            ):
                result = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "request_update"},
                    local_app_data=local,
                )
                record = platform_update._read_bounded_json(
                    platform_update._request_path(platform_update._paths(local), request_id)
                )
        self.assertEqual("accepted", result["status"])
        self.assertEqual(request_id, result["request_id"])
        self.assertEqual(4242, result["process_id"])
        self.assertEqual(
            {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": request_id},
            result["reconcile_with"],
        )
        self.assertEqual(request_id, record["request_id"])
        argv = popen.call_args.args[0]
        self.assertEqual(r"C:\Python\python.exe", argv[0])
        self.assertTrue(argv[1].endswith("platform_update.py"))
        self.assertEqual([platform_update._UPDATE_CHILD_FLAG, request_id], argv[-2:])
        self.assertIs(popen.call_args.kwargs["shell"], False)
        flags = popen.call_args.kwargs["creationflags"]
        self.assertNotEqual(0, flags & getattr(subprocess, "DETACHED_PROCESS", 0x00000008))
        self.assertNotEqual(0, flags & getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200))
        self.assertNotEqual(0, flags & getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000))

    def test_trampoline_writes_request_specific_correlated_receipt(self) -> None:
        request_id = "c" * 32
        process = Mock()
        process.pid = 5000
        process.wait.return_value = 0
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            paths = platform_update._paths(local)
            self._request_record(local, request_id, "2026-09-29T04:00:00+00:00")
            platform_update._write_atomic_json(
                platform_update._updater_result_path(paths, request_id),
                {
                    "schema_version": 1,
                    "request_id": request_id,
                    "process_id": 5000,
                    "action": "update",
                    "status": "current",
                    "completed_at": "2026-09-29T04:00:01+00:00",
                },
            )
            with (
                patch.object(platform_update.os, "name", "nt"),
                patch.object(platform_update.shutil, "which", return_value=r"C:\Program Files\PowerShell\7\pwsh.exe"),
                patch.object(platform_update.subprocess, "Popen", return_value=process) as popen,
            ):
                code = platform_update._run_installed_updater_child(request_id, local_app_data=local)
            receipt = platform_update._read_bounded_json(platform_update._receipt_path(paths, request_id))
        self.assertEqual(0, code)
        self.assertTrue(receipt["correlation_verified"])
        self.assertEqual(5000, receipt["updater_process_id"])
        self.assertEqual("current", receipt["updater_result"]["status"])
        self.assertEqual(["-RequestId", request_id], popen.call_args.args[0][-2:])

    def test_trampoline_ignores_shared_global_result(self) -> None:
        request_id = "d" * 32
        process = Mock()
        process.pid = 6000
        process.wait.return_value = 0
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            paths = platform_update._paths(local)
            self._request_record(local, request_id, "2026-09-29T04:00:00+00:00")
            paths["result"].parent.mkdir(parents=True, exist_ok=True)
            paths["result"].write_text(json.dumps({
                "schema_version": 1,
                "request_id": "9" * 32,
                "process_id": 9999,
                "action": "update",
                "status": "updated",
                "completed_at": "2026-09-29T04:00:02+00:00",
            }), encoding="utf-8")
            platform_update._write_atomic_json(
                platform_update._updater_result_path(paths, request_id),
                {
                    "schema_version": 1,
                    "request_id": request_id,
                    "process_id": 6000,
                    "action": "update",
                    "status": "current",
                    "completed_at": "2026-09-29T04:00:01+00:00",
                },
            )
            with (
                patch.object(platform_update.os, "name", "nt"),
                patch.object(platform_update.shutil, "which", return_value=r"C:\Program Files\PowerShell\7\pwsh.exe"),
                patch.object(platform_update.subprocess, "Popen", return_value=process),
            ):
                code = platform_update._run_installed_updater_child(request_id, local_app_data=local)
            receipt = platform_update._read_bounded_json(platform_update._receipt_path(paths, request_id))
        self.assertEqual(0, code)
        self.assertTrue(receipt["correlation_verified"])
        self.assertEqual(6000, receipt["updater_result"]["process_id"])

    def test_status_reads_only_request_specific_receipt(self) -> None:
        request_id = "e" * 32
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            paths = platform_update._paths(local)
            self._request_record(local, request_id, datetime.now(timezone.utc).isoformat())
            paths["result"].parent.mkdir(parents=True, exist_ok=True)
            paths["result"].write_text(json.dumps({
                "schema_version": 1,
                "process_id": 999,
                "action": "update",
                "status": "updated",
                "completed_at": "2026-09-29T03:00:00+00:00",
            }), encoding="utf-8")
            with patch.object(platform_update.os, "name", "nt"):
                pending = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": request_id},
                    local_app_data=local,
                )
            self.assertEqual("pending", pending["status"])
            self.assertIsNone(pending["receipt"])
            platform_update._write_atomic_json(
                platform_update._receipt_path(paths, request_id),
                {
                    "schema_version": 1,
                    "request_id": request_id,
                    "status": "completed",
                    "correlation_verified": True,
                    "updater_process_id": 5000,
                    "updater_exit_code": 0,
                    "updater_result": {"status": "current", "process_id": 5000},
                },
            )
            with patch.object(platform_update.os, "name", "nt"):
                completed = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": request_id},
                    local_app_data=local,
                )
        self.assertEqual("completed", completed["status"])
        self.assertEqual(5000, completed["receipt"]["updater_result"]["process_id"])

    def test_status_recovers_receipt_from_request_specific_updater_result(self) -> None:
        request_id = "1" * 32
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            paths = platform_update._paths(local)
            self._request_record(local, request_id, "2026-09-29T04:00:00+00:00")
            platform_update._write_atomic_json(
                platform_update._updater_result_path(paths, request_id),
                {
                    "schema_version": 1,
                    "request_id": request_id,
                    "process_id": 7000,
                    "action": "update",
                    "status": "current",
                    "completed_at": "2026-09-29T04:00:01+00:00",
                },
            )
            with patch.object(platform_update.os, "name", "nt"):
                result = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": request_id},
                    local_app_data=local,
                )
            receipt = platform_update._read_bounded_json(platform_update._receipt_path(paths, request_id))
        self.assertEqual("completed", result["status"])
        self.assertTrue(receipt["correlation_verified"])
        self.assertTrue(receipt["recovered_by_status"])
        self.assertEqual(7000, receipt["updater_process_id"])
        self.assertIsNone(receipt["updater_exit_code"])

    def test_status_stops_reporting_pending_after_reconciliation_deadline(self) -> None:
        request_id = "2" * 32
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            self._request_record(local, request_id, "2000-01-01T00:00:00+00:00")
            with patch.object(platform_update.os, "name", "nt"):
                result = platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": request_id},
                    local_app_data=local,
                )
        self.assertEqual("manual_recovery_required", result["status"])
        self.assertEqual("request_specific_updater_result_unavailable", result["reason"])
        self.assertIsNone(result["receipt"])

    def test_unknown_or_malformed_status_request_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            with patch.object(platform_update.os, "name", "nt"), self.assertRaisesRegex(ValueError, "32-character"):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": "../escape"},
                    local_app_data=local,
                )
            with patch.object(platform_update.os, "name", "nt"), self.assertRaisesRegex(ValueError, "unknown"):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "status", "request_id": "f" * 32},
                    local_app_data=local,
                )

    def test_request_history_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            local = self._layout(Path(temporary))
            paths = platform_update._paths(local)
            paths["requests"].mkdir(parents=True)
            for index in range(platform_update._REQUEST_HISTORY_LIMIT):
                rid = f"{index:032x}"
                platform_update._write_atomic_json(
                    platform_update._request_path(paths, rid),
                    {"schema_version": 1, "request_id": rid, "status": "accepted", "accepted_at": "2026-09-29T04:00:00+00:00"},
                )
            with patch.object(platform_update.os, "name", "nt"), self.assertRaisesRegex(RuntimeError, "history limit"):
                platform_update.run_platform_update(
                    {"procedure": platform_update.PROCEDURE_ID, "action": "request_update"},
                    local_app_data=local,
                )


if __name__ == "__main__":
    unittest.main()
