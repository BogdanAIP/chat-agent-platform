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

    def test_capture_requires_explicit_run_bound_terminal_marker(self) -> None:
        self.assertIn("CAP_TEMP_REVIEW_COMPLETE=", POLICY)
        self.assertIn("completionMarker", POLICY)
        self.assertIn("hasTerminalMarker", CONTENT)
        self.assertIn("if (!hasTerminalMarker(last)) return;", CONTENT)
        self.assertIn("Do not emit that completion line in progress updates", LAUNCHER_TEXT)
        self.assertNotEqual(8000, int(POLICY.split("const STABLE_MS = ", 1)[1].split(";", 1)[0]))

    def test_result_identity_is_derived_from_exact_request_and_tolerates_rendering(self) -> None:
        for marker in (
            'requestField(prompt, "repository")',
            'requestField(prompt, "pr_number")',
            'requestField(prompt, "base_sha")',
            'requestField(prompt, "head_sha")',
            'requestField(prompt, "review_skill_version")',
        ):
            self.assertIn(marker, POLICY)
        self.assertIn("normalizeReviewText", POLICY)
        self.assertIn("parseResultFields", POLICY)
        self.assertIn('replace(/\\\\_/g, "_")', POLICY)
        self.assertIn("resultIdentitySummary(text, intent)", CONTENT)
        self.assertIn("completion_marker_at_end", POLICY)
        self.assertIn("TEMP_REVIEW_IDENTITY_DIAGNOSTICS", LAUNCHER_TEXT)

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
            collector.validate_capture({**capture, "command": "invalid"}, run_id)

    def test_collector_is_loopback_only_and_has_no_execution_backend(self) -> None:
        source = (EXPERIMENT / "collector.py").read_text(encoding="utf-8")
        lower = source.lower()
        self.assertIn('ThreadingHTTPServer(("127.0.0.1", args.port)', source)
        self.assertIn('self.path not in {"/event", "/capture"}', source)
        for forbidden in ("subprocess", "os.system", "popen(", "shell=true", "requests.", "github"):
            self.assertNotIn(forbidden, lower)

    def test_launcher_has_fixed_controls_without_answer_leak(self) -> None:
        self.assertIn("[ValidateSet('pass142', 'stale140', 'findings146', 'exact')]", LAUNCHER_TEXT)
        self.assertIn("pr_number=$($target.PrNumber)", LAUNCHER_TEXT)
        self.assertIn("PrNumber = 146", LAUNCHER_TEXT)
        self.assertIn("8318a592848cad66bb6d8e56b10b04b646bc9137", LAUNCHER_TEXT)
        self.assertIn("858dcb7dd065717ea0d59b1e7b931b13a844f8d4", LAUNCHER_TEXT)
        self.assertIn("b10a5fa3122bb6c76c12d37d67911b88e5e1ce28", LAUNCHER_TEXT)
        self.assertIn("7077ecb8496ee89530cbe5efaa1b2112e7be330f", LAUNCHER_TEXT)
        prompt_start = LAUNCHER_TEXT.index('$prompt = @"')
        prompt_end = LAUNCHER_TEXT.index('"@', prompt_start)
        prompt = LAUNCHER_TEXT[prompt_start:prompt_end]
        self.assertNotIn("known accepted outcome", prompt.lower())
        self.assertNotIn("four p1", prompt.lower())
        self.assertNotIn("known finding", prompt.lower())

    def test_exact_target_mode_is_identity_only_and_repository_fixed(self) -> None:
        self.assertIn("if ($Control -eq 'exact')", LAUNCHER_TEXT)
        self.assertIn("TargetPrNumber", LAUNCHER_TEXT)
        self.assertIn("TargetBaseSha", LAUNCHER_TEXT)
        self.assertIn("TargetHeadSha", LAUNCHER_TEXT)
        self.assertIn("^[0-9a-f]{40}$", LAUNCHER_TEXT)
        self.assertIn("TargetSkillVersion -notin @('1.0', '1.1')", LAUNCHER_TEXT)
        self.assertNotIn("TargetFocus", LAUNCHER_TEXT)
        self.assertIn("repository=BogdanAIP/chat-agent-platform", LAUNCHER_TEXT)
        self.assertNotIn("TargetRepository", LAUNCHER_TEXT)
        self.assertNotIn("TargetUrl", LAUNCHER_TEXT)
        self.assertNotIn("TargetBackend", LAUNCHER_TEXT)
        self.assertIn("affected experiment-only browser delivery", LAUNCHER_TEXT)

    def test_launcher_never_reports_protocol_status_for_unstructured_capture(self) -> None:
        self.assertIn("[string]$result.capture_kind -eq 'structured' -and $statusMatch.Success", LAUNCHER_TEXT)
        self.assertIn("else { 'UNSTRUCTURED' }", LAUNCHER_TEXT)

    def test_physical_observations_record_pass_stale_and_findings(self) -> None:
        for run_id in (
            "tmprev-dca1dbf983014bce8341623c8b8fb943",
            "tmprev-0269cce47a08437c92084f43e60affa5",
            "tmprev-52933398b0074575b1e0b2fb87ae1036",
        ):
            self.assertIn(run_id, README)
        self.assertIn("TEMP_REVIEW_CAPTURE=structured", README)
        self.assertIn("TEMP_REVIEW_STATUS=FINDINGS", README)
        self.assertIn("reported exactly four P1 findings", README)
        self.assertIn("CONFIRMED -> FIXED MATERIALLY", README)

    def test_launcher_is_one_command_without_clipboard_or_manual_prompt_input(self) -> None:
        self.assertIn("https://chatgpt.com/?temporary-chat=true", LAUNCHER_TEXT)
        self.assertIn("Start-Process $url", LAUNCHER_TEXT)
        for forbidden in ("Read-Host", "Get-Clipboard", "Set-Clipboard"):
            self.assertNotIn(forbidden, LAUNCHER_TEXT)

    def test_experiment_does_not_claim_architecture_or_production_acceptance(self) -> None:
        self.assertIn("EXPERIMENT ONLY — NO PRODUCTION AUTHORITY", README)
        self.assertIn("does **not** implement or authorize production", README)
        self.assertIn("without manual prompt/result copy-paste", README)
        self.assertIn("Those decisions require fresh Stage Research after physical evidence exists.", README)


if __name__ == "__main__":
    unittest.main()
