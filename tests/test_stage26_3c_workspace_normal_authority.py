from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.verified_workspace_artifact as workspace_artifact
from runtime.control_plane.verification import VerificationResult, VerificationStatus
from runtime.control_plane.working_state import WorkingState


class Stage263CWorkspaceNormalAuthorityTests(unittest.TestCase):
    def request(self, name: str, content: str) -> dict:
        return {
            "procedure": workspace_artifact.PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
        }

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

    def force_unknown(self, effect_id_to_block: str):
        original = workspace_artifact._verify_transition

        def verify(*, effect_id, before, after, predicates, evidence_batch_id=None):
            if effect_id == effect_id_to_block:
                return VerificationResult(
                    effect_id=effect_id,
                    status=VerificationStatus.UNKNOWN,
                    reason="forced_kernel_unknown",
                    observation=after.ref,
                    evidence_batch_id=evidence_batch_id,
                )
            return original(
                effect_id=effect_id,
                before=before,
                after=after,
                predicates=predicates,
                evidence_batch_id=evidence_batch_id,
            )

        return verify

    def assert_last_outcome_unknown(self, checkpoint: dict) -> None:
        working = WorkingState.from_dict(checkpoint["working_state"])
        self.assertTrue(working.attempts)
        self.assertEqual(working.attempts[-1].outcome.value, "outcome_unknown")
        self.assertTrue(working.reconciliations)
        self.assertEqual(working.reconciliations[-1].status.value, "still_unknown")
        self.assertNotEqual(working.attempts[-1].outcome.value, "verified_applied")

    def test_stage_delivery_cannot_be_verified_applied_when_kernel_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_verify_transition",
                side_effect=self.force_unknown("stage_create"),
            ), patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("kernel UNKNOWN must block final create"),
            ) as link_mock:
                result = self.execute(
                    self.request("normal-stage-unknown.txt", "STAGE"),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "staging_postcondition_failed")
            self.assertEqual(result["action_count"], 1)
            self.assertEqual(result["transition_receipts"], [])
            checkpoint = self.checkpoint(state)
            self.assert_last_outcome_unknown(checkpoint)
            task_id = checkpoint["task_id"]
            staging = (
                workspace
                / ".chat-agent-platform"
                / "stage26-3a"
                / f".normal-stage-unknown.txt.{task_id}.staging"
            )
            target = workspace / ".chat-agent-platform" / "stage26-3a" / "normal-stage-unknown.txt"
            self.assertTrue(staging.exists())
            self.assertFalse(target.exists())

    def test_final_delivery_cannot_be_verified_applied_when_kernel_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_unlink = Path.unlink

            def reject_staging_cleanup(path: Path, *args, **kwargs) -> None:
                if path.name.endswith(".staging"):
                    raise AssertionError("kernel UNKNOWN must block staging cleanup")
                return original_unlink(path, *args, **kwargs)

            with patch.object(
                workspace_artifact,
                "_verify_transition",
                side_effect=self.force_unknown("final_create"),
            ), patch.object(Path, "unlink", new=reject_staging_cleanup):
                result = self.execute(
                    self.request("normal-final-unknown.txt", "FINAL"),
                    workspace=workspace,
                    state=state,
                )

            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "final_create_postcondition_failed")
            self.assertEqual(result["action_count"], 2)
            self.assertEqual(
                [item["transition_id"] for item in result["transition_receipts"]],
                ["stage_create"],
            )
            checkpoint = self.checkpoint(state)
            self.assert_last_outcome_unknown(checkpoint)
            task_id = checkpoint["task_id"]
            staging = (
                workspace
                / ".chat-agent-platform"
                / "stage26-3a"
                / f".normal-final-unknown.txt.{task_id}.staging"
            )
            target = workspace / ".chat-agent-platform" / "stage26-3a" / "normal-final-unknown.txt"
            self.assertTrue(staging.exists())
            self.assertTrue(target.exists())

    def test_cleanup_delivery_cannot_be_verified_applied_when_finish_gate_is_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_verify_transition",
                side_effect=self.force_unknown("completion_staging_absent"),
            ):
                result = self.execute(
                    self.request("normal-cleanup-unknown.txt", "CLEANUP"),
                    workspace=workspace,
                    state=state,
                )

            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "completion_postcondition_failed")
            self.assertEqual(result["action_count"], 3)
            self.assertEqual(
                [item["transition_id"] for item in result["transition_receipts"]],
                ["stage_create", "final_create"],
            )
            checkpoint = self.checkpoint(state)
            self.assert_last_outcome_unknown(checkpoint)
            task_id = checkpoint["task_id"]
            staging = (
                workspace
                / ".chat-agent-platform"
                / "stage26-3a"
                / f".normal-cleanup-unknown.txt.{task_id}.staging"
            )
            target = workspace / ".chat-agent-platform" / "stage26-3a" / "normal-cleanup-unknown.txt"
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
