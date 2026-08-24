from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_START = (ROOT / "scripts" / "start-semantic-profile.ps1").read_text(encoding="utf-8")
LAUNCHER = (
    ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-projection-launcher.mjs"
).read_text(encoding="utf-8")


class SemanticStartSixToolContractTests(unittest.TestCase):
    def test_legacy_startup_guard_requires_exact_six_tool_surface(self):
        for name in (
            "'procedure_run'",
            "'web_interact'",
            "'web_observe'",
            "'web_open'",
            "'workspace_read'",
            "'workspace_write'",
        ):
            self.assertIn(name, LEGACY_START)
        self.assertIn("SEMANTIC_TOOL_COUNT=6", LEGACY_START)
        self.assertNotIn("SEMANTIC_TOOL_COUNT=5", LEGACY_START)

    def test_legacy_startup_guard_checks_inventory_before_reporting_ready(self):
        inventory_check = LEGACY_START.index("if (($tools -join")
        ready_marker = LEGACY_START.index("CHAT_PROFILE_STATUS=ready")
        self.assertLess(inventory_check, ready_marker)
        self.assertIn("Semantic profile surface drifted", LEGACY_START)

    def test_canonical_launcher_live_inventory_guard_precedes_working_child(self):
        self.assertIn("new Client({", LAUNCHER)
        self.assertIn("new StdioClientTransport({", LAUNCHER)
        self.assertIn("await client.listTools()", LAUNCHER)
        self.assertIn("EXPECTED_SEMANTIC_TOOLS", LAUNCHER)
        for name in (
            "'procedure_run'",
            "'web_interact'",
            "'web_observe'",
            "'web_open'",
            "'workspace_read'",
            "'workspace_write'",
        ):
            self.assertIn(name, LAUNCHER)

        guard = LAUNCHER.index("await assertExpectedSemanticInventory(semanticEntry)")
        child = LAUNCHER.index("const child = spawn(process.execPath, [semanticEntry]")
        self.assertLess(guard, child)
        self.assertIn("semantic launcher live inventory preflight failed", LAUNCHER)
        self.assertIn("process.exit(1)", LAUNCHER[guard:child])

    def test_inventory_guard_has_explicit_negative_test_entry_mode(self):
        self.assertIn("--verify-inventory-entry", LAUNCHER)
        self.assertIn("expected exactly:", LAUNCHER)


if __name__ == "__main__":
    unittest.main()
