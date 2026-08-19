import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts" / "stage26-window-scoped-uia-resolver.py"
DRIVER = ROOT / "scripts" / "stage26-window-scoped-uia-benchmark.py"
HARNESS = ROOT / "scripts" / "stage26-window-scoped-uia-benchmark.ps1"


class Stage26WindowScopedUiaResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = RESOLVER.read_text(encoding="utf-8")
        self.driver = DRIVER.read_text(encoding="utf-8")
        self.harness = HARNESS.read_text(encoding="utf-8")

    def test_python_assets_parse(self):
        ast.parse(self.resolver)
        ast.parse(self.driver)

    def test_native_uia_conditions_replace_python_desktop_dfs(self):
        self.assertIn("CreatePropertyCondition", self.resolver)
        self.assertIn("CreateAndCondition", self.resolver)
        self.assertIn("root.FindAll(TREE_SCOPE_CHILDREN, window_condition)", self.resolver)
        self.assertIn("window.FindAll(TREE_SCOPE_DESCENDANTS, condition)", self.resolver)
        self.assertNotIn("GetChildren", self.resolver)
        self.assertNotIn("stack.extend", self.resolver)

    def test_search_is_scoped_by_exact_window_name(self):
        self.assertIn('window_name = locator.get("window_name")', self.resolver)
        self.assertIn("auto.ControlType.WindowControl", self.resolver)
        self.assertIn("auto.PropertyId.NameProperty", self.resolver)
        self.assertIn("window_name", self.resolver)
        self.assertIn("desktop_fallback_calls", self.resolver)

    def test_automation_id_has_a_direct_native_condition_path(self):
        self.assertIn("auto.PropertyId.AutomationIdProperty", self.resolver)
        self.assertIn("automation_id_condition_calls", self.resolver)
        self.assertIn("role_name_condition_calls", self.resolver)
        self.assertIn("auto.PropertyId.ControlTypeProperty", self.resolver)

    def test_upstream_act_and_fingerprint_semantics_are_reused(self):
        self.assertIn("upstream._perform_uia_initialized", self.resolver)
        self.assertIn("upstream._find_candidates = self._direct_find_candidates", self.resolver)
        self.assertIn("upstream._find_candidates = original", self.resolver)
        self.assertNotIn("GetInvokePattern", self.resolver)
        self.assertNotIn("SetFocus", self.resolver)
        self.assertNotIn("expected_fingerprint", self.resolver)

    def test_non_find_uia_routes_remain_exact_upstream(self):
        self.assertIn('if operation not in {"find", "act"}', self.resolver)
        self.assertIn("return upstream._perform_uia(operation, payload)", self.resolver)
        self.assertIn("delegated_uia_calls", self.resolver)

    def test_benchmark_injects_only_uia_function(self):
        self.assertIn("WindowScopedUiaResolver()", self.driver)
        self.assertIn("input_fn=baseline.accepted._qualification_input", self.driver)
        self.assertIn("uia_fn=resolver.perform", self.driver)
        self.assertIn("baseline._run_cycle", self.driver)
        self.assertIn("baseline.EXPECTED_OPERATIONS", self.driver)

    def test_all_structural_operations_must_use_window_scoped_path(self):
        self.assertIn("expected_scoped_calls = total_cycles * 8", self.driver)
        self.assertIn(
            "resolver.stats.window_scoped_find_calls == expected_scoped_calls",
            self.driver,
        )
        self.assertIn("resolver.stats.desktop_fallback_calls == 0", self.driver)
        self.assertIn("$result.resolver_stats.desktop_fallback_calls -eq 0", self.harness)

    def test_stage1d_persistent_environment_is_reused_not_reinstalled(self):
        self.assertIn("hot-runtime-env", self.harness)
        self.assertIn("environment_reused = $true", self.harness)
        self.assertIn("Stage 26.1D persistent benchmark environment is missing", self.harness)
        self.assertNotIn("pip install", self.harness)
        self.assertNotIn("'-m', 'venv'", self.harness)
        self.assertNotIn("RebuildEnvironment", self.harness)

    def test_no_generic_execution_or_production_chat_surface(self):
        combined = "\n".join((self.resolver, self.driver, self.harness))
        self.assertNotRegex(self.resolver, re.compile(r"\bexec\s*\(", re.I))
        self.assertNotRegex(self.resolver, re.compile(r"\beval\s*\(", re.I))
        self.assertNotIn("subprocess", self.resolver)
        self.assertNotIn("os.system", self.resolver)
        for forbidden in (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
            "semantic-projection-runtime.ps1 -Action",
            "start-chat-profile.ps1",
        ):
            self.assertNotIn(forbidden, combined)

    def test_safety_evidence_is_still_hard_gated(self):
        self.assertIn('"unrelated_window_action_count": 0', self.driver)
        self.assertIn('"false_action_count": 0', self.driver)
        self.assertIn("fixture_process_reused", self.driver)
        self.assertIn("agent_process_reused", self.driver)
        self.assertIn("CHROME_SURVIVAL_PASS", self.harness)
        self.assertIn("STAGE26_1E_WINDOW_SCOPED_RESULT", self.harness)


if __name__ == "__main__":
    unittest.main()
