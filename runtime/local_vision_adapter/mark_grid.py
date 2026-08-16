"""Deterministic geometry primitives for Stage 25 Mark-Grid grounding.

This module intentionally contains no model/runtime logic and no image-rendering
backend. It defines the coordinate contract that an overlay renderer and a VLM
provider can share without coupling the product surface to either implementation.

Two crop policies are kept explicit:

* ``plan_mark_grid_crop`` mirrors the published reference implementation's
  ``enlarge=True`` behavior: preserve aspect ratio and upscale only when the
  crop's shorter side is below 512 px. It never shrinks an already-large crop.
* ``plan_proportional_crop`` resizes the shorter side to an exact requested
  value and is retained as a separate experimental policy for later A/B tests.

The reference Mark-Grid runner asks for four extremity IDs but then de-duplicates
those IDs and takes the union of every selected cell. ``box_from_selected_cells``
implements that measured/reference behavior; ``box_from_extremity_cells`` keeps
the stricter ordered interpretation available for validation experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


DEFAULT_GRID_SIZE = 8
DEFAULT_CROP_SHORT_SIDE = 512


class MarkGridError(ValueError):
    """Raised when a Mark-Grid geometry request is malformed or inconsistent."""


@dataclass(frozen=True)
class Box:
    """Axis-aligned box in source-image pixel coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def validate(self) -> "Box":
        values = (self.x1, self.y1, self.x2, self.y2)
        if not all(math.isfinite(value) for value in values):
            raise MarkGridError("box coordinates must be finite")
        if self.x1 < 0 or self.y1 < 0:
            raise MarkGridError("box coordinates must be non-negative")
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise MarkGridError("box must have positive width and height")
        return self


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class CropPlan:
    """A source ROI plus the proportional size used for the rendered crop."""

    source_box: Box
    output_width: int
    output_height: int

    @property
    def scale_x(self) -> float:
        return self.output_width / self.source_box.width

    @property
    def scale_y(self) -> float:
        return self.output_height / self.source_box.height


@dataclass(frozen=True)
class TwoPassMarkGridResult:
    """Deterministic geometry produced by a two-pass Mark-Grid prediction."""

    first_roi: Box
    crop_plan: CropPlan
    second_local_roi: Box
    source_roi: Box
    point: Point


def _validate_image_size(width: int | float, height: int | float) -> tuple[float, float]:
    width_f = float(width)
    height_f = float(height)
    if not math.isfinite(width_f) or not math.isfinite(height_f):
        raise MarkGridError("image dimensions must be finite")
    if width_f <= 0 or height_f <= 0:
        raise MarkGridError("image dimensions must be positive")
    return width_f, height_f


def _validate_grid_size(grid_size: int) -> int:
    if isinstance(grid_size, bool) or not isinstance(grid_size, int):
        raise MarkGridError("grid_size must be an integer")
    if grid_size < 2 or grid_size > 64:
        raise MarkGridError("grid_size must be between 2 and 64")
    return grid_size


def _validate_cell_id(cell_id: int, grid_size: int) -> int:
    if isinstance(cell_id, bool) or not isinstance(cell_id, int):
        raise MarkGridError("cell ID must be an integer")
    max_id = grid_size * grid_size - 1
    if cell_id < 0 or cell_id > max_id:
        raise MarkGridError(f"cell ID must be between 0 and {max_id}")
    return cell_id


def _validate_four_mark_ids(mark_ids: Sequence[int], grid_size: int) -> tuple[int, int, int, int]:
    if isinstance(mark_ids, (str, bytes)):
        raise MarkGridError("mark IDs must be a sequence of four integers")
    values = tuple(mark_ids)
    if len(values) != 4:
        raise MarkGridError("Mark-Grid response must contain exactly four cell IDs")
    return tuple(_validate_cell_id(value, grid_size) for value in values)  # type: ignore[return-value]


