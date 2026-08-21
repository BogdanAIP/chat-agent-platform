from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
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
    DesktopRoutingError,
    ObservedDesktopFrame,
    VISION_FALLBACK_DISABLED,
    VISION_FALLBACK_ZERO_EXACT,
    route_desktop_click,
)


def _png(marker: str = "base", width: int = 400, height: int = 300) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    # Deterministically alter the image without depending on fonts.
    value = sum(marker.encode("utf-8")) % 255
    image.putpixel((1, 1), (value, value, value))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _control(
    *,
    name: str,
    role: str = "button",
    automation_id: str = "",
    enabled: bool | None = True,
    visible: bool | None = True,
    left: int = 120,
    top: int = 100,
) -> dict:
    return {
        "role": role,
        "name": name,
        "automation_id": automation_id,
        "bounds": {"left": left, "top": top, "right": left + 100, "bottom": top + 40},
        "enabled": enabled,
        "visible": visible,
        "focused": False,
    }


def _state(
    controls: list[dict],
    *,
    screenshot: bytes | None = None,
    pid: int = 1234,
    process_generation: str = "99",
    hwnd: int = 5678,
    title: str = "Fixture",
):
    return build_desktop_state(
        session_id="windows-session:1",
        application_identity="sha256:test-app",
        executable_name="fixture.exe",
        process_id=pid,
        process_generation=process_generation,
        window_handle=hwnd,
        window_title=title,
        window_bounds=Rect(100, 50, 500, 350),
        controls=controls,
        screenshot_png=screenshot,
        screenshot_source="unit_exact_window" if screenshot is not None else None,
        observed_at=datetime.now(timezone.utc).isoformat(),
    )


def _frame(controls: list[dict], *, marker: str = "base", screenshot: bool = False, **kwargs):
    png = _png(marker) if screenshot else None
    return ObservedDesktopFrame(
        state=_state(controls, screenshot=png, **kwargs),
        screenshot_png=png,
    )


def _diagnostics(*, decision: str = "accepted") -> GrounderDiagnostics:
    return GrounderDiagnostics(
        decision=decision,
        method="unit-grounder",
        inventory_detection_count=1,
        inventory_match_count=1 if decision == "accepted" else 0,
        inventory_labels=("Visual target",),
        pass1_detection_count=1,
        pass2_detection_count=1 if decision == "accepted" else None,
        pass2_labels=("Visual target",) if decision == "accepted" else (),
        consistency_iou=0.8 if decision == "accepted" else None,
        latency_seconds=0.01,
    )


def _proposal(state, *, x: float = 180.0, y: float = 130.0) -> GrounderProposal:
    return GrounderProposal(
        schema_version=1,
        target_text="Visual target",
        window_point=GrounderPoint(x - state.window_bounds.left, y - state.window_bounds.top),
        screen_point=GrounderPoint(x, y),
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
        uia_evidence_digest="abc123",
        method="unit-grounder",
        consistency_iou=0.8,
        confidence=None,
        confidence_basis="uncalibrated-model-proposal",
        latency_seconds=0.01,
    )


class _ObservationSequence:
    def __init__(self, frames: list[ObservedDesktopFrame]):
        self.frames = list(frames)
        self.calls: list[bool] = []

    def __call__(self, need_screenshot: bool) -> ObservedDesktopFrame:
        self.calls.append(need_screenshot)
        if not self.frames:
            raise AssertionError("unexpected observation call")
        frame = self.frames.pop(0)
        if need_screenshot and frame.screenshot_png is None:
            raise AssertionError("test supplied non-visual frame for visual observation")
        return frame


class _Executors:
    def __init__(self):
        self.structural_calls = 0
        self.coordinate_calls = 0

    def structural(self, _request, _control, _state):
        self.structural_calls += 1
        return {
            "status": "delivered",
            "operation": "uia_invoke",
            "outcome_verified": False,
        }

    def coordinate(self, _request, _proposal, _state):
        self.coordinate_calls += 1
        return {
            "status": "delivered",
            "operation": "physical_click",
            "outcome_verified": False,
        }


