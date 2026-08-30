from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.cli as control_plane_cli


class Stage263CWorkspacePythonRuntimeTests(unittest.TestCase):
    def test_python_311_is_rejected_before_workspace_state_or_effect(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            request = {
                "procedure": control_plane_cli.WORKSPACE_ARTIFACT_PROCEDURE_ID,
                "artifact_name": "unsupported-python.txt",
                "content": "MUST_NOT_APPLY",
            }

            with patch.object(control_plane_cli.sys, "version_info", (3, 11, 9)):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "requires Python 3.12 or newer",
                ):
                    control_plane_cli._run_workspace_artifact(
                        request,
                        workspace_root=workspace,
                        state_root=state,
                        candidate_admission="stage26-3a-qualification",
                    )

            self.assertEqual(list(state.iterdir()), [])
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            self.assertFalse(reserved.exists())

    def test_supported_python_gate_accepts_312(self) -> None:
        with patch.object(control_plane_cli.sys, "version_info", (3, 12, 0)):
            control_plane_cli._require_workspace_python()


if __name__ == "__main__":
    unittest.main()
