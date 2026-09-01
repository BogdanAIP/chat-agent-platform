from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIEF = (
    ROOT / "project-context" / "AUTOMATIC_REVIEWER_AUTHORITY_RESEARCH.md"
).read_text(encoding="utf-8")
BASELINE = (
    ROOT / "project-context" / "ARCHITECTURE_REUSE_BASELINE.md"
).read_text(encoding="utf-8")
CURRENT = (ROOT / "project-context" / "CURRENT_STATE.md").read_text(encoding="utf-8")


class AutomaticReviewerAuthorityResearchContractTests(unittest.TestCase):
    def test_reentry_is_narrow_and_bound_to_the_accepted_post_142_base(self) -> None:
        self.assertIn("STAGE RESEARCH — NARROW", BRIEF)
        self.assertIn("90a8e16e6a1badecd3315968339ca691634b7ee4", BRIEF)
        self.assertIn("PR #142 = merged", BRIEF)
        self.assertIn("no production/browser consequence claimed", BRIEF)

    def test_personal_plus_authority_is_removed_by_non_personalized_temporary_chat(self) -> None:
        self.assertIn("non-personalized Temporary Chat", BRIEF)
        self.assertIn("do not use plugins", BRIEF)
        self.assertIn("no ChatGPT plugins are available", BRIEF)
        self.assertIn("GitHub plugin mutation actions absent", BRIEF)
        self.assertIn("URL alone is not authority", BRIEF)
        self.assertIn("positive live proof", BRIEF)
        self.assertIn("manual fresh review", BRIEF)

    def test_native_handoff_is_submit_only_and_not_a_generic_local_bridge(self) -> None:
        self.assertIn("submit-only Native Messaging host", BRIEF)
        self.assertIn("allowed_origins", BRIEF)
        self.assertIn("accepted action = submit_independent_review_result_v1 only", BRIEF)
        self.assertIn(
            "accepted fields = schema_version, review_run_id, result only",
            BRIEF,
        )
        self.assertIn("state root = installed private manager configuration, never caller supplied", BRIEF)
        self.assertIn("procedure/action/path/command/url/backend/repository override = impossible", BRIEF)
        self.assertIn("direct browser access to current 1MCP `/mcp`", BRIEF)
        self.assertIn("generic Native Messaging command host", BRIEF)
        self.assertIn("no broad Local Bridge/MCP authority", BRIEF)

    def test_existing_result_state_remains_authoritative(self) -> None:
        self.assertIn("accepted local review state remains the only result authority", BRIEF)
        self.assertIn("local state machine remains the final parser/validator", BRIEF)
        self.assertIn("same-nonce/same-digest", BRIEF)
        self.assertIn("manual fallback races late native submit", BRIEF)
        self.assertIn("whichever commits first closes slot", BRIEF)

    def test_browser_admission_rejects_noncompleting_or_mismatched_results(self) -> None:
        self.assertIn("assistant turn is no longer streaming", BRIEF)
        self.assertIn("CURRENT PASS", BRIEF)
        self.assertIn("CURRENT FINDINGS", BRIEF)
        self.assertIn("ABSTAIN", BRIEF)
        self.assertIn("STALE", BRIEF)
        self.assertIn("identity-mismatched outputs are not submitted", BRIEF)
        self.assertIn("exact repository/PR/BASE/HEAD/skill/version/context/review_run_id", BRIEF)

    def test_public_surface_and_planner_boundaries_do_not_expand(self) -> None:
        self.assertIn("public Chat-facing semantic inventory remains unchanged", BRIEF)
        self.assertIn("public semantic inventory remains exactly six tools", BRIEF)
        self.assertIn("no seventh public Chat-facing semantic tool", BRIEF)
        self.assertIn("automatic wake remains out of scope", BRIEF)
        self.assertIn("not a second reviewer", BRIEF)
        self.assertIn("not a second planner", BRIEF)

    def test_policy_refinement_is_required_before_automatic_acceptance(self) -> None:
        self.assertIn("Required policy refinement before automatic mode is accepted", BRIEF)
        self.assertIn("code-review` v1.1", BRIEF)
        self.assertIn("reviewer context", BRIEF)
        self.assertIn("unaltered completed reviewer output", BRIEF)
        self.assertIn("implementation PR itself remains governed by accepted BASE", BRIEF)

    def test_failure_matrix_covers_authority_transport_and_races(self) -> None:
        for required in (
            "URL opens normal/personalized chat",
            "Temporary Chat page state is ambiguous",
            "concurrent tabs reach Send",
            "crash after claim before Send",
            "assistant response still streaming",
            "wrong extension calls native host",
            "native host crashes before state commit",
            "state commits but native response is lost",
            "manual fallback races late native submit",
            "extension/native-host source drifts after install",
            "exact PR head changes while reviewer works",
        ):
            self.assertIn(required, BRIEF)
        self.assertIn("No release-critical matrix cell is intentionally answered with blind retry", BRIEF)

    def test_canonical_lineage_is_updated_with_the_replacement(self) -> None:
        self.assertIn("Automatic-review reviewer authority qualification", BASELINE)
        self.assertIn("non-personalized ordinary ChatGPT Temporary Chat", BASELINE)
        self.assertIn("managed read-only Action Control", BASELINE)
        self.assertIn("AUTOMATIC_REVIEWER_AUTHORITY_RESEARCH.md", BASELINE)
        self.assertIn("submit-only Native Messaging host", BASELINE)

    def test_live_state_records_142_as_accepted_and_reentry_as_research_only(self) -> None:
        self.assertIn("automatic-review fixed procedure wiring", CURRENT)
        self.assertIn("ACCEPTED / MERGED #142", CURRENT)
        self.assertIn("AUTOMATIC_REVIEWER_AUTHORITY_RESEARCH.md", CURRENT)
        self.assertIn("research re-entry", CURRENT.lower())
        self.assertIn("production remains blocked", CURRENT.lower())


if __name__ == "__main__":
    unittest.main()
