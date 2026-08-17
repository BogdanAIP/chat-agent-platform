from __future__ import annotations

import base64
from dataclasses import replace
from importlib import util as importlib_util
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from PIL import Image

from runtime.local_vision_adapter.production_grounder import ProductionVisualGroundingResult


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "production-visual-grounder.py"
SPEC = importlib_util.spec_from_file_location("production_visual_grounder_cli", CLI_PATH)
assert SPEC is not None and SPEC.loader is not None
cli = importlib_util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


def png_bytes(width: int = 4, height: int = 3) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def request_bytes(**overrides) -> bytes:
    image = overrides.pop("image", png_bytes())
    payload = {
        "schema_version": 1,
        "image_base64": base64.b64encode(image).decode("ascii"),
        "width": 4,
        "height": 3,
        "coordinate_space": "css_viewport",
        "instruction": "click Search",
        "kind": "icon_only",
        "target_text": None,
    }
    payload.update(overrides)
    import json

    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class ProductionVisualGrounderCliTests(unittest.TestCase):
    def test_reviewed_config_and_resolved_result(self) -> None:
        sentinel_client = object()
        expected = ProductionVisualGroundingResult(
            status="resolved",
            reason="promoted-icon-consistent",
            point={"x": 2.0, "y": 1.0},
            bbox={"x1": 1.0, "y1": 0.5, "x2": 3.0, "y2": 2.0},
            diagnostics={"method": "native_bbox_450m_inventory_zoom"},
        )
        with mock.patch.object(cli, "NativeBBoxLoopbackClient", return_value=sentinel_client) as client_cls:
            with mock.patch.object(cli, "ground_png_for_browser", return_value=expected) as ground:
                result = cli.run_request(request_bytes())

        client_cls.assert_called_once_with(port=3068, timeout_seconds=120.0)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["point"], {"x": 2.0, "y": 1.0})
        self.assertEqual(result["bbox"]["x2"], 3.0)
        kwargs = ground.call_args.kwargs
        self.assertIs(kwargs["client"], sentinel_client)
        self.assertEqual(kwargs["instruction"], "click Search")
        self.assertEqual(kwargs["kind"], "icon_only")

    def test_dimension_mismatch_rejected_before_provider(self) -> None:
        with mock.patch.object(cli, "NativeBBoxLoopbackClient") as client_cls:
            with self.assertRaisesRegex(cli.CliContractError, "image-dimensions-do-not-match-request"):
                cli.run_request(request_bytes(width=5))
        client_cls.assert_not_called()

    def test_unknown_field_rejected(self) -> None:
        with self.assertRaisesRegex(cli.CliContractError, "request-has-unknown-fields"):
            cli.run_request(request_bytes(model_path="C:/should-not-be-accepted.gguf"))

    def test_unreviewed_runtime_port_rejected_before_provider(self) -> None:
        original = cli.CONFIG_PATH
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "runtime.json"
            config.write_text(
                '{"schema_version":1,"profile":"lfm25-vl-450m-f16","runtime":{"host":"127.0.0.1","port":9999}}',
                encoding="utf-8",
            )
            cli.CONFIG_PATH = config
            try:
                with mock.patch.object(cli, "NativeBBoxLoopbackClient") as client_cls:
                    with self.assertRaisesRegex(cli.CliContractError, "reviewed-runtime-loopback-contract-mismatch"):
                        cli.run_request(request_bytes())
                client_cls.assert_not_called()
            finally:
                cli.CONFIG_PATH = original

    def test_non_css_coordinate_space_rejected(self) -> None:
        with self.assertRaisesRegex(cli.CliContractError, "coordinate-space-must-be-css-viewport"):
            cli.run_request(request_bytes(coordinate_space="device_pixels"))


if __name__ == "__main__":
    unittest.main()
