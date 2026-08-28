from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.verified_workspace_artifact as workspace_artifact
from runtime.control_plane.verification import VerificationResult, VerificationStatus
from runtime.control_plane.working_state import WorkingState


class Stage263CWorkspaceReconciliationAuthorityTests(unittest.TestCase):
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

    def test_kernel_unknown_cannot_confirm_not_applied_or_authorize_retry(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=SystemExit("crash after durable prepare"),
            ):
                with self.assertRaises(SystemExit):
                    self.execute(
                        self.request("kernel-gate.txt", "DATA"),
                        workspace=workspace,
                        state=state,
                    )

            task_id = self.checkpoint(state)["task_id"]

            def kernel_unknown(*, effect_id, intent, after, predicates, evidence_batch_id=None):
                return VerificationResult(
                    effect_id=effect_id,
                    status=VerificationStatus.UNKNOWN,
                    reason="forced_kernel_unknown",
                    observation=after.ref,
                    evidence_batch_id=evidence_batch_id,
                )

            with patch.object(
                workspace_artifact,
                "_verify_from_intent",
                side_effect=kernel_unknown,
            ), patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=AssertionError("kernel UNKNOWN must block retry delivery"),
            ) as create_mock:
                result = self.execute(
                    self.request("kernel-gate.txt", "DATA", task_id),
                    workspace=workspace,
                    state=state,
                )

            create_mock.assert_not_called()
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "resume_reconciliation_unknown")
            checkpoint = self.checkpoint(state)
            working = WorkingState.from_dict(checkpoint["working_state"])
            self.assertEqual(working.reconciliations[-1].status.value, "still_unknown")

    def test_task_lock_is_explicitly_released_after_normal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            result = self.execute(
                self.request("lock-normal.txt", "LOCK"),
                workspace=workspace,
                state=state,
            )
            self.assertEqual(result["status"], "completed")

            lock = workspace_artifact._acquire_task_lock(state, result["task_id"])
            lock.close()

    def test_task_lock_is_explicitly_released_after_exceptional_return(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_exclusive_create_file",
                side_effect=SystemExit("create resumable checkpoint"),
            ):
                with self.assertRaises(SystemExit):
                    self.execute(
                        self.request("lock-exception.txt", "LOCK"),
                        workspace=workspace,
                        state=state,
                    )
            task_id = self.checkpoint(state)["task_id"]

            with patch.object(
                workspace_artifact,
                "_run_verified_workspace_artifact_locked",
                side_effect=RuntimeError("forced exceptional exit"),
            ):
                with self.assertRaisesRegex(RuntimeError, "forced exceptional exit"):
                    self.execute(
                        self.request("lock-exception.txt", "LOCK", task_id),
                        workspace=workspace,
                        state=state,
                    )

            lock = workspace_artifact._acquire_task_lock(state, task_id)
            lock.close()


if __name__ == "__main__":
    unittest.main()
