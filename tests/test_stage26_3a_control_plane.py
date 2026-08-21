from __future__ import annotations

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
    run_verified_workspace_artifact,
)


class Stage263AControlPlaneTests(unittest.TestCase):
    def _run(self, workspace: Path, state: Path, *, name: str, content: str):
        return run_verified_workspace_artifact(
            {
                "procedure": PROCEDURE_ID,
                "artifact_name": name,
                "content": content,
            },
            workspace_root=workspace,
            state_root=state,
            candidate_admission=QUALIFICATION_ADMISSION,
        )

    def test_candidate_procedure_completes_three_verified_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            result = self._run(workspace, state, name="autonomy-proof.txt", content="AUTONOMY_OK")

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["procedure_id"], PROCEDURE_ID)
            self.assertEqual(result["procedure_version"], PROCEDURE_VERSION)
            self.assertEqual(result["procedure_status"], PROCEDURE_STATUS)
            self.assertEqual(result["action_count"], MAX_ACTIONS)
            self.assertEqual(
                [item["transition_id"] for item in result["transition_receipts"]],
                ["stage_create", "final_create", "staging_cleanup"],
            )
            self.assertEqual(result["current_node"], "completed")
            self.assertIsNone(result["escalation_reason"])
            relative = result["artifact_relative_path"]
            self.assertEqual(relative, ".chat-agent-platform/stage26-3a/autonomy-proof.txt")
            self.assertEqual((workspace / relative).read_text(encoding="utf-8"), "AUTONOMY_OK")
            self.assertTrue(result["final_verification"]["exists"])
            self.assertEqual(result["final_verification"]["size"], len(b"AUTONOMY_OK"))

            checkpoints = list(state.glob("*.json"))
            self.assertEqual(len(checkpoints), 1)
            retained = json.loads(checkpoints[0].read_text(encoding="utf-8"))
            self.assertEqual(retained["status"], "completed")
            self.assertEqual(retained["action_count"], 3)
            self.assertNotIn("content", retained)
            self.assertEqual(retained["content_sha256"], result["final_verification"]["sha256"])

    def test_preexisting_target_abstains_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            target_dir = workspace / ".chat-agent-platform" / "stage26-3a"
            target_dir.mkdir(parents=True)
            target = target_dir / "existing.txt"
            target.write_text("DO_NOT_TOUCH", encoding="utf-8")

            result = self._run(workspace, state, name="existing.txt", content="NEW")

            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "target_already_exists")
            self.assertEqual(result["action_count"], 0)
            self.assertEqual(result["transition_receipts"], [])
            self.assertEqual(target.read_text(encoding="utf-8"), "DO_NOT_TOUCH")
            self.assertFalse(any(target_dir.glob("*.staging")))

    def test_candidate_requires_explicit_qualification_admission(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            with self.assertRaises(PermissionError):
                run_verified_workspace_artifact(
                    {
                        "procedure": PROCEDURE_ID,
                        "artifact_name": "denied.txt",
                        "content": "NO",
                    },
                    workspace_root=Path(workspace_dir),
                    state_root=Path(state_dir),
                    candidate_admission=None,
                )
            self.assertEqual(list(Path(workspace_dir).rglob("*")), [])

    def test_request_surface_rejects_path_or_command_fields(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            for extra in (
                {"path": "elsewhere.txt"},
                {"command": "whoami"},
                {"tool": "run_anything"},
            ):
                request = {
                    "procedure": PROCEDURE_ID,
                    "artifact_name": "safe.txt",
                    "content": "SAFE",
                    **extra,
                }
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    run_verified_workspace_artifact(
                        request,
                        workspace_root=Path(workspace_dir),
                        state_root=Path(state_dir),
                        candidate_admission=QUALIFICATION_ADMISSION,
                    )

    def test_artifact_name_is_leaf_only_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            for invalid in (
                "../escape.txt",
                "nested/file.txt",
                r"nested\\file.txt",
                ".txt",
                "not-text.bin",
                "a" * 64 + ".txt",
            ):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    self._run(Path(workspace_dir), Path(state_dir), name=invalid, content="X")

    def test_task_state_contains_execution_evidence_not_private_reasoning(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "runtime"
            / "control_plane"
            / "verified_workspace_artifact.py"
        ).read_text(encoding="utf-8").casefold()
        for forbidden in (
            "chain_of_thought",
            "chain-of-thought",
            "private_reasoning",
            "subprocess",
            "os.system",
            "shell=true",
            "eval(",
            "exec(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
