from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "project-context"


def _markdown_level_one_headings(text: str) -> tuple[str, ...]:
    """Extract GFM/CommonMark level-1 headings outside fenced code blocks."""

    headings: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    pending_setext_title: str | None = None

    for line in text.splitlines():
        fence = re.match(r"^ {0,3}((?:`{3,})|(?:~{3,}))(?:[^\n]*)$", line)
        if fence is not None:
            marker = fence.group(1)
            char = marker[0]
            if fence_char is None:
                fence_char = char
                fence_length = len(marker)
            elif char == fence_char and len(marker) >= fence_length:
                fence_char = None
                fence_length = 0
            pending_setext_title = None
            continue

        if fence_char is not None:
            continue

        atx = re.match(r"^ {0,3}#(?!#)(?:[ \t]+|$)(.*?)(?:[ \t]+#+[ \t]*)?$", line)
        if atx is not None:
            title = atx.group(1).strip()
            if title:
                headings.append(title)
            pending_setext_title = None
            continue

        if re.match(r"^ {0,3}=+[ \t]*$", line) is not None:
            if pending_setext_title:
                headings.append(pending_setext_title)
            pending_setext_title = None
            continue

        if not line.strip() or re.match(r"^ {4}", line):
            pending_setext_title = None
            continue

        pending_setext_title = line.strip()

    return tuple(headings)


