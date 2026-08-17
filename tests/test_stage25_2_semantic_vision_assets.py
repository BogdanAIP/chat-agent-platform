from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-projection.mjs"
ROUTER = ROOT / "runtime" / "semantic-projection" / "lib" / "semantic-vision-click-router.mjs"
TARGET_NODE = ROOT / "runtime" / "semantic-projection" / "tests" / "target-stage25-2-real-f16-escalation.mjs"
TARGET_WRAPPER = ROOT / "scripts" / "test-stage25-2-real-f16-escalation.ps1"
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"


class Stage252SemanticVisionAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = CORE.read_text(encoding="utf-8")
        cls.router = ROUTER.read_text(encoding="utf-8")
        cls.target_node = TARGET_NODE.read_text(encoding="utf-8")
        cls.target_wrapper = TARGET_WRAPPER.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    def test_public_surface_stays_exactly_five_tools(self) -> None:
        self.assertEqual(self.core.count("server.registerTool("), 5)
        for name in ("workspace_read", "workspace_write", "web_open", "web_observe", "web_interact"):
            self.assertIn(f"'{name}'", self.core)
        for forbidden in ("tool_invoke", "tool_schema", "mcp_enable", "browser_evaluate", "browser_file_upload"):
            self.assertNotIn(forbidden, self.core)

    def test_visual_escalation_is_bounded_inside_web_interact(self) -> None:
        for marker in (
            "visualFallbackSchema",
            "targetText",
            "instruction",
            "visualFallback supports only one left single click",
            "web_interact type does not accept visualFallback",
            "browser_take_screenshot",
            "browser_mouse_click_xy",
            "--caps",
            "vision",
        ):
            self.assertIn(marker, self.core)
        self.assertNotIn("kind: z.", self.core)

    def test_router_never_trusts_planner_for_visual_kind_or_separate_preflight_name(self) -> None:
        self.assertIn("kind: 'labeled_button'", self.router)
        self.assertIn("semanticName must normalize exactly to targetText", self.router)
        self.assertIn("semantic-ambiguity-visual-escalation-not-promoted", self.router)
        self.assertIn("semantic-click-error", self.router)
        self.assertIn("semantic-unique-enabled-button-state", self.router)
        self.assertNotIn("fallback.kind", self.router)

    def test_abstain_is_not_reported_as_backend_error(self) -> None:
        self.assertIn("outcome?.status === 'abstain'", self.core)
        self.assertIn("web_interact abstained with no action", self.core)
        self.assertIn("performed no action because of an error", self.core)

    def test_target_harness_exercises_public_semantic_server_and_vlm_start_boundary(self) -> None:
        for marker in (
            "semantic-projection-launcher.mjs",
            "web_interact",
            "semantic-unique",
            "semantic-enabled-state",
            "semantic-ambiguity",
            "semantic-miss-visual-hit",
            "semantic-miss-absent",
            "semantic_cases_started_vlm",
            "runtime_running_after",
            "acceptance_pass",
        ):
            self.assertIn(marker, self.target_node)
        self.assertNotIn("createSemanticVisionClickRouter", self.target_node)
        self.assertNotIn("RuntimeBackedVisualGrounder", self.target_node)

    def test_target_wrapper_keeps_resource_and_chrome_guards(self) -> None:
        for marker in (
            "EmergencyRamFloorGB = 0.30",
            "CHAT_VISION_RUNTIME_TEST_MODE",
            "Get-Process chrome",
            "SAFETY_STOP=",
            "MIN_RAM_FREE_GB=",
            "VISION_RUNTIME_RUNNING_AFTER_TEST=",
            "CHROME_RUNNING_AFTER_TEST=",
            "STAGE25_2_RESULT_PATH",
        ):
            self.assertIn(marker, self.target_wrapper)
        self.assertNotIn("Stop-Process -Name", self.target_wrapper)
        self.assertNotIn("taskkill", self.target_wrapper.lower())

    def test_bootstrap_installs_public_fallback_dependency_closure(self) -> None:
        for marker in (
            "semantic-vision-click-router.mjs",
            "runtime-backed-visual-grounder.mjs",
            "local-vision-runtime.ps1",
            "verify-local-vision-listener.ps1",
            "production-visual-grounder.py",
            "local_vision_adapter\\native_bbox.py",
            "local_vision_adapter\\production_grounder.py",
            "local-vision-runtime.json",
        ):
            self.assertIn(marker, self.bootstrap)


if __name__ == "__main__":
    unittest.main()
