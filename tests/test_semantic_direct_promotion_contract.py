from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = (ROOT / "scripts" / "chat-platform.ps1").read_text(encoding="utf-8")
DIRECT = (ROOT / "scripts" / "semantic-direct-controller.ps1").read_text(encoding="utf-8")
BOOTSTRAP = (ROOT / "scripts" / "bootstrap-chat-platform.ps1").read_text(encoding="utf-8")
BOOTSTRAP_MANAGER = (ROOT / "scripts" / "bootstrap-manager-runtime.ps1").read_text(encoding="utf-8")
BOOTSTRAP_LIFECYCLE = (ROOT / "scripts" / "bootstrap-manager-lifecycle.ps1").read_text(encoding="utf-8")


class SemanticDirectPromotionContractTests(unittest.TestCase):
    def test_public_semantic_routes_to_direct_controller(self):
        self.assertIn('$DirectSemanticProfiles = @(', COMMAND)
        self.assertIn('"semantic",', COMMAND)
        self.assertIn('"semantic-direct"', COMMAND)
        self.assertIn('elseif ($TargetProfile -in $DirectSemanticProfiles)', COMMAND)
        self.assertIn('Get-DirectControllerPath', COMMAND)
        self.assertIn('if ($Profile -in $DirectSemanticProfiles)', COMMAND)
        self.assertIn('"direct-stdio"', COMMAND)

    def test_stage24_semantic_settings_are_migration_normalized(self):
        self.assertIn('$profileName -in $DirectSemanticProfiles', COMMAND)
        self.assertIn('"direct-stdio"', COMMAND)
        self.assertIn('stale transport marker', COMMAND)

    def test_direct_controller_preserves_public_profile_identity(self):
        self.assertIn("[ValidateSet('semantic', 'semantic-direct')]", DIRECT)
        self.assertIn('function Get-EffectiveProfileName', DIRECT)
        self.assertIn("active_profile = if ($running) { $profileName }", DIRECT)
        self.assertIn("tunnel_binding = 'direct-stdio'", DIRECT)
        self.assertIn("SEMANTIC_PROFILE=$profileName", DIRECT)

    def test_stable_bundle_contains_direct_controller(self):
        self.assertIn("'semantic-direct-controller.ps1'", BOOTSTRAP_MANAGER)
        self.assertIn('-DirectControllerPath $DirectControllerPath', BOOTSTRAP)
        self.assertIn('foreach ($installed in @($CommandPath, $ControllerPath, $DirectControllerPath, $TrayPath))', BOOTSTRAP_MANAGER)
        self.assertIn('Copy-ChatVerifiedFile', BOOTSTRAP_MANAGER)

    def test_bootstrap_profile_helper_accepts_migration_alias(self):
        self.assertIn("[ValidateSet('reference', 'files-readonly', 'browser-isolated', 'semantic', 'semantic-direct', 'adaptive')]", BOOTSTRAP_LIFECYCLE)

    def test_migration_alias_does_not_create_a_five_vs_six_tool_choice(self):
        self.assertIn("SEMANTIC_PUBLIC_TOOL_COUNT=6", BOOTSTRAP)
        self.assertIn("semantic_public_tool_count = 6", BOOTSTRAP_MANAGER)
        self.assertNotIn("TOOL_COUNT=5", BOOTSTRAP + BOOTSTRAP_MANAGER + BOOTSTRAP_LIFECYCLE)
        self.assertNotIn("procedure-qualification", BOOTSTRAP + BOOTSTRAP_MANAGER + BOOTSTRAP_LIFECYCLE)


if __name__ == "__main__":
    unittest.main()
