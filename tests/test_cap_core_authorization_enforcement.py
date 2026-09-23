from __future__ import annotations

import unittest

from runtime.control_plane.authorization import AuthorizationRequest, CapabilityGrant
from runtime.control_plane.verification import ObservationRef
from runtime.control_plane.working_state import (
    AttemptIntent,
    FailureCategory,
    FailureReason,
    LoopGuard,
    MutatingOutcome,
    WorkingState,
)


class CapCoreAuthorizationEnforcementTests(unittest.TestCase):
    def observation(self) -> ObservationRef:
        return ObservationRef(
            capability="windows",
            subject="case:fixture-a",
            stream_id="evidence:fixture-a",
            sequence=3,
            fingerprint="state:fixture-a:3",
            observed_at="t3",
        )

    def state(self, *, grant_refs: tuple[str, ...] = ("grant:update",)) -> WorkingState:
        observation = self.observation()
        return WorkingState.create(
            task_id="task:fixture-a",
            task_budget=3,
            procedure_budget=3,
            strategy_budgets={"strategy:update": 3},
            observation_ref=observation,
            actor_ref="manager:ordinary-chatgpt",
            execution_environment_ref="runtime:windows-a",
            evidence_scope_ref=observation.stream_id,
            procedure_ref="procedure:update-case",
            evidence_refs=("evidence:before",),
            capability_grant_refs=grant_refs,
        )

    def intent(self, state: WorkingState) -> AttemptIntent:
        return AttemptIntent(
            operation_id="operation:update-case:1",
            strategy_id="strategy:update",
            action_fingerprint="action:update-status:approved",
            observation_ref=state.observation_ref,
            actor_ref=state.actor_ref,
            execution_environment_ref=state.execution_environment_ref,
            evidence_scope_ref=state.evidence_scope_ref,
            evidence_refs=("evidence:before",),
        )

    def grant(self, **overrides: object) -> CapabilityGrant:
        value: dict[str, object] = {
            "grant_ref": "grant:update",
            "task_ref": "task:fixture-a",
            "principal_ref": "manager:ordinary-chatgpt",
            "capability": "windows",
            "allowed_action_refs": ("case.update-status",),
            "resource_scope_ref": "case:fixture-a",
            "delegation_ref": None,
            "execution_environment_ref": "runtime:windows-a",
            "evidence_scope_ref": "evidence:fixture-a",
        }
        value.update(overrides)
        return CapabilityGrant(**value)

    def request(
        self,
        intent: AttemptIntent,
        **overrides: object,
    ) -> AuthorizationRequest:
        value: dict[str, object] = {
            "task_ref": "task:fixture-a",
            "principal_ref": "manager:ordinary-chatgpt",
            "capability": "windows",
            "action_ref": "case.update-status",
            "resource_scope_ref": "case:fixture-a",
            "attempt_authorization_fingerprint": intent.authorization_fingerprint,
            "delegation_ref": None,
            "execution_environment_ref": "runtime:windows-a",
            "evidence_scope_ref": "evidence:fixture-a",
        }
        value.update(overrides)
        return AuthorizationRequest(**value)

    def test_exact_active_grant_allows_exact_attempt(self) -> None:
        state = self.state()
        intent = self.intent(state)

        decision = LoopGuard().evaluate_authorized(
            state,
            intent,
            authorization_request=self.request(intent),
            capability_grant=self.grant(),
            expected_revision=state.revision,
        )

        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.failure)
        self.assertEqual(intent.authorization_fingerprint, decision.authorization_fingerprint)

    def test_missing_or_inactive_grant_blocks(self) -> None:
        state = self.state()
        intent = self.intent(state)

        missing = LoopGuard().evaluate_authorized(
            state,
            intent,
            authorization_request=self.request(intent),
            capability_grant=None,
            expected_revision=state.revision,
        )
        self.assertFalse(missing.allowed)
        self.assertEqual("capability_grant_missing", missing.failure.code)

        inactive_state = self.state(grant_refs=("grant:other",))
        inactive_intent = self.intent(inactive_state)
        inactive = LoopGuard().evaluate_authorized(
            inactive_state,
            inactive_intent,
            authorization_request=self.request(inactive_intent),
            capability_grant=self.grant(),
            expected_revision=inactive_state.revision,
        )
        self.assertFalse(inactive.allowed)
        self.assertEqual("capability_grant_not_active", inactive.failure.code)

    def test_request_must_bind_exact_attempt_fingerprint(self) -> None:
        state = self.state()
        intent = self.intent(state)
        request = self.request(
            intent,
            attempt_authorization_fingerprint="b" * 64,
        )

        decision = LoopGuard().evaluate_authorized(
            state,
            intent,
            authorization_request=request,
            capability_grant=self.grant(),
            expected_revision=state.revision,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(
            "authorization_attempt_fingerprint_mismatch",
            decision.failure.code,
        )

    def test_request_context_cannot_disagree_with_current_state_or_attempt(self) -> None:
        cases = (
            ("task", {"task_ref": "task:other"}, "authorization_task_mismatch"),
            (
                "principal",
                {"principal_ref": "worker:other"},
                "authorization_principal_mismatch",
            ),
            (
                "capability",
                {"capability": "browser"},
                "authorization_capability_mismatch",
            ),
            (
                "delegation",
                {"delegation_ref": "delegation:other"},
                "authorization_delegation_mismatch",
            ),
            (
                "environment",
                {"execution_environment_ref": "runtime:other"},
                "authorization_environment_mismatch",
            ),
            (
                "evidence",
                {"evidence_scope_ref": "evidence:other"},
                "authorization_evidence_scope_mismatch",
            ),
        )
        state = self.state()
        intent = self.intent(state)

        for label, overrides, expected_code in cases:
            with self.subTest(label=label):
                decision = LoopGuard().evaluate_authorized(
                    state,
                    intent,
                    authorization_request=self.request(intent, **overrides),
                    capability_grant=self.grant(),
                    expected_revision=state.revision,
                )
                self.assertFalse(decision.allowed)
                self.assertEqual(expected_code, decision.failure.code)

    def test_grant_action_and_resource_are_enforced_after_context_binding(self) -> None:
        state = self.state()
        intent = self.intent(state)

        wrong_action = LoopGuard().evaluate_authorized(
            state,
            intent,
            authorization_request=self.request(
                intent,
                action_ref="case.delete",
            ),
            capability_grant=self.grant(),
            expected_revision=state.revision,
        )
        self.assertFalse(wrong_action.allowed)
        self.assertEqual("authorization_action_not_granted", wrong_action.failure.code)

        wrong_resource = LoopGuard().evaluate_authorized(
            state,
            intent,
            authorization_request=self.request(
                intent,
                resource_scope_ref="case:other",
            ),
            capability_grant=self.grant(),
            expected_revision=state.revision,
        )
        self.assertFalse(wrong_resource.allowed)
        self.assertEqual(
            "authorization_resource_scope_ref_mismatch",
            wrong_resource.failure.code,
        )

    def test_record_authorized_attempt_uses_enforcement_before_history_mutation(self) -> None:
        state = self.state()
        intent = self.intent(state)

        blocked_request = self.request(intent, action_ref="case.delete")
        with self.assertRaisesRegex(
            ValueError,
            "authorization_action_not_granted",
        ):
            state.record_authorized_attempt(
                intent,
                MutatingOutcome.VERIFIED_APPLIED,
                None,
                authorization_request=blocked_request,
                capability_grant=self.grant(),
                expected_revision=state.revision,
            )

        self.assertEqual(0, state.revision)
        self.assertEqual((), state.attempts)

        updated = state.record_authorized_attempt(
            intent,
            MutatingOutcome.VERIFIED_APPLIED,
            None,
            authorization_request=self.request(intent),
            capability_grant=self.grant(),
            expected_revision=state.revision,
        )
        self.assertEqual(1, updated.revision)
        self.assertEqual(1, len(updated.attempts))
        self.assertEqual(intent, updated.attempts[0].intent)

    def test_active_grant_replacement_is_revisioned_and_evidence_bound(self) -> None:
        state = self.state()
        updated = state.replace_capability_grants(
            ("grant:replacement",),
            evidence_ref="evidence:grant-handoff",
            expected_revision=state.revision,
        )

        self.assertEqual(state.revision + 1, updated.revision)
        self.assertEqual(("grant:replacement",), updated.capability_grant_refs)
        self.assertEqual(
            state.evidence_refs + ("evidence:grant-handoff",),
            updated.evidence_refs,
        )
        self.assertEqual(state.attempts, updated.attempts)
        self.assertEqual(state.failures, updated.failures)
        self.assertEqual(state.reconciliations, updated.reconciliations)
        self.assertEqual(state.budgets, updated.budgets)

        with self.assertRaisesRegex(ValueError, "stale WorkingState revision"):
            state.replace_capability_grants(
                ("grant:replacement",),
                evidence_ref="evidence:stale",
                expected_revision=state.revision + 1,
            )
        with self.assertRaisesRegex(ValueError, "grant set did not change"):
            state.replace_capability_grants(
                state.capability_grant_refs,
                evidence_ref="evidence:no-change",
                expected_revision=state.revision,
            )

    def test_unresolved_attempt_blocks_active_grant_replacement(self) -> None:
        state = self.state()
        intent = self.intent(state)
        failure = FailureReason(
            code="delivery_unknown",
            category=FailureCategory.RECONCILIATION_REQUIRED,
            message="delivery outcome requires reconciliation",
            retryable=False,
            reconciliation_required=True,
            operation_id=intent.operation_id,
            strategy_id=intent.strategy_id,
            outcome=MutatingOutcome.OUTCOME_UNKNOWN,
            evidence_refs=intent.evidence_refs,
        )
        unresolved = state.record_authorized_attempt(
            intent,
            MutatingOutcome.OUTCOME_UNKNOWN,
            failure,
            authorization_request=self.request(intent),
            capability_grant=self.grant(),
            expected_revision=state.revision,
        )

        with self.assertRaisesRegex(
            ValueError,
            "unresolved mutation blocks capability grant replacement",
        ):
            unresolved.replace_capability_grants(
                ("grant:replacement",),
                evidence_ref="evidence:grant-handoff",
                expected_revision=unresolved.revision,
            )
    def test_structural_loop_guard_failure_wins_before_authorization(self) -> None:
        state = self.state()
        intent = self.intent(state)

        decision = LoopGuard().evaluate_authorized(
            state,
            intent,
            authorization_request=self.request(intent),
            capability_grant=self.grant(),
            expected_revision=99,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual("stale_working_state", decision.failure.code)


if __name__ == "__main__":
    unittest.main()
