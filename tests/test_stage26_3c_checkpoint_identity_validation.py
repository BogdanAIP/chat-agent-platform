from __future__ import annotations

import unittest

from runtime.control_plane._verified_workspace_artifact_support import (
    CHECKPOINT_SCHEMA_VERSION,
    MAX_ACTIONS,
    PROCEDURE_ID,
    PROCEDURE_STATUS,
    PROCEDURE_VERSION,
    _validate_resume_state,
)


class Stage263CCheckpointIdentityValidationTests(unittest.TestCase):
    task_id = "a" * 32
    artifact_name = "identity-check.txt"
    expected_sha = "b" * 64
    content_size = 7
    relative_target = ".chat-agent-platform/stage26-3a/identity-check.txt"
    strong_identity = {"device": 1, "inode": 2, "birthtime_ns": 3}
    weak_identity = {"device": 1, "inode": 2}

    def checkpoint(
        self,
        node: str,
        *,
        status: str = "running",
        schema_version: int = CHECKPOINT_SCHEMA_VERSION,
    ) -> dict:
        action_count = {
            "preflight": 0,
            "staged_verified": 1,
            "final_verified": 2,
            "completed": 3,
        }[node]
        receipt_history = [
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
        value = {
            "schema_version": schema_version,
            "task_id": self.task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": self.artifact_name,
            "artifact_relative_path": self.relative_target,
            "content_sha256": self.expected_sha,
            "content_size": self.content_size,
            "current_node": node,
            "status": status,
            "action_count": action_count,
            "action_budget": MAX_ACTIONS,
            "transition_receipts": receipt_history[:action_count],
            "staging_file_identity": dict(self.strong_identity),
            "target_file_identity": dict(self.strong_identity),
        }
        if schema_version == CHECKPOINT_SCHEMA_VERSION:
            value["working_state"] = {}
            value["prepared_intent"] = None
        return value

    def validate(self, checkpoint: dict) -> int:
        return _validate_resume_state(
            checkpoint,
            task_id=self.task_id,
            artifact_name=self.artifact_name,
            expected_sha=self.expected_sha,
            content_size=self.content_size,
            relative_target=self.relative_target,
        )

    def test_schema2_staged_requires_retained_generation_identity(self) -> None:
        for value in (None, dict(self.weak_identity)):
            with self.subTest(value=value):
                checkpoint = self.checkpoint("staged_verified")
                checkpoint["staging_file_identity"] = value
                with self.assertRaisesRegex(ValueError, "staging_file_identity"):
                    self.validate(checkpoint)

    def test_schema2_final_requires_both_retained_generation_identities(self) -> None:
        for field in ("staging_file_identity", "target_file_identity"):
            for value in (None, dict(self.weak_identity)):
                with self.subTest(field=field, value=value):
                    checkpoint = self.checkpoint("final_verified")
                    checkpoint[field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        self.validate(checkpoint)

    def test_schema2_completed_requires_retained_target_generation_identity(self) -> None:
        for node in ("completed", "preflight"):
            for value in (None, dict(self.weak_identity)):
                with self.subTest(node=node, value=value):
                    checkpoint = self.checkpoint(node, status="completed")
                    checkpoint["target_file_identity"] = value
                    with self.assertRaisesRegex(ValueError, "target_file_identity"):
                        self.validate(checkpoint)

    def test_schema2_preflight_does_not_invent_owned_identity_requirement(self) -> None:
        checkpoint = self.checkpoint("preflight")
        checkpoint["staging_file_identity"] = None
        checkpoint["target_file_identity"] = None
        self.assertEqual(self.validate(checkpoint), CHECKPOINT_SCHEMA_VERSION)

    def test_schema1_structural_validation_keeps_legacy_identity_policy_unchanged(self) -> None:
        checkpoint = self.checkpoint("staged_verified", schema_version=1)
        checkpoint["staging_file_identity"] = dict(self.weak_identity)
        checkpoint["target_file_identity"] = None
        self.assertEqual(self.validate(checkpoint), 1)


if __name__ == "__main__":
    unittest.main()
