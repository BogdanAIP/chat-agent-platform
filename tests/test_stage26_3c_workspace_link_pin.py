from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane._verified_workspace_artifact_support as workspace_support
import runtime.control_plane.verified_workspace_artifact as workspace_artifact
import runtime.control_plane.windows_file_pin as windows_file_pin


@unittest.skipUnless(os.name == "nt", "verified workspace file pins are Windows-specific")
class Stage263CWorkspaceLinkPinTests(unittest.TestCase):
    def request(self, name: str, content: str) -> dict:
        return {
            "procedure": workspace_artifact.PROCEDURE_ID,
            "artifact_name": name,
            "content": content,
        }

    def execute(self, request: dict, *, workspace: Path, state: Path) -> dict:
        return workspace_artifact.run_verified_workspace_artifact(
            request,
            workspace_root=workspace,
            state_root=state,
            candidate_admission=workspace_artifact.QUALIFICATION_ADMISSION,
        )

    def target_path(self, workspace: Path, name: str) -> Path:
        return workspace / ".chat-agent-platform" / "stage26-3a" / name

    def test_live_pin_blocks_write_replacement_and_namespace_retarget_during_link(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            original_link = workspace_support.os.link
            blocked_errors: list[OSError] = []

            def attack_then_link(source: Path, target: Path) -> None:
                try:
                    handle = source.open("r+b")
                except OSError as exc:
                    blocked_errors.append(exc)
                else:
                    handle.close()
                    self.fail("pinned staging unexpectedly allowed a write handle")

                replacement = source.with_name(source.name + ".replacement")
                replacement.write_bytes(b"FOREIGN")
                try:
                    os.replace(replacement, source)
                except OSError as exc:
                    blocked_errors.append(exc)
                else:
                    self.fail("pinned staging unexpectedly allowed path replacement")

                for directory in (source.parent, source.parent.parent, workspace):
                    moved = directory.with_name(directory.name + ".retargeted")
                    try:
                        os.rename(directory, moved)
                    except OSError as exc:
                        blocked_errors.append(exc)
                    else:
                        self.fail(
                            f"pinned namespace unexpectedly allowed rename of {directory}"
                        )

                original_link(source, target)

            with patch.object(workspace_support.os, "link", new=attack_then_link):
                result = self.execute(
                    self.request("pin-window.txt", "PINNED"),
                    workspace=workspace,
                    state=state,
                )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["action_count"], 3)
            self.assertGreaterEqual(len(blocked_errors), 5)
            target = self.target_path(workspace, "pin-window.txt")
            self.assertEqual(target.read_text(encoding="utf-8"), "PINNED")

    def test_replacement_before_pin_is_rejected_before_hard_link_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_pin = workspace_artifact.pin_file_for_verified_link
            original_identity: dict[str, int] | None = None
            replacement_identity: dict[str, int] | None = None

            @contextmanager
            def replace_then_pin(path: Path, *, workspace_root: Path | None = None):
                nonlocal original_identity, replacement_identity
                original_identity = workspace_artifact._file_identity(path)
                replacement = path.with_name(path.name + ".replacement")
                replacement.write_bytes(b"PINNED")
                path.unlink()
                os.replace(replacement, path)
                replacement_identity = workspace_artifact._file_identity(path)
                self.assertIsNotNone(original_identity)
                self.assertIsNotNone(replacement_identity)
                self.assertNotEqual(original_identity, replacement_identity)
                with real_pin(path, workspace_root=workspace_root):
                    yield

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_link",
                new=replace_then_pin,
            ), patch.object(
                workspace_artifact,
                "_exclusive_link_file",
                side_effect=AssertionError("replaced staging must never be hard-linked"),
            ) as link_mock:
                result = self.execute(
                    self.request("pre-pin-swap.txt", "PINNED"),
                    workspace=workspace,
                    state=state,
                )

            link_mock.assert_not_called()
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "delivery_error_reconciliation_unknown")
            target = self.target_path(workspace, "pre-pin-swap.txt")
            self.assertFalse(target.exists())
            self.assertNotEqual(original_identity, replacement_identity)

    def test_delete_pin_removes_only_opened_staging_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Path(workspace_dir)
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / ".delete-pin.staging"
            target = reserved / "delete-pin.txt"
            staging.write_bytes(b"PINNED_DELETE")
            os.link(staging, target)
            blocked_errors: list[OSError] = []

            with workspace_artifact.pin_file_for_verified_delete(
                staging,
                workspace_root=workspace,
            ) as mark_delete:
                try:
                    handle = target.open("r+b")
                except OSError as exc:
                    blocked_errors.append(exc)
                else:
                    handle.close()
                    self.fail("delete pin unexpectedly allowed write through target hardlink")

                replacement = staging.with_name(staging.name + ".replacement")
                replacement.write_bytes(b"FOREIGN")
                try:
                    os.replace(replacement, staging)
                except OSError as exc:
                    blocked_errors.append(exc)
                else:
                    self.fail("delete pin unexpectedly allowed staging replacement")

                mark_delete()

            self.assertGreaterEqual(len(blocked_errors), 2)
            self.assertFalse(staging.exists())
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), b"PINNED_DELETE")

    def test_delete_revalidates_same_bytes_replacement_in_handle_transition_gap(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Path(workspace_dir)
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / ".delete-gap.staging"
            target = reserved / "delete-gap.txt"
            content = b"SAME_BYTES_GAP"
            staging.write_bytes(content)
            os.link(staging, target)
            original_identity = workspace_artifact._file_identity(staging)
            self.assertIsNotNone(original_identity)

            real_open = windows_file_pin._open_pinned_handle
            replacement_identity: dict[str, int] | None = None
            injected = False

            @contextmanager
            def replace_before_delete_handle(
                path: Path,
                *,
                desired_access: int,
                share_mode: int,
                directory: bool,
            ):
                nonlocal replacement_identity, injected
                if (
                    not directory
                    and desired_access & windows_file_pin._DELETE
                    and not injected
                ):
                    path.unlink()
                    path.write_bytes(content)
                    replacement_identity = workspace_artifact._file_identity(path)
                    self.assertIsNotNone(replacement_identity)
                    self.assertNotEqual(original_identity, replacement_identity)
                    injected = True
                with real_open(
                    path,
                    desired_access=desired_access,
                    share_mode=share_mode,
                    directory=directory,
                ) as opened:
                    yield opened

            with patch.object(
                windows_file_pin,
                "_open_pinned_handle",
                new=replace_before_delete_handle,
            ):
                with windows_file_pin.pin_file_for_verified_delete(
                    staging,
                    workspace_root=workspace,
                ) as mark_delete:
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "changed before handle-bound delete delivery",
                    ):
                        mark_delete()

            self.assertTrue(injected)
            self.assertTrue(staging.exists())
            self.assertEqual(staging.read_bytes(), content)
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), content)
            self.assertFalse(os.path.samefile(staging, target))
            self.assertNotEqual(original_identity, replacement_identity)

    def test_compensation_delete_refuses_same_bytes_replacement_identity(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Path(workspace_dir)
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            path = reserved / "compensation.txt"
            content = b"SAME_BYTES"
            path.write_bytes(content)
            original_identity = workspace_artifact._file_identity(path)
            self.assertIsNotNone(original_identity)
            path.unlink()
            path.write_bytes(content)
            replacement_identity = workspace_artifact._file_identity(path)
            self.assertIsNotNone(replacement_identity)
            self.assertNotEqual(original_identity, replacement_identity)

            removed = workspace_artifact._delete_verified_owned_file(
                path,
                hashlib.sha256(content).hexdigest(),
                original_identity,
                workspace_root=workspace,
            )

            self.assertFalse(removed)
            self.assertTrue(path.exists())
            self.assertEqual(path.read_bytes(), content)

    def test_cleanup_replacement_before_pin_is_not_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as state_dir:
            workspace = Path(workspace_dir)
            state = Path(state_dir)
            real_delete_pin = workspace_artifact.pin_file_for_verified_delete
            original_identity: dict[str, int] | None = None
            replacement_identity: dict[str, int] | None = None
            replaced = False

            @contextmanager
            def replace_then_delete_pin(path: Path, *, workspace_root: Path | None = None):
                nonlocal original_identity, replacement_identity, replaced
                if path.name.endswith(".staging") and not replaced:
                    original_identity = workspace_artifact._file_identity(path)
                    path.unlink()
                    path.write_bytes(b"CLEAN")
                    replacement_identity = workspace_artifact._file_identity(path)
                    self.assertIsNotNone(original_identity)
                    self.assertIsNotNone(replacement_identity)
                    self.assertNotEqual(original_identity, replacement_identity)
                    replaced = True
                with real_delete_pin(path, workspace_root=workspace_root) as mark_delete:
                    yield mark_delete

            with patch.object(
                workspace_artifact,
                "pin_file_for_verified_delete",
                new=replace_then_delete_pin,
            ):
                result = self.execute(
                    self.request("cleanup-swap.txt", "CLEAN"),
                    workspace=workspace,
                    state=state,
                )

            self.assertTrue(replaced)
            self.assertEqual(result["status"], "abstained")
            self.assertEqual(result["escalation_reason"], "delivery_error_reconciliation_unknown")
            checkpoint_files = list(state.glob("*.json"))
            self.assertEqual(len(checkpoint_files), 1)
            task_id = checkpoint_files[0].stem
            staging = (
                workspace
                / ".chat-agent-platform"
                / "stage26-3a"
                / f".cleanup-swap.txt.{task_id}.staging"
            )
            target = self.target_path(workspace, "cleanup-swap.txt")
            self.assertTrue(staging.exists())
            self.assertEqual(staging.read_bytes(), b"CLEAN")
            self.assertTrue(target.exists())
            self.assertEqual(target.read_bytes(), b"CLEAN")
            self.assertNotEqual(original_identity, replacement_identity)


if __name__ == "__main__":
    unittest.main()
