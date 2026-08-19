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

    def test_driver_has_no_action_channel_and_no_fake_action_counters(self):
        for token in (
            "act_structural",
            "act_guarded",
            "bounded_input",
            "send_unicode_text",
            "runtime.windows.actuation",
            "WindowsBackend(",
        ):
            self.assertNotIn(token, self.driver)
        self.assertNotIn('"action_count"', self.driver)
        self.assertNotIn('"false_action_count"', self.driver)
        self.assertNotIn('"unrelated_window_action_count"', self.driver)
        self.assertNotIn('"observation_only_pass"', self.driver)
        self.assertIn('"observer_source_sha256"', self.driver)
        self.assertIn('"driver_source_sha256"', self.driver)

    def test_exact_window_screenshot_is_bounded_by_observed_rect(self):
        self.assertIn('"left": bounds.left', self.driver)
        self.assertIn('"top": bounds.top', self.driver)
        self.assertIn('"width": bounds.width', self.driver)
        self.assertIn('"height": bounds.height', self.driver)
        self.assertIn("mss.tools.to_png", self.driver)
        self.assertIn("with mss.MSS() as capture:", self.driver)
        self.assertNotIn("with mss.mss() as capture:", self.driver)
        self.assertIn('screenshot_source="mss_exact_bound_window"', self.driver)

    def test_harness_uses_production_observer_and_no_executor_asset(self):
        self.assertIn("runtime\\windows\\observation.py", self.harness)
        self.assertIn("runtime\\windows\\window_scoped_uia.py", self.harness)
        self.assertNotIn("runtime\\windows\\actuation.py", self.harness)
        self.assertIn("no executor or actuation module is invoked", self.harness)
        self.assertIn("Read-only source-boundary enforcement is covered by CI/review", self.harness)
        self.assertIn("OBSERVER_SOURCE_SHA256", self.harness)
        self.assertIn("DRIVER_SOURCE_SHA256", self.harness)
        self.assertNotIn("ACTION_COUNT", self.harness)
        self.assertNotIn("FALSE_ACTION_COUNT", self.harness)
        self.assertNotIn("UNRELATED_WINDOW_ACTION_COUNT", self.harness)
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
