from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.control_plane import independent_review_state as review_state
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


class IndependentReviewProcedureWiringTests(unittest.TestCase):
    def test_launch_prepares_exact_operation_but_fails_closed_before_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            result = run_launch_independent_review(
                identity_request(LAUNCH_PROCEDURE_ID),
                state_root=state_root,
            )

            self.assertEqual("abstained", result["status"])
            self.assertEqual(LAUNCH_PROCEDURE_ID, result["procedure_id"])
            self.assertEqual("reviewer_authority_unqualified", result["escalation_reason"])
            self.assertEqual("prepared", result["dispatch_state"])
            self.assertEqual("open", result["result_state"])
            self.assertFalse(result["automatic_launch_performed"])
            self.assertFalse(result["automatic_submission_open"])
            self.assertNotIn("review_run_id", result)

            prepared = review_state.prepare_review_operation(identity_value(), state_root=state_root)
            self.assertFalse(prepared.created)
            self.assertEqual("prepared", prepared.dispatch_state)
            self.assertEqual("open", prepared.result_state)

    def test_repeated_launch_reuses_operation_without_disclosing_nonce(self) -> None:
        with tempfile.TemporaryDirectory() as state_dir:
            state_root = Path(state_dir)
            first = run_launch_independent_review(
                identity_request(LAUNCH_PROCEDURE_ID),
                state_root=state_root,
            )
            second = run_launch_independent_review(
                identity_request(LAUNCH_PROCEDURE_ID),
                state_root=state_root,
            )

            self.assertEqual(first["operation_key"], second["operation_key"])
            self.assertNotIn("review_run_id", first)
            self.assertNotIn("review_run_id", second)
            self.assertEqual("prepared", second["dispatch_state"])

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


if __name__ == "__main__":
    unittest.main()