class DocumentationConsistencyTests(unittest.TestCase):
    def test_current_document_owners_are_classified_and_historical_default_is_explicit(self) -> None:
        status = (CONTEXT / "DOCUMENT_STATUS.md").read_text(encoding="utf-8")
        required = (
            "CONTINUATION_CONTEXT.md",
            "START_HERE.md",
            "CURRENT_STATE.md",
            "PROJECT_RISKS.md",
            "ARCHITECTURE.md",
            "CONTROL_PLANE.md",
            "COMPUTER_USE_ARCHITECTURE.md",
            "SECURITY_POLICY.md",
            "ROADMAP.md",
            "DOCUMENT_STATUS.md",
            "EVIDENCE_INDEX.md",
            "ARCHITECTURE_REUSE_BASELINE.md",
            "STAGE26_3B_VERIFICATION_KERNEL.md",
        )
        for name in required:
            with self.subTest(name=name):
                self.assertIn(f"`{name}`", status)

        folded = status.casefold()
        self.assertIn("historical / reference by default", folded)
        self.assertIn("current continuation aid", folded)
        self.assertIn("subordinate", folded)
        self.assertIn("current_state.md", folded)
        self.assertIn("active pr/design snapshot", folded)

    def test_authoritative_docs_use_current_planner_control_plane_boundary(self) -> None:
        files = [
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            CONTEXT / "CONTINUATION_CONTEXT.md",
            CONTEXT / "START_HERE.md",
            CONTEXT / "CURRENT_STATE.md",
            CONTEXT / "PROJECT_RISKS.md",
            CONTEXT / "ARCHITECTURE.md",
            CONTEXT / "CONTROL_PLANE.md",
            CONTEXT / "COMPUTER_USE_ARCHITECTURE.md",
            CONTEXT / "ROADMAP.md",
            CONTEXT / "CONSTRAINTS.md",
            CONTEXT / "DECISIONS.md",
            CONTEXT / "DEVELOPMENT_PRINCIPLES.md",
            CONTEXT / "SECURITY_POLICY.md",
            CONTEXT / "MODULE_CATALOG.md",
            CONTEXT / "MODULE_SELECTION_POLICY.md",
            CONTEXT / "VISION.md",
        ]
        for path in files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Control Plane", text)

        control_plane = (CONTEXT / "CONTROL_PLANE.md").read_text(encoding="utf-8")
        folded = control_plane.casefold()
        self.assertIn("only current general planner", folded)
        self.assertIn("deterministic", folded)
        self.assertIn("track p", folded)
        self.assertIn("optional", folded)
        self.assertIn("abstain", folded)

    def test_obsolete_architecture_phrases_do_not_return_to_live_docs(self) -> None:
        live_files = [
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            CONTEXT / "CONTINUATION_CONTEXT.md",
            CONTEXT / "START_HERE.md",
            CONTEXT / "CURRENT_STATE.md",
            CONTEXT / "ARCHITECTURE.md",
            CONTEXT / "CONTROL_PLANE.md",
            CONTEXT / "COMPUTER_USE_ARCHITECTURE.md",
            CONTEXT / "ROADMAP.md",
            CONTEXT / "CONSTRAINTS.md",
            CONTEXT / "DEVELOPMENT_PRINCIPLES.md",
            CONTEXT / "KNOWN_ISSUES.md",
        ]
        forbidden = [
            "no second local planner/Agent Control Plane",
            "Do not insert a local generic Agent Control Plane/Planner",
            "Stage 26.3 must separately establish",
            "Stage 26.3 desktop surface",
            "Codex/automation should perform",
            "fresh ChatGPT/Codex session",
            "active architecture/docs pr = #116",
            "active — final provenance gap",
            "pr #114 fresh hosted checks",
        ]
        for path in live_files:
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_release_order_has_one_authoritative_owner(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        current = (CONTEXT / "CURRENT_STATE.md").read_text(encoding="utf-8")
        continuation = (CONTEXT / "CONTINUATION_CONTEXT.md").read_text(encoding="utf-8")
        status = (CONTEXT / "DOCUMENT_STATUS.md").read_text(encoding="utf-8")

        ordered_sequence = re.compile(
            r"26\.3C[\s\S]{0,3000}?26\.4[\s\S]{0,3000}?26\.5[\s\S]{0,3000}?27[\s\S]{0,3000}?28",
            re.IGNORECASE,
        )
        self.assertRegex(roadmap, ordered_sequence)
        self.assertIn("ROADMAP.md", current)
        self.assertIn("ROADMAP.md", continuation)
        self.assertIn("release sequence", status.casefold())

        # Active PR/design snapshots are intentionally centralized in CURRENT_STATE.
        self.assertIn("active PR/design snapshot", status)
        self.assertNotIn("draft #126", roadmap.casefold())
        self.assertNotIn("hard-link final create", roadmap.casefold())

    def test_authoritative_roadmap_stages_are_capability_owned(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")

        # A prior accepted-looking roadmap heading promoted a research candidate
        # into the release sequence while the coarse release-order check stayed
        # green. The first attempted guard filtered only known stage prefixes,
        # which meant a new prefix (for example "Pre-26.5") could reproduce the
        # same failure class invisibly. Parse both ATX and Setext level-1
        # headings outside fenced code, then pin the complete level-1 ROADMAP
        # structure so any new authoritative-looking top-level section requires
        # an explicit review/guard update instead of silently entering the
        # release document.
        sequence_block = re.search(
            r"The remaining product sequence is:\s*\x60{3}text\s*(?P<body>.*?)\x60{3}",
            roadmap,
            re.IGNORECASE | re.DOTALL,
        )
        self.assertIsNotNone(sequence_block)
        assert sequence_block is not None
        release_stage_titles = tuple(
            match.group(1).strip()
            for match in re.finditer(
                r"(?m)^\d+\.\s+(.+?)\s*$",
                sequence_block.group("body"),
            )
        )
        self.assertEqual(
            release_stage_titles,
            (
                "Reviewer reuse over the accepted Delegation lifecycle",
                "General computer-use coverage",
                "External procedure integration",
                "Skill lifecycle",
                "Skill acquisition",
                "Hybrid capability use",
                "Distribution",
                "Stable release",
            ),
        )

        # Guard the extractor itself against the two counterexamples that
        # defeated/over-constrained earlier versions of this check.
        self.assertEqual(
            _markdown_level_one_headings(
                "Pre-26.5 — OpenAdapt integration qualification\n====\n"
            ),
            ("Pre-26.5 — OpenAdapt integration qualification",),
        )
        self.assertEqual(
            _markdown_level_one_headings(
                "```text\n# not a roadmap heading\n```\n# Real heading\n"
            ),
            ("Real heading",),
        )

        top_level_headings = _markdown_level_one_headings(roadmap)
        self.assertEqual(
            top_level_headings,
            (
                "Roadmap — Chat Agent Platform",
                "26.3B — Verification Kernel + independent Finish Gate — ACCEPTED / CLOSED",
                "26.3C — WorkingState + recovery/reconciliation + LoopGuard — ACCEPTED / CLOSED",
                "Post-26.3C — bounded Agent Session / Delegation — ACCEPTED BOUNDED SCOPE",
                "Automatic reviewer — first specialist consumer after generic Agent Session acceptance",
                "Broad real-application physical coverage gate",
                "Pre-26.4 — bounded external-procedure integration qualification",
                "26.4 — Human Demo -> verified candidate skill / lineage",
                "26.5 — Hybrid Computer-Use Integration",
                "Future research seam — same-task continuation / wake",
                "Future research seam — Physical Device / IoT Capability Family",
                "Local Execution Kernel — adjacent future consequence class",
                "27 — Distribution & Maintenance",
                "28 — Clean User E2E / stable release",
                "Track M expansion beyond the first bounded slice — FUTURE",
                "Parallel Track P — optional future local planner",
            ),
            msg=(
                "authoritative ROADMAP top-level structure changed; classify the "
                "new section explicitly before it can enter the release document"
            ),
        )

    def test_future_local_planner_is_explicitly_non_release_critical(self) -> None:
        roadmap = (CONTEXT / "ROADMAP.md").read_text(encoding="utf-8")
        control = (CONTEXT / "CONTROL_PLANE.md").read_text(encoding="utf-8")
        roadmap_folded = roadmap.casefold()
        control_folded = control.casefold()

        self.assertIn("track p", roadmap_folded)
        self.assertIn("optional future", roadmap_folded)
        self.assertIn("shadow/proposal-only", roadmap_folded)
        self.assertIn("deterministic control plane", roadmap_folded)
        self.assertIn("optional track p research", control_folded)

    def test_computer_use_architecture_preserves_small_surface_and_independent_completion(self) -> None:
        computer_use = (CONTEXT / "COMPUTER_USE_ARCHITECTURE.md").read_text(encoding="utf-8")
        folded = computer_use.casefold()
        self.assertIn("accepted six-tool/product architecture", folded)
        self.assertIn("state first", folded)
        self.assertIn("finish gate", folded)
        self.assertIn("loopguard", folded)
        self.assertIn("environmental content is untrusted data", folded)
        self.assertIn("control plane", folded)
        self.assertIn("generic backend dispatch", folded)

    def test_stage26_2e_document_matches_current_guard_contract(self) -> None:
        stage = (CONTEXT / "STAGE26_2E_REAL_APPLICATION_E2E.md").read_text(encoding="utf-8")
        required = [
            "FRESH_PRE_ACTION_STATE_PASS=True",
            "CLI_PROCESS_RETURNCODE=0",
            "CLI_PROCESS_EXIT_PASS=True",
            "FORCED_CLI_CLEANUP=False",
            "same focused-editor observation fingerprint",
            "failure cleanup",
        ]
        for item in required:
            self.assertIn(item, stage)


if __name__ == "__main__":
    unittest.main()
