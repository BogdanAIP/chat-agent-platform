"""Native bounding-box grounding candidate for Stage 25 local vision.

LFM2.5-VL-450M is explicitly post-trained for normalized bounding-box prediction.
This module keeps that model-specific capability behind a deterministic adapter:

1. detect the requested UI element on the full screenshot;
2. fail closed when zero/multiple candidates make a click ambiguous;
3. crop a bounded context region around one coarse candidate and upscale it;
4. run the same normalized-bbox detector again on the crop;
5. require coarse/refined spatial consistency before deriving a click point.

The model never clicks. The deterministic adapter maps normalized boxes back to
source-image coordinates and emits no point when validation is uncertain.
"""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from io import BytesIO
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Callable
from urllib import error as urllib_error
from urllib import request as urllib_request

from PIL import Image

from .benchmark import box_iou, score_grounding
from .mark_grid import Box, Point, box_center, map_box_from_crop, plan_mark_grid_crop
from .renderer import crop_source_image
from .provider import VisionProviderError


Transport = Callable[[str, bytes, float], dict[str, Any]]


@dataclass(frozen=True)
class NativeDetection:
    label: str
    bbox: Box  # normalized [0,1]


@dataclass(frozen=True)
class NativeVisionResult:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def native_bbox_response_schema() -> dict[str, Any]:
    """Schema matching Liquid AI's documented normalized detection format."""

    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number", "minimum": 0, "maximum": 1},
                    "minItems": 4,
                    "maxItems": 4,
                },
            },
            "required": ["label", "bbox"],
            "additionalProperties": False,
        },
        "maxItems": 8,
    }


def build_native_bbox_prompt(target: str) -> str:
    """Use the model-card grounding contract, specialized to one UI instruction."""

    target = target.strip() if isinstance(target, str) else ""
    if not target:
        raise VisionProviderError("target must be non-empty text")
    return (
        "Detect all instances of the UI element needed to complete this instruction: "
        f"{target}. "
        'Response must be a JSON array: [{"label": "...", "bbox": [x1, y1, x2, y2]}, ...]. '
        "Coordinates are normalized to [0,1]. Return [] if no matching UI element is visible. "
        "Do not invent an element that is not visible."
    )


def _extract_json_array(text: str) -> list[Any]:
    if not isinstance(text, str) or not text.strip():
        raise VisionProviderError("model response must be non-empty text")
    stripped = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise VisionProviderError("native bbox response must be valid JSON") from exc
    if not isinstance(value, list):
        raise VisionProviderError("native bbox response must be a JSON array")
    return value


def parse_native_bbox_response(text: str) -> tuple[NativeDetection, ...]:
    """Validate normalized model-card detections; [] is an explicit abstention."""

    value = _extract_json_array(text)
    if len(value) > 8:
        raise VisionProviderError("native bbox response contains too many detections")

    detections: list[NativeDetection] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"label", "bbox"}:
            raise VisionProviderError(f"detection {index} must contain exactly label and bbox")
        label = item["label"]
        raw_box = item["bbox"]
        if not isinstance(label, str) or not label.strip():
            raise VisionProviderError(f"detection {index} label must be non-empty text")
        if not isinstance(raw_box, list) or len(raw_box) != 4:
            raise VisionProviderError(f"detection {index} bbox must contain four numbers")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in raw_box):
            raise VisionProviderError(f"detection {index} bbox coordinates must be numeric")
        coords = tuple(float(v) for v in raw_box)
        if not all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in coords):
            raise VisionProviderError(f"detection {index} bbox must be normalized to [0,1]")
        box = Box(*coords).validate()
        detections.append(NativeDetection(label=label.strip(), bbox=box))
    return tuple(detections)


def normalized_box_to_pixels(box: Box, width: int, height: int) -> Box:
    box = box.validate()
    if box.x2 > 1.0 or box.y2 > 1.0:
        raise VisionProviderError("normalized bbox extends outside [0,1]")
    if width <= 0 or height <= 0:
        raise VisionProviderError("image dimensions must be positive")
    return Box(
        box.x1 * width,
        box.y1 * height,
        box.x2 * width,
        box.y2 * height,
    ).validate()


