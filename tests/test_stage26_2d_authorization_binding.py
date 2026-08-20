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


def _frame() -> ObservedDesktopFrame:
    png = _png()
    state = build_desktop_state(
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
                "automation_id": "visualButton",
                "bounds": {"left": 140, "top": 110, "right": 260, "bottom": 170},
                "enabled": True,
                "visible": True,
                "focused": False,
            }
        ],
        screenshot_png=png,
        screenshot_source="unit_exact_window",
        observed_at=datetime.now(timezone.utc).isoformat(),
    )
    return ObservedDesktopFrame(state=state, screenshot_png=png)


def _proposal(frame: ObservedDesktopFrame) -> GrounderProposal:
    state = frame.state
    return GrounderProposal(
        schema_version=1,
        target_text="Visual target",
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


def _outcome(proposal: GrounderProposal) -> DesktopGroundingResult:
    return DesktopGroundingResult(
        status="proposal",
        reason="grounder-accepted-proposal-only",
        proposal=proposal,
        diagnostics=GrounderDiagnostics(
            decision="accepted",
            method="unit-grounder",
            inventory_detection_count=1,
            inventory_match_count=1,
            inventory_labels=("Visual target",),
            pass1_detection_count=1,
            pass2_detection_count=1,
            pass2_labels=("Visual target",),
            consistency_iou=0.8,
            latency_seconds=0.01,
        ),
    )


class _Observe:
    def __init__(self, initial: ObservedDesktopFrame, visual: ObservedDesktopFrame):
        self.frames = [ObservedDesktopFrame(state=replace(initial.state, screenshot_digest=None), screenshot_png=None), visual]

    def __call__(self, _need_screenshot: bool) -> ObservedDesktopFrame:
        if not self.frames:
            raise AssertionError("unexpected observation after authorization refusal")
        return self.frames.pop(0)


class AuthorizationBindingTests(unittest.TestCase):
    def _request(self) -> DesktopClickRequest:
        return DesktopClickRequest(
            window_name="Fixture",
            target_text="Visual target",
            role="button",
            vision_fallback=VISION_FALLBACK_ZERO_EXACT,
        )

    def _assert_refused(self, mutate):
        visual = _frame()
        initial = visual
        proposal = mutate(_proposal(visual))
        executor_calls = 0

        def execute_coordinate(*_args):
            nonlocal executor_calls
            executor_calls += 1
            raise AssertionError("mismatched proposal must not reach executor")

        result = route_desktop_click(
            request=self._request(),
            observe=_Observe(initial, visual),
            ground=lambda *_args: _outcome(proposal),
            execute_structural=lambda *_args: (_ for _ in ()).throw(AssertionError("no structural action")),
            execute_coordinate=execute_coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "vision-proposal-evidence-mismatch")
        self.assertEqual(executor_calls, 0)

    def test_wrong_proposal_target_is_not_authorized(self):
        self._assert_refused(lambda proposal: replace(proposal, target_text="Different target"))

    def test_missing_uia_evidence_digest_is_not_authorized(self):
        self._assert_refused(lambda proposal: replace(proposal, uia_evidence_digest=None))

    def test_inconsistent_window_to_screen_translation_is_not_authorized(self):
        self._assert_refused(
            lambda proposal: replace(proposal, screen_point=GrounderPoint(181.0, 130.0))
        )

    def test_inconsistent_region_translation_is_not_authorized(self):
        self._assert_refused(
            lambda proposal: replace(
                proposal,
                screen_region=GrounderRegion(141.0, 110.0, 261.0, 170.0),
            )
        )

    def test_noncanonical_confidence_is_not_authorized(self):
        self._assert_refused(lambda proposal: replace(proposal, confidence=0.99))


if __name__ == "__main__":
    unittest.main()
