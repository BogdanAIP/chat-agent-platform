from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
import time
from typing import Any, Callable, Mapping, Protocol

from .grounder import DesktopGroundingResult, GrounderProposal, GrounderRegion
from .observation import ControlObservation, DesktopState, Rect


SCHEMA_VERSION = 1
MAX_TARGET_TEXT_CHARS = 512
DEFAULT_MAX_OBSERVATION_AGE_SECONDS = 5.0
VISION_FALLBACK_DISABLED = "disabled"
VISION_FALLBACK_ZERO_EXACT = "zero-exact-candidate"
_ALLOWED_VISION_POLICIES = {VISION_FALLBACK_DISABLED, VISION_FALLBACK_ZERO_EXACT}


class DesktopRoutingError(RuntimeError):
    """Contract error in the deterministic desktop-routing boundary."""


@dataclass(frozen=True)
class DesktopClickRequest:
    window_name: str
    target_text: str
    role: str | None = None
    automation_id: str | None = None
    structural_name: str | None = None
    vision_fallback: str = VISION_FALLBACK_DISABLED


@dataclass(frozen=True)
class ObservedDesktopFrame:
    state: DesktopState
    screenshot_png: bytes | None = None


@dataclass(frozen=True)
class DesktopRoutingResult:
    schema_version: int
    status: str  # "delivered" | "abstain"
    reason: str
    route: str | None  # "structural" | "vision" | None
    initial_frame_digest: str
    authorized_frame_digest: str | None
    proposal: GrounderProposal | None
    receipt: Mapping[str, Any] | None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "reason": self.reason,
            "route": self.route,
            "initial_frame_digest": self.initial_frame_digest,
            "authorized_frame_digest": self.authorized_frame_digest,
            "proposal": self.proposal.to_mapping() if self.proposal is not None else None,
            "receipt": dict(self.receipt) if self.receipt is not None else None,
        }


class ObservationProvider(Protocol):
    def __call__(self, need_screenshot: bool) -> ObservedDesktopFrame: ...


class GroundingProvider(Protocol):
    def __call__(
        self,
        frame: ObservedDesktopFrame,
        request: DesktopClickRequest,
        uia_evidence: tuple[ControlObservation, ...],
    ) -> DesktopGroundingResult: ...


StructuralExecutor = Callable[
    [DesktopClickRequest, ControlObservation, DesktopState], Mapping[str, Any]
]
CoordinateExecutor = Callable[
    [DesktopClickRequest, GrounderProposal, DesktopState], Mapping[str, Any]
]


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def _validate_request(request: DesktopClickRequest) -> DesktopClickRequest:
    if not isinstance(request, DesktopClickRequest):
        raise DesktopRoutingError("request must be DesktopClickRequest")
    if not isinstance(request.window_name, str) or not request.window_name.strip():
        raise DesktopRoutingError("window_name is required")
    if not isinstance(request.target_text, str):
        raise DesktopRoutingError("target_text must be text")
    target = " ".join(request.target_text.split())
    if not target or len(target) > MAX_TARGET_TEXT_CHARS:
        raise DesktopRoutingError("target_text length is invalid")
    for name, value in (
        ("role", request.role),
        ("automation_id", request.automation_id),
        ("structural_name", request.structural_name),
    ):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise DesktopRoutingError(f"{name} must be non-empty text when supplied")
    if request.vision_fallback not in _ALLOWED_VISION_POLICIES:
        raise DesktopRoutingError("unknown vision_fallback policy")
    return request


def _parse_observed_at(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise DesktopRoutingError("DesktopState observed_at is invalid") from exc
    if parsed.tzinfo is None:
        raise DesktopRoutingError("DesktopState observed_at must include timezone")
    return parsed.astimezone(timezone.utc)


def _require_recent(state: DesktopState, *, max_age_seconds: float) -> None:
    if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, (int, float)):
        raise DesktopRoutingError("max observation age must be numeric")
    if not 0 < float(max_age_seconds) <= 30.0:
        raise DesktopRoutingError("max observation age is outside the bounded contract")
    age = (datetime.now(timezone.utc) - _parse_observed_at(state.observed_at)).total_seconds()
    if age < -2.0 or age > float(max_age_seconds):
        raise DesktopRoutingError("desktop-state-not-fresh")


