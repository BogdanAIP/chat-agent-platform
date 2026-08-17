#!/usr/bin/env python
"""Internal Stage 25.1 production visual-grounder CLI.

This process is intentionally not a generic inference endpoint.  It reads one
bounded JSON request from stdin, validates the checked-in reviewed runtime
profile, talks only to that profile's loopback llama.cpp port, and emits one
bridge-shaped resolved/abstain/error JSON result.
"""

from __future__ import annotations

import base64
import binascii
from io import BytesIO
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, UnidentifiedImageError

from runtime.local_vision_adapter.native_bbox import NativeBBoxLoopbackClient
from runtime.local_vision_adapter.production_grounder import (
    ProductionGrounderError,
    ground_png_for_browser,
)


CONFIG_PATH = REPO_ROOT / "config" / "local-vision-runtime.json"
MAX_STDIN_BYTES = 12 * 1024 * 1024
MAX_PNG_BYTES = 8 * 1024 * 1024
REVIEWED_PROFILE = "lfm25-vl-450m-f16"
REVIEWED_HOST = "127.0.0.1"
REVIEWED_PORT = 3068
ALLOWED_KINDS = frozenset(
    {
        "labeled_button",
        "icon_only",
        "visual_state",
        "repeated_similar_control",
        "tiny_target",
        "absent_target",
    }
)


class CliContractError(ValueError):
    pass


def _read_reviewed_runtime() -> dict[str, Any]:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CliContractError("reviewed-runtime-config-invalid") from exc

    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise CliContractError("reviewed-runtime-config-schema-invalid")
    if config.get("profile") != REVIEWED_PROFILE:
        raise CliContractError("reviewed-runtime-profile-mismatch")
    runtime = config.get("runtime")
    if not isinstance(runtime, dict):
        raise CliContractError("reviewed-runtime-section-invalid")
    if runtime.get("host") != REVIEWED_HOST or runtime.get("port") != REVIEWED_PORT:
        raise CliContractError("reviewed-runtime-loopback-contract-mismatch")
    return config


def _decode_request(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_STDIN_BYTES:
        raise CliContractError("request-size-invalid")
    try:
        request = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CliContractError("request-json-invalid") from exc
    if not isinstance(request, dict):
        raise CliContractError("request-must-be-object")
    if set(request) - {
        "schema_version",
        "image_base64",
        "width",
        "height",
        "coordinate_space",
        "instruction",
        "kind",
        "target_text",
    }:
        raise CliContractError("request-has-unknown-fields")
    if request.get("schema_version") != 1:
        raise CliContractError("request-schema-version-invalid")
    if request.get("coordinate_space") != "css_viewport":
        raise CliContractError("coordinate-space-must-be-css-viewport")

    for name in ("width", "height"):
        value = request.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > 16384:
            raise CliContractError(f"{name}-invalid")

    instruction = request.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip() or len(instruction) > 4096:
        raise CliContractError("instruction-invalid")
    kind = request.get("kind")
    if kind not in ALLOWED_KINDS:
        raise CliContractError("kind-not-reviewed")
    target_text = request.get("target_text")
    if target_text is not None and (
        not isinstance(target_text, str) or len(target_text) > 2048
    ):
        raise CliContractError("target-text-invalid")

    encoded = request.get("image_base64")
    if not isinstance(encoded, str) or not encoded:
        raise CliContractError("image-base64-invalid")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CliContractError("image-base64-invalid") from exc
    if not image_bytes or len(image_bytes) > MAX_PNG_BYTES:
        raise CliContractError("image-size-invalid")

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            if image.format != "PNG":
                raise CliContractError("image-must-be-png")
            actual_size = image.size
    except CliContractError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise CliContractError("image-must-be-valid-png") from exc

    if actual_size != (request["width"], request["height"]):
        raise CliContractError("image-dimensions-do-not-match-request")

    request["instruction"] = instruction.strip()
    request["target_text"] = target_text.strip() if isinstance(target_text, str) else None
    request["image_bytes"] = image_bytes
    return request


def _result_payload(result: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": result.status,
        "reason": result.reason,
    }
    if result.point is not None:
        payload["point"] = result.point
    if result.bbox is not None:
        payload["bbox"] = result.bbox
    if result.diagnostics is not None:
        payload["diagnostics"] = result.diagnostics
    return payload


def run_request(raw: bytes) -> dict[str, Any]:
    _read_reviewed_runtime()
    request = _decode_request(raw)
    client = NativeBBoxLoopbackClient(port=REVIEWED_PORT, timeout_seconds=120.0)
    result = ground_png_for_browser(
        client=client,
        image_bytes=request["image_bytes"],
        instruction=request["instruction"],
        kind=request["kind"],
        target_text=request["target_text"],
    )
    return _result_payload(result)


def main() -> int:
    raw = sys.stdin.buffer.read(MAX_STDIN_BYTES + 1)
    try:
        payload = run_request(raw)
        exit_code = 0
    except (CliContractError, ProductionGrounderError) as exc:
        payload = {
            "schema_version": 1,
            "status": "error",
            "reason": str(exc) or type(exc).__name__,
        }
        exit_code = 2
    except Exception:
        payload = {
            "schema_version": 1,
            "status": "error",
            "reason": "unexpected-grounder-error",
        }
        exit_code = 3

    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
