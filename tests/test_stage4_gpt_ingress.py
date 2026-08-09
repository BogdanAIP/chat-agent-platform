import json
import unittest
from pathlib import Path


class Stage4GptIngressTests(unittest.TestCase):
    def setUp(self):
        self.gateway = json.loads(
            Path("gateway/yandex-apigateway.template.json").read_text(encoding="utf-8")
        )
        self.actions = json.loads(
            Path("gateway/actions-openapi-gpt.template.json").read_text(encoding="utf-8")
        )

    def test_gpt_gateway_route_filters_original_request_headers(self):
        route = self.gateway["paths"]["/gpt"]["post"]
        integration = route["x-yc-apigateway-integration"]

        self.assertEqual(integration["type"], "http")
        self.assertEqual(
            integration["url"], "https://functions.yandexcloud.net/__FUNCTION_ID__"
        )
        self.assertEqual(integration["method"], "POST")
        self.assertEqual(
            integration["headers"],
            {
                "Content-Type": "application/json",
                "X-MCP-Token": "{X-MCP-Token}",
            },
        )
        self.assertTrue(integration["omitEmptyHeaders"])
        self.assertNotIn("*", integration["headers"])
        self.assertNotIn("X-Request-Id", integration["headers"])

        parameters = route["parameters"]
        self.assertEqual(len(parameters), 1)
        self.assertEqual(parameters[0]["name"], "X-MCP-Token")
        self.assertEqual(parameters[0]["in"], "header")
        self.assertTrue(parameters[0]["required"])

    def test_existing_root_relay_routes_remain_cloud_function_integrations(self):
        for method in ("get", "post"):
            integration = self.gateway["paths"]["/"][method][
                "x-yc-apigateway-integration"
            ]
            self.assertEqual(integration["type"], "cloud_functions")
            self.assertEqual(integration["function_id"], "__FUNCTION_ID__")

    def test_private_gpt_openapi_targets_only_gpt_route_with_custom_header_auth(self):
        self.assertIn(self.actions["openapi"], {"3.1.0", "3.1.1"})
        self.assertIsInstance(self.actions["components"]["schemas"], dict)
        self.assertEqual(set(self.actions["paths"]), {"/gpt"})

        action = self.actions["paths"]["/gpt"]["post"]
        self.assertEqual(action["operationId"], "runLocalAgentTool")
        action_schema = action["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(
            action_schema["properties"]["action"]["enum"],
            ["local_ping", "runtime_self_test"],
        )

        security = self.actions["components"]["securitySchemes"]["mcpToken"]
        self.assertEqual(
            security,
            {"type": "apiKey", "in": "header", "name": "X-MCP-Token"},
        )
        self.assertEqual(action["security"], [{"mcpToken": []}])


if __name__ == "__main__":
    unittest.main()
