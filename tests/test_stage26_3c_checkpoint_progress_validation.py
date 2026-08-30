from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runtime.control_plane import verified_workspace_artifact as workspace_artifact
from runtime.control_plane._verified_workspace_artifact_support import (
    CHECKPOINT_SCHEMA_VERSION,
    MAX_ACTIONS,
    PROCEDURE_ID,
    PROCEDURE_STATUS,
    PROCEDURE_VERSION,
    QUALIFICATION_ADMISSION,
    _validate_resume_state,
)


class Stage263CCheckpointProgressValidationTests(unittest.TestCase):
    task_id = "c" * 32
    artifact_name = "progress-guard.txt"
    content = "PROGRESS_GUARD"
    expected_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    relative_target = ".chat-agent-platform/stage26-3a/progress-guard.txt"
    strong_identity = {"device": 1, "inode": 2, "birthtime_ns": 3}

    def receipt_history(self) -> list[dict]:
        return [
            {
                "transition_id": "stage_create",
                "from_node": "preflight",
                "to_node": "staged_verified",
            },
            {
                "transition_id": "final_create",
                "from_node": "staged_verified",
                "to_node": "final_verified",
            },
            {
                "transition_id": "staging_cleanup",
                "from_node": "final_verified",
                "to_node": "completed",
            },
        ]

    def corrupt_preflight_checkpoint(self) -> dict:
        return {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "task_id": self.task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": self.artifact_name,
            "artifact_relative_path": self.relative_target,
            "content_sha256": self.expected_sha,
            "content_size": len(self.content.encode("utf-8")),
            "current_node": "preflight",
            "status": "running",
            "action_count": MAX_ACTIONS,
            "action_budget": MAX_ACTIONS,
            "transition_receipts": [],
            "staging_file_identity": None,
            "target_file_identity": None,
            "working_state": {},
            "prepared_intent": None,
        }

    def completed_checkpoint(self) -> dict:
        return {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "task_id": self.task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": self.artifact_name,
            "artifact_relative_path": self.relative_target,
            "content_sha256": self.expected_sha,
            "content_size": len(self.content.encode("utf-8")),
            "current_node": "completed",
            "status": "completed",
            "action_count": MAX_ACTIONS,
            "action_budget": MAX_ACTIONS,
            "transition_receipts": self.receipt_history(),
            "staging_file_identity": dict(self.strong_identity),
            "target_file_identity": dict(self.strong_identity),
            "working_state": {},
            "prepared_intent": None,
        }

    def validate(self, checkpoint: dict) -> int:
        return _validate_resume_state(
            checkpoint,
            task_id=self.task_id,
            artifact_name=self.artifact_name,
            expected_sha=self.expected_sha,
            content_size=len(self.content.encode("utf-8")),
            relative_target=self.relative_target,
        )

    def test_schema2_running_preflight_cannot_claim_exhausted_action_budget(self) -> None:
        with self.assertRaisesRegex(ValueError, "running action progress mismatch"):
            self.validate(self.corrupt_preflight_checkpoint())

    def test_corrupt_exhausted_preflight_resume_fails_before_staging_create(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_text, tempfile.TemporaryDirectory() as state_text:
            workspace_root = Path(workspace_text)
            state_root = Path(state_text)
            checkpoint_path = state_root / f"{self.task_id}.json"
            checkpoint_path.write_text(
                json.dumps(self.corrupt_preflight_checkpoint()),
                encoding="utf-8",
            )

            request = {
                "procedure": PROCEDURE_ID,
                "artifact_name": self.artifact_name,
                "content": self.content,
                "resume_task_id": self.task_id,
            }
            with mock.patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("physical staging create must not be reached"),
            ):
                with self.assertRaisesRegex(ValueError, "running action progress mismatch"):
                    workspace_artifact.run_verified_workspace_artifact(
                        request,
                        workspace_root=workspace_root,
                        state_root=state_root,
                        candidate_admission=QUALIFICATION_ADMISSION,
                    )

            reserved_root = workspace_root / ".chat-agent-platform" / "stage26-3a"
            staging = reserved_root / f".{self.artifact_name}.{self.task_id}.staging"
            target = reserved_root / self.artifact_name
            self.assertFalse(staging.exists())
            self.assertFalse(target.exists())

    def test_schema2_completed_requires_completed_node_and_full_action_count(self) -> None:
        wrong_node = self.completed_checkpoint()
        wrong_node["current_node"] = "preflight"
        wrong_node["action_count"] = 0
        wrong_node["transition_receipts"] = []
        with self.assertRaisesRegex(ValueError, "completed node is invalid"):
            self.validate(wrong_node)

        wrong_count = self.completed_checkpoint()
        wrong_count["action_count"] = MAX_ACTIONS - 1
        with self.assertRaisesRegex(ValueError, "completed action progress mismatch"):
            self.validate(wrong_count)

    def test_schema2_completed_requires_exact_transition_receipt_history(self) -> None:
        missing_receipt = self.completed_checkpoint()
        missing_receipt["transition_receipts"] = missing_receipt["transition_receipts"][:-1]
        with self.assertRaisesRegex(ValueError, "completed receipt progress mismatch"):
            self.validate(missing_receipt)

        wrong_history = self.completed_checkpoint()
        wrong_history["transition_receipts"][1]["transition_id"] = "stage_create"
        with self.assertRaisesRegex(ValueError, "completed transition history mismatch"):
            self.validate(wrong_history)

    def test_schema2_completed_rejects_dangling_prepared_intent(self) -> None:
        checkpoint = self.completed_checkpoint()
        checkpoint["prepared_intent"] = {"transition_id": "staging_cleanup"}
        with self.assertRaisesRegex(ValueError, "completed prepared intent is invalid"):
            self.validate(checkpoint)

    def test_schema2_structurally_consistent_completed_checkpoint_passes_progress_validation(self) -> None:
        self.assertEqual(self.validate(self.completed_checkpoint()), CHECKPOINT_SCHEMA_VERSION)

    def test_corrupt_completed_resume_fails_before_current_target_certification(self) -> None:
        checkpoint = self.completed_checkpoint()
        checkpoint["current_node"] = "preflight"
        checkpoint["action_count"] = 0
        checkpoint["transition_receipts"] = []

        with tempfile.TemporaryDirectory() as workspace_text, tempfile.TemporaryDirectory() as state_text:
            workspace_root = Path(workspace_text)
            state_root = Path(state_text)
            (state_root / f"{self.task_id}.json").write_text(
                json.dumps(checkpoint),
                encoding="utf-8",
            )
            request = {
                "procedure": PROCEDURE_ID,
                "artifact_name": self.artifact_name,
                "content": self.content,
                "resume_task_id": self.task_id,
            }
            with mock.patch.object(
                workspace_artifact,
                "_verify_current_state",
                side_effect=AssertionError("completed target certification must not be reached"),
            ):
                with self.assertRaisesRegex(ValueError, "completed node is invalid"):
                    workspace_artifact.run_verified_workspace_artifact(
                        request,
                        workspace_root=workspace_root,
                        state_root=state_root,
                        candidate_admission=QUALIFICATION_ADMISSION,
                    )


if __name__ == "__main__":
    unittest.main()
