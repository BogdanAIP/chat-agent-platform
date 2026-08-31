from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
import unittest

from runtime.control_plane import independent_review_state as review_state


BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def identity_dict() -> dict[str, object]:
    return {
        "repository": "BogdanAIP/chat-agent-platform",
        "pr_number": 141,
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "review_skill": "code-review",
        "review_skill_version": "1.1",
    }


def finding_block(number: int, *, severity: str = "P1", omit: str | None = None) -> str:
    fields = [
        ("severity", severity),
        ("location", "runtime/control_plane/independent_review_state.py — result parser"),
        ("introduced_by", "The reviewed diff introduced this exact behavior."),
        ("failure_mechanism", "A concrete accepted input reaches the failing branch."),
        ("consequence", "The mandatory review lifecycle cannot complete correctly."),
        ("supporting_evidence", "The exact-head code and focused regression reproduce it."),
        ("falsification_attempt", "Neighboring guards and recovery paths were checked."),
        ("why_it_survives", "No accepted guard defeats the concrete scenario."),
    ]
    lines = [f"### FINDING {number}"]
    for name, value in fields:
        if name == omit:
            continue
        lines.append(f"**{name} =** {value}")
    return "\n\n".join(lines)


def review_result(
    *,
    status: str = "PASS",
    findings: int = 0,
    review_run_id: str | None = None,
    body: str = "",
) -> str:
    validity = "CURRENT" if status in {"PASS", "FINDINGS", "ABSTAIN"} else "STALE_MATERIAL_CHANGE"
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
        f"status={status}",
        f"review_validity={validity}",
        f"reported_findings={findings}",
        "rejected_candidates=0",
        "reviewed_at=2026-08-31T13:46:25+00:00",
    ]
    if review_run_id is not None:
        lines.append(f"review_run_id={review_run_id}")
    if body:
        lines.extend(["", body])
    return "\n".join(lines)


class IndependentReviewResultCompletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "procedure-state"
        self.identity = review_state.parse_review_identity(identity_dict())
        self.operation_key = review_state.review_operation_key(self.identity)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def dispatch(self) -> review_state.PreparedReviewOperation:
        prepared = review_state.prepare_review_operation(identity_dict(), state_root=self.state_root)
        review_state.mark_dispatch_attempted(identity_dict(), state_root=self.state_root)
        return prepared

    def state_path(self) -> Path:
        root = review_state._review_root(self.state_root)
        return review_state._state_path(root, self.operation_key)

    def test_automatic_abstain_is_noncompleting_and_manual_pass_can_close_same_operation(self) -> None:
        prepared = self.dispatch()
        before = self.state_path().read_bytes()
        abstain = review_result(status="ABSTAIN", review_run_id=prepared.review_run_id)

        with self.assertRaisesRegex(review_state.ReviewStateError, "non-completing.*ABSTAIN"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": abstain},
                state_root=self.state_root,
            )

        self.assertEqual(before, self.state_path().read_bytes())
        pending = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("pending", pending["status"])
        self.assertTrue(pending["automatic_submission_open"])

        manual = review_result(body="Fresh manual review completed after automatic ABSTAIN.")
        closed = review_state.reconcile_independent_review_result(
            {**identity_dict(), "manual_result": manual},
            state_root=self.state_root,
        )
        self.assertEqual("manual-fallback-recorded", closed["result_state"])
        self.assertEqual("manual", closed["result_source"])
        self.assertEqual(manual, closed["result"])

    def test_manual_abstain_and_stale_do_not_close_open_operation(self) -> None:
        self.dispatch()
        before = self.state_path().read_bytes()
        for status in ("ABSTAIN", "STALE"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(review_state.ReviewStateError, "non-completing"):
                    review_state.reconcile_independent_review_result(
                        {**identity_dict(), "manual_result": review_result(status=status)},
                        state_root=self.state_root,
                    )
                self.assertEqual(before, self.state_path().read_bytes())

    def test_complete_findings_result_is_accepted_and_round_trips(self) -> None:
        prepared = self.dispatch()
        payload = review_result(
            status="FINDINGS",
            findings=2,
            review_run_id=prepared.review_run_id,
            body="\n\n---\n\n".join(
                [finding_block(1, severity="P1"), finding_block(2, severity="P2")]
            ),
        )
        recorded = review_state.submit_independent_review_result(
            {"review_run_id": prepared.review_run_id, "result": payload},
            state_root=self.state_root,
        )
        self.assertEqual("recorded", recorded["status"])
        consumed = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual(payload, consumed["result"])
        self.assertEqual("automatic-result-recorded", consumed["result_state"])

    def test_findings_header_without_body_is_rejected_before_checkpoint_write(self) -> None:
        prepared = self.dispatch()
        before = self.state_path().read_bytes()
        payload = review_result(
            status="FINDINGS",
            findings=1,
            review_run_id=prepared.review_run_id,
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "finding body count"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": payload},
                state_root=self.state_root,
            )
        self.assertEqual(before, self.state_path().read_bytes())

    def test_findings_missing_required_field_is_rejected(self) -> None:
        prepared = self.dispatch()
        payload = review_result(
            status="FINDINGS",
            findings=1,
            review_run_id=prepared.review_run_id,
            body=finding_block(1, omit="falsification_attempt"),
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "missing required fields"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": payload},
                state_root=self.state_root,
            )

    def test_findings_count_and_severity_order_must_match_structured_bodies(self) -> None:
        prepared = self.dispatch()
        wrong_count = review_result(
            status="FINDINGS",
            findings=2,
            review_run_id=prepared.review_run_id,
            body=finding_block(1),
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "finding body count"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": wrong_count},
                state_root=self.state_root,
            )

        wrong_order = review_result(
            status="FINDINGS",
            findings=2,
            review_run_id=prepared.review_run_id,
            body="\n\n".join([finding_block(1, severity="P2"), finding_block(2, severity="P1")]),
        )
        with self.assertRaisesRegex(review_state.ReviewStateError, "severity order"):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": wrong_order},
                state_root=self.state_root,
            )

    def test_load_rejects_tampered_terminal_abstain_state(self) -> None:
        prepared = self.dispatch()
        payload = review_result(status="ABSTAIN", review_run_id=prepared.review_run_id)
        state_path = self.state_path()
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["revision"] += 1
        state["result_state"] = "automatic-result-recorded"
        state["result_source"] = "automatic"
        state["result_body_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        state["result_payload"] = payload
        state["result_recorded_at"] = "2026-08-31T13:46:25+00:00"
        state["updated_at"] = "2026-08-31T13:46:25+00:00"
        state_path.write_text(json.dumps(state), encoding="utf-8")

        with self.assertRaisesRegex(review_state.ReviewStateError, "recorded review result is non-completing"):
            review_state.reconcile_independent_review_result(
                identity_dict(), state_root=self.state_root
            )


if __name__ == "__main__":
    unittest.main()