def _context_box(coarse: Box, width: int, height: int) -> Box:
    """Expand a coarse detection while preserving useful nearby UI context."""

    coarse = coarse.validate()
    target_width = min(float(width), max(256.0, coarse.width * 3.0))
    target_height = min(float(height), max(256.0, coarse.height * 3.0))
    cx = (coarse.x1 + coarse.x2) / 2.0
    cy = (coarse.y1 + coarse.y2) / 2.0

    x1 = max(0.0, min(float(width) - target_width, cx - target_width / 2.0))
    y1 = max(0.0, min(float(height) - target_height, cy - target_height / 2.0))
    x2 = x1 + target_width
    y2 = y1 + target_height

    # Integer-aligned crop bounds keep Pillow crop dimensions and mapping exact.
    x1_i = max(0, int(math.floor(x1)))
    y1_i = max(0, int(math.floor(y1)))
    x2_i = min(width, int(math.ceil(x2)))
    y2_i = min(height, int(math.ceil(y2)))
    return Box(float(x1_i), float(y1_i), float(x2_i), float(y2_i)).validate()


def _image_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _urllib_json_transport(url: str, body: bytes, timeout_seconds: float) -> dict[str, Any]:
    req = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read()
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise VisionProviderError(f"local inference HTTP {exc.code}: {detail[:500]}") from exc
    except (urllib_error.URLError, TimeoutError, OSError) as exc:
        raise VisionProviderError(f"local inference transport failed: {exc}") from exc

    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VisionProviderError("local inference response was not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise VisionProviderError("local inference response JSON must be an object")
    return value


class NativeBBoxLoopbackClient:
    """Small model-specific client using Liquid AI's documented vision sampling."""

    def __init__(
        self,
        *,
        port: int,
        timeout_seconds: float = 120.0,
        transport: Transport | None = None,
    ) -> None:
        if isinstance(port, bool) or not isinstance(port, int) or not (1 <= port <= 65535):
            raise VisionProviderError("port must be an integer between 1 and 65535")
        if not math.isfinite(float(timeout_seconds)) or timeout_seconds <= 0:
            raise VisionProviderError("timeout_seconds must be positive and finite")
        self._url = f"http://127.0.0.1:{port}/v1/chat/completions"
        self._timeout_seconds = float(timeout_seconds)
        self._transport = transport or _urllib_json_transport

    @property
    def url(self) -> str:
        return self._url

    def detect(self, *, image_data_uri: str, target: str) -> NativeVisionResult:
        if not isinstance(image_data_uri, str) or not image_data_uri.startswith("data:image/"):
            raise VisionProviderError("image must be a local data:image URI")
        prompt = build_native_bbox_prompt(target)
        payload = {
            "model": "local",
            "messages": [
                {
                    "role": "user",
                    # Keep image first to mirror Liquid AI's published grounding example.
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_data_uri}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "temperature": 0.1,
            "min_p": 0.15,
            "repeat_penalty": 1.05,
            "seed": 42,
            "max_tokens": 96,
            "response_format": {
                "type": "json_object",
                "schema": native_bbox_response_schema(),
            },
        }
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
        response = self._transport(self._url, body, self._timeout_seconds)
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise VisionProviderError("local inference response is missing choices[0].message.content") from exc
        if not isinstance(content, str) or not content.strip():
            raise VisionProviderError("local inference content must be non-empty text")
        usage = response.get("usage")
        if not isinstance(usage, dict):
            usage = {}

        def token_value(name: str) -> int | None:
            value = usage.get(name)
            return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None

        return NativeVisionResult(
            content=content,
            prompt_tokens=token_value("prompt_tokens"),
            completion_tokens=token_value("completion_tokens"),
            total_tokens=token_value("total_tokens"),
        )


def _target_box(case: dict[str, Any]) -> Box | None:
    raw = case.get("bbox")
    if raw is None:
        return None
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError(f"case {case.get('id')} has malformed bbox")
    return Box(*(float(value) for value in raw)).validate()


def _usage(result: NativeVisionResult) -> dict[str, int | None]:
    return {
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
    }


def _save_image(image: Image.Image, path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def run_native_bbox_zoom_case(
    *,
    client: NativeBBoxLoopbackClient,
    source: Image.Image,
    case: dict[str, Any],
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    """Run native normalized bbox grounding plus deterministic coarse-to-fine zoom."""

    target = _target_box(case)
    instruction = str(case["instruction"])
    started = time.perf_counter()
    error: str | None = None
    decision = "error"
    pass1_response: str | None = None
    pass2_response: str | None = None
    pass1_count: int | None = None
    pass2_count: int | None = None
    coarse_box: Box | None = None
    context_box: Box | None = None
    refined_box: Box | None = None
    point: Point | None = None
    consistency_iou: float | None = None
    usage: dict[str, Any] = {"pass1": {}, "pass2": {}}

    try:
        first = client.detect(image_data_uri=_image_data_uri(source), target=instruction)
        pass1_response = first.content
        usage["pass1"] = _usage(first)
        first_detections = parse_native_bbox_response(first.content)
        pass1_count = len(first_detections)

        if len(first_detections) == 0:
            decision = "absent"
        elif len(first_detections) > 1:
            decision = "ambiguous-pass1"
        else:
            coarse_box = normalized_box_to_pixels(
                first_detections[0].bbox,
                source.width,
                source.height,
            )
            context_box = _context_box(coarse_box, source.width, source.height)
            plan = plan_mark_grid_crop(
                context_box,
                image_width=source.width,
                image_height=source.height,
                min_short_side=512,
            )
            crop = crop_source_image(source, context_box)
            if crop.size != (plan.output_width, plan.output_height):
                crop = crop.resize((plan.output_width, plan.output_height), Image.Resampling.LANCZOS)
            _save_image(
                crop,
                artifact_dir / str(case["id"]) / "native-bbox-pass2-crop.png"
                if artifact_dir is not None
                else None,
            )

            second = client.detect(image_data_uri=_image_data_uri(crop), target=instruction)
            pass2_response = second.content
            usage["pass2"] = _usage(second)
            second_detections = parse_native_bbox_response(second.content)
            pass2_count = len(second_detections)

            if len(second_detections) == 0:
                decision = "refinement-abstain"
            elif len(second_detections) > 1:
                decision = "ambiguous-pass2"
            else:
                local_box = normalized_box_to_pixels(
                    second_detections[0].bbox,
                    plan.output_width,
                    plan.output_height,
                )
                refined_box = map_box_from_crop(local_box, plan)
                consistency_iou = box_iou(coarse_box, refined_box)
                if consistency_iou <= 0.0:
                    decision = "inconsistent"
                    refined_box = None
                else:
                    decision = "accepted"
                    point = box_center(refined_box)
    except (VisionProviderError, ValueError, OSError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    latency = time.perf_counter() - started
    score = asdict(
        score_grounding(
            target_box=target,
            predicted_point=point,
            predicted_box=refined_box,
        )
    )
    return {
        "case_id": case["id"],
        "kind": case["kind"],
        "instruction": instruction,
        "method": "native_bbox_450m_zoom",
        "latency_seconds": round(latency, 4),
        "decision": decision,
        "pass1_response": pass1_response,
        "pass1_detection_count": pass1_count,
        "coarse_box": asdict(coarse_box) if coarse_box is not None else None,
        "context_box": asdict(context_box) if context_box is not None else None,
        "pass2_response": pass2_response,
        "pass2_detection_count": pass2_count,
        "refined_box": asdict(refined_box) if refined_box is not None else None,
        "coarse_refined_iou": consistency_iou,
        "prediction_point": asdict(point) if point is not None else None,
        "parse_error": error,
        "score": score,
        "usage": usage,
    }
