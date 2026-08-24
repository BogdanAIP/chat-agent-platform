from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
START = (ROOT / "scripts" / "start-semantic-profile.ps1").read_text(encoding="utf-8")


class SemanticStartSixToolContractTests(unittest.TestCase):
    def test_startup_guard_requires_exact_six_tool_surface(self):
        for name in (
            "'procedure_run'",
            "'web_interact'",
            "'web_observe'",
            "'web_open'",
            "'workspace_read'",
            "'workspace_write'",
        ):
            self.assertIn(name, START)
        self.assertIn("SEMANTIC_TOOL_COUNT=6", START)
        self.assertNotIn("SEMANTIC_TOOL_COUNT=5", START)

    def test_startup_guard_checks_inventory_before_reporting_ready(self):
        inventory_check = START.index("if (($tools -join")
        ready_marker = START.index("CHAT_PROFILE_STATUS=ready")
        self.assertLess(inventory_check, ready_marker)
        self.assertIn("Semantic profile surface drifted", START)


if __name__ == "__main__":
    unittest.main()
