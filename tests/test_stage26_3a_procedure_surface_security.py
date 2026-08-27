from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "runtime" / "semantic-projection" / "bin" / "semantic-control-plane-projection.mjs"


class Stage263AProcedureSurfaceSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PROJECTION.read_text(encoding="utf-8")

    def test_all_descendants_use_explicit_environment_allowlists(self) -> None:
        self.assertIn("const SAFE_CHILD_ENV_ALLOWLIST = new Set", self.source)
        self.assertIn("function safeChildEnvironment()", self.source)
        self.assertIn("function controlPlaneEnvironment(request)", self.source)
        self.assertIn("env: safeChildEnvironment()", self.source)
        self.assertNotIn("env: process.env", self.source)

    def test_descendants_do_not_receive_tunnel_or_openai_credentials(self) -> None:
        allowlist_block = self.source[
            self.source.index("const SAFE_CHILD_ENV_ALLOWLIST") :
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
        ):
            self.assertIn(required, allowlist_block)

        for secret in (
            "CONTROL_PLANE_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_ADMIN_KEY",
        ):
            self.assertIn(f"'{secret}'", self.source)
        self.assertIn("delete process.env[key]", self.source)

    def test_public_surface_is_six_tools_but_procedure_registry_remains_non_generic(self) -> None:
        self.assertIn("PUBLIC_TOOLS.size !== 6", self.source)
        for required in (
            "verified_workspace_artifact_v1",
            "windows_case_update_v1",
            "resume_task_id",
            "case_id",
            "note",
            "status",
            "openWorldHint: false",
        ):
            self.assertIn(required, self.source)
        for forbidden in (
            "server.registerTool('shell'",
            "server.registerTool('python'",
            "server.registerTool('tool_invoke'",
            "server.registerTool('exec'",
            "pid: z.",
            "hwnd: z.",
            "path: z.string().optional()",
            "backend: z.",
            "command: z.",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_windows_runtime_and_admission_are_selected_only_by_registered_procedure(self) -> None:
        self.assertIn("request?.procedure === WINDOWS_CASE_PROCEDURE", self.source)
        self.assertIn("'stage26-3b-windows-l3'", self.source)
        self.assertIn("'hot-runtime-env'", self.source)
        self.assertIn("'python.exe'", self.source)
        self.assertIn("fs.existsSync(python)", self.source)
        self.assertNotIn("request.python", self.source)
        self.assertNotIn("request.executable", self.source)
        self.assertNotIn("request.admission", self.source)


if __name__ == "__main__":
    unittest.main()
