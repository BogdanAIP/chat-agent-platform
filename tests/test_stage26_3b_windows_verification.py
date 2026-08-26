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
from runtime.windows.observation import Rect, build_desktop_state


class WindowsSharedKernelVerificationTests(unittest.TestCase):
    def raw(
        self,
        *,
        window_title: str = "Fixture - Before",
        process_generation: str = "123456789",
        window_handle: int = 98765,
        application_identity: str | None = None,
        controls=None,
        observed_at: str = "2026-08-26T12:00:00+00:00",
    ):
        if controls is None:
            controls = [
                {
                    "role": "textbox",
                    "name": "Editor",
                    "automation_id": "editor",
                    "bounds": {
                        "left": 30,
                        "top": 50,
                        "right": 500,
                        "bottom": 300,
                    },
                    "enabled": True,
                    "visible": True,
                    "focused": True,
                }
            ]
        state = build_desktop_state(
            session_id="windows-session:1",
            application_identity=application_identity or ("sha256:" + ("a" * 64)),
            executable_name="fixture.exe",
            process_id=4242,
            process_generation=process_generation,
            window_handle=window_handle,
            window_title=window_title,
            window_bounds=Rect(left=10, top=20, right=610, bottom=420),
            controls=controls,
            observed_at=observed_at,
            focus_evidence={"selected_source": "has_keyboard_focus"},
        )
        return state.to_mapping()

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
        control_id = next(iter(first.state["controls"]))
        self.assertEqual(first.state["controls"][control_id]["automation_id"], "editor")

    def test_visible_text_is_reduced_to_digest(self):
        raw = self.raw()
        snapshot = WindowsDesktopObservationStream(subject="fixture").observe(raw)
        expected = hashlib.sha256(raw["visible_text"].encode("utf-8")).hexdigest()
        self.assertEqual(snapshot.state["evidence"]["visible_text_sha256"], expected)
        self.assertNotIn("visible_text", snapshot.state)

    def test_same_process_and_hwnd_can_verify_legitimate_title_change(self):
        before_raw = self.raw()
        after_raw = self.raw(
            window_title="Fixture - Saved",
            observed_at="2026-08-26T12:00:01+00:00",
        )
        self.assertNotEqual(before_raw["window_instance"], after_raw["window_instance"])

        result = verify_windows_desktop_transition(
            before_raw=before_raw,
            after_raw=after_raw,
            expected={"window": {"title": "Fixture - Saved"}},
            subject="fixture",
            stream_id="win-stream",
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["verification"]["reason"], "expected_effect_verified")

    def test_process_generation_drift_fails_even_when_final_title_matches(self):
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=self.raw(
                window_title="Fixture - Saved",
                process_generation="999999999",
                observed_at="2026-08-26T12:00:01+00:00",
            ),
            expected={"window": {"title": "Fixture - Saved"}},
        )
        self.assertEqual(result["status"], "fail")
        paths = [
            tuple(item["path"])
            for item in result["verification"]["predicate_results"]
            if item["status"] == "fail"
        ]
        self.assertIn(("identity", "process_generation"), paths)

    def test_hwnd_drift_fails(self):
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=self.raw(
                window_title="Fixture - Saved",
                window_handle=44444,
                observed_at="2026-08-26T12:00:01+00:00",
            ),
            expected={"window": {"title": "Fixture - Saved"}},
        )
        self.assertEqual(result["status"], "fail")

    def test_application_identity_drift_fails(self):
        result = verify_windows_desktop_transition(
            before_raw=self.raw(),
            after_raw=self.raw(
                window_title="Fixture - Saved",
                application_identity="sha256:" + ("9" * 64),
                observed_at="2026-08-26T12:00:01+00:00",
            ),
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
        duplicate_control = {
            "role": "textbox",
            "name": "Editor",
            "automation_id": "editor",
            "bounds": {"left": 30, "top": 50, "right": 500, "bottom": 300},
            "enabled": True,
            "visible": True,
            "focused": True,
        }
        after = self.raw(
            window_title="Fixture - Saved",
            controls=[duplicate_control, dict(duplicate_control)],
            observed_at="2026-08-26T12:00:01+00:00",
        )
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

    def test_window_instance_and_frame_digest_are_recomputed(self):
        raw = self.raw()
        bad_window_instance = dict(raw)
        bad_window_instance["window_instance"] = "f" * 64
        bad_window_instance["freshness_evidence"] = {
            **raw["freshness_evidence"],
            "window_instance": "f" * 64,
        }
        with self.assertRaises(ValueError):
            normalize_windows_desktop_observation(bad_window_instance)

        bad_frame = dict(raw)
        bad_frame["frame_digest"] = "e" * 64
        with self.assertRaises(ValueError):
            normalize_windows_desktop_observation(bad_frame)

    def test_control_fingerprint_is_recomputed(self):
        raw = self.raw()
        raw["controls"][0]["observation_fingerprint"] = "e" * 64
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
