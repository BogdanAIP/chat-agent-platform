from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from runtime.control_plane.browser_observation import BrowserObservationStream
from runtime.control_plane.browser_transition import verify_navigation_transition


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "runtime" / "control_plane" / "browser_transition_cli.py"


class BrowserNavigationVerificationTests(unittest.TestCase):
    def raw(self, *, url: str, text: str, title: str = "Example", ambiguous: bool = False):
        return {
            "url": url,
            "title": title,
            "document_id": None,
            "snapshot_text": text,
            "controls": [],
            "settled": True,
            "complete": True,
            "ambiguous": ambiguous,
        }

    def test_about_blank_is_admitted_only_as_observed_pre_navigation_state(self):
        stream = BrowserObservationStream(subject="page")
        observed = stream.observe(self.raw(url="about:blank", text="", title=""))
        self.assertEqual(observed.state["url"], "about:blank")
        self.assertEqual(observed.state["origin"], "about:")

        with self.assertRaises(ValueError):
            verify_navigation_transition(
                before_raw=self.raw(url="about:blank", text="", title=""),
                after_raw=self.raw(url="about:blank", text="", title=""),
                expected_url="about:blank",
            )

    def test_exact_final_url_and_document_state_pass(self):
        result = verify_navigation_transition(
            before_raw=self.raw(url="about:blank", text="", title=""),
            after_raw=self.raw(url="https://example.com/", text="- heading Example"),
            expected_url="https://EXAMPLE.com:443",
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["verification"]["status"], "pass")
        self.assertEqual(result["expected_url"], "https://example.com/")
        self.assertEqual(result["before"]["stream_id"], result["after"]["stream_id"])
        self.assertLess(result["before"]["sequence"], result["after"]["sequence"])

    def test_redirect_or_wrong_final_url_is_fail_closed(self):
        result = verify_navigation_transition(
            before_raw=self.raw(url="https://example.com/start", text="start"),
            after_raw=self.raw(url="https://example.com/final", text="final"),
            expected_url="https://example.com/redirect",
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["verification"]["reason"], "expected_effect_failed")

    def test_ambiguous_final_observation_is_unknown(self):
        result = verify_navigation_transition(
            before_raw=self.raw(url="about:blank", text="", title=""),
            after_raw=self.raw(
                url="https://example.com/",
                text="ambiguous",
                ambiguous=True,
            ),
            expected_url="https://example.com/",
        )
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["verification"]["reason"], "ambiguous_observation")

    def test_page_state_digest_changes_with_observed_document(self):
        stream = BrowserObservationStream(subject="page", stream_id="stream")
        first = stream.observe(self.raw(url="https://example.com/", text="first"))
        second = stream.observe(self.raw(url="https://example.com/", text="second"))
        self.assertNotEqual(first.state["page_state_sha256"], second.state["page_state_sha256"])

    def run_cli(self, request):
        completed = subprocess.run(
            [sys.executable, str(CLI)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
        return completed.returncode, json.loads(completed.stdout)

    def test_cli_is_closed_to_one_navigation_verification_operation(self):
        request = {
            "operation": "verify_navigation",
            "before": self.raw(url="about:blank", text="", title=""),
            "after": self.raw(url="https://example.com/", text="done"),
            "expected_url": "https://example.com/",
        }
        code, result = self.run_cli(request)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "pass")

        code, rejected = self.run_cli({**request, "execute_js": "alert(1)"})
        self.assertEqual(code, 2)
        self.assertEqual(rejected["status"], "error")
        self.assertEqual(rejected["reason"], "unsupported_request_fields")

        code, rejected = self.run_cli({**request, "operation": "run_anything"})
        self.assertEqual(code, 2)
        self.assertEqual(rejected["reason"], "unsupported_operation")


if __name__ == "__main__":
    unittest.main()
