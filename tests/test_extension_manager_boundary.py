from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHAT_PROFILES = (ROOT / '.github' / 'workflows' / 'chat-profiles.yml').read_text(encoding='utf-8')
SEMANTIC = (ROOT / '.github' / 'workflows' / 'semantic-projection.yml').read_text(encoding='utf-8')
EXTENSIONS = (ROOT / '.github' / 'workflows' / 'extension-manager.yml').read_text(encoding='utf-8')
CI = (ROOT / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
BOOTSTRAP = (ROOT / 'scripts' / 'bootstrap-chat-platform.ps1').read_text(encoding='utf-8')
MANAGER = (ROOT / 'scripts' / 'bootstrap-manager-runtime.ps1').read_text(encoding='utf-8')
INSTALLER = (ROOT / 'scripts' / 'install-extension-manager.ps1').read_text(encoding='utf-8')


class ExtensionManagerBoundaryTests(unittest.TestCase):
    def test_adaptive_runtime_is_not_part_of_baseline_chat_profile_gate(self):
        self.assertNotIn('adaptive-runtime:', CHAT_PROFILES)
        self.assertNotIn('runtime/1mcp-adaptive-shim/**', CHAT_PROFILES)
        self.assertNotIn('tests/adaptive-mcp-acceptance.mjs', CHAT_PROFILES)
        self.assertNotIn("Get-Content 'runtime/chat-profiles/adaptive/mcp.json'", CHAT_PROFILES)
        self.assertIn('Prove promoted six-tool semantic profile routes through the public manager', CHAT_PROFILES)

    def test_required_semantic_projection_gate_does_not_use_1mcp(self):
        self.assertNotIn('@1mcp/agent', SEMANTIC)
        self.assertNotIn('real 1MCP lifecycle', SEMANTIC)
        self.assertNotIn('SEMANTIC_PROFILE_1MCP', SEMANTIC)
        self.assertIn('SEMANTIC_INSTALLED_1MCP_REQUIRED=False', SEMANTIC)
        self.assertIn('Run canonical six-tool acceptance and internal base regressions', SEMANTIC)
        self.assertIn('Prove semantic runtime from standalone installed layout', SEMANTIC)

    def test_baseline_bundle_does_not_install_or_verify_adaptive_1mcp(self):
        install_body = MANAGER.split('function Install-ChatManagerBundle', 1)[1]
        self.assertNotIn("runtime\\chat-profiles\\adaptive\\mcp.json", install_body)
        self.assertNotIn("runtime\\1mcp-adaptive-shim\\package.json", install_body)
        self.assertNotIn('Assert-ChatInstalledAdaptiveRuntime -AppRuntimeDir', install_body)
        self.assertIn('extension_manager_included = $false', install_body)
        self.assertIn('EXTENSION_MANAGER_INCLUDED=False', install_body)

    def test_general_ci_does_not_start_1mcp_runtime(self):
        self.assertNotIn('Prove local MCP runtime on Windows', CI)
        self.assertNotIn('./scripts/start-local-bridge.ps1 -Port 3059', CI)
        self.assertIn('BASELINE_1MCP_RUNTIME_REQUIRED=False', CI)

    def test_optional_extension_workflow_owns_1mcp_runtime_acceptance(self):
        self.assertIn('name: Optional Extension Manager Acceptance', EXTENSIONS)
        self.assertIn('runtime/1mcp-adaptive-shim/**', EXTENSIONS)
        self.assertIn('runtime/chat-profiles/adaptive/**', EXTENSIONS)
        self.assertIn('scripts/install-extension-manager.ps1', EXTENSIONS)
        self.assertIn('Prove opt-in Extension Manager install lifecycle', EXTENSIONS)
        self.assertIn('Prove legacy internal 1MCP runtime remains available when explicitly tested', EXTENSIONS)
        self.assertIn('./scripts/start-local-bridge.ps1 -Port 3059', EXTENSIONS)
        self.assertIn('tests/adaptive-mcp-acceptance.mjs', EXTENSIONS)
        self.assertIn('EXTENSION_MANAGER=1mcp-optional-internal', EXTENSIONS)
        self.assertIn('BASELINE_SEMANTIC_DEPENDENCY=False', EXTENSIONS)

    def test_opt_in_installer_is_explicit_and_does_not_modify_baseline_transport(self):
        self.assertIn("[ValidateSet('Install', 'Remove', 'Status')]", INSTALLER)
        self.assertIn("extension_manager = '1mcp'", INSTALLER)
        self.assertIn("role = 'optional-internal-extension-manager'", INSTALLER)
        self.assertIn('baseline_semantic_dependency = $false', INSTALLER)
        self.assertIn('Assert-ChatInstalledAdaptiveRuntime -AppRuntimeDir', INSTALLER)
        self.assertNotIn('semantic-direct-controller.ps1', INSTALLER)
        self.assertNotIn('tunnel.json', INSTALLER)
        self.assertNotIn('desired-state.json', INSTALLER)

    def test_normal_bootstrap_remains_1mcp_independent(self):
        self.assertNotIn('OneMcpPackage', BOOTSTRAP)
        self.assertNotIn("Require-Command 'npx.cmd'", BOOTSTRAP)
        self.assertIn('NORMAL_SEMANTIC_1MCP_REQUIRED=False', BOOTSTRAP)
        self.assertIn('EXTENSION_MANAGER=optional-1mcp', BOOTSTRAP)


if __name__ == '__main__':
    unittest.main()
