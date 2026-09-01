from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap-manager-runtime.ps1"


class ManagerBundleReviewModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = BOOTSTRAP.read_text(encoding="utf-8")

    def test_installed_runtime_assertion_requires_reviewer_modules(self) -> None:
        assertion = self.source.split("function Assert-ChatInstalledSixToolSemanticRuntime", 1)[1].split(
            "function Install-ChatManagerBundle", 1
        )[0]
        for name in ("independent_review_procedures.py", "independent_review_state.py"):
            with self.subTest(name=name):
                self.assertIn(f"        '{name}',", assertion)

    def test_production_bundle_copies_reviewer_modules_and_records_them_as_runtime_assets(self) -> None:
        installer = self.source.split("function Install-ChatManagerBundle", 1)[1]
        for name in ("independent_review_procedures.py", "independent_review_state.py"):
            relative = f"runtime\\control_plane\\{name}"
            with self.subTest(name=name):
                self.assertIn(f"@('{relative}', '{relative}')", installer)
        self.assertIn(
            "runtime_assets = @($runtimeFiles | ForEach-Object { ([string]$_[0]).Replace('\\', '/') })",
            installer,
        )


if __name__ == "__main__":
    unittest.main()
