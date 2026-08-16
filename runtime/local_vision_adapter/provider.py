"""Bounded provider-neutral inference contract for Stage 25 local vision.

The public Chat surface must not expose raw model prompts, arbitrary endpoints or
provider administration. This module is an internal benchmark/adapter boundary:
it builds reviewed grounding prompts, validates responses, and can call an
already-running llama.cpp server bound to loopback.

Lifecycle/start-stop policy deliberately remains outside this module.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import math
import re
from typing import Any, Callable
from urllib import error as urllib_error
from urllib import request as urllib_request

from .mark_grid import DEFAULT_GRID_SIZE, MarkGridError, Point


class VisionProviderError(RuntimeError):
    """Raised for malformed provider requests/responses or local transport errors."""


@dataclass(frozen=True)
class VisionChatResult:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


Transport = Callable[[str, bytes, float], dict[str, Any]]


def encode_image_data_uri(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """Encode already-authorized image bytes for the local OpenAI-compatible API."""

    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        raise VisionProviderError("image_bytes must be non-empty bytes")
    allowed = {"image/png", "image/jpeg", "image/webp"}
    if mime_type not in allowed:
        raise VisionProviderError(f"unsupported image MIME type: {mime_type}")
    encoded = base64.b64encode(bytes(image_bytes)).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_direct_point_prompt(target: str, image_width: int, image_height: int) -> str:
    """Build the reviewed one-pass point-grounding benchmark prompt."""

    target = target.strip() if isinstance(target, str) else ""
    if not target:
        raise VisionProviderError("target must be non-empty text")
    if image_width <= 0 or image_height <= 0:
        raise VisionProviderError("image dimensions must be positive")

    return (
        "Locate the UI element needed to complete this instruction: "
        f"{target}\n"
        f"The source image is {image_width} pixels wide and {image_height} pixels high. "
        "The origin is the top-left corner.\n"
        "If the target is visible, return only this JSON object with source-image pixel coordinates: "
        '{"found":true,"point":[x,y]}. '
        "Choose a click point inside the target.\n"
        "If the requested target is not visible, return only: "
        '{"found":false}. '
        "Do not add prose, Markdown, or a guessed coordinate."
    )


def build_mark_grid_prompt(target: str, grid_size: int = DEFAULT_GRID_SIZE) -> str:
    """Build the faithful Mark-Grid four-ID benchmark prompt."""

    target = target.strip() if isinstance(target, str) else ""
    if not target:
        raise VisionProviderError("target must be non-empty text")
    if isinstance(grid_size, bool) or not isinstance(grid_size, int) or grid_size < 2:
        raise VisionProviderError("grid_size must be an integer >= 2")
    max_id = grid_size * grid_size - 1

    return (
        f"A UI image is overlaid with a labeled {grid_size} x {grid_size} grid in red, "
        "with each cell ID shown at its center. Determine which grid cells contain the UI element "
        f"needed to complete this instruction: {target}.\n"
        "List exactly 4 grid IDs corresponding to the leftmost, topmost, rightmost and bottommost "
        "cells that contain the object. These IDs can be identical if the object fits in one cell. "
        f"Every ID must be between 0 and {max_id}.\n"
        "Return only a JSON array in this exact shape: [left_id,top_id,right_id,bottom_id]."
    )


def _extract_json_value(text: str) -> Any:
    if not isinstance(text, str) or not text.strip():
        raise VisionProviderError("model response must be non-empty text")

    stripped = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Tolerate a small amount of provider wrapper text for benchmark diagnostics,
    # but still require exactly one parseable JSON object/array candidate.
    candidates: list[str] = []
    for opener, closer in (("{", "}"), ("[", "]")):
        start = stripped.find(opener)
        end = stripped.rfind(closer)
        if start >= 0 and end > start:
            candidates.append(stripped[start : end + 1])

    parsed: list[Any] = []
    for candidate in candidates:
        try:
            parsed.append(json.loads(candidate))
        except json.JSONDecodeError:
            continue

    if len(parsed) != 1:
        raise VisionProviderError("model response does not contain one unambiguous JSON value")
    return parsed[0]


def parse_direct_point_response(
    text: str,
    *,
    image_width: int,
    image_height: int,
) -> Point | None:
    """Parse the reviewed Direct benchmark contract into a click point or abstain."""

    if image_width <= 0 or image_height <= 0:
        raise VisionProviderError("image dimensions must be positive")
    value = _extract_json_value(text)
    if not isinstance(value, dict) or set(value) - {"found", "point"}:
        raise VisionProviderError("direct response must be a found/point JSON object")
    if not isinstance(value.get("found"), bool):
        raise VisionProviderError("direct response found must be boolean")

    if value["found"] is False:
        if "point" in value and value["point"] is not None:
            raise VisionProviderError("abstain response must not include a point")
        return None

    point = value.get("point")
    if not isinstance(point, list) or len(point) != 2:
        raise VisionProviderError("found response must contain point=[x,y]")
    if any(isinstance(component, bool) or not isinstance(component, (int, float)) for component in point):
        raise VisionProviderError("point coordinates must be numeric")

    x = float(point[0])
    y = float(point[1])
    if not math.isfinite(x) or not math.isfinite(y):
        raise VisionProviderError("point coordinates must be finite")
    if x < 0 or y < 0 or x > image_width or y > image_height:
        raise VisionProviderError("point lies outside the source image")
    return Point(x, y)


def parse_mark_grid_response(text: str, grid_size: int = DEFAULT_GRID_SIZE) -> tuple[int, int, int, int]:
    """Parse exactly four Mark-Grid IDs; duplicates remain valid."""

    if isinstance(grid_size, bool) or not isinstance(grid_size, int) or grid_size < 2:
        raise VisionProviderError("grid_size must be an integer >= 2")
    max_id = grid_size * grid_size - 1
    value = _extract_json_value(text)
    if not isinstance(value, list) or len(value) != 4:
        raise VisionProviderError("Mark-Grid response must be a JSON array of exactly four IDs")

    result: list[int] = []
    for cell_id in value:
        if isinstance(cell_id, bool) or not isinstance(cell_id, int):
            raise VisionProviderError("Mark-Grid IDs must be integers")
        if cell_id < 0 or cell_id > max_id:
            raise VisionProviderError(f"Mark-Grid ID must be between 0 and {max_id}")
        result.append(cell_id)
    return (result[0], result[1], result[2], result[3])


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


class LlamaCppLoopbackClient:
    """Small internal client for an already-running loopback llama.cpp server."""

    def __init__(
        self,
        *,
        port: int,
        timeout_seconds: float = 300.0,
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

    def chat_with_image(
        self,
        *,
        image_data_uri: str,
        prompt: str,
        max_tokens: int = 128,
    ) -> VisionChatResult:
        if not isinstance(image_data_uri, str) or not image_data_uri.startswith("data:image/"):
            raise VisionProviderError("image_data_uri must be a local data:image URI")
        if not isinstance(prompt, str) or not prompt.strip():
            raise VisionProviderError("prompt must be non-empty text")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not (1 <= max_tokens <= 1024):
            raise VisionProviderError("max_tokens must be between 1 and 1024")

        payload = {
            "model": "local",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data_uri}},
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
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

        return VisionChatResult(
            content=content,
            prompt_tokens=token_value("prompt_tokens"),
            completion_tokens=token_value("completion_tokens"),
            total_tokens=token_value("total_tokens"),
        )
