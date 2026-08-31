from __future__ import annotations

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


def malformed_findings_result(review_run_id: str) -> str:
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
            "status=FINDINGS",
            "review_validity=CURRENT",
            "reported_findings=2",
            "rejected_candidates=0",
            "reviewed_at=2026-08-31T14:39:26+00:00",
            f"review_run_id={review_run_id}",
            "",
            "### FINDING 1",
            "severity = P1",
            "location = runtime/control_plane/example.py:10",
            "introduced_by = changed behavior",
            "failure_mechanism = reachable path",
            "consequence = broken invariant",
            "supporting_evidence = direct code evidence",
            "falsification_attempt = checked neighboring guard",
            "why_it_survives =",
            "```text",
            "```",
            "---",
            "### FINDING 2",
            "severity = P2",
            "location = runtime/control_plane/example.py:20",
            "introduced_by = second changed behavior",
            "failure_mechanism = second reachable path",
            "consequence = second broken invariant",
            "supporting_evidence = second direct code evidence",
            "falsification_attempt = checked second neighboring guard",
            "why_it_survives = second candidate remains valid",
        ]
    )


class IndependentReviewStructuralContentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.state_root = Path(self.temp.name) / "procedure-state"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_structural_markdown_cannot_satisfy_empty_required_finding_field(self) -> None:
        prepared = review_state.prepare_review_operation(
            identity_dict(), state_root=self.state_root
        )
        review_state.mark_dispatch_attempted(
            identity_dict(), state_root=self.state_root
        )

        root = review_state._review_root(self.state_root)
        state_path = review_state._state_path(root, prepared.operation_key)
        before = state_path.read_bytes()
        payload = malformed_findings_result(prepared.review_run_id)

        with self.assertRaisesRegex(
            review_state.ReviewStateError,
            r"finding 1 field why_it_survives must have substantive inline content",
        ):
            review_state.submit_independent_review_result(
                {"review_run_id": prepared.review_run_id, "result": payload},
                state_root=self.state_root,
            )

        self.assertEqual(before, state_path.read_bytes())
        pending = review_state.reconcile_independent_review_result(
            identity_dict(), state_root=self.state_root
        )
        self.assertEqual("pending", pending["status"])
        self.assertEqual("open", pending["result_state"])
        self.assertTrue(pending["automatic_submission_open"])

    def test_heading_and_table_scaffold_cannot_fill_empty_inline_field(self) -> None:
        identity = review_state.parse_review_identity(identity_dict())
        payload = "\n".join(
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
                "status=FINDINGS",
                "review_validity=CURRENT",
                "reported_findings=1",
                "rejected_candidates=0",
                "reviewed_at=2026-08-31T15:32:24+00:00",
                "",
                "### FINDING 1",
                "severity = P2",
                "location = runtime/control_plane/example.py:20",
                "introduced_by = changed behavior",
                "failure_mechanism = reachable path",
                "consequence = broken invariant",
                "supporting_evidence =",
                "## Evidence",
                "| source | detail |",
                "| --- | --- |",
                "| code | parser |",
                "falsification_attempt = checked neighboring guard",
                "why_it_survives = candidate remains valid",
            ]
        )

        with self.assertRaisesRegex(
            review_state.ReviewStateError,
            r"finding 1 field supporting_evidence must have substantive inline content",
        ):
            review_state.parse_review_result(
                payload,
                expected_identity=identity,
                automatic=False,
            )


if __name__ == "__main__":
    unittest.main()
