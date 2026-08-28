from __future__ import annotations

import json
import unittest

from runtime.control_plane.verification import (
    ObservationRef,
    VerificationResult,
    VerificationStatus,
)
from runtime.control_plane.working_state import (
    AttemptIntent,
    BudgetKind,
    FailureCategory,
    FailureReason,
    LoopGuard,
    LoopGuardPolicy,
    MutatingOutcome,
    ReconciliationStatus,
    WorkingState,
    reconciliation_effect_id,
)


class WorkingStateRecoveryTests(unittest.TestCase):
    def observation(
        self,
        sequence: int = 0,
        fingerprint: str = "state-a",
        *,
        stream_id: str = "scope-1",
        capability: str = "windows",
        subject: str = "case-1",
    ) -> ObservationRef:
        return ObservationRef(
            capability=capability,
            subject=subject,
            stream_id=stream_id,
            sequence=sequence,
            fingerprint=fingerprint,
            observed_at=f"t{sequence}",
        )

    def state(
        self,
        *,
        task_budget: int = 5,
        procedure_budget: int = 5,
        strategy_budgets: dict[str, int] | None = None,
        observation: ObservationRef | None = None,
    ) -> WorkingState:
        observation = observation or self.observation()
        return WorkingState.create(
            task_id="task-26c",
            task_budget=task_budget,
            procedure_budget=procedure_budget,
            strategy_budgets=strategy_budgets or {"s1": 5, "s2": 5, "s3": 5},
            observation_ref=observation,
            actor_ref="manager",
            execution_environment_ref="env-1",
            evidence_scope_ref=observation.stream_id,
            procedure_ref="procedure:v1",
            user_constraints=("target-only",),
            subgoal_refs=("update-case",),
            evidence_refs=(f"obs:{observation.sequence}",),
            capability_grant_refs=("grant:update",),
        )

    def intent(
        self,
        state: WorkingState,
        *,
        operation: str = "op-1",
        strategy: str = "s1",
        action: str = "click-save",
        observation: ObservationRef | None = None,
        evidence_refs: tuple[str, ...] | None = None,
    ) -> AttemptIntent:
        observation = observation or state.observation_ref
        return AttemptIntent(
            operation_id=operation,
            strategy_id=strategy,
            action_fingerprint=action,
            observation_ref=observation,
            actor_ref="manager",
            execution_environment_ref="env-1",
            evidence_scope_ref="scope-1",
            evidence_refs=(
                evidence_refs
                if evidence_refs is not None
                else (f"obs:{observation.sequence}",)
            ),
        )

    def failure(
        self,
        intent: AttemptIntent,
        outcome: MutatingOutcome = MutatingOutcome.NOT_APPLIED,
        *,
        code: str = "no-effect",
        retryable: bool = True,
        reconciliation_required: bool = False,
    ) -> FailureReason:
        return FailureReason(
            code=code,
            category=FailureCategory.ACTION_NO_EFFECT,
            message="The action produced no verified effect.",
            retryable=retryable,
            reconciliation_required=reconciliation_required,
            operation_id=intent.operation_id,
            strategy_id=intent.strategy_id,
            outcome=outcome,
            evidence_refs=("obs:after",),
        )

    def apply(
        self,
        state: WorkingState,
        intent: AttemptIntent,
        outcome: MutatingOutcome = MutatingOutcome.NOT_APPLIED,
        failure: FailureReason | None = None,
        *,
        guard: LoopGuard | None = None,
    ) -> WorkingState:
        if outcome is not MutatingOutcome.VERIFIED_APPLIED and failure is None:
            failure = self.failure(intent, outcome)
        return state.record_attempt(
            intent,
            outcome,
            failure,
            expected_revision=state.revision,
            guard=guard,
        )

    def unknown_state(self) -> WorkingState:
        state = self.state()
        intent = self.intent(state)
        failure = FailureReason(
            code="delivery-unknown",
            category=FailureCategory.RUNTIME_UNCERTAIN,
            message="Delivery outcome is unknown.",
            retryable=False,
            reconciliation_required=True,
            operation_id=intent.operation_id,
            strategy_id=intent.strategy_id,
            outcome=MutatingOutcome.OUTCOME_UNKNOWN,
        )
        return self.apply(
            state,
            intent,
            MutatingOutcome.OUTCOME_UNKNOWN,
            failure,
        )

    def verification(
        self,
        attempt,
        status: ReconciliationStatus,
        *,
        observation: ObservationRef | None = None,
        verification_status: VerificationStatus = VerificationStatus.PASS,
        evidence_batch_id: str | None = "batch-1",
    ) -> VerificationResult:
        observation = observation or self.observation(
            attempt.intent.observation_ref.sequence + 1,
            "fresh",
        )
        return VerificationResult(
            effect_id=reconciliation_effect_id(
                attempt.intent.operation_id,
                attempt.revision_after,
                status,
            ),
            status=verification_status,
            reason="reconciliation",
            observation=observation,
            evidence_batch_id=evidence_batch_id,
        )

    def test_structured_failure_and_observation_survive_json_round_trip(self) -> None:
        state = self.state()
        state = self.apply(state, self.intent(state))
        restored = WorkingState.from_dict(json.loads(json.dumps(state.as_dict())))
        self.assertEqual(restored, state)
        self.assertEqual(restored.attempts[0].failure.code, "no-effect")
        self.assertEqual(restored.observation_ref, state.observation_ref)

    def test_stale_working_state_revision_blocks_before_attempt(self) -> None:
        state = self.state()
        decision = LoopGuard().evaluate(
            state,
            self.intent(state),
            expected_revision=99,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.failure.code, "stale_working_state")

    def test_stale_concrete_observation_cannot_authorize_attempt(self) -> None:
        state = self.state()
        stale = state.observation_ref
        state = state.record_observation(
            self.observation(1, "new-state"),
            expected_revision=state.revision,
        )
        decision = LoopGuard().evaluate(
            state,
            self.intent(state, observation=stale),
            expected_revision=state.revision,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.failure.code, "stale_or_mismatched_observation")

    def test_outcome_unknown_requires_reconciliation_before_same_operation_retry(self) -> None:
        state = self.unknown_state()
        decision = LoopGuard().evaluate(
            state,
            self.intent(state, strategy="s2", action="alternate-save"),
            expected_revision=state.revision,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(
            decision.failure.code,
            "logical_operation_reconciliation_required",
        )

    def test_fresh_confirmed_not_applied_reconciliation_allows_retry(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        fresh = self.observation(1, "fresh-authoritative")
        state = state.record_reconciliation(
            operation_id=attempt.intent.operation_id,
            attempt_revision=attempt.revision_after,
            status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
            verification=self.verification(
                attempt,
                ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                observation=fresh,
            ),
            expected_revision=state.revision,
        )
        candidate = self.intent(
            state,
            strategy="s2",
            action="alternate-save",
        )
        self.assertTrue(
            LoopGuard().evaluate(
                state,
                candidate,
                expected_revision=state.revision,
            ).allowed
        )

    def test_confirmed_applied_reconciliation_prevents_redelivery(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        state = state.record_reconciliation(
            operation_id=attempt.intent.operation_id,
            attempt_revision=attempt.revision_after,
            status=ReconciliationStatus.CONFIRMED_APPLIED,
            verification=self.verification(
                attempt,
                ReconciliationStatus.CONFIRMED_APPLIED,
                observation=self.observation(1, "saved"),
            ),
            expected_revision=state.revision,
        )
        decision = LoopGuard().evaluate(
            state,
            self.intent(state, strategy="s2", action="other-save"),
            expected_revision=state.revision,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(
            decision.failure.code,
            "logical_operation_reconciled_applied",
        )

    def test_ack_failed_cannot_be_reconciled_as_not_applied(self) -> None:
        state = self.state()
        intent = self.intent(state)
        failure = FailureReason(
            code="ack-failed",
            category=FailureCategory.RUNTIME_UNCERTAIN,
            message="The effect may be applied but acknowledgement was lost.",
            retryable=False,
            reconciliation_required=True,
            operation_id=intent.operation_id,
            strategy_id=intent.strategy_id,
            outcome=MutatingOutcome.APPLIED_BUT_ACK_FAILED,
        )
        state = self.apply(
            state,
            intent,
            MutatingOutcome.APPLIED_BUT_ACK_FAILED,
            failure,
        )
        attempt = state.attempts[-1]
        with self.assertRaisesRegex(
            ValueError,
            "cannot reconcile as not applied",
        ):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                ),
                expected_revision=state.revision,
            )

    def test_strategy_rename_cannot_bypass_identical_physical_attempt_guard(self) -> None:
        state = self.state()
        state = self.apply(
            state,
            self.intent(state, operation="op-a", strategy="s1"),
        )
        candidate = self.intent(
            state,
            operation="op-b",
            strategy="s2",
        )
        self.assertEqual(
            candidate.physical_fingerprint,
            state.attempts[-1].intent.physical_fingerprint,
        )
        decision = LoopGuard().evaluate(
            state,
            candidate,
            expected_revision=state.revision,
        )
        self.assertEqual(
            decision.failure.code,
            "repeated_physical_attempt_fingerprint",
        )

    def test_materially_different_strategy_can_continue_after_not_applied(self) -> None:
        state = self.state()
        state = self.apply(state, self.intent(state))
        candidate = self.intent(
            state,
            strategy="s2",
            action="keyboard-save",
        )
        self.assertTrue(
            LoopGuard().evaluate(
                state,
                candidate,
                expected_revision=state.revision,
            ).allowed
        )

    def test_task_procedure_and_strategy_budgets_are_distinct(self) -> None:
        state = self.state(
            task_budget=3,
            procedure_budget=3,
            strategy_budgets={"s1": 1, "s2": 3},
        )
        state = self.apply(state, self.intent(state))
        decision = LoopGuard().evaluate(
            state,
            self.intent(state, strategy="s1", action="other"),
            expected_revision=state.revision,
        )
        self.assertEqual(decision.failure.code, "strategy_budget_exhausted")
        self.assertEqual(
            state.budget(BudgetKind.TASK, strategy_id="s1").used,
            1,
        )
        self.assertEqual(
            state.budget(BudgetKind.PROCEDURE, strategy_id="s1").used,
            1,
        )

        task_state = self.state(
            task_budget=1,
            procedure_budget=3,
            strategy_budgets={"s1": 3, "s2": 3},
        )
        task_state = self.apply(task_state, self.intent(task_state))
        decision = LoopGuard().evaluate(
            task_state,
            self.intent(task_state, strategy="s2", action="other"),
            expected_revision=task_state.revision,
        )
        self.assertEqual(decision.failure.code, "task_budget_exhausted")

    def test_oscillation_is_blocked_even_when_actions_differ(self) -> None:
        guard = LoopGuard(
            LoopGuardPolicy(
                max_identical_physical_attempts=10,
                oscillation_window=4,
            )
        )
        state = self.state(
            task_budget=10,
            procedure_budget=10,
            strategy_budgets={"s1": 10, "s2": 10, "s3": 10, "s4": 10},
        )
        for index, fingerprint in enumerate(("A", "B", "A"), start=1):
            if state.observation_ref.fingerprint != fingerprint:
                state = state.record_observation(
                    self.observation(
                        state.observation_ref.sequence + 1,
                        fingerprint,
                    ),
                    expected_revision=state.revision,
                )
            state = self.apply(
                state,
                self.intent(
                    state,
                    operation=f"op-{index}",
                    strategy=f"s{index}",
                    action=f"action-{index}",
                ),
                guard=guard,
            )
        state = state.record_observation(
            self.observation(state.observation_ref.sequence + 1, "B"),
            expected_revision=state.revision,
        )
        candidate = self.intent(
            state,
            operation="op-4",
            strategy="s4",
            action="action-4",
        )
        decision = guard.evaluate(
            state,
            candidate,
            expected_revision=state.revision,
        )
        self.assertEqual(decision.failure.code, "physical_state_oscillation")

    def test_verified_applied_survives_restart_and_blocks_replay(self) -> None:
        state = self.state()
        state = self.apply(
            state,
            self.intent(state),
            MutatingOutcome.VERIFIED_APPLIED,
            None,
        )
        restarted = WorkingState.from_dict(
            json.loads(json.dumps(state.as_dict()))
        )
        decision = LoopGuard().evaluate(
            restarted,
            self.intent(restarted, strategy="s2", action="other"),
            expected_revision=restarted.revision,
        )
        self.assertEqual(
            decision.failure.code,
            "logical_operation_already_verified_applied",
        )

    def test_candidate_done_becomes_stale_after_fresh_observation(self) -> None:
        state = self.state().mark_candidate_done(expected_revision=0)
        self.assertTrue(state.candidate_done_current)
        state = state.record_observation(
            self.observation(1, "changed"),
            expected_revision=state.revision,
        )
        self.assertFalse(state.candidate_done_current)

    def test_stagnation_report_is_diagnostic_only(self) -> None:
        state = self.state(strategy_budgets={"s1": 1})
        state = self.apply(state, self.intent(state))
        report = state.stagnation_report("no-progress").as_dict()
        self.assertEqual(report["authority"], "diagnostic_only")
        self.assertNotIn("capability_grant_refs", report)
        self.assertIn("strategy:s1", report["exhausted_budgets"])


if __name__ == "__main__":
    unittest.main()
