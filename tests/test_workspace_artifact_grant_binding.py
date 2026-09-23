from __future__ import annotations

from dataclasses import replace
import unittest

from runtime.control_plane._verified_workspace_artifact_support import (
    CHECKPOINT_SCHEMA_VERSION,
    FILE_ARTIFACT_CAPABILITY,
    LEGACY_WORKING_STATE_SCHEMA_VERSION,
    PROCEDURE_ID,
    QUALIFICATION_ADMISSION,
    _make_intent,
    _migrate_legacy_workspace_grant,
    _new_working_state,
    _validate_working_state,
    _workspace_grant_ref,
    _workspace_guard_decision,
    _workspace_resource_scope_ref,
)
from runtime.control_plane.verification import ObservationRef, ObservationSnapshot


TASK_ID = "a" * 32
RELATIVE_TARGET = ".chat-agent-platform/stage26-3a/grant-bound.txt"
EXPECTED_SHA = "b" * 64
CONTENT_SIZE = 11


class WorkspaceArtifactGrantBindingTests(unittest.TestCase):
    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot(
            ref=ObservationRef(
                capability=FILE_ARTIFACT_CAPABILITY,
                subject=f"{PROCEDURE_ID}:{TASK_ID}",
                stream_id="workspace-stream:grant-bound",
                sequence=0,
                fingerprint="workspace-state:0",
                observed_at="t0",
            ),
            state={
                "staging": {"exists": False},
                "target": {"exists": False},
            },
        )

    def state(self):
        return _new_working_state(
            TASK_ID,
            self.snapshot(),
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

    def test_new_state_uses_concrete_task_resource_grant_not_shared_admission(self) -> None:
        state = self.state()
        expected = _workspace_grant_ref(
            task_id=TASK_ID,
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        self.assertEqual(CHECKPOINT_SCHEMA_VERSION, 3)
        self.assertEqual(LEGACY_WORKING_STATE_SCHEMA_VERSION, 2)
        self.assertEqual((expected,), state.capability_grant_refs)
        self.assertNotEqual((QUALIFICATION_ADMISSION,), state.capability_grant_refs)

    def test_grant_identity_changes_with_task_path_content_or_size(self) -> None:
        baseline = _workspace_grant_ref(
            task_id=TASK_ID,
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )
        variants = (
            _workspace_grant_ref(
                task_id="c" * 32,
                relative_target=RELATIVE_TARGET,
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE,
            ),
            _workspace_grant_ref(
                task_id=TASK_ID,
                relative_target=".chat-agent-platform/stage26-3a/other.txt",
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE,
            ),
            _workspace_grant_ref(
                task_id=TASK_ID,
                relative_target=RELATIVE_TARGET,
                expected_sha="d" * 64,
                content_size=CONTENT_SIZE,
            ),
            _workspace_grant_ref(
                task_id=TASK_ID,
                relative_target=RELATIVE_TARGET,
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE + 1,
            ),
        )

        self.assertEqual(4, len(set(variants)))
        for variant in variants:
            self.assertNotEqual(baseline, variant)

    def test_resource_scope_binds_exact_path_digest_and_size(self) -> None:
        baseline = _workspace_resource_scope_ref(
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )
        changed = _workspace_resource_scope_ref(
            relative_target=RELATIVE_TARGET,
            expected_sha="e" * 64,
            content_size=CONTENT_SIZE,
        )
        self.assertNotEqual(baseline, changed)
        self.assertIn(RELATIVE_TARGET, baseline)
        self.assertIn(EXPECTED_SHA, baseline)

    def test_schema_3_rejects_legacy_admission_and_schema_2_rejects_new_grant(self) -> None:
        concrete = self.state()
        legacy = replace(
            concrete,
            capability_grant_refs=(QUALIFICATION_ADMISSION,),
        )

        _validate_working_state(
            concrete,
            task_id=TASK_ID,
            schema_version=CHECKPOINT_SCHEMA_VERSION,
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )
        _validate_working_state(
            legacy,
            task_id=TASK_ID,
            schema_version=LEGACY_WORKING_STATE_SCHEMA_VERSION,
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        with self.assertRaisesRegex(ValueError, "capability grant mismatch"):
            _validate_working_state(
                legacy,
                task_id=TASK_ID,
                schema_version=CHECKPOINT_SCHEMA_VERSION,
                relative_target=RELATIVE_TARGET,
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE,
            )
        with self.assertRaisesRegex(ValueError, "capability grant mismatch"):
            _validate_working_state(
                concrete,
                task_id=TASK_ID,
                schema_version=LEGACY_WORKING_STATE_SCHEMA_VERSION,
                relative_target=RELATIVE_TARGET,
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE,
            )

    def test_legacy_state_cannot_authorize_new_mutation_before_forward_handoff(self) -> None:
        concrete = self.state()
        legacy = replace(
            concrete,
            capability_grant_refs=(QUALIFICATION_ADMISSION,),
        )
        intent = _make_intent(
            legacy,
            task_id=TASK_ID,
            transition_id="stage_create",
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        with self.assertRaisesRegex(
            ValueError,
            "concrete workspace grant required before mutation",
        ):
            _workspace_guard_decision(
                legacy,
                intent,
                task_id=TASK_ID,
                transition_id="stage_create",
                relative_target=RELATIVE_TARGET,
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE,
            )

    def test_legacy_forward_handoff_changes_only_active_authority_and_revision(self) -> None:
        snapshot = self.snapshot()
        concrete = self.state()
        legacy = replace(
            concrete,
            capability_grant_refs=(QUALIFICATION_ADMISSION,),
        )
        task_state = {
            "schema_version": LEGACY_WORKING_STATE_SCHEMA_VERSION,
            "prepared_intent": None,
            "working_state": legacy.as_dict(),
        }

        migrated = _migrate_legacy_workspace_grant(
            task_state,
            legacy,
            snapshot,
            task_id=TASK_ID,
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        expected = _workspace_grant_ref(
            task_id=TASK_ID,
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )
        self.assertEqual(CHECKPOINT_SCHEMA_VERSION, task_state["schema_version"])
        self.assertEqual((expected,), migrated.capability_grant_refs)
        self.assertEqual(legacy.revision + 1, migrated.revision)
        self.assertEqual(legacy.attempts, migrated.attempts)
        self.assertEqual(legacy.reconciliations, migrated.reconciliations)
        self.assertEqual(legacy.budgets, migrated.budgets)
        self.assertTrue(migrated.evidence_refs[-1].startswith("workspace-grant-handoff:"))
    def test_concrete_grant_authorizes_exact_transition_before_effect(self) -> None:
        state = self.state()
        intent = _make_intent(
            state,
            task_id=TASK_ID,
            transition_id="stage_create",
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        decision = _workspace_guard_decision(
            state,
            intent,
            task_id=TASK_ID,
            transition_id="stage_create",
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        self.assertTrue(decision.allowed)

    def test_concrete_grant_cannot_be_reused_for_different_resource(self) -> None:
        state = self.state()
        intent = _make_intent(
            state,
            task_id=TASK_ID,
            transition_id="stage_create",
            relative_target=RELATIVE_TARGET,
            expected_sha=EXPECTED_SHA,
            content_size=CONTENT_SIZE,
        )

        with self.assertRaisesRegex(ValueError, "capability grant identity is invalid"):
            _workspace_guard_decision(
                state,
                intent,
                task_id=TASK_ID,
                transition_id="stage_create",
                relative_target=".chat-agent-platform/stage26-3a/other.txt",
                expected_sha=EXPECTED_SHA,
                content_size=CONTENT_SIZE,
            )


if __name__ == "__main__":
    unittest.main()
