import json
from pathlib import Path
import unittest

from runtime.local_vision_adapter.benchmark import (
    box_iou,
    point_in_box,
    score_grounding,
)
from runtime.local_vision_adapter.mark_grid import Box, Point


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CASE_PATH = FIXTURE_DIR / "stage25_grounding_cases.json"
HTML_PATH = FIXTURE_DIR / "stage25_grounding_fixture.html"


class GroundingBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(CASE_PATH.read_text(encoding="utf-8"))
        cls.html = HTML_PATH.read_text(encoding="utf-8")

    def test_fixture_spec_has_unique_cases_and_valid_boxes(self):
        viewport = self.spec["viewport"]
        width = viewport["width"]
        height = viewport["height"]
        ids = [case["id"] for case in self.spec["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 6)

        for case in self.spec["cases"]:
            bbox = case["bbox"]
            target_id = case["target_id"]
            if bbox is None:
                self.assertIsNone(target_id)
                continue

            self.assertIsNotNone(target_id)
            self.assertIn(f'id="{target_id}"', self.html)
            self.assertEqual(len(bbox), 4)
            x1, y1, x2, y2 = bbox
            self.assertGreaterEqual(x1, 0)
            self.assertGreaterEqual(y1, 0)
            self.assertGreater(x2, x1)
            self.assertGreater(y2, y1)
            self.assertLessEqual(x2, width)
            self.assertLessEqual(y2, height)

    def test_primary_screen_spot_style_metric_is_point_inside_target(self):
        target = Box(1056, 636, 1200, 684)
        self.assertTrue(point_in_box(Point(1128, 660), target))
        self.assertTrue(point_in_box(Point(1056, 636), target))
        self.assertFalse(point_in_box(Point(1000, 660), target))

        hit = score_grounding(
            target_box=target,
            predicted_point=Point(1128, 660),
        )
        self.assertTrue(hit.point_hit)
        self.assertFalse(hit.false_click)
        self.assertFalse(hit.abstained)

        miss = score_grounding(
            target_box=target,
            predicted_point=Point(1000, 660),
        )
        self.assertFalse(miss.point_hit)
        self.assertTrue(miss.false_click)

    def test_box_prediction_uses_center_for_click_and_records_iou(self):
        target = Box(32, 24, 64, 56)
        predicted = Box(36, 28, 60, 52)
        score = score_grounding(target_box=target, predicted_box=predicted)

        self.assertTrue(score.point_hit)
        self.assertFalse(score.false_click)
        self.assertIsNotNone(score.box_iou)
        self.assertGreater(score.box_iou, 0.5)
        self.assertAlmostEqual(score.box_iou, box_iou(target, predicted))
        self.assertAlmostEqual(score.center_error_px, 0.0)

    def test_absent_target_rewards_abstention_and_flags_false_positive(self):
        abstain = score_grounding(target_box=None)
        self.assertTrue(abstain.abstained)
        self.assertFalse(abstain.false_click)
        self.assertIsNone(abstain.point_hit)

        false_positive = score_grounding(
            target_box=None,
            predicted_point=Point(100, 100),
        )
        self.assertFalse(false_positive.abstained)
        self.assertTrue(false_positive.false_click)
        self.assertIsNone(false_positive.point_hit)

    def test_present_target_abstention_is_explicit_not_false_click(self):
        score = score_grounding(target_box=Box(100, 100, 140, 140))
        self.assertTrue(score.abstained)
        self.assertFalse(score.false_click)
        self.assertFalse(score.point_hit)

    def test_fixture_contains_hard_case_categories(self):
        kinds = {case["kind"] for case in self.spec["cases"]}
        self.assertTrue(
            {
                "labeled_button",
                "icon_only",
                "repeated_similar_control",
                "tiny_target",
                "visual_state",
                "absent_target",
            }.issubset(kinds)
        )


if __name__ == "__main__":
    unittest.main()
