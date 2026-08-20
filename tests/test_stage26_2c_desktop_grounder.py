from __future__ import annotations

from dataclasses import replace
from io import BytesIO
from pathlib import Path
import unittest

from PIL import Image

from runtime.local_vision_adapter.native_bbox import NativeBBoxLoopbackClient
from runtime.windows.grounder import (
    DesktopGrounderError,
    ground_desktop_target,
    locate_desktop_target,
)
from runtime.windows.observation import Rect, build_desktop_state


def _png(width: int = 400, height: int = 300) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _state(image_bytes: bytes, *, left: int = 100, top: int = 50):
    return build_desktop_state(
        session_id="windows-session:1",
        application_identity="sha256:test-app",
        executable_name="fixture.exe",
        process_id=1234,
        process_generation="99",
        window_handle=5678,
        window_title="Fixture",
        window_bounds=Rect(left, top, left + 400, top + 300),
        controls=[
            {
                "role": "button",
                "name": "Save",
                "automation_id": "saveButton",
                "bounds": {"left": left + 40, "top": top + 60, "right": left + 120, "bottom": top + 100},
                "enabled": True,
                "visible": True,
                "focused": False,
            }
        ],
        screenshot_png=image_bytes,
        screenshot_source="unit_exact_window",
        observed_at="2026-08-19T20:00:00+00:00",
    )


class _Transport:
    def __init__(self, contents: list[str]):
        self.contents = list(contents)
        self.calls = 0

    def __call__(self, _url: str, _body: bytes, _timeout: float):
        self.calls += 1
        if not self.contents:
            raise AssertionError("unexpected model call")
        content = self.contents.pop(0)
        return {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }


def _client(contents: list[str]) -> tuple[NativeBBoxLoopbackClient, _Transport]:
    transport = _Transport(contents)
    return NativeBBoxLoopbackClient(port=3068, transport=transport), transport


