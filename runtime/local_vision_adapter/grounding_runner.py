"""Executable Direct-vs-Mark-Grid benchmark logic for Stage 25.

This module still does not own model lifecycle. It assumes an already-running
bounded local provider and evaluates one source screenshot against authoritative
fixture cases. Intermediate Mark-Grid images can be saved for auditability.
"""

from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
import json
from pathlib import Path
import time
from typing import Any, Iterable

from PIL import Image, ImageDraw

from .benchmark import score_grounding
from .mark_grid import Box, Point, box_center
from .provider import (
    LlamaCppLoopbackClient,
    VisionProviderError,
    build_direct_point_prompt,
    build_mark_grid_prompt,
    direct_point_response_schema,
    encode_image_data_uri,
    mark_grid_response_schema,
    parse_direct_point_response,
    parse_mark_grid_response,
)
from .renderer import crop_source_image, render_mark_grid, selected_cells_box


def _image_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return encode_image_data_uri(buffer.getvalue(), "image/png")


def _target_box(case: dict[str, Any]) -> Box | None:
    raw = case.get("bbox")
    if raw is None:
        return None
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError(f"case {case.get('id')} has malformed bbox")
    return Box(*(float(value) for value in raw)).validate()


def _score_dict(target: Box | None, point: Point | None) -> dict[str, Any]:
    return asdict(score_grounding(target_box=target, predicted_point=point))


