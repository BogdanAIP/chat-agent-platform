import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "scripts" / "stage26-windows-hot-runtime-benchmark.py"
HARNESS = ROOT / "scripts" / "stage26-windows-hot-runtime-benchmark.ps1"
FIXTURE = ROOT / "scripts" / "stage26-windows-hot-runtime-fixture.ps1"


class Stage26WindowsHotRuntimeBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.benchmark = BENCHMARK.read_text(encoding="utf-8")
        self.harness = HARNESS.read_text(encoding="utf-8")
        self.fixture = FIXTURE.read_text(encoding="utf-8")

    def test_benchmark_python_parses(self):
        ast.parse(self.benchmark)

    def test_reuses_exact_accepted_executor_seam_instead_of_copying_it(self):
        self.assertIn(
            'ACCEPTED_DRIVER_PATH = SCRIPT_DIR / "stage26-openadapt-windows-executor-driver.py"',
            self.benchmark,
        )
        self.assertIn("importlib.util.spec_from_file_location", self.benchmark)
        self.assertIn("create_server(config, input_fn=accepted._qualification_input)", self.benchmark)
        self.assertIn("accepted._guarded_keyboard", self.benchmark)
        self.assertIn("accepted._guarded_coordinate", self.benchmark)
        self.assertIn("accepted._guarded_scroll_raw", self.benchmark)
        self.assertNotIn("KEYEVENTF_UNICODE", self.benchmark)
        self.assertNotIn("SendInput", self.benchmark)

    def test_hot_runtime_is_one_agent_and_one_fixture_across_all_cycles(self):
        self.assertIn('"benchmark_kind": "warm-single-process-uia-first"', self.benchmark)
        self.assertIn('parser.add_argument("--warmup-cycles", type=int, default=2)', self.benchmark)
        self.assertIn('parser.add_argument("--measured-cycles", type=int, default=10)', self.benchmark)
        self.assertEqual(self.benchmark.count("create_server("), 1)
        self.assertIn('result["agent_process_reused"] = True', self.benchmark)
        self.assertIn('result["fixture_process_reused"]', self.benchmark)
        self.assertIn('$totalCycles = $WarmupCycles + $MeasuredCycles', self.harness)
        self.assertEqual(self.harness.count('& $pythonExe @driverArgs'), 1)

    def test_setup_time_is_separate_from_action_sequence_latency(self):
        self.assertIn("environment_setup_ms", self.harness)
        self.assertIn("benchmark_driver_ms", self.harness)
        self.assertIn("action_sequence_total_ms", self.benchmark)
        self.assertIn("time.perf_counter_ns()", self.benchmark)
        self.assertIn("_P50_MS", self.harness)
        self.assertIn("_P95_MS", self.harness)
        self.assertIn('"p50_ms"', self.benchmark)
        self.assertIn('"p95_ms"', self.benchmark)

    def test_initial_run_observes_latency_without_inventing_a_budget(self):
        self.assertIn('"latency_budget_enforced": False', self.benchmark)
        self.assertIn('latency_budget_enforced = $false', self.harness)
        self.assertNotRegex(self.benchmark, re.compile(r"p95.*[<>]=?\s*\d", re.I))

    def test_metrics_cover_every_executor_phase_and_total_cycle(self):
        for metric in (
            "start_uia_ms",
            "focus_uia_ms",
            "guarded_type_ms",
            "guarded_press_ms",
            "row_uia_find_ms",
            "guarded_click_ms",
            "guarded_scroll_ms",
            "finish_uia_ms",
            "action_sequence_total_ms",
        ):
            self.assertIn(metric, self.benchmark)

    def test_every_measured_cycle_requires_exact_accepted_operation_sequence(self):
        for operation in (
            "uia_invoke",
            "uia_focus",
            "physical_type_text",
            "physical_press",
            "physical_click",
            "physical_scroll",
        ):
            self.assertIn(f'"{operation}"', self.benchmark)
        self.assertIn("delivered != EXPECTED_OPERATIONS", self.benchmark)
        self.assertIn('sample["delivered_operations"] == EXPECTED_OPERATIONS', self.benchmark)

    def test_fixture_resets_itself_without_restarting_process(self):
        self.assertIn("function Reset-Cycle", self.fixture)
        self.assertIn("completed_cycles", self.fixture)
        self.assertIn("current_iteration", self.fixture)
        self.assertIn("benchmark_done", self.fixture)
        self.assertIn("HOT_{0:00}", self.fixture)
        self.assertIn("$state.current_iteration = [int]$state.current_iteration + 1", self.fixture)
        self.assertIn("fixture_pid = $PID", self.fixture)

    def test_persistent_environment_is_reused_and_exact_pinned(self):
        self.assertIn("hot-runtime-env", self.harness)
        self.assertIn("Test-EnvironmentPin", self.harness)
        self.assertIn("environment_reused", self.harness)
        self.assertIn("mss = '10.2.0'", self.harness)
        self.assertIn("pyautogui = '0.9.54'", self.harness)
        self.assertIn("uiautomation = '2.0.29'", self.harness)
        self.assertIn("direct_url.json", self.harness)

    def test_benchmark_has_no_generic_execution_or_production_surface_changes(self):
        combined = "\n".join((self.benchmark, self.harness, self.fixture))
        self.assertNotRegex(self.benchmark, re.compile(r"\bexec\s*\(", re.I))
        self.assertNotRegex(self.benchmark, re.compile(r"\beval\s*\(", re.I))
        self.assertNotIn("subprocess", self.benchmark)
        self.assertNotIn("os.system", self.benchmark)
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

    def test_safety_evidence_remains_acceptance_gated(self):
        self.assertIn('"unrelated_window_action_count": 0', self.benchmark)
        self.assertIn('"false_action_count": 0', self.benchmark)
        self.assertIn('$result.unrelated_window_action_count -eq 0', self.harness)
        self.assertIn('$result.false_action_count -eq 0', self.harness)
        self.assertIn("chrome_survival_pass", self.harness)
        self.assertIn("fixture_cleanup_pass", self.harness)
        self.assertIn("STAGE26_1D_HOT_RUNTIME_RESULT", self.harness)


if __name__ == "__main__":
    unittest.main()
