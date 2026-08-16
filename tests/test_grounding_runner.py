import tempfile
from pathlib import Path
import unittest

from PIL import Image

from runtime.local_vision_adapter.grounding_runner import (
    run_direct_case,
    run_mark_grid_case,
    summarize_results,
)
from runtime.local_vision_adapter.provider import VisionChatResult


class FakeGroundingClient:
    def __init__(self, *, direct=None, pass1=None, pass2=None):
        self.direct = direct
        self.pass1 = pass1
        self.pass2 = pass2
        self.single_calls = 0
        self.multi_calls = 0

    def chat_with_image(self, **kwargs):
        self.single_calls += 1
        content = self.direct if self.direct is not None else self.pass1
        return VisionChatResult(content=content, prompt_tokens=10, completion_tokens=4, total_tokens=14)

    def chat_with_images(self, **kwargs):
        self.multi_calls += 1
        self.assert_two_images = len(tuple(kwargs["image_data_uris"])) == 2
        return VisionChatResult(content=self.pass2, prompt_tokens=20, completion_tokens=4, total_tokens=24)


class GroundingRunnerTests(unittest.TestCase):
    def setUp(self):
        self.source = Image.new("RGB", (1280, 720), "white")

    def test_direct_case_scores_point_hit(self):
        case = {
            "id": "send",
            "kind": "labeled_button",
            "instruction": "click Send",
            "bbox": [1056, 636, 1200, 684],
        }
        client = FakeGroundingClient(direct='{"found":true,"point":[1128,660]}')
        result = run_direct_case(client=client, source=self.source, case=case)

        self.assertEqual(client.single_calls, 1)
        self.assertTrue(result["score"]["point_hit"])
        self.assertFalse(result["score"]["false_click"])
        self.assertIsNone(result["parse_error"])

    def test_direct_absent_case_preserves_explicit_abstain(self):
        case = {
            "id": "absent",
            "kind": "absent_target",
            "instruction": "click Export CSV",
            "bbox": None,
        }
        client = FakeGroundingClient(direct='{"found":false}')
        result = run_direct_case(client=client, source=self.source, case=case)

        self.assertTrue(result["score"]["abstained"])
        self.assertFalse(result["score"]["false_click"])

    def test_mark_grid_two_pass_uses_reference_geometry_and_two_image_refinement(self):
        case = {
            "id": "bottom-right-target",
            "kind": "tiny_target",
            "instruction": "click target",
            "bbox": [1180, 660, 1200, 680],
        }
        client = FakeGroundingClient(
            pass1="[63,63,63,63]",
            pass2="[27,27,27,27]",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_mark_grid_case(
                client=client,
                source=self.source,
                case=case,
                artifact_dir=Path(temp_dir),
            )
            self.assertTrue((Path(temp_dir) / case["id"] / "pass1-grid.png").is_file())
            self.assertTrue((Path(temp_dir) / case["id"] / "pass2-overview.png").is_file())
            self.assertTrue((Path(temp_dir) / case["id"] / "pass2-grid.png").is_file())

        self.assertEqual(client.single_calls, 1)
        self.assertEqual(client.multi_calls, 1)
        self.assertTrue(client.assert_two_images)
        self.assertEqual(result["pass1_ids"], [63, 63, 63, 63])
        self.assertEqual(result["pass2_ids"], [27, 27, 27, 27])
        self.assertIsNone(result["parse_error"])
        self.assertTrue(result["score"]["point_hit"])
        self.assertAlmostEqual(result["prediction_point"]["y"], 669.375, places=3)

    def test_mark_grid_malformed_output_fails_closed_to_no_click(self):
        case = {
            "id": "present",
            "kind": "icon_only",
            "instruction": "click icon",
            "bbox": [32, 24, 64, 56],
        }
        client = FakeGroundingClient(pass1="not json", pass2="[1,1,1,1]")
        result = run_mark_grid_case(client=client, source=self.source, case=case)

        self.assertIsNotNone(result["parse_error"])
        self.assertTrue(result["score"]["abstained"])
        self.assertFalse(result["score"]["false_click"])

    def test_summary_keeps_accuracy_false_click_abstain_and_error_counts_separate(self):
        rows = [
            {
                "latency_seconds": 1.0,
                "parse_error": None,
                "score": {"target_present": True, "point_hit": True, "false_click": False, "abstained": False},
            },
            {
                "latency_seconds": 2.0,
                "parse_error": "bad json",
                "score": {"target_present": True, "point_hit": False, "false_click": False, "abstained": True},
            },
            {
                "latency_seconds": 3.0,
                "parse_error": None,
                "score": {"target_present": False, "point_hit": None, "false_click": True, "abstained": False},
            },
        ]
        summary = summarize_results(rows)

        self.assertEqual(summary["present_target_count"], 2)
        self.assertEqual(summary["point_hits"], 1)
        self.assertEqual(summary["point_accuracy"], 0.5)
        self.assertEqual(summary["false_clicks"], 1)
        self.assertEqual(summary["abstains"], 1)
        self.assertEqual(summary["malformed_or_provider_errors"], 1)
        self.assertEqual(summary["total_latency_seconds"], 6.0)


if __name__ == "__main__":
    unittest.main()
