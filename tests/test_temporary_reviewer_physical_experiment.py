from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "chatgpt-temporary-reviewer"
LAUNCHER = ROOT / "scripts" / "launch-temporary-reviewer-probe.ps1"
README = (EXPERIMENT / "README.md").read_text(encoding="utf-8")
POLICY = (EXPERIMENT / "policy.js").read_text(encoding="utf-8")
CONTENT = (EXPERIMENT / "content.js").read_text(encoding="utf-8")
BACKGROUND = (EXPERIMENT / "background.js").read_text(encoding="utf-8")
LAUNCHER_TEXT = LAUNCHER.read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("temporary_reviewer_collector", EXPERIMENT / "collector.py")
assert spec is not None and spec.loader is not None
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class TemporaryReviewerPhysicalExperimentTests(unittest.TestCase):
    def test_manifest_has_only_the_experiment_loopback_host_permission(self) -> None:
        manifest = json.loads((EXPERIMENT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(3, manifest["manifest_version"])
        self.assertEqual(["http://127.0.0.1:3077/*"], manifest["host_permissions"])
        self.assertNotIn("permissions", manifest)
        self.assertEqual("background.js", manifest["background"]["service_worker"])
        self.assertEqual(["https://chatgpt.com/*"], manifest["content_scripts"][0]["matches"])

    def test_probe_is_bound_to_temporary_chat_and_one_send_attempt(self) -> None:
        self.assertIn('url.searchParams.get("temporary-chat") !== "true"', POLICY)
        self.assertIn('url.searchParams.get("cap_temp_review") !== "1"', POLICY)
        self.assertIn("CAP_TEMP_REVIEW_RUN_ID=", POLICY)
        self.assertIn("REVIEW_REQUEST_V1", POLICY)
        send_marker = CONTENT.index("sessionStorage.setItem(\n        policy.attemptKey")
        click = CONTENT.index("button.click()")
        self.assertLess(send_marker, click)
        self.assertIn("temporary-ui-not-proven", CONTENT)
        self.assertIn("positive_ui_evidence", CONTENT)

    def test_extension_transport_is_not_native_messaging_or_mcp(self) -> None:
        for text in (POLICY, CONTENT, BACKGROUND):
            self.assertNotIn("nativeMessaging", text)
            self.assertNotIn("/mcp", text)
            self.assertNotIn("workspace_write", text)
            self.assertNotIn("procedure_run", text)
        self.assertIn('const COLLECTOR_ORIGIN = "http://127.0.0.1:3077"', BACKGROUND)
        self.assertIn('new Set(["event", "capture"])', BACKGROUND)

    def test_collector_accepts_only_bounded_evidence_schemas(self) -> None:
        run_id = "tmprev-" + "a" * 32
        event = collector.validate_event(
            {
                "schema_version": 1,
                "run_id": run_id,
                "event": "send-attempted",
                "details": {"temporary": True},
            },
            run_id,
        )
        self.assertEqual("send-attempted", event["event"])
        capture = collector.validate_capture(
            {
                "schema_version": 1,
                "run_id": run_id,
                "temporary_state": {},
                "capture_kind": "structured",
                "result_text": "REVIEW_RESULT_V1\nstatus=PASS",
                "diagnostics": {},
            },
            run_id,
        )
        self.assertEqual("structured", capture["capture_kind"])
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            collector.validate_capture({**capture, "command": "whoami"}, run_id)

    def test_collector_is_loopback_only_and_has_no_execution_backend(self) -> None:
        source = (EXPERIMENT / "collector.py").read_text(encoding="utf-8")
        lower = source.lower()
        self.assertIn('ThreadingHTTPServer(("127.0.0.1", args.port)', source)
        self.assertIn('self.path not in {"/event", "/capture"}', source)
        for forbidden in ("subprocess", "os.system", "popen(", "shell=true", "requests.", "github"):
            self.assertNotIn(forbidden, lower)

    def test_launcher_is_one_command_without_clipboard_or_manual_prompt_input(self) -> None:
        self.assertIn("https://chatgpt.com/?temporary-chat=true", LAUNCHER_TEXT)
        self.assertIn("Start-Process $url", LAUNCHER_TEXT)
        self.assertIn("pr_number=142", LAUNCHER_TEXT)
        self.assertIn("8318a592848cad66bb6d8e56b10b04b646bc9137", LAUNCHER_TEXT)
        self.assertIn("858dcb7dd065717ea0d59b1e7b931b13a844f8d4", LAUNCHER_TEXT)
        for forbidden in ("Read-Host", "Get-Clipboard", "Set-Clipboard"):
            self.assertNotIn(forbidden, LAUNCHER_TEXT)

    def test_experiment_does_not_claim_architecture_or_production_acceptance(self) -> None:
        self.assertIn("EXPERIMENT ONLY — NO PRODUCTION AUTHORITY", README)
        self.assertIn("does **not** implement or authorize production", README)
        self.assertIn("without manual prompt/result copy-paste", README)
        self.assertIn("Those decisions require fresh Stage Research after physical evidence exists.", README)


if __name__ == "__main__":
    unittest.main()