def cell_row_col(cell_id: int, grid_size: int = DEFAULT_GRID_SIZE) -> tuple[int, int]:
    """Return the row/column for a zero-based, row-major grid cell ID."""

    grid_size = _validate_grid_size(grid_size)
    cell_id = _validate_cell_id(cell_id, grid_size)
    return divmod(cell_id, grid_size)


def cell_bounds(
    cell_id: int,
    image_width: int | float,
    image_height: int | float,
    grid_size: int = DEFAULT_GRID_SIZE,
) -> Box:
    """Return exact fractional source-image bounds for one row-major grid cell."""

    width, height = _validate_image_size(image_width, image_height)
    grid_size = _validate_grid_size(grid_size)
    row, column = cell_row_col(cell_id, grid_size)

    return Box(
        x1=width * column / grid_size,
        y1=height * row / grid_size,
        x2=width * (column + 1) / grid_size,
        y2=height * (row + 1) / grid_size,
    )


def cell_id_at_point(
    x: int | float,
    y: int | float,
    image_width: int | float,
    image_height: int | float,
    grid_size: int = DEFAULT_GRID_SIZE,
) -> int:
    """Return the row-major cell containing a source-image point."""

    width, height = _validate_image_size(image_width, image_height)
    grid_size = _validate_grid_size(grid_size)
    x_f = float(x)
    y_f = float(y)
    if not math.isfinite(x_f) or not math.isfinite(y_f):
        raise MarkGridError("point coordinates must be finite")
    if x_f < 0 or y_f < 0 or x_f > width or y_f > height:
        raise MarkGridError("point must be inside the image")

    # Treat the outer right/bottom edge as belonging to the final cell.
    column = min(grid_size - 1, int(x_f / width * grid_size))
    row = min(grid_size - 1, int(y_f / height * grid_size))
    return row * grid_size + column


def box_from_selected_cells(
    cell_ids: Iterable[int],
    *,
    image_width: int | float,
    image_height: int | float,
    grid_size: int = DEFAULT_GRID_SIZE,
    padding_cells: float = 0.0,
) -> Box:
    """Return the union of selected cells, matching the reference runner.

    The paper prompt asks for left/top/right/bottom extremity IDs. The public
    reference code converts those predictions to a set and then unions the full
    bounds of every selected cell. Duplicated IDs are therefore valid.
    """

    width, height = _validate_image_size(image_width, image_height)
    grid_size = _validate_grid_size(grid_size)

    if isinstance(cell_ids, (str, bytes)):
        raise MarkGridError("cell_ids must be an iterable of integers")
    ids = tuple(cell_ids)
    if not ids:
        raise MarkGridError("at least one selected cell is required")

    unique_ids = tuple(dict.fromkeys(_validate_cell_id(cell_id, grid_size) for cell_id in ids))
    bounds = [cell_bounds(cell_id, width, height, grid_size) for cell_id in unique_ids]

    if not math.isfinite(float(padding_cells)) or padding_cells < 0:
        raise MarkGridError("padding_cells must be a finite non-negative number")

    cell_width = width / grid_size
    cell_height = height / grid_size
    x1 = min(box.x1 for box in bounds) - padding_cells * cell_width
    y1 = min(box.y1 for box in bounds) - padding_cells * cell_height
    x2 = max(box.x2 for box in bounds) + padding_cells * cell_width
    y2 = max(box.y2 for box in bounds) + padding_cells * cell_height

    return Box(
        x1=max(0.0, x1),
        y1=max(0.0, y1),
        x2=min(width, x2),
        y2=min(height, y2),
    ).validate()


