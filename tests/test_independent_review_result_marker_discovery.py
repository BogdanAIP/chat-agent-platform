from __future__ import annotations

import unittest

from runtime.control_plane import independent_review_state as review_state


BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def identity() -> review_state.ReviewIdentity:
    return review_state.parse_review_identity(
        {
            "repository": "BogdanAIP/chat-agent-platform",
            "pr_number": 141,
            "base_sha": BASE_SHA,
            "head_sha": HEAD_SHA,
            "review_skill": "code-review",
            "review_skill_version": "1.1",
        }
    )


def header_lines(*, status: str = "PASS", findings: int = 0) -> list[str]:
    return [
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
        "review_validity=CURRENT",
        f"reported_findings={findings}",
        "rejected_candidates=0",
        "reviewed_at=2026-08-31T16:00:00+00:00",
    ]


def finding_lines() -> list[str]:
    return [
        "### FINDING 1",
        "severity = P2",
        "location = runtime/control_plane/independent_review_state.py:1",
        "introduced_by = exact parser branch",
        "failure_mechanism = quoted protocol marker appears in evidence",
        "consequence = valid completed result would be rejected",
        "supporting_evidence = parser evidence follows",
        "```text",
        "REVIEW_RESULT_V1",
        "repository=quoted/example",
        "```",
        "falsification_attempt = checked header and body parser paths",
        "why_it_survives = global marker scanning would count the quoted literal",
    ]


def simple_finding_lines() -> list[str]:
    return [
        "### FINDING 1",
        "severity = P2",
        "location = runtime/control_plane/independent_review_state.py:423",
        "introduced_by = accepted outer wrapper was treated as evidence fencing",
        "failure_mechanism = schema visibility hid the complete finding body",
        "consequence = canonical fenced FINDINGS result could not be recorded",
        "supporting_evidence = code-review v1.1 structured result contract",
        "falsification_attempt = checked bare and fenced parser paths",
        "why_it_survives = only the fenced FINDINGS path lost all schema lines",
    ]


class IndependentReviewMarkerDiscoveryTests(unittest.TestCase):
    def test_quoted_result_marker_in_fenced_evidence_is_not_a_second_header(self) -> None:
        payload = "\n".join([*header_lines(status="FINDINGS", findings=1), "", *finding_lines()])
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("FINDINGS", parsed.header["status"])
        self.assertEqual(1, parsed.header["reported_findings"])

    def test_governing_text_fenced_header_form_remains_accepted(self) -> None:
        payload = "\n".join(["```text", *header_lines(), "```"])
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("PASS", parsed.header["status"])
        self.assertEqual(0, parsed.header["reported_findings"])

    def test_governing_text_fenced_findings_form_remains_accepted(self) -> None:
        payload = "\n".join(
            ["```text", *header_lines(status="FINDINGS", findings=1), "", *simple_finding_lines(), "```"]
        )
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("FINDINGS", parsed.header["status"])
        self.assertEqual(1, parsed.header["reported_findings"])

    def test_outer_transport_fence_does_not_expose_nested_evidence_schema(self) -> None:
        payload = "\n".join(
            ["````text", *header_lines(status="FINDINGS", findings=1), "", *finding_lines(), "````"]
        )
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("FINDINGS", parsed.header["status"])
        self.assertEqual(1, parsed.header["reported_findings"])

    def test_prose_before_result_marker_is_not_accepted_as_wire_header(self) -> None:
        payload = "\n".join(["preface", *header_lines()])
        with self.assertRaisesRegex(
            review_state.ReviewStateError,
            r"review result must begin with REVIEW_RESULT_V1",
        ):
            review_state.parse_review_result(
                payload,
                expected_identity=identity(),
                automatic=False,
            )


if __name__ == "__main__":
    unittest.main()
