"""Deterministic scoring helpers for Stage 25 grounding benchmarks.

The primary ScreenSpot-style success metric is whether the predicted click point
falls inside the authoritative target box. Extra metrics are recorded so two
methods that have the same click accuracy can still be compared for geometric
quality and abstention behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from .mark_grid import Box, MarkGridError, Point, box_center


@dataclass(frozen=True)
class GroundingScore:
    """One benchmark case result independent of model/runtime provider."""

    target_present: bool
    prediction_present: bool
    abstained: bool
    point_hit: bool | None
    false_click: bool
    box_iou: float | None
    center_error_px: float | None


def _validate_point(point: Point) -> Point:
    x = float(point.x)
    y = float(point.y)
    if not math.isfinite(x) or not math.isfinite(y):
        raise MarkGridError("prediction point coordinates must be finite")
    if x < 0 or y < 0:
        raise MarkGridError("prediction point coordinates must be non-negative")
    return Point(x, y)


def point_in_box(point: Point, box: Box) -> bool:
    """Return whether a click point falls inside a target box, edges inclusive."""

    point = _validate_point(point)
    box = box.validate()
    return box.x1 <= point.x <= box.x2 and box.y1 <= point.y <= box.y2


def box_iou(first: Box, second: Box) -> float:
    """Intersection-over-union for two validated axis-aligned boxes."""

    first = first.validate()
    second = second.validate()

    inter_x1 = max(first.x1, second.x1)
    inter_y1 = max(first.y1, second.y1)
    inter_x2 = min(first.x2, second.x2)
    inter_y2 = min(first.y2, second.y2)

    inter_width = max(0.0, inter_x2 - inter_x1)
    inter_height = max(0.0, inter_y2 - inter_y1)
    intersection = inter_width * inter_height

    first_area = first.width * first.height
    second_area = second.width * second.height
    union = first_area + second_area - intersection
    if union <= 0:
        raise MarkGridError("box union must be positive")
    return intersection / union


def point_distance(first: Point, second: Point) -> float:
    first = _validate_point(first)
    second = _validate_point(second)
    return math.hypot(first.x - second.x, first.y - second.y)


def score_grounding(
    *,
    target_box: Box | None,
    predicted_point: Point | None = None,
    predicted_box: Box | None = None,
) -> GroundingScore:
    """Score one grounding attempt, including explicit abstention/absence cases.

    ``target_box=None`` represents a deliberately absent target. A prediction in
    that case is a false click; no prediction is the desired abstention.

    When only a predicted box is supplied, its center is used as the click point
    for the ScreenSpot-style point-in-target metric.
    """

    if predicted_point is not None:
        predicted_point = _validate_point(predicted_point)
    if predicted_box is not None:
        predicted_box = predicted_box.validate()

    prediction_present = predicted_point is not None or predicted_box is not None
    abstained = not prediction_present

    if target_box is None:
        return GroundingScore(
            target_present=False,
            prediction_present=prediction_present,
            abstained=abstained,
            point_hit=None,
            false_click=prediction_present,
            box_iou=None,
            center_error_px=None,
        )

    target_box = target_box.validate()
    if not prediction_present:
        return GroundingScore(
            target_present=True,
            prediction_present=False,
            abstained=True,
            point_hit=False,
            false_click=False,
            box_iou=None,
            center_error_px=None,
        )

    click_point = predicted_point
    if click_point is None and predicted_box is not None:
        click_point = box_center(predicted_box)
    assert click_point is not None

    hit = point_in_box(click_point, target_box)
    iou = box_iou(target_box, predicted_box) if predicted_box is not None else None
    center_error = point_distance(click_point, box_center(target_box))

    return GroundingScore(
        target_present=True,
        prediction_present=True,
        abstained=False,
        point_hit=hit,
        false_click=not hit,
        box_iou=iou,
        center_error_px=center_error,
    )
