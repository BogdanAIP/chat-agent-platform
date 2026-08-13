import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "runtime" / "chat-profiles" / "adaptive" / "mcp.json"
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

    def test_adaptive_uses_stable_lazy_surface_without_async_loading(self):
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

    def test_adaptive_runtime_is_tracked_by_status_and_stop(self):
        self.assertIn("chat-profiles\\adaptive\\mcp.json", self.status_profile)
        self.assertIn("RuntimeReadyOnly = $true", self.status_profile)
        self.assertIn("/health/ready", self.status_profile)
        self.assertIn("chat-profiles\\adaptive\\mcp.json", self.stop_profile)


if __name__ == "__main__":
    unittest.main()
