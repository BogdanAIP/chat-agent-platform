from __future__ import annotations

from io import BytesIO
import unittest

from PIL import Image

from runtime.local_vision_adapter.native_bbox import NativeBBoxLoopbackClient
from runtime.local_vision_adapter.production_grounder import (
    ProductionGrounderError,
    ground_png_for_browser,
)


def png_bytes(width: int = 512, height: int = 512) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


class ProductionGrounderTests(unittest.TestCase):
    def test_inventory_backed_text_resolves_to_bridge_shape(self) -> None:
        responses = iter(
            [
                '[{"label":"Send","bbox":[0.10,0.10,0.30,0.30]}]',
                '[{"label":"Send","bbox":[0.36,0.36,0.56,0.56]}]',
            ]
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": next(responses)}}]}

        result = ground_png_for_browser(
            client=NativeBBoxLoopbackClient(port=3068, transport=transport),
            image_bytes=png_bytes(),
            instruction="click Send",
            kind="labeled_button",
            target_text="Send",
        )

        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.reason, "promoted-text-inventory")
        self.assertIsNotNone(result.point)
        self.assertIsNotNone(result.bbox)
        assert result.point is not None
        assert result.bbox is not None
        self.assertGreaterEqual(result.point["x"], result.bbox["x1"])
        self.assertLessEqual(result.point["x"], result.bbox["x2"])
        self.assertGreaterEqual(result.point["y"], result.bbox["y1"])
        self.assertLessEqual(result.point["y"], result.bbox["y2"])
        self.assertNotIn("pass1_response", result.diagnostics or {})
        self.assertNotIn("pass2_response", result.diagnostics or {})

    def test_repeated_row_remains_abstain_even_when_native_adapter_accepts(self) -> None:
        responses = iter(
            [
                '[{"label":"Gamma actions","bbox":[0.50,0.50,0.80,0.70]}]',
                '[{"label":"Gamma actions","bbox":[0.45,0.33,0.78,0.67]}]',
            ]
        )

        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": next(responses)}}]}

        result = ground_png_for_browser(
            client=NativeBBoxLoopbackClient(port=3068, transport=transport),
            image_bytes=png_bytes(1280, 720),
            instruction="open the actions menu for the Gamma deployment row",
            kind="repeated_similar_control",
        )

        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "target-class-not-promoted:repeated-similar-control")
        self.assertIsNone(result.point)
        self.assertIsNone(result.bbox)

    def test_absent_inventory_target_abstains_without_second_request(self) -> None:
        calls = 0

        def transport(url: str, body: bytes, timeout: float) -> dict:
            nonlocal calls
            calls += 1
            return {"choices": [{"message": {"content": '[{"label":"Send","bbox":[0.1,0.1,0.2,0.2]}]'}}]}

        result = ground_png_for_browser(
            client=NativeBBoxLoopbackClient(port=3068, transport=transport),
            image_bytes=png_bytes(),
            instruction="click Export CSV",
            kind="labeled_button",
            target_text="Export CSV",
        )

        self.assertEqual(result.status, "abstain")
        self.assertEqual(result.reason, "grounder-inventory-absent")
        self.assertEqual(calls, 1)

    def test_provider_parse_failure_never_returns_resolved(self) -> None:
        def transport(url: str, body: bytes, timeout: float) -> dict:
            return {"choices": [{"message": {"content": "not-json"}}]}

        with self.assertRaises(ProductionGrounderError):
            ground_png_for_browser(
                client=NativeBBoxLoopbackClient(port=3068, transport=transport),
                image_bytes=png_bytes(),
                instruction="click Search",
                kind="icon_only",
            )

    def test_non_png_is_rejected_before_provider_call(self) -> None:
        calls = 0

        def transport(url: str, body: bytes, timeout: float) -> dict:
            nonlocal calls
            calls += 1
            return {"choices": [{"message": {"content": "[]"}}]}

        with self.assertRaises(ProductionGrounderError):
            ground_png_for_browser(
                client=NativeBBoxLoopbackClient(port=3068, transport=transport),
                image_bytes=b"not-a-png",
                instruction="click Search",
                kind="icon_only",
            )
        self.assertEqual(calls, 0)


if __name__ == "__main__":
    unittest.main()
