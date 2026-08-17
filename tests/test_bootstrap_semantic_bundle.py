from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"


class BootstrapSemanticBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    def test_installed_semantic_bundle_keeps_secure_entry_lockfile_and_vision_bridge(self) -> None:
        for marker in (
            'runtime\\semantic-projection\\package.json',
            'runtime\\semantic-projection\\package-lock.json',
            'runtime\\semantic-projection\\bin\\semantic-projection-launcher.mjs',
            'runtime\\semantic-projection\\bin\\semantic-projection.mjs',
            'runtime\\semantic-projection\\lib\\semantic-vision-click-router.mjs',
            'runtime\\semantic-projection\\lib\\visual-grounding-bridge.mjs',
            'runtime\\semantic-projection\\lib\\runtime-backed-bridge-grounder.mjs',
            'runtime\\semantic-projection\\lib\\runtime-backed-visual-grounder.mjs',
            'config\\local-vision-runtime.json',
            'runtime\\local_vision_adapter\\native_bbox.py',
            'runtime\\local_vision_adapter\\production_grounder.py',
            'runtime\\local_vision_adapter\\production_policy.py',
            'local-vision-runtime.ps1',
            'verify-local-vision-listener.ps1',
            'production-visual-grounder.py',
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

    def test_installed_semantic_bundle_verifies_reviewed_vision_runtime(self) -> None:
        for marker in (
            "lfm25-vl-450m-f16",
            "127.0.0.1",
            "runtime.port -ne 3068",
            "min_start_physical_gb -ne 1.35",
            "min_run_physical_gb -ne 0.5",
        ):
            self.assertIn(marker, self.bootstrap)

    def test_manager_metadata_records_complete_semantic_bundle(self) -> None:
        runtime_assets = self.bootstrap.split('runtime_assets = @(', 1)[1].split(')', 1)[0]
        for marker in (
            'runtime/semantic-projection/package.json',
            'runtime/semantic-projection/package-lock.json',
            'runtime/semantic-projection/bin/semantic-projection-launcher.mjs',
            'runtime/semantic-projection/bin/semantic-projection.mjs',
            'runtime/semantic-projection/lib/semantic-vision-click-router.mjs',
            'runtime/semantic-projection/lib/visual-grounding-bridge.mjs',
            'runtime/semantic-projection/lib/runtime-backed-bridge-grounder.mjs',
            'runtime/semantic-projection/lib/runtime-backed-visual-grounder.mjs',
            'runtime/local_vision_adapter/native_bbox.py',
            'runtime/local_vision_adapter/production_grounder.py',
            'runtime/local_vision_adapter/production_policy.py',
        ):
            self.assertIn(marker, runtime_assets)


if __name__ == "__main__":
    unittest.main()
