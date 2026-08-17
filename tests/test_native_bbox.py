from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from runtime.local_vision_adapter.native_bbox import (
    NativeBBoxLoopbackClient,
    build_labeled_button_inventory_prompt,
    build_native_bbox_prompt,
    native_bbox_response_schema,
    normalized_box_to_pixels,
    parse_native_bbox_response,
    run_native_bbox_zoom_case,
)
from runtime.local_vision_adapter.provider import VisionProviderError


class NativeBBoxContractTests(unittest.TestCase):
    def test_schema_matches_normalized_detection_contract(self) -> None:
        schema = native_bbox_response_schema()
        self.assertEqual(schema["type"], "array")
        bbox = schema["items"]["properties"]["bbox"]
        self.assertEqual(bbox["minItems"], 4)
        self.assertEqual(bbox["maxItems"], 4)
        self.assertEqual(bbox["items"]["minimum"], 0)
        self.assertEqual(bbox["items"]["maximum"], 1)

    def test_prompt_has_explicit_absence_rule(self) -> None:
        prompt = build_native_bbox_prompt("click Send")
        self.assertIn("normalized to [0,1]", prompt)
        self.assertIn("Return []", prompt)
        self.assertIn("Do not invent", prompt)

    def test_inventory_prompt_is_target_blind(self) -> None:
        prompt = build_labeled_button_inventory_prompt()
        self.assertIn("without looking for any particular requested target", prompt)
        self.assertIn("copy the visible button text exactly", prompt)
        self.assertNotIn("Send", prompt)
        self.assertNotIn("Export CSV", prompt)

    def test_parse_accepts_detection_and_empty_abstention(self) -> None:
        rows = parse_native_bbox_response(
            '[{"label":"Send","bbox":[0.8,0.7,0.95,0.9]}]'
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].label, "Send")
        pixel_box = normalized_box_to_pixels(rows[0].bbox, 1000, 500)
        self.assertEqual((pixel_box.x1, pixel_box.y1, pixel_box.x2, pixel_box.y2), (800, 350, 950, 450))
        self.assertEqual(parse_native_bbox_response("[]"), ())

    def test_parse_rejects_out_of_range_or_degenerate_box(self) -> None:
        with self.assertRaises(VisionProviderError):
            parse_native_bbox_response('[{"label":"Send","bbox":[-0.1,0,0.5,0.5]}]')
        with self.assertRaises((VisionProviderError, ValueError)):
            parse_native_bbox_response('[{"label":"Send","bbox":[0.5,0.5,0.5,0.7]}]')

    def test_client_uses_vendor_sampling_and_image_first(self) -> None:
        captured: dict = {}

        def transport(url: str, body: bytes, timeout: float) -> dict:
            captured.update(json.loads(body.decode("utf-8")))
            return {
                "choices": [{"message": {"content": "[]"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
            }

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        result = client.detect(
            image_data_uri="data:image/png;base64,AAAA",
            target="click Send",
        )
        self.assertEqual(result.content, "[]")
        self.assertEqual(captured["temperature"], 0.1)
        self.assertEqual(captured["min_p"], 0.15)
        self.assertEqual(captured["repeat_penalty"], 1.05)
        content = captured["messages"][0]["content"]
        self.assertEqual(content[0]["type"], "image_url")
        self.assertEqual(content[1]["type"], "text")
        self.assertEqual(captured["response_format"]["schema"]["type"], "array")

    def test_inventory_client_does_not_name_target(self) -> None:
        captured: dict = {}

        def transport(url: str, body: bytes, timeout: float) -> dict:
            captured.update(json.loads(body.decode("utf-8")))
            return {"choices": [{"message": {"content": "[]"}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        client.inventory_labeled_buttons(image_data_uri="data:image/png;base64,AAAA")
        prompt = captured["messages"][0]["content"][1]["text"]
        self.assertNotIn("Send", prompt)
        self.assertNotIn("Export CSV", prompt)
        self.assertEqual(captured["response_format"]["schema"]["maxItems"], 16)


class NativeBBoxRunnerTests(unittest.TestCase):
    def test_two_pass_zoom_maps_refined_box_and_scores_hit(self) -> None:
        responses = iter(
            [
                '[{"label":"Send","bbox":[0.2,0.2,0.4,0.4]}]',
                '[{"label":"Send","bbox":[0.34375,0.34375,0.65625,0.65625]}]',
            ]
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": next(responses)}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (512, 512), "white")
        case = {
            "id": "send",
            "kind": "labeled_button",
            "instruction": "click Send",
            "bbox": [110, 110, 190, 190],
        }

        with tempfile.TemporaryDirectory() as directory:
            row = run_native_bbox_zoom_case(
                client=client,
                source=source,
                case=case,
                artifact_dir=Path(directory),
            )
            self.assertEqual(row["decision"], "accepted")
            self.assertTrue(row["score"]["point_hit"])
            self.assertFalse(row["score"]["false_click"])
            self.assertIsNotNone(row["coarse_refined_iou"])
            crop_path = Path(directory) / "send" / "native-bbox-pass2-crop.png"
            self.assertTrue(crop_path.is_file())
            with Image.open(crop_path) as crop:
                self.assertEqual(crop.size, (308, 308))

    def test_target_blind_inventory_selects_labeled_button_before_refinement(self) -> None:
        responses = iter(
            [
                '[{"label":"Send","bbox":[0.7,0.9,0.86,0.99]}]',
                '[{"label":"Send","bbox":[0.7,0.67,0.9,0.85]}]',
            ]
        )
        prompts: list[str] = []

        def transport(url: str, body: bytes, timeout: float) -> dict:
            payload = json.loads(body.decode("utf-8"))
            prompts.append(payload["messages"][0]["content"][1]["text"])
            return {"choices": [{"message": {"content": next(responses)}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (1280, 720), "white")
        case = {
            "id": "send",
            "kind": "labeled_button",
            "instruction": "click the enabled Send button in the lower-right corner",
            "target_text": "Send",
            "bbox": [1056, 636, 1200, 684],
        }

        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
        self.assertEqual(len(prompts), 2)
        self.assertNotIn("Send", prompts[0])
        self.assertIn("Send", prompts[1])
        self.assertEqual(row["inventory_match_count"], 1)
        self.assertEqual(row["decision"], "accepted")
        self.assertTrue(row["score"]["point_hit"])

    def test_inventory_absence_vetoes_hallucinated_labeled_target(self) -> None:
        calls = 0

        def transport(url: str, body: bytes, timeout: float) -> dict:
            nonlocal calls
            calls += 1
            return {
                "choices": [{
                    "message": {
                        "content": '[{"label":"Send","bbox":[0.7,0.9,0.86,0.99]}]'
                    }
                }]
            }

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (1280, 720), "white")
        case = {
            "id": "absent",
            "kind": "absent_target",
            "instruction": "click the Export CSV button",
            "target_text": "Export CSV",
            "bbox": None,
        }

        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
        self.assertEqual(calls, 1)
        self.assertEqual(row["decision"], "inventory-absent")
        self.assertEqual(row["inventory_match_count"], 0)
        self.assertTrue(row["score"]["abstained"])
        self.assertFalse(row["score"]["false_click"])

    def test_duplicate_inventory_label_fails_closed(self) -> None:
        payload = (
            '[{"label":"Send","bbox":[0.1,0.1,0.2,0.2]},'
            '{"label":"Send","bbox":[0.7,0.7,0.8,0.8]}]'
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": payload}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (320, 240), "white")
        case = {
            "id": "ambiguous",
            "kind": "visual_state",
            "instruction": "click enabled Send",
            "target_text": "Send",
            "bbox": [224, 168, 256, 192],
        }
        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
        self.assertEqual(row["decision"], "inventory-ambiguous")
        self.assertTrue(row["score"]["abstained"])
        self.assertFalse(row["score"]["false_click"])

    def test_absent_first_pass_is_safe_abstention_without_second_request(self) -> None:
        calls = 0

        def transport(url: str, body: bytes, timeout: float) -> dict:
            nonlocal calls
            calls += 1
            return {"choices": [{"message": {"content": "[]"}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (320, 240), "white")
        case = {
            "id": "absent",
            "kind": "absent_target",
            "instruction": "click Export CSV",
            "bbox": None,
        }
        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
        self.assertEqual(calls, 1)
        self.assertEqual(row["decision"], "absent")
        self.assertTrue(row["score"]["abstained"])
        self.assertFalse(row["score"]["false_click"])

    def test_multiple_first_pass_candidates_fail_closed(self) -> None:
        payload = (
            '[{"label":"Send","bbox":[0.1,0.1,0.2,0.2]},'
            '{"label":"Send","bbox":[0.7,0.7,0.8,0.8]}]'
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": payload}}]}

        client = NativeBBoxLoopbackClient(port=3068, transport=transport)
        source = Image.new("RGB", (320, 240), "white")
        case = {
            "id": "ambiguous",
            "kind": "visual_state",
            "instruction": "click enabled Send",
            "bbox": [224, 168, 256, 192],
        }
        row = run_native_bbox_zoom_case(client=client, source=source, case=case)
        self.assertEqual(row["decision"], "ambiguous-pass1")
        self.assertTrue(row["score"]["abstained"])
        self.assertFalse(row["score"]["false_click"])


if __name__ == "__main__":
    unittest.main()
