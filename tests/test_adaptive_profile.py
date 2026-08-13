import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "runtime" / "chat-profiles" / "adaptive" / "mcp.json"
ADAPTIVE_SHIM = ROOT / "runtime" / "1mcp-adaptive-shim"
START_LOCAL = ROOT / "scripts" / "start-local-bridge.ps1"
START_PROFILE = ROOT / "scripts" / "start-chat-profile.ps1"
STATUS_PROFILE = ROOT / "scripts" / "status-chat-profile.ps1"
STOP_PROFILE = ROOT / "scripts" / "stop-chat-profile.ps1"


class AdaptiveProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(ADAPTIVE.read_text(encoding="utf-8"))
        cls.start_local = START_LOCAL.read_text(encoding="utf-8")
        cls.start_profile = START_PROFILE.read_text(encoding="utf-8")
        cls.status_profile = STATUS_PROFILE.read_text(encoding="utf-8")
        cls.stop_profile = STOP_PROFILE.read_text(encoding="utf-8")
        cls.shim_manifest = json.loads(
            (ADAPTIVE_SHIM / "package.json").read_text(encoding="utf-8")
        )
        cls.shim_patch = (
            ADAPTIVE_SHIM / "scripts" / "apply-compatibility-patch.mjs"
        ).read_text(encoding="utf-8")
        cls.shim_bin = (
            ADAPTIVE_SHIM / "bin" / "1mcp-adaptive.mjs"
        ).read_text(encoding="utf-8")

    def test_adaptive_catalog_contains_pinned_filesystem_and_playwright(self):
        servers = self.config["mcpServers"]
        self.assertEqual(set(servers), {"filesystem", "playwright"})
        self.assertIn(
            "@modelcontextprotocol/server-filesystem@2026.7.10",
            " ".join(servers["filesystem"]["args"]),
        )
        self.assertIn(
            "@playwright/mcp@0.0.78",
            " ".join(servers["playwright"]["args"]),
        )

    def test_backends_start_disabled_for_task_driven_activation(self):
        for server in self.config["mcpServers"].values():
            self.assertIs(server.get("disabled"), True)

    def test_existing_capability_restrictions_survive_in_adaptive_catalog(self):
        filesystem_disabled = set(
            self.config["mcpServers"]["filesystem"]["disabledTools"]
        )
        self.assertTrue(
            {"create_directory", "write_file", "edit_file", "move_file"}
            <= filesystem_disabled
        )
        browser_disabled = set(
            self.config["mcpServers"]["playwright"]["disabledTools"]
        )
        self.assertTrue(
            {
                "browser_run_code_unsafe",
                "browser_evaluate",
                "browser_file_upload",
                "browser_network_request",
            }
            <= browser_disabled
        )

    def test_adaptive_uses_stable_lazy_surface_with_compatibility_launcher(self):
        self.assertIn("[switch]$EnableLazyLoading", self.start_local)
        self.assertIn("[switch]$DisableAsyncLoading", self.start_local)
        self.assertIn("--enable-lazy-loading", self.start_local)
        self.assertIn("--enable-async-loading", self.start_local)
        self.assertIn("[string]$InternalTools", self.start_local)
        self.assertIn("--enable-internal-tools", self.start_local)
        self.assertIn("--internal-tools", self.start_local)
        self.assertIn("[switch]$RuntimeReadyOnly", self.start_local)

        self.assertIn("'adaptive'", self.start_profile)
        self.assertIn("EnableLazyLoading = $true", self.start_profile)
        self.assertIn("DisableAsyncLoading = $true", self.start_profile)
        self.assertIn(
            "InternalTools = 'list,status,enable,disable,reload'",
            self.start_profile,
        )
        self.assertIn("OneMcpLauncherPackage", self.start_local)
        self.assertIn("OneMcpLauncherExecutable", self.start_local)
        self.assertIn("New-AdaptiveLauncherPackage", self.start_profile)
        self.assertIn("LauncherExecutable = '1mcp-adaptive'", self.start_profile)

    def test_adaptive_compatibility_patch_is_exact_and_hash_guarded(self):
        self.assertEqual(
            self.shim_manifest["dependencies"],
            {"@1mcp/agent": "0.35.0-beta.3"},
        )
        self.assertEqual(
            self.shim_manifest["bin"],
            {"1mcp-adaptive": "bin/1mcp-adaptive.mjs"},
        )
        self.assertEqual(
            self.shim_manifest["scripts"]["postinstall"],
            "node scripts/apply-compatibility-patch.mjs",
        )
        self.assertIn("@1mcp/agent/build/index.js", self.shim_bin)
        self.assertIn(
            "371587f5d19201f33e2fd18c2ad33b7db1552e763d80b0c36783e71754d09d1e",
            self.shim_patch,
        )
        self.assertIn(
            "02bfaed53dbbc94788feef13680d1fa1ee4b90c1ed04b9d53929c922a0d52ec3",
            self.shim_patch,
        )
        self.assertIn("loadDeclaredServerConfigs", self.shim_patch)
        self.assertIn("lazyLoadingOrchestrator?.refreshCapabilities", self.shim_patch)
        self.assertNotIn("await this.notifyBackendCapabilityListsChanged()", self.shim_patch)

    def test_adaptive_runtime_is_tracked_by_status_and_stop(self):
        self.assertIn("chat-profiles\\adaptive\\mcp.json", self.status_profile)
        self.assertIn("RuntimeReadyOnly = $true", self.status_profile)
        self.assertIn("/health/ready", self.status_profile)
        self.assertIn("chat-profiles\\adaptive\\mcp.json", self.stop_profile)

    def test_adaptive_start_recovers_persisted_enable_state(self):
        self.assertIn("Reset-AdaptiveCatalogToDisabled", self.start_profile)
        self.assertIn("ADAPTIVE_CATALOG_RESET=all-disabled", self.start_profile)
        self.assertRegex(
            self.start_profile,
            r"Reset-AdaptiveCatalogToDisabled -ConfigPath \$selectedConfig",
        )


if __name__ == "__main__":
    unittest.main()
