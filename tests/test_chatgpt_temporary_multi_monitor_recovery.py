from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest

from runtime.agent_sessions.chatgpt_temporary_controller import TemporaryControllerState
from tests.test_chatgpt_temporary_controller import (
    TASK,
    TASK_SHA,
    authority_request,
    expected_runtime_attestation,
    identity_dict,
    runtime_report,
)


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "background.js"
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


def delivery_request(state: TemporaryControllerState) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": state.launch.run_id,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "task_sha256": TASK_SHA,
        "outcome": "delivered",
        "evidence_ref": "chatgpt-temporary:delivery:visible:multi-monitor",
    }


def cleanup_event(state: TemporaryControllerState) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": state.launch.run_id,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "event": "delivery-visible",
        "details": {
            "post_delivery_ui_disarmed": True,
            "launch_url_clean": True,
            "composer_clean": True,
        },
    }


def prepare_request(state: TemporaryControllerState, cleanup_token: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": state.launch.run_id,
        "delegation_id": state.launch.delegation_id,
        "delivery_id": state.launch.delivery_id,
        "cleanup_token": cleanup_token,
        "runtime_attestation": runtime_report(),
    }


class MultiMonitorControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.state_root = root / "private-state"
        self.output_root = root / "output"
        self.state = TemporaryControllerState(
            identity_value=identity_dict(),
            task=TASK,
            expected_runtime_attestation_value=expected_runtime_attestation(),
            state_root=self.state_root,
            output_dir=self.output_root,
        )
        authorized = self.state.authorize_send(authority_request(self.state))
        self.assertTrue(authorized["send_authorized"])
        self.state.record_delivery(delivery_request(self.state))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_later_cleanup_acknowledgement_cannot_replace_an_earlier_monitor_token(self) -> None:
        first = self.state.record_event(cleanup_event(self.state))["cleanup_token"]
        second = self.state.record_event(cleanup_event(self.state))["cleanup_token"]
        self.assertIsInstance(first, str)
        self.assertIsInstance(second, str)
        self.assertEqual(first, second)
        self.assertEqual(first, self.state.cleanup_token)

    def test_later_capture_preparation_cannot_replace_an_unconsumed_monitor_token(self) -> None:
        cleanup = self.state.record_event(cleanup_event(self.state))["cleanup_token"]
        self.assertIsInstance(cleanup, str)
        first = self.state.prepare_capture(
            prepare_request(self.state, str(cleanup))
        )["capture_token"]
        second = self.state.prepare_capture(
            prepare_request(self.state, str(cleanup))
        )["capture_token"]
        self.assertIsInstance(first, str)
        self.assertIsInstance(second, str)
        self.assertEqual(first, second)
        self.assertEqual(first, self.state.capture_token)


class BrowserEphemeralRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def run_node(self, script: str) -> None:
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_resume_intent_never_discloses_private_run_capability(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const generation = "9".repeat(64);
let onMessageHandler = null;

const context = {{
  console,
  URL,
  importScripts() {{}},
  CAPChatGPTTemporaryExecutionGeneration: generation,
  chrome: {{
    runtime: {{
      onInstalled: {{ addListener() {{}} }},
      onStartup: {{ addListener() {{}} }},
      onMessage: {{ addListener(fn) {{ onMessageHandler = fn; }} }},
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{ filename: "background.js" }});
if (typeof onMessageHandler !== "function") process.exit(10);
let response = null;
const returned = onMessageHandler(
  {{ schema_version: 1, kind: "resume-intent", execution_generation: generation }},
  {{ url: "https://chatgpt.com/c/foreign-session-1234", tab: {{ id: 91, url: "https://chatgpt.com/c/foreign-session-1234" }} }},
  (value) => {{ response = value; }},
);
if (returned !== false) process.exit(11);
if (!response || response.enabled !== false) process.exit(12);
if (response.reason !== "temporary-profile-ephemeral") process.exit(13);
if (Object.prototype.hasOwnProperty.call(response, "run_id")) process.exit(14);
"""
        self.run_node(script)

    def test_post_send_existing_claim_never_becomes_monitor_only(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const generation = "9".repeat(64);
const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const head = "e".repeat(40);
const promptSha = "f".repeat(64);
const ownerTab = 17;

const context = {{
  console,
  URL,
  importScripts() {{}},
  CAPChatGPTTemporaryExecutionGeneration: generation,
  chrome: {{
    runtime: {{
      onInstalled: {{ addListener() {{}} }},
      onStartup: {{ addListener() {{}} }},
      onMessage: {{ addListener() {{}} }},
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{ filename: "background.js" }});

context.message = {{
  schema_version: 1,
  kind: "authorize-send",
  execution_generation: generation,
  run_id: runId,
  delegation_id: delegationId,
  delivery_id: deliveryId,
  task_sha256: taskSha,
  expected_runtime_head: head,
  prompt_sha256: promptSha,
}};
context.record = {{
  schema_version: 1,
  run_id: runId,
  delegation_id: delegationId,
  delivery_id: deliveryId,
  task_sha256: taskSha,
  expected_runtime_head: head,
  prompt_sha256: promptSha,
  claim_tab_id: ownerTab,
  claimed_at: new Date().toISOString(),
}};
context.sender = {{ url: "https://chatgpt.com/", tab: {{ id: ownerTab, url: "https://chatgpt.com/" }} }};
context.delegationId = delegationId;
context.deliveryId = deliveryId;

vm.runInContext(`
  claimBrowserSend = async () => ({{ granted: false, reason: "already-claimed" }});
  claimRecordByDelivery = async () => record;
  controllerStatus = async () => ({{
    delegation_id: delegationId,
    delivery_id: deliveryId,
    launch_state: "child-bound",
    delivery_state: "delivered",
    result_state: "open",
  }});
`, context);

(async () => {{
  const response = await vm.runInContext("authorizeSend(message, sender)", context);
  if (response.send_authorized !== false) process.exit(20);
  if (response.monitor_only !== false) process.exit(21);
  if (response.reason !== "temporary-profile-ephemeral") process.exit(22);
}})().catch((error) => {{ console.error(error); process.exit(30); }});
"""
        self.run_node(script)

    def test_provider_conversation_recovery_implementation_is_absent(self) -> None:
        background = BACKGROUND.read_text(encoding="utf-8")
        self.assertNotIn("async function resumeIntent", background)
        self.assertNotIn("async function bindRecoveryConversation", background)
        self.assertNotIn("async function bindClaimConversationRecord", background)
        self.assertNotIn("conversation_id: null", background)
        self.assertIn('kind === "resume-intent"', background)
        self.assertIn('reason: "temporary-profile-ephemeral"', background)


class CleanupAuthorizationRearmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_invalidated_cleanup_authority_requires_a_new_full_clean_window(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const expectedHead = "e".repeat(40);
const promptSha = "f".repeat(64);
let tokenCounter = 0;
let now = 1000;
let intervalFn = null;
let href = "https://chatgpt.com/c/rearm-session-1234";
const editor = {{ textContent: "", innerText: "" }};
const userTurn = {{
  innerText: `delegation_id=${{delegationId}}\\ndelivery_id=${{deliveryId}}\\ntask_sha256=${{taskSha}}`,
  textContent: "",
}};

global.location = {{ get href() {{ return href; }} }};
global.history = {{ state: null, replaceState(_state, _title, next) {{ href = new URL(next, href).toString(); }} }};
global.document = {{
  querySelector(selector) {{ return selector === "#prompt-textarea" ? editor : null; }},
  querySelectorAll(selector) {{ return selector.includes('data-message-author-role="user"') ? [userTurn] : []; }},
}};
global.CAPChatGPTTemporaryExecutionGeneration = "2".repeat(64);
global.chrome = {{ runtime: {{ sendMessage(_message, callback) {{ tokenCounter += 1; callback({{ ok: true, cleanup_token: String(tokenCounter).repeat(64) }}); }} }} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};
Date.now = () => now;

vm.runInThisContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), {{ filename: "policy.js" }});
const intent = {{ runId, delegationId, deliveryId, taskSha256: taskSha, expectedHead, promptSha256: promptSha }};
if (!CAPChatGPTTemporaryPolicy.armPostDeliveryUiGuard(intent)) process.exit(30);
intervalFn();
now = 9001;
intervalFn();
const first = CAPChatGPTTemporaryPolicy.captureAuthorization();
if (!first || first.cleanupToken !== "1".repeat(64)) process.exit(31);
if (!CAPChatGPTTemporaryPolicy.invalidatePostDeliveryAuthorization()) process.exit(32);
if (CAPChatGPTTemporaryPolicy.captureAuthorization() !== null) process.exit(33);
now = 9500;
intervalFn();
if (CAPChatGPTTemporaryPolicy.captureAuthorization() !== null) process.exit(34);
now = 17501;
intervalFn();
const second = CAPChatGPTTemporaryPolicy.captureAuthorization();
if (!second || second.cleanupToken !== "2".repeat(64)) process.exit(35);
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_content_rearms_only_for_stale_server_capture_authority(self) -> None:
        content = CONTENT.read_text(encoding="utf-8")
        self.assertIn("function staleCaptureAuthority", content)
        self.assertIn("worker capture cleanup token is stale or missing", content)
        self.assertIn("worker capture preparation token is stale or missing", content)
        self.assertIn("policy.invalidatePostDeliveryAuthorization()", content)


if __name__ == "__main__":
    unittest.main()
