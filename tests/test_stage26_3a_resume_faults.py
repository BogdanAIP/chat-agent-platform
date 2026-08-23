from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runtime.control_plane.verified_workspace_artifact import (
    MAX_ACTIONS,
    PROCEDURE_ID,
    PROCEDURE_STATUS,
    PROCEDURE_VERSION,
    QUALIFICATION_ADMISSION,
    _file_identity,
    run_verified_workspace_artifact,
)


class Stage263AResumeFaultTests(unittest.TestCase):
    def _request(self, name: str, content: str, task_id: str) -> dict:
        return {
            "procedure": PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
            "resume_task_id": task_id,
        }

    def _base_checkpoint(self, *, task_id: str, name: str, content: str) -> dict:
        data = content.encode("utf-8")
        return {
            "schema_version": 1,
            "task_id": task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": name,
            "artifact_relative_path": f".chat-agent-platform/stage26-3a/{name}",
            "content_sha256": hashlib.sha256(data).hexdigest(),
            "content_size": len(data),
            "current_node": "preflight",
            "status": "running",
            "action_count": 0,
            "action_budget": MAX_ACTIONS,
            "runtime_budget_seconds": 10.0,
            "transition_receipts": [],
            "escalation_reason": None,
            "staging_file_identity": None,
            "target_file_identity": None,
            "created_at": "2026-08-23T00:00:00+00:00",
        }

    def test_resume_from_final_verified_runs_cleanup_only(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            task_id = "c" * 32
            name = "final-resume.txt"
            content = "FINAL_RESUME"
            data = content.encode("utf-8")
            digest = hashlib.sha256(data).hexdigest()
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / f".{name}.{task_id}.staging"
            target = reserved / name
            staging.write_bytes(data)
            target.write_bytes(data)

            checkpoint = self._base_checkpoint(task_id=task_id, name=name, content=content)
            checkpoint.update(
                {
                    "current_node": "final_verified",
                    "action_count": 2,
                    "staging_file_identity": _file_identity(staging),
                    "target_file_identity": _file_identity(target),
                    "transition_receipts": [
                        {
                            "transition_id": "stage_create",
                            "from_node": "preflight",
                            "to_node": "staged_verified",
                            "action": "exclusive_create_staging",
                            "verification": {"exists": True, "size": len(data), "sha256": digest},
                            "verified_at": "2026-08-23T00:00:00+00:00",
                        },
                        {
                            "transition_id": "final_create",
                            "from_node": "staged_verified",
                            "to_node": "final_verified",
                            "action": "exclusive_create_final",
                            "verification": {
                                "target": {"exists": True, "size": len(data), "sha256": digest},
                                "staging": {"exists": True, "size": len(data), "sha256": digest},
                            },
                            "verified_at": "2026-08-23T00:00:01+00:00",
                        },
                    ],
                }
            )
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            result = run_verified_workspace_artifact(
                self._request(name, content, task_id),
                workspace_root=workspace,
                state_root=state,
                candidate_admission=QUALIFICATION_ADMISSION,
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertEqual(result["transition_receipts"][-1]["transition_id"], "staging_cleanup")
            self.assertFalse(staging.exists())
            self.assertEqual(target.read_bytes(), data)

    def test_resume_rejects_checkpoint_content_mismatch_before_workspace_action(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            task_id = "d" * 32
            checkpoint = self._base_checkpoint(task_id=task_id, name="mismatch.txt", content="OLD")
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "content digest mismatch|content size mismatch"):
                run_verified_workspace_artifact(
                    self._request("mismatch.txt", "NEW", task_id),
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=QUALIFICATION_ADMISSION,
                )

            self.assertFalse((workspace / ".chat-agent-platform").exists())

    def test_corrupt_checkpoint_fails_closed_before_workspace_action(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            task_id = "e" * 32
            (state / f"{task_id}.json").write_text("{not-json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "checkpoint is invalid"):
                run_verified_workspace_artifact(
                    self._request("corrupt.txt", "DATA", task_id),
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=QUALIFICATION_ADMISSION,
                )

            self.assertFalse((workspace / ".chat-agent-platform").exists())

    def test_resume_rejects_action_budget_drift(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            task_id = "f" * 32
            checkpoint = self._base_checkpoint(task_id=task_id, name="budget.txt", content="DATA")
            checkpoint["action_count"] = MAX_ACTIONS + 1
            (state / f"{task_id}.json").write_text(json.dumps(checkpoint), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "action count is invalid"):
                run_verified_workspace_artifact(
                    self._request("budget.txt", "DATA", task_id),
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=QUALIFICATION_ADMISSION,
                )

            self.assertFalse((workspace / ".chat-agent-platform").exists())


if __name__ == "__main__":
    unittest.main()
