from __future__ import annotations

import unittest

from runtime.control_plane.semantic_browser_authorization import (
    BROWSER_POLICY_REF,
    authorize_browser_request,
)


class SemanticBrowserAuthorizationTests(unittest.TestCase):
    def request(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "activation_ref": "a" * 32,
            "browser_policy_ref": BROWSER_POLICY_REF,
            "action_ref": "browser.navigate",
            "before_fingerprint": "b" * 64,
            "resource": {
                "url": "https://example.com/",
                "network_scope": "hostname",
            },
        }
        value.update(overrides)
        return value

    def test_exact_request_authorizes(self) -> None:
        result = authorize_browser_request(self.request())

        self.assertEqual("authorized", result["status"])
        self.assertEqual("exact_grant_match", result["reason"])
        self.assertEqual("browser.navigate", result["action_ref"])
        self.assertTrue(result["resource_scope_ref"].startswith("semantic-browser-resource:"))
        self.assertEqual("authorized", result["authorization"]["status"])

    def test_grant_changes_with_activation_action_before_and_resource(self) -> None:
        baseline = authorize_browser_request(self.request())
        variants = (
            authorize_browser_request(self.request(activation_ref="c" * 32)),
            authorize_browser_request(
                self.request(
                    action_ref="browser.click",
                    resource={
                        "target": "e1",
                        "expected": {"control": {"control_id": "e2", "value": "DONE"}},
                    },
                )
            ),
            authorize_browser_request(self.request(before_fingerprint="d" * 64)),
            authorize_browser_request(
                self.request(
                    resource={
                        "url": "https://example.com/other",
                        "network_scope": "hostname",
                    }
                )
            ),
        )

        fingerprints = {
            baseline["authorization"]["grant_fingerprint"],
            *(
                item["authorization"]["grant_fingerprint"]
                for item in variants
            ),
        }
        self.assertEqual(5, len(fingerprints))

    def test_policy_action_and_fingerprints_are_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "browser policy ref mismatch"):
            authorize_browser_request(
                self.request(browser_policy_ref="other-policy")
            )
        with self.assertRaisesRegex(ValueError, "unsupported browser action_ref"):
            authorize_browser_request(
                self.request(action_ref="browser.evaluate")
            )
        with self.assertRaisesRegex(ValueError, "activation_ref"):
            authorize_browser_request(
                self.request(activation_ref="invalid")
            )
        with self.assertRaisesRegex(ValueError, "before_fingerprint"):
            authorize_browser_request(
                self.request(before_fingerprint="B" * 64)
            )

    def test_resource_is_plain_bounded_json(self) -> None:
        with self.assertRaisesRegex(TypeError, "plain object"):
            authorize_browser_request(self.request(resource=[]))
        with self.assertRaisesRegex(ValueError, "plain JSON"):
            authorize_browser_request(
                self.request(resource={"bad": float("nan")})
            )

    def test_unknown_fields_are_rejected(self) -> None:
        request = self.request()
        request["backend"] = "playwright"

        with self.assertRaisesRegex(ValueError, "unsupported request fields"):
            authorize_browser_request(request)


if __name__ == "__main__":
    unittest.main()
