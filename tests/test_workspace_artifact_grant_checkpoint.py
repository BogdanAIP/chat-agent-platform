from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from runtime.control_plane._verified_workspace_artifact_support import (
    CHECKPOINT_SCHEMA_VERSION,
    LEGACY_WORKING_STATE_SCHEMA_VERSION,
    QUALIFICATION_ADMISSION,
)
from runtime.control_plane.verified_workspace_artifact import (
    PROCEDURE_ID,
    run_verified_workspace_artifact,
)


class WorkspaceArtifactGrantCheckpointTests(unittest.TestCase):
    @staticmethod
    def request(name: str, content: str, task_id: str | None = None) -> dict[str, str]:
        value = {
            "procedure": PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
        }
        if task_id is not None:
            value["resume_task_id"] = task_id
        return value

    @staticmethod
    def run(request: dict[str, str], *, workspace: Path, state: Path) -> dict:
        return run_verified_workspace_artifact(
            request,
            workspace_root=workspace,
            state_root=state,
            candidate_admission=QUALIFICATION_ADMISSION,
        )

    def checkpoint_path(self, state: Path) -> Path:
        files = list(state.glob("*.json"))
        self.assertEqual(1, len(files))
        return files[0]

    def test_completed_schema3_checkpoint_persists_concrete_grant(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            result = self.run(
                self.request("grant-state.txt", "GRANT_STATE"),
                workspace=workspace,
                state=state,
            )
            self.assertEqual("completed", result["status"])

            checkpoint = json.loads(
                self.checkpoint_path(state).read_text(encoding="utf-8")
            )
            self.assertEqual(CHECKPOINT_SCHEMA_VERSION, checkpoint["schema_version"])
            refs = checkpoint["working_state"]["capability_grant_refs"]
            self.assertEqual(1, len(refs))
            self.assertNotEqual([QUALIFICATION_ADMISSION], refs)
            self.assertTrue(refs[0].startswith("grant:workspace-artifact:"))

    def test_schema3_checkpoint_cannot_downgrade_to_shared_admission(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            first = self.run(
                self.request("downgrade.txt", "DOWNGRADE"),
                workspace=workspace,
                state=state,
            )
            checkpoint_path = self.checkpoint_path(state)
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            task_id = checkpoint["task_id"]

            checkpoint["working_state"]["capability_grant_refs"] = [
                QUALIFICATION_ADMISSION
            ]
            checkpoint_path.write_text(
                json.dumps(checkpoint, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "WorkingState capability grant mismatch",
            ):
                self.run(
                    self.request("downgrade.txt", "DOWNGRADE", task_id),
                    workspace=workspace,
                    state=state,
                )

            self.assertEqual("completed", first["status"])

    def test_explicit_schema2_checkpoint_keeps_legacy_admission_on_observation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            first = self.run(
                self.request("legacy-observe.txt", "LEGACY_OBSERVE"),
                workspace=workspace,
                state=state,
            )
            checkpoint_path = self.checkpoint_path(state)
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            task_id = checkpoint["task_id"]

            checkpoint["schema_version"] = LEGACY_WORKING_STATE_SCHEMA_VERSION
            checkpoint["working_state"]["capability_grant_refs"] = [
                QUALIFICATION_ADMISSION
            ]
            checkpoint_path.write_text(
                json.dumps(checkpoint, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )

            resumed = self.run(
                self.request(
                    "legacy-observe.txt",
                    "LEGACY_OBSERVE",
                    task_id,
                ),
                workspace=workspace,
                state=state,
            )
            self.assertEqual("completed", first["status"])
            self.assertEqual("completed", resumed["status"])
            self.assertTrue(resumed["resumed"])

            retained = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(
                LEGACY_WORKING_STATE_SCHEMA_VERSION,
                retained["schema_version"],
            )
            self.assertEqual(
                [QUALIFICATION_ADMISSION],
                retained["working_state"]["capability_grant_refs"],
            )


if __name__ == "__main__":
    unittest.main()
