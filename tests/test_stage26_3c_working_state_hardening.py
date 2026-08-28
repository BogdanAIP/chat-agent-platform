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
    GuardDecision,
    GuardStatus,
    LoopGuard,
    MutatingOutcome,
    ReconciliationStatus,
    WorkingState,
    reconciliation_effect_id,
)


class WorkingStateHardeningTests(unittest.TestCase):
    def observation(
        self,
        sequence: int = 0,
        fingerprint: str = "state-a",
        *,
        stream_id: str = "scope-1",
    ) -> ObservationRef:
        return ObservationRef(
            capability="windows",
            subject="case-1",
            stream_id=stream_id,
            sequence=sequence,
            fingerprint=fingerprint,
            observed_at=f"t{sequence}",
        )

    def state(self) -> WorkingState:
        observation = self.observation()
        return WorkingState.create(
            task_id="task-hardening",
            task_budget=4,
            procedure_budget=4,
            strategy_budgets={"s1": 4, "s2": 4},
            observation_ref=observation,
            actor_ref="manager",
            execution_environment_ref="env-1",
            evidence_scope_ref=observation.stream_id,
            procedure_ref="procedure:v1",
            evidence_refs=("obs:0",),
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
    ) -> FailureReason:
        return FailureReason(
            code="no-effect",
            category=FailureCategory.ACTION_NO_EFFECT,
            message="No verified effect.",
            retryable=True,
            operation_id=intent.operation_id,
            strategy_id=intent.strategy_id,
            outcome=outcome,
        )

    def unknown_state(self) -> WorkingState:
        state = self.state()
        intent = self.intent(state)
        return state.record_attempt(
            intent,
            MutatingOutcome.OUTCOME_UNKNOWN,
            FailureReason(
                code="delivery-unknown",
                category=FailureCategory.RUNTIME_UNCERTAIN,
                message="Delivery outcome is unknown.",
                retryable=False,
                reconciliation_required=True,
                operation_id=intent.operation_id,
                strategy_id=intent.strategy_id,
                outcome=MutatingOutcome.OUTCOME_UNKNOWN,
            ),
            expected_revision=state.revision,
        )

    def verification(
        self,
        attempt,
        status: ReconciliationStatus,
        *,
        observation: ObservationRef | None = None,
        verification_status: VerificationStatus = VerificationStatus.PASS,
        evidence_batch_id: str | None = "batch-1",
        effect_id: str | None = None,
    ) -> VerificationResult:
        observation = observation or self.observation(
            attempt.intent.observation_ref.sequence + 1,
            "fresh",
        )
        return VerificationResult(
            effect_id=(
                effect_id
                or reconciliation_effect_id(
                    attempt.intent.operation_id,
                    attempt.revision_after,
                    status,
                )
            ),
            status=verification_status,
            reason="reconciliation",
            observation=observation,
            evidence_batch_id=evidence_batch_id,
        )

    def test_unresolved_unknown_blocks_new_operation_id_and_changed_fingerprint(self) -> None:
        state = self.unknown_state()
        candidate = self.intent(
            state,
            operation="op-2",
            strategy="s2",
            action="keyboard-save",
        )
        decision = LoopGuard().evaluate(
            state,
            candidate,
            expected_revision=state.revision,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(
            decision.failure.code,
            "unresolved_mutation_blocks_other_operation",
        )

    def test_reconciliation_requires_bound_kernel_effect_id(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        with self.assertRaisesRegex(ValueError, "effect_id mismatch"):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                    effect_id="caller-invented",
                ),
                expected_revision=state.revision,
            )

    def test_reconciliation_rejects_stale_observation(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        with self.assertRaisesRegex(
            ValueError,
            "not fresh relative to attempt",
        ):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                    observation=attempt.intent.observation_ref,
                ),
                expected_revision=state.revision,
            )

    def test_reconciliation_requires_evidence_batch(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        with self.assertRaisesRegex(ValueError, "requires evidence_batch_id"):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                    evidence_batch_id=None,
                ),
                expected_revision=state.revision,
            )

    def test_confirmed_reconciliation_requires_pass_verification(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        with self.assertRaisesRegex(ValueError, "requires PASS"):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                    verification_status=VerificationStatus.UNKNOWN,
                ),
                expected_revision=state.revision,
            )

    def test_reconciliation_may_consume_current_already_recorded_fresh_observation(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        fresh = self.observation(1, "fresh")
        state = state.record_observation(
            fresh,
            expected_revision=state.revision,
        )
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
        self.assertEqual(state.observation_ref, fresh)

    def test_attempt_must_bind_to_current_observation_ref(self) -> None:
        state = self.state()
        stale = state.observation_ref
        state = state.record_observation(
            self.observation(1, "new"),
            expected_revision=state.revision,
        )
        decision = LoopGuard().evaluate(
            state,
            self.intent(state, observation=stale),
            expected_revision=state.revision,
        )
        self.assertEqual(
            decision.failure.code,
            "stale_or_mismatched_observation",
        )

    def test_record_attempt_rechecks_guard_instead_of_trusting_allow_object(self) -> None:
        state = self.state()
        first = self.intent(state)
        state = state.record_attempt(
            first,
            MutatingOutcome.NOT_APPLIED,
            self.failure(first),
            expected_revision=state.revision,
        )
        state = state.record_observation(
            self.observation(1, "state-a"),
            expected_revision=state.revision,
        )
        candidate = self.intent(
            state,
            operation="op-2",
            strategy="s2",
        )
        fake_allow = GuardDecision(
            GuardStatus.ALLOW,
            state.revision,
            candidate.authorization_fingerprint,
        )
        self.assertTrue(fake_allow.allowed)
        with self.assertRaisesRegex(
            ValueError,
            "repeated_physical_attempt_fingerprint",
        ):
            state.record_attempt(
                candidate,
                MutatingOutcome.NOT_APPLIED,
                self.failure(candidate),
                expected_revision=state.revision,
            )

    def test_authorization_fingerprint_binds_full_attempt_identity(self) -> None:
        state = self.state()
        first = self.intent(
            state,
            operation="op-a",
            strategy="s1",
            evidence_refs=("obs:0",),
        )
        second = self.intent(
            state,
            operation="op-b",
            strategy="s2",
            evidence_refs=("obs:0", "grant:x"),
        )
        self.assertEqual(
            first.physical_fingerprint,
            second.physical_fingerprint,
        )
        self.assertNotEqual(
            first.authorization_fingerprint,
            second.authorization_fingerprint,
        )

    def test_mutating_attempt_has_no_caller_controlled_physical_false_bypass(self) -> None:
        state = self.state()
        with self.assertRaises(TypeError):
            AttemptIntent(
                "op-1",
                "s1",
                "click-save",
                state.observation_ref,
                "manager",
                "env-1",
                "scope-1",
                (),
                False,
            )

    def test_every_recorded_attempt_consumes_task_procedure_and_strategy_budget(self) -> None:
        state = self.state()
        intent = self.intent(state)
        state = state.record_attempt(
            intent,
            MutatingOutcome.NOT_APPLIED,
            self.failure(intent),
            expected_revision=state.revision,
        )
        self.assertEqual(
            state.budget(BudgetKind.TASK, strategy_id="s1").used,
            1,
        )
        self.assertEqual(
            state.budget(BudgetKind.PROCEDURE, strategy_id="s1").used,
            1,
        )
        self.assertEqual(
            state.budget(BudgetKind.STRATEGY, strategy_id="s1").used,
            1,
        )

    def test_durable_budget_reset_tamper_fails_closed(self) -> None:
        state = self.state()
        intent = self.intent(state)
        state = state.record_attempt(
            intent,
            MutatingOutcome.NOT_APPLIED,
            self.failure(intent),
            expected_revision=state.revision,
        )
        payload = json.loads(json.dumps(state.as_dict()))
        for budget in payload["budgets"]:
            budget["used"] = 0
        with self.assertRaisesRegex(ValueError, "budget history mismatch"):
            WorkingState.from_dict(payload)

    def test_durable_reference_fields_require_array_shape(self) -> None:
        payload = self.state().as_dict()
        payload["capability_grant_refs"] = "admin"
        with self.assertRaises(TypeError):
            WorkingState.from_dict(payload)

        payload = self.state().as_dict()
        payload["evidence_refs"] = {"obs": "x"}
        with self.assertRaises(TypeError):
            WorkingState.from_dict(payload)

    def test_durable_state_rejects_unknown_authority_fields(self) -> None:
        payload = self.state().as_dict()
        payload["unexpected_authority"] = True
        with self.assertRaisesRegex(ValueError, "shape mismatch"):
            WorkingState.from_dict(payload)

    def test_durable_attempt_actor_mismatch_fails_closed(self) -> None:
        state = self.state()
        intent = self.intent(state)
        state = state.record_attempt(
            intent,
            MutatingOutcome.NOT_APPLIED,
            self.failure(intent),
            expected_revision=state.revision,
        )
        payload = json.loads(json.dumps(state.as_dict()))
        payload["attempts"][0]["intent"]["actor_ref"] = "foreign-actor"
        with self.assertRaisesRegex(
            ValueError,
            "attempt actor_ref does not match WorkingState",
        ):
            WorkingState.from_dict(payload)

    def test_durable_attempt_observations_must_advance_between_attempts(self) -> None:
        state = self.state()
        first = self.intent(state)
        state = state.record_attempt(
            first,
            MutatingOutcome.NOT_APPLIED,
            self.failure(first),
            expected_revision=state.revision,
        )
        state = state.record_observation(
            self.observation(1, "state-a"),
            expected_revision=state.revision,
        )
        second = self.intent(
            state,
            operation="op-2",
            strategy="s2",
            action="keyboard-save",
        )
        state = state.record_attempt(
            second,
            MutatingOutcome.NOT_APPLIED,
            self.failure(second),
            expected_revision=state.revision,
        )
        payload = json.loads(json.dumps(state.as_dict()))
        payload["attempts"][1]["intent"]["observation_ref"] = json.loads(
            json.dumps(payload["attempts"][0]["intent"]["observation_ref"])
        )
        with self.assertRaisesRegex(
            ValueError,
            "attempt observations must advance between physical attempts",
        ):
            WorkingState.from_dict(payload)

    def test_earlier_unresolved_attempt_cannot_be_hidden_by_later_durable_attempt(self) -> None:
        state = self.unknown_state()
        payload = json.loads(json.dumps(state.as_dict()))
        first = payload["attempts"][0]
        later = json.loads(json.dumps(first))
        later["intent"]["strategy_id"] = "s2"
        later["intent"]["action_fingerprint"] = "alternate-save"
        later["intent"]["observation_ref"]["sequence"] = 1
        later["intent"]["observation_ref"]["fingerprint"] = "fresh-forged"
        later["intent"]["observation_ref"]["observed_at"] = "t1"
        later["outcome"] = MutatingOutcome.NOT_APPLIED.value
        later["revision_before"] = 2
        later["revision_after"] = 3
        later["failure"] = {
            "code": "no-effect-2",
            "category": FailureCategory.ACTION_NO_EFFECT.value,
            "message": "No effect on second attempt.",
            "retryable": True,
            "reconciliation_required": False,
            "operation_id": "op-1",
            "strategy_id": "s2",
            "outcome": MutatingOutcome.NOT_APPLIED.value,
            "evidence_refs": [],
        }
        payload["attempts"].append(later)
        payload["failures"].append(later["failure"])
        payload["observation_ref"] = json.loads(
            json.dumps(later["intent"]["observation_ref"])
        )
        payload["revision"] = 3
        for budget in payload["budgets"]:
            if budget["kind"] in (BudgetKind.TASK.value, BudgetKind.PROCEDURE.value):
                budget["used"] = 2
            elif budget["kind"] == BudgetKind.STRATEGY.value:
                budget["used"] = 1 if budget["scope_id"] in ("s1", "s2") else 0

        with self.assertRaisesRegex(
            ValueError,
            "attempt occurred while reconciliation was pending",
        ):
            WorkingState.from_dict(payload)

    def test_resolved_reconciliation_cannot_be_reversed(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        state = state.record_reconciliation(
            operation_id=attempt.intent.operation_id,
            attempt_revision=attempt.revision_after,
            status=ReconciliationStatus.CONFIRMED_APPLIED,
            verification=self.verification(
                attempt,
                ReconciliationStatus.CONFIRMED_APPLIED,
                observation=self.observation(1, "applied"),
            ),
            expected_revision=state.revision,
        )
        with self.assertRaisesRegex(ValueError, "resolved reconciliation cannot be replaced"):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                    observation=self.observation(2, "not-applied"),
                ),
                expected_revision=state.revision,
            )

    def test_durable_reconciliation_cross_history_is_validated(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        state = state.record_reconciliation(
            operation_id=attempt.intent.operation_id,
            attempt_revision=attempt.revision_after,
            status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
            verification=self.verification(
                attempt,
                ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                observation=self.observation(1, "fresh"),
            ),
            expected_revision=state.revision,
        )
        payload = json.loads(json.dumps(state.as_dict()))
        payload["reconciliations"][0]["verification_effect_id"] = "forged"
        with self.assertRaisesRegex(ValueError, "durable reconciliation effect_id mismatch"):
            WorkingState.from_dict(payload)

    def test_reconciliation_rejects_conflicting_observation_same_sequence(self) -> None:
        state = self.unknown_state()
        attempt = state.attempts[-1]
        current = self.observation(1, "current")
        state = state.record_observation(
            current,
            expected_revision=state.revision,
        )
        conflicting = self.observation(1, "different-fingerprint")
        with self.assertRaisesRegex(ValueError, "conflicts with current sequence"):
            state.record_reconciliation(
                operation_id=attempt.intent.operation_id,
                attempt_revision=attempt.revision_after,
                status=ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                verification=self.verification(
                    attempt,
                    ReconciliationStatus.CONFIRMED_NOT_APPLIED,
                    observation=conflicting,
                ),
                expected_revision=state.revision,
            )


if __name__ == "__main__":
    unittest.main()
