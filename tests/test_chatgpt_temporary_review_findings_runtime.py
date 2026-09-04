from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "background.js"
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class FreshReviewFindingRuntimeTests(unittest.TestCase):
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

    def test_losing_tab_cannot_recover_pre_send_local_authority(self) -> None:
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
const loserTab = 18;

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
  conversation_id: null,
  claimed_at: new Date().toISOString(),
}};
context.ownerSender = {{ url: "https://chatgpt.com/", tab: {{ id: ownerTab, url: "https://chatgpt.com/" }} }};
context.loserSender = {{ url: "https://chatgpt.com/", tab: {{ id: loserTab, url: "https://chatgpt.com/" }} }};
context.authorityCalls = [];
context.delegationId = delegationId;
context.deliveryId = deliveryId;

vm.runInContext(`
  claimBrowserSend = async () => ({{ granted: false, reason: "already-claimed" }});
  claimRecordByDelivery = async () => record;
  controllerStatus = async () => ({{
    delegation_id: delegationId,
    delivery_id: deliveryId,
    launch_state: "launch-attempted",
    delivery_state: "prepared",
    result_state: "open",
  }});
  requestLocalSendAuthority = async (_message, tabId) => {{
    authorityCalls.push(tabId);
    return {{ send_authorized: true, delivery_state: "claimed", status: "authorized" }};
  }};
  LIVE_PRE_SEND_CLAIMS.add(message.delivery_id);
`, context);

