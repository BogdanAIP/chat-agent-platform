import pathlib
import unittest


class Stage4GatewayRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(__file__).resolve().parents[1]
        self.script = (self.repo / "scripts" / "ensure-stage4-gateway-active.ps1").read_text(
            encoding="utf-8"
        )

    def test_recovery_resumes_stopped_gateway_and_waits_for_active(self):
        self.assertIn("serverless api-gateway resume --id $GatewayId", self.script)
        self.assertIn("$initialStatus -eq 'STOPPED'", self.script)
        self.assertIn("$status -eq 'ACTIVE'", self.script)
        self.assertIn("$status -eq 'ERROR'", self.script)
        self.assertIn("API Gateway did not become ACTIVE", self.script)

    def test_recovery_uses_acceptance_gateway_id_and_checks_public_health(self):
        self.assertIn("runtime/stage4-yandex-acceptance.json", self.script)
        self.assertIn("$evidence.gateway_id", self.script)
        self.assertIn("Invoke-RestMethod -Method Get -Uri $gatewayUrl", self.script)
        self.assertIn("$health.status -ne 'ok'", self.script)

    def test_optional_clipboard_path_validates_generated_gpt_action_schema(self):
        self.assertIn("runtime/relay/actions-openapi.json", self.script)
        self.assertIn("@('3.1.0','3.1.1')", self.script)
        self.assertIn("$openApi.servers[0].url -ne $gatewayUrl", self.script)
        self.assertIn("$openApi.components.schemas", self.script)
        self.assertIn("Set-Clipboard -Value $openApiText", self.script)
        self.assertNotIn("MCP_TOKEN", self.script)
        self.assertNotIn("AGENT_TOKEN", self.script)


if __name__ == "__main__":
    unittest.main()
