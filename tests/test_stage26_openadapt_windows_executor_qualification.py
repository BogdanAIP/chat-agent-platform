import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = ROOT / "scripts" / "stage26-openadapt-windows-executor-driver.py"
HARNESS_PATH = ROOT / "scripts" / "stage26-openadapt-windows-executor-qualification.ps1"
FIXTURE_PATH = ROOT / "scripts" / "stage26-windows-capture-fixture.ps1"


class Stage26OpenAdaptWindowsExecutorQualificationTests(unittest.TestCase):
    def setUp(self):
        self.driver = DRIVER_PATH.read_text(encoding="utf-8")
        self.harness = HARNESS_PATH.read_text(encoding="utf-8")
        self.fixture = FIXTURE_PATH.read_text(encoding="utf-8")

    def test_python_driver_parses(self):
        ast.parse(self.driver)

    def test_harness_is_lock_driven_and_exact_pinned(self):
        self.assertIn("stage26-openadapt-lock.json", self.harness)
        self.assertIn("openadapt-flow[windows]", self.harness)
        self.assertIn("direct_url.json", self.harness)
        self.assertIn("flow_pin_pass", self.harness)
        self.assertNotIn("d7f58d9f35c8369f16a9b378f23952d425334ad7", self.harness)

    def test_product_candidate_constructs_agent_without_cli_passthrough(self):
        self.assertIn('AgentConfig(', self.driver)
        self.assertIn('host="127.0.0.1"', self.driver)
        self.assertIn('port=0', self.driver)
        self.assertIn('token=token', self.driver)
        self.assertIn('allow_legacy_exec=False', self.driver)
        self.assertIn('create_server(config)', self.driver)
        self.assertNotIn('win_agent.server.main', self.driver)
        self.assertNotIn('--allow-legacy-exec', self.driver)

    def test_windows_backend_is_also_legacy_disabled(self):
        self.assertIn('WindowsBackend(', self.driver)
        self.assertIn('auth_token=token', self.driver)
        self.assertIn('require_tls=False', self.driver)
        self.assertGreaterEqual(self.driver.count('allow_legacy_exec=False'), 2)
        self.assertIn('windows_backend_allow_legacy_exec', self.driver)

    def test_legacy_and_command_shaped_requests_are_proven_unreachable(self):
        self.assertIn('"/execute_windows"', self.driver)
        self.assertIn('legacy_route_404_pass', self.driver)
        self.assertIn('unauthorized_input_401_pass', self.driver)
        self.assertIn('command_field_rejected_pass', self.driver)
        self.assertIn('unsupported_action_rejected_pass', self.driver)
        self.assertIn('{"action": "exec", "command": "print(\'BLOCKED\')"}', self.driver)
        self.assertIn('{"action": "exec"}', self.driver)
        self.assertNotRegex(self.driver, re.compile(r"\bexec\s*\(", re.I))
        self.assertNotRegex(self.driver, re.compile(r"\beval\s*\(", re.I))
        self.assertNotIn('subprocess', self.driver)
        self.assertNotIn('os.system', self.driver)

    def test_negative_guard_probes_are_non_mutating(self):
        self.assertIn('"expected_frame_sha256": "0" * 64', self.driver)
        self.assertIn('stale_frame_refusal_pass', self.driver)
        self.assertIn('stale_context_refusal_pass', self.driver)
        # Both deliberate stale probes carry a zero-notch scroll. If a guard
        # regressed, the test still emits no input edge before failing closed.
        self.assertGreaterEqual(self.driver.count('"horizontal_notches": 0'), 3)
        self.assertGreaterEqual(self.driver.count('"vertical_notches": 0'), 2)

    def test_real_actions_are_fixture_scoped_and_typed(self):
        self.assertIn('FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"', self.driver)
        for target in (
            "Stage 26 start button",
            "Stage 26 capture input",
            "Qualification row 01",
            "Stage 26 finish button",
        ):
            self.assertIn(target, self.driver)
        self.assertIn('backend.locate_structural(locator)', self.driver)
        self.assertIn('backend.act_structural', self.driver)
        self.assertIn('backend.arm_guarded_keyboard', self.driver)
        self.assertIn('backend.type_text_guarded', self.driver)
        self.assertIn('backend.press_guarded', self.driver)
        self.assertIn('backend.arm_guarded_coordinate', self.driver)
        self.assertIn('"/input/guarded"', self.driver)

    def test_uia_uniqueness_fingerprint_and_freshness_are_acceptance_gates(self):
        for gate in (
            "uia_unique_target_pass",
            "fingerprint_bound_action_pass",
            "stale_frame_refusal_pass",
            "stale_context_refusal_pass",
            "guarded_keyboard_pass",
            "guarded_coordinate_pass",
            "guarded_scroll_pass",
        ):
            self.assertIn(f'"{gate}"', self.driver)
        self.assertIn('handle.candidate_count != 1', self.driver)
        self.assertIn('handle.target_fingerprint', self.driver)
        self.assertIn('expected_frame_sha256', self.driver)

    def test_fixture_is_disabled_until_security_preflight_passes(self):
        preflight = self.driver.index('raise RuntimeError("pre-actuation Windows agent security gate failed")')
        ready = self.driver.index('ready_path.write_text("READY\\n"')
        self.assertLess(preflight, ready)
        self.assertIn('$startButton.Enabled = $false', self.fixture)
        self.assertIn('$inputBox.Enabled = $false', self.fixture)
        self.assertIn('$listBox.Enabled = $false', self.fixture)

    def test_target_harness_uses_only_exact_owned_fixture_for_cleanup(self):
        self.assertIn('ProcessStartInfo', self.harness)
        self.assertIn('$fixtureProcess.Kill($true)', self.harness)
        self.assertNotRegex(self.harness, re.compile(r"Stop-Process", re.I))
        self.assertNotRegex(self.harness, re.compile(r"taskkill", re.I))
        self.assertNotIn('Get-Process pwsh', self.harness)
        self.assertIn('Get-Process chrome', self.harness)

    def test_no_screenshot_or_token_is_persisted_by_driver(self):
        self.assertNotIn('write_bytes', self.driver)
        self.assertNotIn('image_base64', self.driver)
        self.assertNotIn('token_urlsafe(32)', self.harness)
        self.assertIn('token = secrets.token_urlsafe(32)', self.driver)
        self.assertNotIn('"token": token', self.driver)

    def test_production_chat_surface_is_not_touched(self):
        combined = "\n".join((self.driver, self.harness))
        for forbidden in (
            "semantic-projection-runtime.ps1 -Action",
            "start-chat-profile.ps1",
            "stop-chat-profile.ps1",
            "start-semantic-profile.ps1",
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
        ):
            self.assertNotIn(forbidden, combined)

    def test_final_acceptance_requires_zero_false_or_unrelated_actions(self):
        self.assertIn('result["unrelated_window_action_count"] == 0', self.driver)
        self.assertIn('result["false_action_count"] == 0', self.driver)
        self.assertIn('STAGE26_1C_EXECUTOR_RESULT', self.harness)
        self.assertIn('fixture_cleanup_pass', self.harness)
        self.assertIn('chrome_survival_pass', self.harness)


if __name__ == "__main__":
    unittest.main()