(async () => {{
  const loser = await vm.runInContext("authorizeSend(message, loserSender)", context);
  if (loser.send_authorized !== false || loser.monitor_only !== false) process.exit(10);
  if (loser.reason !== "browser-claim-owned-by-other-tab") process.exit(11);
  if (context.authorityCalls.length !== 0) process.exit(12);

  const owner = await vm.runInContext("authorizeSend(message, ownerSender)", context);
  if (owner.send_authorized !== true || owner.reason !== "recovered-local-authority") process.exit(13);
  if (context.authorityCalls.length !== 1 || context.authorityCalls[0] !== ownerTab) process.exit(14);
}})().catch((error) => {{ console.error(error); process.exit(20); }});
"""
        self.run_node(script)

    def test_reused_owner_tab_id_after_background_restart_cannot_recover_pre_send_authority(self) -> None:
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
const reusedOwnerTab = 17;

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
  claim_tab_id: reusedOwnerTab,
  conversation_id: null,
  claimed_at: new Date().toISOString(),
}};
context.reusedSender = {{ url: "https://chatgpt.com/", tab: {{ id: reusedOwnerTab, url: "https://chatgpt.com/" }} }};
context.authorityCalls = [];
context.delegationId = delegationId;
context.deliveryId = deliveryId;

vm.runInContext(`
  claimBrowserSend = async () => ({{ granted: false, reason: "already-claimed" }});
  claimRecordByDelivery = async () => record;
  controllerStatus = async () => ({{
    delegation_id: delegationId,
    delivery_id: deliveryId,
    launch_state: "launch-attempted",
    delivery_state: "prepared",
    result_state: "open",
  }});
  requestLocalSendAuthority = async (_message, tabId) => {{
    authorityCalls.push(tabId);
    return {{ send_authorized: true, delivery_state: "claimed", status: "authorized" }};
  }};
`, context);

(async () => {{
  // A fresh service-worker context intentionally has no LIVE_PRE_SEND_CLAIMS
  // entry even if Chromium reuses the old numeric tab id after restart.
  const reused = await vm.runInContext("authorizeSend(message, reusedSender)", context);
  if (reused.send_authorized !== false || reused.monitor_only !== false) process.exit(21);
  if (reused.reason !== "browser-claim-owner-context-expired") process.exit(22);
  if (context.authorityCalls.length !== 0) process.exit(23);
}})().catch((error) => {{ console.error(error); process.exit(30); }});
"""
        self.run_node(script)

    def test_delivery_ack_loss_retries_the_same_evidence_reference(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const generation = "9".repeat(64);
const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const head = "e".repeat(40);
const promptSha = "f".repeat(64);
const conversationId = "delivery-retry-session-1234";
let now = 1000;
let intervalFn = null;
const evidenceRefs = [];
const userTurn = {{
  innerText: `delegation_id=${{delegationId}}\\ndelivery_id=${{deliveryId}}\\ntask_sha256=${{taskSha}}`,
  textContent: "",
}};

const policy = {{
  HEX64_RE: /^[0-9a-f]{{64}}$/,
  HEAD40_RE: /^[0-9a-f]{{40}}$/,
  parseIntent() {{ return {{ enabled: false }}; }},
  conversationId() {{ return conversationId; }},
  armPostDeliveryUiGuard() {{ return true; }},
  invalidatePostDeliveryAuthorization() {{}},
  hasExpectedPrompt() {{ return false; }},
  personalizationModeFromText() {{ return "unknown"; }},
  captureAuthorization() {{ return null; }},
  singleResultBlockShape() {{ return false; }},
  hasSingleResultBlock() {{ return false; }},
}};

global.CAPChatGPTTemporaryPolicy = policy;
global.CAPChatGPTTemporaryExecutionGeneration = generation;
global.location = {{ href: `https://chatgpt.com/c/${{conversationId}}`, origin: "https://chatgpt.com" }};
global.history = {{ state: null, replaceState() {{}} }};
global.document = {{
  querySelector() {{ return null; }},
  querySelectorAll(selector) {{
    if (selector.includes('data-message-author-role="user"')) return [userTurn];
    return [];
  }},
}};
global.chrome = {{ runtime: {{
  lastError: null,
  sendMessage(message, callback) {{
    if (message.kind === "resume-intent") {{
      callback({{
        ok: true,
        enabled: true,
        monitor_only: true,
        execution_generation: generation,
        run_id: runId,
        delegation_id: delegationId,
        delivery_id: deliveryId,
        task_sha256: taskSha,
        expected_runtime_head: head,
        prompt_sha256: promptSha,
        conversation_id: conversationId,
        delivery_state: "claimed",
        result_state: "open",
      }});
      return;
    }}
    if (message.kind === "status") {{
      callback({{
        ok: true,
        delegation_id: delegationId,
        delivery_id: deliveryId,
        delivery_state: "claimed",
        result_state: "open",
        result_status: null,
        final_observation_request_id: null,
      }});
      return;
    }}
    if (message.kind === "delivery") {{
      evidenceRefs.push(message.evidence_ref);
      if (evidenceRefs.length === 1) callback({{ ok: false, reason: "Failed to fetch" }});
      else callback({{ ok: true, delivery_state: "delivered", result_state: "open" }});
      return;
    }}
    callback({{ ok: true }});
  }},
}} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};
Date.now = () => now;

function flush() {{ return new Promise((resolve) => setImmediate(resolve)); }}

(async () => {{
  vm.runInThisContext(source, {{ filename: "content.js" }});
  await flush();
  await flush();
  if (typeof intervalFn !== "function") process.exit(30);
  if (evidenceRefs.length !== 1) process.exit(31);

  now = 1600;
  intervalFn();
  await flush();
  await flush();
  if (evidenceRefs.length !== 2) process.exit(32);
  if (evidenceRefs[0] !== evidenceRefs[1]) process.exit(33);

  now = 2200;
  intervalFn();
  await flush();
  if (evidenceRefs.length !== 2) process.exit(34);
}})().catch((error) => {{ console.error(error); process.exit(40); }});
"""
        self.run_node(script)

    def test_capture_transport_ack_loss_rearms_and_terminal_status_closes(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const generation = "9".repeat(64);
const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const head = "e".repeat(40);
const promptSha = "f".repeat(64);
const conversationId = "capture-retry-session-1234";
const cleanupToken = "1".repeat(64);
const captureToken = "2".repeat(64);
const resultText = "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END";
let now = 1000;
let intervalFn = null;
let cleared = false;
let captureCalls = 0;
let invalidations = 0;
let durableRecorded = false;
let captureAuthorization = {{ cleanupToken }};
const stoppedEvents = [];
const userTurn = {{
  innerText: `delegation_id=${{delegationId}}\\ndelivery_id=${{deliveryId}}\\ntask_sha256=${{taskSha}}`,
  textContent: "",
}};
const assistantTurn = {{ innerText: resultText, textContent: resultText }};

const policy = {{
  HEX64_RE: /^[0-9a-f]{{64}}$/,
  HEAD40_RE: /^[0-9a-f]{{40}}$/,
  parseIntent() {{ return {{ enabled: false }}; }},
  conversationId() {{ return conversationId; }},
  armPostDeliveryUiGuard() {{ return true; }},
  invalidatePostDeliveryAuthorization() {{ invalidations += 1; captureAuthorization = null; return true; }},
  hasExpectedPrompt() {{ return false; }},
  personalizationModeFromText() {{ return "unknown"; }},
  captureAuthorization() {{ return captureAuthorization; }},
  singleResultBlockShape(text) {{ return text === resultText; }},
  hasSingleResultBlock(text) {{ return text === resultText; }},
}};

global.CAPChatGPTTemporaryPolicy = policy;
global.CAPChatGPTTemporaryExecutionGeneration = generation;
global.location = {{ href: `https://chatgpt.com/c/${{conversationId}}`, origin: "https://chatgpt.com" }};
global.history = {{ state: null, replaceState() {{}} }};
global.document = {{
  querySelector() {{ return null; }},
  querySelectorAll(selector) {{
    if (selector.includes('data-message-author-role="user"') && selector.includes('data-message-author-role="assistant"')) return [userTurn, assistantTurn];
    if (selector.includes('data-message-author-role="user"')) return [userTurn];
    if (selector.includes('data-message-author-role="assistant"')) return [assistantTurn];
    return [];
  }},
}};
global.chrome = {{ runtime: {{
  lastError: null,
  sendMessage(message, callback) {{
    if (message.kind === "resume-intent") {{
      callback({{
        ok: true,
        enabled: true,
        monitor_only: true,
        execution_generation: generation,
        run_id: runId,
        delegation_id: delegationId,
        delivery_id: deliveryId,
        task_sha256: taskSha,
        expected_runtime_head: head,
        prompt_sha256: promptSha,
        conversation_id: conversationId,
        delivery_state: "delivered",
        result_state: "open",
      }});
      return;
    }}
    if (message.kind === "status") {{
      callback({{
        ok: true,
        delegation_id: delegationId,
        delivery_id: deliveryId,
        delivery_state: "delivered",
        result_state: durableRecorded ? "recorded" : "open",
        result_status: durableRecorded ? "COMPLETED" : null,
        final_observation_request_id: null,
      }});
      return;
    }}
    if (message.kind === "prepare-capture") {{
      callback({{ ok: true, capture_token: captureToken }});
      return;
    }}
    if (message.kind === "capture") {{
      captureCalls += 1;
      durableRecorded = true;
      callback({{ ok: false, reason: "Failed to fetch" }});
      return;
    }}
    if (message.kind === "event") {{
      if (message.event === "stopped") stoppedEvents.push(message.details);
      callback({{ ok: true }});
      return;
    }}
    callback({{ ok: true }});
  }},
}} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{ cleared = true; }};
Date.now = () => now;

function flush() {{ return new Promise((resolve) => setImmediate(resolve)); }}

(async () => {{
  vm.runInThisContext(source, {{ filename: "content.js" }});
  await flush();
  await flush();
  if (typeof intervalFn !== "function") process.exit(50);

  now = 4101;
  intervalFn();
  await flush();
  now = 7202;
  intervalFn();
  await flush();
  await flush();

  if (captureCalls !== 1) process.exit(51);
  if (invalidations !== 1) process.exit(52);
  if (cleared) process.exit(53);

  now = 8303;
  intervalFn();
  await flush();
  await flush();
  if (!cleared) process.exit(54);
  if (!stoppedEvents.some((details) => details.reason === "result-recorded" && details.recovered_from_status === true)) process.exit(55);
}})().catch((error) => {{ console.error(error); process.exit(60); }});
"""
        self.run_node(script)


if __name__ == "__main__":
    unittest.main()
