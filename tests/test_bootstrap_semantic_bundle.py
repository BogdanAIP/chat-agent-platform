from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap-chat-platform.ps1"
BOOTSTRAP_MANAGER = ROOT / "scripts" / "bootstrap-manager-runtime.ps1"


class BootstrapSemanticBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.manager = BOOTSTRAP_MANAGER.read_text(encoding="utf-8")
        cls.combined = f"{cls.bootstrap}\n{cls.manager}"

    def test_installed_semantic_bundle_keeps_secure_six_tool_entry_lockfile_and_vision_bridge(self) -> None:
        for marker in (
            'runtime\\semantic-projection\\package.json',
            'runtime\\semantic-projection\\package-lock.json',
            'runtime\\semantic-projection\\bin\\semantic-projection-launcher.mjs',
            'runtime\\semantic-projection\\bin\\semantic-control-plane-projection.mjs',
            'runtime\\semantic-projection\\bin\\semantic-projection.mjs',
            'runtime\\semantic-projection\\lib\\semantic-vision-click-router.mjs',
            'runtime\\semantic-projection\\lib\\visual-grounding-bridge.mjs',
            'runtime\\semantic-projection\\lib\\runtime-backed-bridge-grounder.mjs',
            'runtime\\semantic-projection\\lib\\runtime-backed-visual-grounder.mjs',
            'runtime\\control_plane\\cli.py',
            'runtime\\control_plane\\verified_workspace_artifact.py',
            'config\\local-vision-runtime.json',
            'runtime\\local_vision_adapter\\native_bbox.py',
            'runtime\\local_vision_adapter\\production_grounder.py',
            'runtime\\local_vision_adapter\\production_policy.py',
            'local-vision-runtime.ps1',
            'verify-local-vision-listener.ps1',
            'production-visual-grounder.py',
            "'CONTROL_PLANE_API_KEY'",
            "'OPENAI_API_KEY'",
            'delete process.env[key]',
            "semantic-control-plane-projection.mjs",
            "server.registerTool('$toolName'",
        ):
            self.assertIn(marker, self.combined)

    def test_installed_semantic_bundle_verifies_lock_root_pins(self) -> None:
        self.assertIn("ConvertFrom-Json -AsHashtable", self.manager)
        self.assertIn("$lock['packages']['']", self.manager)
        self.assertIn("Installed semantic lockfile dependency pin drifted", self.manager)

    def test_installed_semantic_bundle_verifies_reviewed_vision_runtime(self) -> None:
        for marker in (
            "lfm25-vl-450m-f16",
            "127.0.0.1",
            "runtime.port -ne 3068",
            "min_start_physical_gb -ne 1.35",
            "min_run_physical_gb -ne 0.5",
        ):
            self.assertIn(marker, self.manager)

    def test_manager_metadata_records_complete_six_tool_semantic_bundle(self) -> None:
        self.assertIn("schema_version = 4", self.manager)
        self.assertIn("semantic_public_tool_count = 6", self.manager)
        self.assertIn("runtime_assets", self.manager)
        for marker in (
            'runtime\\semantic-projection\\package.json',
            'runtime\\semantic-projection\\package-lock.json',
            'runtime\\semantic-projection\\bin\\semantic-projection-launcher.mjs',
            'runtime\\semantic-projection\\bin\\semantic-control-plane-projection.mjs',
            'runtime\\semantic-projection\\bin\\semantic-projection.mjs',
            'runtime\\semantic-projection\\lib\\semantic-vision-click-router.mjs',
            'runtime\\semantic-projection\\lib\\visual-grounding-bridge.mjs',
            'runtime\\semantic-projection\\lib\\runtime-backed-bridge-grounder.mjs',
            'runtime\\semantic-projection\\lib\\runtime-backed-visual-grounder.mjs',
            'runtime\\control_plane\\cli.py',
            'runtime\\control_plane\\verified_workspace_artifact.py',
            'runtime\\local_vision_adapter\\native_bbox.py',
            'runtime\\local_vision_adapter\\production_grounder.py',
            'runtime\\local_vision_adapter\\production_policy.py',
        ):
            self.assertIn(marker, self.manager)

    def test_public_bootstrap_delegates_to_verified_six_tool_bundle_installer(self) -> None:
        self.assertIn("bootstrap-manager-runtime.ps1", self.bootstrap)
        self.assertIn("Install-ChatManagerBundle", self.bootstrap)
        self.assertIn("SEMANTIC_PUBLIC_TOOL_COUNT=6", self.bootstrap)


if __name__ == "__main__":
    unittest.main()
