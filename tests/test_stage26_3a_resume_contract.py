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
    _rollback_owned_file,
    run_verified_workspace_artifact,
)


class Stage263AResumeContractTests(unittest.TestCase):
    def _request(self, name: str, content: str, *, task_id: str | None = None) -> dict:
        request = {"procedure": PROCEDURE_ID, "artifact_name": name, "content": content}
        if task_id is not None:
            request["resume_task_id"] = task_id
        return request

    def _seed_staged_checkpoint(
        self,
        workspace: Path,
        state_root: Path,
        *,
        task_id: str,
        name: str,
        content: str,
    ) -> tuple[Path, Path]:
        reserved = workspace / ".chat-agent-platform" / "stage26-3a"
        reserved.mkdir(parents=True)
        staging = reserved / f".{name}.{task_id}.staging"
        staging.write_bytes(content.encode("utf-8"))
        identity = _file_identity(staging)
        self.assertIsNotNone(identity)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        checkpoint = {
            "schema_version": 1,
            "task_id": task_id,
            "procedure_id": PROCEDURE_ID,
            "procedure_version": PROCEDURE_VERSION,
            "procedure_status": PROCEDURE_STATUS,
            "artifact_name": name,
            "artifact_relative_path": f".chat-agent-platform/stage26-3a/{name}",
            "content_sha256": digest,
            "content_size": len(content.encode("utf-8")),
            "current_node": "staged_verified",
            "status": "running",
            "action_count": 1,
            "action_budget": MAX_ACTIONS,
            "runtime_budget_seconds": 10.0,
            "transition_receipts": [
                {
                    "transition_id": "stage_create",
                    "from_node": "preflight",
                    "to_node": "staged_verified",
                    "action": "exclusive_create_staging",
                    "verification": {
                        "exists": True,
                        "size": len(content.encode("utf-8")),
                        "sha256": digest,
                    },
                    "verified_at": "2026-08-23T00:00:00+00:00",
                }
            ],
            "escalation_reason": None,
            "staging_file_identity": identity,
            "target_file_identity": None,
            "created_at": "2026-08-23T00:00:00+00:00",
        }
        state_root.mkdir(parents=True, exist_ok=True)
        checkpoint_path = state_root / f"{task_id}.json"
        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
        return staging, checkpoint_path

    def test_resume_from_verified_staging_checkpoint_completes_remaining_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            task_id = "a" * 32
            staging, _ = self._seed_staged_checkpoint(
                workspace,
                state,
                task_id=task_id,
                name="resume.txt",
                content="RESUME_OK",
            )

            result = run_verified_workspace_artifact(
                self._request("resume.txt", "RESUME_OK", task_id=task_id),
                workspace_root=workspace,
                state_root=state,
                candidate_admission=QUALIFICATION_ADMISSION,
            )

            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["resumed"])
            self.assertEqual(result["action_count"], 3)
            self.assertEqual(
                [receipt["transition_id"] for receipt in result["transition_receipts"]],
                ["stage_create", "final_create", "staging_cleanup"],
            )
            self.assertFalse(staging.exists())
            target = workspace / ".chat-agent-platform" / "stage26-3a" / "resume.txt"
            self.assertEqual(target.read_text(encoding="utf-8"), "RESUME_OK")

    def test_resume_rejects_same_digest_replacement_with_different_file_identity(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            task_id = "b" * 32
            staging, _ = self._seed_staged_checkpoint(
                workspace,
                state,
                task_id=task_id,
                name="identity.txt",
                content="SAME_BYTES",
            )
            original_identity = _file_identity(staging)
            staging.unlink()
            staging.write_text("SAME_BYTES", encoding="utf-8")
            self.assertNotEqual(_file_identity(staging), original_identity)

            result = run_verified_workspace_artifact(
                self._request("identity.txt", "SAME_BYTES", task_id=task_id),
                workspace_root=workspace,
                state_root=state,
                candidate_admission=QUALIFICATION_ADMISSION,
            )

            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "resume_staging_identity_mismatch")
            self.assertEqual(result["action_count"], 1)
            self.assertTrue(staging.exists())
            self.assertEqual(staging.read_text(encoding="utf-8"), "SAME_BYTES")

    def test_completed_checkpoint_is_idempotently_observable(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            first = run_verified_workspace_artifact(
                self._request("done.txt", "DONE"),
                workspace_root=workspace,
                state_root=state,
                candidate_admission=QUALIFICATION_ADMISSION,
            )
            target = workspace / first["artifact_relative_path"]
            identity_before = _file_identity(target)

            second = run_verified_workspace_artifact(
                self._request("done.txt", "DONE", task_id=first["task_id"]),
                workspace_root=workspace,
                state_root=state,
                candidate_admission=QUALIFICATION_ADMISSION,
            )

            self.assertEqual(second["status"], "completed")
            self.assertTrue(second["resumed"])
            self.assertEqual(second["action_count"], 3)
            self.assertEqual(_file_identity(target), identity_before)

    def test_rollback_refuses_same_digest_replacement_object(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            path = Path(root_dir) / "owned.txt"
            path.write_text("IDENTICAL", encoding="utf-8")
            expected_identity = _file_identity(path)
            digest = hashlib.sha256(b"IDENTICAL").hexdigest()
            path.unlink()
            path.write_text("IDENTICAL", encoding="utf-8")
            self.assertNotEqual(_file_identity(path), expected_identity)

            removed = _rollback_owned_file(path, digest, expected_identity)

            self.assertFalse(removed)
            self.assertTrue(path.exists())

    def test_resume_task_id_is_strictly_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            with self.assertRaises(ValueError):
                run_verified_workspace_artifact(
                    self._request("bad.txt", "X", task_id="not-a-task"),
                    workspace_root=Path(workspace_dir),
                    state_root=Path(state_dir),
                    candidate_admission=QUALIFICATION_ADMISSION,
                )


if __name__ == "__main__":
    unittest.main()