def box_from_extremity_cells(
    *,
    left_cell: int,
    top_cell: int,
    right_cell: int,
    bottom_cell: int,
    image_width: int | float,
    image_height: int | float,
    grid_size: int = DEFAULT_GRID_SIZE,
    padding_cells: float = 0.0,
) -> Box:
    """Build a strict ordered ROI from four Mark-Grid extremity cell IDs.

    Only the column of the left/right cells and the row of the top/bottom cells
    define the ROI. This is useful as a validation/experimental policy. The
    published reference runner itself uses ``box_from_selected_cells``-style
    union semantics after de-duplicating the four predictions.
    """

    width, height = _validate_image_size(image_width, image_height)
    grid_size = _validate_grid_size(grid_size)

    left_row, left_col = cell_row_col(left_cell, grid_size)
    top_row, top_col = cell_row_col(top_cell, grid_size)
    right_row, right_col = cell_row_col(right_cell, grid_size)
    bottom_row, bottom_col = cell_row_col(bottom_cell, grid_size)

    # Keep these variables explicit so debug output can preserve the
    # four-extremity semantics even though only one axis from each ID is used.
    _ = (left_row, top_col, right_row, bottom_col)

    if left_col > right_col:
        raise MarkGridError("left extremity is to the right of the right extremity")
    if top_row > bottom_row:
        raise MarkGridError("top extremity is below the bottom extremity")

    if not math.isfinite(float(padding_cells)) or padding_cells < 0:
        raise MarkGridError("padding_cells must be a finite non-negative number")

    cell_width = width / grid_size
    cell_height = height / grid_size

    x1 = left_col * cell_width - padding_cells * cell_width
    x2 = (right_col + 1) * cell_width + padding_cells * cell_width
    y1 = top_row * cell_height - padding_cells * cell_height
    y2 = (bottom_row + 1) * cell_height + padding_cells * cell_height

    return Box(
        x1=max(0.0, x1),
        y1=max(0.0, y1),
        x2=min(width, x2),
        y2=min(height, y2),
    ).validate()


def _validated_crop_box(
    source_box: Box,
    *,
    image_width: int | float,
    image_height: int | float,
) -> tuple[Box, float, float]:
    width, height = _validate_image_size(image_width, image_height)
    source_box = source_box.validate()
    if source_box.x2 > width or source_box.y2 > height:
        raise MarkGridError("source crop extends outside the image")
    return source_box, width, height


def plan_mark_grid_crop(
    source_box: Box,
    *,
    image_width: int | float,
    image_height: int | float,
    min_short_side: int = DEFAULT_CROP_SHORT_SIDE,
) -> CropPlan:
    """Plan the reference Mark-Grid ``enlarge=True`` crop behavior.

    If the shorter crop side is below ``min_short_side``, upscale proportionally
    until that side reaches the minimum. Otherwise preserve the crop dimensions;
    importantly, this function does not downscale an already-large crop.
    """

    source_box, _, _ = _validated_crop_box(
        source_box,
        image_width=image_width,
        image_height=image_height,
    )
    if (
        isinstance(min_short_side, bool)
        or not isinstance(min_short_side, int)
        or min_short_side <= 0
    ):
        raise MarkGridError("min_short_side must be a positive integer")

    scale = max(1.0, min_short_side / min(source_box.width, source_box.height))
    output_width = max(1, int(round(source_box.width * scale)))
    output_height = max(1, int(round(source_box.height * scale)))

    return CropPlan(
        source_box=source_box,
        output_width=output_width,
        output_height=output_height,
    )


def plan_proportional_crop(
    source_box: Box,
    *,
    image_width: int | float,
    image_height: int | float,
    short_side: int = DEFAULT_CROP_SHORT_SIDE,
) -> CropPlan:
    """Experimental exact-short-side resize policy.

    Unlike ``plan_mark_grid_crop``, this may downscale a crop whose shorter side
    is already larger than ``short_side``. Keep it separate so A/B tests cannot
    accidentally change the evidence-backed Mark-Grid baseline.
    """

    source_box, _, _ = _validated_crop_box(
        source_box,
        image_width=image_width,
        image_height=image_height,
    )
    if isinstance(short_side, bool) or not isinstance(short_side, int) or short_side <= 0:
        raise MarkGridError("short_side must be a positive integer")

    scale = short_side / min(source_box.width, source_box.height)
    output_width = max(1, int(round(source_box.width * scale)))
    output_height = max(1, int(round(source_box.height * scale)))

    return CropPlan(
        source_box=source_box,
        output_width=output_width,
        output_height=output_height,
    )


