from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from runtime.control_plane.browser_transition import verify_interaction_transition


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "runtime" / "control_plane" / "browser_transition_cli.py"


class BrowserInteractionVerificationTests(unittest.TestCase):
    def control(
        self,
        control_id: str,
        *,
        role: str = "textbox",
        name: str | None = "Input",
        value: str | None = None,
        checked: bool | None = None,
        selected: bool | None = None,
        enabled: bool | None = True,
    ) -> dict:
        return {
            "control_id": control_id,
            "role": role,
            "name": name,
            "enabled": enabled,
            "checked": checked,
            "selected": selected,
            "visible": True,
            "value": value,
        }

    def raw(
        self,
        *,
        url: str = "https://example.com/form",
        text: str = "fixture",
        controls: list[dict] | None = None,
        ambiguous: bool = False,
    ) -> dict:
        return {
            "url": url,
            "title": "Fixture",
            "document_id": None,
            "snapshot_text": text,
            "controls": controls or [],
            "settled": True,
            "complete": True,
            "ambiguous": ambiguous,
        }

    def test_textbox_value_postcondition_passes(self):
        before = self.raw(
            controls=[self.control("e12", value="old")],
            text='- textbox "Input" [ref=e12]: old',
        )
        after = self.raw(
            controls=[self.control("e12", value="hello")],
            text='- textbox "Input" [ref=e12]: hello',
        )
        result = verify_interaction_transition(
            before_raw=before,
            after_raw=after,
            expected={"control": {"control_id": "e12", "value": "hello"}},
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["expected"]["control"]["value"], "hello")
        self.assertEqual(result["before"]["stream_id"], result["after"]["stream_id"])
        self.assertLess(result["before"]["sequence"], result["after"]["sequence"])

    def test_checkbox_state_postcondition_passes(self):
        before = self.raw(
            controls=[self.control("e20", role="checkbox", name="Accept", checked=False)],
            text='- checkbox "Accept" [ref=e20] [unchecked]',
        )
        after = self.raw(
            controls=[self.control("e20", role="checkbox", name="Accept", checked=True)],
            text='- checkbox "Accept" [ref=e20] [checked]',
        )
        result = verify_interaction_transition(
            before_raw=before,
            after_raw=after,
            expected={"control": {"control_id": "e20", "checked": True}},
        )
        self.assertEqual(result["status"], "pass")

    def test_control_absence_postcondition_passes(self):
        before = self.raw(
            controls=[self.control("e30", role="button", name="Dismiss")],
            text='- button "Dismiss" [ref=e30]',
        )
        after = self.raw(controls=[], text='- heading "Done"')
        result = verify_interaction_transition(
            before_raw=before,
            after_raw=after,
            expected={"control": {"control_id": "e30", "present": False}},
        )
        self.assertEqual(result["status"], "pass")

    def test_expected_final_url_can_be_combined_with_control_state(self):
        before = self.raw(
            url="https://example.com/start",
            controls=[self.control("e40", role="link", name="Next")],
            text='- link "Next" [ref=e40]',
        )
        after = self.raw(
            url="https://example.com/done",
            controls=[self.control("e99", role="heading", name="Done", enabled=None)],
            text='- heading "Done" [ref=e99]',
        )
        result = verify_interaction_transition(
            before_raw=before,
            after_raw=after,
            expected={
                "url": "https://EXAMPLE.com:443/done",
                "control": {"control_id": "e99", "present": True},
            },
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["expected"]["url"], "https://example.com/done")

    def test_wrong_declared_result_fails_closed(self):
        before = self.raw(controls=[self.control("e12", value="old")])
        after = self.raw(controls=[self.control("e12", value="actual")])
        result = verify_interaction_transition(
            before_raw=before,
            after_raw=after,
            expected={"control": {"control_id": "e12", "value": "wanted"}},
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["verification"]["reason"], "expected_effect_failed")

    def test_ambiguous_after_state_is_unknown(self):
        before = self.raw(controls=[self.control("e12", value="old")])
        after = self.raw(
            controls=[self.control("e12", value="hello")],
            ambiguous=True,
        )
        result = verify_interaction_transition(
            before_raw=before,
            after_raw=after,
            expected={"control": {"control_id": "e12", "value": "hello"}},
        )
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["verification"]["reason"], "ambiguous_observation")

    def test_broad_or_contradictory_expectations_are_rejected(self):
        before = self.raw()
        after = self.raw()
        for expected in (
            {},
            {"control": {"control_id": "e1"}},
            {"control": {"control_id": "e1", "present": False, "value": "x"}},
            {"javascript": "document.body.innerText"},
        ):
            with self.subTest(expected=expected):
                with self.assertRaises((TypeError, ValueError)):
                    verify_interaction_transition(
                        before_raw=before,
                        after_raw=after,
                        expected=expected,
                    )

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

    def test_cli_accepts_only_bounded_interaction_verification(self):
        request = {
            "operation": "verify_interaction",
            "before": self.raw(controls=[self.control("e12", value="old")]),
            "after": self.raw(controls=[self.control("e12", value="hello")]),
            "expected": {"control": {"control_id": "e12", "value": "hello"}},
        }
        code, result = self.run_cli(request)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "pass")

        code, rejected = self.run_cli({**request, "selector": "body"})
        self.assertEqual(code, 2)
        self.assertEqual(rejected["reason"], "unsupported_request_fields")

        code, rejected = self.run_cli({**request, "expected": {"script": "alert(1)"}})
        self.assertEqual(code, 2)
        self.assertTrue(rejected["reason"].startswith("invalid_request:"))


if __name__ == "__main__":
    unittest.main()
