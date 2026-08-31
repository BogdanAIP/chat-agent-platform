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
            "MV3 service-worker + IndexedDB unique-key claim",
            "content script requests claim(review_run_id)",
            "one readwrite transaction",
            "objectStore.add(claim, review_run_id)",
            "committed winner receives grant",
        ):
            self.assertIn(phrase, self.research)

    def test_direct_indexeddb_evidence_matches_required_claim(self) -> None:
        for phrase in (
            "https://www.w3.org/TR/IndexedDB/#transaction-scheduling",
            "overlapping `readwrite` transactions do not run simultaneously",
            "https://www.w3.org/TR/IndexedDB/#dom-idbobjectstore-add",
            "fails with `ConstraintError` when the key already exists",
            "https://www.w3.org/TR/IndexedDB/#dom-idbtransaction-abort",
        ):
            self.assertIn(phrase, self.research)

    def test_service_worker_lifecycle_is_not_used_as_memory_ownership(self) -> None:
        for phrase in (
            "https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle",
            "workers may terminate after inactivity or unexpectedly",
            "globals are lost",
            "https://developer.chrome.com/docs/extensions/how-to/test/test-serviceworker-termination-with-puppeteer",
            "service-worker memory != durable browser ownership",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_same_run_two_tab_race_has_zero_extra_send_budget(self) -> None:
        for phrase in (
            "two tabs claim same run",
            "one IDB key may commit",
            "one grant only",
            "0 extra Sends",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_claim_crash_and_lost_response_fail_closed(self) -> None:
        for phrase in (
            "service worker terminates before claim commit",
            "claim commits, response lost/tab dies",
            "no regrant",
            "manual fallback",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_claim_schema_is_preinitialized_and_not_lazily_upgraded(self) -> None:
        for phrase in (
            "pre-initialized expected IndexedDB schema/version",
            "no lazy schema upgrade on the claim path",
            "claim-time DB create/upgrade is forbidden",
        ):
            self.assertIn(phrase.casefold(), self.folded)

    def test_physical_gate_includes_real_concurrent_same_run_tabs(self) -> None:
        self.assertIn(
            "two real same-run tabs released concurrently produce exactly one committed grant and one Send click",
            self.research,
        )

    def test_browser_claim_does_not_expand_into_general_runtime(self) -> None:
        for phrase in (
            "scheduler/event bus",
            "general browser database/storage runtime",
            "native messaging result bus",
            "automatic developer wake",
        ):
            self.assertIn(phrase, self.folded)


if __name__ == "__main__":
    unittest.main()
