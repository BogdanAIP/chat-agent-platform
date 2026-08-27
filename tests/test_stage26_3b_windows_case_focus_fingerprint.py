from __future__ import annotations

import hashlib
import json
import unittest

from runtime.control_plane.windows_case_update import _control_fingerprint


class WindowsCaseFocusFingerprintTests(unittest.TestCase):
    def test_expected_focus_fingerprint_matches_desktop_state_contract(self) -> None:
        control = {
            "role": "textbox",
            "name": "New case note",
            "automation_id": "case-note",
            "bounds": {"left": 10, "top": 20, "right": 210, "bottom": 50, "width": 200, "height": 30},
            "enabled": True,
            "visible": True,
            "focused": False,
            "observation_fingerprint": "before-focus-placeholder",
        }
        raw = {"controls": [control]}
        expected_payload = {
            "role": "textbox",
            "name": "New case note",
            "automation_id": "case-note",
            "bounds": control["bounds"],
            "enabled": True,
            "visible": True,
            "focused": True,
        }
        expected = hashlib.sha256(
            json.dumps(
                expected_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        self.assertEqual(
            _control_fingerprint(
                raw,
                role="textbox",
                name="New case note",
                focused=True,
            ),
            expected,
        )
        self.assertEqual(
            _control_fingerprint(raw, role="textbox", name="New case note"),
            "before-focus-placeholder",
        )
        self.assertNotEqual(expected, "before-focus-placeholder")


if __name__ == "__main__":
    unittest.main()
