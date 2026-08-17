from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"


class BootstrapSemanticBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    def test_installed_semantic_bundle_keeps_secure_entry_and_lockfile(self) -> None:
        for marker in (
            'runtime\\semantic-projection\\package.json',
            'runtime\\semantic-projection\\package-lock.json',
            'runtime\\semantic-projection\\bin\\semantic-projection-launcher.mjs',
            'runtime\\semantic-projection\\bin\\semantic-projection.mjs',
            'bin/semantic-projection-launcher.mjs',
            'lockfileVersion',
            "'CONTROL_PLANE_API_KEY'",
            "'OPENAI_API_KEY'",
            'delete process.env[key]',
            "await import('./semantic-projection.mjs')",
        ):
            self.assertIn(marker, self.bootstrap)

    def test_installed_semantic_bundle_verifies_lock_root_pins(self) -> None:
        self.assertIn("ConvertFrom-Json -AsHashtable", self.bootstrap)
        self.assertIn("$lock['packages']['']", self.bootstrap)
        self.assertIn("Installed semantic lockfile dependency pin drifted", self.bootstrap)

    def test_manager_metadata_records_complete_semantic_bundle(self) -> None:
        runtime_assets = self.bootstrap.split('runtime_assets = @(', 1)[1].split(')', 1)[0]
        for marker in (
            'runtime/semantic-projection/package.json',
            'runtime/semantic-projection/package-lock.json',
            'runtime/semantic-projection/bin/semantic-projection-launcher.mjs',
            'runtime/semantic-projection/bin/semantic-projection.mjs',
        ):
            self.assertIn(marker, runtime_assets)


if __name__ == "__main__":
    unittest.main()
