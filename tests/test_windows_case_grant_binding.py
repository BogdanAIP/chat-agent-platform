from __future__ import annotations

import unittest

from runtime.control_plane.verification import ObservationRef, ObservationSnapshot
from runtime.control_plane.windows_case_update import (
    _new_windows_working_state,
    _record_windows_case_attempt,
    _windows_case_grant_ref,
    _windows_case_guard_decision,
    _windows_case_intent,
    _windows_case_resource_scope_ref,
    _windows_unknown_failure,
)
from runtime.control_plane.working_state import MutatingOutcome


TASK_ID = "1" * 32
RUN_ID = "12AB34CD"
HEAD = "a" * 40
CASE_ID = "CASE-12AB34CD-4821"
NOTE_SHA = "b" * 64
STATUS = "Approved"
SUBJECT = f"windows_case_update_v1:{TASK_ID}"
STREAM = f"{TASK_ID}:windows-desktop"


def snapshot(sequence: int, fingerprint: str, observed_at: str) -> ObservationSnapshot:
    return ObservationSnapshot(
        ref=ObservationRef(
            capability="windows.desktop",
            subject=SUBJECT,
            stream_id=STREAM,
            sequence=sequence,
            fingerprint=fingerprint,
            observed_at=observed_at,
        ),
        state={"sequence": sequence},
    )


def new_state():
    return _new_windows_working_state(
        task_id=TASK_ID,
        initial=snapshot(1, "c" * 64, "2026-09-23T12:00:00+00:00"),
        run_id=RUN_ID,
        expected_head=HEAD,
        case_id=CASE_ID,
        note_sha256=NOTE_SHA,
        requested_status=STATUS,
    )


class WindowsCaseGrantBindingTests(unittest.TestCase):
    def test_resource_and_grant_identity_bind_exact_task_request_and_session(self) -> None:
        base_scope = _windows_case_resource_scope_ref(
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        self.assertNotEqual(
            base_scope,
            _windows_case_resource_scope_ref(
                run_id=RUN_ID,
                expected_head=HEAD,
                case_id=CASE_ID,
                note_sha256="d" * 64,
                requested_status=STATUS,
            ),
        )
        self.assertNotEqual(
            base_scope,
            _windows_case_resource_scope_ref(
                run_id=RUN_ID,
                expected_head=HEAD,
                case_id=CASE_ID,
                note_sha256=NOTE_SHA,
                requested_status="Needs Review",
            ),
        )

        base_grant = _windows_case_grant_ref(
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        self.assertNotEqual(
            base_grant,
            _windows_case_grant_ref(
                task_id="2" * 32,
                run_id=RUN_ID,
                expected_head=HEAD,
                case_id=CASE_ID,
                note_sha256=NOTE_SHA,
                requested_status=STATUS,
            ),
        )
        self.assertNotEqual(
            base_grant,
            _windows_case_grant_ref(
                task_id=TASK_ID,
                run_id=RUN_ID,
                expected_head="e" * 40,
                case_id=CASE_ID,
                note_sha256=NOTE_SHA,
                requested_status=STATUS,
            ),
        )

    def test_exact_grant_authorizes_one_fixed_transition(self) -> None:
        state = new_state()
        intent = _windows_case_intent(
            state,
            task_id=TASK_ID,
            transition_id="select_case",
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        decision = _windows_case_guard_decision(
            state,
            intent,
            transition_id="select_case",
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        self.assertTrue(decision.allowed)

        changed_request = _windows_case_guard_decision(
            state,
            intent,
            transition_id="select_case",
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256="d" * 64,
            requested_status=STATUS,
        )
        self.assertFalse(changed_request.allowed)

        unknown_action_intent = _windows_case_intent(
            state,
            task_id=TASK_ID,
            transition_id="delete_case",
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        unknown_action = _windows_case_guard_decision(
            state,
            unknown_action_intent,
            transition_id="delete_case",
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        self.assertFalse(unknown_action.allowed)

    def test_successful_authorized_attempt_consumes_budget_and_advances_observation(self) -> None:
        state = new_state()
        intent = _windows_case_intent(
            state,
            task_id=TASK_ID,
            transition_id="select_case",
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        state = _record_windows_case_attempt(
            state,
            intent,
            MutatingOutcome.VERIFIED_APPLIED,
            None,
            transition_id="select_case",
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        state = state.record_observation(
            snapshot(2, "d" * 64, "2026-09-23T12:00:01+00:00").ref,
            expected_revision=state.revision,
        )

        self.assertEqual(len(state.attempts), 1)
        self.assertIs(state.attempts[0].outcome, MutatingOutcome.VERIFIED_APPLIED)
        self.assertEqual(state.observation_ref.sequence, 2)
        self.assertEqual(
            sorted(item.used for item in state.budgets),
            [0, 0, 0, 0, 1, 1, 1],
        )

        next_intent = _windows_case_intent(
            state,
            task_id=TASK_ID,
            transition_id="focus_note",
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        self.assertTrue(
            _windows_case_guard_decision(
                state,
                next_intent,
                transition_id="focus_note",
                task_id=TASK_ID,
                run_id=RUN_ID,
                expected_head=HEAD,
                case_id=CASE_ID,
                note_sha256=NOTE_SHA,
                requested_status=STATUS,
            ).allowed
        )

    def test_unknown_outcome_blocks_later_physical_transition(self) -> None:
        state = new_state()
        intent = _windows_case_intent(
            state,
            task_id=TASK_ID,
            transition_id="select_case",
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        state = _record_windows_case_attempt(
            state,
            intent,
            MutatingOutcome.OUTCOME_UNKNOWN,
            _windows_unknown_failure(intent),
            transition_id="select_case",
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        state = state.record_observation(
            snapshot(2, "d" * 64, "2026-09-23T12:00:01+00:00").ref,
            expected_revision=state.revision,
        )

        next_intent = _windows_case_intent(
            state,
            task_id=TASK_ID,
            transition_id="focus_note",
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        decision = _windows_case_guard_decision(
            state,
            next_intent,
            transition_id="focus_note",
            task_id=TASK_ID,
            run_id=RUN_ID,
            expected_head=HEAD,
            case_id=CASE_ID,
            note_sha256=NOTE_SHA,
            requested_status=STATUS,
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(state.unresolved_attempts())


if __name__ == "__main__":
    unittest.main()
