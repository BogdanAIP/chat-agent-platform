from __future__ import annotations

from contextlib import contextmanager
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.verified_workspace_artifact as workspace_artifact
from runtime.control_plane._verified_workspace_artifact_support import (
    CHECKPOINT_SCHEMA_VERSION,
    LEGACY_WORKING_STATE_SCHEMA_VERSION,
    QUALIFICATION_ADMISSION,
)
from runtime.control_plane.verified_workspace_artifact import (
    PROCEDURE_ID,
    run_verified_workspace_artifact,
)


class WorkspaceLegacyGrantHandoffTests(unittest.TestCase):
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
    def execute(request: dict[str, str], *, workspace: Path, state: Path) -> dict:
        return run_verified_workspace_artifact(
            request,
            workspace_root=workspace,
            state_root=state,
            candidate_admission=QUALIFICATION_ADMISSION,
        )

    @staticmethod
    def checkpoint_path(state: Path) -> Path:
        files = list(state.glob("*.json"))
        if len(files) != 1:
            raise AssertionError(f"expected one checkpoint, found {len(files)}")
        return files[0]

    @staticmethod
    def downgrade_to_schema2(path: Path) -> tuple[str, list[dict]]:
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
        checkpoint["schema_version"] = LEGACY_WORKING_STATE_SCHEMA_VERSION
        checkpoint["working_state"]["capability_grant_refs"] = [
            QUALIFICATION_ADMISSION
        ]
        prior_attempts = list(checkpoint["working_state"]["attempts"])
        path.write_text(
            json.dumps(checkpoint, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        return checkpoint["task_id"], prior_attempts

    def test_schema2_staged_resume_handoffs_before_final_create(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=SystemExit("crash before final create"),
            ):
                with self.assertRaisesRegex(SystemExit, "before final create"):
                    self.execute(
                        self.request("handoff-final.txt", "HANDOFF_FINAL"),
                        workspace=workspace,
                        state=state,
                    )

            checkpoint_path = self.checkpoint_path(state)
            before = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual("staged_verified", before["current_node"])
            self.assertEqual("final_create", before["prepared_intent"]["transition_id"])
            task_id, prior_attempts = self.downgrade_to_schema2(checkpoint_path)
            real_link = workspace_artifact._exclusive_link_file
            observed_handoff = False

            def checking_link(source: Path, target: Path) -> None:
                nonlocal observed_handoff
                durable = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                self.assertEqual(CHECKPOINT_SCHEMA_VERSION, durable["schema_version"])
                refs = durable["working_state"]["capability_grant_refs"]
                self.assertEqual(1, len(refs))
                self.assertTrue(refs[0].startswith("grant:workspace-artifact:"))
                self.assertEqual(
                    prior_attempts,
                    durable["working_state"]["attempts"][: len(prior_attempts)],
                )
                observed_handoff = True
                real_link(source, target)

            with patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=checking_link,
            ):
                result = self.execute(
                    self.request("handoff-final.txt", "HANDOFF_FINAL", task_id),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(observed_handoff)
            self.assertEqual("completed", result["status"])
            final = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(CHECKPOINT_SCHEMA_VERSION, final["schema_version"])
            self.assertTrue(
                final["working_state"]["capability_grant_refs"][0].startswith(
                    "grant:workspace-artifact:"
                )
            )

    def test_schema2_final_resume_handoffs_before_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                side_effect=SystemExit("crash before cleanup"),
            ):
                with self.assertRaisesRegex(SystemExit, "before cleanup"):
                    self.execute(
                        self.request("handoff-cleanup.txt", "HANDOFF_CLEANUP"),
                        workspace=workspace,
                        state=state,
                    )

            checkpoint_path = self.checkpoint_path(state)
            before = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual("final_verified", before["current_node"])
            self.assertEqual("staging_cleanup", before["prepared_intent"]["transition_id"])
            task_id, prior_attempts = self.downgrade_to_schema2(checkpoint_path)
            real_pin = workspace_artifact.pin_file_for_verified_delete
            observed_handoff = False

            @contextmanager
            def checking_pin(path: Path, *, workspace_root: Path | None = None):
                nonlocal observed_handoff
                durable = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                self.assertEqual(CHECKPOINT_SCHEMA_VERSION, durable["schema_version"])
                refs = durable["working_state"]["capability_grant_refs"]
                self.assertEqual(1, len(refs))
                self.assertTrue(refs[0].startswith("grant:workspace-artifact:"))
                self.assertEqual(
                    prior_attempts,
                    durable["working_state"]["attempts"][: len(prior_attempts)],
                )
                observed_handoff = True
                with real_pin(path, workspace_root=workspace_root) as mark_delete:
                    yield mark_delete

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                new=checking_pin,
            ):
                result = self.execute(
                    self.request(
                        "handoff-cleanup.txt",
                        "HANDOFF_CLEANUP",
                        task_id,
                    ),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(observed_handoff)
            self.assertEqual("completed", result["status"])
            final = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(CHECKPOINT_SCHEMA_VERSION, final["schema_version"])
            self.assertTrue(
                final["working_state"]["capability_grant_refs"][0].startswith(
                    "grant:workspace-artifact:"
                )
            )


if __name__ == "__main__":
    unittest.main()
