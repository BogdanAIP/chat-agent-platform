from __future__ import annotations

import unittest
from pathlib import Path


class DesktopObservationQualificationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        cls.driver = (repo / "scripts" / "stage26-desktop-observation-qualification.py").read_text(
            encoding="utf-8"
        )
        cls.harness = (repo / "scripts" / "stage26-desktop-observation-qualification.ps1").read_text(
            encoding="utf-8"
        )
        cls.ci = (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    def test_driver_uses_production_observation_and_resolver(self):
        self.assertIn("from runtime.windows.observation import", self.driver)
        self.assertIn("observe_bound_window", self.driver)
        self.assertIn("WindowScopedUiaResolver", self.driver)
        self.assertNotIn("runtime.windows.actuation", self.driver)
        self.assertNotIn("WindowsBackend(", self.driver)
        self.assertNotIn("create_server(", self.driver)

    def test_driver_is_read_only_and_hard_gates_zero_actions(self):
        self.assertIn('"action_count": 0', self.driver)
        self.assertIn('"false_action_count": 0', self.driver)
        self.assertIn('"unrelated_window_action_count": 0', self.driver)
        self.assertIn('result["action_count"] == 0', self.driver)
        self.assertIn('result["false_action_count"] == 0', self.driver)
        self.assertIn('result["unrelated_window_action_count"] == 0', self.driver)
        for token in ("act_structural", "act_guarded", "bounded_input", "send_unicode_text"):
            self.assertNotIn(token, self.driver)

    def test_exact_window_screenshot_is_bounded_by_observed_rect(self):
        self.assertIn('"left": bounds.left', self.driver)
        self.assertIn('"top": bounds.top', self.driver)
        self.assertIn('"width": bounds.width', self.driver)
        self.assertIn('"height": bounds.height', self.driver)
        self.assertIn("mss.tools.to_png", self.driver)
        self.assertIn('screenshot_source="mss_exact_bound_window"', self.driver)

    def test_harness_uses_production_observer_and_no_executor_asset(self):
        self.assertIn("runtime\\windows\\observation.py", self.harness)
        self.assertIn("runtime\\windows\\window_scoped_uia.py", self.harness)
        self.assertNotIn("runtime\\windows\\actuation.py", self.harness)
        self.assertIn("Read-only fixture observation", self.harness)
        self.assertIn("STAGE26_2B_DESKTOP_OBSERVATION_RESULT", self.harness)

    def test_ci_parses_current_stage26_harnesses(self):
        for script in (
            "scripts/stage26-windows-hot-runtime-fixture.ps1",
            "scripts/stage26-windows-hot-runtime-benchmark.ps1",
            "scripts/stage26-window-scoped-uia-benchmark.ps1",
            "scripts/stage26-desktop-observation-qualification.ps1",
        ):
            self.assertIn(script, self.ci)


if __name__ == "__main__":
    unittest.main()
