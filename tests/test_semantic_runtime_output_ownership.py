from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-projection-launcher.mjs"
PACKAGE = ROOT / "runtime" / "semantic-projection" / "package.json"


class SemanticRuntimeOutputOwnershipTests(unittest.TestCase):
    def test_canonical_semantic_bin_uses_hardened_launcher(self) -> None:
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        self.assertEqual(
            package["bin"]["chat-semantic-projection"],
            "bin/semantic-projection-launcher.mjs",
        )

        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("env.PLAYWRIGHT_MCP_OUTPUT_DIR = paths.playwrightOutputDir;", source)
        self.assertIn("fs.mkdirSync(paths.playwrightOutputDir, { recursive: true });", source)
        self.assertIn("cwd: runtime.runtimeDir", source)
        self.assertIn("'logs', 'semantic-runtime'", source)

    def test_launcher_ignores_caller_cwd_and_parent_playwright_output_override(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is unavailable")

        with tempfile.TemporaryDirectory(prefix="cap-semantic-output-") as temp:
            root = Path(temp)
            caller = root / "source-checkout"
            local_app_data = root / "local-app-data"
            node_temp = root / "node-temp"
            caller.mkdir()
            local_app_data.mkdir()
            node_temp.mkdir()

            hostile_output = caller / "attacker-selected-playwright-output"
            env = os.environ.copy()
            env["LOCALAPPDATA"] = str(local_app_data)
            env["TEMP"] = str(node_temp)
            env["TMP"] = str(node_temp)
            env["TMPDIR"] = str(node_temp)
            env["PLAYWRIGHT_MCP_OUTPUT_DIR"] = str(hostile_output)

            result = subprocess.run(
                [node, str(LAUNCHER), "--verify-runtime-output-ownership"],
                cwd=caller,
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout.strip().splitlines()[-1])

            caller_resolved = caller.resolve()
            runtime_dir = Path(payload["runtime_dir"]).resolve()
            playwright_dir = Path(payload["playwright_output_dir"]).resolve()
            env_output_dir = Path(payload["playwright_env_output_dir"]).resolve()

            self.assertEqual(Path(payload["caller_cwd"]).resolve(), caller_resolved)
            self.assertEqual(env_output_dir, playwright_dir)
            self.assertNotEqual(playwright_dir, hostile_output.resolve())
            self.assertTrue(playwright_dir.is_dir())
            self.assertTrue(runtime_dir.is_dir())
            self.assertFalse(runtime_dir.is_relative_to(caller_resolved))
            self.assertFalse(playwright_dir.is_relative_to(caller_resolved))
            self.assertFalse((caller / ".playwright-mcp").exists())
            self.assertFalse(hostile_output.exists())

            if os.name == "nt":
                expected_parent = (
                    local_app_data
                    / "ChatAgentPlatform"
                    / "logs"
                    / "semantic-runtime"
                ).resolve()
            else:
                expected_parent = (
                    node_temp
                    / "ChatAgentPlatform"
                    / "logs"
                    / "semantic-runtime"
                ).resolve()
            self.assertTrue(runtime_dir.is_relative_to(expected_parent))


if __name__ == "__main__":
    unittest.main()
