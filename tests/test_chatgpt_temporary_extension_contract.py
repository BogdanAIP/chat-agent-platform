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
        claim_start = self.background.index("async function claimBrowserSend")
        claim_end = self.background.index("async function claimRecordsForTab", claim_start)
        claim_body = self.background[claim_start:claim_end]
        self.assertIn('db.transaction(CLAIM_STORE, "readwrite")', claim_body)
        self.assertIn("store.add(", claim_body)
        self.assertIn("delegation_id: message.delegation_id", claim_body)
        self.assertIn("task_sha256: message.task_sha256", claim_body)
        self.assertIn("tab_id: tabId", claim_body)
        self.assertNotIn("createObjectStore", claim_body)
        self.assertNotIn("store.put(", claim_body)
        self.assertNotIn("delete(", claim_body)

    def test_browser_claim_commits_before_local_delivery_authority(self) -> None:
        authorize = self.background[
            self.background.index("async function authorizeSend") : self.background.index("chrome.runtime.onInstalled")
        ]
        claim = authorize.index("await claimBrowserSend")
        local = authorize.index('controllerPost(message, "/authorize-send"')
        self.assertLess(claim, local)
        self.assertIn("browser_claim_committed: true", authorize)
        self.assertIn("browser_claim_id: message.delivery_id", authorize)
        self.assertIn("send_authorized: false", authorize)

    def test_existing_browser_claim_is_monitor_only_and_never_regranted(self) -> None:
        authorize = self.background[
            self.background.index("async function authorizeSend") : self.background.index("chrome.runtime.onInstalled")
        ]
        self.assertIn('reason: "already-claimed"', self.background)
        self.assertIn("if (!browserClaim.granted)", authorize)
        self.assertIn("monitor_only: monitorOnly", authorize)
        self.assertNotIn("store.delete", self.background)
        self.assertNotIn("store.put", self.background)

    def test_full_tab_reload_recovers_only_one_live_claim_as_monitor_only(self) -> None:
        self.assertIn("async function claimRecordsForTab(tabId)", self.background)
        self.assertIn("async function resumeIntent(sender)", self.background)
        self.assertIn('message.kind === "resume-intent"', self.background)
        resume = self.background[
            self.background.index("async function resumeIntent") : self.background.index("async function authorizeSend")
        ]
        self.assertIn("active.length !== 1", resume)
        self.assertIn('monitor_only: true', resume)
        self.assertIn('["claimed", "unknown", "delivered"]', resume)
        self.assertIn('status.result_state !== "open"', resume)
        self.assertIn('kind: "resume-intent"', self.content)
        self.assertIn("start(recoveredIntent(response), true)", self.content)
        recovered = self.content[self.content.index("function recoveredIntent") : self.content.index("function start")]
        self.assertNotIn("sendAuthorized: true", recovered)

    def test_content_can_click_send_only_after_both_authorities(self) -> None:
        self.assertEqual(1, self.content.count("button.click();"))
        click = self.content.index("button.click();")
        gate = self.content.rfind("if (sendAuthorized && !sendClickedAt)", 0, click)
        self.assertGreaterEqual(gate, 0)
        request = self.content.index('sendMessage("authorize-send"')
        self.assertLess(request, gate)
        self.assertIn("if (response.send_authorized === true)", self.content[:gate])
        self.assertIn("monitorOnly = recovered", self.content)

    def test_delivery_ambiguity_never_triggers_resend(self) -> None:
        self.assertIn('postDelivery(\n          "unknown"', self.content)
        self.assertIn('postDelivery(\n          "delivered"', self.content)
        self.assertEqual(1, self.content.count("button.click();"))
        ambiguity_path = self.content[self.content.index('postDelivery(\n          "unknown"') :]
        self.assertNotIn("sendAuthorized = true", ambiguity_path)

    def test_result_capture_requires_exact_single_structured_block(self) -> None:
        for phrase in (
            'const RESULT_BEGIN = "CAP_WORKER_RESULT_V1_BEGIN"',
            'const RESULT_END = "CAP_WORKER_RESULT_V1_END"',
            "beginCount !== 1 || endCount !== 1",
            "return !before && !after",
        ):
            self.assertIn(phrase, self.policy)
        self.assertIn("if (!policy.hasSingleResultBlock(last)) return;", self.content)
        self.assertIn('sendMessage("capture", { result_text: text })', self.content)

    def test_private_run_id_is_fragment_capability_not_query_or_worker_prompt(self) -> None:
        self.assertIn("new URLSearchParams(url.hash", self.policy)
        self.assertIn('fragmentParams.get("cap_run_id")', self.policy)
        self.assertIn('url.searchParams.has("cap_run_id")', self.policy)
        self.assertIn('reason: "private-run-id-in-query"', self.policy)
        self.assertIn('prompt.includes(runId)', self.policy)
        self.assertIn('reason: "private-run-id-leaked-to-prompt"', self.policy)
        self.assertIn('"X-CAP-Agent-Token": message.run_id', self.background)

    def test_javascript_syntax_when_node_is_available(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is unavailable")
        for path in (EXTENSION / "policy.js", EXTENSION / "background.js", EXTENSION / "content.js"):
            completed = subprocess.run(
                [node, "--check", str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
