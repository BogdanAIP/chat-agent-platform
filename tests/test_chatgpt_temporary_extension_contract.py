from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"


class ChatGPTTemporaryExtensionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
        self.background = (EXTENSION / "background.js").read_text(encoding="utf-8")
        self.content = (EXTENSION / "content.js").read_text(encoding="utf-8")
        self.policy = (EXTENSION / "policy.js").read_text(encoding="utf-8")
        self.generation = (EXTENSION / "execution_generation.js").read_text(encoding="utf-8")

    def test_extension_authority_is_narrow_and_loopback_only(self) -> None:
        self.assertEqual(3, self.manifest["manifest_version"])
        self.assertNotIn("permissions", self.manifest)
        self.assertEqual(["http://127.0.0.1:3078/*"], self.manifest["host_permissions"])
        folded = json.dumps(self.manifest).casefold()
        for forbidden in (
            "nativemessaging",
            "downloads",
            "management",
            "cookies",
            "webrequest",
            "github.com",
            "api.github.com",
        ):
            self.assertNotIn(forbidden, folded)

    def test_send_claim_schema_is_preinitialized_and_claim_path_never_upgrades(self) -> None:
        for phrase in (
            'chrome.runtime.onInstalled.addListener',
            'chrome.runtime.onStartup.addListener',
            'indexedDB.open(DB_NAME, DB_VERSION)',
            'db.createObjectStore(CLAIM_STORE)',
            'function openExistingClaimDb()',
            'request.transaction?.abort()',
            '"claim-db-schema-missing"',
        ):
            self.assertIn(phrase, self.background)
        claim = self.background[
            self.background.index("async function claimBrowserSend") :
            self.background.index("async function claimRecordByDelivery")
        ]
        self.assertIn('db.transaction(CLAIM_STORE, "readwrite")', claim)
        self.assertIn("store.add(", claim)
        self.assertIn("expected_runtime_head: message.expected_runtime_head", claim)
        self.assertIn("prompt_sha256: message.prompt_sha256", claim)
        self.assertIn("claim_tab_id: tabId", claim)
        self.assertNotIn("run_id:", claim)
        self.assertNotIn("conversation_id", claim)
        self.assertNotIn("store.put(", claim)
        self.assertNotIn("store.delete", self.background)

    def test_live_preflight_handoff_exists_before_task_authority(self) -> None:
        self.assertIn("const LIVE_LAUNCHES = new Map();", self.background)
        self.assertIn("function preflightIdFromSender", self.background)
        self.assertIn('url.searchParams.get("cap_agent_preflight") !== "1"', self.background)
        self.assertIn('fragment.get("cap_preflight_id")', self.background)
        self.assertIn('preflightPost(preflightId, "/preflight"', self.background)
        self.assertIn("LIVE_LAUNCHES.set(prepared.launch_handle, live)", self.background)
        self.assertIn('preflightPost(preflightId, "/preflight-commit"', self.background)
        self.assertIn("function resolveLiveMessage(message)", self.background)
        self.assertIn("const live = LIVE_LAUNCHES.get(launchHandle)", self.background)
        self.assertIn("run_id: live.run_id", self.background)
        self.assertIn('reason: "live-launch-context-expired-or-invalid"', self.background)

    def test_executing_generation_and_runtime_bytes_are_attested_before_preflight_send_and_capture_prepare(self) -> None:
        for phrase in (
            'importScripts("execution_generation.js");',
            'const EXECUTION_GENERATION = globalThis.CAPChatGPTTemporaryExecutionGeneration || "";',
            'const RUNTIME_ASSETS = ["manifest.json", "execution_generation.js", "policy.js", "background.js", "content.js"]',
            'crypto.subtle.digest("SHA-256", buffer)',
            "chrome.runtime.getURL(name)",
            "async function runtimeAttestation()",
            "execution_generation: EXECUTION_GENERATION",
        ):
            self.assertIn(phrase, self.background)
        self.assertIn("CAPChatGPTTemporaryExecutionGeneration", self.generation)
        self.assertEqual(
            ["execution_generation.js", "policy.js", "content.js"],
            self.manifest["content_scripts"][0]["js"],
        )
        self.assertIn("execution_generation: executionGeneration", self.content)
        preflight = self.background[
            self.background.index("async function prepareLiveLaunch") :
            self.background.index("function resolveLiveMessage")
        ]
        self.assertGreaterEqual(preflight.count("runtimeAttestation()"), 2)
        prepare = self.background[
            self.background.index('message.kind === "prepare-capture"') :
            self.background.index('message.kind === "capture"')
        ]
        self.assertIn("runtimeAttestation()", prepare)
        commit = self.background[
            self.background.index('message.kind === "capture"') :
            self.background.index('message.kind === "final-observation"')
        ]
        self.assertNotIn("runtimeAttestation()", commit)
        self.assertIn("capture_token: message.capture_token", commit)

    def test_browser_claim_keeps_exact_delivery_identity_and_live_owner_fence(self) -> None:
        exact = self.background[
            self.background.index("function exactClaimMatches") :
            self.background.index("async function controllerPost")
        ]
        for phrase in (
            "record.delegation_id === message.delegation_id",
            "record.delivery_id === message.delivery_id",
            "record.task_sha256 === message.task_sha256",
            "record.expected_runtime_head === message.expected_runtime_head",
            "record.prompt_sha256 === message.prompt_sha256",
        ):
            self.assertIn(phrase, exact)
        self.assertNotIn("record.run_id", exact)
        self.assertIn("const LIVE_PRE_SEND_CLAIMS = new Set();", self.background)
        self.assertIn("LIVE_PRE_SEND_CLAIMS.add(message.delivery_id)", self.background)
        self.assertIn("LIVE_PRE_SEND_CLAIMS.has(message.delivery_id)", self.background)
        self.assertIn("existing.claim_tab_id !== tabId", self.background)
        self.assertNotIn("claimRecordsForRecovery", self.background)

    def test_complete_browser_restart_recovery_is_disabled_but_neutral_preflight_can_arm_initial_launch(self) -> None:
        self.assertNotIn("async function resumeIntent", self.background)
        self.assertNotIn("async function bindRecoveryConversation", self.background)
        self.assertNotIn("async function bindClaimConversationRecord", self.background)
        self.assertNotIn("senderConversationId", self.background)
        self.assertNotIn("observedClaimMatches", self.background)
        self.assertIn('incoming.kind === "resume-intent"', self.background)
        self.assertIn("const preflightId = preflightIdFromSender(sender)", self.background)
        self.assertIn('reason: "temporary-profile-ephemeral"', self.background)
        self.assertIn("enabled: false", self.background)
        self.assertNotIn("run_id: value", self.background)

    def test_post_send_existing_claim_never_grants_monitor_or_second_send(self) -> None:
        authorize = self.background[
            self.background.index("async function authorizeSend") :
            self.background.index("chrome.runtime.onInstalled")
        ]
        self.assertIn('reason: "temporary-profile-ephemeral"', authorize)
        self.assertIn("monitor_only: false", authorize)
        self.assertNotIn("const monitorOnly =", authorize)
        self.assertNotIn("monitor_only: true", authorize)

    def test_pre_send_recovery_is_bound_to_exact_head_prompt_live_owner_and_tab(self) -> None:
        authorize = self.background[
            self.background.index("async function authorizeSend") :
            self.background.index("chrome.runtime.onInstalled")
        ]
        exact = self.background[
            self.background.index("function exactClaimMatches") :
            self.background.index("async function controllerPost")
        ]
        local = self.background[
            self.background.index("async function requestLocalSendAuthority") :
            self.background.index("async function authorizeSend")
        ]
        self.assertIn('status.delivery_state === "prepared"', authorize)
        self.assertIn('["launch-attempted", "child-bound"].includes(status.launch_state)', authorize)
        self.assertIn("exactClaimMatches(existing, message)", authorize)
        self.assertIn("LIVE_PRE_SEND_CLAIMS.has(message.delivery_id)", authorize)
        self.assertIn("existing.claim_tab_id !== tabId", authorize)
        self.assertIn("record.expected_runtime_head === message.expected_runtime_head", exact)
        self.assertIn("record.prompt_sha256 === message.prompt_sha256", exact)
        self.assertIn("expected_runtime_head: message.expected_runtime_head", local)
        self.assertIn("prompt_sha256: message.prompt_sha256", local)
        self.assertIn('"cap_expected_head"', self.policy)
        self.assertIn('"cap_prompt_sha256"', self.policy)
        self.assertIn("promptDigest !== intent.promptSha256", self.content)

    def test_content_can_click_send_only_after_both_authorities(self) -> None:
        self.assertEqual(1, self.content.count("button.click();"))
        click = self.content.index("button.click();")
        gate = self.content.rfind("if (sendAuthorized && !sendClickedAt)", 0, click)
        self.assertGreaterEqual(gate, 0)
        request = self.content.index('sendMessage("authorize-send"')
        self.assertLess(request, gate)
        self.assertIn("if (response.send_authorized === true)", self.content[:gate])

    def test_temporary_mode_never_implies_non_personalized_state(self) -> None:
        observe = self.content[
            self.content.index("function observeTemporaryState") :
            self.content.index("function userDeliveryVisible")
        ]
        request = self.content[
            self.content.index("async function requestAuthority") :
            self.content.index("async function bindRecoveryConversation")
        ]
        self.assertIn("policy.personalizationModeFromText(text)", observe)
        self.assertIn('personalizationState === "non-personalized"', observe)
        self.assertNotIn("personalization_disabled: temporaryMode", observe)
        self.assertIn("temporary.personalization_disabled !== true", request)
        self.assertLess(
            request.index("temporary.personalization_disabled !== true"),
            request.index('sendMessage("authorize-send"'),
        )

    def test_post_delivery_guard_requires_head_prompt_clean_window_and_cleanup_token(self) -> None:
        for phrase in (
            '"cap_expected_head"',
            '"cap_prompt_sha256"',
            "expectedHead",
            "promptSha256",
            "POST_DELIVERY_UI_STABLE_MS = 8000",
            "resetPostDeliveryStability()",
            "postDeliveryCleanupToken = null",
            "response.cleanup_token",
            "captureAuthorization()",
            "currentPostDeliveryUiClean()",
            "invalidatePostDeliveryAuthorization()",
        ):
            self.assertIn(phrase, self.policy)
        self.assertIn("policy.armPostDeliveryUiGuard(intent)", self.content)
        self.assertIn("policy.invalidatePostDeliveryAuthorization()", self.content)

    def test_capture_is_two_phase_and_rechecks_ui_after_async_attestation(self) -> None:
        capture = self.content[
            self.content.index("async function captureResult") :
            self.content.index("async function pollControllerStatus")
        ]
        first = capture.index("policy.captureAuthorization()")
        prepare = capture.index('sendMessage("prepare-capture"')
        second = capture.index("policy.captureAuthorization()", first + 1)
        commit = capture.index('sendMessage("capture"')
        self.assertLess(first, prepare)
        self.assertLess(prepare, second)
        self.assertLess(second, commit)
        self.assertIn("capture_token: prepared.capture_token", capture)

    def test_timeout_final_observation_is_polled_from_delivered_worker(self) -> None:
        self.assertIn("final_observation_request_id", self.content)
        self.assertIn('sendMessage("final-observation"', self.content)
        self.assertIn("terminal_result_visible: policy.singleResultBlockShape(last)", self.content)
        self.assertIn("worker_generating: stopButtonPresent()", self.content)
        final = self.background[
            self.background.index('message.kind === "final-observation"') :
            self.background.index('message.kind === "status"')
        ]
        self.assertIn("runtimeAttestation()", final)

    def test_delivery_ambiguity_never_triggers_resend(self) -> None:
        self.assertEqual(1, self.content.count("button.click();"))
        self.assertIn('postDelivery("unknown"', self.content)
        self.assertIn('postDelivery("delivered"', self.content)

    def test_result_capture_requires_exact_single_structured_block(self) -> None:
        for phrase in (
            'const RESULT_BEGIN = "CAP_WORKER_RESULT_V1_BEGIN"',
            'const RESULT_END = "CAP_WORKER_RESULT_V1_END"',
            "beginCount !== 1 || endCount !== 1",
            "return !before && !after",
        ):
            self.assertIn(phrase, self.policy)
        self.assertIn("if (!policy.hasSingleResultBlock(last)) return;", self.content)

    def test_legacy_fragment_value_is_only_live_handle_and_private_run_id_is_not_persisted_in_browser_claim(self) -> None:
        self.assertIn("new URLSearchParams(url.hash", self.policy)
        self.assertIn('fragmentParams.get("cap_run_id")', self.policy)
        self.assertIn('url.searchParams.has("cap_run_id")', self.policy)
        self.assertIn('reason: "private-run-id-in-query"', self.policy)
        self.assertIn("const launchHandle = message.run_id", self.background)
        self.assertIn("const live = LIVE_LAUNCHES.get(launchHandle)", self.background)
        self.assertIn("run_id: live.run_id", self.background)
        claim = self.background[
            self.background.index("async function claimBrowserSend") :
            self.background.index("async function claimRecordByDelivery")
        ]
        self.assertNotIn("run_id:", claim)
        self.assertIn('"X-CAP-Agent-Token": message.run_id', self.background)

    def test_javascript_syntax_when_node_is_available(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is unavailable")
        for path in (
            EXTENSION / "execution_generation.js",
            EXTENSION / "policy.js",
            EXTENSION / "background.js",
            EXTENSION / "content.js",
        ):
            completed = subprocess.run(
                [node, "--check", str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