def _save_image(image: Image.Image, path: Path | None) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def run_direct_case(
    *,
    client: LlamaCppLoopbackClient,
    source: Image.Image,
    case: dict[str, Any],
) -> dict[str, Any]:
    target = _target_box(case)
    prompt = build_direct_point_prompt(
        str(case["instruction"]),
        source.width,
        source.height,
    )

    started = time.perf_counter()
    raw_content: str | None = None
    error: str | None = None
    point: Point | None = None
    usage: dict[str, int | None] = {}

    try:
        response = client.chat_with_image(
            image_data_uri=_image_data_uri(source),
            prompt=prompt,
            max_tokens=32,
            response_schema=direct_point_response_schema(),
        )
        raw_content = response.content
        usage = {
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "total_tokens": response.total_tokens,
        }
        point = parse_direct_point_response(
            raw_content,
            image_width=source.width,
            image_height=source.height,
        )
    except (VisionProviderError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    latency = time.perf_counter() - started
    result = {
        "case_id": case["id"],
        "kind": case["kind"],
        "instruction": case["instruction"],
        "method": "direct",
        "latency_seconds": round(latency, 4),
        "raw_response": raw_content,
        "parse_error": error,
        "prediction_point": asdict(point) if point is not None else None,
        "score": _score_dict(target, point),
        "usage": usage,
    }
    return result


def run_mark_grid_case(
    *,
    client: LlamaCppLoopbackClient,
    source: Image.Image,
    case: dict[str, Any],
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the public reference method's two-pass geometry and image ordering."""

    target = _target_box(case)
    started = time.perf_counter()
    error: str | None = None
    first_response: str | None = None
    second_response: str | None = None
    first_ids: tuple[int, int, int, int] | None = None
    second_ids: tuple[int, int, int, int] | None = None
    coarse_roi: Box | None = None
    final_roi: Box | None = None
    point: Point | None = None
    usage: dict[str, Any] = {"pass1": {}, "pass2": {}}

    try:
        first_grid = render_mark_grid(source, grid_size=8, enlarge=True, color="red")
        if artifact_dir is not None:
            _save_image(first_grid.image, artifact_dir / str(case["id"]) / "pass1-grid.png")

        first = client.chat_with_image(
            image_data_uri=_image_data_uri(first_grid.image),
            prompt=build_mark_grid_prompt(str(case["instruction"]), 8),
            max_tokens=32,
            response_schema=mark_grid_response_schema(8),
        )
        first_response = first.content
        usage["pass1"] = {
            "prompt_tokens": first.prompt_tokens,
            "completion_tokens": first.completion_tokens,
            "total_tokens": first.total_tokens,
        }
        first_ids = parse_mark_grid_response(first_response, 8)
        coarse_roi = selected_cells_box(first_ids, first_grid)

        crop = crop_source_image(source, coarse_roi)
        second_grid = render_mark_grid(crop, grid_size=8, enlarge=True, color="red")

        overview = source.convert("RGB").copy()
        draw = ImageDraw.Draw(overview)
        draw.rectangle(
            [coarse_roi.x1, coarse_roi.y1, coarse_roi.x2, coarse_roi.y2],
            outline="red",
            width=3,
        )

        if artifact_dir is not None:
            case_dir = artifact_dir / str(case["id"])
            _save_image(overview, case_dir / "pass2-overview.png")
            _save_image(second_grid.image, case_dir / "pass2-grid.png")

        second = client.chat_with_images(
            image_data_uris=(
                _image_data_uri(overview),
                _image_data_uri(second_grid.image),
            ),
            prompt=build_mark_grid_prompt(
                str(case["instruction"]),
                8,
                refinement_with_overview=True,
            ),
            max_tokens=32,
            response_schema=mark_grid_response_schema(8),
        )
        second_response = second.content
        usage["pass2"] = {
            "prompt_tokens": second.prompt_tokens,
            "completion_tokens": second.completion_tokens,
            "total_tokens": second.total_tokens,
        }
        second_ids = parse_mark_grid_response(second_response, 8)
        local_roi = selected_cells_box(second_ids, second_grid)

        # `selected_cells_box` metadata is already expressed in pre-enlarge crop
        # coordinates, matching the reference runner's division by resize_ratio.
        final_roi = Box(
            coarse_roi.x1 + local_roi.x1,
            coarse_roi.y1 + local_roi.y1,
            coarse_roi.x1 + local_roi.x2,
            coarse_roi.y1 + local_roi.y2,
        ).validate()
        point = box_center(final_roi)
    except (VisionProviderError, ValueError, OSError) as exc:
        error = f"{type(exc).__name__}: {exc}"

    latency = time.perf_counter() - started
    return {
        "case_id": case["id"],
        "kind": case["kind"],
        "instruction": case["instruction"],
        "method": "mark_grid_8x8_two_pass",
        "latency_seconds": round(latency, 4),
        "pass1_response": first_response,
        "pass1_ids": list(first_ids) if first_ids is not None else None,
        "coarse_roi": asdict(coarse_roi) if coarse_roi is not None else None,
        "pass2_response": second_response,
        "pass2_ids": list(second_ids) if second_ids is not None else None,
        "final_roi": asdict(final_roi) if final_roi is not None else None,
        "prediction_point": asdict(point) if point is not None else None,
        "parse_error": error,
        "score": _score_dict(target, point),
        "usage": usage,
    }


def summarize_results(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(results)
    if not rows:
        raise ValueError("benchmark results cannot be empty")

    present = [row for row in rows if row["score"]["target_present"]]
    absent = [row for row in rows if not row["score"]["target_present"]]

    point_hits = sum(1 for row in present if row["score"]["point_hit"] is True)
    false_clicks = sum(1 for row in rows if row["score"]["false_click"] is True)
    abstains = sum(1 for row in rows if row["score"]["abstained"] is True)
    malformed = sum(1 for row in rows if row.get("parse_error"))
    correct_absent_abstains = sum(
        1 for row in absent if row["score"]["abstained"] and not row["score"]["false_click"]
    )

    return {
        "case_count": len(rows),
        "present_target_count": len(present),
        "absent_target_count": len(absent),
        "point_hits": point_hits,
        "point_accuracy": point_hits / len(present) if present else None,
        "false_clicks": false_clicks,
        "false_click_rate_all_cases": false_clicks / len(rows),
        "abstains": abstains,
        "correct_absent_abstains": correct_absent_abstains,
        "malformed_or_provider_errors": malformed,
        "total_latency_seconds": round(sum(float(row["latency_seconds"]) for row in rows), 4),
        "mean_latency_seconds": round(
            sum(float(row["latency_seconds"]) for row in rows) / len(rows),
            4,
        ),
    }


def load_fixture_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("fixture metadata must contain non-empty cases")
    return cases
