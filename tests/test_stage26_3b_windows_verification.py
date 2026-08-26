from __future__ import annotations

import hashlib
import unittest

from runtime.control_plane.verification import VerificationStatus, verify_expected_effect
from runtime.control_plane.windows_observation import (
    WINDOWS_DESKTOP_CAPABILITY,
    WindowsDesktopObservationStream,
    normalize_windows_desktop_observation,
)
from runtime.control_plane.windows_transition import (
    build_windows_desktop_effect,
    verify_windows_desktop_transition,
)


class WindowsSharedKernelVerificationTests(unittest.TestCase):
    def raw(self, **overrides):
        raw = {
            "schema_version": 1,
            "session_id": "windows-session:1",
            "application_identity": "sha256:" + ("a" * 64),
            "executable_name": "fixture.exe",
            "process_id": 4242,
            "process_generation": "123456789",
            "window_handle": 98765,
            "window_instance": "b" * 64,
            "window_title": "Fixture - Before",
            "window_bounds": {
                "left": 10,
                "top": 20,
                "right": 610,
                "bottom": 420,
                "width": 600,
                "height": 400,
            },
            "coordinate_space": "screen_physical_px",
            "focused_control": "d" * 64,
            "controls": [
                {
                    "role": "textbox",
                    "name": "Editor",
                    "automation_id": "editor",
                    "bounds": {
                        "left": 30,
                        "top": 50,
                        "right": 500,
                        "bottom": 300,
                        "width": 470,
                        "height": 250,
                    },
                    "enabled": True,
                    "visible": True,
                    "focused": True,
                    "observation_fingerprint": "d" * 64,
                }
            ],
            "visible_text": "Editor\nSave",
            "observed_capabilities": ["win32_identity", "uia_structure", "uia_focus_state"],
            "screenshot_digest": None,
            "frame_digest": "c" * 64,
            "observed_at": "2026-08-26T12:00:00+00:00",
            "observation_source": ["win32_identity", "uia_structure"],
            "provenance": [],
            "freshness_evidence": {
                "process_generation": "123456789",
                "window_handle": 98765,
                "window_instance": "b" * 64,
                "structural_control_count": 1,
                "screenshot_digest": None,
                "focus_evidence": {"selected_source": "has_keyboard_focus"},
            },
        }
        raw.update(overrides)
        return raw

    def test_normalizes_desktopstate_into_shared_observation(self):
        stream = WindowsDesktopObservationStream(subject="fixture", stream_id="win-stream")
        first = stream.observe(self.raw())
        second = stream.observe(self.raw(window_title="Fixture - After"))

        self.assertEqual(first.ref.capability, WINDOWS_DESKTOP_CAPABILITY)
        self.assertEqual(first.ref.subject, "fixture")
        self.assertEqual(first.ref.stream_id, second.ref.stream_id)
        self.assertEqual(first.ref.sequence + 1, second.ref.sequence)
        self.assertEqual(first.state["identity"]["process_generation"], "123456789")
        self.assertEqual(first.state["window"]["title"], "Fixture - Before")
        self.assertEqual(first.state["controls"]["d" * 64]["automation_id"], "editor")

    def test_visible_text_is_reduced_to_digest(self):
        snapshot = WindowsDesktopObservationStream(subject="fixture").observe(self.raw())
        expected = hashlib.sha256(b"Editor\nSave").hexdigest()
        self.assertEqual(snapshot.state["evidence"]["visible_text_sha256"], expected)
        self.assertNotIn("visible_text", snapshot.state)

    def test_same_process_window_identity_and_expected_title_pass(self):
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=self.raw(
                window_title="Fixture - Saved",
                frame_digest="e" * 64,
                observed_at="2026-08-26T12:00:01+00:00",
            ),
            expected={"window": {"title": "Fixture - Saved"}},
            subject="fixture",
            stream_id="win-stream",
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["verification"]["reason"], "expected_effect_verified")

    def test_process_generation_drift_fails_even_when_final_title_matches(self):
        after = self.raw(
            window_title="Fixture - Saved",
            process_generation="999999999",
            observed_at="2026-08-26T12:00:01+00:00",
        )
        after["freshness_evidence"] = {
            **after["freshness_evidence"],
            "process_generation": "999999999",
        }
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=after,
            expected={"window": {"title": "Fixture - Saved"}},
        )
        self.assertEqual(result["status"], "fail")
        paths = [tuple(item["path"]) for item in result["verification"]["predicate_results"] if item["status"] == "fail"]
        self.assertIn(("identity", "process_generation"), paths)

    def test_hwnd_and_window_instance_drift_fail(self):
        after = self.raw(
            window_title="Fixture - Saved",
            window_handle=44444,
            window_instance="f" * 64,
            observed_at="2026-08-26T12:00:01+00:00",
        )
        after["freshness_evidence"] = {
            **after["freshness_evidence"],
            "window_handle": 44444,
            "window_instance": "f" * 64,
        }
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=after,
            expected={"window": {"title": "Fixture - Saved"}},
        )
        self.assertEqual(result["status"], "fail")

    def test_application_identity_drift_fails(self):
        after = self.raw(
            window_title="Fixture - Saved",
            application_identity="sha256:" + ("9" * 64),
            observed_at="2026-08-26T12:00:01+00:00",
        )
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=after,
            expected={"window": {"title": "Fixture - Saved"}},
        )
        self.assertEqual(result["status"], "fail")

    def test_wrong_expected_final_state_fails(self):
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=self.raw(
                window_title="Fixture - Saved",
                observed_at="2026-08-26T12:00:01+00:00",
            ),
            expected={"window": {"title": "Wrong title"}},
        )
        self.assertEqual(result["status"], "fail")

    def test_duplicate_observation_fingerprint_makes_verification_unknown(self):
        duplicate = dict(self.raw()["controls"][0])
        after = self.raw(
            window_title="Fixture - Saved",
            controls=[self.raw()["controls"][0], duplicate],
            observed_at="2026-08-26T12:00:01+00:00",
        )
        after["freshness_evidence"] = {
            **after["freshness_evidence"],
            "structural_control_count": 2,
        }
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=after,
            expected={"window": {"title": "Fixture - Saved"}},
        )
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["verification"]["reason"], "ambiguous_observation")

    def test_stale_snapshot_is_unknown(self):
        stream = WindowsDesktopObservationStream(subject="fixture", stream_id="win-stream")
        before = stream.observe(self.raw())
        effect, _ = build_windows_desktop_effect(
            before=before,
            expected={"window": {"title": "Fixture - Before"}},
        )
        result = verify_expected_effect(effect, before)
        self.assertEqual(result.status, VerificationStatus.UNKNOWN)
        self.assertEqual(result.reason, "stale_observation")

    def test_freshness_contradiction_is_rejected(self):
        raw = self.raw()
        raw["freshness_evidence"] = {
            **raw["freshness_evidence"],
            "process_generation": "different",
        }
        with self.assertRaises(ValueError):
            normalize_windows_desktop_observation(raw)

    def test_empty_or_unreviewed_expected_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            verify_windows_desktop_transition(
                before_raw=self.raw(),
                after_raw=self.raw(),
                expected={},
            )
        with self.assertRaises(ValueError):
            verify_windows_desktop_transition(
                before_raw=self.raw(),
                after_raw=self.raw(),
                expected={"run_command": "calc.exe"},
            )


if __name__ == "__main__":
    unittest.main()
