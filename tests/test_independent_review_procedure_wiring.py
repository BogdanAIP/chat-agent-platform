from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.control_plane import cli as control_plane_cli
from runtime.control_plane import delegation_state
from runtime.control_plane import independent_review_state as review_state
from runtime.control_plane.independent_review_delegation import (
    prepare_review_delegation,
    settle_review_from_delegation,
)
from runtime.control_plane.independent_review_procedures import (
    LAUNCH_PROCEDURE_ID,
    RECONCILE_PROCEDURE_ID,
    SUBMIT_PROCEDURE_ID,
    run_launch_independent_review,
    run_reconcile_independent_review_result,
    run_submit_independent_review_result,
)


BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def identity_request(procedure: str) -> dict[str, object]:
    return {
        "procedure": procedure,
        "repository": "BogdanAIP/chat-agent-platform",
        "pr_number": 141,
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "review_skill": "code-review",
        "review_skill_version": "1.1",
    }


def identity_value() -> dict[str, object]:
    request = identity_request(LAUNCH_PROCEDURE_ID)
    request.pop("procedure")
    return request


def pass_result(*, review_run_id: str | None = None) -> str:
    lines = [
        "REVIEW_RESULT_V1",
        "repository=BogdanAIP/chat-agent-platform",
        "pr_number=141",
        f"base_sha={BASE_SHA}",
        f"head_sha={HEAD_SHA}",
        f"review_policy_ref={BASE_SHA}",
        "review_skill=code-review",
        "review_skill_version=1.1",
        "review_context=ordinary_chat_fresh",
        "status=PASS",
        "review_validity=CURRENT",
        "reported_findings=0",
        "rejected_candidates=0",
        "reviewed_at=2026-09-01T00:00:00+00:00",
    ]
    if review_run_id is not None:
        lines.append(f"review_run_id={review_run_id}")
    return "\n".join(lines)


def stale_result(*, review_run_id: str) -> str:
    return "\n".join(
        [
            "REVIEW_RESULT_V1",
            "repository=BogdanAIP/chat-agent-platform",
            "pr_number=141",
            f"base_sha={BASE_SHA}",
            f"head_sha={HEAD_SHA}",
            f"review_policy_ref={BASE_SHA}",
            "review_skill=code-review",
            "review_skill_version=1.1",
            "review_context=ordinary_chat_fresh",
            "status=STALE",
            "review_validity=STALE_MATERIAL_CHANGE",
            "reported_findings=0",
            "rejected_candidates=0",
            "reviewed_at=2026-09-01T00:00:00+00:00",
            f"review_run_id={review_run_id}",
        ]
    )


