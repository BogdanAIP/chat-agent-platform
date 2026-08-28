from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "source-code-research" / "SKILL.md"
BASELINE = ROOT / "project-context" / "ARCHITECTURE_REUSE_BASELINE.md"
CODEX_REVIEW = ROOT / "project-context" / "CODEX_AGENT_HOST_SOURCE_REVIEW.md"


def _split_markdown_table_row(line: str) -> tuple[str, ...]:
    body = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    code_delimiter_len: int | None = None
    escaped = False
    index = 0
    while index < len(body):
        char = body[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            index += 1
            continue
        if char == "`":
            run_end = index + 1
            while run_end < len(body) and body[run_end] == "`":
                run_end += 1
            run_len = run_end - index
            current.append(body[index:run_end])
            if code_delimiter_len is None:
                code_delimiter_len = run_len
            elif run_len == code_delimiter_len:
                code_delimiter_len = None
            index = run_end
            continue
        if char == "|" and code_delimiter_len is None:
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return tuple(cells)


def _reuse_baseline_rows(text: str) -> dict[str, tuple[str, ...]]:
    section = text.split("## Canonical role map", 1)[1]
    rows: dict[str, tuple[str, ...]] = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = _split_markdown_table_row(line)
        if len(cells) != 7 or cells[0] in {"Architectural role", "---"}:
            continue
        if set(cells[0]) == {"-"}:
            continue
        rows[cells[0]] = cells
    return rows


class SourceCodeResearchContractTests(unittest.TestCase):
    def test_source_code_research_is_discoverable_and_requires_exact_ref_evidence(self) -> None:
        self.assertTrue(SKILL.is_file())
        text = SKILL.read_text(encoding="utf-8")

        required = (
            "name: source-code-research",
            "README-only/product-description review does not count as implementation evidence",
            "bind the repository to an exact commit SHA or immutable tag",
            "trace the relevant execution/state path",
            "inspect tests for the claimed invariant or lifecycle",
            "OPEN_IMPLEMENTED",
            "OPEN_PARTIAL",
            "DOCUMENTED_ONLY",
            "CLOSED_OR_UNKNOWN",
            "NOT_FOUND_AFTER_TARGETED_SEARCH",
            "### Source-code evidence",
            "A Stage Research Brief that relies on a public implementation but contains only README/docs-level evidence is incomplete",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_agent_harness_research_compares_codex_and_an_independent_implementation(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("`openai/codex` is a mandatory comparison reference", text)
        self.assertIn("at least **one independent mature open agent/harness implementation**", text)
        self.assertIn("Examples of currently relevant public repositories include", text)
        self.assertIn("`OpenHands/OpenHands`", text)
        self.assertIn("`aaif-goose/goose`", text)
        self.assertIn("`cline/cline`", text)
        self.assertIn("research candidates, not selected dependencies", text)

    def test_code_research_does_not_replace_domain_evidence_or_project_authority(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        for phrase in (
            "Source-code study complements domain evidence rather than replacing it",
            "A strong reference implementation is not automatically a dependency",
            "deterministic Control Plane authority",
            "project `WorkingState`",
            "Verification Kernel and independent Finish Gate",
            "bounded public semantic tool surface",
            "physical Browser/Windows verification guarantees",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_codex_reference_has_pinned_source_evidence(self) -> None:
        self.assertTrue(CODEX_REVIEW.is_file())
        review = CODEX_REVIEW.read_text(encoding="utf-8")

        self.assertIn("PINNED SOURCE-CODE RESEARCH EVIDENCE — REFERENCE ONLY", review)
        self.assertIn("Upstream repository: `openai/codex`", review)
        self.assertRegex(
            review,
            re.compile(r"Exact inspected upstream ref:\s*\n\s*`[0-9a-f]{40}`"),
        )
        for path in (
            "codex-rs/app-server/src/request_processors/thread_processor.rs",
            "codex-rs/app-server/tests/suite/v2/thread_resume.rs",
            "codex-rs/core/src/context/world_state/persistent_mode.rs",
            "codex-rs/core/src/context/world_state/persistent_mode_tests.rs",
            "codex-rs/core/src/agent/control/spawn.rs",
            "codex-rs/core/src/tools/handlers/send_user_message_async.rs",
            "codex-rs/core/tests/suite/send_user_message_async.rs",
        ):
            with self.subTest(path=path):
                self.assertIn(path, review)

        self.assertIn("Classification: `OPEN_IMPLEMENTED`", review)
        self.assertIn("Classification: `NOT_FOUND_AFTER_TARGETED_SEARCH`", review)
        self.assertIn("this is **not proof that such a mechanism does not exist anywhere in Codex**", review)
        self.assertIn("lesson classification: `REFERENCE_ONLY`", review)
        self.assertIn("Persistent wake/scheduler mechanism: **unresolved**", review)

    def test_reuse_baseline_records_codex_reference_in_the_correct_columns(self) -> None:
        baseline = BASELINE.read_text(encoding="utf-8")
        rows = _reuse_baseline_rows(baseline)
        role = "Agent session / long-lived host lifecycle and orchestration"
        self.assertIn(role, rows)

        row = rows[role]
        source = row[1]
        intended_reuse = row[2]
        not_delegated = row[3]
        detailed_owner = row[5]
        posture = row[6]

        self.assertIn("`openai/codex`", source)
        self.assertIn("source-code reference implementation", source)
        self.assertIn("not a selected runtime dependency", source)

        for phrase in (
            "App Server/thread lifecycle",
            "resume/fork",
            "WorldState/Persistent context transitions",
            "agent-graph parent/child ownership",
            "async user messaging",
        ):
            with self.subTest(intended=phrase):
                self.assertIn(phrase, intended_reuse)

        for phrase in (
            "project Control Plane authority",
            "WorkingState",
            "Verification Kernel",
            "Finish Gate",
            "capability grants",
            "bounded public semantic surface",
            "unresolved wake/scheduler semantics",
        ):
            with self.subTest(not_delegated=phrase):
                self.assertIn(phrase, not_delegated)

        self.assertIn("`CODEX_AGENT_HOST_SOURCE_REVIEW.md`", detailed_owner)
        self.assertEqual(posture, "`REFERENCE_REVALIDATE_PER_STAGE`")

        self.assertIn(".agents/skills/source-code-research/SKILL.md", baseline)
        self.assertIn("exact upstream ref, concrete implementation paths/symbols", baseline)


if __name__ == "__main__":
    unittest.main()
