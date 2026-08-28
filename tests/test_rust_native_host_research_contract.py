from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "project-context" / "RUST_NATIVE_HOST_BOUNDARY_RESEARCH.md"


class RustNativeHostResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RESEARCH.read_text(encoding="utf-8")

    def test_production_rust_is_explicitly_deferred(self) -> None:
        self.assertIn("STAGE RESEARCH BRIEF — DEFER PRODUCTION ADOPTION", self.text)
        self.assertIn("Top-level Stage Research decision: `DEFER`", self.text)
        self.assertIn("do not migrate the deterministic Control Plane", self.text)
        self.assertIn("Stage 26.3C continues", self.text)

    def test_future_candidate_is_narrow_native_host_below_authority(self) -> None:
        required = (
            "future optional Rust native host",
            "process / process-tree ownership",
            "Windows Job Objects / native process handles",
            "sandbox bootstrap / native OS containment",
            "below project authority",
            "typed private IPC",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_project_authority_is_not_delegated_to_native_host(self) -> None:
        for phrase in (
            "must not become a planner",
            "decide `PASS`",
            "decide task `DONE`",
            "own `WorkingState`",
            "six-tool Chat-facing surface",
            "native `success` cannot directly create project Verification `PASS` or Finish `DONE`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_research_compares_current_stack_narrow_host_and_broad_rewrite(self) -> None:
        headings = (
            "### A — keep current Python/Node/PowerShell",
            "### B — narrow Rust native host below project authority",
            "### C — migrate Control Plane / WorkingState / broad agent runtime to Rust",
            "### D — move only durable checkpoint/state storage to Rust",
        )
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.text)

        self.assertIn("Disposition: **KEEP current production**", self.text)
        self.assertIn("production `DEFER` now", self.text)
        self.assertIn("REJECT for the current architecture horizon", self.text)
        self.assertIn("DEFER as separate persistence research", self.text)

    def test_source_code_evidence_is_pinned(self) -> None:
        refs = (
            "openai/codex@4ee04c0aa5833ac39b1763f6ea44c7bc777c83dd",
            "aaif-goose/goose@a9060fd2eff2ef32c207bb39e9f0e229b8a2fb87",
            "cline/cline@1fbcfab05dccad23c12ef75ce45f99d711a82fb7",
            "OpenHands/OpenHands@226a6d2e68ebd5c86e4f275a0f33ca25f1ee0878",
        )
        for ref in refs:
            with self.subTest(ref=ref):
                self.assertIn(ref, self.text)

    def test_source_code_negative_space_is_recorded(self) -> None:
        self.assertIn(
            "targeted search at this exact ref",
            self.text,
        )
        self.assertIn(
            "did **not** locate a dedicated direct test",
            self.text,
        )
        self.assertIn("Classification: `OPEN_PARTIAL`", self.text)
        self.assertIn(
            "does **not** claim to have proven its complete lifecycle implementation",
            self.text,
        )

    def test_domain_evidence_and_failure_matrix_are_present(self) -> None:
        for phrase in (
            "Engineering-domain evidence",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "PR_SET_PDEATHSIG",
            "Failure / Crash Matrix",
            "nested-job/assignment-failure",
            "PID reused",
            "OS/machine power loss",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_reentry_requires_observed_trigger_and_fresh_research(self) -> None:
        self.assertIn("Re-entry triggers", self.text)
        self.assertIn("repeated accepted evidence of leaked child/grandchild processes", self.text)
        self.assertIn("Re-run fresh Stage Research before production Rust work", self.text)
        self.assertIn("not timeless architecture", self.text)


if __name__ == "__main__":
    unittest.main()
