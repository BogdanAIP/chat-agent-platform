"""Stage 25 deterministic local-vision adapter primitives."""

from .mark_grid import (
    DEFAULT_CROP_SHORT_SIDE,
    DEFAULT_GRID_SIZE,
    Box,
    CropPlan,
    MarkGridError,
    Point,
    box_center,
    box_from_extremity_cells,
    cell_bounds,
    cell_id_at_point,
    cell_row_col,
    map_box_from_crop,
    map_point_from_crop,
    normalize_box,
    normalize_point,
    plan_proportional_crop,
)

__all__ = [
    "DEFAULT_CROP_SHORT_SIDE",
    "DEFAULT_GRID_SIZE",
    "Box",
    "CropPlan",
    "MarkGridError",
    "Point",
    "box_center",
    "box_from_extremity_cells",
    "cell_bounds",
    "cell_id_at_point",
    "cell_row_col",
    "map_box_from_crop",
    "map_point_from_crop",
    "normalize_box",
    "normalize_point",
    "plan_proportional_crop",
]