def _validate_frame(
    frame: ObservedDesktopFrame,
    *,
    require_screenshot: bool,
    max_age_seconds: float,
) -> None:
    if not isinstance(frame, ObservedDesktopFrame):
        raise DesktopRoutingError("observation provider returned invalid frame")
    if not isinstance(frame.state, DesktopState):
        raise DesktopRoutingError("observation provider returned invalid DesktopState")
    _require_recent(frame.state, max_age_seconds=max_age_seconds)
    if not require_screenshot:
        return
    if not isinstance(frame.screenshot_png, bytes) or not frame.screenshot_png:
        raise DesktopRoutingError("fresh visual routing requires exact-window PNG bytes")
    digest = hashlib.sha256(frame.screenshot_png).hexdigest()
    if frame.state.screenshot_digest != digest:
        raise DesktopRoutingError("observation-screenshot-digest-mismatch")


def _window_identity(state: DesktopState) -> tuple[Any, ...]:
    bounds = state.window_bounds
    return (
        state.session_id,
        state.application_identity,
        state.process_id,
        state.process_generation,
        state.window_handle,
        state.window_instance,
        state.window_title,
        bounds.left,
        bounds.top,
        bounds.right,
        bounds.bottom,
        state.coordinate_space,
    )


def _same_window(left: DesktopState, right: DesktopState) -> bool:
    return _window_identity(left) == _window_identity(right)


def _target_name(request: DesktopClickRequest) -> str:
    return request.structural_name or request.target_text


def _role_matches(control: ControlObservation, request: DesktopClickRequest) -> bool:
    return request.role is None or _normalize_text(control.role) == _normalize_text(request.role)


def _name_matches(control: ControlObservation, request: DesktopClickRequest) -> bool:
    return _normalize_text(control.name) == _normalize_text(_target_name(request))


def _is_actionable(control: ControlObservation) -> bool:
    return control.visible is True and control.enabled is True and control.bounds is not None


def _structural_classification(
    state: DesktopState,
    request: DesktopClickRequest,
) -> tuple[str, ControlObservation | None]:
    controls = state.controls
    if request.automation_id is not None:
        matches = tuple(control for control in controls if control.automation_id == request.automation_id)
        if not matches:
            return "automation-id-miss", None
        if len(matches) > 1:
            return "structural-ambiguous", None
        control = matches[0]
        if not _role_matches(control, request) or not _name_matches(control, request):
            return "structural-identity-conflict", None
        if not _is_actionable(control):
            return "structural-target-not-actionable", None
        return "structural-exact", control

    exact = tuple(
        control
        for control in controls
        if _name_matches(control, request) and _role_matches(control, request)
    )
    if len(exact) > 1:
        return "structural-ambiguous", None
    if len(exact) == 1:
        control = exact[0]
        if not _is_actionable(control):
            return "structural-target-not-actionable", None
        return "structural-exact", control

    name_only = tuple(control for control in controls if _name_matches(control, request))
    if name_only and request.role is not None:
        return "structural-role-conflict", None
    return "structural-miss", None


def _abstain(
    *,
    initial: DesktopState,
    reason: str,
    route: str | None = None,
    proposal: GrounderProposal | None = None,
) -> DesktopRoutingResult:
    return DesktopRoutingResult(
        schema_version=SCHEMA_VERSION,
        status="abstain",
        reason=reason,
        route=route,
        initial_frame_digest=initial.frame_digest,
        authorized_frame_digest=None,
        proposal=proposal,
        receipt=None,
    )


