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

    @staticmethod
    def _open_reparse_writer(path: Path):
        (
            api_ctypes,
            create_file,
            close_handle,
            _,
            _,
            _,
            _,
        ) = windows_file_pin._win32_api()
        handle = create_file(
            str(path),
            0x00000100,  # FILE_WRITE_ATTRIBUTES
            0x00000001 | 0x00000002 | 0x00000004,  # READ|WRITE|DELETE sharing
            None,
            windows_file_pin._OPEN_EXISTING,
            windows_file_pin._FILE_FLAG_OPEN_REPARSE_POINT
            | windows_file_pin._FILE_FLAG_BACKUP_SEMANTICS,
            None,
        )
        invalid = api_ctypes.c_void_p(-1).value
        if handle == invalid:
            code = api_ctypes.get_last_error()
            raise OSError(code, api_ctypes.FormatError(code), str(path))
        return api_ctypes, handle, close_handle

    @staticmethod
    def _set_mount_point(handle, target: Path) -> None:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        device_io_control = kernel32.DeviceIoControl
        device_io_control.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        device_io_control.restype = wintypes.BOOL

        substitute = "\\??\\" + str(target.resolve())
        printed = str(target.resolve())
        substitute_bytes = substitute.encode("utf-16-le")
        printed_bytes = printed.encode("utf-16-le")
        path_buffer = substitute_bytes + b"\x00\x00" + printed_bytes + b"\x00\x00"
        substitute_offset = 0
        substitute_length = len(substitute_bytes)
        print_offset = substitute_length + 2
        print_length = len(printed_bytes)
        mount_payload = (
            substitute_offset.to_bytes(2, "little")
            + substitute_length.to_bytes(2, "little")
            + print_offset.to_bytes(2, "little")
            + print_length.to_bytes(2, "little")
            + path_buffer
        )
        tag = 0xA0000003  # IO_REPARSE_TAG_MOUNT_POINT
        header = (
            tag.to_bytes(4, "little")
            + len(mount_payload).to_bytes(2, "little")
            + b"\x00\x00"
        )
        payload = header + mount_payload
        buffer = ctypes.create_string_buffer(payload, len(payload))
        returned = wintypes.DWORD()
        if not device_io_control(
            handle,
            0x000900A4,  # FSCTL_SET_REPARSE_POINT
            buffer,
            len(payload),
            None,
            0,
            ctypes.byref(returned),
            None,
        ):
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code), str(target))

    @staticmethod
    def _delete_mount_point(handle) -> None:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        device_io_control = kernel32.DeviceIoControl
        device_io_control.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        device_io_control.restype = wintypes.BOOL
        tag = 0xA0000003
        payload = tag.to_bytes(4, "little") + b"\x00\x00\x00\x00"
        buffer = ctypes.create_string_buffer(payload, len(payload))
        returned = wintypes.DWORD()
        if not device_io_control(
            handle,
            0x000900AC,  # FSCTL_DELETE_REPARSE_POINT
            buffer,
            len(payload),
            None,
            0,
            ctypes.byref(returned),
            None,
        ):
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code))

    def test_stage_create_holds_namespace_pins_before_exclusive_open(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_create_handle = windows_file_pin._create_new_pinned_handle_at
            attack_ran = False
            blocked: list[OSError] = []

            @contextmanager
            def attack_then_create(parent_handle, path: Path):
                nonlocal attack_ran
                if not attack_ran:
                    attack_ran = True
                    # The rooted leaf helper is entered only after the trusted
                    # descendant namespace has been pinned. Renaming either
                    # reserved directory must therefore be denied before the
                    # exclusive leaf create is dispatched.
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
                with original_create_handle(parent_handle, path) as created:
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
                "_create_new_pinned_handle_at",
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

    def test_stage_create_reparse_insert_after_check_cannot_escape_rooted_leaf_create(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir, tempfile.TemporaryDirectory() as external_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            external = Path(external_dir)
            name = "rooted-reparse-race.txt"
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            original_create = windows_file_pin._create_new_pinned_handle_at
            attack_ran = False
            escaped_during_create = False

            @contextmanager
            def reparse_then_rooted_create(parent_handle, path: Path):
                nonlocal attack_ran, escaped_during_create
                attack_ran = True
                _, attack_handle, close_handle = self._open_reparse_writer(path.parent)
                reparse_set = False
                try:
                    self._set_mount_point(attack_handle, external)
                    reparse_set = True
                    with original_create(parent_handle, path) as created:
                        escaped_during_create = (external / path.name).exists()
                        yield created
                finally:
                    if reparse_set:
                        self._delete_mount_point(attack_handle)
                    close_handle(attack_handle)

            with patch.object(
                windows_file_pin,
                "_create_new_pinned_handle_at",
                new=reparse_then_rooted_create,
            ):
                result = workspace_artifact.run_verified_workspace_artifact(
                    {
                        "procedure": workspace_artifact.PROCEDURE_ID,
                        "artifact_name": name,
                        "content": "MUST_NOT_ESCAPE_ROOTED_CREATE",
                    },
                    workspace_root=workspace,
                    state_root=state,
                    candidate_admission=workspace_artifact.QUALIFICATION_ADMISSION,
                )

            self.assertTrue(attack_ran)
            self.assertFalse(
                escaped_during_create,
                "handle-relative NtCreateFile traversed the raced parent reparse point",
            )
            self.assertFalse((external / f".{name}.{result['task_id']}.staging").exists())
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["action_count"], 0)
            self.assertEqual(result["escalation_reason"], "delivery_error_confirmed_not_applied")
            self.assertFalse(list(reserved.glob(f".{name}.*.staging")))

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
