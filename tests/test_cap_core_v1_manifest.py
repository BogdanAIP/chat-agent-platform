from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "runtime" / "control_plane" / "core_v1_manifest.json"


class CapCoreV1ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_exact_bounded_freeze_candidate(self) -> None:
        self.assertEqual(1, self.manifest["schema_version"])
        self.assertEqual("cap-core-v1", self.manifest["core_id"])
        self.assertEqual("freeze-candidate", self.manifest["status"])
        self.assertEqual("runtime.control_plane", self.manifest["package"])
        modules = self.manifest["kernel_modules"]
        self.assertEqual(len(modules), len(set(modules)))
        self.assertEqual(
            {
                "runtime/control_plane/verification.py",
                "runtime/control_plane/working_state.py",
                "runtime/control_plane/local_state.py",
            },
            set(modules),
        )
        for relative in modules:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_kernel_internal_imports_are_explicitly_allowlisted(self) -> None:
        allowed = self.manifest["allowed_internal_dependencies"]
        forbidden_prefixes = tuple(self.manifest["forbidden_dependency_prefixes"])

        self.assertEqual(set(self.manifest["kernel_modules"]), set(allowed))

        for relative in self.manifest["kernel_modules"]:
            source = (ROOT / relative).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
            package = ".".join(Path(relative).with_suffix("").parts[:-1])
            observed_internal: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("runtime."):
                            observed_internal.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        base_parts = package.split(".")
                        if node.level > len(base_parts):
                            self.fail(f"{relative} has invalid relative import level")
                        prefix = ".".join(base_parts[: len(base_parts) - node.level + 1])
                        module = f"{prefix}.{node.module}" if node.module else prefix
                    else:
                        module = node.module or ""
                    if module.startswith("runtime."):
                        observed_internal.add(module)

            for dependency in observed_internal:
                with self.subTest(relative=relative, dependency=dependency):
                    self.assertFalse(
                        dependency.startswith(forbidden_prefixes),
                        f"Core module {relative} depends on forbidden implementation {dependency}",
                    )

            self.assertEqual(
                set(allowed[relative]),
                observed_internal,
                f"Core dependency drift in {relative}; update architecture research before widening it",
            )

    def test_core_exports_match_manifest_without_loading_implementations(self) -> None:
        script = """
import json
import sys
import runtime.control_plane as core

blocked_prefixes = (
    "runtime.agent_sessions",
    "runtime.local_vision_adapter",
    "runtime.semantic_projection",
    "runtime.control_plane.browser_",
    "runtime.control_plane.file_artifact_",
    "runtime.control_plane.independent_review_",
    "runtime.control_plane.verified_workspace_artifact",
    "runtime.control_plane.windows_",
)
print(json.dumps({
    "exports": sorted(core.__all__),
    "blocked_loaded": sorted(
        name for name in sys.modules
        if name.startswith(blocked_prefixes)
    ),
}))
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(sorted(self.manifest["core_exports"]), result["exports"])
        self.assertEqual([], result["blocked_loaded"])

    def test_non_core_examples_stay_outside_kernel_manifest(self) -> None:
        kernel = set(self.manifest["kernel_modules"])
        for relative in self.manifest["non_core_examples"]:
            with self.subTest(relative=relative):
                self.assertNotIn(relative, kernel)
                self.assertTrue((ROOT / relative).is_file())


if __name__ == "__main__":
    unittest.main()
