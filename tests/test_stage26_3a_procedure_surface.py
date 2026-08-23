from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
NORMAL_PROFILE = ROOT / "runtime" / "chat-profiles" / "semantic" / "mcp.json"
QUAL_PROFILE = ROOT / "runtime" / "chat-profiles" / "procedure-qualification" / "mcp.json"
PROXY = ROOT / "runtime" / "semantic-projection" / "bin" / "procedure-qualification-projection.mjs"
PACKAGE = ROOT / "runtime" / "semantic-projection" / "package.json"
START = ROOT / "scripts" / "start-procedure-qualification-profile.ps1"


class Stage263AProcedureSurfaceTests(unittest.TestCase):
    def test_normal_semantic_profile_is_unchanged_and_has_no_procedure_authority(self) -> None:
        normal = NORMAL_PROFILE.read_text(encoding="utf-8")
        self.assertIn('"semantic-projection"', normal)
        self.assertNotIn("procedure_run", normal)
        self.assertNotIn("CHAT_PROCEDURE_", normal)
        self.assertNotIn("procedure-qualification", normal)

    def test_qualification_profile_has_separate_entry_and_state_admission(self) -> None:
        profile = json.loads(QUAL_PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(list(profile["mcpServers"]), ["procedure-qualification-projection"])
        server = profile["mcpServers"]["procedure-qualification-projection"]
        self.assertEqual(server["command"], "node")
        self.assertEqual(server["args"], ["${CHAT_PROCEDURE_QUALIFICATION_ENTRY}"])
        self.assertEqual(
            set(server["env"]),
            {
                "CHAT_LOCAL_FILES_ROOT",
                "CHAT_PROCEDURE_STATE_ROOT",
                "CHAT_PROCEDURE_ALLOW_CANDIDATE",
                "CHAT_PROCEDURE_QUALIFICATION_ENTRY",
            },
        )

    def test_procedure_run_schema_is_closed_and_has_no_generic_dispatch(self) -> None:
        source = PROXY.read_text(encoding="utf-8")
        self.assertIn("server.registerTool('procedure_run'", source)
        self.assertIn("z.literal('verified_workspace_artifact_v1')", source)
        self.assertIn("resume_task_id", source)
        self.assertIn("const controlPlaneCli = path.join(repoRoot, 'runtime', 'control_plane', 'cli.py')", source)
        self.assertIn("spawn('python', [controlPlaneCli]", source)
        for forbidden in (
            "args.command",
            "args.path",
            "args.backend",
            "args.tool",
            "args.server",
            "shell: true",
            "eval(",
            "exec(",
        ):
            self.assertNotIn(forbidden, source)

    def test_proxy_scrubs_tunnel_credentials_and_allowlists_control_plane_environment(self) -> None:
        source = PROXY.read_text(encoding="utf-8")
        for secret in ("CONTROL_PLANE_API_KEY", "OPENAI_API_KEY", "OPENAI_ADMIN_KEY"):
            self.assertIn(f"'{secret}'", source)
        self.assertIn("delete process.env[key]", source)
        self.assertIn("CONTROL_PLANE_ENV_ALLOWLIST", source)
        self.assertIn("env: controlPlaneEnvironment()", source)
        allowlist_block = source.split("const CONTROL_PLANE_ENV_ALLOWLIST", 1)[1].split("]);", 1)[0]
        for secret in ("CONTROL_PLANE_API_KEY", "OPENAI_API_KEY", "OPENAI_ADMIN_KEY"):
            self.assertNotIn(secret, allowlist_block)

    def test_proxy_requires_exact_five_tool_semantic_child(self) -> None:
        source = PROXY.read_text(encoding="utf-8")
        for name in (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
        ):
            self.assertIn(f"'{name}'", source)
        self.assertIn("missing.length || unexpected.length", source)
        self.assertIn("exact five-tool semantic surface", source)

    def test_qualification_proxy_is_not_in_production_package_file_allowlist(self) -> None:
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        self.assertNotIn("bin/procedure-qualification-projection.mjs", package["files"])
        self.assertIn("acceptance:procedure-qualification", package["scripts"])

    def test_launcher_requires_exact_six_tool_surface(self) -> None:
        source = START.read_text(encoding="utf-8")
        self.assertIn("CHAT_PROCEDURE_ALLOW_CANDIDATE = $qualificationAdmission", source)
        self.assertIn("'procedure_run'", source)
        self.assertIn("'SEMANTIC_TOOL_COUNT=5'", source)
        self.assertIn("'PROCEDURE_TOOL_COUNT=1'", source)
        self.assertIn("'TOTAL_TOOL_COUNT=6'", source)


if __name__ == "__main__":
    unittest.main()
