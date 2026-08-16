"""Deterministic geometry primitives for Stage 25 Mark-Grid grounding.

This module intentionally contains no model/runtime logic and no image-rendering
backend.  It defines the coordinate contract that an overlay renderer and a VLM
provider can share without coupling the product surface to either implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


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
    """A source ROI plus the proportional size used for the magnified crop."""

    source_box: Box
    output_width: int
    output_height: int

    @property
    def scale_x(self) -> float:
        return self.output_width / self.source_box.width

    @property
    def scale_y(self) -> float:
        return self.output_height / self.source_box.height


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
    """Build a conservative ROI from four Mark-Grid extremity cell IDs.

    Only the column of the left/right cells and the row of the top/bottom cells
    define the ROI.  This matches the intended semantics of predicting the grid
    cells that contain the target's four spatial extremities.
    """

    width, height = _validate_image_size(image_width, image_height)
    grid_size = _validate_grid_size(grid_size)

    left_row, left_col = cell_row_col(left_cell, grid_size)
    top_row, top_col = cell_row_col(top_cell, grid_size)
    right_row, right_col = cell_row_col(right_cell, grid_size)
    bottom_row, bottom_col = cell_row_col(bottom_cell, grid_size)

    # Keep these variables explicit so callers/debug output can preserve the
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


def plan_proportional_crop(
    source_box: Box,
    *,
    image_width: int | float,
    image_height: int | float,
    short_side: int = DEFAULT_CROP_SHORT_SIDE,
) -> CropPlan:
    """Validate a source ROI and plan proportional resize to ``short_side`` px."""

    width, height = _validate_image_size(image_width, image_height)
    source_box = source_box.validate()

    if source_box.x2 > width or source_box.y2 > height:
        raise MarkGridError("source crop extends outside the image")
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
    """Map a point from magnified-crop pixels back to source-image pixels."""

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