def map_point_from_crop(point: Point, plan: CropPlan) -> Point:
    """Map a point from rendered-crop pixels back to source-image pixels."""

    x = float(point.x)
    y = float(point.y)
    if not math.isfinite(x) or not math.isfinite(y):
        raise MarkGridError("crop point coordinates must be finite")
    if x < 0 or y < 0 or x > plan.output_width or y > plan.output_height:
        raise MarkGridError("crop point lies outside the rendered crop")

    return Point(
        x=plan.source_box.x1 + (x / plan.output_width) * plan.source_box.width,
        y=plan.source_box.y1 + (y / plan.output_height) * plan.source_box.height,
    )


def map_box_from_crop(local_box: Box, plan: CropPlan) -> Box:
    """Map a crop-local box back to source-image pixel coordinates."""

    local_box = local_box.validate()
    if local_box.x2 > plan.output_width or local_box.y2 > plan.output_height:
        raise MarkGridError("crop-local box extends outside the rendered crop")

    top_left = map_point_from_crop(Point(local_box.x1, local_box.y1), plan)
    bottom_right = map_point_from_crop(Point(local_box.x2, local_box.y2), plan)
    return Box(top_left.x, top_left.y, bottom_right.x, bottom_right.y).validate()


def two_pass_mark_grid_result(
    *,
    first_mark_ids: Sequence[int],
    second_mark_ids: Sequence[int],
    image_width: int | float,
    image_height: int | float,
    grid_size: int = DEFAULT_GRID_SIZE,
    min_short_side: int = DEFAULT_CROP_SHORT_SIDE,
) -> TwoPassMarkGridResult:
    """Resolve two four-ID Mark-Grid passes to a source-image point.

    This mirrors the reference runner at the geometry-contract level:

    1. require four predicted IDs per pass (duplicates allowed);
    2. de-duplicate and union all selected cells;
    3. crop the first-pass ROI;
    4. upscale only when the crop's short side is below 512 px;
    5. union second-pass cells on the rendered crop;
    6. map that ROI back to source coordinates and return its center.

    Rendering details such as line width/font and the reference implementation's
    integer/ceil behavior are intentionally left to the overlay renderer and its
    fixture-level compatibility tests.
    """

    width, height = _validate_image_size(image_width, image_height)
    grid_size = _validate_grid_size(grid_size)
    first_ids = _validate_four_mark_ids(first_mark_ids, grid_size)
    second_ids = _validate_four_mark_ids(second_mark_ids, grid_size)

    first_roi = box_from_selected_cells(
        first_ids,
        image_width=width,
        image_height=height,
        grid_size=grid_size,
    )
    crop_plan = plan_mark_grid_crop(
        first_roi,
        image_width=width,
        image_height=height,
        min_short_side=min_short_side,
    )
    second_local_roi = box_from_selected_cells(
        second_ids,
        image_width=crop_plan.output_width,
        image_height=crop_plan.output_height,
        grid_size=grid_size,
    )
    source_roi = map_box_from_crop(second_local_roi, crop_plan)
    point = box_center(source_roi)

    return TwoPassMarkGridResult(
        first_roi=first_roi,
        crop_plan=crop_plan,
        second_local_roi=second_local_roi,
        source_roi=source_roi,
        point=point,
    )


def box_center(box: Box) -> Point:
    box = box.validate()
    return Point((box.x1 + box.x2) / 2.0, (box.y1 + box.y2) / 2.0)


def normalize_point(point: Point, image_width: int | float, image_height: int | float) -> Point:
    width, height = _validate_image_size(image_width, image_height)
    if point.x < 0 or point.y < 0 or point.x > width or point.y > height:
        raise MarkGridError("point must be inside the image before normalization")
    return Point(point.x / width, point.y / height)


def normalize_box(box: Box, image_width: int | float, image_height: int | float) -> Box:
    width, height = _validate_image_size(image_width, image_height)
    box = box.validate()
    if box.x2 > width or box.y2 > height:
        raise MarkGridError("box must be inside the image before normalization")
    return Box(box.x1 / width, box.y1 / height, box.x2 / width, box.y2 / height)
