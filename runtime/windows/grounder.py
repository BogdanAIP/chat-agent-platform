from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Sequence

from PIL import Image, UnidentifiedImageError

from runtime.local_vision_adapter.native_bbox import (
    NativeBBoxLoopbackClient,
    parse_native_bbox_response,
    run_native_bbox_zoom_case,
)
from runtime.local_vision_adapter.provider import VisionProviderError

from .observation import ControlObservation, DesktopState


SCHEMA_VERSION = 1
WINDOW_COORDINATE_SPACE = "window_physical_px"
SCREEN_COORDINATE_SPACE = "screen_physical_px"
MAX_TARGET_TEXT_CHARS = 512
MAX_UIA_EVIDENCE = 32


class DesktopGrounderError(RuntimeError):
    """Fail-closed contract/provider error for non-authorizing desktop grounding."""


@dataclass(frozen=True)
class GrounderPoint:
    x: float
    y: float

    def to_mapping(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}


@dataclass(frozen=True)
class GrounderRegion:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    def to_mapping(self) -> dict[str, float]:
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class GrounderDiagnostics:
    decision: str
    method: str
    inventory_detection_count: int | None
    inventory_match_count: int | None
    inventory_labels: tuple[str, ...]
    pass1_detection_count: int | None
    pass2_detection_count: int | None
    pass2_labels: tuple[str, ...]
    consistency_iou: float | None
    latency_seconds: float | None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "method": self.method,
            "inventory_detection_count": self.inventory_detection_count,
            "inventory_match_count": self.inventory_match_count,
            "inventory_labels": list(self.inventory_labels),
            "pass1_detection_count": self.pass1_detection_count,
            "pass2_detection_count": self.pass2_detection_count,
            "pass2_labels": list(self.pass2_labels),
            "consistency_iou": self.consistency_iou,
            "latency_seconds": self.latency_seconds,
        }


@dataclass(frozen=True)
class GrounderProposal:
    schema_version: int
    target_text: str
    window_point: GrounderPoint
    screen_point: GrounderPoint
    window_region: GrounderRegion
    screen_region: GrounderRegion
    image_coordinate_space: str
    coordinate_space: str
    frame_digest: str
    screenshot_digest: str
    session_id: str
    application_identity: str
    process_id: int
    process_generation: str
    window_handle: int
    window_instance: str
    uia_evidence_digest: str | None
    method: str
    consistency_iou: float | None
    confidence: float | None
    confidence_basis: str
    latency_seconds: float | None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "target_text": self.target_text,
            "window_point": self.window_point.to_mapping(),
            "screen_point": self.screen_point.to_mapping(),
            "window_region": self.window_region.to_mapping(),
            "screen_region": self.screen_region.to_mapping(),
            "image_coordinate_space": self.image_coordinate_space,
            "coordinate_space": self.coordinate_space,
            "frame_digest": self.frame_digest,
            "screenshot_digest": self.screenshot_digest,
            "session_id": self.session_id,
            "application_identity": self.application_identity,
            "process_id": self.process_id,
            "process_generation": self.process_generation,
            "window_handle": self.window_handle,
            "window_instance": self.window_instance,
            "uia_evidence_digest": self.uia_evidence_digest,
            "method": self.method,
            "consistency_iou": self.consistency_iou,
            "confidence": self.confidence,
            "confidence_basis": self.confidence_basis,
            "latency_seconds": self.latency_seconds,
        }


@dataclass(frozen=True)
class DesktopGroundingResult:
    status: str  # "proposal" | "abstain"
    reason: str
    proposal: GrounderProposal | None
    diagnostics: GrounderDiagnostics

    def to_mapping(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "proposal": self.proposal.to_mapping() if self.proposal is not None else None,
            "diagnostics": self.diagnostics.to_mapping(),
        }


def _decode_exact_window_png(window_png: bytes, state: DesktopState) -> Image.Image:
    if not isinstance(window_png, bytes) or not window_png:
        raise DesktopGrounderError("window_png must be non-empty PNG bytes")
    if state.coordinate_space != SCREEN_COORDINATE_SPACE:
        raise DesktopGrounderError("desktop-state-coordinate-space-mismatch")
    if not state.screenshot_digest:
        raise DesktopGrounderError("desktop-state-missing-screenshot-digest")

    actual_digest = hashlib.sha256(window_png).hexdigest()
    if actual_digest != state.screenshot_digest:
        raise DesktopGrounderError("screenshot-digest-mismatch")

    try:
        with Image.open(BytesIO(window_png)) as opened:
            if opened.format != "PNG":
                raise DesktopGrounderError("window image must be PNG")
            opened.load()
            image = opened.convert("RGB")
    except DesktopGrounderError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise DesktopGrounderError("window image is not a valid PNG") from exc

    expected_size = (state.window_bounds.width, state.window_bounds.height)
    if image.size != expected_size:
        raise DesktopGrounderError("window-image-dimensions-do-not-match-desktop-state")
    if image.width <= 0 or image.height <= 0:
        raise DesktopGrounderError("window image has invalid dimensions")
    return image


