from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "project-context" / "RUST_NATIVE_HOST_BOUNDARY_RESEARCH.md"

_DECISION_RE = re.compile(
    r"<!-- RUST_BOUNDARY_DECISION_V1\n(?P<body>.*?)\n-->",
    re.DOTALL,
)


def _decision_fields(text: str) -> dict[str, str]:
    matches = list(_DECISION_RE.finditer(text))
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one structured Rust research decision, got {len(matches)}"
        )

    fields: dict[str, str] = {}
    for line in matches[0].group("body").splitlines():
        key, separator, value = line.partition("=")
        if not separator or not key or not value:
            raise AssertionError(f"invalid decision field: {line!r}")
        if key in fields:
            raise AssertionError(f"duplicate decision field: {key}")
        fields[key] = value
    return fields


class RustNativeHostResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RESEARCH.read_text(encoding="utf-8")
        self.decision = _decision_fields(self.text)

    def test_structured_decision_is_single_and_fail_closed(self) -> None:
        self.assertEqual(
            self.decision,
            {
                "stage_decision": "DEFER",
                "production_rust": "BLOCKED",
                "future_native_boundary": "RESEARCH_ONLY",
                "future_native_language": "UNRESOLVED",
                "critical_path_change": "NO",
            },
        )
        self.assertIn(
            "sole implementation-decision representation in this Brief",
            self.text,
        )
        self.assertNotRegex(
            self.text,
            r"(?im)^\s*(?:top-level\s+)?stage research (?:result|decision)\s*[:=]\s*`?(?:PROCEED|NARROW)`?\s*$",
        )
        self.assertNotRegex(
            self.text.lower(),
            r"production rust(?: work)?\s+(?:is|=)\s+(?:now\s+)?(?:authorized|allowed|unblocked|enabled|open(?:ed)?)\b",
        )
        self.assertNotRegex(
            self.text.lower(),
            r"(?:this brief|this research|the decision)\s+(?:now\s+)?(?:authorizes|allows|unblocks|enables|opens)\s+production rust\b",
        )
        self.assertIn("Production Rust work is blocked", self.text)
        self.assertIn("Stage 26.3C continues", self.text)

    def test_future_boundary_is_narrow_below_authority_and_language_unresolved(self) -> None:
        required = (
            "future optional native host (language unresolved)",
            "process / process-tree ownership",
            "Windows Job Objects / native process handles",
            "sandbox bootstrap / native OS containment",
            "below project authority",
            "typed private IPC",
            "does not select its implementation language",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_project_authority_is_not_delegated_to_native_executor(self) -> None:
        for phrase in (
            "must not become a planner",
            "decide `PASS`",
            "decide task `DONE`",
            "own `WorkingState`",
            "six-tool Chat-facing surface",
            "executor `success` cannot directly create project Verification `PASS` or Finish `DONE`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_same_boundary_language_alternatives_are_compared(self) -> None:
        headings = (
            "### A — keep current Python/Node/PowerShell with no new native-host boundary",
            "### B — narrow language-neutral/current-runtime native boundary",
            "### C — narrow Rust native host below project authority",
            "### D — migrate Control Plane / WorkingState / broad agent runtime to Rust",
            "### E — move only durable checkpoint/state storage to Rust",
        )
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.text)

        self.assertIn("credible same-boundary alternative", self.text)
        self.assertIn("credible candidate, not selected", self.text)
        self.assertIn("Future native-host language remains `UNRESOLVED`", self.text)
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

    def test_source_code_negative_space_and_failure_history_are_recorded(self) -> None:
        self.assertIn("did **not** locate a dedicated direct test", self.text)
        self.assertIn("Classification: `OPEN_PARTIAL`", self.text)
        self.assertIn(
            "does **not** claim to have proven its complete lifecycle implementation",
            self.text,
        )
        self.assertIn("036fc75b1f89ca0af9fee84162064758183b0bc0", self.text)
        self.assertIn("5–7 second beach-ball", self.text)
        self.assertIn(
            "does not decide which language our future native boundary should use",
            self.text,
        )

    def test_duplicate_delivery_contract_keeps_invariant_but_not_mechanism(self) -> None:
        required = (
            "P4 — lost acknowledgement exposes a separate idempotency/concurrency research problem",
            "logical_operation_id + attempt_id",
            "maximum physical effects before reconciliation: at most one spawn for one authorized attempt",
            "duplicate or concurrent delivery must never increase that maximum",
            "`OUTCOME_UNKNOWN` / unresolved",
            "`CONFIRMED_NOT_APPLIED`",
            "`CONFIRMED_APPLIED`",
            "`STILL_UNKNOWN`",
            "Implementation mechanism is intentionally unspecified",
            "consistency boundary, crash behavior, retained state, contention model, alternatives and failure history",
            "duplicate/concurrent delivery fault test proving the **at-most-one-spawn** invariant",
            "separate research evidence for whatever consistency primitive is proposed",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

        forbidden_selected_mechanisms = (
            "may atomically claim one attempt_id",
            "must be atomically deduplicated before spawn",
            "atomic claim/dedup",
            "durable native attempt ledger",
        )
        for phrase in forbidden_selected_mechanisms:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.text)

    def test_domain_evidence_and_failure_matrix_are_present(self) -> None:
        for phrase in (
            "Engineering-domain evidence",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "PR_SET_PDEATHSIG",
            "Failure / Crash Matrix",
            "nested-job/assignment failure",
            "PID reused",
            "OS/machine power loss",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_reentry_requires_observed_trigger_and_fresh_comparison(self) -> None:
        self.assertIn("Re-entry triggers", self.text)
        self.assertIn("repeated accepted evidence of leaked child/grandchild processes", self.text)
        self.assertIn("Re-run fresh Stage Research before production Rust work", self.text)
        self.assertIn("not timeless architecture", self.text)
        self.assertIn(
            "compare Rust against an equivalent language-neutral/current-runtime implementation",
            self.text,
        )
        self.assertIn(
            "Any proposed duplicate/concurrent-delivery primitive is itself a material concurrency/recovery mechanism",
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
