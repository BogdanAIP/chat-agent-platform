from __future__ import annotations

import hashlib
import unittest

from runtime.control_plane.browser_observation import (
    BROWSER_PAGE_CAPABILITY,
    MAX_BROWSER_CONTROLS,
    BrowserObservationStream,
    canonicalize_browser_url,
    normalize_browser_observation,
)
from runtime.control_plane.verification import (
    ExpectedEffect,
    StatePredicate,
    VerificationStatus,
    verify_expected_effect,
)


class BrowserObservationStreamTests(unittest.TestCase):
    def raw(self, **overrides):
        value = {
            "url": "https://example.com/start",
            "title": "Example",
            "document_id": "doc-1",
            "snapshot_text": "- heading Example\n- button Save",
            "controls": [
                {
                    "control_id": "save",
                    "role": "button",
                    "name": "Save",
                    "enabled": True,
                    "visible": True,
                }
            ],
            "settled": True,
            "complete": True,
            "ambiguous": False,
        }
        value.update(overrides)
        return value

    def test_canonicalizes_url_and_origin(self):
        canonical, origin = canonicalize_browser_url("HTTPS://Example.COM:443")
        self.assertEqual(canonical, "https://example.com/")
        self.assertEqual(origin, "https://example.com")

    def test_rejects_non_http_and_credentials(self):
        with self.assertRaises(ValueError):
            canonicalize_browser_url("file:///tmp/test")
        with self.assertRaises(ValueError):
            canonicalize_browser_url("https://user:pass@example.com/")

    def test_emits_monotonic_same_stream_observations(self):
        stream = BrowserObservationStream(subject="page-1", stream_id="stream-1")
        first = stream.observe(self.raw())
        second = stream.observe(self.raw(url="https://example.com/next"))

        self.assertEqual(first.ref.capability, BROWSER_PAGE_CAPABILITY)
        self.assertEqual(first.ref.subject, "page-1")
        self.assertEqual(first.ref.stream_id, second.ref.stream_id)
        self.assertEqual(first.ref.sequence + 1, second.ref.sequence)
        self.assertNotEqual(first.ref.fingerprint, second.ref.fingerprint)

    def test_snapshot_text_is_reduced_to_digest(self):
        raw = self.raw(snapshot_text="private-ish page text")
        snapshot = BrowserObservationStream(subject="page-1").observe(raw)
        expected = hashlib.sha256(b"private-ish page text").hexdigest()

        self.assertEqual(snapshot.state["document"]["snapshot_sha256"], expected)
        self.assertNotIn("snapshot_text", snapshot.state)

    def test_control_state_is_verifier_addressable(self):
        stream = BrowserObservationStream(subject="page-1", stream_id="stream-1")
        before = stream.observe(self.raw())
        after = stream.observe(self.raw(controls=[{
            "control_id": "save",
            "role": "button",
            "name": "Save",
            "enabled": False,
            "visible": True,
        }]))
        effect = ExpectedEffect(
            effect_id="save-disabled",
            before=before.ref,
            predicates=(StatePredicate.equals("controls", "save", "enabled", expected=False),),
        )

        result = verify_expected_effect(effect, after)
        self.assertEqual(result.status, VerificationStatus.PASS)

    def test_url_expected_effect_pass_and_mismatch_fail(self):
        stream = BrowserObservationStream(subject="page-1", stream_id="stream-1")
        before = stream.observe(self.raw())
        after = stream.observe(self.raw(url="https://example.com/result"))

        passed = verify_expected_effect(
            ExpectedEffect(
                effect_id="navigate-result",
                before=before.ref,
                predicates=(StatePredicate.equals("url", expected="https://example.com/result"),),
            ),
            after,
        )
        failed = verify_expected_effect(
            ExpectedEffect(
                effect_id="navigate-wrong",
                before=before.ref,
                predicates=(StatePredicate.equals("url", expected="https://example.com/other"),),
            ),
            after,
        )

        self.assertEqual(passed.status, VerificationStatus.PASS)
        self.assertEqual(failed.status, VerificationStatus.FAIL)

    def test_duplicate_control_identity_marks_observation_ambiguous(self):
        controls = [
            {"control_id": "same", "role": "button", "name": "A"},
            {"control_id": "same", "role": "button", "name": "B"},
        ]
        stream = BrowserObservationStream(subject="page-1", stream_id="stream-1")
        before = stream.observe(self.raw())
        after = stream.observe(self.raw(controls=controls))
        result = verify_expected_effect(
            ExpectedEffect(
                effect_id="ambiguous-control",
                before=before.ref,
                predicates=(StatePredicate.present("controls", "same"),),
            ),
            after,
        )

        self.assertTrue(after.ambiguous)
        self.assertEqual(list(after.state["control_collisions"]), ["same"])
        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertEqual(result.reason, "ambiguous_observation")

    def test_missing_control_is_fail_when_complete_and_unknown_when_incomplete(self):
        stream = BrowserObservationStream(subject="page-1", stream_id="stream-1")
        before = stream.observe(self.raw())
        complete_after = stream.observe(self.raw(controls=[]))
        incomplete_after = stream.observe(self.raw(
            controls=[], snapshot_text=None, settled=None, complete=False
        ))
        effect = ExpectedEffect(
            effect_id="save-present",
            before=before.ref,
            predicates=(StatePredicate.present("controls", "save"),),
        )

        complete_result = verify_expected_effect(effect, complete_after)
        effect_from_complete = ExpectedEffect(
            effect_id="save-present-incomplete",
            before=complete_after.ref,
            predicates=(StatePredicate.present("controls", "save"),),
        )
        incomplete_result = verify_expected_effect(effect_from_complete, incomplete_after)

        self.assertEqual(complete_result.status, VerificationStatus.FAIL)
        self.assertEqual(incomplete_result.status, VerificationStatus.UNKNOWN)

    def test_complete_observation_can_prove_control_absence(self):
        stream = BrowserObservationStream(subject="page-1", stream_id="stream-1")
        before = stream.observe(self.raw())
        after = stream.observe(self.raw(controls=[]))
        result = verify_expected_effect(
            ExpectedEffect(
                effect_id="save-gone",
                before=before.ref,
                predicates=(StatePredicate.absent("controls", "save"),),
            ),
            after,
        )
        self.assertEqual(result.status, VerificationStatus.PASS)

    def test_normalization_detaches_from_mutable_input(self):
        raw = self.raw()
        snapshot = BrowserObservationStream(subject="page-1").observe(raw)
        raw["controls"][0]["enabled"] = False
        raw["snapshot_text"] = "changed"

        self.assertTrue(snapshot.state["controls"]["save"]["enabled"])
        self.assertEqual(
            snapshot.state["document"]["snapshot_sha256"],
            hashlib.sha256(b"- heading Example\n- button Save").hexdigest(),
        )

    def test_rejects_unbounded_or_unreviewed_shapes(self):
        with self.assertRaises(ValueError):
            normalize_browser_observation({**self.raw(), "execute_js": "alert(1)"})
        with self.assertRaises(TypeError):
            normalize_browser_observation(self.raw(complete=1))
        with self.assertRaises(ValueError):
            normalize_browser_observation(self.raw(controls=[
                {"control_id": f"c-{index}", "role": "button"}
                for index in range(MAX_BROWSER_CONTROLS + 1)
            ]))
        with self.assertRaises(ValueError):
            normalize_browser_observation(self.raw(snapshot_text=None, complete=True))


if __name__ == "__main__":
    unittest.main()