def _clean_target_text(value: str) -> str:
    if not isinstance(value, str):
        raise DesktopGrounderError("target_text must be text")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > MAX_TARGET_TEXT_CHARS:
        raise DesktopGrounderError("target_text length is invalid")
    return cleaned


def _uia_evidence_digest(items: Sequence[ControlObservation] | None) -> str | None:
    if items is None:
        return None
    if isinstance(items, (str, bytes)):
        raise DesktopGrounderError("uia_evidence must be a control sequence")
    controls = tuple(items)
    if len(controls) > MAX_UIA_EVIDENCE:
        raise DesktopGrounderError("uia_evidence exceeds bounded limit")
    if not controls:
        return None

    parts: list[str] = []
    for control in controls:
        if not isinstance(control, ControlObservation):
            raise DesktopGrounderError("uia_evidence must contain ControlObservation values")
        parts.append(control.observation_fingerprint)
    encoded = "\n".join(sorted(parts)).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DesktopGrounderError("grounder returned malformed numeric evidence")
    converted = float(value)
    if not math.isfinite(converted):
        raise DesktopGrounderError("grounder returned non-finite numeric evidence")
    return converted


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DesktopGrounderError("grounder returned malformed count evidence")
    return value


def _diagnostic_labels(value: object, *, max_items: int) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        return ()
    try:
        detections = parse_native_bbox_response(value, max_items=max_items)
    except VisionProviderError:
        return ()
    return tuple(detection.label for detection in detections)


def _diagnostics_from_row(row: dict[str, Any]) -> GrounderDiagnostics:
    decision = row.get("decision")
    if not isinstance(decision, str) or not decision:
        raise DesktopGrounderError("desktop-grounder-missing-decision")
    return GrounderDiagnostics(
        decision=decision,
        method=str(row.get("method") or "native_bbox_450m_inventory_zoom"),
        inventory_detection_count=_int_or_none(row.get("inventory_detection_count")),
        inventory_match_count=_int_or_none(row.get("inventory_match_count")),
        inventory_labels=_diagnostic_labels(row.get("inventory_response"), max_items=16),
        pass1_detection_count=_int_or_none(row.get("pass1_detection_count")),
        pass2_detection_count=_int_or_none(row.get("pass2_detection_count")),
        pass2_labels=_diagnostic_labels(row.get("pass2_response"), max_items=8),
        consistency_iou=_float_or_none(row.get("coarse_refined_iou")),
        latency_seconds=_float_or_none(row.get("latency_seconds")),
    )