def _validate_receipt(receipt: Mapping[str, Any], *, expected_route: str) -> Mapping[str, Any]:
    if not isinstance(receipt, Mapping):
        raise DesktopRoutingError("executor returned an invalid receipt")
    if receipt.get("status") != "delivered":
        raise DesktopRoutingError("executor did not return delivered status")
    if receipt.get("outcome_verified") is not False:
        raise DesktopRoutingError("delivery receipt must not claim task completion")
    operation = receipt.get("operation")
    if not isinstance(operation, str) or not operation:
        raise DesktopRoutingError("delivery receipt omitted operation")
    if expected_route == "vision" and operation != "physical_click":
        raise DesktopRoutingError("vision route must deliver exactly physical_click")
    if expected_route == "structural" and not operation.startswith("uia_"):
        raise DesktopRoutingError("structural route must deliver a native UIA operation")
    return dict(receipt)


def _point_inside(bounds: Rect, x: float, y: float) -> bool:
    return bool(
        math.isfinite(x)
        and math.isfinite(y)
        and float(bounds.left) <= x <= float(bounds.right)
        and float(bounds.top) <= y <= float(bounds.bottom)
    )


def _point_inside_region(region: GrounderRegion, x: float, y: float) -> bool:
    return bool(
        math.isfinite(x)
        and math.isfinite(y)
        and region.left <= x <= region.right
        and region.top <= y <= region.bottom
    )


def _proposal_matches_state(
    proposal: GrounderProposal,
    state: DesktopState,
    request: DesktopClickRequest,
    *,
    require_uia_evidence: bool,
) -> bool:
    left = float(state.window_bounds.left)
    top = float(state.window_bounds.top)
    width = float(state.window_bounds.width)
    height = float(state.window_bounds.height)
    translated_point = bool(
        abs(proposal.screen_point.x - (proposal.window_point.x + left)) < 1e-6
        and abs(proposal.screen_point.y - (proposal.window_point.y + top)) < 1e-6
    )
    translated_region = bool(
        abs(proposal.screen_region.left - (proposal.window_region.left + left)) < 1e-6
        and abs(proposal.screen_region.top - (proposal.window_region.top + top)) < 1e-6
        and abs(proposal.screen_region.right - (proposal.window_region.right + left)) < 1e-6
        and abs(proposal.screen_region.bottom - (proposal.window_region.bottom + top)) < 1e-6
    )
    local_region_valid = bool(
        0.0 <= proposal.window_region.left < proposal.window_region.right <= width
        and 0.0 <= proposal.window_region.top < proposal.window_region.bottom <= height
        and _point_inside_region(
            proposal.window_region,
            proposal.window_point.x,
            proposal.window_point.y,
        )
    )
    return bool(
        _normalize_text(proposal.target_text) == _normalize_text(request.target_text)
        and proposal.session_id == state.session_id
        and proposal.application_identity == state.application_identity
        and proposal.process_id == state.process_id
        and proposal.process_generation == state.process_generation
        and proposal.window_handle == state.window_handle
        and proposal.window_instance == state.window_instance
        and proposal.frame_digest == state.frame_digest
        and proposal.screenshot_digest == state.screenshot_digest
        and proposal.image_coordinate_space == "window_physical_px"
        and proposal.coordinate_space == "screen_physical_px"
        and proposal.confidence is None
        and proposal.confidence_basis == "uncalibrated-model-proposal"
        and (not require_uia_evidence or bool(proposal.uia_evidence_digest))
        and translated_point
        and translated_region
        and local_region_valid
        and _point_inside(state.window_bounds, proposal.screen_point.x, proposal.screen_point.y)
        and _point_inside_region(
            proposal.screen_region,
            proposal.screen_point.x,
            proposal.screen_point.y,
        )
        and _point_inside(state.window_bounds, proposal.screen_region.left, proposal.screen_region.top)
        and _point_inside(state.window_bounds, proposal.screen_region.right, proposal.screen_region.bottom)
    )


def _bounded_uia_evidence(
    state: DesktopState,
    request: DesktopClickRequest,
) -> tuple[ControlObservation, ...]:
    relevant = tuple(
        control
        for control in state.controls
        if control.visible is not False and (request.role is None or _role_matches(control, request))
    )
    return relevant[:32]


