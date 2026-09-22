from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from runtime.control_plane.semantic_workspace_write import (
    handle_request,
    prepare_workspace_write,
    verify_workspace_write,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SemanticWorkspaceWriteGateTests(unittest.TestCase):
    def prepare_request(
        self,
        root: Path,
        *,
        activation: str = "a" * 32,
        relative_path: str = "notes.txt",
        content: str = "HELLO",
    ) -> dict[str, object]:
        payload = content.encode("utf-8")
        return {
            "operation": "prepare",
            "activation_ref": activation,
            "workspace_root": str(root),
            "relative_path": relative_path,
            "content_sha256": hashlib.sha256(payload).hexdigest(),
            "content_size": len(payload),
        }

    def verify_request(
        self,
        prepare: dict,
        root: Path,
        *,
        activation: str = "a" * 32,
        relative_path: str = "notes.txt",
        content: str = "HELLO",
    ) -> dict[str, object]:
        payload = content.encode("utf-8")
        return {
            "operation": "verify",
            "activation_ref": activation,
            "workspace_root": str(root),
            "relative_path": relative_path,
            "content_sha256": hashlib.sha256(payload).hexdigest(),
            "content_size": len(payload),
            "before": prepare["before"],
        }

    def test_prepare_authorizes_exact_request_and_binds_activation_resource(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = prepare_workspace_write(self.prepare_request(root))
            second = prepare_workspace_write(
                self.prepare_request(root, activation="b" * 32)
            )
            other_path = prepare_workspace_write(
                self.prepare_request(root, relative_path="other.txt")
            )
            other_content = prepare_workspace_write(
                self.prepare_request(root, content="DIFFERENT")
            )

            self.assertEqual("authorized", first["status"])
            self.assertFalse(first["already_satisfied"])
            self.assertEqual("authorized", first["authorization"]["status"])
            self.assertNotEqual(
                first["authorization"]["grant_fingerprint"],
                second["authorization"]["grant_fingerprint"],
            )
            self.assertNotEqual(
                first["authorization"]["grant_fingerprint"],
                other_path["authorization"]["grant_fingerprint"],
            )
            self.assertNotEqual(
                first["authorization"]["grant_fingerprint"],
                other_content["authorization"]["grant_fingerprint"],
            )

    def test_prepare_detects_exact_already_satisfied_noop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.txt").write_text("HELLO", encoding="utf-8")

            prepared = prepare_workspace_write(self.prepare_request(root))

            self.assertEqual("authorized", prepared["status"])
            self.assertTrue(prepared["already_satisfied"])

    def test_verify_passes_only_for_exact_final_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = prepare_workspace_write(self.prepare_request(root))

            (root / "notes.txt").write_text("HELLO", encoding="utf-8")
            verified = verify_workspace_write(
                self.verify_request(prepared, root)
            )
            self.assertEqual("pass", verified["status"])
            self.assertEqual(
                "expected_effect_verified",
                verified["verification"]["reason"],
            )

            prepared_again = prepare_workspace_write(
                self.prepare_request(root, relative_path="bad.txt")
            )
            (root / "bad.txt").write_text("WRONG", encoding="utf-8")
            failed = verify_workspace_write(
                self.verify_request(
                    prepared_again,
                    root,
                    relative_path="bad.txt",
                    content="HELLO",
                )
            )
            self.assertEqual("fail", failed["status"])
            self.assertEqual(
                "expected_effect_failed",
                failed["verification"]["reason"],
            )

    def test_verify_rejects_before_observation_from_other_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = prepare_workspace_write(
                self.prepare_request(root, activation="a" * 32)
            )
            request = self.verify_request(
                prepared,
                root,
                activation="b" * 32,
            )

            with self.assertRaisesRegex(
                ValueError,
                "before observation subject mismatch",
            ):
                verify_workspace_write(request)

    def test_parent_traversal_and_absolute_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("../outside.txt", str(root / "absolute.txt")):
                with self.subTest(relative=relative):
                    with self.assertRaises((ValueError, OSError)):
                        prepare_workspace_write(
                            self.prepare_request(root, relative_path=relative)
                        )

    def test_junction_or_symlink_parent_escape_is_rejected_before_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            link = root / "outside-link"
            try:
                link.symlink_to(
                    Path(outside),
                    target_is_directory=True,
                )
            except (OSError, NotImplementedError):
                self.skipTest("directory symlink/junction unavailable")

            with self.assertRaisesRegex(
                ValueError,
                "escaped its configured root",
            ):
                prepare_workspace_write(
                    self.prepare_request(
                        root,
                        relative_path="outside-link/escape.txt",
                    )
                )

    def test_handle_request_is_closed_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = self.prepare_request(root)
            request["backend"] = "filesystem"

            with self.assertRaisesRegex(ValueError, "unsupported request fields"):
                handle_request(request)

            invalid_activation = self.prepare_request(root)
            invalid_activation["activation_ref"] = "not-an-activation"
            with self.assertRaisesRegex(ValueError, "activation_ref"):
                handle_request(invalid_activation)

            invalid_sha = self.prepare_request(root)
            invalid_sha["content_sha256"] = digest("wrong").upper()
            with self.assertRaisesRegex(ValueError, "content_sha256"):
                handle_request(invalid_sha)


if __name__ == "__main__":
    unittest.main()
