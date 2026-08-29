from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.verified_workspace_artifact as workspace_artifact
from runtime.control_plane.verified_workspace_artifact import (
    PROCEDURE_ID,
    QUALIFICATION_ADMISSION,
    run_verified_workspace_artifact,
)
from runtime.control_plane.working_state import WorkingState


class Stage263CWorkspaceWorkingStateTests(unittest.TestCase):
    def request(self, name: str, content: str, task_id: str | None = None) -> dict:
        value = {
            "procedure": PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
        }
        if task_id is not None:
            value["resume_task_id"] = task_id
        return value

    def checkpoint(self, state_root: Path) -> dict:
        files = list(state_root.glob("*.json"))
        self.assertEqual(len(files), 1)
        return json.loads(files[0].read_text(encoding="utf-8"))

    def execute(
        self,
        request: dict,
        *,
        workspace: Path,
        state: Path,
    ) -> dict:
        return run_verified_workspace_artifact(
            request,
            workspace_root=workspace,
            state_root=state,
            candidate_admission=QUALIFICATION_ADMISSION,
        )

    def staging_path(self, workspace: Path, name: str, task_id: str) -> Path:
        return (
            workspace
            / ".chat-agent-platform"
            / "stage26-3a"
            / f".{name}.{task_id}.staging"
        )

    def target_path(self, workspace: Path, name: str) -> Path:
        return workspace / ".chat-agent-platform" / "stage26-3a" / name

    def test_stage_create_write_ahead_is_durable_before_physical_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            def crash_before_delivery(path: Path, data: bytes) -> None:
                checkpoint = self.checkpoint(state)
                working = WorkingState.from_dict(checkpoint["working_state"])
                prepared = checkpoint["prepared_intent"]
                self.assertEqual(checkpoint["action_count"], 0)
                self.assertEqual(working.attempts, ())
                self.assertEqual(working.unresolved_attempts(), ())
                self.assertIsInstance(prepared, dict)
                self.assertTrue(prepared["operation_id"].endswith(":stage_create"))
                self.assertEqual(prepared["action_count_before"], 0)
                self.assertFalse(path.exists())
                raise SystemExit("simulated crash before delivery")

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=crash_before_delivery,
            ):
                with self.assertRaisesRegex(SystemExit, "before delivery"):
                    self.execute(
                        self.request("write-ahead.txt", "DATA"),
                        workspace=workspace,
                        state=state,
                    )

            checkpoint = self.checkpoint(state)
            working = WorkingState.from_dict(checkpoint["working_state"])
            self.assertEqual(checkpoint["status"], "running")
            self.assertEqual(working.attempts, ())
            self.assertIsInstance(checkpoint["prepared_intent"], dict)

    def test_resume_after_crash_before_stage_delivery_reconciles_then_completes(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=SystemExit("simulated crash before delivery"),
            ):
                with self.assertRaises(SystemExit):
                    self.execute(
                        self.request("resume-before.txt", "RECOVER"),
                        workspace=workspace,
                        state=state,
                    )

            task_id = self.checkpoint(state)["task_id"]
            result = self.execute(
                self.request("resume-before.txt", "RECOVER", task_id),
                workspace=workspace,
                state=state,
            )

            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["resumed"])
            self.assertEqual(result["action_count"], 3)
            checkpoint = self.checkpoint(state)
            working = WorkingState.from_dict(checkpoint["working_state"])
            self.assertFalse(working.unresolved_attempts())
            self.assertIsNone(checkpoint["prepared_intent"])
            self.assertEqual(
                working.reconciliations[0].status.value,
                "confirmed_not_applied",
            )

    def test_resume_after_stage_delivery_repairs_receipt_without_redelivery(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            def create_then_crash(path: Path, data: bytes) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                raise SystemExit("simulated crash after stage delivery")

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=create_then_crash,
            ):
                with self.assertRaisesRegex(SystemExit, "stage delivery"):
                    self.execute(
                        self.request("resume-stage.txt", "APPLIED"),
                        workspace=workspace,
                        state=state,
                    )

            task_id = self.checkpoint(state)["task_id"]
            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("stage create was redelivered"),
            ) as create_mock:
                result = self.execute(
                    self.request("resume-stage.txt", "APPLIED", task_id),
                    workspace=workspace,
                    state=state,
                )

            create_mock.assert_not_called()
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertEqual(
                [receipt["transition_id"] for receipt in result["transition_receipts"]],
                ["stage_create", "final_create", "staging_cleanup"],
            )
            checkpoint = self.checkpoint(state)
            working = WorkingState.from_dict(checkpoint["working_state"])
            self.assertEqual(
                working.reconciliations[0].status.value,
                "confirmed_applied",
            )

    def test_resume_after_final_link_delivery_never_relinks(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            def link_then_crash(source: Path, target: Path) -> None:
                os.link(source, target)
                raise SystemExit("simulated crash after final link")

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=link_then_crash,
            ):
                with self.assertRaisesRegex(SystemExit, "final link"):
                    self.execute(
                        self.request("resume-final.txt", "LINKED"),
                        workspace=workspace,
                        state=state,
                    )

            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging_path(workspace, "resume-final.txt", task_id)
            target = self.target_path(workspace, "resume-final.txt")
            self.assertTrue(staging.exists())
            self.assertTrue(target.exists())
            self.assertEqual(os.stat(staging).st_ino, os.stat(target).st_ino)

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("final link was redelivered"),
            ) as link_mock:
                result = self.execute(
                    self.request("resume-final.txt", "LINKED", task_id),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())

    def test_resume_after_cleanup_delivery_finishes_without_second_delete(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_delete_pin = workspace_artifact.pin_file_for_verified_delete

            @contextmanager
            def delete_then_crash(path: Path, *, workspace_root: Path | None = None):
                with real_delete_pin(path, workspace_root=workspace_root) as mark_delete:
                    def mark_then_crash() -> None:
                        mark_delete()
                        raise SystemExit("simulated crash after cleanup")

                    yield mark_then_crash

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                new=delete_then_crash,
            ):
                with self.assertRaisesRegex(SystemExit, "after cleanup"):
                    self.execute(
                        self.request("resume-cleanup.txt", "CLEAN"),
                        workspace=workspace,
                        state=state,
                    )

            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging_path(workspace, "resume-cleanup.txt", task_id)
            target = self.target_path(workspace, "resume-cleanup.txt")
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                side_effect=AssertionError("cleanup was redelivered"),
            ) as delete_mock:
                result = self.execute(
                    self.request("resume-cleanup.txt", "CLEAN", task_id),
                    workspace=workspace,
                    state=state,
                )

            delete_mock.assert_not_called()
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertTrue(target.exists())

    def test_same_content_different_identity_does_not_prove_final_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            def external_copy_then_crash(source: Path, target: Path) -> None:
                target.write_bytes(source.read_bytes())
                self.assertNotEqual(os.stat(source).st_ino, os.stat(target).st_ino)
                raise SystemExit("external same-content target")

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=external_copy_then_crash,
            ):
                with self.assertRaisesRegex(SystemExit, "same-content"):
                    self.execute(
                        self.request("identity-conflict.txt", "SAME"),
                        workspace=workspace,
                        state=state,
                    )

            task_id = self.checkpoint(state)["task_id"]
            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("conflicted final create must not retry"),
            ) as link_mock:
                result = self.execute(
                    self.request("identity-conflict.txt", "SAME", task_id),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "resume_reconciliation_unknown")

    def test_completed_checkpoint_records_same_identity_for_hardlinked_final(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            result = self.execute(
                self.request("hardlink.txt", "IDENTITY"),
                workspace=workspace,
                state=state,
            )

            self.assertEqual(result["status"], "completed")
            checkpoint = self.checkpoint(state)
            self.assertEqual(
                checkpoint["staging_file_identity"],
                checkpoint["target_file_identity"],
            )
            target = self.target_path(workspace, "hardlink.txt")
            self.assertTrue(
                workspace_artifact._same_file_identity(
                    target,
                    checkpoint["target_file_identity"],
                )
            )

    def test_task_lock_blocks_duplicate_runner_before_checkpoint_load_or_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=SystemExit("prepare a resumable task"),
            ):
                with self.assertRaises(SystemExit):
                    self.execute(
                        self.request("locked.txt", "LOCK"),
                        workspace=workspace,
                        state=state,
                    )
            task_id = self.checkpoint(state)["task_id"]
            lock = workspace_artifact._acquire_task_lock(state, task_id)
            try:
                with patch.object(
                    workspace_artifact,
                    "_load_checkpoint",
                    side_effect=AssertionError("duplicate runner must not load checkpoint"),
                ) as load_mock, patch.object(
                    workspace_artifact,
                    "_exclusive_create_file",
                    side_effect=AssertionError("duplicate runner must not mutate"),
                ) as create_mock:
                    with self.assertRaisesRegex(BlockingIOError, "task_already_running"):
                        self.execute(
                            self.request("locked.txt", "LOCK", task_id),
                            workspace=workspace,
                            state=state,
                        )
                load_mock.assert_not_called()
                create_mock.assert_not_called()
            finally:
                lock.close()

    def test_task_lock_is_released_when_holder_process_terminates(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state = Path(state_dir)
            task_id = "a" * 32
            script = (
                "import sys,time; from pathlib import Path; "
                "from runtime.control_plane.verified_workspace_artifact import _acquire_task_lock; "
                "lock=_acquire_task_lock(Path(sys.argv[1]),sys.argv[2]); "
                "print('READY', flush=True); time.sleep(30)"
            )
            proc = subprocess.Popen(
                [sys.executable, "-c", script, str(state), task_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(proc.stdout.readline().strip(), "READY")
                with self.assertRaises(BlockingIOError):
                    workspace_artifact._acquire_task_lock(state, task_id)
            finally:
                proc.kill()
                proc.wait(timeout=10)
            lock = workspace_artifact._acquire_task_lock(state, task_id)
            lock.close()

    def test_tampered_working_state_fails_closed_before_resume_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=SystemExit("simulated crash"),
            ):
                with self.assertRaises(SystemExit):
                    self.execute(
                        self.request("tamper.txt", "DATA"),
                        workspace=workspace,
                        state=state,
                    )

            files = list(state.glob("*.json"))
            self.assertEqual(len(files), 1)
            checkpoint = json.loads(files[0].read_text(encoding="utf-8"))
            task_id = checkpoint["task_id"]
            checkpoint["working_state"]["actor_ref"] = "foreign-actor"
            files[0].write_text(json.dumps(checkpoint), encoding="utf-8")

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("mutation must not run"),
            ) as create_mock:
                with self.assertRaises(ValueError):
                    self.execute(
                        self.request("tamper.txt", "DATA", task_id),
                        workspace=workspace,
                        state=state,
                    )

            create_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
