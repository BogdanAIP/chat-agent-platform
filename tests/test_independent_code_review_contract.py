from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
SKILL = ROOT / ".agents" / "skills" / "code-review" / "SKILL.md"


class IndependentCodeReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = SKILL.read_text(encoding="utf-8")
        self.agents = AGENTS.read_text(encoding="utf-8")

    def test_skill_is_discoverable_and_versioned(self) -> None:
        self.assertTrue(self.skill.startswith("---\n"))
        self.assertRegex(self.skill, r"(?m)^name:\s*code-review\s*$")
        self.assertRegex(self.skill, r'(?m)^\s*version:\s*"1\.1"\s*$')
        self.assertIn("fresh ordinary-ChatGPT", self.skill)

    def test_review_request_is_bound_to_exact_repository_pr_base_and_head(self) -> None:
        for field in (
            "REVIEW_REQUEST_V1",
            "repository=<owner/repo>",
            "pr_number=<number>",
            "base_sha=<40-hex SHA>",
            "head_sha=<40-hex SHA>",
            "review_skill=code-review",
            "review_skill_version=<version expected by caller>",
        ):
            self.assertIn(field, self.skill)
        self.assertIn("PR.base.sha == REVIEW_REQUEST.base_sha", self.skill)
        self.assertIn("PR.head.sha == REVIEW_REQUEST.head_sha", self.skill)
        self.assertIn("Never silently review a newer head than the request", self.skill)

    def test_review_policy_comes_from_base_and_target_semantics_from_head(self) -> None:
        self.assertIn("review policy / AGENTS.md / code-review skill -> BASE_SHA", self.skill)
        self.assertIn("review target and its changed code/docs/tests     -> HEAD_SHA", self.skill)
        self.assertIn("cannot weaken the accepted BASE review protocol", self.skill)
        self.assertIn("accepted BASE review policy governs adoption", self.skill)

    def test_primary_review_is_fresh_ordinary_chat_and_not_work_or_codex(self) -> None:
        hard_boundary = self.skill.split("## 1. Require an immutable review request", 1)[0]
        self.assertIn("fresh **ordinary ChatGPT** conversation/context", hard_boundary)
        self.assertIn("must not use ChatGPT Work, Workspace Agents, Codex automation or Codex Review", hard_boundary)
        self.assertIn("Codex quota exhaustion does not waive this skill's required primary review", hard_boundary)
        self.assertIn("No other model/service is required", hard_boundary)

    def test_launcher_requires_fresh_context_and_qualified_authority(self) -> None:
        launcher = self.skill.split("## 13. One-time Review Task launcher contract", 1)[1].split(
            "## 14. Bounded automatic local result-submission envelope", 1
        )[0]
        self.assertIn("REVIEW_REQUEST_V1", launcher)
        self.assertIn("Do not attach development-chat reasoning summaries", launcher)
        self.assertIn("review_context=ordinary_chat_fresh", launcher)
        self.assertIn("Work, Workspace Agents or Codex", launcher)
        self.assertIn("manually opened fresh ordinary-ChatGPT conversation", launcher)
        self.assertIn("must not return the private `review_run_id`", launcher)
        self.assertIn("GitHub mutation actions are actually unavailable", launcher)
        self.assertIn("Per-message non-selection and approval prompts do not satisfy this condition", launcher)
        self.assertIn("fail closed before automatic Send", launcher)

    def test_findings_require_concrete_evidence_and_falsification(self) -> None:
        for phrase in (
            "introduced by the reviewed diff",
            "falsification pass",
            "inspect neighboring code and callers",
            "verify the suspected path is reachable",
            "If the finding cannot survive this attempt to disprove it, drop it",
            "failure_mechanism",
            "supporting_evidence",
            "falsification_attempt",
            "why_it_survives",
        ):
            self.assertIn(phrase, self.skill)

    def test_reviewer_cannot_self_fix_or_mutate_target(self) -> None:
        self.assertIn("The independent reviewer does not patch the PR in the same review run", self.skill)
        self.assertIn("does not mutate production/repository state", self.skill)
        self.assertIn("does **not** give the reviewer GitHub write authority", self.skill)
        self.assertIn("store the already-computed review result in project-owned local state", self.skill)
        for disposition in ("CONFIRMED", "REJECTED", "SUPERSEDED"):
            self.assertIn(disposition, self.skill)
        self.assertIn("Do not merge with unresolved reported findings", self.skill)

    def test_material_changes_invalidate_review(self) -> None:
        invalidation = self.skill.split("## 10. Review invalidation", 1)[1].split(
            "## 11. Final exact-head gate", 1
        )[0]
        for phrase in (
            "production/runtime code",
            "security or authorization policy",
            "persistence/recovery/retry/reconciliation",
            "concurrency/identity/ownership/provenance",
            "verification or Finish Gate semantics",
            "tests whose semantics define acceptance",
            "repository merge/review policy itself",
            "base-branch advance",
        ):
            self.assertIn(phrase, invalidation)

    def test_structured_result_can_fail_closed(self) -> None:
        for phrase in (
            "REVIEW_RESULT_V1",
            "review_policy_ref=<BASE_SHA>",
            "review_context=ordinary_chat_fresh",
            "status=PASS | FINDINGS | ABSTAIN | STALE",
            "review_validity=CURRENT | STALE_BASE_CHANGE | STALE_MATERIAL_CHANGE",
            "never translate missing evidence into `PASS`",
        ):
            self.assertIn(phrase, self.skill)

    def test_automatic_path_is_local_only_and_idempotently_reconcilable(self) -> None:
        envelope = self.skill.split("## 14. Bounded automatic local result-submission envelope", 1)[1]
        for phrase in (
            "procedure=submit_independent_review_result_v1",
            "no reachable GitHub mutation action or raw GitHub write credential",
            "automatic-result-recorded",
            "no GitHub write and no external result-publication side effect",
            "same-nonce/same-digest",
            "already_recorded",
            "reconcile_independent_review_result_v1",
            "manual-fallback-recorded",
            "a later automatic submit after manual closure is rejected",
            "APPROVE",
            "REQUEST_CHANGES",
            "merge, close or reopen the PR",
            "change repository settings",
        ):
            self.assertIn(phrase, envelope)
        self.assertNotIn("PR Conversation comment", envelope)
        self.assertNotIn("project-owned publisher", envelope)
        self.assertNotIn("GitHub App", envelope)
        self.assertIn("review_run_id=<same value received in REVIEW_REQUEST_V1>", self.skill)

    def test_final_gate_requires_local_result_reconciliation(self) -> None:
        gate = self.skill.split("## 11. Final exact-head gate", 1)[1].split("## 12. Structured result", 1)[0]
        self.assertIn("reconcile project-owned local review-result state", gate)
        self.assertIn("manual result must be atomically recorded through the same reconciliation state machine", gate)
        self.assertIn("late automatic submit cannot create a second unresolved result", gate)
        self.assertIn("verify PR base/head still match reviewed identity", gate)

    def test_agents_merge_policy_requires_chatgpt_review_and_makes_codex_optional(self) -> None:
        merge_policy = self.agents.split("## Merge policy", 1)[1].split(
            "## PR/document discipline", 1
        )[0]
        required = (
            "independent semantic review is required",
            ".agents/skills/code-review/SKILL.md",
            "fresh ordinary ChatGPT",
            "exact `BASE_SHA..HEAD_SHA`",
            "Codex Review is an optional additional reviewer",
            "Codex quota exhaustion does not block merge",
            "ChatGPT Work",
            "material post-review change",
            "final exact-head CI",
            "unresolved reported findings",
        )
        folded = merge_policy.casefold()
        for phrase in required:
            self.assertIn(phrase.casefold(), folded)
        self.assertNotRegex(
            merge_policy,
            re.compile(r"(?i)codex review\s+(?:is\s+)?(?:mandatory|required)"),
        )


if __name__ == "__main__":
    unittest.main()
