from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "project-context" / "AUTOMATIC_REVIEWER_RESEARCH.md"


class AutomaticReviewerBrowserClaimContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.research = RESEARCH.read_text(encoding="utf-8")
        self.folded = self.research.casefold()

    def test_send_claim_has_a_selected_atomic_cross_tab_owner(self) -> None:
        for phrase in (
            "Browser-side cross-tab Send ownership",
            "MV3 extension service worker",
            "extension-origin IndexedDB",
            "readwrite transaction",
            "review_send_claims",
            "add primary-key record review_run_id",
            "claim_status=granted",
            "only the caller whose add transaction committed",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

    def test_content_scripts_cannot_self_authorize_send(self) -> None:
        self.assertIn("A content script never self-authorizes Send", self.research)
        self.assertIn("Never treat `chrome.storage.local` `get()` / `set()` as an atomic Send-claim primitive", self.research)
        self.assertIn("chrome.storage.local", self.research)
        self.assertIn("it is not Send ownership", self.research)

    def test_same_run_two_tab_race_has_zero_extra_send_budget(self) -> None:
        for phrase in (
            "two tabs request same run claim concurrently",
            "overlapping IndexedDB readwrite transactions serialize",
            "exactly one `add(review_run_id)` can commit",
            "only that caller gets grant",
            "0 extra Sends",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

    def test_claim_crash_and_ambiguous_response_fail_closed(self) -> None:
        for phrase in (
            "service worker / claim transaction fails or aborts before commit",
            "claim commits but response is lost or winning tab dies before click",
            "durable claim remains",
            "manual fallback",
            "does not automatically retry an ambiguous claim response",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

    def test_claim_schema_is_preinitialized_and_not_lazily_recreated(self) -> None:
        for phrase in (
            "must not lazily create or upgrade the database schema",
            "Missing marker",
            "unexpected version",
            "onupgradeneeded",
            "fail closed with **no automatic Send**",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)

    def test_physical_gate_includes_real_concurrent_same_run_tabs(self) -> None:
        self.assertIn(
            "two real same-run tabs released concurrently prove exactly one service-worker IndexedDB claim grant and exactly one Send click",
            self.research,
        )

    def test_browser_claim_does_not_expand_into_general_runtime(self) -> None:
        for phrase in (
            "not a general project database or scheduler/event bus",
            "general browser storage/database dispatcher",
            "broader browser database/runtime authority",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.research)


if __name__ == "__main__":
    unittest.main()
