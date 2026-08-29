from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane._verified_workspace_artifact_support as workspace_support
import runtime.control_plane.verified_workspace_artifact as workspace_artifact
import runtime.control_plane.windows_file_pin as windows_file_pin


@unittest.skipUnless(os.name == "nt", "workspace namespace pin is Windows-specific")
class Stage263CStageCreateNamespacePinTests(unittest.TestCase):
    def test_stage_create_holds_namespace_pins_before_exclusive_open(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_open = Path.open
            attack_ran = False
            blocked: list[OSError] = []

            def attack_then_open(path_self: Path, mode: str = "r", *args, **kwargs):
                nonlocal attack_ran
                if (
                    not attack_ran
                    and mode == "xb"
                    and path_self.name.endswith(".staging")
                    and path_self.parent.name == "stage26-3a"
                ):
                    attack_ran = True
                    for directory in (path_self.parent, path_self.parent.parent, workspace):
                        moved = directory.with_name(directory.name + ".retargeted")
                        try:
                            os.rename(directory, moved)
                        except OSError as exc:
                            blocked.append(exc)
                        else:
                            self.fail(
                                f"stage-create namespace pin allowed replacement precursor for {directory}"
                            )
                return original_open(path_self, mode, *args, **kwargs)

            self.assertIs(
                workspace_support._exclusive_create_file,
                windows_file_pin.create_file_in_pinned_namespace,
                "Windows package wiring must bind stage_create to the namespace-pinned create primitive",
            )

            request = {
                "procedure": workspace_artifact.PROCEDURE_ID,
                "artifact_name": "stage-create-pin.txt",
                "content": "PINNED_STAGE_CREATE",
            }
            with patch.object(Path, "open", new=attack_then_open):
                result = workspace_artifact.run_verified_workspace_artifact(
                    request,
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=workspace_artifact.QUALIFICATION_ADMISSION,
                )

            self.assertTrue(attack_ran)
            self.assertEqual(len(blocked), 3)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            target = workspace / ".chat-agent-platform" / "stage26-3a" / "stage-create-pin.txt"
            self.assertEqual(target.read_text(encoding="utf-8"), "PINNED_STAGE_CREATE")


if __name__ == "__main__":
    unittest.main()
