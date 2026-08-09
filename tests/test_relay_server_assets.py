import json
import unittest
from pathlib import Path


class RelayServerAssetTests(unittest.TestCase):
    def test_gpt_action_schema_targets_root_with_custom_header_auth(self):
        schema = json.loads(
            Path("gateway/actions-openapi-relay.template.json").read_text(encoding="utf-8")
        )
        self.assertIn(schema["openapi"], {"3.1.0", "3.1.1"})
        self.assertEqual(schema["servers"], [{"url": "__RELAY_URL__"}])
        self.assertEqual(set(schema["paths"]), {"/"})
        action = schema["paths"]["/"]["post"]
        self.assertEqual(action["operationId"], "runLocalAgentTool")
        self.assertEqual(
            action["requestBody"]["content"]["application/json"]["schema"]
            ["properties"]["action"]["enum"],
            ["local_ping", "runtime_self_test"],
        )
        self.assertEqual(
            schema["components"]["securitySchemes"]["mcpToken"],
            {"type": "apiKey", "in": "header", "name": "X-MCP-Token"},
        )

    def test_systemd_service_keeps_relay_on_loopback_configuration(self):
        service = Path("deploy/relay-server/agent-platform-relay.service").read_text(
            encoding="utf-8"
        )
        env = Path("deploy/relay-server/relay.env.example").read_text(encoding="utf-8")
        self.assertIn("EnvironmentFile=/etc/agent-platform-relay/relay.env", service)
        self.assertIn("NoNewPrivileges=true", service)
        self.assertIn("ProtectSystem=strict", service)
        self.assertIn("ReadWritePaths=/var/lib/agent-platform-relay", service)
        self.assertIn("RELAY_BIND=127.0.0.1:8787", env)
        self.assertIn("RELAY_DATABASE=/var/lib/agent-platform-relay/relay.sqlite3", env)

    def test_caddy_example_does_not_enable_access_logging(self):
        caddy = Path("deploy/relay-server/Caddyfile.example").read_text(encoding="utf-8")
        self.assertIn("reverse_proxy 127.0.0.1:8787", caddy)
        self.assertNotRegex(caddy, r"(?m)^\s*log\s*(?:\{|$)")

    def test_prepare_helper_is_provider_neutral(self):
        helper = Path("scripts/prepare-relay-gpt-action.ps1").read_text(encoding="utf-8")
        lowered = helper.lower()
        self.assertIn("__relay_url__", lowered)
        self.assertIn("relay-server-v1", lowered)
        self.assertIn("x-mcp-token", lowered)
        self.assertNotIn("yandex", lowered)
        self.assertNotIn("cloudflare", lowered)
        self.assertNotIn("ngrok", lowered)


if __name__ == "__main__":
    unittest.main()
