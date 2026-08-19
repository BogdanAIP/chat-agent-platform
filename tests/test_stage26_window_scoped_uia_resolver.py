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

    def test_window_binding_uses_pid_scoped_win32_hwnds_not_desktop_uia_walk(self):
        self.assertIn("EnumWindows", self.resolver)
        self.assertIn("GetWindowThreadProcessId", self.resolver)
        self.assertIn("auto.ControlFromHandle(hwnd)", self.resolver)
        self.assertIn("expected_process_id", self.resolver)
        self.assertIn("window_name_match_count", self.resolver)
        self.assertNotIn("GetRootControl", self.resolver)
        self.assertNotIn("GetChildren", self.resolver)
        self.assertNotIn("root.Element.FindAll", self.resolver)
        self.assertNotIn("stack.extend", self.resolver)

    def test_window_binding_is_bounded_and_fail_closed(self):
        self.assertIn("_MAX_ENUM_WINDOWS = 4096", self.resolver)
        self.assertIn("window_context_unbound", self.resolver)
        self.assertIn("window_enumeration_truncated", self.resolver)
        self.assertIn("window_binding_failures", self.resolver)
        self.assertIn("window_binding_ambiguities", self.resolver)

    def test_target_search_is_native_and_only_inside_bound_window(self):
        self.assertIn("CreatePropertyCondition", self.resolver)
        self.assertIn("CreateAndCondition", self.resolver)
        self.assertIn("window.Element.FindAll(", self.resolver)
        self.assertIn("TREE_SCOPE_DESCENDANTS", self.resolver)
        self.assertIn("elements.Length", self.resolver)
        self.assertIn("elements.GetElement(index)", self.resolver)
        self.assertIn("auto.Control.CreateControlFromElement(raw)", self.resolver)

    def test_search_is_scoped_by_exact_normalized_window_name(self):
        self.assertIn('window_name = locator.get("window_name")', self.resolver)
        self.assertIn("_normalize_name", self.resolver)
        self.assertIn('ControlTypeName", ""', self.resolver)
        self.assertIn('!= "WindowControl"', self.resolver)
        self.assertIn("observed_name == expected_name", self.resolver)

    def test_window_binding_happens_before_native_condition_client_creation(self):
        function_start = self.resolver.index("def _direct_find_candidates")
        function_end = self.resolver.index("\n    def perform", function_start)
        function = self.resolver[function_start:function_end]
        bind_index = function.index("windows = self._find_target_windows(auto, window_name)")
        client_index = function.index("auto_impl._AutomationClient.instance().IUIAutomation")
        self.assertLess(bind_index, client_index)
        self.assertIn("Physical qualification proved", function)

    def test_pinned_uiautomation_internal_client_is_imported_explicitly(self):
        self.assertIn(
            "from uiautomation import uiautomation as auto_impl",
            self.resolver,
        )
        self.assertIn(
            "auto_impl._AutomationClient.instance().IUIAutomation",
            self.resolver,
        )
        self.assertNotIn(
            "client = auto._AutomationClient.instance().IUIAutomation",
            self.resolver,
        )
        self.assertIn("star-import intentionally omits leading-underscore names", self.resolver)

    def test_hidden_uia_failures_are_diagnostic_not_collapsed_silently(self):
        self.assertIn("last_failure_stage", self.resolver)
        self.assertIn("last_failure_detail", self.resolver)
        self.assertIn('"automation_client"', self.resolver)
        self.assertIn('"target_findall"', self.resolver)
        self.assertIn('"target_candidate_match"', self.resolver)
        self.assertIn('"window_match"', self.resolver)
        self.assertIn("conversion_error", self.resolver)

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

    def test_non_actuating_preflight_must_pass_before_cycles(self):
        self.assertIn("resolver.set_expected_process_id(fixture_pid)", self.driver)
        self.assertIn("preflight_locator = baseline.accepted._structural", self.driver)
        self.assertIn("preflight_handle = baseline.accepted._resolve_unique", self.driver)
        self.assertIn('"window_binding_pass": True', self.driver)
        self.assertIn("expected_scoped_calls = total_cycles * 8 + 1", self.driver)
        self.assertIn('result["preflight"]["window_binding_pass"]', self.driver)
        self.assertIn("resolver.stats.window_binding_failures == 0", self.driver)
        self.assertIn("resolver.stats.window_binding_ambiguities == 0", self.driver)

    def test_role_name_path_is_provider_tolerant_inside_bound_window(self):
        self.assertIn("_MAX_WINDOW_CONTROL_SCAN = 512", self.resolver)
        self.assertIn("Provider-tolerant fallback", self.resolver)
        direct_start = self.resolver.index("def _direct_find_candidates")
        direct_end = self.resolver.index("\n    def perform", direct_start)
        direct = self.resolver[direct_start:direct_end]
        self.assertNotIn("auto.PropertyId.NameProperty", direct)
        self.assertIn("candidate.get(key) != expected", direct)

    def test_performance_gate_is_derived_from_physical_stage1d_baseline(self):
        self.assertIn("BASELINE_ACTION_P50_MS = 183606.855", self.driver)
        self.assertIn("BASELINE_ACTION_P95_MS = 185567.403", self.driver)
        self.assertIn("MINIMUM_SPEEDUP = 10.0", self.driver)
        self.assertIn("minimum_speedup_pass", self.driver)
        self.assertIn("and speedup_pass", self.driver)
        self.assertIn("$result.baseline_comparison.minimum_speedup_pass", self.harness)
        self.assertIn("P50_SPEEDUP", self.harness)
        self.assertIn("P95_SPEEDUP", self.harness)

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
