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


def header(findings: int = 1) -> list[str]:
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
        "status=FINDINGS",
        "review_validity=CURRENT",
        f"reported_findings={findings}",
        "rejected_candidates=0",
        "reviewed_at=2026-08-31T15:32:24+00:00",
        "",
    ]


def valid_fields() -> list[str]:
    return [
        "severity = P1",
        "location = runtime/control_plane/example.py:42",
        "introduced_by = exact changed branch",
        "failure_mechanism = reachable failing path",
        "consequence = incorrect terminal authority",
        "supporting_evidence = commit 0123456789abcdef at https://github.com/example/repo",
        "falsification_attempt = checked `guard != None` and neighboring tests",
        "why_it_survives = no guard defeats the path",
    ]


class IndependentReviewFencedSchemaTests(unittest.TestCase):
    def test_fenced_schema_shaped_lines_cannot_supply_missing_required_fields(self) -> None:
        for opener, closer in (("```text", "```"), ("~~~text", "~~~")):
            with self.subTest(opener=opener):
                payload = "\n".join(
                    [
                        *header(),
                        "### FINDING 1",
                        "severity = P1",
                        "location = runtime/control_plane/example.py:42",
                        "introduced_by = exact changed branch",
                        opener,
                        "failure_mechanism = quoted example only",
                        "consequence = quoted example only",
                        "supporting_evidence = quoted example only",
                        "falsification_attempt = quoted example only",
                        "why_it_survives = quoted example only",
                        closer,
                    ]
                )
                with self.assertRaisesRegex(
                    review_state.ReviewStateError,
                    r"finding 1 is missing required fields",
                ):
                    review_state.parse_review_result(
                        payload,
                        expected_identity=identity(),
                        automatic=False,
                    )

    def test_fenced_severity_and_heading_do_not_create_extra_findings(self) -> None:
        payload = "\n".join(
            [
                *header(),
                "### FINDING 1",
                *valid_fields(),
                "```text",
                "### FINDING 2",
                "severity = P0",
                "location = quoted/example.py:1",
                "```",
            ]
        )
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual(1, parsed.header["reported_findings"])
        self.assertEqual("FINDINGS", parsed.header["status"])

    def test_indented_code_schema_does_not_duplicate_fields_or_create_findings(self) -> None:
        payload = "\n".join(
            [
                *header(),
                "### FINDING 1",
                *valid_fields(),
                "    ### FINDING 2",
                "    severity = P0",
                "    location = quoted/example.py:1",
                "    why_it_survives = quoted code only",
            ]
        )
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual(1, parsed.header["reported_findings"])
        self.assertEqual("FINDINGS", parsed.header["status"])

    def test_indented_code_cannot_supply_missing_required_fields(self) -> None:
        payload = "\n".join(
            [
                *header(),
                "### FINDING 1",
                "severity = P1",
                "location = runtime/control_plane/example.py:42",
                "introduced_by = exact changed branch",
                "    failure_mechanism = quoted example only",
                "    consequence = quoted example only",
                "    supporting_evidence = quoted example only",
                "    falsification_attempt = quoted example only",
                "    why_it_survives = quoted example only",
            ]
        )
        with self.assertRaisesRegex(
            review_state.ReviewStateError,
            r"finding 1 is missing required fields",
        ):
            review_state.parse_review_result(
                payload,
                expected_identity=identity(),
                automatic=False,
            )

    def test_legitimate_inline_code_path_sha_and_url_evidence_remain_valid(self) -> None:
        payload = "\n".join([*header(), "FINDING 1", *valid_fields()])
        parsed = review_state.parse_review_result(
            payload,
            expected_identity=identity(),
            automatic=False,
        )
        self.assertEqual("CURRENT", parsed.header["review_validity"])
        self.assertEqual(1, parsed.header["reported_findings"])


if __name__ == "__main__":
    unittest.main()
