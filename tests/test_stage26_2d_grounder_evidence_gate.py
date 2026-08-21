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


def _frame(*, screenshot: bool) -> ObservedDesktopFrame:
    png = _png() if screenshot else None
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
        screenshot_source="unit_exact_window" if screenshot else None,
        observed_at=datetime.now(timezone.utc).isoformat(),
    )
    return ObservedDesktopFrame(state=state, screenshot_png=png)


def _proposal(frame: ObservedDesktopFrame, *, iou: float | None = 0.8) -> GrounderProposal:
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
        consistency_iou=iou,
        confidence=None,
        confidence_basis="uncalibrated-model-proposal",
        latency_seconds=0.01,
    )


def _result(
    frame: ObservedDesktopFrame,
    *,
    reason: str = "grounder-accepted-proposal-only",
    decision: str = "accepted",
    inventory_matches: int | None = 1,
    pass1_count: int | None = 1,
    pass2_count: int | None = 1,
    diagnostics_iou: float | None = 0.8,
    proposal_iou: float | None = 0.8,
) -> DesktopGroundingResult:
    return DesktopGroundingResult(
        status="proposal",
        reason=reason,
        proposal=_proposal(frame, iou=proposal_iou),
        diagnostics=GrounderDiagnostics(
            decision=decision,
            method="unit-grounder",
            inventory_detection_count=1,
            inventory_match_count=inventory_matches,
            inventory_labels=("Visual target",),
            pass1_detection_count=pass1_count,
            pass2_detection_count=pass2_count,
            pass2_labels=("Visual target",),
            consistency_iou=diagnostics_iou,
            latency_seconds=0.01,
        ),
    )


class _Sequence:
    def __init__(self, frames):
        self.frames = list(frames)

    def __call__(self, _need_screenshot):
        if not self.frames:
            raise AssertionError("unauthorized grounding must not request fresh action frame")
        return self.frames.pop(0)


class GrounderEvidenceAuthorizationTests(unittest.TestCase):
    def _request(self):
        return DesktopClickRequest(
            window_name="Fixture",
            target_text="Visual target",
            role="button",
            vision_fallback=VISION_FALLBACK_ZERO_EXACT,
        )

    def _assert_refused(self, make_result):
        initial = _frame(screenshot=False)
        visual = _frame(screenshot=True)
        coordinate_calls = 0

        def coordinate(*_args):
            nonlocal coordinate_calls
            coordinate_calls += 1
            raise AssertionError("unauthorized grounding must not reach executor")

        result = route_desktop_click(
            request=self._request(),
            observe=_Sequence([initial, visual]),
            ground=lambda frame, *_args: make_result(frame),
            execute_structural=lambda *_args: (_ for _ in ()).throw(AssertionError("no structural action")),
            execute_coordinate=coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "vision-grounder-evidence-not-authorized")
        self.assertEqual(coordinate_calls, 0)

    def test_zero_cross_pass_iou_is_not_action_authority(self):
        self._assert_refused(lambda frame: _result(frame, diagnostics_iou=0.0, proposal_iou=0.0))

    def test_missing_cross_pass_iou_is_not_action_authority(self):
        self._assert_refused(lambda frame: _result(frame, diagnostics_iou=None, proposal_iou=None))

    def test_proposal_and_diagnostics_iou_must_agree(self):
        self._assert_refused(lambda frame: _result(frame, diagnostics_iou=0.8, proposal_iou=0.7))

    def test_inventory_must_have_exactly_one_match(self):
        self._assert_refused(lambda frame: _result(frame, inventory_matches=2))

    def test_both_detection_passes_must_be_unique(self):
        self._assert_refused(lambda frame: _result(frame, pass1_count=2))
        self._assert_refused(lambda frame: _result(frame, pass2_count=2))

    def test_unknown_accepted_reason_is_not_action_authority(self):
        self._assert_refused(lambda frame: _result(frame, reason="grounder-custom-accepted"))

    def test_nonaccepted_diagnostic_decision_is_not_action_authority(self):
        self._assert_refused(lambda frame: _result(frame, decision="inconsistent-pass2"))

    def test_positive_consistent_evidence_can_continue(self):
        initial = _frame(screenshot=False)
        visual = _frame(screenshot=True)
        fresh = _frame(screenshot=True)
        calls = 0

        def coordinate(*_args):
            nonlocal calls
            calls += 1
            return {"status": "delivered", "operation": "physical_click", "outcome_verified": False}

        result = route_desktop_click(
            request=self._request(),
            observe=_Sequence([initial, visual, fresh]),
            ground=lambda frame, *_args: _result(frame),
            execute_structural=lambda *_args: (_ for _ in ()).throw(AssertionError("no structural action")),
            execute_coordinate=coordinate,
        )
        self.assertEqual(result.status, "delivered")
        self.assertEqual(result.route, "vision")
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
