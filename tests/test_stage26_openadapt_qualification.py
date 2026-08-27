import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "config" / "stage26-openadapt-lock.json"
DOC_PATH = ROOT / "project-context" / "STAGE26_1A_OPENADAPT_QUALIFICATION.md"
SCRIPT_PATH = ROOT / "scripts" / "stage26-openadapt-qualification.ps1"


class Stage26OpenAdaptQualificationContractTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.doc = DOC_PATH.read_text(encoding="utf-8")
        self.script = SCRIPT_PATH.read_text(encoding="utf-8")

    def test_lock_is_exact_and_non_authorizing(self):
        self.assertEqual(self.lock["schema_version"], 1)
        self.assertEqual(self.lock["python"]["required_major_minor"], "3.12")

        upstreams = self.lock["upstreams"]
        self.assertEqual(
            set(upstreams),
            {"openadapt_flow", "openadapt_capture", "openadapt_desktop"},
        )
        for name, entry in upstreams.items():
            self.assertRegex(entry["commit"], r"^[0-9a-f]{40}$", name)
            self.assertEqual(entry["license"], "MIT", name)
            self.assertTrue(entry["declared_version"], name)

        self.assertEqual(upstreams["openadapt_flow"]["declared_version"], "1.31.0")
        self.assertEqual(upstreams["openadapt_capture"]["declared_version"], "1.2.2")
        self.assertEqual(upstreams["openadapt_desktop"]["declared_version"], "0.15.0")
        self.assertEqual(
            upstreams["openadapt_desktop"]["embedded_flow_version_at_pin"],
            "1.27.1",
        )
        self.assertIn("effect-evidence provider", upstreams["openadapt_flow"]["role"])
        self.assertNotEqual(upstreams["openadapt_flow"]["role"].strip(), "verifier")

        non_goals = "\n".join(self.lock["non_goals"])
        self.assertIn("only planner/intelligence", non_goals)
        self.assertIn("execute_windows", non_goals)
        self.assertIn("six public semantic tool names", non_goals)
        self.assertIn("project Verification Kernel and Finish Gate", non_goals)
        self.assertIn("project-wide WorkingState", non_goals)

    def test_doc_preserves_chatgpt_only_and_fail_closed_boundaries(self):
        for tool in (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
        ):
            self.assertIn(tool, self.doc)

        for required in (
            "Ordinary ChatGPT remains the only planner/intelligence",
            "Decision: ADOPT",
            "Decision: ADAPT",
            "HALT/ABSTAIN",
            "raw capture",
            "F16",
            "/execute_windows",
            "do not auto-generate hundreds of public MCP tools",
        ):
            self.assertIn(required, self.doc)

    def test_preflight_is_isolated_and_does_not_kill_user_chrome(self):
        self.assertIn("py.exe", self.script)
        self.assertIn("-m', 'venv'", self.script)
        self.assertIn("direct_url.json", self.script)
        self.assertIn("PLAYWRIGHT_BROWSERS_PATH", self.script)
        self.assertIn("openadapt-flow[windows]", self.script)
        self.assertIn("openadapt-flow[browser,windows]", self.script)
        self.assertIn("PROBE_ERROR", self.script)
        self.assertIn("Get-Process chrome", self.script)
        self.assertNotRegex(self.script, re.compile(r"Stop-Process\s+.*chrome", re.I))
        self.assertNotRegex(self.script, re.compile(r"taskkill.*chrome", re.I))
        self.assertNotIn("semantic-projection-runtime.ps1 -Action", self.script)
        self.assertNotIn("start-chat-profile.ps1", self.script)


if __name__ == "__main__":
    unittest.main()
