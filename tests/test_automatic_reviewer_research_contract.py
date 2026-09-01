from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"
RESEARCH = CONTEXT / "AUTOMATIC_REVIEWER_RESEARCH.md"
CURRENT = CONTEXT / "CURRENT_STATE.md"
REUSE = CONTEXT / "ARCHITECTURE_REUSE_BASELINE.md"
BENCHMARK_STRATEGY = CONTEXT / "BENCHMARK_EVALUATION_STRATEGY.md"
SKILL = ROOT / ".agents" / "skills" / "code-review" / "SKILL.md"


CANONICAL_LINEAGE = {"KEEP", "REUSE_MORE", "REFINE", "REPLACE", "DEFER", "REJECT"}


def _markdown_value(value: str) -> str:
    return value.strip().replace("**", "").replace("`", "")


class AutomaticReviewerResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.research = RESEARCH.read_text(encoding="utf-8")
        self.current = CURRENT.read_text(encoding="utf-8")
        self.reuse = REUSE.read_text(encoding="utf-8")
        self.benchmark_strategy = BENCHMARK_STRATEGY.read_text(encoding="utf-8")
        self.skill = SKILL.read_text(encoding="utf-8")
        self.folded = self.research.casefold()

    def test_stage_research_has_required_sections(self) -> None:
        for heading in (
            "## Stage goal",
            "## Current project baseline",
            "## Architecture lineage comparison",
            "## Architecture primitives and adjacent domains",
            "## Problem evidence",
            "## Solution evidence",
            "## Best current approaches",
            "## Failure lessons",
            "## Alternatives comparison",
            "## Source-code evidence",
            "## Failure/Crash Matrix",
            "## Fit to this architecture",
            "## Reviewer evaluation method",
            "## Acceptance checks",
            "## Architecture decision",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, self.research)

    def test_narrow_is_accepted_after_research_pr_merge(self) -> None:
        # The immutable reviewer research Brief keeps the historical adoption condition.
        self.assertIn("NARROW (PROPOSED UNTIL THIS PR IS ACCEPTED)", self.research)
        self.assertIn("Production implementation remains blocked until this research PR", self.research)
        self.assertIn("effective only after this PR is accepted and merged", self.research)

        # CURRENT_STATE is the live owner. Agent Session / Delegation may supersede
        # reviewer automation as the product-level critical path without deleting
        # the already accepted reviewer-specific fallback and fixed procedures.
        self.assertIn("AGENT_SESSION_DELEGATION_REENTRY.md", self.current)
        self.assertIn("PR #149", self.current)
        self.assertIn("## Automatic reviewer status", self.current)
        self.assertIn(
            "automatic-review Stage Research / local-result v1 ACCEPTED NARROW / MERGED #140",
            self.current,
        )
        self.assertIn("automatic-review local state foundation           ACCEPTED / MERGED #141", self.current)
        self.assertIn("automatic-review fixed procedure wiring           ACCEPTED / MERGED #142", self.current)
        for procedure in (
            "launch_independent_review_v1",
            "submit_independent_review_result_v1",
            "reconcile_independent_review_result_v1",
        ):
            self.assertIn(procedure, self.current)
        self.assertIn("remain intact", self.current)
        self.assertIn("not deleted or silently replaced by #149", self.current)
        self.assertNotIn("Production implementation is **still blocked** until #140", self.current)
        self.assertNotIn("PR #140 is currently the **open acceptance gate**", self.current)

    def test_first_slice_stays_review_specific_and_local_result_only(self) -> None:
        for phrase in (
            "launch_independent_review_v1",
            "submit_independent_review_result_v1",
            "reconcile_independent_review_result_v1",
            "review_run_id",
            "manual fallback",
            "There is **no GitHub write in reviewer automation v1**",
        ):
            self.assertIn(phrase, self.research)
        for forbidden in (
            "project-owned allowlisted publisher creates at most one top-level PR result comment",
            "dedicated GitHub App installation token",
            "POST /repos/<exact owner>/<exact repo>/issues/<exact pr>/comments",
        ):
            self.assertNotIn(forbidden, self.research)
        self.assertIn("waiting -> wake -> planner continuation", self.folded)
        self.assertIn("automatic wake/resampling", self.folded)
        self.assertIn("scheduler/event bus", self.folded)

    def test_local_operation_reuses_lock_genesis_and_atomic_checkpoint(self) -> None:
        for phrase in (
            "Accepted Stage 26.3C cooperating-runner lock",
            "Accepted Stage 26.3C crash-oriented file primitives",
            "_TaskLock",
            "_acquire_task_lock",
            "_exclusive_create_file",
            "_write_checkpoint",
            "_load_checkpoint",
            "_validate_resume_state",
            "immutable genesis",
            "sibling-temp",
            "os.fsync",
            "os.replace",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_genesis_state_pair_fails_closed_without_false_power_loss_claim(self) -> None:
        for phrase in (
            "valid genesis, missing mutable state",
            "state exists, genesis missing",
            "pair/nonce mismatch",
            "hostile deletion",
            "storage rollback",
            "machine/power-loss",
            "outside declared v1 guarantee",
            "no guarantee claimed",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_genesis_only_crash_has_manual_only_terminal_recovery(self) -> None:
        for phrase in (
            "crash after fsynced genesis before initial mutable checkpoint",
            "same original review_run_id retained",
            "automatic relaunch and automatic submit forbidden",
            "manual_recovery_required",
            "complete fresh manual result",
            "automation-abandoned",
            "manual-fallback-recorded",
            "never generate a replacement nonce and never relaunch",
            "genesis-only-crash manual-closure test",
            "genesis-plus-temp manual-recovery test",
            "manual-only terminal recovery",
            "fail-closed must not mean permanently uncloseable",
        ):
            self.assertIn(phrase.casefold(), self.folded)
        self.assertIn("0 late accepted automatic results", self.folded)
        self.assertIn("temp is never parsed as authority", self.folded)

    def test_direct_solution_domain_evidence_covers_filesystem_and_browser_claim(self) -> None:
        for source in (
            "https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html",
            "https://pubs.opengroup.org/onlinepubs/009695399/functions/fsync.html",
            "https://docs.python.org/3/library/os.html#os.fsync",
            "https://docs.python.org/3/library/os.html#os.replace",
            "https://www.w3.org/TR/IndexedDB/#transaction-scheduling",
            "https://www.w3.org/TR/IndexedDB/#dom-idbobjectstore-add",
            "https://www.w3.org/TR/IndexedDB/#dom-idbtransaction-abort",
            "https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle",
            "https://developer.chrome.com/docs/extensions/how-to/test/test-serviceworker-termination-with-puppeteer",
        ):
            with self.subTest(source=source):
                self.assertIn(source, self.research)
        self.assertIn("overlapping `readwrite` transactions do not run simultaneously", self.research)
        self.assertIn("fails with `ConstraintError` when the key already exists", self.research)
        self.assertIn("workers may terminate after inactivity or unexpectedly", self.research)

    def test_reviewer_authority_requires_unreachability_not_non_selection(self) -> None:
        for phrase in (
            "GitHub mutation actions are unavailable to the reviewer security context",
            "disconnected/disabled/unavailable",
            "Action Control",
            "only read actions are available",
            "Per-message non-selection",
            "approval policy",
            "reviewer_authority_unqualified",
            "fail closed",
        ):
            self.assertIn(phrase.casefold(), self.folded)
        for source in (
            "https://help.openai.com/en/articles/11487775",
            "https://help.openai.com/en/articles/11509118",
            "https://help.openai.com/en/articles/12584461",
        ):
            self.assertIn(source, self.research)

    def test_result_handoff_is_local_and_manual_fallback_closes_late_submit(self) -> None:
        for phrase in (
            "result_state = open | automatic-result-recorded | manual-fallback-recorded",
            "submit_independent_review_result_v1",
            "reconcile_independent_review_result_v1",
            "same OS lock",
            "same-nonce/same-digest",
            "already_recorded",
            "manual-fallback-recorded",
            "late automatic submit",
            "late submit rejected",
            "later automatic submit cannot appear after",
            "final development-side reconciliation",
        ):
            self.assertIn(phrase.casefold(), self.folded)
        self.assertIn("manual fallback and automatic submit race", self.folded)
        self.assertIn("winner commits authoritative result", self.folded)
        self.assertIn("0 late accepted results", self.folded)

    def test_existing_role_lineage_table_uses_exactly_one_canonical_decision(self) -> None:
        section = self.research.split("## Architecture lineage comparison", 1)[1].split(
            "## Architecture primitives and adjacent domains", 1
        )[0]
        rows = [line for line in section.splitlines() if line.startswith("|")]
        data_rows = [line for line in rows if "---" not in line and "Role |" not in line]
        self.assertGreaterEqual(len(data_rows), 8)
        for row in data_rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            self.assertEqual(4, len(cells), row)
            decision = _markdown_value(cells[2])
            with self.subTest(role=cells[0], decision=decision):
                self.assertIn(decision, CANONICAL_LINEAGE)
        self.assertIn("NEW_ARCHITECTURE", section)
        self.assertIn("Scope qualifiers are separate", section)

    def test_reuse_baseline_preserves_old_postures_and_new_reviewer_rows_are_unambiguous(self) -> None:
        self.assertIn("`PREFERRED_CANDIDATE_REVALIDATE_BEFORE_ADOPTION`", self.reuse)
        self.assertIn("`REFERENCE_REVALIDATE_PER_STAGE`", self.reuse)
        self.assertIn("Existing historical posture labels in this table are preserved", self.reuse)
        role_map = self.reuse.split("## Canonical role map", 1)[1].split("## How to compare a new mechanism", 1)[0]
        rows = [line for line in role_map.splitlines() if line.startswith("| Automatic")]
        self.assertGreaterEqual(len(rows), 8)
        allowed = CANONICAL_LINEAGE | {"NEW_ARCHITECTURE"}
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            self.assertEqual(7, len(cells), row)
            posture = _markdown_value(cells[-1])
            with self.subTest(role=cells[0], posture=posture):
                self.assertIn(posture, allowed)

    def test_source_code_evidence_uses_required_classifications(self) -> None:
        for phrase in (
            "harbor-framework/harbor",
            "389bd4f8ce796ef4a97de4b62675021e262c8e76",
            "OPEN_IMPLEMENTED",
            "REUSE_COMPONENT",
            "openai/codex",
            "94cbbddafc1776d5e377bca1b05932c697e82238",
            "REFERENCE_ONLY",
            "NOT_FOUND_AFTER_TARGETED_SEARCH",
            "OpenHands/OpenHands",
            "1098d73df42351a31b2940557efb9fe8750365c4",
            "ADAPT_MECHANIC",
            "REJECT_MECHANIC",
            "ignores a replayed tool call",
            "tests/unit/test_single_step_trial.py",
            "thread_manager_tests.rs",
        ):
            self.assertIn(phrase, self.research)

    def test_failure_matrix_has_required_dimensions_and_new_race_shields(self) -> None:
        for heading in (
            "Boundary / failure",
            "Authoritative durable state",
            "Possible physical state",
            "Required fresh evidence",
            "Retry / reconciliation permission",
            "Shield / test",
            "Max unauthorized additional effect",
        ):
            self.assertIn(heading, self.research)
        for phrase in (
            "authority environment not qualified",
            "two tabs claim same run",
            "manual fallback and automatic submit race",
            "manual fallback commits first",
            "automatic result commits first",
            "late-submit test",
            "0 late results",
            "crash after fsynced genesis before initial mutable checkpoint",
            "missing-state manual-recovery test",
        ):
            self.assertIn(phrase, self.research)

    def test_skill_matches_local_only_result_handoff(self) -> None:
        self.assertRegex(self.skill, r'(?m)^\s*version:\s*"1\.1"\s*$')
        self.assertIn("## 14. Bounded automatic local result-submission envelope", self.skill)
        self.assertIn("submit_independent_review_result_v1", self.skill)
        self.assertIn("reconcile_independent_review_result_v1", self.skill)
        self.assertIn("no reachable GitHub mutation action", self.skill)
        self.assertIn("no GitHub write and no external result-publication side effect", self.skill)
        self.assertNotIn("project-owned publisher", self.skill)
        self.assertNotIn("PR Conversation comment", self.skill)

    def test_benchmark_plan_remains_evaluation_only(self) -> None:
        for phrase in ("Harbor", "ReviewBench", "SWE-Review-Bench", "CR-Bench"):
            self.assertIn(phrase, self.research)
        self.assertIn("Do **not** collapse these planes into one score", self.research)
        self.assertIn("baseline, not a release exam", self.folded)
        self.assertIn("Reviewer — first active rung", self.benchmark_strategy)
        self.assertIn("Code-review evaluation harness", self.reuse)
        self.assertIn("evaluation only", self.research.casefold())


if __name__ == "__main__":
    unittest.main()
