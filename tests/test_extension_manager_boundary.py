from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHAT_PROFILES = (ROOT / '.github' / 'workflows' / 'chat-profiles.yml').read_text(encoding='utf-8')
EXTENSIONS = (ROOT / '.github' / 'workflows' / 'extension-manager.yml').read_text(encoding='utf-8')
BOOTSTRAP = (ROOT / 'scripts' / 'bootstrap-chat-platform.ps1').read_text(encoding='utf-8')


class ExtensionManagerBoundaryTests(unittest.TestCase):
    def test_adaptive_runtime_is_not_part_of_baseline_chat_profile_gate(self):
        self.assertNotIn('adaptive-runtime:', CHAT_PROFILES)
        self.assertNotIn('runtime/1mcp-adaptive-shim/**', CHAT_PROFILES)
        self.assertNotIn('tests/adaptive-mcp-acceptance.mjs', CHAT_PROFILES)
        self.assertNotIn("Get-Content 'runtime/chat-profiles/adaptive/mcp.json'", CHAT_PROFILES)
        self.assertIn('Prove promoted six-tool semantic profile routes through the public manager', CHAT_PROFILES)

    def test_optional_extension_workflow_owns_1mcp_adaptive_acceptance(self):
        self.assertIn('name: Optional Extension Manager Acceptance', EXTENSIONS)
        self.assertIn('runtime/1mcp-adaptive-shim/**', EXTENSIONS)
        self.assertIn('runtime/chat-profiles/adaptive/**', EXTENSIONS)
        self.assertIn('tests/adaptive-mcp-acceptance.mjs', EXTENSIONS)
        self.assertIn('EXTENSION_MANAGER=1mcp-optional-internal', EXTENSIONS)
        self.assertIn('BASELINE_SEMANTIC_DEPENDENCY=False', EXTENSIONS)

    def test_normal_bootstrap_remains_1mcp_independent(self):
        self.assertNotIn('OneMcpPackage', BOOTSTRAP)
        self.assertNotIn("Require-Command 'npx.cmd'", BOOTSTRAP)
        self.assertIn('NORMAL_SEMANTIC_1MCP_REQUIRED=False', BOOTSTRAP)
        self.assertIn('EXTENSION_MANAGER=optional-1mcp', BOOTSTRAP)


if __name__ == '__main__':
    unittest.main()
