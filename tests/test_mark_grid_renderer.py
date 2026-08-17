import unittest

from PIL import Image

from runtime.local_vision_adapter import (
    Box,
    crop_source_image,
    render_mark_grid,
    selected_cells_box,
)


class MarkGridRendererTests(unittest.TestCase):
    def test_full_fixture_grid_is_exact_8x8_without_enlarge(self):
        source = Image.new("RGB", (1280, 720), "white")
        rendered = render_mark_grid(source, grid_size=8, enlarge=True, color="red")

        self.assertEqual(rendered.source_width, 1280)
        self.assertEqual(rendered.source_height, 720)
        self.assertEqual(rendered.rendered_width, 1280)
        self.assertEqual(rendered.rendered_height, 720)
        self.assertEqual(rendered.resize_ratio, 1.0)
        self.assertEqual(len(rendered.cell_bounds), 64)
        self.assertEqual(rendered.cell_bounds[0], Box(0.0, 0.0, 160.0, 90.0))
        self.assertEqual(rendered.cell_bounds[63], Box(1120.0, 630.0, 1280.0, 720.0))

        # Reference grid lines are two-pixel red rectangles.
        self.assertGreater(rendered.image.getpixel((0, 0))[0], 200)
        self.assertLess(rendered.image.getpixel((0, 0))[1], 100)
        self.assertLess(rendered.image.getpixel((0, 0))[2], 100)

    def test_reference_enlarge_uses_short_side_512_and_truncates_long_side(self):
        source = Image.new("RGB", (160, 90), "white")
        rendered = render_mark_grid(source, grid_size=8, enlarge=True, color="red")

        expected_ratio = 512 / 90
        self.assertAlmostEqual(rendered.resize_ratio, expected_ratio)
        self.assertEqual(rendered.rendered_height, 512)
        self.assertEqual(rendered.rendered_width, int(160 * expected_ratio))
        self.assertEqual(rendered.rendered_width, 910)

    def test_reference_cell_bounds_use_ceil_and_pre_enlarge_coordinates(self):
        source = Image.new("RGB", (160, 90), "white")
        rendered = render_mark_grid(source, grid_size=8, enlarge=True, color="red")

        # Rendered width is 910, so ceil(910 / 8) == 114. The public
        # implementation divides cell coordinates by the nominal resize ratio.
        ratio = 512 / 90
        expected = Box(
            7 * 114 / ratio,
            7 * 64 / ratio,
            8 * 114 / ratio,
            8 * 64 / ratio,
        )
        actual = rendered.cell_bounds[63]
        self.assertAlmostEqual(actual.x1, expected.x1)
        self.assertAlmostEqual(actual.y1, expected.y1)
        self.assertAlmostEqual(actual.x2, expected.x2)
        self.assertAlmostEqual(actual.y2, expected.y2)
        self.assertGreater(actual.x2, 160.0)  # faithful reference overhang
        self.assertEqual(actual.y2, 90.0)

    def test_selected_cell_union_deduplicates_like_reference_runner(self):
        source = Image.new("RGB", (1280, 720), "white")
        rendered = render_mark_grid(source, grid_size=8, enlarge=False, color="red")

        single = selected_cells_box([63, 63, 63, 63], rendered)
        self.assertEqual(single, Box(1120.0, 630.0, 1280.0, 720.0))

        union = selected_cells_box([17, 10, 20, 35], rendered)
        self.assertEqual(union, Box(160.0, 90.0, 800.0, 450.0))

    def test_crop_source_image_keeps_pillow_out_of_bounds_semantics(self):
        source = Image.new("RGB", (20, 10), "white")
        crop = crop_source_image(source, Box(15.0, 5.0, 25.0, 15.0))
        self.assertEqual(crop.size, (10, 10))
        self.assertEqual(crop.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(crop.getpixel((9, 9)), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
