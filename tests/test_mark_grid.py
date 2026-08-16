import unittest

from runtime.local_vision_adapter import (
    Box,
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


class MarkGridGeometryTests(unittest.TestCase):
    def test_row_major_cell_ids(self):
        self.assertEqual(cell_row_col(0), (0, 0))
        self.assertEqual(cell_row_col(7), (0, 7))
        self.assertEqual(cell_row_col(8), (1, 0))
        self.assertEqual(cell_row_col(63), (7, 7))

    def test_cell_bounds_cover_source_edges(self):
        first = cell_bounds(0, 1920, 1080)
        last = cell_bounds(63, 1920, 1080)

        self.assertEqual(first, Box(0.0, 0.0, 240.0, 135.0))
        self.assertEqual(last, Box(1680.0, 945.0, 1920.0, 1080.0))

    def test_point_to_cell_includes_outer_right_bottom_edge(self):
        self.assertEqual(cell_id_at_point(0, 0, 1920, 1080), 0)
        self.assertEqual(cell_id_at_point(1919.9, 1079.9, 1920, 1080), 63)
        self.assertEqual(cell_id_at_point(1920, 1080, 1920, 1080), 63)

    def test_extremity_cells_build_conservative_roi(self):
        roi = box_from_extremity_cells(
            left_cell=17,   # row 2, col 1
            top_cell=10,    # row 1, col 2
            right_cell=20,  # row 2, col 4
            bottom_cell=35, # row 4, col 3
            image_width=1920,
            image_height=1080,
        )

        self.assertEqual(roi, Box(240.0, 135.0, 1200.0, 675.0))

    def test_extremity_padding_clamps_to_image(self):
        roi = box_from_extremity_cells(
            left_cell=0,
            top_cell=0,
            right_cell=9,
            bottom_cell=9,
            image_width=800,
            image_height=400,
            padding_cells=1.0,
        )

        self.assertEqual(roi.x1, 0.0)
        self.assertEqual(roi.y1, 0.0)
        self.assertLessEqual(roi.x2, 800.0)
        self.assertLessEqual(roi.y2, 400.0)

    def test_reversed_extremities_are_rejected(self):
        with self.assertRaises(MarkGridError):
            box_from_extremity_cells(
                left_cell=5,
                top_cell=0,
                right_cell=2,
                bottom_cell=8,
                image_width=800,
                image_height=400,
            )

        with self.assertRaises(MarkGridError):
            box_from_extremity_cells(
                left_cell=0,
                top_cell=40,
                right_cell=7,
                bottom_cell=16,
                image_width=800,
                image_height=400,
            )

    def test_crop_plan_preserves_aspect_ratio_and_short_side(self):
        roi = Box(240.0, 135.0, 1200.0, 675.0)
        plan = plan_proportional_crop(
            roi,
            image_width=1920,
            image_height=1080,
            short_side=512,
        )

        self.assertEqual(plan.output_height, 512)
        self.assertEqual(plan.output_width, 910)
        self.assertAlmostEqual(
            plan.output_width / plan.output_height,
            roi.width / roi.height,
            places=3,
        )

    def test_crop_point_maps_back_to_source(self):
        roi = Box(240.0, 135.0, 1200.0, 675.0)
        plan = plan_proportional_crop(
            roi,
            image_width=1920,
            image_height=1080,
            short_side=512,
        )

        mapped = map_point_from_crop(
            Point(plan.output_width / 2, plan.output_height / 2),
            plan,
        )

        self.assertAlmostEqual(mapped.x, 720.0)
        self.assertAlmostEqual(mapped.y, 405.0)

    def test_crop_box_maps_back_to_source(self):
        roi = Box(100.0, 50.0, 500.0, 250.0)
        plan = plan_proportional_crop(
            roi,
            image_width=1000,
            image_height=500,
            short_side=500,
        )

        local = Box(
            plan.output_width * 0.25,
            plan.output_height * 0.25,
            plan.output_width * 0.75,
            plan.output_height * 0.75,
        )
        mapped = map_box_from_crop(local, plan)

        self.assertAlmostEqual(mapped.x1, 200.0)
        self.assertAlmostEqual(mapped.y1, 100.0)
        self.assertAlmostEqual(mapped.x2, 400.0)
        self.assertAlmostEqual(mapped.y2, 200.0)

    def test_normalized_result_contract(self):
        box = Box(192.0, 108.0, 960.0, 540.0)
        point = box_center(box)

        normalized_box = normalize_box(box, 1920, 1080)
        normalized_point = normalize_point(point, 1920, 1080)

        self.assertEqual(normalized_box, Box(0.1, 0.1, 0.5, 0.5))
        self.assertAlmostEqual(normalized_point.x, 0.3)
        self.assertAlmostEqual(normalized_point.y, 0.3)

    def test_invalid_cell_and_out_of_bounds_local_box_are_rejected(self):
        with self.assertRaises(MarkGridError):
            cell_bounds(64, 1920, 1080)

        plan = plan_proportional_crop(
            Box(0.0, 0.0, 400.0, 200.0),
            image_width=800,
            image_height=400,
        )
        with self.assertRaises(MarkGridError):
            map_box_from_crop(
                Box(0.0, 0.0, plan.output_width + 1.0, 10.0),
                plan,
            )


if __name__ == "__main__":
    unittest.main()
