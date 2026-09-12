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
BUNDLE_BUILDER = (EXPERIMENT / "build_private_bundle.py").read_text(encoding="utf-8")
COLLECTOR_SOURCE = (EXPERIMENT / "collector.py").read_text(encoding="utf-8")

spec = importlib.util.spec_from_file_location("temporary_reviewer_collector", EXPERIMENT / "collector.py")
assert spec is not None and spec.loader is not None
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

bundle_spec = importlib.util.spec_from_file_location("temporary_reviewer_bundle", EXPERIMENT / "build_private_bundle.py")
assert bundle_spec is not None and bundle_spec.loader is not None
bundle_builder = importlib.util.module_from_spec(bundle_spec)
bundle_spec.loader.exec_module(bundle_builder)


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
        self.assertIn("resultIdentitySummary(text, intent)", CONTENT)
        self.assertIn("completion_marker_at_end", POLICY)
        self.assertIn("TEMP_REVIEW_IDENTITY_DIAGNOSTICS", LAUNCHER_TEXT)

    def test_private_bundle_intent_is_run_hash_and_nonce_bound(self) -> None:
        self.assertIn('url.searchParams.get("cap_bundle") === "1"', POLICY)
        self.assertIn('url.searchParams.get("cap_bundle_sha256")', POLICY)
        self.assertIn('url.searchParams.get("cap_bundle_nonce")', POLICY)
        self.assertIn("PRIVATE_BUNDLE_CONTROL_V1", POLICY)
        self.assertIn("PRIVATE_BUNDLE_REVIEW_RESULT_V1", POLICY)
        self.assertIn('fields.get("bundle_nonce") === intent.bundleNonce', POLICY)
        self.assertIn('fields.get("evidence_source") === "bundle_only"', POLICY)
        self.assertIn('externalWebUsed === "no"', POLICY)

    def test_private_bundle_is_fetched_verified_and_injected_before_send(self) -> None:
        self.assertIn('sendToCollector("bundle")', CONTENT)
        self.assertIn('crypto.subtle.digest("SHA-256"', CONTENT)
        self.assertIn("bundle-sha256-mismatch", CONTENT)
        self.assertIn("bundle-content-binding-mismatch", CONTENT)
        self.assertIn("appendTextToEditor", CONTENT)
        self.assertIn("bundle-injected", CONTENT)
        injection_gate = CONTENT.index("if (intent.bundleMode && !bundleInjected)")
        send_marker = CONTENT.index("sessionStorage.setItem(\n        policy.attemptKey")
        self.assertLess(injection_gate, send_marker)

    def test_private_bundle_builder_is_local_git_only_and_pseudonymizes_identity(self) -> None:
        self.assertIn('["git", "-C", str(repo)', BUNDLE_BUILDER)
        self.assertNotIn("requests", BUNDLE_BUILDER)
        self.assertNotIn("urllib", BUNDLE_BUILDER)
        self.assertNotIn("https://api.github.com", BUNDLE_BUILDER)
        self.assertIn("REVIEW_EVIDENCE_BUNDLE_V1", BUNDLE_BUILDER)
        self.assertIn("external_network_used_by_builder=no", BUNDLE_BUILDER)
        self.assertIn("PrivateControl/reviewer-fixture", BUNDLE_BUILDER)
        original = "BogdanAIP/chat-agent-platform 0123456789abcdef0123456789abcdef01234567"
        redacted = bundle_builder.pseudonymize(original, "a" * 64)
        self.assertNotIn("BogdanAIP/chat-agent-platform", redacted)
        self.assertNotIn("0123456789abcdef0123456789abcdef01234567", redacted)
        self.assertRegex(redacted, r"PrivateControl/reviewer-fixture [0-9a-f]{40}")

    def test_library_stage_does_not_disclose_evidence_nonce_in_prompt_or_url(self) -> None:
        self.assertIn("parseLibraryStageIntent", POLICY)
        self.assertIn("cap_library_stage", POLICY)
        self.assertIn("libraryEvidenceKey", POLICY)
        self.assertIn("extractBundleNonce", CONTENT)
        self.assertIn("sessionStorage.setItem(policy.libraryEvidenceKey(stageIntent.runId), evidenceNonce)", CONTENT)
        self.assertIn("TEMP_REVIEW_LIBRARY_NONCE_DISCLOSED_TO_PROMPT=False", LAUNCHER_TEXT)
        self.assertNotIn("cap_library_nonce", LAUNCHER_TEXT)
        self.assertNotIn("evidence_nonce=$bundleNonce", LAUNCHER_TEXT)

    def test_library_stage_fetches_local_file_and_uploads_it_without_native_filesystem_authority(self) -> None:
        self.assertIn("library-stage-loaded", CONTENT)
        self.assertIn('const file = new File([response.text], stageIntent.libraryFilename', CONTENT)
        self.assertIn('document.querySelectorAll(\'input[type="file"]\')', CONTENT)
        self.assertIn("new DataTransfer()", CONTENT)
        self.assertIn("library-file-uploaded", CONTENT)
        self.assertIn("location.assign(reviewUrl.toString())", CONTENT)
        self.assertIn("regular-chat-library-stage-then-temporary-chat", LAUNCHER_TEXT)

    def test_library_review_selects_saved_file_before_send_and_binds_final_result_to_file_nonce(self) -> None:
        self.assertIn('url.searchParams.get("cap_library_review") === "1"', POLICY)
        self.assertIn("LIBRARY_PRIVATE_CONTROL_V1", POLICY)
        self.assertIn("LIBRARY_PRIVATE_REVIEW_RESULT_V1", POLICY)
        self.assertIn('fields.get("evidence_nonce") === intent.evidenceNonce', POLICY)
        self.assertIn('fields.get("evidence_source") === "library_file"', POLICY)
        self.assertIn("findLibraryMenuItem", CONTENT)
        self.assertIn("findLibraryFileNode", CONTENT)
        self.assertIn("library-file-attached", CONTENT)
        library_gate = CONTENT.index("if (intent.libraryMode && !libraryAttached)")
        send_marker = CONTENT.index("sessionStorage.setItem(\n        policy.attemptKey")
        self.assertLess(library_gate, send_marker)

    def test_library_review_allows_generic_external_research_but_not_repository_lookup(self) -> None:
        self.assertIn("You MAY use built-in web search for general public technical documentation", LAUNCHER_TEXT)
        self.assertIn("Do not use GitHub or web search to locate, reconstruct, or supplement the private repository", LAUNCHER_TEXT)
        self.assertIn("do not search the web for unique identifiers or code snippets", LAUNCHER_TEXT)
        self.assertIn("external_research_used=no|yes", LAUNCHER_TEXT)
        self.assertIn("TEMP_REVIEW_EXTERNAL_RESEARCH_USED", LAUNCHER_TEXT)

    def test_extension_transport_is_not_native_messaging_or_mcp(self) -> None:
        for text in (POLICY, CONTENT, BACKGROUND):
            self.assertNotIn("nativeMessaging", text)
            self.assertNotIn("/mcp", text)
            self.assertNotIn("workspace_write", text)
            self.assertNotIn("procedure_run", text)
        self.assertIn('const COLLECTOR_ORIGIN = "http://127.0.0.1:3077"', BACKGROUND)
        self.assertIn('new Set(["event", "capture", "bundle"])', BACKGROUND)
        self.assertIn('fetch(`${COLLECTOR_ORIGIN}/bundle`', BACKGROUND)

    def test_collector_accepts_only_bounded_evidence_schemas(self) -> None:
        run_id = "tmprev-" + "a" * 32
        event = collector.validate_event(
            {
                "schema_version": 1,
                "run_id": run_id,
                "event": "library-file-attached",
                "details": {"filename": f"cap-private-review-{run_id}.txt"},
            },
            run_id,
        )
        self.assertEqual("library-file-attached", event["event"])
        capture = collector.validate_capture(
            {
                "schema_version": 1,
                "run_id": run_id,
                "temporary_state": {},
                "capture_kind": "structured",
                "result_text": "LIBRARY_PRIVATE_REVIEW_RESULT_V1\nstatus=FINDINGS",
                "diagnostics": {},
            },
            run_id,
        )
        self.assertEqual("structured", capture["capture_kind"])
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            collector.validate_capture({**capture, "command": "invalid"}, run_id)

    def test_collector_is_loopback_only_and_bundle_read_is_authenticated(self) -> None:
        lower = COLLECTOR_SOURCE.lower()
        self.assertIn('ThreadingHTTPServer(("127.0.0.1", args.port)', COLLECTOR_SOURCE)
        self.assertIn('if self.path != "/bundle"', COLLECTOR_SOURCE)
        self.assertIn('self.headers.get("X-CAP-Collector-Token") != state.token', COLLECTOR_SOURCE)
        self.assertIn("MAX_BUNDLE_BYTES", COLLECTOR_SOURCE)
        for forbidden in ("subprocess", "os.system", "popen(", "shell=true", "requests.", "github"):
            self.assertNotIn(forbidden, lower)

    def test_launcher_has_fixed_controls_without_answer_leak(self) -> None:
        self.assertIn("'privatebundle140'", LAUNCHER_TEXT)
        self.assertIn("'libraryfile140'", LAUNCHER_TEXT)
        self.assertIn("PrNumber = 146", LAUNCHER_TEXT)
        self.assertIn("8318a592848cad66bb6d8e56b10b04b646bc9137", LAUNCHER_TEXT)
        self.assertIn("858dcb7dd065717ea0d59b1e7b931b13a844f8d4", LAUNCHER_TEXT)
        self.assertIn("b10a5fa3122bb6c76c12d37d67911b88e5e1ce28", LAUNCHER_TEXT)
        self.assertIn("7077ecb8496ee89530cbe5efaa1b2112e7be330f", LAUNCHER_TEXT)
        self.assertNotIn("four P1", LAUNCHER_TEXT)
        self.assertNotIn("known finding", LAUNCHER_TEXT.lower())

    def test_private_bundle_control_forbids_external_evidence(self) -> None:
        self.assertIn("Use ONLY that injected REVIEW_EVIDENCE_BUNDLE_V1", LAUNCHER_TEXT)
        self.assertIn("Do not use built-in web search, GitHub", LAUNCHER_TEXT)
        self.assertIn("evidence_source=bundle_only", LAUNCHER_TEXT)
        self.assertIn("external_web_used=no|yes", LAUNCHER_TEXT)
        self.assertIn("TEMP_REVIEW_VISIBLE_WEB_ACTIVITY_COUNT", LAUNCHER_TEXT)
        self.assertIn("visible_web_activity", CONTENT)

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