def route_desktop_click(
    *,
    request: DesktopClickRequest,
    observe: ObservationProvider,
    ground: GroundingProvider,
    execute_structural: StructuralExecutor,
    execute_coordinate: CoordinateExecutor,
    max_observation_age_seconds: float = DEFAULT_MAX_OBSERVATION_AGE_SECONDS,
) -> DesktopRoutingResult:
    """Route one click through structure first, then explicitly promoted vision.

    Vision is never authorization. A visual proposal is executable only after
    fresh exact-window re-observation proves the same process/window/frame.
    Structural ambiguity, non-actionable controls, role conflicts and supplied
    AutomationId misses never escalate to vision. Delivery is not completion.
    """

    request = _validate_request(request)
    initial = observe(False)
    _validate_frame(initial, require_screenshot=False, max_age_seconds=max_observation_age_seconds)

    classification, _ = _structural_classification(initial.state, request)
    if classification == "structural-exact":
        fresh = observe(False)
        _validate_frame(fresh, require_screenshot=False, max_age_seconds=max_observation_age_seconds)
        if not _same_window(initial.state, fresh.state):
            return _abstain(initial=initial.state, reason="window-changed-before-structural-action")
        fresh_classification, fresh_control = _structural_classification(fresh.state, request)
        if fresh_classification != "structural-exact" or fresh_control is None:
            return _abstain(initial=initial.state, reason="structure-changed-before-structural-action")
        receipt = _validate_receipt(
            execute_structural(request, fresh_control, fresh.state),
            expected_route="structural",
        )
        return DesktopRoutingResult(
            schema_version=SCHEMA_VERSION,
            status="delivered",
            reason="structural-exact-delivered",
            route="structural",
            initial_frame_digest=initial.state.frame_digest,
            authorized_frame_digest=fresh.state.frame_digest,
            proposal=None,
            receipt=receipt,
        )

    if classification != "structural-miss":
        return _abstain(initial=initial.state, reason=classification)
    if request.vision_fallback != VISION_FALLBACK_ZERO_EXACT:
        return _abstain(initial=initial.state, reason="vision-fallback-not-promoted")

    visual = observe(True)
    _validate_frame(visual, require_screenshot=True, max_age_seconds=max_observation_age_seconds)
    if not _same_window(initial.state, visual.state):
        return _abstain(initial=initial.state, reason="window-changed-before-vision")
    visual_classification, _ = _structural_classification(visual.state, request)
    if visual_classification != "structural-miss":
        return _abstain(initial=initial.state, reason="structure-changed-before-vision")

    uia_evidence = _bounded_uia_evidence(visual.state, request)
    grounding = ground(visual, request, uia_evidence)
    if not isinstance(grounding, DesktopGroundingResult):
        raise DesktopRoutingError("grounder returned an invalid result")
    if grounding.status != "proposal" or grounding.proposal is None:
        return _abstain(
            initial=initial.state,
            reason=f"vision-{grounding.reason}",
            route="vision",
        )
    proposal = grounding.proposal
    if not _proposal_matches_state(
        proposal,
        visual.state,
        request,
        require_uia_evidence=bool(uia_evidence),
    ):
        return _abstain(
            initial=initial.state,
            reason="vision-proposal-evidence-mismatch",
            route="vision",
            proposal=proposal,
        )

    fresh = observe(True)
    _validate_frame(fresh, require_screenshot=True, max_age_seconds=max_observation_age_seconds)
    if not _same_window(visual.state, fresh.state):
        return _abstain(
            initial=initial.state,
            reason="window-changed-after-vision",
            route="vision",
            proposal=proposal,
        )
    if fresh.state.frame_digest != visual.state.frame_digest:
        return _abstain(
            initial=initial.state,
            reason="frame-changed-after-vision",
            route="vision",
            proposal=proposal,
        )
    if fresh.state.screenshot_digest != visual.state.screenshot_digest:
        return _abstain(
            initial=initial.state,
            reason="screenshot-changed-after-vision",
            route="vision",
            proposal=proposal,
        )
    fresh_classification, _ = _structural_classification(fresh.state, request)
    if fresh_classification != "structural-miss":
        return _abstain(
            initial=initial.state,
            reason="structure-changed-after-vision",
            route="vision",
            proposal=proposal,
        )
    if not _proposal_matches_state(
        proposal,
        fresh.state,
        request,
        require_uia_evidence=bool(uia_evidence),
    ):
        return _abstain(
            initial=initial.state,
            reason="vision-proposal-stale",
            route="vision",
            proposal=proposal,
        )

    receipt = _validate_receipt(
        execute_coordinate(request, proposal, fresh.state),
        expected_route="vision",
    )
    return DesktopRoutingResult(
        schema_version=SCHEMA_VERSION,
        status="delivered",
        reason="vision-zero-exact-delivered",
        route="vision",
        initial_frame_digest=initial.state.frame_digest,
        authorized_frame_digest=fresh.state.frame_digest,
        proposal=proposal,
        receipt=receipt,
    )


