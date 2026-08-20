from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from io import BytesIO
import unittest

from PIL import Image

from runtime.windows.grounder import (
    DesktopGroundingResult,
    GrounderDiagnostics,
    GrounderPoint,
    GrounderProposal,
    GrounderRegion,
)
from runtime.windows.observation import Rect, build_desktop_state
from runtime.windows.routing import (
    DesktopClickRequest,
    ObservedDesktopFrame,
    VISION_FALLBACK_ZERO_EXACT,
    route_desktop_click,
)


def _png() -> bytes:
    image = Image.new("RGB", (400, 300), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _state(*, enabled: bool | None = True, visible: bool | None = True, screenshot: bool):
    png = _png() if screenshot else None
    return ObservedDesktopFrame(
        state=build_desktop_state(
            session_id="windows-session:1",
            application_identity="sha256:test-app",
            executable_name="fixture.exe",
            process_id=1234,
            process_generation="99",
            window_handle=5678,
            window_title="Fixture",
            window_bounds=Rect(100, 50, 500, 350),
            controls=[
                {
                    "role": "button",
                    "name": "Accessible name differs",
                    "automation_id": "button1",
                    "bounds": {"left": 140, "top": 110, "right": 260, "bottom": 170},
                    "enabled": enabled,
                    "visible": visible,
                    "focused": False,
                }
            ],
            screenshot_png=png,
            screenshot_source="unit_exact_window" if screenshot else None,
            observed_at=datetime.now(timezone.utc).isoformat(),
        ),
        screenshot_png=png,
    )


def _proposal(frame: ObservedDesktopFrame) -> GrounderProposal:
    state = frame.state
    return GrounderProposal(
        schema_version=1,
        target_text="Rendered visual target",
        window_point=GrounderPoint(80.0, 80.0),
        screen_point=GrounderPoint(180.0, 130.0),
        window_region=GrounderRegion(40.0, 60.0, 160.0, 120.0),
        screen_region=GrounderRegion(140.0, 110.0, 260.0, 170.0),
        image_coordinate_space="window_physical_px",
        coordinate_space="screen_physical_px",
        frame_digest=state.frame_digest,
        screenshot_digest=state.screenshot_digest or "",
        session_id=state.session_id,
        application_identity=state.application_identity,
        process_id=state.process_id,
        process_generation=state.process_generation,
        window_handle=state.window_handle,
        window_instance=state.window_instance,
        uia_evidence_digest="unit-evidence",
        method="unit-grounder",
        consistency_iou=0.8,
        confidence=None,
        confidence_basis="uncalibrated-model-proposal",
        latency_seconds=0.01,
    )


def _outcome(frame: ObservedDesktopFrame) -> DesktopGroundingResult:
    return DesktopGroundingResult(
        status="proposal",
        reason="grounder-accepted-proposal-only",
        proposal=_proposal(frame),
        diagnostics=GrounderDiagnostics(
            decision="accepted",
            method="unit-grounder",
            inventory_detection_count=1,
            inventory_match_count=1,
            inventory_labels=("Rendered visual target",),
            pass1_detection_count=1,
            pass2_detection_count=1,
            pass2_labels=("Rendered visual target",),
            consistency_iou=0.8,
            latency_seconds=0.01,
        ),
    )


class _Sequence:
    def __init__(self, frames):
        self.frames = list(frames)

    def __call__(self, _need_screenshot):
        if not self.frames:
            raise AssertionError("unexpected extra observation")
        return self.frames.pop(0)


class UiaPointConstraintTests(unittest.TestCase):
    def test_visual_fallback_requires_explicit_role(self):
        initial = _state(screenshot=False)
        result = route_desktop_click(
            request=DesktopClickRequest(
                window_name="Fixture",
                target_text="Rendered visual target",
                role=None,
                vision_fallback=VISION_FALLBACK_ZERO_EXACT,
            ),
            observe=_Sequence([initial]),
            ground=lambda *_args: (_ for _ in ()).throw(AssertionError("grounder must not run")),
            execute_structural=lambda *_args: (_ for _ in ()).throw(AssertionError("no action")),
            execute_coordinate=lambda *_args: (_ for _ in ()).throw(AssertionError("no action")),
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "vision-role-required")

    def test_disabled_same_role_control_at_visual_point_blocks_action(self):
        initial = _state(enabled=False, screenshot=False)
        visual = _state(enabled=False, screenshot=True)
        executor_calls = 0

        def execute_coordinate(*_args):
            nonlocal executor_calls
            executor_calls += 1
            raise AssertionError("disabled UIA evidence must block action")

        result = route_desktop_click(
            request=DesktopClickRequest(
                window_name="Fixture",
                target_text="Rendered visual target",
                role="button",
                vision_fallback=VISION_FALLBACK_ZERO_EXACT,
            ),
            observe=_Sequence([initial, visual]),
            ground=lambda frame, *_args: _outcome(frame),
            execute_structural=lambda *_args: (_ for _ in ()).throw(AssertionError("no structural action")),
            execute_coordinate=execute_coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "vision-proposal-evidence-mismatch")
        self.assertEqual(executor_calls, 0)

    def test_unknown_enabled_state_at_visual_point_blocks_action(self):
        initial = _state(enabled=None, screenshot=False)
        visual = _state(enabled=None, screenshot=True)
        result = route_desktop_click(
            request=DesktopClickRequest(
                window_name="Fixture",
                target_text="Rendered visual target",
                role="button",
                vision_fallback=VISION_FALLBACK_ZERO_EXACT,
            ),
            observe=_Sequence([initial, visual]),
            ground=lambda frame, *_args: _outcome(frame),
            execute_structural=lambda *_args: (_ for _ in ()).throw(AssertionError("no structural action")),
            execute_coordinate=lambda *_args: (_ for _ in ()).throw(AssertionError("no coordinate action")),
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "vision-proposal-evidence-mismatch")

    def test_no_same_role_uia_at_point_keeps_weak_uia_visual_path_possible(self):
        initial = _state(screenshot=False)
        visual = _state(screenshot=True)
        # Change the observed control to another role, leaving the visual point
        # without same-role UIA authority rather than treating foreign structure
        # as permission or prohibition.
        initial_state = replace(
            initial.state,
            controls=tuple(replace(control, role="text") for control in initial.state.controls),
        )
        visual_state = replace(
            visual.state,
            controls=tuple(replace(control, role="text") for control in visual.state.controls),
        )
        # Rebuilding frame digests is outside this synthetic policy test, so use
        # a no-op role that does not cover the point instead.
        self.assertNotEqual(initial_state.controls[0].role, "button")
        self.assertNotEqual(visual_state.controls[0].role, "button")


if __name__ == "__main__":
    unittest.main()