class DesktopGrounderContractTests(unittest.TestCase):
    def test_proposal_binds_frame_and_translates_window_to_screen_coordinates(self):
        image = _png()
        state = _state(image)
        client, transport = _client(
            [
                '[{"label":"Save","bbox":[0.10,0.20,0.30,0.40]}]',
                '[{"label":"Save","bbox":[0.25,0.25,0.75,0.75]}]',
            ]
        )

        outcome = ground_desktop_target(
            client=client,
            window_png=image,
            target_text="Save",
            desktop_state=state,
            uia_evidence=[state.controls[0]],
        )
        proposal = outcome.proposal

        self.assertEqual(outcome.status, "proposal")
        self.assertEqual(outcome.reason, "grounder-accepted-proposal-only")
        self.assertEqual(outcome.diagnostics.decision, "accepted")
        self.assertEqual(outcome.diagnostics.inventory_labels, ("Save",))
        self.assertEqual(outcome.diagnostics.pass2_labels, ("Save",))
        self.assertIsNotNone(proposal)
        assert proposal is not None
        self.assertEqual(transport.calls, 2)
        self.assertEqual(proposal.frame_digest, state.frame_digest)
        self.assertEqual(proposal.screenshot_digest, state.screenshot_digest)
        self.assertEqual(proposal.window_instance, state.window_instance)
        self.assertEqual(proposal.session_id, state.session_id)
        self.assertEqual(proposal.application_identity, state.application_identity)
        self.assertEqual(proposal.process_generation, state.process_generation)
        self.assertEqual(proposal.image_coordinate_space, "window_physical_px")
        self.assertEqual(proposal.coordinate_space, "screen_physical_px")
        self.assertAlmostEqual(proposal.screen_point.x, proposal.window_point.x + 100.0)
        self.assertAlmostEqual(proposal.screen_point.y, proposal.window_point.y + 50.0)
        self.assertIsNotNone(proposal.uia_evidence_digest)
        self.assertIsNone(proposal.confidence)
        self.assertEqual(proposal.confidence_basis, "uncalibrated-model-proposal")

    def test_absent_inventory_preserves_reason_and_labels(self):
        image = _png()
        state = _state(image)
        client, transport = _client(
            ['[{"label":"Other","bbox":[0.10,0.20,0.30,0.40]}]']
        )

        outcome = ground_desktop_target(
            client=client,
            window_png=image,
            target_text="Save",
            desktop_state=state,
        )

        self.assertEqual(outcome.status, "abstain")
        self.assertEqual(outcome.reason, "grounder-inventory-absent")
        self.assertIsNone(outcome.proposal)
        self.assertEqual(outcome.diagnostics.decision, "inventory-absent")
        self.assertEqual(outcome.diagnostics.inventory_detection_count, 1)
        self.assertEqual(outcome.diagnostics.inventory_match_count, 0)
        self.assertEqual(outcome.diagnostics.inventory_labels, ("Other",))
        self.assertEqual(transport.calls, 1)

        compat_client, _ = _client(
            ['[{"label":"Other","bbox":[0.10,0.20,0.30,0.40]}]']
        )
        self.assertIsNone(
            locate_desktop_target(
                client=compat_client,
                window_png=image,
                target_text="Save",
                desktop_state=state,
            )
        )

    def test_ambiguous_inventory_preserves_reason(self):
        image = _png()
        state = _state(image)
        client, transport = _client(
            ['[{"label":"Save","bbox":[0.1,0.1,0.2,0.2]},{"label":"Save","bbox":[0.5,0.5,0.6,0.6]}]']
        )
        outcome = ground_desktop_target(
            client=client,
            window_png=image,
            target_text="Save",
            desktop_state=state,
        )
        self.assertEqual(outcome.status, "abstain")
        self.assertEqual(outcome.reason, "grounder-inventory-ambiguous")
        self.assertEqual(outcome.diagnostics.inventory_match_count, 2)
        self.assertEqual(outcome.diagnostics.inventory_labels, ("Save", "Save"))
        self.assertEqual(transport.calls, 1)

    def test_refinement_abstain_preserves_pass2_diagnostics(self):
        image = _png()
        state = _state(image)
        client, transport = _client(
            [
                '[{"label":"Save","bbox":[0.10,0.20,0.30,0.40]}]',
                '[]',
            ]
        )
        outcome = ground_desktop_target(
            client=client,
            window_png=image,
            target_text="Save",
            desktop_state=state,
        )
        self.assertEqual(outcome.status, "abstain")
        self.assertEqual(outcome.reason, "grounder-refinement-abstain")
        self.assertEqual(outcome.diagnostics.inventory_match_count, 1)
        self.assertEqual(outcome.diagnostics.pass2_detection_count, 0)
        self.assertEqual(outcome.diagnostics.pass2_labels, ())
        self.assertEqual(transport.calls, 2)

    def test_stale_or_wrong_frame_is_rejected_before_model_call(self):
        image = _png()
        state = replace(_state(image), screenshot_digest="0" * 64)
        client, transport = _client([])

        with self.assertRaisesRegex(DesktopGrounderError, "screenshot-digest-mismatch"):
            ground_desktop_target(
                client=client,
                window_png=image,
                target_text="Save",
                desktop_state=state,
            )
        self.assertEqual(transport.calls, 0)

    def test_window_image_dimensions_must_match_observed_window(self):
        image = _png(399, 300)
        state = build_desktop_state(
            session_id="windows-session:1",
            application_identity="sha256:test-app",
            executable_name="fixture.exe",
            process_id=1234,
            process_generation="99",
            window_handle=5678,
            window_title="Fixture",
            window_bounds=Rect(0, 0, 400, 300),
            controls=[],
            screenshot_png=image,
            screenshot_source="unit_wrong_size",
            observed_at="2026-08-19T20:00:00+00:00",
        )
        client, transport = _client([])
        with self.assertRaisesRegex(DesktopGrounderError, "dimensions"):
            ground_desktop_target(
                client=client,
                window_png=image,
                target_text="Save",
                desktop_state=state,
            )
        self.assertEqual(transport.calls, 0)

    def test_uia_evidence_is_bounded(self):
        image = _png()
        state = _state(image)
        client, transport = _client([])
        with self.assertRaisesRegex(DesktopGrounderError, "bounded limit"):
            ground_desktop_target(
                client=client,
                window_png=image,
                target_text="Save",
                desktop_state=state,
                uia_evidence=[state.controls[0]] * 33,
            )
        self.assertEqual(transport.calls, 0)


class DesktopGrounderSourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        cls.source = (repo / "runtime" / "windows" / "grounder.py").read_text(encoding="utf-8")

    def test_grounder_is_proposal_only_and_has_no_action_channel(self):
        for token in (
            "bounded_input(",
            "send_unicode_text(",
            "act_structural",
            "act_guarded",
            "WindowsBackend(",
            "subprocess.",
            "os.system(",
            "shell=True",
        ):
            self.assertNotIn(token, self.source)
        self.assertIn("The model remains non-authorizing", self.source)

    def test_desktop_coordinates_are_explicitly_not_browser_css_coordinates(self):
        self.assertIn('WINDOW_COORDINATE_SPACE = "window_physical_px"', self.source)
        self.assertIn('SCREEN_COORDINATE_SPACE = "screen_physical_px"', self.source)
        self.assertNotIn('"css_viewport"', self.source)

    def test_browser_production_policy_is_not_reused_as_windows_authorization(self):
        self.assertNotIn("production_policy", self.source)
        self.assertNotIn("authorize_native_grounding", self.source)

    def test_abstention_is_explicit_and_bounded(self):
        self.assertIn('status: str  # "proposal" | "abstain"', self.source)
        self.assertIn("MAX_UIA_EVIDENCE = 32", self.source)
        self.assertIn("inventory_labels", self.source)
        self.assertNotIn("inventory_response=", self.source)


if __name__ == "__main__":
    unittest.main()
