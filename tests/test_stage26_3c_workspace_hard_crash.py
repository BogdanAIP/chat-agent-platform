from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.verified_workspace_artifact as workspace_artifact
from runtime.control_plane.verified_workspace_artifact import (
    MAX_ACTIONS,
    PROCEDURE_ID,
    PROCEDURE_STATUS,
    PROCEDURE_VERSION,
    QUALIFICATION_ADMISSION,
    run_verified_workspace_artifact,
)


ROOT = Path(__file__).resolve().parents[1]


class Stage263CWorkspaceHardCrashTests(unittest.TestCase):
    def request(self, name: str, content: str, task_id: str | None = None) -> dict:
        value = {
            "procedure": PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
        }
        if task_id is not None:
            value["resume_task_id"] = task_id
        return value

    def execute(self, request: dict, *, workspace: Path, state: Path) -> dict:
        return run_verified_workspace_artifact(
            request,
            workspace_root=workspace,
            state_root=state,
            candidate_admission=QUALIFICATION_ADMISSION,
        )

    def checkpoint(self, state: Path) -> dict:
        files = list(state.glob("*.json"))
        self.assertEqual(len(files), 1)
        return json.loads(files[0].read_text(encoding="utf-8"))

    def staging_path(self, workspace: Path, name: str, task_id: str) -> Path:
        return (
            workspace
            / ".chat-agent-platform"
            / "stage26-3a"
            / f".{name}.{task_id}.staging"
        )

    def target_path(self, workspace: Path, name: str) -> Path:
        return workspace / ".chat-agent-platform" / "stage26-3a" / name

    def run_hard_crash_child(
        self,
        *,
        workspace: Path,
        state: Path,
        mode: str,
        artifact_name: str,
        content: str,
    ) -> subprocess.CompletedProcess[str]:
        script = textwrap.dedent(
            """
            import os
            import sys
            from contextlib import contextmanager
            from pathlib import Path
            import runtime.control_plane.verified_workspace_artifact as wa

            workspace = Path(sys.argv[1])
            state = Path(sys.argv[2])
            mode = sys.argv[3]
            artifact_name = sys.argv[4]
            content = sys.argv[5]

            if mode == "before_stage":
                def crash_before_stage(path, data):
                    os._exit(80)
                wa._exclusive_create_file = crash_before_stage
            elif mode == "after_stage":
                def crash_after_stage(path, data):
                    with path.open("xb") as handle:
                        handle.write(data)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os._exit(81)
                wa._exclusive_create_file = crash_after_stage
            elif mode == "after_final":
                def crash_after_final(source, target):
                    os.link(source, target)
                    os._exit(82)
                wa._exclusive_link_file = crash_after_final
            elif mode == "after_cleanup":
                original_delete_pin = wa.pin_file_for_verified_delete
                @contextmanager
                def crash_after_cleanup(path, *, workspace_root=None):
                    with original_delete_pin(path, workspace_root=workspace_root) as mark_delete:
                        def mark_then_crash():
                            mark_delete()
                            os._exit(83)
                        yield mark_then_crash
                wa.pin_file_for_verified_delete = crash_after_cleanup
            elif mode == "before_final":
                def crash_before_final(source, target):
                    os._exit(84)
                wa._exclusive_link_file = crash_before_final
            elif mode == "before_cleanup":
                original_delete_pin = wa.pin_file_for_verified_delete
                @contextmanager
                def crash_before_cleanup(path, *, workspace_root=None):
                    with original_delete_pin(path, workspace_root=workspace_root):
                        def crash_before_mark():
                            os._exit(85)
                        yield crash_before_mark
                wa.pin_file_for_verified_delete = crash_before_cleanup
            elif mode in {"after_stage_commit", "after_final_commit", "after_cleanup_commit"}:
                original_write = wa._write_checkpoint
                expected_node = {
                    "after_stage_commit": "staged_verified",
                    "after_final_commit": "final_verified",
                    "after_cleanup_commit": "completed",
                }[mode]
                exit_code = {
                    "after_stage_commit": 86,
                    "after_final_commit": 87,
                    "after_cleanup_commit": 88,
                }[mode]
                def crash_after_transition_commit(state_root, task_state):
                    original_write(state_root, task_state)
                    if (
                        task_state.get("current_node") == expected_node
                        and task_state.get("prepared_intent") is None
                        and (
                            expected_node != "completed"
                            or task_state.get("status") == "completed"
                        )
                    ):
                        os._exit(exit_code)
                wa._write_checkpoint = crash_after_transition_commit
            else:
                raise RuntimeError("unknown crash mode")

            wa.run_verified_workspace_artifact(
                {
                    "procedure": wa.PROCEDURE_ID,
                    "artifact_name": artifact_name,
                    "content": content,
                },
                workspace_root=workspace,
                state_root=state,
                candidate_admission=wa.QUALIFICATION_ADMISSION,
            )
            raise RuntimeError("hard-crash hook was not reached")
            """
        )
        return subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(workspace),
                str(state),
                mode,
                artifact_name,
                content,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

    def assert_completed_once(self, result: dict) -> None:
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["action_count"], 3)
        self.assertEqual(
            [receipt["transition_id"] for receipt in result["transition_receipts"]],
            ["stage_create", "final_create", "staging_cleanup"],
        )

    def test_hard_process_death_before_stage_delivery_resumes_from_durable_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="before_stage",
                artifact_name="hard-before.txt",
                content="BEFORE",
            )
            self.assertEqual(child.returncode, 80, child.stderr)
            checkpoint = self.checkpoint(state)
            self.assertIsInstance(checkpoint["prepared_intent"], dict)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "stage_create")
            self.assertEqual(checkpoint["action_count"], 0)

            result = self.execute(
                self.request("hard-before.txt", "BEFORE", checkpoint["task_id"]),
                workspace=workspace,
                state=state,
            )
            self.assert_completed_once(result)

    def test_hard_process_death_before_final_delivery_resumes_from_durable_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="before_final",
                artifact_name="hard-before-final.txt",
                content="BEFORE_FINAL",
            )
            self.assertEqual(child.returncode, 84, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            self.assertEqual(checkpoint["current_node"], "staged_verified")
            self.assertEqual(checkpoint["action_count"], 1)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "final_create")
            self.assertTrue(self.staging_path(workspace, "hard-before-final.txt", task_id).exists())
            self.assertFalse(self.target_path(workspace, "hard-before-final.txt").exists())

            result = self.execute(
                self.request("hard-before-final.txt", "BEFORE_FINAL", task_id),
                workspace=workspace,
                state=state,
            )
            self.assert_completed_once(result)

    def test_hard_process_death_before_cleanup_delivery_resumes_from_durable_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="before_cleanup",
                artifact_name="hard-before-cleanup.txt",
                content="BEFORE_CLEANUP",
            )
            self.assertEqual(child.returncode, 85, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging_path(workspace, "hard-before-cleanup.txt", task_id)
            target = self.target_path(workspace, "hard-before-cleanup.txt")
            self.assertEqual(checkpoint["current_node"], "final_verified")
            self.assertEqual(checkpoint["action_count"], 2)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "staging_cleanup")
            self.assertTrue(staging.exists())
            self.assertTrue(target.exists())
            self.assertTrue(os.path.samefile(staging, target))

            result = self.execute(
                self.request("hard-before-cleanup.txt", "BEFORE_CLEANUP", task_id),
                workspace=workspace,
                state=state,
            )
            self.assert_completed_once(result)

    def test_hard_process_death_after_stage_delivery_repairs_without_redelivery(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="after_stage",
                artifact_name="hard-stage.txt",
                content="STAGE",
            )
            self.assertEqual(child.returncode, 81, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            self.assertTrue(self.staging_path(workspace, "hard-stage.txt", task_id).exists())

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("stage delivery repeated after hard crash"),
            ) as create_mock:
                result = self.execute(
                    self.request("hard-stage.txt", "STAGE", task_id),
                    workspace=workspace,
                    state=state,
                )
            create_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_hard_process_death_after_final_link_repairs_without_relink(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="after_final",
                artifact_name="hard-final.txt",
                content="FINAL",
            )
            self.assertEqual(child.returncode, 82, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging_path(workspace, "hard-final.txt", task_id)
            target = self.target_path(workspace, "hard-final.txt")
            self.assertTrue(staging.exists())
            self.assertTrue(target.exists())
            self.assertTrue(os.path.samefile(staging, target))

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("final delivery repeated after hard crash"),
            ) as link_mock:
                result = self.execute(
                    self.request("hard-final.txt", "FINAL", task_id),
                    workspace=workspace,
                    state=state,
                )
            link_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_hard_process_death_after_cleanup_repairs_without_second_delete(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="after_cleanup",
                artifact_name="hard-cleanup.txt",
                content="CLEANUP",
            )
            self.assertEqual(child.returncode, 83, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging_path(workspace, "hard-cleanup.txt", task_id)
            target = self.target_path(workspace, "hard-cleanup.txt")
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                side_effect=AssertionError("cleanup repeated after hard crash"),
            ) as delete_mock:
                result = self.execute(
                    self.request("hard-cleanup.txt", "CLEANUP", task_id),
                    workspace=workspace,
                    state=state,
                )
            delete_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_hard_process_death_after_stage_commit_resumes_without_recreating_stage(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="after_stage_commit",
                artifact_name="hard-stage-commit.txt",
                content="STAGE_COMMIT",
            )
            self.assertEqual(child.returncode, 86, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            self.assertEqual(checkpoint["current_node"], "staged_verified")
            self.assertEqual(checkpoint["action_count"], 1)
            self.assertIsNone(checkpoint["prepared_intent"])

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("committed stage was recreated"),
            ) as create_mock:
                result = self.execute(
                    self.request("hard-stage-commit.txt", "STAGE_COMMIT", task_id),
                    workspace=workspace,
                    state=state,
                )
            create_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_hard_process_death_after_final_commit_resumes_without_relink(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="after_final_commit",
                artifact_name="hard-final-commit.txt",
                content="FINAL_COMMIT",
            )
            self.assertEqual(child.returncode, 87, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            self.assertEqual(checkpoint["current_node"], "final_verified")
            self.assertEqual(checkpoint["action_count"], 2)
            self.assertIsNone(checkpoint["prepared_intent"])

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("committed final link was repeated"),
            ) as link_mock:
                result = self.execute(
                    self.request("hard-final-commit.txt", "FINAL_COMMIT", task_id),
                    workspace=workspace,
                    state=state,
                )
            link_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_hard_process_death_after_cleanup_commit_returns_completed_without_delete(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            child = self.run_hard_crash_child(
                workspace=workspace,
                state=state,
                mode="after_cleanup_commit",
                artifact_name="hard-cleanup-commit.txt",
                content="CLEANUP_COMMIT",
            )
            self.assertEqual(child.returncode, 88, child.stderr)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging_path(workspace, "hard-cleanup-commit.txt", task_id)
            target = self.target_path(workspace, "hard-cleanup-commit.txt")
            self.assertEqual(checkpoint["status"], "completed")
            self.assertEqual(checkpoint["current_node"], "completed")
            self.assertEqual(checkpoint["action_count"], 3)
            self.assertIsNone(checkpoint["prepared_intent"])
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                side_effect=AssertionError("committed cleanup was repeated"),
            ) as delete_mock:
                result = self.execute(
                    self.request("hard-cleanup-commit.txt", "CLEANUP_COMMIT", task_id),
                    workspace=workspace,
                    state=state,
                )
            delete_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_delivery_exception_after_applied_stage_repairs_receipt_and_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_create = workspace_artifact._exclusive_create_file

            def create_then_raise(path: Path, data: bytes) -> None:
                original_create(path, data)
                raise OSError("simulated acknowledgement loss after stage write")

            with patch.object(workspace_artifact, "_exclusive_create_file", side_effect=create_then_raise):
                first = self.execute(
                    self.request("exception-stage.txt", "EXCEPTION"),
                    workspace=workspace,
                    state=state,
                )

            self.assertEqual(first["status"], "running")
            self.assertEqual(first["current_node"], "staged_verified")
            self.assertEqual(first["action_count"], 1)
            self.assertEqual(
                [receipt["transition_id"] for receipt in first["transition_receipts"]],
                ["stage_create"],
            )
            task_id = first["task_id"]
            checkpoint = self.checkpoint(state)
            self.assertIsNone(checkpoint["prepared_intent"])

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("confirmed stage effect was redelivered"),
            ) as create_mock:
                result = self.execute(
                    self.request("exception-stage.txt", "EXCEPTION", task_id),
                    workspace=workspace,
                    state=state,
                )
            create_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_delivery_exception_after_final_link_preserves_repaired_state_for_resume(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_link = workspace_artifact._exclusive_link_file

            def link_then_raise(source: Path, target: Path) -> None:
                original_link(source, target)
                raise OSError("simulated acknowledgement loss after final link")

            with patch.object(workspace_artifact, "_exclusive_link_file", side_effect=link_then_raise):
                first = self.execute(
                    self.request("exception-final.txt", "EXCEPTION"),
                    workspace=workspace,
                    state=state,
                )

            self.assertEqual(first["status"], "running")
            self.assertEqual(first["current_node"], "final_verified")
            self.assertEqual(first["action_count"], 2)
            task_id = first["task_id"]
            staging = self.staging_path(workspace, "exception-final.txt", task_id)
            target = self.target_path(workspace, "exception-final.txt")
            self.assertTrue(staging.exists(), "repaired final state must retain staging for cleanup")
            self.assertTrue(target.exists())
            self.assertTrue(os.path.samefile(staging, target))

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("confirmed final link was redelivered"),
            ) as link_mock:
                result = self.execute(
                    self.request("exception-final.txt", "EXCEPTION", task_id),
                    workspace=workspace,
                    state=state,
                )
            link_mock.assert_not_called()
            self.assert_completed_once(result)

    def test_schema1_cleanup_accepts_distinct_generation_bound_identities(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            artifact_name = "legacy-cleanup.txt"
            content = b"LEGACY"
            task_id = "b" * 32
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / f".{artifact_name}.{task_id}.staging"
            target = reserved / artifact_name
            staging.write_bytes(content)
            target.write_bytes(content)
            self.assertFalse(os.path.samefile(staging, target))

            staging_identity = workspace_artifact._file_identity(staging)
            target_identity = workspace_artifact._file_identity(target)
            self.assertIsNotNone(staging_identity)
            self.assertIsNotNone(target_identity)
            if "birthtime_ns" not in staging_identity or "birthtime_ns" not in target_identity:
                self.skipTest("generation-bearing file identity is unavailable on this platform")

            checkpoint = {
                "schema_version": 1,
                "task_id": task_id,
                "procedure_id": PROCEDURE_ID,
                "procedure_version": PROCEDURE_VERSION,
                "procedure_status": PROCEDURE_STATUS,
                "artifact_name": artifact_name,
                "artifact_relative_path": f".chat-agent-platform/stage26-3a/{artifact_name}",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_size": len(content),
                "current_node": "final_verified",
                "status": "running",
                "action_count": 2,
                "action_budget": MAX_ACTIONS,
                "transition_receipts": [],
                "escalation_reason": None,
                "staging_file_identity": staging_identity,
                "target_file_identity": target_identity,
            }
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            result = self.execute(
                self.request(artifact_name, content.decode("utf-8"), task_id),
                workspace=workspace,
                state=state,
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), content)

    def test_historical_schema1_staged_weak_identity_fails_closed_before_final_create(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            artifact_name = "legacy-staged-weak.txt"
            content = b"LEGACY_STAGED"
            task_id = "c" * 32
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / f".{artifact_name}.{task_id}.staging"
            target = reserved / artifact_name
            staging.write_bytes(content)
            stat = staging.stat()
            checkpoint = {
                "schema_version": 1,
                "task_id": task_id,
                "procedure_id": PROCEDURE_ID,
                "procedure_version": PROCEDURE_VERSION,
                "procedure_status": PROCEDURE_STATUS,
                "artifact_name": artifact_name,
                "artifact_relative_path": f".chat-agent-platform/stage26-3a/{artifact_name}",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_size": len(content),
                "current_node": "staged_verified",
                "status": "running",
                "action_count": 1,
                "action_budget": MAX_ACTIONS,
                "transition_receipts": [],
                "escalation_reason": None,
                "staging_file_identity": {"device": int(stat.st_dev), "inode": int(stat.st_ino)},
                "target_file_identity": None,
            }
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("weak legacy identity must not authorize final creation"),
            ) as link_mock:
                result = self.execute(
                    self.request(artifact_name, content.decode("utf-8"), task_id),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "legacy_identity_generation_unproven")
            self.assertEqual(result["action_count"], 1)
            self.assertTrue(staging.exists())
            self.assertFalse(target.exists())

    def test_historical_schema1_cleanup_weak_identities_fail_closed_before_delete(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            artifact_name = "legacy-cleanup-weak.txt"
            content = b"LEGACY_WEAK"
            task_id = "d" * 32
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / f".{artifact_name}.{task_id}.staging"
            target = reserved / artifact_name
            staging.write_bytes(content)
            target.write_bytes(content)
            staging_stat = staging.stat()
            target_stat = target.stat()
            checkpoint = {
                "schema_version": 1,
                "task_id": task_id,
                "procedure_id": PROCEDURE_ID,
                "procedure_version": PROCEDURE_VERSION,
                "procedure_status": PROCEDURE_STATUS,
                "artifact_name": artifact_name,
                "artifact_relative_path": f".chat-agent-platform/stage26-3a/{artifact_name}",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_size": len(content),
                "current_node": "final_verified",
                "status": "running",
                "action_count": 2,
                "action_budget": MAX_ACTIONS,
                "transition_receipts": [],
                "escalation_reason": None,
                "staging_file_identity": {
                    "device": int(staging_stat.st_dev),
                    "inode": int(staging_stat.st_ino),
                },
                "target_file_identity": {
                    "device": int(target_stat.st_dev),
                    "inode": int(target_stat.st_ino),
                },
            }
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                side_effect=AssertionError("weak legacy identity must not authorize cleanup"),
            ) as delete_mock:
                result = self.execute(
                    self.request(artifact_name, content.decode("utf-8"), task_id),
                    workspace=workspace,
                    state=state,
                )

            delete_mock.assert_not_called()
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "legacy_identity_generation_unproven")
            self.assertEqual(result["action_count"], 2)
            self.assertTrue(staging.exists())
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), content)

    def test_historical_schema1_completed_weak_identity_cannot_reassert_completion(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            artifact_name = "legacy-completed-weak.txt"
            content = b"LEGACY_DONE"
            task_id = "e" * 32
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            target = reserved / artifact_name
            target.write_bytes(content)
            stat = target.stat()
            checkpoint = {
                "schema_version": 1,
                "task_id": task_id,
                "procedure_id": PROCEDURE_ID,
                "procedure_version": PROCEDURE_VERSION,
                "procedure_status": PROCEDURE_STATUS,
                "artifact_name": artifact_name,
                "artifact_relative_path": f".chat-agent-platform/stage26-3a/{artifact_name}",
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_size": len(content),
                "current_node": "completed",
                "status": "completed",
                "action_count": 3,
                "action_budget": MAX_ACTIONS,
                "transition_receipts": [],
                "escalation_reason": None,
                "staging_file_identity": None,
                "target_file_identity": {"device": int(stat.st_dev), "inode": int(stat.st_ino)},
            }
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "legacy completed identity generation"):
                self.execute(
                    self.request(artifact_name, content.decode("utf-8"), task_id),
                    workspace=workspace,
                    state=state,
                )
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
