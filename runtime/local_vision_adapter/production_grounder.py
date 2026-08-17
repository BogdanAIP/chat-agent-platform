"""Model-neutral production boundary for the accepted Stage 25 native-bbox grounder.

This module deliberately does not own llama.cpp, choose model artifacts, inspect
browser state, or perform browser actions.  A reviewed runtime owner supplies an
already-ready loopback client; this layer only turns one PNG capture plus bounded
target metadata into a bridge-shaped resolved/abstain result.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from .native_bbox import NativeBBoxLoopbackClient, run_native_bbox_zoom_case
from .production_policy import authorize_native_grounding
from .provider import VisionProviderError


@dataclass(frozen=True)
class ProductionVisualGroundingResult:
    status: str  # "resolved" | "abstain"
    reason: str
    point: dict[str, float] | None = None
    bbox: dict[str, float] | None = None
    diagnostics: dict[str, Any] | None = None


class ProductionGrounderError(RuntimeError):
    """Non-authorizing provider/contract failure at the production boundary."""


def _decode_png(image_bytes: bytes) -> Image.Image:
    if not isinstance(image_bytes, bytes) or not image_bytes:
        raise ProductionGrounderError("grounding image must be non-empty PNG bytes")
    try:
        with Image.open(BytesIO(image_bytes)) as opened:
            if opened.format != "PNG":
                raise ProductionGrounderError("grounding image must be PNG")
            opened.load()
            source = opened.convert("RGB")
    except ProductionGrounderError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ProductionGrounderError("grounding image is not a valid PNG") from exc

    if source.width <= 0 or source.height <= 0:
        raise ProductionGrounderError("grounding image has invalid dimensions")
    return source


def _clean_target_text(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProductionGrounderError("target_text must be text or null")
    cleaned = value.strip()
    return cleaned or None


def ground_png_for_browser(
    *,
    client: NativeBBoxLoopbackClient,
    image_bytes: bytes,
    instruction: str,
    kind: str,
    target_text: str | None = None,
) -> ProductionVisualGroundingResult:
    """Ground one CSS-viewport PNG and apply the production promotion policy.

    The returned object is intentionally compatible with the semantic bridge's
    callback contract: only ``resolved`` carries an actionable point; every
    measured but unpromoted/uncertain class returns ``abstain``. Provider or
    malformed-result failures raise ``ProductionGrounderError`` so the bridge
    records an error and still performs zero page mutation.
    """

    if not isinstance(client, NativeBBoxLoopbackClient):
        raise ProductionGrounderError("client must be NativeBBoxLoopbackClient")
    if not isinstance(instruction, str) or not instruction.strip():
        raise ProductionGrounderError("instruction must be non-empty text")
    if not isinstance(kind, str) or not kind.strip():
        raise ProductionGrounderError("kind must be non-empty text")

    source = _decode_png(image_bytes)
    cleaned_target_text = _clean_target_text(target_text)
    case = {
        "id": "production-browser-grounding",
        "kind": kind.strip(),
        "instruction": instruction.strip(),
        "target_text": cleaned_target_text,
        "bbox": None,
    }

    try:
        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
    except (VisionProviderError, ValueError, OSError) as exc:
        raise ProductionGrounderError(f"native-grounder-failed:{type(exc).__name__}") from exc

    policy = authorize_native_grounding(row)
    diagnostics = {
        "method": row.get("method"),
        "native_decision": row.get("decision"),
        "inventory_detection_count": row.get("inventory_detection_count"),
        "inventory_match_count": row.get("inventory_match_count"),
        "pass1_detection_count": row.get("pass1_detection_count"),
        "pass2_detection_count": row.get("pass2_detection_count"),
        "coarse_refined_iou": row.get("coarse_refined_iou"),
        "latency_seconds": row.get("latency_seconds"),
        "usage": row.get("usage"),
    }

    if policy.status == "error":
        raise ProductionGrounderError(policy.reason)
    if not policy.authorized:
        return ProductionVisualGroundingResult(
            status="abstain",
            reason=policy.reason,
            diagnostics=diagnostics,
        )

    assert policy.point is not None
    point = {"x": float(policy.point[0]), "y": float(policy.point[1])}
    refined = row.get("refined_box")
    bbox = None
    if isinstance(refined, dict):
        try:
            bbox = {
                "x1": float(refined["x1"]),
                "y1": float(refined["y1"]),
                "x2": float(refined["x2"]),
                "y2": float(refined["y2"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ProductionGrounderError("authorized-result-missing-valid-bbox") from exc

    if bbox is None:
        raise ProductionGrounderError("authorized-result-missing-valid-bbox")

    if not (0 <= point["x"] < source.width and 0 <= point["y"] < source.height):
        raise ProductionGrounderError("authorized-point-outside-source-image")

    return ProductionVisualGroundingResult(
        status="resolved",
        reason=policy.reason,
        point=point,
        bbox=bbox,
        diagnostics=diagnostics,
    )