def _receipt_mapping(receipt: object) -> dict[str, Any]:
    if isinstance(receipt, Mapping):
        return dict(receipt)
    names = (
        "status",
        "receipt_id",
        "operation",
        "native",
        "target_fingerprint",
        "delivered_at",
        "outcome_verified",
    )
    mapped = {name: getattr(receipt, name, None) for name in names}
    if not mapped.get("status"):
        raise DesktopRoutingError("backend receipt is missing status")
    return mapped


def execute_structural_click_with_backend(
    backend: object,
    request: DesktopClickRequest,
    _control: ControlObservation,
    _state: DesktopState,
) -> Mapping[str, Any]:
    """Execute one independently re-resolved native UIA click."""

    from openadapt_flow.ir import StructuralLocator

    locator = StructuralLocator(
        role=request.role,
        name=_target_name(request),
        automation_id=request.automation_id,
        window_name=request.window_name,
    )
    handle = backend.locate_structural(locator)
    if handle is None or handle.candidate_count != 1 or not handle.target_fingerprint:
        raise DesktopRoutingError("backend structural re-resolution was not unique")
    return _receipt_mapping(backend.act_structural(locator, handle))


def execute_guarded_coordinate_click_with_backend(
    backend: object,
    _request: DesktopClickRequest,
    proposal: GrounderProposal,
    state: DesktopState,
    *,
    attempts: int = 12,
) -> Mapping[str, Any]:
    """Deliver one guarded point click after native foreground/hit-test checks.

    Exact-window routing authorization happens before this helper. Here a Win32
    guard additionally proves that the authorized top-level HWND is foreground
    and is the root window physically under the proposed point. The already
    accepted backend frame guard then binds actual delivery to a fresh frame.
    """

    from openadapt_flow.backend import StructuralResolutionRefused
    from .native_point_guard import NativePointGuardError, require_foreground_hit_target

    x = int(round(proposal.screen_point.x))
    y = int(round(proposal.screen_point.y))
    if not 1 <= attempts <= 20:
        raise DesktopRoutingError("guarded coordinate attempts are outside the bounded contract")

    last: Exception | None = None
    for _ in range(attempts):
        try:
            # Reject focus changes or foreign overlays before arming mutation.
            require_foreground_hit_target(state, x, y)
        except NativePointGuardError as exc:
            raise DesktopRoutingError("native-point-guard-refused") from exc

        try:
            backend.arm_guarded_coordinate(x, y)
            frame = backend.screenshot()
            try:
                # Re-check after arming/screenshot so an overlay appearing in
                # that interval still cancels the armed point before delivery.
                require_foreground_hit_target(state, x, y)
            except NativePointGuardError as exc:
                backend.cancel_guarded_coordinate()
                raise DesktopRoutingError("native-point-guard-refused") from exc
            digest = hashlib.sha256(frame).hexdigest()
            receipt = backend.act_guarded_coordinate(
                x,
                y,
                expected_frame_sha256=digest,
            )
            return _receipt_mapping(receipt)
        except StructuralResolutionRefused as exc:
            last = exc
            backend.cancel_guarded_coordinate()
            time.sleep(0.06)
    raise DesktopRoutingError("guarded coordinate action could not obtain a stable frame") from last