class IndependentReviewProcedureWiringTests(unittest.TestCase):
    def test_launch_preserves_dispatch_when_installed_reviewer_runtime_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            result = run_launch_independent_review(
                identity_request(LAUNCH_PROCEDURE_ID),
                state_root=state_root,
            )

            self.assertEqual("abstained", result["status"])
            self.assertEqual(LAUNCH_PROCEDURE_ID, result["procedure_id"])
            self.assertEqual("reviewer_runtime_unavailable", result["escalation_reason"])
            self.assertEqual("prepared", result["dispatch_state"])
            self.assertEqual("open", result["result_state"])
            self.assertFalse(result["automatic_launch_performed"])
            self.assertFalse(result["automatic_submission_open"])
            self.assertNotIn("review_run_id", result)

            prepared = review_state.prepare_review_operation(identity_value(), state_root=state_root)
            self.assertFalse(prepared.created)
            self.assertEqual("prepared", prepared.dispatch_state)
            self.assertEqual("open", prepared.result_state)

    def test_successful_launch_consumes_dispatch_once_and_never_spawns_twice(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            delegation_root = state_root / "agent-sessions"
            with (
                patch(
                    "runtime.control_plane.independent_review_procedures.validate_review_worker_runtime",
                    return_value=state_root,
                ),
                patch(
                    "runtime.control_plane.independent_review_procedures.review_delegation_state_root",
                    return_value=delegation_root,
                ),
                patch(
                    "runtime.control_plane.independent_review_procedures.spawn_review_worker"
                ) as spawn,
            ):
                first = run_launch_independent_review(
                    identity_request(LAUNCH_PROCEDURE_ID),
                    state_root=state_root,
                )
                second = run_launch_independent_review(
                    identity_request(LAUNCH_PROCEDURE_ID),
                    state_root=state_root,
                )

            self.assertEqual("pending", first["status"])
            self.assertEqual("dispatch-attempted", first["dispatch_state"])
            self.assertTrue(first["automatic_launch_performed"])
            self.assertTrue(first["automatic_submission_open"])
            self.assertNotIn("review_run_id", first)

            self.assertEqual(first["operation_key"], second["operation_key"])
            self.assertEqual("pending", second["status"])
            self.assertEqual("dispatch-attempted", second["dispatch_state"])
            self.assertFalse(second["automatic_launch_performed"])
            self.assertTrue(second["automatic_submission_open"])
            self.assertNotIn("review_run_id", second)
            spawn.assert_called_once()

    def test_submit_is_real_local_recording_after_trusted_dispatch_transition(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            prepared = review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            payload = pass_result(review_run_id=prepared.review_run_id)

            result = run_submit_independent_review_result(
                {
                    "procedure": SUBMIT_PROCEDURE_ID,
                    "review_run_id": prepared.review_run_id,
                    "result": payload,
                },
                state_root=state_root,
            )
            repeated = run_submit_independent_review_result(
                {
                    "procedure": SUBMIT_PROCEDURE_ID,
                    "review_run_id": prepared.review_run_id,
                    "result": payload,
                },
                state_root=state_root,
            )

            self.assertEqual("recorded", result["status"])
            self.assertEqual("automatic", result["result_source"])
            self.assertEqual("already_recorded", repeated["status"])

    def test_reconcile_returns_pending_then_records_manual_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            run_launch_independent_review(
                identity_request(LAUNCH_PROCEDURE_ID),
                state_root=state_root,
            )

            reconcile = identity_request(RECONCILE_PROCEDURE_ID)
            pending = run_reconcile_independent_review_result(reconcile, state_root=state_root)
            self.assertEqual("pending", pending["status"])
            self.assertEqual("prepared", pending["dispatch_state"])
            self.assertFalse(pending["automatic_submission_open"])

            terminal = run_reconcile_independent_review_result(
                {**reconcile, "manual_result": pass_result()},
                state_root=state_root,
            )
            self.assertEqual("recorded", terminal["status"])
            self.assertEqual("manual-fallback-recorded", terminal["result_state"])
            self.assertEqual("manual", terminal["result_source"])
            self.assertEqual(pass_result(), terminal["result"])

    def test_reconcile_settles_recorded_generic_worker_result_into_reviewer_state(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            prepared_review = review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            _task, delegated_identity = prepare_review_delegation(
                prepared_review.identity,
                review_run_id=prepared_review.review_run_id,
                delegation_state_root=state_root / "agent-sessions",
            )
            prepared = delegation_state.prepare_delegation(
                delegated_identity,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.mark_launch_attempted(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.bind_worker_session(
                delegated_identity,
                run_id=prepared.run_id,
                session_ref_value={
                    "adapter_id": "chatgpt-temporary",
                    "session_id": "chatgpt-delivery-test",
                    "conversation_id": None,
                    "ownership": "manager_owned",
                    "observation_ref": "test-observation",
                },
                state_root=state_root / "agent-sessions",
            )
            delegation_state.claim_delivery(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.record_delivery_outcome(
                delegated_identity,
                run_id=prepared.run_id,
                outcome="delivered",
                evidence_ref="test-delivered",
                state_root=state_root / "agent-sessions",
            )

            payload = pass_result(review_run_id=prepared_review.review_run_id)
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            delegation_state.record_worker_result(
                delegated_identity,
                run_id=prepared.run_id,
                result_value={
                    "schema_version": 1,
                    "delegation_id": prepared.delegation_id,
                    "delivery_id": prepared.delivery_id,
                    "worker_kind": delegated_identity["worker_kind"],
                    "result_contract_id": delegated_identity["result_contract_id"],
                    "status": "COMPLETED",
                    "payload": payload,
                    "payload_sha256": digest,
                },
                state_root=state_root / "agent-sessions",
            )

            with patch(
                "runtime.control_plane.independent_review_procedures.review_delegation_state_root",
                return_value=state_root / "agent-sessions",
            ):
                result = run_reconcile_independent_review_result(
                    identity_request(RECONCILE_PROCEDURE_ID),
                    state_root=state_root,
                )
            self.assertEqual("recorded", result["status"])
            self.assertEqual("automatic-result-recorded", result["result_state"])
            self.assertEqual("automatic", result["result_source"])
            self.assertEqual(payload, result["result"])

    def test_delegated_result_uses_registered_submit_procedure_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            prepared_review = review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            _task, delegated_identity = prepare_review_delegation(
                prepared_review.identity,
                review_run_id=prepared_review.review_run_id,
                delegation_state_root=state_root / "agent-sessions",
            )
            prepared = delegation_state.prepare_delegation(
                delegated_identity,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.mark_launch_attempted(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.bind_worker_session(
                delegated_identity,
                run_id=prepared.run_id,
                session_ref_value={
                    "adapter_id": "chatgpt-temporary",
                    "session_id": "chatgpt-submit-boundary-test",
                    "conversation_id": None,
                    "ownership": "manager_owned",
                    "observation_ref": "test-observation",
                },
                state_root=state_root / "agent-sessions",
            )
            delegation_state.claim_delivery(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.record_delivery_outcome(
                delegated_identity,
                run_id=prepared.run_id,
                outcome="delivered",
                evidence_ref="test-delivered",
                state_root=state_root / "agent-sessions",
            )
            payload = pass_result(review_run_id=prepared_review.review_run_id)
            delegation_state.record_worker_result(
                delegated_identity,
                run_id=prepared.run_id,
                result_value={
                    "schema_version": 1,
                    "delegation_id": prepared.delegation_id,
                    "delivery_id": prepared.delivery_id,
                    "worker_kind": delegated_identity["worker_kind"],
                    "result_contract_id": delegated_identity["result_contract_id"],
                    "status": "COMPLETED",
                    "payload": payload,
                    "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                },
                state_root=state_root / "agent-sessions",
            )

            with patch(
                "runtime.control_plane.independent_review_procedures.review_delegation_state_root",
                return_value=state_root / "agent-sessions",
            ):
                result = run_reconcile_independent_review_result(
                    identity_request(RECONCILE_PROCEDURE_ID),
                    state_root=state_root,
                )

            self.assertEqual("automatic-result-recorded", result["result_state"])
            persisted = review_state.reconcile_independent_review_result(
                identity_value(),
                state_root=state_root,
            )
            self.assertEqual("automatic-result-recorded", persisted["result_state"])
            self.assertEqual(payload, persisted["result"])

    def test_delegated_submit_invokes_control_plane_cli_with_exact_registered_request(self) -> None:
        from runtime.control_plane import independent_review_procedures as review_procedures

        fake = SimpleNamespace(
            stdout=b'{"schema_version":1,"status":"recorded"}',
            returncode=0,
        )
        with tempfile.TemporaryDirectory() as state_dir, patch(
            "runtime.control_plane.independent_review_procedures.subprocess.run",
            return_value=fake,
        ) as run:
            result = review_procedures._submit_delegated_result_via_registered_procedure(
                "a" * 64,
                "REVIEW_RESULT_V1",
                state_root=Path(state_dir),
            )

        self.assertEqual("recorded", result["status"])
        request = __import__("json").loads(run.call_args.kwargs["input"].decode("utf-8"))
        self.assertEqual(
            {
                "procedure": SUBMIT_PROCEDURE_ID,
                "review_run_id": "a" * 64,
                "result": "REVIEW_RESULT_V1",
            },
            request,
        )
        self.assertTrue(str(run.call_args.args[0][1]).endswith("runtime/control_plane/cli.py"))

    def test_noncompleting_generic_worker_result_does_not_close_reviewer_state(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            prepared_review = review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            _task, delegated_identity = prepare_review_delegation(
                prepared_review.identity,
                review_run_id=prepared_review.review_run_id,
                delegation_state_root=state_root / "agent-sessions",
            )
            prepared = delegation_state.prepare_delegation(
                delegated_identity,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.mark_launch_attempted(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.bind_worker_session(
                delegated_identity,
                run_id=prepared.run_id,
                session_ref_value={
                    "adapter_id": "chatgpt-temporary",
                    "session_id": "chatgpt-delivery-test",
                    "conversation_id": None,
                    "ownership": "manager_owned",
                    "observation_ref": "test-observation",
                },
                state_root=state_root / "agent-sessions",
            )
            delegation_state.claim_delivery(
                delegated_identity,
                run_id=prepared.run_id,
                state_root=state_root / "agent-sessions",
            )
            delegation_state.record_delivery_outcome(
                delegated_identity,
                run_id=prepared.run_id,
                outcome="delivered",
                evidence_ref="test-delivered",
                state_root=state_root / "agent-sessions",
            )

            payload = "worker could not obtain required read-only evidence"
            delegation_state.record_worker_result(
                delegated_identity,
                run_id=prepared.run_id,
                result_value={
                    "schema_version": 1,
                    "delegation_id": prepared.delegation_id,
                    "delivery_id": prepared.delivery_id,
                    "worker_kind": delegated_identity["worker_kind"],
                    "result_contract_id": delegated_identity["result_contract_id"],
                    "status": "ABSTAIN",
                    "payload": payload,
                    "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
                },
                state_root=state_root / "agent-sessions",
            )

            with patch(
                "runtime.control_plane.independent_review_procedures.review_delegation_state_root",
                return_value=state_root / "agent-sessions",
            ):
                result = run_reconcile_independent_review_result(
                    identity_request(RECONCILE_PROCEDURE_ID),
                    state_root=state_root,
                )
            self.assertEqual("pending", result["status"])
            self.assertEqual("open", result["result_state"])
            self.assertEqual("ABSTAIN", result["automatic_worker_status"])

    def test_repeated_launch_surfaces_noncompleting_review_result_without_relaunch(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)

            with (
                patch(
                    "runtime.control_plane.independent_review_procedures.review_delegation_state_root",
                    return_value=state_root / "agent-sessions",
                ),
                patch(
                    "runtime.control_plane.independent_review_procedures.settle_review_from_delegation",
                    return_value={
                        "schema_version": 1,
                        "status": "review_terminal_noncompleting",
                        "review_status": "STALE",
                        "review_validity": "STALE_MATERIAL_CHANGE",
                        "delegation_id": "d" * 64,
                        "result_sha256": "e" * 64,
                    },
                ),
                patch(
                    "runtime.control_plane.independent_review_procedures.spawn_review_worker"
                ) as spawn,
            ):
                result = run_launch_independent_review(
                    identity_request(LAUNCH_PROCEDURE_ID),
                    state_root=state_root,
                )

            spawn.assert_not_called()
            self.assertEqual("pending", result["status"])
            self.assertFalse(result["automatic_launch_performed"])
            self.assertEqual("STALE", result["automatic_review_status"])
            self.assertEqual(
                "STALE_MATERIAL_CHANGE",
                result["automatic_review_validity"],
            )
            self.assertEqual("e" * 64, result["automatic_worker_result_sha256"])

    def test_stale_completed_worker_payload_remains_noncompleting_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            prepared_review = review_state.prepare_review_operation(
                identity_value(),
                state_root=state_root,
            )
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            payload = stale_result(review_run_id=prepared_review.review_run_id)
            fake_snapshot = SimpleNamespace(
                result_state="recorded",
                result_status="COMPLETED",
                result_payload=payload,
                delegation_id="d" * 64,
                result_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            )

            with patch(
                "runtime.control_plane.independent_review_delegation.load_delegation",
                return_value=fake_snapshot,
            ):
                settlement = settle_review_from_delegation(
                    identity_value(),
                    reviewer_state_root=state_root,
                    delegation_state_root=state_root / "agent-sessions",
                    submit_result=lambda _review_run_id, _result: self.fail(
                        "noncompleting result must not invoke submit"
                    ),
                )

            self.assertIsNotNone(settlement)
            assert settlement is not None
            self.assertEqual("review_terminal_noncompleting", settlement["status"])
            self.assertEqual("STALE", settlement["review_status"])
            self.assertEqual(
                "STALE_MATERIAL_CHANGE",
                settlement["review_validity"],
            )

            pending = review_state.reconcile_independent_review_result(
                identity_value(),
                state_root=state_root,
            )
            self.assertEqual("pending", pending["status"])
            self.assertEqual("open", pending["result_state"])

    def test_terminal_manual_fallback_skips_late_automatic_settlement(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            reconcile = identity_request(RECONCILE_PROCEDURE_ID)
            manual = run_reconcile_independent_review_result(
                {**reconcile, "manual_result": pass_result()},
                state_root=state_root,
            )
            self.assertEqual("manual-fallback-recorded", manual["result_state"])

            with patch(
                "runtime.control_plane.independent_review_procedures.settle_review_from_delegation"
            ) as settle:
                repeated = run_reconcile_independent_review_result(
                    reconcile,
                    state_root=state_root,
                )

            settle.assert_not_called()
            self.assertEqual("recorded", repeated["status"])
            self.assertEqual("manual-fallback-recorded", repeated["result_state"])
            self.assertEqual("manual", repeated["result_source"])
            self.assertEqual(pass_result(), repeated["result"])

    def test_manual_fallback_winning_during_automatic_settlement_remains_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            review_state.prepare_review_operation(identity_value(), state_root=state_root)
            review_state.mark_dispatch_attempted(identity_value(), state_root=state_root)
            reconcile = identity_request(RECONCILE_PROCEDURE_ID)

            def lose_automatic_race(*args, **kwargs):
                review_state.reconcile_independent_review_result(
                    {**identity_value(), "manual_result": pass_result()},
                    state_root=state_root,
                )
                raise review_state.ReviewStateError(
                    "automatic submission is closed by manual fallback"
                )

            with (
                patch(
                    "runtime.control_plane.independent_review_procedures.review_delegation_state_root",
                    return_value=state_root / "agent-sessions",
                ),
                patch(
                    "runtime.control_plane.independent_review_procedures.settle_review_from_delegation",
                    side_effect=lose_automatic_race,
                ),
            ):
                result = run_reconcile_independent_review_result(
                    reconcile,
                    state_root=state_root,
                )

            self.assertEqual("recorded", result["status"])
            self.assertEqual("manual-fallback-recorded", result["result_state"])
            self.assertEqual("manual", result["result_source"])
            self.assertEqual(pass_result(), result["result"])

    def test_fixed_procedure_schemas_reject_generic_authority_fields(self) -> None:
        forbidden = (
            {"url": "https://chatgpt.com/"},
            {"prompt": "do something"},
            {"command": "whoami"},
            {"path": "elsewhere"},
            {"backend": "arbitrary"},
            {"github_token": "secret"},
        )
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            for extra in forbidden:
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    run_launch_independent_review(
                        {**identity_request(LAUNCH_PROCEDURE_ID), **extra},
                        state_root=state_root,
                    )

    def test_submit_and_reconcile_require_their_exact_registered_procedure_ids(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            with self.assertRaises(ValueError):
                run_submit_independent_review_result(
                    {
                        "procedure": "wrong",
                        "review_run_id": "a" * 64,
                        "result": "x",
                    },
                    state_root=state_root,
                )
            with self.assertRaises(ValueError):
                run_reconcile_independent_review_result(
                    identity_request("wrong"),
                    state_root=state_root,
                )

    def test_cli_rejects_reviewer_state_inside_readable_workspace_before_genesis(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace_root = Path(workspace_dir)
            for state_root in (
                workspace_root,
                workspace_root / ".chat-agent-platform" / "procedure-state",
            ):
                with self.subTest(state_root=state_root), self.assertRaisesRegex(
                    ValueError,
                    r"independent-review state directory must be path-disjoint from the readable workspace",
                ):
                    control_plane_cli._dispatch_registered_procedure(
                        identity_request(LAUNCH_PROCEDURE_ID),
                        workspace_root=workspace_root,
                        state_root=state_root,
                        candidate_admission=None,
                    )
                self.assertFalse(
                    (state_root / review_state.STATE_DIRECTORY).exists(),
                    "privacy rejection must happen before review genesis/state creation",
                )

    def test_cli_rejects_workspace_equal_to_or_below_actual_review_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir)
            state_root = root / "procedure-state"
            review_root = state_root / review_state.STATE_DIRECTORY
            for workspace_root in (review_root, review_root / "nested-workspace"):
                workspace_root.mkdir(parents=True, exist_ok=True)
                with self.subTest(workspace_root=workspace_root), self.assertRaisesRegex(
                    ValueError,
                    r"independent-review state directory must be path-disjoint from the readable workspace",
                ):
                    control_plane_cli._dispatch_registered_procedure(
                        identity_request(LAUNCH_PROCEDURE_ID),
                        workspace_root=workspace_root,
                        state_root=state_root,
                        candidate_admission=None,
                    )
                self.assertEqual(
                    [],
                    list(review_root.glob("*.genesis.json")),
                    "inverse-overlap rejection must happen before private genesis creation",
                )

    def test_cli_privacy_guard_does_not_change_non_review_procedure_policy(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            workspace_root = Path(workspace_dir)
            control_plane_cli._require_private_review_state_root(
                control_plane_cli.WORKSPACE_ARTIFACT_PROCEDURE_ID,
                workspace_root=workspace_root,
                state_root=workspace_root / ".chat-agent-platform" / "procedure-state",
            )


if __name__ == "__main__":
    unittest.main()
