import json
import unittest
from pathlib import Path


class ActionsOpenApiTests(unittest.TestCase):
    def test_gpt_actions_schema_uses_supported_openapi_and_object_components_schemas(self):
        template = Path("gateway/actions-openapi.template.json")
        schema = json.loads(template.read_text(encoding="utf-8"))

        self.assertIn(schema["openapi"], {"3.1.0", "3.1.1"})
        self.assertIsInstance(schema["components"], dict)
        self.assertIsInstance(schema["components"]["schemas"], dict)
        self.assertIsInstance(schema["components"]["securitySchemes"], dict)

        action = schema["paths"]["/"]["post"]
        self.assertEqual(action["operationId"], "runLocalAgentTool")
        action_schema = action["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(
            action_schema["properties"]["action"]["enum"],
            ["local_ping", "runtime_self_test"],
        )

        response_schema = action["responses"]["200"]["content"]["application/json"]["schema"]
        for property_name in ("result", "error"):
            property_schema = response_schema["properties"][property_name]
            self.assertEqual(property_schema["type"], "object")
            self.assertTrue(property_schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
