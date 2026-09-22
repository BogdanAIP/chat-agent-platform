from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CapCoreBoundaryTests(unittest.TestCase):
    def run_isolated(self, script: str) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        return json.loads(completed.stdout)

    def test_plain_control_plane_import_is_provider_neutral(self) -> None:
        value = self.run_isolated(
            """
import json
import sys
import runtime.control_plane

blocked = [
    "runtime.control_plane.file_artifact_observation",
    "runtime.control_plane.verified_workspace_artifact",
    "runtime.control_plane._verified_workspace_artifact_support",
    "runtime.control_plane._verified_workspace_artifact_runtime",
    "runtime.control_plane.windows_file_pin",
    "runtime.control_plane.windows_observation",
    "runtime.control_plane.windows_transition",
]
print(json.dumps({
    "blocked_loaded": [name for name in blocked if name in sys.modules],
    "has_working_state": hasattr(runtime.control_plane, "WorkingState"),
    "has_verification": hasattr(runtime.control_plane, "verify_expected_effect"),
}))
"""
        )
        self.assertEqual([], value["blocked_loaded"])
        self.assertTrue(value["has_working_state"])
        self.assertTrue(value["has_verification"])

    def test_star_import_is_core_only_and_provider_neutral(self) -> None:
        value = self.run_isolated(
            """
import json
import sys
namespace = {}
exec("from runtime.control_plane import *", namespace)
blocked = [
    "runtime.control_plane.file_artifact_observation",
    "runtime.control_plane.verified_workspace_artifact",
    "runtime.control_plane._verified_workspace_artifact_support",
    "runtime.control_plane._verified_workspace_artifact_runtime",
    "runtime.control_plane.windows_file_pin",
    "runtime.control_plane.windows_observation",
    "runtime.control_plane.windows_transition",
]
print(json.dumps({
    "blocked_loaded": [name for name in blocked if name in sys.modules],
    "working_state_exported": "WorkingState" in namespace,
    "provider_exports": sorted(name for name in (
        "FILE_ARTIFACT_CAPABILITY",
        "run_verified_workspace_artifact",
        "WINDOWS_DESKTOP_CAPABILITY",
    ) if name in namespace),
}))
"""
        )
        self.assertEqual([], value["blocked_loaded"])
        self.assertTrue(value["working_state_exported"])
        self.assertEqual([], value["provider_exports"])

    def test_workspace_compatibility_export_loads_hardening_lazily(self) -> None:
        value = self.run_isolated(
            """
import json
import sys
import runtime.control_plane as control_plane

before = "runtime.control_plane._verified_workspace_artifact_runtime" in sys.modules
runner = control_plane.run_verified_workspace_artifact
from runtime.control_plane import verified_workspace_artifact

print(json.dumps({
    "before": before,
    "after": "runtime.control_plane._verified_workspace_artifact_runtime" in sys.modules,
    "same_runner": runner is verified_workspace_artifact.run_verified_workspace_artifact,
    "runner_name": runner.__name__,
}))
"""
        )
        self.assertFalse(value["before"])
        self.assertTrue(value["after"])
        self.assertTrue(value["same_runner"])
        self.assertEqual("_run_workspace_artifact_with_stage_create_proof_cleanup", value["runner_name"])

    def test_generic_state_consumers_share_neutral_local_state_primitive(self) -> None:
        from runtime.control_plane import delegation_state
        from runtime.control_plane import independent_review_state
        from runtime.control_plane import local_state
        from runtime.control_plane import _verified_workspace_artifact_support as workspace_support

        self.assertIs(delegation_state._acquire_task_lock, local_state.acquire_task_lock)
        self.assertIs(delegation_state._safe_child, local_state.safe_child)
        self.assertIs(independent_review_state._acquire_task_lock, local_state.acquire_task_lock)
        self.assertIs(independent_review_state._safe_child, local_state.safe_child)
        self.assertIs(workspace_support._acquire_task_lock, local_state.acquire_task_lock)
        self.assertIs(workspace_support._safe_child, local_state.safe_child)

    def test_installed_semantic_bundle_contains_new_core_dependencies(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "semantic-projection.yml"
        ).read_text(encoding="utf-8")
        manager = (ROOT / "scripts" / "bootstrap-manager-runtime.ps1").read_text(
            encoding="utf-8"
        )
        for relative in (
            "runtime/control_plane/local_state.py",
            "runtime/control_plane/authorization.py",
            "runtime/control_plane/_verified_workspace_artifact_runtime.py",
        ):
            with self.subTest(relative=relative):
                self.assertIn(relative, workflow)
                self.assertIn(relative.replace("/", "\\"), manager)

    def test_semantic_mutation_gate_assets_are_in_both_installed_bundles(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "semantic-projection.yml"
        ).read_text(encoding="utf-8")
        manager = (ROOT / "scripts" / "bootstrap-manager-runtime.ps1").read_text(
            encoding="utf-8"
        )
        for relative in (
            "runtime/semantic-projection/lib/semantic-activation.mjs",
            "runtime/semantic-projection/lib/workspace-write-bridge.mjs",
            "runtime/control_plane/semantic_workspace_write.py",
        ):
            with self.subTest(relative=relative):
                self.assertIn(relative, workflow)
                self.assertIn(relative.replace("/", "\\"), manager)

    def test_local_state_lock_remains_fail_closed_and_reusable_after_release(self) -> None:
        from runtime.control_plane.local_state import acquire_task_lock

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "state"
            task_id = "a" * 32
            first = acquire_task_lock(root, task_id)
            try:
                with self.assertRaisesRegex(BlockingIOError, "task_already_running"):
                    acquire_task_lock(root, task_id)
            finally:
                first.close()

            second = acquire_task_lock(root, task_id)
            second.close()


if __name__ == "__main__":
    unittest.main()
