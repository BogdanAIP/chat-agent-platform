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


def header() -> str:
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
            "reported_findings=1",
            "rejected_candidates=0",
            "reviewed_at=2026-08-31T13:46:25+00:00",
        ]
    )


def fields() -> str:
    return "\n\n".join(
        [
            "**severity =** P1",
            "**location =** runtime/control_plane/independent_review_state.py",
            "**introduced_by =** Exact reviewed behavior.",
            "**failure_mechanism =** Concrete accepted input reaches the branch.",
            "**consequence =** The required lifecycle breaks.",
            "**supporting_evidence =** Exact-head code and regression evidence.",
            "**falsification_attempt =** Neighboring guards were checked.",
            "**why_it_survives =** No accepted guard defeats the scenario.",
        ]
    )


class IndependentReviewResultFormatAliasTests(unittest.TestCase):
    def test_headingless_finding_uses_required_severity_field_as_group_boundary(self) -> None:
        payload = header() + "\n\n" + fields()
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("FINDINGS", parsed.header["status"])
        self.assertEqual(1, parsed.header["reported_findings"])

    def test_alternate_numbered_heading_is_accepted_without_weakening_fields(self) -> None:
        payload = header() + "\n\nFinding 1:\n\n" + fields()
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("FINDINGS", parsed.header["status"])


if __name__ == "__main__":
    unittest.main()
