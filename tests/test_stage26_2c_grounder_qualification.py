from __future__ import annotations

from pathlib import Path
import unittest


class DesktopGrounderQualificationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        cls.driver = (repo / "scripts" / "stage26-desktop-grounder-qualification.py").read_text(
            encoding="utf-8"
        )
        cls.harness = (repo / "scripts" / "stage26-desktop-grounder-qualification.ps1").read_text(
            encoding="utf-8"
        )
        cls.ci = (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    def test_driver_uses_production_observer_grounder_and_exact_window_capture(self):
        self.assertIn("observe_bound_window", self.driver)
        self.assertIn("locate_desktop_target", self.driver)
        self.assertIn("NativeBBoxLoopbackClient", self.driver)
        self.assertIn("with mss.MSS() as capture:", self.driver)
        self.assertIn('screenshot_source="mss_exact_bound_window"', self.driver)
        self.assertIn('"grounder_source_sha256"', self.driver)
        self.assertIn('"observer_source_sha256"', self.driver)

    def test_driver_has_no_action_channel(self):
        for token in (
            "runtime.windows.actuation",
            "WindowsBackend(",
            "act_structural",
            "act_guarded",
            "bounded_input",
            "send_unicode_text",
        ):
            self.assertNotIn(token, self.driver)
        self.assertNotIn('"action_count"', self.driver)
        self.assertNotIn('"false_action_count"', self.driver)
        self.assertNotIn('"unrelated_window_action_count"', self.driver)

    def test_driver_requires_positive_target_absent_and_stale_frame_gates(self):
        self.assertIn('"target_point_inside_uia_pass"', self.driver)
        self.assertIn('"absent_target_abstain_pass"', self.driver)
        self.assertIn('"stale_frame_rejection_pass"', self.driver)
        self.assertIn("screenshot-digest-mismatch", self.driver)

    def test_harness_reuses_reviewed_local_vision_lifecycle_and_restores_it(self):
        self.assertIn("local-vision-runtime.ps1", self.harness)
        self.assertIn("lfm25-vl-450m-f16", self.harness)
        self.assertIn("VISION_STARTED_BY_HARNESS", self.harness)
        self.assertIn("VISION_RESTORED_PASS", self.harness)
        self.assertIn("Stage 26.2C", self.harness)
        self.assertNotIn("production-visual-grounder.py", self.harness)

    def test_ci_parses_stage26_2c_harness(self):
        self.assertIn("scripts/stage26-desktop-grounder-qualification.ps1", self.ci)


if __name__ == "__main__":
    unittest.main()
