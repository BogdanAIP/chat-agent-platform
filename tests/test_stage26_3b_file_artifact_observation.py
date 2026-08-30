from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from runtime.control_plane.file_artifact_observation import (
    FILE_ARTIFACT_CAPABILITY,
    FileArtifactObservationStream,
)
from runtime.control_plane.verification import (
    ExpectedEffect,
    StatePredicate,
    VerificationStatus,
    verify_expected_effect,
)


class Stage263BFileArtifactObservationTests(unittest.TestCase):
    def test_fresh_created_file_verifies_on_same_stream(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            target = root / "artifact.txt"
            observer = FileArtifactObservationStream(
                root=root,
                subject="task:artifact",
                paths={"target": target},
            )
            before = observer.observe()
            target.write_bytes(b"VERIFIED")
            after = observer.observe()
            digest = hashlib.sha256(b"VERIFIED").hexdigest()

            result = verify_expected_effect(
                ExpectedEffect(
                    effect_id="create",
                    before=before.ref,
                    predicates=(
                        StatePredicate.equals("target", "exists", expected=True),
                        StatePredicate.equals("target", "kind", expected="file"),
                        StatePredicate.equals("target", "size", expected=8),
                        StatePredicate.equals("target", "sha256", expected=digest),
                        StatePredicate.present("target", "identity"),
                    ),
                ),
                after,
            )

            self.assertEqual(after.ref.capability, FILE_ARTIFACT_CAPABILITY)
            self.assertEqual(after.ref.sequence, before.ref.sequence + 1)
            self.assertEqual(result.status, VerificationStatus.PASS)

    def test_restart_can_continue_existing_stream_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            target = root / "artifact.txt"
            observer = FileArtifactObservationStream(
                root=root,
                subject="task:restart",
                paths={"target": target},
                stream_id="durable-stream",
                initial_sequence=7,
            )

            snapshot = observer.observe()

            self.assertEqual(snapshot.ref.stream_id, "durable-stream")
            self.assertEqual(snapshot.ref.sequence, 8)

    def test_oversized_file_is_incomplete_not_false_digest_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            target = root / "large.txt"
            target.write_bytes(b"12345")
            observer = FileArtifactObservationStream(
                root=root,
                subject="task:large",
                paths={"target": target},
                max_bytes=4,
            )
            before = observer.observe()
            after = observer.observe()
            result = verify_expected_effect(
                ExpectedEffect(
                    effect_id="digest",
                    before=before.ref,
                    predicates=(
                        StatePredicate.equals("target", "sha256", expected="not-observed"),
                    ),
                ),
                after,
            )

            self.assertFalse(after.complete)
            self.assertNotIn("sha256", after.state["target"])
            self.assertEqual(result.status, VerificationStatus.UNKNOWN)

    def test_symlink_is_observed_as_symlink_not_followed_as_file(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            real = root / "real.txt"
            link = root / "link.txt"
            real.write_text("DATA", encoding="utf-8")
            try:
                link.symlink_to(real)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            observer = FileArtifactObservationStream(
                root=root,
                subject="task:link",
                paths={"target": link},
            )

            snapshot = observer.observe()

            self.assertTrue(snapshot.complete)
            self.assertFalse(snapshot.ambiguous)
            self.assertEqual(snapshot.state["target"]["kind"], "symlink")
            self.assertIsNone(snapshot.state["target"]["sha256"])

    def test_paths_outside_root_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as other_dir:
            with self.assertRaisesRegex(ValueError, "escaped"):
                FileArtifactObservationStream(
                    root=Path(root_dir),
                    subject="task:escape",
                    paths={"target": Path(other_dir) / "outside.txt"},
                )


if __name__ == "__main__":
    unittest.main()
