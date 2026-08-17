from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from runtime.local_vision_adapter.native_bbox import (
    NativeBBoxLoopbackClient,
    run_native_bbox_zoom_case,
)


class NativeBBoxSafetyRegressionTests(unittest.TestCase):
    def test_non_text_zero_overlap_refinement_fails_closed(self) -> None:
        responses = iter(
            [
                '[{"label":"alert","bbox":[0.10,0.10,0.20,0.20]}]',
                '[{"label":"alert","bbox":[0.80,0.80,0.90,0.90]}]',
            ]
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": next(responses)}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (320, 240), "white")
        case = {
            "id": "tiny",
            "kind": "tiny_target",
            "instruction": "click the red unread indicator",
            "target_text": None,
            "bbox": [32, 24, 64, 48],
        }

        row = run_native_bbox_zoom_case(client=client, source=source, case=case)

        self.assertEqual(row["decision"], "inconsistent-pass2")
        self.assertEqual(row["coarse_refined_iou"], 0.0)
        self.assertIsNone(row["prediction_point"])
        self.assertTrue(row["score"]["abstained"])
        self.assertFalse(row["score"]["false_click"])
        self.assertIsNotNone(row["refined_box"])

    def test_text_inventory_path_can_accept_low_positive_overlap(self) -> None:
        responses = iter(
            [
                '[{"label":"Send","bbox":[0.10,0.10,0.30,0.30]}]',
                '[{"label":"Send","bbox":[0.36,0.36,0.56,0.56]}]',
            ]
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": next(responses)}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (512, 512), "white")
        case = {
            "id": "send-low-overlap",
            "kind": "labeled_button",
            "instruction": "click Send",
            "target_text": "Send",
            "bbox": [111, 111, 255, 255],
        }

        row = run_native_bbox_zoom_case(client=client, source=source, case=case)

        self.assertEqual(row["decision"], "accepted")
        self.assertIsNotNone(row["prediction_point"])
        self.assertIsNotNone(row["coarse_refined_iou"])
        self.assertGreater(row["coarse_refined_iou"], 0.0)

    def test_large_non_text_context_is_downscaled_and_maps_back_to_source(self) -> None:
        responses = iter(
            [
                '[{"label":"Gamma actions","bbox":[0.50,0.50,0.80,0.70]}]',
                '[{"label":"Gamma actions","bbox":[0.45,0.33,0.78,0.67]}]',
            ]
        )
        image_sizes: list[tuple[int, int]] = []

        def transport(url: str, body: bytes, timeout: float) -> dict:
            payload = json.loads(body.decode("utf-8"))
            image_url = payload["messages"][0]["content"][0]["image_url"]["url"]
            # The saved artifact below is authoritative for dimensions; recording
            # calls here also proves the two-pass path actually executed.
            self.assertTrue(image_url.startswith("data:image/png;base64,"))
            image_sizes.append((1, 1))
            return {"choices": [{"message": {"content": next(responses)}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (1280, 720), "white")
        case = {
            "id": "gamma",
            "kind": "repeated_similar_control",
            "instruction": "open the actions menu for the Gamma deployment row",
            "target_text": None,
            "bbox": [646, 358, 1027, 506],
        }

        with tempfile.TemporaryDirectory() as directory:
            row = run_native_bbox_zoom_case(
                client=client,
                source=source,
                case=case,
                artifact_dir=Path(directory),
            )
            crop_path = Path(directory) / "gamma" / "native-bbox-pass2-crop.png"
            self.assertTrue(crop_path.is_file())
            with Image.open(crop_path) as crop:
                self.assertEqual(crop.size, (768, 288))

        self.assertEqual(len(image_sizes), 2)
        self.assertEqual(row["decision"], "accepted")
        self.assertEqual(
            row["context_box"],
            {"x1": 128.0, "y1": 216.0, "x2": 1280.0, "y2": 648.0},
        )
        refined = row["refined_box"]
        self.assertIsNotNone(refined)
        assert refined is not None
        self.assertAlmostEqual(refined["x1"], 646.4, places=3)
        self.assertAlmostEqual(refined["y1"], 358.56, places=3)
        self.assertAlmostEqual(refined["x2"], 1026.56, places=3)
        self.assertAlmostEqual(refined["y2"], 505.44, places=3)


if __name__ == "__main__":
    unittest.main()
