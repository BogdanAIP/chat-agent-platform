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
        self.prepare = Path("scripts/prepare-stage4-gpt-action.ps1").read_text(
            encoding="utf-8"
        )

    def test_gateway_remains_relay_only_after_gpt_proxy_failure(self):
        self.assertEqual(set(self.gateway["paths"]), {"/"})
        for method in ("get", "post"):
            integration = self.gateway["paths"]["/"][method][
                "x-yc-apigateway-integration"
            ]
            self.assertEqual(integration["type"], "cloud_functions")
            self.assertEqual(integration["function_id"], "__FUNCTION_ID__")

    def test_private_gpt_openapi_targets_direct_function_with_custom_header_auth(self):
        self.assertIn(self.actions["openapi"], {"3.1.0", "3.1.1"})
        self.assertIsInstance(self.actions["components"]["schemas"], dict)
        self.assertEqual(self.actions["servers"][0]["url"], "__FUNCTION_URL__")
        self.assertEqual(set(self.actions["paths"]), {"/"})

        action = self.actions["paths"]["/"]["post"]
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

    def test_prepare_helper_does_not_update_or_depend_on_api_gateway(self):
        self.assertIn('https://functions.yandexcloud.net/$functionId', self.prepare)
        self.assertIn("api_gateway_used = $false", self.prepare)
        self.assertIn("__FUNCTION_URL__", self.prepare)
        self.assertNotIn("api-gateway','update", self.prepare)
        self.assertNotIn("/gpt", self.prepare)
        self.assertNotIn("MCP_TOKEN", self.prepare)
        self.assertNotIn("AGENT_TOKEN", self.prepare)


if __name__ == "__main__":
    unittest.main()
