import unittest

from runtime.local_vision_adapter import (
    Box,
    MarkGridError,
    Point,
    box_center,
    box_from_extremity_cells,
    box_from_selected_cells,
    cell_bounds,
    cell_id_at_point,
    cell_row_col,
    map_box_from_crop,
    map_point_from_crop,
    normalize_box,
    normalize_point,
    plan_mark_grid_crop,
    plan_proportional_crop,
    two_pass_mark_grid_result,
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

    def test_selected_cells_match_reference_union_semantics(self):
        roi = box_from_selected_cells(
            [17, 10, 20, 35],
            image_width=1920,
            image_height=1080,
        )

        self.assertEqual(roi, Box(240.0, 135.0, 1200.0, 675.0))

        # Duplicates are allowed because the reference runner converts the
        # four model outputs to a set before unioning cell bounds.
        one_cell = box_from_selected_cells(
            [63, 63, 63, 63],
            image_width=1280,
            image_height=720,
        )
        self.assertEqual(one_cell, Box(1120.0, 630.0, 1280.0, 720.0))

    def test_extremity_cells_build_strict_ordered_roi(self):
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

    def test_mark_grid_crop_does_not_shrink_large_roi(self):
        roi = Box(240.0, 135.0, 1200.0, 675.0)  # 960 x 540
        plan = plan_mark_grid_crop(
            roi,
            image_width=1920,
            image_height=1080,
        )

        self.assertEqual(plan.output_width, 960)
        self.assertEqual(plan.output_height, 540)

    def test_mark_grid_crop_upscales_small_roi_to_min_short_side(self):
        roi = Box(1120.0, 630.0, 1280.0, 720.0)  # 160 x 90
        plan = plan_mark_grid_crop(
            roi,
            image_width=1280,
            image_height=720,
        )

        self.assertEqual(plan.output_height, 512)
        self.assertEqual(plan.output_width, 910)
        self.assertAlmostEqual(
            plan.output_width / plan.output_height,
            roi.width / roi.height,
            places=3,
        )

    def test_experimental_exact_short_side_policy_remains_separate(self):
        roi = Box(240.0, 135.0, 1200.0, 675.0)  # 960 x 540
        plan = plan_proportional_crop(
            roi,
            image_width=1920,
            image_height=1080,
            short_side=512,
        )

        self.assertEqual(plan.output_height, 512)
        self.assertEqual(plan.output_width, 910)

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

    def test_two_pass_mark_grid_maps_second_pass_back_to_source(self):
        result = two_pass_mark_grid_result(
            first_mark_ids=[63, 63, 63, 63],
            second_mark_ids=[27, 27, 27, 27],
            image_width=1280,
            image_height=720,
        )

        self.assertEqual(result.first_roi, Box(1120.0, 630.0, 1280.0, 720.0))
        self.assertEqual(result.crop_plan.output_width, 910)
        self.assertEqual(result.crop_plan.output_height, 512)
        self.assertAlmostEqual(result.source_roi.x1, 1180.0)
        self.assertAlmostEqual(result.source_roi.y1, 663.75)
        self.assertAlmostEqual(result.source_roi.x2, 1200.0)
        self.assertAlmostEqual(result.source_roi.y2, 675.0)
        self.assertAlmostEqual(result.point.x, 1190.0)
        self.assertAlmostEqual(result.point.y, 669.375)

    def test_two_pass_mark_grid_requires_four_ids_per_pass(self):
        with self.assertRaises(MarkGridError):
            two_pass_mark_grid_result(
                first_mark_ids=[63],
                second_mark_ids=[27, 27, 27, 27],
                image_width=1280,
                image_height=720,
            )

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
