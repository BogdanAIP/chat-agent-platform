import json
import unittest

from runtime.local_vision_adapter.mark_grid import Point
from runtime.local_vision_adapter.provider import (
    LlamaCppLoopbackClient,
    VisionProviderError,
    build_direct_point_prompt,
    build_mark_grid_prompt,
    direct_point_response_schema,
    encode_image_data_uri,
    mark_grid_response_schema,
    parse_direct_point_response,
    parse_mark_grid_response,
)


class LocalVisionProviderTests(unittest.TestCase):
    def test_image_data_uri_is_local_and_bounded_to_known_mime_types(self):
        uri = encode_image_data_uri(b"png-bytes", "image/png")
        self.assertTrue(uri.startswith("data:image/png;base64,"))

        with self.assertRaises(VisionProviderError):
            encode_image_data_uri(b"x", "application/octet-stream")

    def test_response_schemas_are_bounded(self):
        direct = direct_point_response_schema()
        self.assertEqual(direct["type"], "object")
        self.assertFalse(direct["additionalProperties"])
        self.assertEqual(direct["properties"]["point"]["minItems"], 2)
        self.assertEqual(direct["properties"]["point"]["maxItems"], 2)

        grid = mark_grid_response_schema(8)
        self.assertEqual(grid["type"], "array")
        self.assertEqual(grid["minItems"], 4)
        self.assertEqual(grid["maxItems"], 4)
        self.assertEqual(grid["items"]["minimum"], 0)
        self.assertEqual(grid["items"]["maximum"], 63)

    def test_direct_prompt_has_explicit_abstain_contract(self):
        prompt = build_direct_point_prompt("click Send", 1280, 720)
        self.assertIn('"found":false', prompt)
        self.assertIn("1280", prompt)
        self.assertIn("720", prompt)

    def test_mark_grid_prompt_matches_four_id_contract(self):
        prompt = build_mark_grid_prompt("open Gamma actions", 8)
        self.assertIn("exactly 4 grid IDs", prompt)
        self.assertIn("between 0 and 63", prompt)
        self.assertIn("[left_id,top_id,right_id,bottom_id]", prompt)

        refinement = build_mark_grid_prompt(
            "open Gamma actions",
            8,
            refinement_with_overview=True,
        )
        self.assertIn("two images", refinement)
        self.assertIn("Use the second image", refinement)

    def test_direct_parser_accepts_plain_fenced_and_single_wrapped_json(self):
        point = parse_direct_point_response(
            '{"found":true,"point":[1128,660]}',
            image_width=1280,
            image_height=720,
        )
        self.assertEqual(point, Point(1128.0, 660.0))

        fenced = parse_direct_point_response(
            '```json\n{"found":false}\n```',
            image_width=1280,
            image_height=720,
        )
        self.assertIsNone(fenced)

        wrapped = parse_direct_point_response(
            'Result: {"found":true,"point":[1128,660]}',
            image_width=1280,
            image_height=720,
        )
        self.assertEqual(wrapped, Point(1128.0, 660.0))

    def test_direct_parser_rejects_guessed_out_of_bounds_point(self):
        with self.assertRaises(VisionProviderError):
            parse_direct_point_response(
                '{"found":true,"point":[2000,100]}',
                image_width=1280,
                image_height=720,
            )

    def test_direct_parser_rejects_ambiguous_or_malformed_output(self):
        with self.assertRaises(VisionProviderError):
            parse_direct_point_response(
                "I think it is around 100,100",
                image_width=1280,
                image_height=720,
            )

        with self.assertRaises(VisionProviderError):
            parse_direct_point_response(
                '{"found":false,"point":[100,100]}',
                image_width=1280,
                image_height=720,
            )

        with self.assertRaises(VisionProviderError):
            parse_direct_point_response(
                'first {"found":false} second {"found":true,"point":[100,100]}',
                image_width=1280,
                image_height=720,
            )

    def test_mark_grid_parser_preserves_duplicates(self):
        result = parse_mark_grid_response("```json\n[63,63,63,63]\n```", 8)
        self.assertEqual(result, (63, 63, 63, 63))

        with self.assertRaises(VisionProviderError):
            parse_mark_grid_response("[1,2,3]", 8)

        with self.assertRaises(VisionProviderError):
            parse_mark_grid_response("[1,2,3,64]", 8)

    def test_loopback_client_cannot_be_configured_to_remote_host(self):
        client = LlamaCppLoopbackClient(port=3063)
        self.assertEqual(client.url, "http://127.0.0.1:3063/v1/chat/completions")

        with self.assertRaises(VisionProviderError):
            LlamaCppLoopbackClient(port=0)

    def test_loopback_client_builds_reviewed_payload_and_parses_usage(self):
        captured = {}

        def fake_transport(url, body, timeout):
            captured["url"] = url
            captured["body"] = json.loads(body.decode("utf-8"))
            captured["timeout"] = timeout
            return {
                "choices": [{"message": {"content": '{"found":true,"point":[1128,660]}'}}],
                "usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 12,
                    "total_tokens": 212,
                },
            }

        client = LlamaCppLoopbackClient(
            port=3063,
            timeout_seconds=123,
            transport=fake_transport,
        )
        schema = direct_point_response_schema()
        result = client.chat_with_image(
            image_data_uri=encode_image_data_uri(b"fake-image"),
            prompt="ground target",
            max_tokens=64,
            response_schema=schema,
        )

        self.assertEqual(captured["url"], "http://127.0.0.1:3063/v1/chat/completions")
        self.assertEqual(captured["timeout"], 123.0)
        payload = captured["body"]
        self.assertEqual(payload["model"], "local")
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["max_tokens"], 64)
        self.assertEqual(payload["response_format"]["type"], "json_object")
        self.assertEqual(payload["response_format"]["schema"], schema)
        self.assertEqual(payload["messages"][0]["content"][0]["type"], "text")
        self.assertEqual(payload["messages"][0]["content"][1]["type"], "image_url")
        self.assertEqual(len(payload["messages"][0]["content"]), 2)
        self.assertTrue(
            payload["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
        )
        self.assertEqual(result.prompt_tokens, 200)
        self.assertEqual(result.completion_tokens, 12)
        self.assertEqual(result.total_tokens, 212)

    def test_loopback_client_supports_bounded_two_image_refinement(self):
        captured = {}

        def fake_transport(url, body, timeout):
            captured["body"] = json.loads(body.decode("utf-8"))
            return {"choices": [{"message": {"content": "[3,3,4,9]"}}]}

        client = LlamaCppLoopbackClient(port=3063, transport=fake_transport)
        first = encode_image_data_uri(b"overview")
        second = encode_image_data_uri(b"zoom")
        schema = mark_grid_response_schema(8)
        result = client.chat_with_images(
            image_data_uris=(first, second),
            prompt="refine target",
            max_tokens=32,
            response_schema=schema,
        )

        payload = captured["body"]
        content = payload["messages"][0]["content"]
        self.assertEqual([part["type"] for part in content], ["text", "image_url", "image_url"])
        self.assertEqual(content[1]["image_url"]["url"], first)
        self.assertEqual(content[2]["image_url"]["url"], second)
        self.assertEqual(payload["response_format"]["schema"], schema)
        self.assertEqual(result.content, "[3,3,4,9]")

        with self.assertRaises(VisionProviderError):
            client.chat_with_images(
                image_data_uris=(first, second, first),
                prompt="too many images",
            )

    def test_loopback_client_rejects_invalid_schema_and_non_data_image_reference(self):
        client = LlamaCppLoopbackClient(
            port=3063,
            transport=lambda *_: {},
        )
        with self.assertRaises(VisionProviderError):
            client.chat_with_image(
                image_data_uri="https://example.com/image.png",
                prompt="ground target",
            )
        with self.assertRaises(VisionProviderError):
            client.chat_with_image(
                image_data_uri=encode_image_data_uri(b"x"),
                prompt="ground target",
                response_schema={},
            )


if __name__ == "__main__":
    unittest.main()
