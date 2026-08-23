from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "runtime" / "semantic-projection" / "bin" / "procedure-qualification-projection.mjs"


class Stage263AProcedureSurfaceSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PROJECTION.read_text(encoding="utf-8")

    def test_all_descendants_use_explicit_environment_allowlist(self) -> None:
        self.assertIn("const CONTROL_PLANE_ENV_ALLOWLIST = new Set", self.source)
        self.assertIn("function scopedChildEnvironment()", self.source)
        self.assertGreaterEqual(self.source.count("env: scopedChildEnvironment()"), 2)
        self.assertNotIn("env: process.env", self.source)

    def test_descendants_do_not_receive_tunnel_or_openai_credentials(self) -> None:
        allowlist_block = self.source[
            self.source.index("const CONTROL_PLANE_ENV_ALLOWLIST") :
            self.source.index("function toolError")
        ]
        for forbidden in (
            "CONTROL_PLANE_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_ADMIN_KEY",
            "TUNNEL_TOKEN",
        ):
            self.assertNotIn(forbidden, allowlist_block)
        for required in (
            "CHAT_LOCAL_FILES_ROOT",
            "CHAT_PROCEDURE_STATE_ROOT",
            "CHAT_PROCEDURE_ALLOW_CANDIDATE",
        ):
            self.assertIn(required, allowlist_block)

        for secret in (
            "CONTROL_PLANE_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_ADMIN_KEY",
        ):
            self.assertIn(f"'{secret}'", self.source)
        self.assertIn("delete process.env[key]", self.source)

    def test_procedure_surface_remains_fixed_and_non_generic(self) -> None:
        for required in (
            "verified_workspace_artifact_v1",
            "resume_task_id",
            "openWorldHint: false",
        ):
            self.assertIn(required, self.source)
        for forbidden in (
            "server.registerTool('shell'",
            "server.registerTool('python'",
            "server.registerTool('tool_invoke'",
            "server.registerTool('exec'",
        ):
            self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