def _region_from_row(value: object, *, width: int, height: int) -> GrounderRegion:
    if not isinstance(value, dict):
        raise DesktopGrounderError("accepted-grounder-result-missing-region")
    try:
        x1 = float(value["x1"])
        y1 = float(value["y1"])
        x2 = float(value["x2"])
        y2 = float(value["y2"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DesktopGrounderError("accepted-grounder-result-has-malformed-region") from exc
    coords = (x1, y1, x2, y2)
    if not all(math.isfinite(item) for item in coords):
        raise DesktopGrounderError("accepted-grounder-result-has-nonfinite-region")
    if not (0.0 <= x1 < x2 <= float(width) and 0.0 <= y1 < y2 <= float(height)):
        raise DesktopGrounderError("accepted-grounder-region-outside-window-image")
    return GrounderRegion(x1, y1, x2, y2)


def _point_from_row(value: object, *, width: int, height: int) -> GrounderPoint:
    if not isinstance(value, dict):
        raise DesktopGrounderError("accepted-grounder-result-missing-point")
    try:
        x = float(value["x"])
        y = float(value["y"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DesktopGrounderError("accepted-grounder-result-has-malformed-point") from exc
    if not math.isfinite(x) or not math.isfinite(y):
        raise DesktopGrounderError("accepted-grounder-result-has-nonfinite-point")
    if not (0.0 <= x < float(width) and 0.0 <= y < float(height)):
        raise DesktopGrounderError("accepted-grounder-point-outside-window-image")
    return GrounderPoint(x, y)


def _translate_point(point: GrounderPoint, state: DesktopState) -> GrounderPoint:
    return GrounderPoint(
        x=point.x + float(state.window_bounds.left),
        y=point.y + float(state.window_bounds.top),
    )


def _translate_region(region: GrounderRegion, state: DesktopState) -> GrounderRegion:
    left = float(state.window_bounds.left)
    top = float(state.window_bounds.top)
    return GrounderRegion(
        left=region.left + left,
        top=region.top + top,
        right=region.right + left,
        bottom=region.bottom + top,
    )


def ground_desktop_target(
    *,
    client: NativeBBoxLoopbackClient,
    window_png: bytes,
    target_text: str,
    desktop_state: DesktopState,
    uia_evidence: Sequence[ControlObservation] | None = None,
) -> DesktopGroundingResult:
    """Return an explicit proposal/abstain result bound to one DesktopState frame.

    The model remains non-authorizing.  Abstention preserves the exact grounding
    decision and bounded diagnostic labels/counts so routing and qualification do
    not need to guess why the local VLM refused a target.
    """

    if not isinstance(client, NativeBBoxLoopbackClient):
        raise DesktopGrounderError("client must be NativeBBoxLoopbackClient")
    if not isinstance(desktop_state, DesktopState):
        raise DesktopGrounderError("desktop_state must be DesktopState")

    cleaned_target = _clean_target_text(target_text)
    source = _decode_exact_window_png(window_png, desktop_state)
    evidence_digest = _uia_evidence_digest(uia_evidence)

    case = {
        "id": "production-desktop-grounding",
        "kind": "desktop_exact_window",
        "instruction": (
            "Locate the visible Windows UI element whose exact readable label is "
            f"{cleaned_target!r} in this exact application window."
        ),
        "target_text": cleaned_target,
        "bbox": None,
    }

    try:
        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
    except (VisionProviderError, ValueError, OSError) as exc:
        raise DesktopGrounderError(f"desktop-grounder-failed:{type(exc).__name__}") from exc

    if row.get("parse_error"):
        raise DesktopGrounderError("desktop-grounder-provider-or-parse-error")

    diagnostics = _diagnostics_from_row(row)
    abstain_decisions = {
        "inventory-absent",
        "inventory-ambiguous",
        "absent",
        "ambiguous-pass1",
        "refinement-abstain",
        "ambiguous-pass2",
        "inconsistent-pass2",
    }
    if diagnostics.decision in abstain_decisions:
        return DesktopGroundingResult(
            status="abstain",
            reason=f"grounder-{diagnostics.decision}",
            proposal=None,
            diagnostics=diagnostics,
        )
    if diagnostics.decision != "accepted":
        raise DesktopGrounderError("desktop-grounder-returned-unknown-decision")

    window_point = _point_from_row(
        row.get("prediction_point"),
        width=source.width,
        height=source.height,
    )
    window_region = _region_from_row(
        row.get("refined_box"),
        width=source.width,
        height=source.height,
    )
    if not (
        window_region.left <= window_point.x <= window_region.right
        and window_region.top <= window_point.y <= window_region.bottom
    ):
        raise DesktopGrounderError("accepted-grounder-point-outside-proposed-region")

    proposal = GrounderProposal(
        schema_version=SCHEMA_VERSION,
        target_text=cleaned_target,
        window_point=window_point,
        screen_point=_translate_point(window_point, desktop_state),
        window_region=window_region,
        screen_region=_translate_region(window_region, desktop_state),
        image_coordinate_space=WINDOW_COORDINATE_SPACE,
        coordinate_space=SCREEN_COORDINATE_SPACE,
        frame_digest=desktop_state.frame_digest,
        screenshot_digest=desktop_state.screenshot_digest,
        session_id=desktop_state.session_id,
        application_identity=desktop_state.application_identity,
        process_id=desktop_state.process_id,
        process_generation=desktop_state.process_generation,
        window_handle=desktop_state.window_handle,
        window_instance=desktop_state.window_instance,
        uia_evidence_digest=evidence_digest,
        method=diagnostics.method,
        consistency_iou=diagnostics.consistency_iou,
        confidence=None,
        confidence_basis="uncalibrated-model-proposal",
        latency_seconds=diagnostics.latency_seconds,
    )
    return DesktopGroundingResult(
        status="proposal",
        reason="grounder-accepted-proposal-only",
        proposal=proposal,
        diagnostics=diagnostics,
    )


def locate_desktop_target(
    *,
    client: NativeBBoxLoopbackClient,
    window_png: bytes,
    target_text: str,
    desktop_state: DesktopState,
    uia_evidence: Sequence[ControlObservation] | None = None,
) -> GrounderProposal | None:
    """Compatibility wrapper returning only the proposal or ``None`` on abstain."""

    return ground_desktop_target(
        client=client,
        window_png=window_png,
        target_text=target_text,
        desktop_state=desktop_state,
        uia_evidence=uia_evidence,
    ).proposal
