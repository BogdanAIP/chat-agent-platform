from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane as control_plane
import runtime.control_plane.verified_workspace_artifact as workspace_artifact


class Stage263CPostEffectExceptionRecoveryTests(unittest.TestCase):
    def request(self, name: str, content: str, task_id: str | None = None) -> dict:
        value = {
            "procedure": workspace_artifact.PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
        }
        if task_id is not None:
            value["resume_task_id"] = task_id
        return value

    def execute(self, request: dict, *, workspace: Path, state: Path) -> dict:
        return workspace_artifact.run_verified_workspace_artifact(
            request,
            workspace_root=workspace,
            state_root=state,
            candidate_admission=workspace_artifact.QUALIFICATION_ADMISSION,
        )

    def checkpoint(self, state: Path) -> dict:
        files = list(state.glob("*.json"))
        self.assertEqual(len(files), 1)
        return json.loads(files[0].read_text(encoding="utf-8"))

    @staticmethod
    def staging(workspace: Path, name: str, task_id: str) -> Path:
        return (
            workspace
            / ".chat-agent-platform"
            / "stage26-3a"
            / f".{name}.{task_id}.staging"
        )

    @staticmethod
    def target(workspace: Path, name: str) -> Path:
        return workspace / ".chat-agent-platform" / "stage26-3a" / name

    def test_final_link_post_effect_exception_preserves_prepared_resume_state(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_verify = workspace_artifact._verify_transition
            injected = False

            def verify_with_post_link_exception(*args, **kwargs):
                nonlocal injected
                if kwargs.get("effect_id") == "final_create" and not injected:
                    injected = True
                    raise RuntimeError("post-link verification fault")
                return real_verify(*args, **kwargs)

            with patch.object(
                workspace_artifact,
                "_verify_transition",
                new=verify_with_post_link_exception,
            ):
                first = self.execute(
                    self.request("post-link.txt", "POST_LINK"),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(injected)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging(workspace, "post-link.txt", task_id)
            target = self.target(workspace, "post-link.txt")
            self.assertEqual(first["status"], "running")
            self.assertEqual(checkpoint["status"], "running")
            self.assertEqual(checkpoint["current_node"], "staged_verified")
            self.assertEqual(checkpoint["action_count"], 1)
            self.assertIsInstance(checkpoint["prepared_intent"], dict)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "final_create")
            self.assertTrue(staging.exists())
            self.assertTrue(target.exists())

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("final link must reconcile, not redeliver"),
            ) as link_mock:
                resumed = self.execute(
                    self.request("post-link.txt", "POST_LINK", task_id),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(resumed["status"], "completed")
            self.assertEqual(resumed["action_count"], 3)
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())

    def test_final_receipt_checkpoint_failure_restores_last_durable_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_write = control_plane._original_workspace_write_checkpoint
            injected = False

            def fail_first_final_receipt(state_root: Path, task_state: dict) -> None:
                nonlocal injected
                if (
                    not injected
                    and task_state.get("current_node") == "final_verified"
                    and task_state.get("prepared_intent") is None
                ):
                    injected = True
                    raise OSError("simulated final receipt checkpoint failure")
                real_write(state_root, task_state)

            with patch.object(
                control_plane,
                "_original_workspace_write_checkpoint",
                new=fail_first_final_receipt,
            ):
                first = self.execute(
                    self.request("receipt-fail.txt", "RECEIPT_FAIL"),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(injected)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            target = self.target(workspace, "receipt-fail.txt")
            self.assertEqual(first["status"], "running")
            self.assertEqual(checkpoint["status"], "running")
            self.assertEqual(checkpoint["current_node"], "staged_verified")
            self.assertEqual(checkpoint["action_count"], 1)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "final_create")
            self.assertTrue(target.exists())

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("checkpoint-failed final link must not redeliver"),
            ) as link_mock:
                resumed = self.execute(
                    self.request("receipt-fail.txt", "RECEIPT_FAIL", task_id),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(resumed["status"], "completed")
            self.assertEqual(resumed["action_count"], 3)

    def test_stage_post_effect_exception_loses_proof_and_resume_abstains(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_verify = workspace_artifact._verify_transition
            injected = False

            def fail_stage_verification(*args, **kwargs):
                nonlocal injected
                if kwargs.get("effect_id") == "stage_create" and not injected:
                    injected = True
                    raise RuntimeError("post-stage verification fault")
                return real_verify(*args, **kwargs)

            with patch.object(
                workspace_artifact,
                "_verify_transition",
                new=fail_stage_verification,
            ):
                first = self.execute(
                    self.request("post-stage.txt", "POST_STAGE"),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(injected)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging(workspace, "post-stage.txt", task_id)
            self.assertEqual(first["status"], "running")
            self.assertEqual(checkpoint["status"], "running")
            self.assertEqual(checkpoint["action_count"], 0)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "stage_create")
            self.assertTrue(staging.exists())

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("unproven stage must not redeliver"),
            ) as create_mock, patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("unproven stage must not link"),
            ) as link_mock:
                resumed = self.execute(
                    self.request("post-stage.txt", "POST_STAGE", task_id),
                    workspace=workspace,
                    state=state,
                )

            create_mock.assert_not_called()
            link_mock.assert_not_called()
            self.assertEqual(resumed["status"], "abstained")
            self.assertEqual(resumed["escalation_reason"], "resume_reconciliation_unknown")
            self.assertEqual(resumed["action_count"], 0)
            self.assertTrue(staging.exists())

    def test_cleanup_post_effect_exception_preserves_prepared_resume_state(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_verify = workspace_artifact._verify_transition
            injected = False

            def fail_completion_verification(*args, **kwargs):
                nonlocal injected
                if kwargs.get("effect_id") == "completion_target" and not injected:
                    injected = True
                    raise RuntimeError("post-cleanup verification fault")
                return real_verify(*args, **kwargs)

            with patch.object(
                workspace_artifact,
                "_verify_transition",
                new=fail_completion_verification,
            ):
                first = self.execute(
                    self.request("post-cleanup.txt", "POST_CLEANUP"),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(injected)
            checkpoint = self.checkpoint(state)
            task_id = checkpoint["task_id"]
            staging = self.staging(workspace, "post-cleanup.txt", task_id)
            target = self.target(workspace, "post-cleanup.txt")
            self.assertEqual(first["status"], "running")
            self.assertEqual(checkpoint["status"], "running")
            self.assertEqual(checkpoint["current_node"], "final_verified")
            self.assertEqual(checkpoint["action_count"], 2)
            self.assertEqual(checkpoint["prepared_intent"]["transition_id"], "staging_cleanup")
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                side_effect=AssertionError("cleanup must reconcile, not redeliver"),
            ) as delete_mock:
                resumed = self.execute(
                    self.request("post-cleanup.txt", "POST_CLEANUP", task_id),
                    workspace=workspace,
                    state=state,
                )

            delete_mock.assert_not_called()
            self.assertEqual(resumed["status"], "completed")
            self.assertEqual(resumed["action_count"], 3)
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
