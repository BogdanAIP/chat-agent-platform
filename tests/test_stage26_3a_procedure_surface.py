from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_PROFILE = ROOT / "runtime" / "chat-profiles" / "semantic" / "mcp.json"
CONTROL_PLANE = ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-control-plane-projection.mjs"
LAUNCHER = ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-projection-launcher.mjs"
PACKAGE = ROOT / "runtime" / "semantic-projection" / "package.json"
FROZEN_COMPAT = ROOT / "project-context" / "SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md"
OBSOLETE_PROFILE = ROOT / "runtime" / "chat-profiles" / "procedure-qualification" / "mcp.json"
OBSOLETE_PROJECTION = ROOT / "runtime" / "semantic-projection" / "bin" / "procedure-qualification-projection.mjs"
OBSOLETE_START = ROOT / "scripts" / "start-procedure-qualification-profile.ps1"
OBSOLETE_DIRECT = ROOT / "scripts" / "stage26-3a-procedure-direct-tunnel.ps1"
OBSOLETE_HANDOFF = ROOT / "scripts" / "stage26-3a-procedure-supervised-handoff.ps1"


class Stage263AProcedureSurfaceTests(unittest.TestCase):
    def test_semantic_profile_is_the_only_stage26_3a_chat_profile(self) -> None:
        profile = json.loads(SEMANTIC_PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(list(profile["mcpServers"]), ["semantic-projection"])
        server = profile["mcpServers"]["semantic-projection"]
        self.assertEqual(server["command"], "node")
        self.assertEqual(server["args"], ["${CHAT_SEMANTIC_PROJECTION_ENTRY}"])
        self.assertIn("procedure", server["tags"])
        self.assertIn("control-plane", server["tags"])
        self.assertFalse(OBSOLETE_PROFILE.exists())
        self.assertFalse(OBSOLETE_START.exists())
        self.assertFalse(OBSOLETE_DIRECT.exists())
        self.assertFalse(OBSOLETE_HANDOFF.exists())

    def test_public_launcher_always_enters_six_tool_control_plane(self) -> None:
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("semantic-control-plane-projection.mjs", launcher)
        self.assertNotIn("path.join(launcherDir, 'semantic-projection.mjs')", launcher)
        for name in (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
            "procedure_run",
        ):
            self.assertIn(name, launcher)

    def test_frozen_action_compatibility_is_exact_and_snapshot_boundary_is_documented(self) -> None:
        launcher = LAUNCHER.read_text(encoding="utf-8")
        documentation = FROZEN_COMPAT.read_text(encoding="utf-8")
        canonical = (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
            "procedure_run",
        )
        prefixes = (
            "semantic-projection_1mcp_",
            "procedure-qualification-projection_1mcp_",
        )
        for prefix in prefixes:
            for name in canonical:
                alias = f"{prefix}{name}"
                self.assertIn(alias, launcher)
                self.assertIn(alias, documentation)

        self.assertIn("const LEGACY_TOOL_ALIASES = new Map", launcher)
        self.assertIn("LEGACY_TOOL_ALIASES.has(message.params.name)", launcher)
        self.assertNotIn("replace('semantic-projection_1mcp_'", launcher)
        self.assertNotIn("replace(\"semantic-projection_1mcp_\"", launcher)

        for required in (
            "Critical ChatGPT frozen-snapshot boundary",
            "after ChatGPT has already selected an action",
            "cannot repair ChatGPT-side state",
            "app/connector connection state",
            "per-action permission or confirmation state",
            "App rebind gate before final Stage 26.3A E2E",
            "newly created or explicitly rebound ChatGPT app",
        ):
            self.assertIn(required, documentation)

    def test_public_control_plane_registers_exact_six_tool_model(self) -> None:
        source = CONTROL_PLANE.read_text(encoding="utf-8")
        for name in (
            "workspace_read",
            "workspace_write",
            "web_open",
            "web_observe",
            "web_interact",
            "procedure_run",
        ):
            self.assertIn(f"'{name}'", source)
        self.assertIn("PUBLIC_TOOLS.size !== 6", source)
        self.assertIn("always exposes exactly six reviewed tools", source)
        self.assertNotIn("qualification-only", source.lower())
        self.assertFalse(OBSOLETE_PROJECTION.exists())

    def test_procedure_run_schema_is_closed_and_has_no_generic_dispatch(self) -> None:
        source = CONTROL_PLANE.read_text(encoding="utf-8")
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

    def test_control_plane_scrubs_tunnel_credentials_and_allowlists_children(self) -> None:
        source = CONTROL_PLANE.read_text(encoding="utf-8")
        for secret in ("CONTROL_PLANE_API_KEY", "OPENAI_API_KEY", "OPENAI_ADMIN_KEY"):
            self.assertIn(f"'{secret}'", source)
        self.assertIn("delete process.env[key]", source)
        self.assertIn("SAFE_CHILD_ENV_ALLOWLIST", source)
        self.assertIn("env: safeChildEnvironment()", source)
        self.assertIn("env,", source)
        allowlist_block = source.split("const SAFE_CHILD_ENV_ALLOWLIST", 1)[1].split("]);", 1)[0]
        for secret in ("CONTROL_PLANE_API_KEY", "OPENAI_API_KEY", "OPENAI_ADMIN_KEY"):
            self.assertNotIn(secret, allowlist_block)

    def test_package_ships_the_canonical_control_plane_projection(self) -> None:
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        self.assertIn("bin/semantic-control-plane-projection.mjs", package["files"])
        self.assertNotIn("bin/procedure-qualification-projection.mjs", package["files"])
        self.assertIn("acceptance:six-tool", package["scripts"])
        self.assertNotIn("acceptance:procedure-qualification", package["scripts"])


if __name__ == "__main__":
    unittest.main()
