from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane._verified_workspace_artifact_support as workspace_support
import runtime.control_plane.verified_workspace_artifact as workspace_artifact
import runtime.control_plane.windows_file_pin as windows_file_pin


@unittest.skipUnless(os.name == "nt", "workspace namespace pin is Windows-specific")
class Stage263CStageCreateNamespacePinTests(unittest.TestCase):
    @staticmethod
    def _create_junction(link: Path, target: Path) -> None:
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"failed to create test junction {link} -> {target}: "
                f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
            )

    def test_stage_create_holds_namespace_pins_before_exclusive_open(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_create_handle = windows_file_pin._create_new_pinned_handle
            attack_ran = False
            blocked: list[OSError] = []

            @contextmanager
            def attack_then_create(path: Path):
                nonlocal attack_ran
                if not attack_ran:
                    attack_ran = True
                    # _create_new_pinned_handle is entered only after the trusted
                    # descendant namespace has been pinned. Renaming either
                    # reserved directory must therefore be denied before the
                    # exclusive leaf create can resolve its path.
                    for directory in (path.parent, path.parent.parent):
                        moved = directory.with_name(directory.name + ".retargeted")
                        try:
                            os.rename(directory, moved)
                        except OSError as exc:
                            blocked.append(exc)
                        else:
                            self.fail(
                                f"stage-create namespace pin allowed replacement precursor for {directory}"
                            )
                with original_create_handle(path) as created:
                    yield created

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
            with patch.object(
                windows_file_pin,
                "_create_new_pinned_handle",
                new=attack_then_create,
            ):
                result = workspace_artifact.run_verified_workspace_artifact(
                    request,
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=workspace_artifact.QUALIFICATION_ADMISSION,
                )

            self.assertTrue(attack_ran)
            self.assertEqual(len(blocked), 2)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            target = workspace / ".chat-agent-platform" / "stage26-3a" / "stage-create-pin.txt"
            self.assertEqual(target.read_text(encoding="utf-8"), "PINNED_STAGE_CREATE")

    def test_stage_create_leaf_pin_survives_after_observation_and_receipt_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            name = "stage-receipt-pin.txt"
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            target = reserved / name
            original_observe = workspace_artifact.FileArtifactObservationStream.observe
            original_write_checkpoint = workspace_artifact._write_checkpoint
            blocked_phases: list[str] = []
            allowed_phases: list[str] = []
            observation_probed = False
            checkpoint_probed = False

            def staging_path() -> Path | None:
                matches = list(reserved.glob(f".{name}.*.staging")) if reserved.exists() else []
                return matches[0] if len(matches) == 1 else None

            def probe_write_handle(phase: str) -> None:
                staging = staging_path()
                self.assertIsNotNone(staging)
                try:
                    handle = staging.open("r+b")
                except OSError:
                    blocked_phases.append(phase)
                else:
                    handle.close()
                    allowed_phases.append(phase)

            def observe_with_probe(stream):
                nonlocal observation_probed
                if (
                    not observation_probed
                    and windows_file_pin.stage_create_delivery_proof_live()
                    and staging_path() is not None
                    and not target.exists()
                ):
                    observation_probed = True
                    probe_write_handle("stage_after_observation_entry")
                return original_observe(stream)

            def checkpoint_with_probe(state_root: Path, task_state: dict) -> None:
                nonlocal checkpoint_probed
                if (
                    not checkpoint_probed
                    and task_state.get("current_node") == "staged_verified"
                    and task_state.get("prepared_intent") is None
                    and windows_file_pin.stage_create_delivery_proof_live()
                ):
                    checkpoint_probed = True
                    probe_write_handle("staged_verified_checkpoint")
                original_write_checkpoint(state_root, task_state)

            with patch.object(
                workspace_artifact.FileArtifactObservationStream,
                "observe",
                new=observe_with_probe,
            ), patch.object(
                workspace_artifact,
                "_write_checkpoint",
                new=checkpoint_with_probe,
            ):
                result = workspace_artifact.run_verified_workspace_artifact(
                    {
                        "procedure": workspace_artifact.PROCEDURE_ID,
                        "artifact_name": name,
                        "content": "PINNED_STAGE_RECEIPT",
                    },
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=workspace_artifact.QUALIFICATION_ADMISSION,
                )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertTrue(observation_probed)
            self.assertTrue(checkpoint_probed)
            self.assertEqual(allowed_phases, [])
            self.assertEqual(
                blocked_phases,
                ["stage_after_observation_entry", "staged_verified_checkpoint"],
            )
            self.assertFalse(windows_file_pin.stage_create_delivery_proof_live())
            self.assertEqual(target.read_text(encoding="utf-8"), "PINNED_STAGE_RECEIPT")

    def test_stage_create_rejects_preexisting_junction_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as external_dir:
            workspace = Path(workspace_dir)
            external = Path(external_dir)
            external_stage = external / "stage26-3a"
            external_stage.mkdir()
            reserved_parent = workspace / ".chat-agent-platform"
            self._create_junction(reserved_parent, external)
            staging = reserved_parent / "stage26-3a" / ".preexisting.staging"
            try:
                self.assertEqual(
                    windows_file_pin._infer_workspace_root(staging),
                    workspace,
                    "workspace trust must be reconstructed lexically, not by following the junction",
                )
                with self.assertRaisesRegex(ValueError, "reparse point"):
                    windows_file_pin.create_file_in_pinned_namespace(staging, b"MUST_NOT_ESCAPE")
                self.assertFalse((external_stage / ".preexisting.staging").exists())
            finally:
                windows_file_pin.release_stage_create_delivery_proof()
                if reserved_parent.exists() or reserved_parent.is_symlink():
                    os.rmdir(reserved_parent)

    def test_stage_create_rejects_junction_inserted_before_descendant_handle_open(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as external_dir:
            workspace = Path(workspace_dir)
            external = Path(external_dir)
            reserved_parent = workspace / ".chat-agent-platform"
            reserved_stage = reserved_parent / "stage26-3a"
            reserved_stage.mkdir(parents=True)
            external_stage = external / "stage26-3a"
            external_stage.mkdir()
            staging = reserved_stage / ".interleaved.staging"
            moved_parent = workspace / ".chat-agent-platform.original"
            original_open_pinned = windows_file_pin._open_pinned_handle
            attack_ran = False

            @contextmanager
            def attack_then_pin(path: Path, *, desired_access: int, share_mode: int, directory: bool):
                nonlocal attack_ran
                if not attack_ran and directory and path.name == ".chat-agent-platform":
                    attack_ran = True
                    os.rename(reserved_parent, moved_parent)
                    self._create_junction(reserved_parent, external)
                with original_open_pinned(
                    path,
                    desired_access=desired_access,
                    share_mode=share_mode,
                    directory=directory,
                ) as pinned:
                    yield pinned

            try:
                with patch.object(windows_file_pin, "_open_pinned_handle", new=attack_then_pin):
                    with self.assertRaisesRegex(ValueError, "reparse point"):
                        windows_file_pin.create_file_in_pinned_namespace(
                            staging,
                            b"MUST_NOT_ESCAPE_INTERLEAVED",
                        )
                self.assertTrue(attack_ran)
                self.assertFalse((external_stage / ".interleaved.staging").exists())
            finally:
                windows_file_pin.release_stage_create_delivery_proof()
                if reserved_parent.exists() or reserved_parent.is_symlink():
                    os.rmdir(reserved_parent)
                if moved_parent.exists():
                    os.rename(moved_parent, reserved_parent)


if __name__ == "__main__":
    unittest.main()
