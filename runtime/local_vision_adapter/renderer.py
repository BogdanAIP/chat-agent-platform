"""Pillow renderer for the Stage 25 faithful Mark-Grid benchmark.

The implementation intentionally mirrors the public `liweim/AuxiliaryReasoning`
`create_grid_mark` image transform where it matters for benchmark behavior:

* optional `enlarge=True` upsizes only when the short side is below 512 px;
* the long side uses Python `int(...)` truncation, like the reference code;
* grid cell width/height use `math.ceil(image_dimension / num_grid)`;
* IDs are zero-based, row-major and drawn at cell centers;
* cell metadata is reported in the pre-enlarge coordinate system by dividing
  rendered coordinates by the reference resize ratio.

The project does not vendor the reference repository's `arial.ttf`. On Windows,
the renderer uses the installed system Arial font. A non-Windows fallback is
provided for deterministic unit testing, but target acceptance remains Windows.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .mark_grid import Box, DEFAULT_CROP_SHORT_SIDE, DEFAULT_GRID_SIZE, MarkGridError


@dataclass(frozen=True)
class RenderedMarkGrid:
    image: Image.Image
    cell_bounds: dict[int, Box]
    resize_ratio: float
    source_width: int
    source_height: int
    rendered_width: int
    rendered_height: int


def _validate_grid_size(grid_size: int) -> int:
    if isinstance(grid_size, bool) or not isinstance(grid_size, int):
        raise MarkGridError("grid_size must be an integer")
    if grid_size < 2 or grid_size > 64:
        raise MarkGridError("grid_size must be between 2 and 64")
    return grid_size


def _resolve_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_size = max(1, int(font_size))

    candidates: list[Path] = []
    windir = os.environ.get("WINDIR")
    if windir:
        candidates.extend(
            [
                Path(windir) / "Fonts" / "arial.ttf",
                Path(windir) / "Fonts" / "Arial.ttf",
            ]
        )

    # Pillow installations commonly expose DejaVu Sans by font name. It is only
    # a portability fallback; the Windows benchmark path should resolve Arial.
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), font_size)

    try:
        return ImageFont.truetype("DejaVuSans.ttf", font_size)
    except OSError:
        return ImageFont.load_default()


def _validate_image(image: Image.Image) -> Image.Image:
    if not isinstance(image, Image.Image):
        raise MarkGridError("image must be a Pillow Image")
    if image.width <= 0 or image.height <= 0:
        raise MarkGridError("image dimensions must be positive")
    if image.mode != "RGB":
        return image.convert("RGB")
    return image.copy()


def crop_source_image(image: Image.Image, source_box: Box) -> Image.Image:
    """Crop with Pillow semantics used by the reference runner.

    Coordinates must be finite/non-negative. Right/bottom may extend beyond the
    source image, matching Pillow's crop behavior (out-of-bounds area is padded).
    """

    image = _validate_image(image)
    source_box = source_box.validate()
    return image.crop((source_box.x1, source_box.y1, source_box.x2, source_box.y2))


def render_mark_grid(
    image: Image.Image,
    *,
    grid_size: int = DEFAULT_GRID_SIZE,
    enlarge: bool = False,
    min_short_side: int = DEFAULT_CROP_SHORT_SIDE,
    color: str = "red",
) -> RenderedMarkGrid:
    """Render one reference-compatible Mark-Grid pass and return cell metadata."""

    grid_size = _validate_grid_size(grid_size)
    if isinstance(min_short_side, bool) or not isinstance(min_short_side, int) or min_short_side <= 0:
        raise MarkGridError("min_short_side must be a positive integer")
    if not isinstance(color, str) or not color.strip():
        raise MarkGridError("color must be non-empty text")

    source = _validate_image(image)
    source_width, source_height = source.size

    resize_ratio = 1.0
    rendered = source
    if enlarge and min(source_width, source_height) < min_short_side:
        if source_width < source_height:
            new_width = min_short_side
            resize_ratio = new_width / source_width
            new_height = int(source_height * resize_ratio)
        else:
            new_height = min_short_side
            resize_ratio = new_height / source_height
            new_width = int(source_width * resize_ratio)
        rendered = source.resize((new_width, new_height))

    width, height = rendered.size
    output = rendered.copy()
    draw = ImageDraw.Draw(output)

    font_size = min(width, height) // grid_size // 3
    font = _resolve_font(font_size)

    grid_width = math.ceil(width / grid_size)
    grid_height = math.ceil(height / grid_size)

    id_coord: dict[int, Box] = {}
    count = 0
    for y in range(0, height, grid_height):
        for x in range(0, width, grid_width):
            id_coord[count] = Box(
                x / resize_ratio,
                y / resize_ratio,
                (x + grid_width) / resize_ratio,
                (y + grid_height) / resize_ratio,
            )

            draw.rectangle(
                [(x, y), (x + grid_width, y + grid_height)],
                outline=color,
                width=2,
            )

            text = str(count)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            center_x = x + (grid_width - text_width) // 2
            center_y = y + (grid_height - text_height) // 2
            draw.text((center_x, center_y), text, fill=color, font=font)
            count += 1

    if count != grid_size * grid_size:
        raise MarkGridError(
            f"reference grid produced {count} cells, expected {grid_size * grid_size}"
        )

    return RenderedMarkGrid(
        image=output,
        cell_bounds=id_coord,
        resize_ratio=resize_ratio,
        source_width=source_width,
        source_height=source_height,
        rendered_width=width,
        rendered_height=height,
    )


def selected_cells_box(cell_ids: Iterable[int], rendered: RenderedMarkGrid) -> Box:
    """Union selected cells exactly as the public Mark-Grid runner does."""

    if isinstance(cell_ids, (str, bytes)):
        raise MarkGridError("cell_ids must be an iterable of integers")
    ids = tuple(cell_ids)
    if not ids:
        raise MarkGridError("at least one selected cell is required")

    unique_ids: list[int] = []
    seen: set[int] = set()
    for cell_id in ids:
        if isinstance(cell_id, bool) or not isinstance(cell_id, int):
            raise MarkGridError("cell ID must be an integer")
        if cell_id not in rendered.cell_bounds:
            raise MarkGridError(f"unknown rendered cell ID: {cell_id}")
        if cell_id not in seen:
            seen.add(cell_id)
            unique_ids.append(cell_id)

    cells = [rendered.cell_bounds[cell_id] for cell_id in unique_ids]
    return Box(
        min(cell.x1 for cell in cells),
        min(cell.y1 for cell in cells),
        max(cell.x2 for cell in cells),
        max(cell.y2 for cell in cells),
    ).validate()


def render_mark_grid_file(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    *,
    grid_size: int = DEFAULT_GRID_SIZE,
    enlarge: bool = False,
    min_short_side: int = DEFAULT_CROP_SHORT_SIDE,
    color: str = "red",
) -> RenderedMarkGrid:
    """Convenience file boundary for benchmark scripts; source file is never modified."""

    input_path = Path(input_path)
    output_path = Path(output_path)
    if not input_path.is_file():
        raise MarkGridError(f"input image does not exist: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as image:
        rendered = render_mark_grid(
            image,
            grid_size=grid_size,
            enlarge=enlarge,
            min_short_side=min_short_side,
            color=color,
        )
        rendered.image.save(output_path, format="PNG")
    return rendered
