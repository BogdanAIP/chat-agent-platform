from __future__ import annotations

from pathlib import Path
import unittest

from runtime.windows.native_point_guard import native_point_context_authorized


class NativePointGuardPolicyTests(unittest.TestCase):
    def test_exact_foreground_root_and_process_is_authorized(self):
        self.assertTrue(
            native_point_context_authorized(
                expected_hwnd=100,
                expected_pid=200,
                foreground_hwnd=100,
                foreground_pid=200,
                hit_root_hwnd=100,
                hit_pid=200,
            )
        )

    def test_foreground_change_is_refused(self):
        self.assertFalse(
            native_point_context_authorized(
                expected_hwnd=100,
                expected_pid=200,
                foreground_hwnd=300,
                foreground_pid=400,
                hit_root_hwnd=100,
                hit_pid=200,
            )
        )

    def test_foreign_overlay_at_click_point_is_refused(self):
        self.assertFalse(
            native_point_context_authorized(
                expected_hwnd=100,
                expected_pid=200,
                foreground_hwnd=100,
                foreground_pid=200,
                hit_root_hwnd=300,
                hit_pid=400,
            )
        )

    def test_same_hwnd_with_wrong_process_is_refused(self):
        self.assertFalse(
            native_point_context_authorized(
                expected_hwnd=100,
                expected_pid=200,
                foreground_hwnd=100,
                foreground_pid=999,
                hit_root_hwnd=100,
                hit_pid=200,
            )
        )

    def test_invalid_zero_handles_are_refused(self):
        self.assertFalse(
            native_point_context_authorized(
                expected_hwnd=100,
                expected_pid=200,
                foreground_hwnd=0,
                foreground_pid=200,
                hit_root_hwnd=100,
                hit_pid=200,
            )
        )


class NativePointGuardSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        cls.guard_source = (repo / "runtime" / "windows" / "native_point_guard.py").read_text(encoding="utf-8")
        cls.routing_source = (repo / "runtime" / "windows" / "routing.py").read_text(encoding="utf-8")

    def test_windows_guard_uses_foreground_and_point_hit_test(self):
        self.assertIn("GetForegroundWindow", self.guard_source)
        self.assertIn("WindowFromPoint", self.guard_source)
        self.assertIn("GetAncestor", self.guard_source)
        self.assertIn("GetWindowThreadProcessId", self.guard_source)

    def test_coordinate_delivery_runs_native_guard_twice(self):
        self.assertGreaterEqual(self.routing_source.count("require_foreground_hit_target(state, x, y)"), 2)
        self.assertIn("native-point-guard-refused", self.routing_source)

    def test_guard_has_no_mutation_channel(self):
        for token in (
            "SendInput",
            "SetForegroundWindow",
            "SetWindowPos",
            "PostMessage",
            "SendMessage",
            "subprocess.",
            "os.system(",
        ):
            self.assertNotIn(token, self.guard_source)


if __name__ == "__main__":
    unittest.main()
