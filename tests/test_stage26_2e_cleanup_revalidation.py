from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts" / "stage26-vscode-real-app-e2e.py"
HARNESS = ROOT / "scripts" / "stage26-vscode-real-app-e2e.ps1"


class Stage262ECleanupRevalidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.driver = DRIVER.read_text(encoding="utf-8")
        cls.harness = HARNESS.read_text(encoding="utf-8")

    def test_cleanup_revalidates_random_title_hwnd_pid_executable_and_generation(self) -> None:
        helper_start = self.driver.index("def _validated_cleanup_matches")
        helper_end = self.driver.index("\ndef _wait_unique_vscode_window", helper_start)
        helper = self.driver[helper_start:helper_end]
        for required in (
            "_matching_vscode_windows(unique_filename)",
            "hwnd != expected_hwnd",
            "pid != expected_pid",
            "_query_process_identity(pid)",
            "executable_name.casefold() != EXPECTED_EXECUTABLE",
            "process_generation != expected_process_generation",
        ):
            self.assertIn(required, helper)

    def test_cleanup_never_posts_wm_close_to_cached_hwnd_directly(self) -> None:
        self.assertNotIn("_post_close(bound_hwnd)", self.driver)
        self.assertIn('_post_close(int(validated_matches[0]["hwnd"]))', self.driver)
        post_index = self.driver.index('_post_close(int(validated_matches[0]["hwnd"]))')
        validate_index = self.driver.rindex("_validated_cleanup_matches(", 0, post_index)
        self.assertLess(validate_index, post_index)

    def test_ambiguous_or_changed_cleanup_identity_fails_closed(self) -> None:
        for required in (
            'len(cleanup_matches) == 1 and len(validated_matches) == 1',
            'result["cleanup_revalidation_pass"] = False',
            '"VS Code cleanup identity was not uniquely revalidated; refusing WM_CLOSE"',
            'result["cleanup_revalidation_pass"]',
        ):
            self.assertIn(required, self.driver)

        rollback_start = self.driver.index('result["rollback_pass"] = bool(')
        rollback_end = self.driver.index("\n            )", rollback_start)
        rollback = self.driver[rollback_start:rollback_end]
        self.assertIn('result["cleanup_revalidation_pass"]', rollback)
        self.assertIn('result["application_cleanup_pass"]', rollback)

    def test_harness_requires_cleanup_revalidation_for_acceptance(self) -> None:
        for required in (
            "schema_version = 5",
            "cleanup_revalidation_pass = $false",
            "'CLEANUP_REVALIDATION_PASS'",
            "$result.cleanup_revalidation_pass -and",
        ):
            self.assertIn(required, self.harness)


if __name__ == "__main__":
    unittest.main()
