from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHAT_PROFILES = (ROOT / '.github' / 'workflows' / 'chat-profiles.yml').read_text(encoding='utf-8')
SEMANTIC = (ROOT / '.github' / 'workflows' / 'semantic-projection.yml').read_text(encoding='utf-8')
EXTENSIONS = (ROOT / '.github' / 'workflows' / 'extension-manager.yml').read_text(encoding='utf-8')
CI = (ROOT / '.github' / 'workflows' / 'ci.yml').read_text(encoding='utf-8')
BOOTSTRAP = (ROOT / 'scripts' / 'bootstrap-chat-platform.ps1').read_text(encoding='utf-8')
LIFECYCLE = (ROOT / 'scripts' / 'bootstrap-manager-lifecycle.ps1').read_text(encoding='utf-8')
MANAGER = (ROOT / 'scripts' / 'bootstrap-manager-runtime.ps1').read_text(encoding='utf-8')
INSTALLER = (ROOT / 'scripts' / 'install-extension-manager.ps1').read_text(encoding='utf-8')
EXTENSION_DOC = (ROOT / 'project-context' / 'EXTENSION_MANAGER.md').read_text(encoding='utf-8')


class ExtensionManagerBoundaryTests(unittest.TestCase):
    def test_baseline_chat_profile_gate_does_not_start_legacy_1mcp_runtime(self):
        for forbidden in (
            'adaptive-runtime:',
            'runtime/1mcp-adaptive-shim/**',
            'tests/adaptive-mcp-acceptance.mjs',
            './scripts/start-local-bridge.ps1',
            './scripts/start-chat-profile.ps1',
            './scripts/stop-chat-profile.ps1',
            'npx --version',
            'Prove direct profile switching and isolation',
            'Prove public manager can observe and clean conflicting runtime scopes',
        ):
            self.assertNotIn(forbidden, CHAT_PROFILES)
        self.assertIn('Prove promoted six-tool semantic profile routes through the public manager', CHAT_PROFILES)
        self.assertIn('SEMANTIC_PUBLIC_MANAGER_1MCP_REQUIRED=False', CHAT_PROFILES)

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
        self.assertNotIn('./scripts/stop-chat-profile.ps1', CI)
        self.assertIn('Prove clean public semantic manager status without 1MCP', CI)
        self.assertIn('BASELINE_1MCP_RUNTIME_REQUIRED=False', CI)

    def test_optional_extension_workflow_owns_all_live_1mcp_runtime_acceptance(self):
        self.assertIn('name: Optional Extension Manager Acceptance', EXTENSIONS)
        self.assertIn('runtime/1mcp-adaptive-shim/**', EXTENSIONS)
        self.assertIn('runtime/chat-profiles/adaptive/**', EXTENSIONS)
        self.assertIn('runtime/chat-profiles/files-readonly/**', EXTENSIONS)
        self.assertIn('runtime/chat-profiles/browser-isolated/**', EXTENSIONS)
        self.assertIn('scripts/install-extension-manager.ps1', EXTENSIONS)
        self.assertIn('Prove opt-in Extension Manager install lifecycle', EXTENSIONS)
        self.assertIn('Prove legacy internal 1MCP runtime remains available when explicitly tested', EXTENSIONS)
        self.assertIn('Prove legacy files and browser profile switching and isolation', EXTENSIONS)
        self.assertIn('Prove optional manager can observe and clean conflicting legacy runtime scopes', EXTENSIONS)
        self.assertIn('./scripts/start-local-bridge.ps1 -Port 3059', EXTENSIONS)
        self.assertIn('./scripts/start-chat-profile.ps1 -Profile files-readonly', EXTENSIONS)
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

    def test_normal_bootstrap_uses_semantic_core_not_legacy_install(self):
        self.assertNotIn('OneMcpPackage', BOOTSTRAP)
        self.assertNotIn("Require-Command 'npx.cmd'", BOOTSTRAP)
        self.assertNotIn('Install-ChatManager -CommandPath', BOOTSTRAP)
        self.assertIn('Initialize-ChatSemanticCore', BOOTSTRAP)
        self.assertIn('NORMAL_SEMANTIC_1MCP_REQUIRED=False', BOOTSTRAP)
        self.assertIn('EXTENSION_MANAGER=optional-1mcp', BOOTSTRAP)
        self.assertIn('Save-ChatProtectedApiKeyIfMissing', LIFECYCLE)
        self.assertIn('-Action SetProfile', LIFECYCLE)
        self.assertIn('-Profile semantic', LIFECYCLE)
        self.assertIn('DEFAULT_TUNNEL_BINDING=direct-stdio', LIFECYCLE)
        self.assertIn('LEGACY_1MCP_INSTALL_PATH_USED=False', LIFECYCLE)

    def test_extension_manager_doc_matches_runtime_paths_and_default(self):
        self.assertIn(r'%LOCALAPPDATA%\ChatAgentPlatform\tunnel\local-1mcp.yaml', EXTENSION_DOC)
        self.assertNotIn(r'%LOCALAPPDATA%\ChatAgentPlatform\config\openai-tunnel-client\local-1mcp.yaml', EXTENSION_DOC)
        self.assertIn('extension_manager_included = false', EXTENSION_DOC)
        self.assertIn('profile = semantic', EXTENSION_DOC)
        self.assertIn('tunnel binding = direct-stdio', EXTENSION_DOC)
        self.assertIn('normal bootstrap does not call the legacy 1MCP-oriented controller install path', EXTENSION_DOC)


if __name__ == '__main__':
    unittest.main()
