from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from runtime.windows.observation import (
    MAX_OBSERVED_CONTROLS,
    Rect,
    build_desktop_state,
)


FIXED_TIME = "2026-08-19T18:00:00+00:00"


def _control(
    *,
    role: str = "button",
    name: str = "Save",
    automation_id: str = "saveButton",
    left: int = 10,
    top: int = 20,
    right: int = 110,
    bottom: int = 60,
    enabled: bool = True,
    visible: bool = True,
    focused: bool = False,
):
    return {
        "role": role,
        "name": name,
        "automation_id": automation_id,
        "bounds": {
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
        },
        "enabled": enabled,
        "visible": visible,
        "focused": focused,
    }


def _state(*, controls=None, screenshot_png=None, screenshot_source=None, generation="100"):
    return build_desktop_state(
        session_id="windows-session:1",
        application_identity="sha256:application",
        executable_name="fixture.exe",
        process_id=1234,
        process_generation=generation,
        window_handle=5678,
        window_title="Fixture Window",
        window_bounds=Rect(0, 0, 800, 600),
        controls=controls if controls is not None else [_control()],
        screenshot_png=screenshot_png,
        screenshot_source=screenshot_source,
        observed_at=FIXED_TIME,
    )


class DesktopObservationContractTests(unittest.TestCase):
    def test_state_is_deterministic_for_identical_evidence(self):
        first = _state(screenshot_png=b"png-evidence", screenshot_source="test_exact_window")
        second = _state(screenshot_png=b"png-evidence", screenshot_source="test_exact_window")

        self.assertEqual(first.frame_digest, second.frame_digest)
        self.assertEqual(first.window_instance, second.window_instance)
        self.assertEqual(first.to_mapping(), second.to_mapping())
        self.assertEqual(
            first.screenshot_digest,
            hashlib.sha256(b"png-evidence").hexdigest(),
        )
        self.assertNotIn(b"png-evidence", repr(first.to_mapping()).encode("utf-8"))

    def test_process_generation_changes_window_instance_and_frame(self):
        first = _state(generation="100")
        second = _state(generation="101")

        self.assertNotEqual(first.window_instance, second.window_instance)
        self.assertNotEqual(first.frame_digest, second.frame_digest)

    def test_control_observation_fingerprint_tracks_current_state(self):
        enabled = _state(controls=[_control(enabled=True)]).controls[0]
        disabled = _state(controls=[_control(enabled=False)]).controls[0]
        moved = _state(controls=[_control(left=11)]).controls[0]

        self.assertNotEqual(enabled.observation_fingerprint, disabled.observation_fingerprint)
        self.assertNotEqual(enabled.observation_fingerprint, moved.observation_fingerprint)

    def test_focused_control_is_bound_to_observed_control_fingerprint(self):
        state = _state(
            controls=[
                _control(name="Save", focused=False),
                _control(
                    role="textbox",
                    name="Name",
                    automation_id="nameBox",
                    focused=True,
                ),
            ]
        )

        self.assertEqual(state.focused_control, state.controls[1].observation_fingerprint)

    def test_visible_text_excludes_hidden_controls_and_deduplicates(self):
        state = _state(
            controls=[
                _control(name="Visible"),
                _control(name="Visible", automation_id="duplicate"),
                _control(name="Hidden", automation_id="hidden", visible=False),
                _control(name="", automation_id="empty"),
            ]
        )

        self.assertEqual(state.visible_text, "Visible")

    def test_observed_capabilities_are_evidence_sources_not_actions(self):
        state = _state(screenshot_png=b"png", screenshot_source="test_exact_window")

        self.assertEqual(
            state.observed_capabilities,
            (
                "win32_identity",
                "uia_structure",
                "uia_focus_state",
                "screenshot_digest",
            ),
        )
        self.assertNotIn("click", state.observed_capabilities)
        self.assertNotIn("type", state.observed_capabilities)

    def test_screenshot_is_optional_but_source_requires_bytes(self):
        without = _state()
        self.assertIsNone(without.screenshot_digest)
        self.assertNotIn("screenshot_digest", without.observation_source)

        with self.assertRaisesRegex(ValueError, "screenshot_source requires"):
            _state(screenshot_source="invalid")

    def test_control_scan_is_bounded(self):
        controls = [_control(name=f"Control {index}", automation_id=str(index)) for index in range(MAX_OBSERVED_CONTROLS + 1)]
        with self.assertRaisesRegex(ValueError, "bounded scan contract"):
            _state(controls=controls)

    def test_mapping_contains_required_desktop_state_identity_and_freshness(self):
        state = _state()
        mapping = state.to_mapping()

        required = {
            "session_id",
            "application_identity",
            "process_id",
            "process_generation",
            "window_handle",
            "window_instance",
            "window_title",
            "window_bounds",
            "coordinate_space",
            "focused_control",
            "controls",
            "visible_text",
            "observed_capabilities",
            "screenshot_digest",
            "frame_digest",
            "observed_at",
            "observation_source",
            "provenance",
            "freshness_evidence",
        }
        self.assertTrue(required.issubset(mapping))
        self.assertEqual(mapping["coordinate_space"], "screen_physical_px")


class DesktopObservationSourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[1]
        cls.source = (cls.repo / "runtime" / "windows" / "observation.py").read_text(
            encoding="utf-8"
        )

    def test_observer_reuses_pid_window_binding_and_never_walks_desktop_root(self):
        self.assertIn("resolver._find_target_windows(auto, window_name)", self.source)
        self.assertNotIn("GetRootControl", self.source)
        self.assertIn("MAX_OBSERVED_CONTROLS = MAX_WINDOW_CONTROL_SCAN", self.source)

    def test_observer_has_no_action_or_generic_exec_channel(self):
        forbidden = (
            "bounded_input(",
            "send_unicode_text(",
            "subprocess.",
            "os.system(",
            "shell=True",
            "eval(",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source)
        self.assertNotIn("def click", self.source)
        self.assertNotIn("def type", self.source)

    def test_observation_fingerprint_is_explicitly_non_authorizing(self):
        self.assertIn("must not be confused with executor authorization fingerprints", self.source)
        self.assertIn("without authorizing an action", self.source)


if __name__ == "__main__":
    unittest.main()
