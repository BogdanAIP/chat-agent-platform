from __future__ import annotations

import ast
from pathlib import Path
import unittest

from runtime.windows.verifier import VerificationStatus, verify_expected_fields


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "stage26-vscode-real-app-e2e.py"
HARNESS = ROOT / "scripts" / "stage26-vscode-real-app-e2e.ps1"


class Stage262EVSCodeRealAppContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.driver = DRIVER.read_text(encoding="utf-8")
        cls.harness = HARNESS.read_text(encoding="utf-8")
        ast.parse(cls.driver, filename=str(DRIVER))

    def test_driver_uses_isolated_disposable_vscode_profile(self) -> None:
        for required in (
            '"--wait"',
            '"--new-window"',
            '"--disable-extensions"',
            '"--user-data-dir"',
            '"--extensions-dir"',
            '"--goto"',
            '"security.workspace.trust.enabled": False',
            '"files.autoSave": "afterDelay"',
            '"editor.accessibilitySupport": "on"',
            '"chat.disableAIFeatures": True',
        ):
            self.assertIn(required, self.driver)
        self.assertIn('workspace_root = app_root / "workspace"', self.driver)
        self.assertIn('user_data_root = app_root / "user-data"', self.driver)
        self.assertIn('extensions_root = app_root / "extensions"', self.driver)
        self.assertIn("shell=False", self.driver)

    def test_driver_enforces_temp_containment_before_recursive_delete(self) -> None:
        for required in (
            "tempfile.gettempdir()",
            "app_root.is_relative_to(temp_root)",
            "QUALIFICATION_PREFIX",
            "_require_disposable_root(app_root)",
            "_remove_disposable_root(app_root)",
        ):
            self.assertIn(required, self.driver)
        self.assertEqual(self.driver.count("shutil.rmtree(app_root)"), 1)
        helper_start = self.driver.index("def _remove_disposable_root")
        helper_end = self.driver.index("\ndef _wait_until", helper_start)
        helper = self.driver[helper_start:helper_end]
        self.assertIn("_require_disposable_root(app_root)", helper)
        self.assertIn("shutil.rmtree(app_root)", helper)
        self.assertIn('result["temp_containment_pass"]', self.driver)

    def test_driver_reuses_accepted_windows_guards_and_verifier(self) -> None:
        for required in (
            "observe_bound_window",
            "require_foreground_hit_target",
            "verify_expected_fields",
            "backend.arm_guarded_keyboard",
            "backend.guarded_keyboard_frame",
            "backend.type_text_guarded",
            "allow_legacy_exec=False",
        ):
            self.assertIn(required, self.driver)
        self.assertEqual(self.driver.count("backend.type_text_guarded("), 1)

    def test_editor_target_is_exact_hidden_monaco_keyboard_identity(self) -> None:
        helper_start = self.driver.index("def _focused_editor_control")
        helper_end = self.driver.index("\ndef _window_guard_point", helper_start)
        helper = self.driver[helper_start:helper_end]
        for required in (
            "state.focused_control",
            "control.observation_fingerprint == state.focused_control",
            "control.enabled is not True",
            "control.focused is not True",
            'control.role.casefold() != "textbox"',
            "control.name.casefold() != unique_filename.casefold()",
        ):
            self.assertIn(required, helper)
        for forbidden in (
            "control.visible is not True",
            "control.bounds",
            "FOCUSED_EDITOR_ROLES",
            '"text editor" in name',
            '"editor content" in name',
        ):
            self.assertNotIn(forbidden, helper)

    def test_window_point_is_only_derived_from_bound_window_geometry(self) -> None:
        helper_start = self.driver.index("def _window_guard_point")
        helper_end = self.driver.index("\ndef _verification_decision", helper_start)
        helper = self.driver[helper_start:helper_end]
        self.assertIn("bounds = state.window_bounds", helper)
        self.assertIn("bounds.width <= 0 or bounds.height <= 0", helper)
        self.assertIn("bounds.left + bounds.right", helper)
        self.assertIn("bounds.top + bounds.bottom", helper)
        self.assertNotIn("ControlObservation", helper)
        self.assertNotIn("ControlFromPoint", helper)

    def test_fresh_same_focused_editor_is_required_immediately_before_typing(self) -> None:
        self.assertIn("action_state = observe_bound_window(resolver, window_title)", self.driver)
        self.assertIn("action_focused = _focused_editor_control(action_state, unique_filename)", self.driver)
        self.assertIn("_same_window_identity(before_state, action_state)", self.driver)
        self.assertIn(
            "action_focused.observation_fingerprint == focused.observation_fingerprint",
            self.driver,
        )
        self.assertIn('result["fresh_pre_action_state_pass"]', self.driver)
        fresh_index = self.driver.index("action_state = observe_bound_window")
        type_index = self.driver.index("backend.type_text_guarded(")
        self.assertLess(fresh_index, type_index)

    def test_exact_hidden_focus_is_armed_before_guarded_keyboard_request(self) -> None:
        arm = self.driver.index("resolver.arm_focused_keyboard_target(")
        backend_arm = self.driver.index("backend.arm_guarded_keyboard(")
        frame = self.driver.index("backend.guarded_keyboard_frame()")
        type_index = self.driver.index("backend.type_text_guarded(")
        cancel = self.driver.index("resolver.cancel_focused_keyboard_target()", arm)
        self.assertLess(arm, backend_arm)
        self.assertLess(backend_arm, frame)
        self.assertLess(frame, type_index)
        self.assertGreater(cancel, type_index)
        for required in (
            "window_title=window_title",
            "window_handle=action_state.window_handle",
            "process_generation=action_state.process_generation",
            "focused_fingerprint=action_focused.observation_fingerprint",
            "role=action_focused.role",
            "name=action_focused.name",
            'result["keyboard_focus_guard_armed_pass"] = True',
        ):
            self.assertIn(required, self.driver)

    def test_keyboard_focus_guard_must_pass_exactly_once(self) -> None:
        for required in (
            "resolver.stats.keyboard_focus_guard_arms == 1",
            "resolver.stats.keyboard_focus_guard_calls == 1",
            "resolver.stats.keyboard_focus_guard_passes == 1",
            "resolver.stats.keyboard_focus_guard_failures == 0",
            'result["keyboard_focus_guard_pass"]',
            'result["keyboard_focus_guard_armed_pass"]',
            'KEYBOARD_FOCUS_GUARD_MODE = "window_scoped_focused_observation_fingerprint"',
        ):
            self.assertIn(required, self.driver)

    def test_real_app_gate_has_no_hidden_extra_action_channel(self) -> None:
        forbidden = (
            "SetForegroundWindow",
            "pyautogui",
            "pyperclip",
            "clipboard",
            "shell=True",
            "os.system",
            "subprocess.run",
            "taskkill",
            "act_guarded_coordinate",
            "press_guarded",
            "act_structural",
            "execute_windows",
            "allow_legacy_exec=True",
        )
        for item in forbidden:
            with self.subTest(item=item):
                self.assertNotIn(item, self.driver)

    def test_mismatch_is_mapped_to_abstain_before_mutation(self) -> None:
        baseline = {
            "exists": True,
            "size": 0,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        }
        mismatch = verify_expected_fields(
            before={},
            after=baseline,
            expectation={"exists": True, "size": 0, "sha256": "0" * 64},
        )
        self.assertIs(mismatch.status, VerificationStatus.FAIL)
        self.assertIn(
            'return "continue" if status is VerificationStatus.PASS else "abstain"',
            self.driver,
        )
        self.assertIn('result["mismatch_probe_zero_action_pass"]', self.driver)
        self.assertIn('result["keyboard_action_count"] == 0', self.driver)

    def test_completion_is_independent_file_evidence_not_delivery_receipt(self) -> None:
        self.assertIn("completion = verify_expected_fields(", self.driver)
        self.assertIn('result["completion_verification_pass"] = completion.passed', self.driver)
        self.assertIn('result["completion_artifact_evidence"] = after_artifact', self.driver)
        self.assertIn("receipt.outcome_verified is False", self.driver)
        self.assertIn("workspace_snapshot = _workspace_snapshot(workspace_root)", self.driver)
        self.assertIn('result["workspace_expected_only_pass"]', self.driver)

    def test_single_measured_mutation_is_the_only_delivery_claim(self) -> None:
        self.assertIn('"keyboard_action_count": 0', self.driver)
        self.assertIn('result["keyboard_action_count"] += 1', self.driver)
        self.assertIn('result["keyboard_action_count"] == 1', self.driver)
        self.assertNotIn('"false_action_count": 0', self.driver)
        self.assertNotIn('"unrelated_window_action_count": 0', self.driver)

    def test_cleanup_requires_natural_zero_cli_exit_for_acceptance(self) -> None:
        self.assertIn("PostMessageW", self.driver)
        self.assertIn("WM_CLOSE", self.driver)
        self.assertIn("_remove_disposable_root(app_root)", self.driver)
        self.assertIn('result["cli_process_returncode"] = returncode', self.driver)
        self.assertIn('result["cli_process_exit_pass"] = returncode == 0', self.driver)
        self.assertIn('result["forced_cli_cleanup"] = True', self.driver)
        self.assertIn('result["cli_process_exit_pass"] = False', self.driver)
        self.assertIn('and result["cli_process_returncode"] == 0', self.driver)
        self.assertIn('and not result["forced_cli_cleanup"]', self.driver)
        self.assertIn('result["rollback_pass"]', self.driver)
        self.assertNotIn("TerminateProcess", self.driver)

    def test_failure_cleanup_is_randomized_and_freshly_revalidated(self) -> None:
        helper_start = self.driver.index("def _validated_cleanup_matches")
        helper_end = self.driver.index("\ndef _wait_unique_vscode_window", helper_start)
        helper = self.driver[helper_start:helper_end]
        self.assertIn("matches = _matching_vscode_windows(unique_filename)", helper)
        self.assertIn("_query_process_identity(pid)", helper)
        self.assertIn("executable_name.casefold() != EXPECTED_EXECUTABLE", helper)
        self.assertIn('result["failure_window_cleanup_count"] = len(cleanup_matches)', self.driver)
        self.assertIn('len(cleanup_matches) == 1 and len(validated_matches) == 1', self.driver)
        self.assertIn('_post_close(int(validated_matches[0]["hwnd"]))', self.driver)
        self.assertIn(
            '"VS Code cleanup identity was not uniquely revalidated; refusing WM_CLOSE"',
            self.driver,
        )
        self.assertNotIn("_post_close(bound_hwnd)", self.driver)

    def test_harness_discovers_code_without_touching_user_workspace(self) -> None:
        self.assertIn("Resolve-VSCodeExecutable", self.harness)
        self.assertIn("Microsoft VS Code\\Code.exe", self.harness)
        self.assertIn("$env:TEMP", self.harness)
        self.assertIn("chat-agent-stage26e-vscode-", self.harness)
        self.assertNotIn("Documents\\", self.harness)
        self.assertNotIn("Desktop\\", self.harness)
        self.assertNotIn("taskkill", self.harness.casefold())

    def test_harness_recursive_cleanup_is_temp_prefix_guarded(self) -> None:
        self.assertIn("function Test-DisposableRoot", self.harness)
        self.assertIn("function Remove-DisposableRoot", self.harness)
        self.assertIn("[IO.Path]::GetTempPath()", self.harness)
        self.assertIn("chat-agent-stage26e-vscode-*", self.harness)
        self.assertEqual(self.harness.count("Remove-Item -LiteralPath $Path -Recurse -Force"), 1)
        self.assertIn("Remove-DisposableRoot -Path $appRoot", self.harness)
        self.assertIn("$result.temp_containment_pass", self.harness)

    def test_harness_requires_verification_fresh_focus_and_rollback_for_acceptance(self) -> None:
        for required in (
            "$result.temp_containment_pass",
            "$result.fresh_pre_action_state_pass",
            "$result.completion_verification_pass",
            "$result.current_state_verification_pass",
            "$result.workspace_expected_only_pass",
            "$result.cleanup_revalidation_pass",
            "$result.application_cleanup_pass",
            "$result.cli_process_exit_pass",
            "$null -ne $result.cli_process_returncode",
            "[int]$result.cli_process_returncode -eq 0",
            "-not $result.forced_cli_cleanup",
            "$result.app_root_cleanup_pass",
            "$result.rollback_pass",
        ):
            self.assertIn(required, self.harness)


if __name__ == "__main__":
    unittest.main()