class DesktopVisionRoutingTests(unittest.TestCase):
    def _request(self, **kwargs) -> DesktopClickRequest:
        values = {
            "window_name": "Fixture",
            "target_text": "Visual target",
            "role": "button",
            "vision_fallback": VISION_FALLBACK_ZERO_EXACT,
        }
        values.update(kwargs)
        return DesktopClickRequest(**values)

    def test_exact_structural_target_wins_without_grounder(self):
        controls = [_control(name="Visual target")]
        observe = _ObservationSequence([_frame(controls), _frame(controls)])
        executors = _Executors()
        ground_calls = 0

        def ground(*_args):
            nonlocal ground_calls
            ground_calls += 1
            raise AssertionError("grounder must not run for exact structure")

        result = route_desktop_click(
            request=self._request(),
            observe=observe,
            ground=ground,
            execute_structural=executors.structural,
            execute_coordinate=executors.coordinate,
        )
        self.assertEqual(result.status, "delivered")
        self.assertEqual(result.route, "structural")
        self.assertEqual(result.reason, "structural-exact-delivered")
        self.assertEqual(ground_calls, 0)
        self.assertEqual(executors.structural_calls, 1)
        self.assertEqual(executors.coordinate_calls, 0)
        self.assertEqual(observe.calls, [False, False])

    def test_duplicate_exact_structure_abstains_without_vision(self):
        controls = [_control(name="Visual target"), _control(name="Visual target", left=260)]
        observe = _ObservationSequence([_frame(controls)])
        executors = _Executors()
        result = route_desktop_click(
            request=self._request(),
            observe=observe,
            ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
            execute_structural=executors.structural,
            execute_coordinate=executors.coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "structural-ambiguous")
        self.assertEqual(executors.coordinate_calls, 0)

    def test_hidden_or_disabled_exact_target_does_not_escalate(self):
        for control in (
            _control(name="Visual target", visible=False),
            _control(name="Visual target", enabled=False),
            _control(name="Visual target", visible=None),
            _control(name="Visual target", enabled=None),
        ):
            with self.subTest(control=control):
                observe = _ObservationSequence([_frame([control])])
                executors = _Executors()
                result = route_desktop_click(
                    request=self._request(),
                    observe=observe,
                    ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
                    execute_structural=executors.structural,
                    execute_coordinate=executors.coordinate,
                )
                self.assertEqual(result.status, "abstain")
                self.assertEqual(result.reason, "structural-target-not-actionable")
                self.assertEqual(executors.coordinate_calls, 0)

    def test_role_conflict_does_not_escalate(self):
        controls = [_control(name="Visual target", role="link")]
        result = route_desktop_click(
            request=self._request(role="button"),
            observe=_ObservationSequence([_frame(controls)]),
            ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
            execute_structural=_Executors().structural,
            execute_coordinate=_Executors().coordinate,
        )
        self.assertEqual(result.reason, "structural-role-conflict")

    def test_automation_id_miss_does_not_escalate(self):
        controls = [_control(name="Other", automation_id="known")]
        result = route_desktop_click(
            request=self._request(automation_id="missing"),
            observe=_ObservationSequence([_frame(controls)]),
            ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
            execute_structural=_Executors().structural,
            execute_coordinate=_Executors().coordinate,
        )
        self.assertEqual(result.reason, "automation-id-miss")

    def test_zero_exact_requires_explicit_visual_promotion(self):
        controls = [_control(name="Accessible name differs")]
        result = route_desktop_click(
            request=self._request(vision_fallback=VISION_FALLBACK_DISABLED),
            observe=_ObservationSequence([_frame(controls)]),
            ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
            execute_structural=_Executors().structural,
            execute_coordinate=_Executors().coordinate,
        )
        self.assertEqual(result.reason, "vision-fallback-not-promoted")

    def test_grounder_abstain_causes_zero_action(self):
        controls = [_control(name="Accessible name differs")]
        initial = _frame(controls)
        visual = _frame(controls, screenshot=True)
        executors = _Executors()

        def ground(_frame, _request, _uia):
            return DesktopGroundingResult(
                status="abstain",
                reason="grounder-inventory-ambiguous",
                proposal=None,
                diagnostics=_diagnostics(decision="inventory-ambiguous"),
            )

        result = route_desktop_click(
            request=self._request(),
            observe=_ObservationSequence([initial, visual]),
            ground=ground,
            execute_structural=executors.structural,
            execute_coordinate=executors.coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "vision-grounder-inventory-ambiguous")
        self.assertEqual(executors.coordinate_calls, 0)

    def test_valid_visual_proposal_is_reobserved_before_one_click(self):
        controls = [_control(name="Accessible name differs")]
        initial = _frame(controls)
        visual = _frame(controls, screenshot=True, marker="stable")
        fresh = _frame(controls, screenshot=True, marker="stable")
        executors = _Executors()

        def ground(frame, _request, uia):
            self.assertGreaterEqual(len(uia), 1)
            proposal = _proposal(frame.state)
            return DesktopGroundingResult(
                status="proposal",
                reason="grounder-accepted-proposal-only",
                proposal=proposal,
                diagnostics=_diagnostics(),
            )

        result = route_desktop_click(
            request=self._request(),
            observe=_ObservationSequence([initial, visual, fresh]),
            ground=ground,
            execute_structural=executors.structural,
            execute_coordinate=executors.coordinate,
        )
        self.assertEqual(result.status, "delivered")
        self.assertEqual(result.route, "vision")
        self.assertEqual(result.reason, "vision-zero-exact-delivered")
        self.assertEqual(executors.structural_calls, 0)
        self.assertEqual(executors.coordinate_calls, 1)
        self.assertIsNotNone(result.proposal)
        self.assertEqual(result.receipt["operation"], "physical_click")

    def test_changed_screenshot_after_grounding_abstains_before_executor(self):
        controls = [_control(name="Accessible name differs")]
        initial = _frame(controls)
        visual = _frame(controls, screenshot=True, marker="before")
        fresh = _frame(controls, screenshot=True, marker="after")
        executors = _Executors()

        result = route_desktop_click(
            request=self._request(),
            observe=_ObservationSequence([initial, visual, fresh]),
            ground=lambda frame, _request, _uia: DesktopGroundingResult(
                status="proposal",
                reason="grounder-accepted-proposal-only",
                proposal=_proposal(frame.state),
                diagnostics=_diagnostics(),
            ),
            execute_structural=executors.structural,
            execute_coordinate=executors.coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertIn(result.reason, {"frame-changed-after-vision", "screenshot-changed-after-vision"})
        self.assertEqual(executors.coordinate_calls, 0)

    def test_changed_process_or_window_after_grounding_abstains(self):
        controls = [_control(name="Accessible name differs")]
        for changed in (
            _frame(controls, screenshot=True, marker="stable", pid=9999),
            _frame(controls, screenshot=True, marker="stable", process_generation="100"),
            _frame(controls, screenshot=True, marker="stable", hwnd=9999),
            _frame(controls, screenshot=True, marker="stable", title="Other"),
        ):
            with self.subTest(identity=changed.state.window_instance):
                initial = _frame(controls)
                visual = _frame(controls, screenshot=True, marker="stable")
                executors = _Executors()
                result = route_desktop_click(
                    request=self._request(),
                    observe=_ObservationSequence([initial, visual, changed]),
                    ground=lambda frame, _request, _uia: DesktopGroundingResult(
                        status="proposal",
                        reason="grounder-accepted-proposal-only",
                        proposal=_proposal(frame.state),
                        diagnostics=_diagnostics(),
                    ),
                    execute_structural=executors.structural,
                    execute_coordinate=executors.coordinate,
                )
                self.assertEqual(result.status, "abstain")
                self.assertEqual(result.reason, "window-changed-after-vision")
                self.assertEqual(executors.coordinate_calls, 0)

    def test_proposal_evidence_mismatch_or_outside_window_abstains(self):
        controls = [_control(name="Accessible name differs")]
        for mutation in ("pid", "outside"):
            with self.subTest(mutation=mutation):
                initial = _frame(controls)
                visual = _frame(controls, screenshot=True, marker="stable")
                executors = _Executors()

                def ground(frame, _request, _uia):
                    proposal = _proposal(frame.state)
                    if mutation == "pid":
                        proposal = replace(proposal, process_id=9999)
                    else:
                        proposal = replace(proposal, screen_point=GrounderPoint(900.0, 900.0))
                    return DesktopGroundingResult(
                        status="proposal",
                        reason="grounder-accepted-proposal-only",
                        proposal=proposal,
                        diagnostics=_diagnostics(),
                    )

                result = route_desktop_click(
                    request=self._request(),
                    observe=_ObservationSequence([initial, visual]),
                    ground=ground,
                    execute_structural=executors.structural,
                    execute_coordinate=executors.coordinate,
                )
                self.assertEqual(result.status, "abstain")
                self.assertEqual(result.reason, "vision-proposal-evidence-mismatch")
                self.assertEqual(executors.coordinate_calls, 0)

    def test_structure_appearing_before_visual_action_forces_abstain(self):
        miss = [_control(name="Accessible name differs")]
        exact = [_control(name="Visual target")]
        initial = _frame(miss)
        visual = _frame(miss, screenshot=True, marker="stable")
        fresh = _frame(exact, screenshot=True, marker="stable")
        executors = _Executors()
        result = route_desktop_click(
            request=self._request(),
            observe=_ObservationSequence([initial, visual, fresh]),
            ground=lambda frame, _request, _uia: DesktopGroundingResult(
                status="proposal",
                reason="grounder-accepted-proposal-only",
                proposal=_proposal(frame.state),
                diagnostics=_diagnostics(),
            ),
            execute_structural=executors.structural,
            execute_coordinate=executors.coordinate,
        )
        self.assertEqual(result.status, "abstain")
        self.assertIn(result.reason, {"frame-changed-after-vision", "structure-changed-after-vision"})
        self.assertEqual(executors.coordinate_calls, 0)

    def test_stale_observation_is_rejected_before_any_action(self):
        controls = [_control(name="Visual target")]
        stale = replace(
            _frame(controls).state,
            observed_at="2020-01-01T00:00:00+00:00",
        )
        executors = _Executors()
        with self.assertRaisesRegex(DesktopRoutingError, "desktop-state-not-fresh"):
            route_desktop_click(
                request=self._request(),
                observe=_ObservationSequence([ObservedDesktopFrame(stale)]),
                ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
                execute_structural=executors.structural,
                execute_coordinate=executors.coordinate,
            )
        self.assertEqual(executors.structural_calls, 0)
        self.assertEqual(executors.coordinate_calls, 0)

    def test_delivery_receipt_cannot_claim_task_completion(self):
        controls = [_control(name="Visual target")]
        observe = _ObservationSequence([_frame(controls), _frame(controls)])

        def bad_executor(_request, _control, _state):
            return {"status": "delivered", "operation": "uia_invoke", "outcome_verified": True}

        with self.assertRaisesRegex(DesktopRoutingError, "must not claim task completion"):
            route_desktop_click(
                request=self._request(),
                observe=observe,
                ground=lambda *_args: (_ for _ in ()).throw(AssertionError("no vision")),
                execute_structural=bad_executor,
                execute_coordinate=_Executors().coordinate,
            )


class DesktopVisionRoutingSourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        cls.source = (repo / "runtime" / "windows" / "routing.py").read_text(encoding="utf-8")

    def test_vision_is_explicitly_promoted_and_non_authorizing(self):
        self.assertIn('VISION_FALLBACK_DISABLED = "disabled"', self.source)
        self.assertIn('VISION_FALLBACK_ZERO_EXACT = "zero-exact-candidate"', self.source)
        self.assertIn("Vision is never authorization", self.source)
        self.assertIn("frame_digest != visual.state.frame_digest", self.source)
        self.assertIn("screenshot_digest != visual.state.screenshot_digest", self.source)

    def test_no_generic_execution_or_public_dispatch_channel(self):
        for token in (
            "subprocess.",
            "os.system(",
            "shell=True",
            "eval(",
            "exec(",
            "tool_invoke",
            "run_anything",
        ):
            self.assertNotIn(token, self.source)

    def test_router_only_exposes_click_delivery_helpers(self):
        self.assertIn("execute_structural_click_with_backend", self.source)
        self.assertIn("execute_guarded_coordinate_click_with_backend", self.source)
        self.assertNotIn("type_text_guarded", self.source)
        self.assertNotIn("press_guarded", self.source)
        self.assertNotIn("scroll", self.source.casefold())


if __name__ == "__main__":
    unittest.main()
