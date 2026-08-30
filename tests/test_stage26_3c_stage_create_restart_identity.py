from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.control_plane.verified_workspace_artifact as workspace_artifact
from runtime.control_plane.working_state import ReconciliationStatus


class Stage263CStageCreateRestartIdentityTests(unittest.TestCase):
    def test_stage_create_fresh_bytes_cannot_self_authenticate_after_process_proof_is_gone(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Path(workspace_dir)
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            staging = reserved / ".self-auth.staging"
            staging.write_bytes(b"SAME_BYTES")

            observer = workspace_artifact.FileArtifactObservationStream(
                root=workspace,
                subject="stage-create-self-auth",
                paths={"staging": staging, "target": reserved / "target.txt"},
                max_bytes=workspace_artifact.MAX_CONTENT_BYTES,
            )
            snapshot = observer.observe()
            status = workspace_artifact._direct_reconciliation_status(
                "stage_create",
                snapshot,
                content_size=len(b"SAME_BYTES"),
                expected_sha=workspace_artifact._sha256(b"SAME_BYTES"),
                staging_identity=None,
            )
            self.assertIs(status, ReconciliationStatus.STILL_UNKNOWN)
            predicates = workspace_artifact._reconciliation_predicates(
                "stage_create",
                ReconciliationStatus.CONFIRMED_APPLIED,
                snapshot,
                content_size=len(b"SAME_BYTES"),
                expected_sha=workspace_artifact._sha256(b"SAME_BYTES"),
                staging_identity=None,
                target_identity=None,
            )
            self.assertIsNone(predicates)

    def test_stage_create_missing_state_can_still_confirm_not_applied_for_safe_retry(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace = Path(workspace_dir)
            reserved = workspace / ".chat-agent-platform" / "stage26-3a"
            reserved.mkdir(parents=True)
            observer = workspace_artifact.FileArtifactObservationStream(
                root=workspace,
                subject="stage-create-not-applied",
                paths={
                    "staging": reserved / ".missing.staging",
                    "target": reserved / "missing.txt",
                },
                max_bytes=workspace_artifact.MAX_CONTENT_BYTES,
            )
            snapshot = observer.observe()
            status = workspace_artifact._direct_reconciliation_status(
                "stage_create",
                snapshot,
                content_size=4,
                expected_sha=workspace_artifact._sha256(b"DATA"),
                staging_identity=None,
            )
            self.assertIs(status, ReconciliationStatus.CONFIRMED_NOT_APPLIED)


if __name__ == "__main__":
    unittest.main()
