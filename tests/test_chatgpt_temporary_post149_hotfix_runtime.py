from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
BACKGROUND = EXTENSION / "background.js"
POLICY = EXTENSION / "policy.js"
CONTENT = EXTENSION / "content.js"


class ChatGPTTemporaryPost149HotfixRuntimeTests(unittest.TestCase):
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

    def test_initial_send_claim_is_bound_to_live_preflight_owner_tab(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const generation = "9".repeat(64);
const launchHandle = "1".repeat(64);
const privateRun = "2".repeat(64);
const delegationId = "3".repeat(64);
const deliveryId = "4".repeat(64);
const taskSha = "5".repeat(64);
const head = "6".repeat(40);
const promptSha = "7".repeat(64);
const context = {{
  console, URL, URLSearchParams,
  generation, launchHandle, privateRun, delegationId, deliveryId, taskSha, head, promptSha,
  claimCalls: 0, localCalls: 0,
  importScripts() {{}},
  CAPChatGPTTemporaryExecutionGeneration: generation,
  chrome: {{runtime: {{
    onInstalled: {{addListener() {{}}}},
    onStartup: {{addListener() {{}}}},
    onMessage: {{addListener() {{}}}},
  }}}},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{filename: "background.js"}});
vm.runInContext(`
  LIVE_LAUNCHES.set(launchHandle, {{
    run_id: privateRun,
    delegation_id: delegationId,
    delivery_id: deliveryId,
    task_sha256: taskSha,
    expected_runtime_head: head,
    prompt_sha256: promptSha,
    launch_url: "https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=" + launchHandle,
    owner_tab_id: 17,
    preflight_id: "8".repeat(64),
    commit_state: "committed",
  }});
  claimBrowserSend = async (_message, _tabId) => {{
    claimCalls += 1;
    return {{granted: true, reason: "committed"}};
  }};
  requestLocalSendAuthority = async (_message, _tabId) => {{
    localCalls += 1;
    return {{send_authorized: true, delivery_state: "claimed", status: "send-authorized"}};
  }};
`, context);
context.raw = {{
  schema_version: 1,
  execution_generation: generation,
  run_id: launchHandle,
  delegation_id: delegationId,
  delivery_id: deliveryId,
  task_sha256: taskSha,
  expected_runtime_head: head,
  prompt_sha256: promptSha,
}};
context.nonOwner = {{url: "https://chatgpt.com/", tab: {{id: 18}}}};
context.owner = {{url: "https://chatgpt.com/", tab: {{id: 17}}}};
(async () => {{
  const resolved = vm.runInContext("resolveLiveMessage(raw)", context);
  if (!resolved || resolved.launch_handle !== launchHandle || resolved.run_id !== privateRun) process.exit(10);
  if (resolved.owner_tab_id !== 17) process.exit(11);

  context.resolved = resolved;
  const rejected = await vm.runInContext("authorizeSend(resolved, nonOwner)", context);
  if (rejected.send_authorized !== false || rejected.reason !== "browser-launch-owned-by-other-tab") process.exit(12);
  if (context.claimCalls !== 0 || context.localCalls !== 0) process.exit(13);

  const accepted = await vm.runInContext("authorizeSend(resolved, owner)", context);
  if (accepted.send_authorized !== true) process.exit(14);
  if (context.claimCalls !== 1 || context.localCalls !== 1) process.exit(15);
}})().catch((error) => {{ console.error(error); process.exit(20); }});
"""
        self.run_node(script)

    def test_hidden_stop_button_does_not_block_stable_result_capture_but_visible_stop_does(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(POLICY))}, "utf8");
let now = 1000;
let intervalCallback = null;
const taskSha = "c".repeat(64);
const delegationId = "a".repeat(64);
const deliveryId = "b".repeat(64);
const runId = "d".repeat(64);
const promptSha = "e".repeat(64);
const expectedHead = "f".repeat(40);
const userText = [
  "WORKER_TASK_V1",
  `delegation_id=${{delegationId}}`,
  `delivery_id=${{deliveryId}}`,
  `task_sha256=${{taskSha}}`,
  `TASK_BEGIN:${{taskSha}}`,
  "bounded task",
  `TASK_END:${{taskSha}}`,
].join("\\n");
const assistantText = "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END";
function rect() {{ return {{width: 500, height: 80}}; }}
function style() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }}
const form = {{nodeType: 1, tagName: "FORM", isConnected: true, parentElement: null,
  hidden: false, inert: false, getBoundingClientRect: rect,
  getAttribute() {{ return null; }}, matches() {{ return false; }}}};
const editor = {{nodeType: 1, tagName: "DIV", isConnected: true, parentElement: form,
  hidden: false, inert: false, isContentEditable: true, innerText: "", textContent: "",
  getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "contenteditable" ? "true" : null; }},
  closest(selector) {{ return selector === "form" ? form : null; }}, matches() {{ return false; }}}};
const userNode = {{nodeType: 1, isConnected: true, parentElement: null, hidden: false, inert: false,
  innerText: userText, textContent: userText, getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "data-message-author-role" ? "user" : null; }},
  matches(selector) {{ return selector.includes('data-message-author-role="user"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }}, querySelector() {{ return null; }}}};
const assistantNode = {{nodeType: 1, isConnected: true, parentElement: null, hidden: false, inert: false,
  innerText: assistantText, textContent: assistantText, getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "data-message-author-role" ? "assistant" : null; }},
  matches(selector) {{ return selector.includes('data-message-author-role="assistant"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }}, querySelector() {{ return null; }}}};
const stop = {{nodeType: 1, tagName: "BUTTON", isConnected: true, parentElement: null,
  hidden: true, inert: false, textContent: "Stop", getBoundingClientRect: rect,
  getAttribute(name) {{
    if (name === "data-testid") return "stop-button";
    if (name === "aria-label") return "Stop";
    return null;
  }}, matches() {{ return false; }}, closest(selector) {{ return selector === "button" ? this : null; }}}};
const root = {{nodeType: 1, isConnected: true, parentElement: null, hidden: false, inert: false,
  getBoundingClientRect: rect, getAttribute() {{ return null; }}, matches() {{ return false; }},
  closest() {{ return null; }}, querySelector() {{ return null; }}, querySelectorAll() {{ return []; }}}};
class FakeMutationObserver {{
  constructor(callback) {{ this.callback = callback; this.pending = []; }}
  observe() {{}}
  takeRecords() {{ const value = this.pending; this.pending = []; return value; }}
}}
const context = {{
  console, URL, URLSearchParams,
  Date: class extends Date {{ static now() {{ return now; }} }},
  MutationObserver: FakeMutationObserver,
  setInterval(callback) {{ intervalCallback = callback; return 1; }}, clearInterval() {{}},
  getComputedStyle: style,
  location: {{href: "https://chatgpt.com/c/post149-hotfix", origin: "https://chatgpt.com"}},
  history: {{state: null, replaceState() {{}}}},
  document: {{
    documentElement: root,
    querySelector(selector) {{
      if (selector === "#prompt-textarea") return editor;
      if (selector === 'button[data-testid="stop-button"]') return stop;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector === '#prompt-textarea,[contenteditable="true"],textarea') return [editor];
      if (selector.includes('data-message-author-role="user"')) return [userNode];
      if (selector.includes('data-message-author-role="assistant"')) return [assistantNode];
      if (selector === "button") return [stop];
      return [];
    }},
  }},
  chrome: {{runtime: {{sendMessage(message, callback) {{
    if (message.kind === "event" && message.event === "delivery-visible") {{
      callback({{ok: true, cleanup_token: "9".repeat(64)}}); return;
    }}
    callback({{ok: true}});
  }}}}}},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{filename: "policy.js"}});
const policy = context.CAPChatGPTTemporaryPolicy;
const intent = {{runId, delegationId, deliveryId, taskSha256: taskSha, expectedHead, promptSha256: promptSha}};
if (policy.armPostDeliveryUiGuard(intent) !== true) process.exit(30);
intervalCallback();
now += 8001;
intervalCallback();
const authorization = policy.captureAuthorization();
if (!authorization) process.exit(31);
stop.hidden = false;
if (policy.captureAuthorization() !== null) process.exit(32);
"""
        self.run_node(script)

    def test_content_final_observation_ignores_hidden_stop_and_reports_visible_stop(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const generation = "9".repeat(64);
const runId = "1".repeat(64);
const delegationId = "2".repeat(64);
const deliveryId = "3".repeat(64);
const taskSha = "4".repeat(64);
const head = "5".repeat(40);
const promptSha = "6".repeat(64);
const requestId = "7".repeat(64);
function rect() {{ return {{width: 400, height: 80}}; }}
function visibleStyle() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }}
async function runCase(hidden) {{
  const observations = [];
  const assistant = {{
    isConnected: true, parentElement: null, hidden: false, inert: false,
    innerText: "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END",
    textContent: "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END",
    getBoundingClientRect: rect,
    getAttribute(name) {{ return name === "data-message-author-role" ? "assistant" : null; }},
  }};
  const stop = {{
    isConnected: true, parentElement: null, hidden, inert: false, textContent: "Stop",
    getBoundingClientRect: rect,
    getAttribute(name) {{
      if (name === "data-testid") return "stop-button";
      if (name === "aria-label") return "Stop";
      return null;
    }},
  }};
  const policy = {{
    HEX64_RE: /^[0-9a-f]{{64}}$/,
    HEAD40_RE: /^[0-9a-f]{{40}}$/,
    parseIntent() {{ return {{enabled: false}}; }},
    conversationId() {{ return "post149conv"; }},
    armPostDeliveryUiGuard() {{ return true; }},
    singleResultBlockShape() {{ return true; }},
    hasSingleResultBlock() {{ return false; }},
    captureAuthorization() {{ return null; }},
    invalidatePostDeliveryAuthorization() {{}},
    findComposerEditor() {{ return null; }},
    exactPromptMatches() {{ return false; }},
    hasExpectedPrompt() {{ return false; }},
    personalizationModeFromText() {{ return "unknown"; }},
  }};
  const context = {{
    console, URL, URLSearchParams, TextEncoder,
    CAPChatGPTTemporaryPolicy: policy,
    CAPChatGPTTemporaryExecutionGeneration: generation,
    location: {{href: "https://chatgpt.com/c/post149conv", origin: "https://chatgpt.com"}},
    history: {{state: null, replaceState() {{}}}},
    getComputedStyle: visibleStyle,
    setInterval() {{ return 1; }}, clearInterval() {{}},
    document: {{
      querySelector(selector) {{
        if (selector === 'button[data-testid="stop-button"]') return stop;
        return null;
      }},
      querySelectorAll(selector) {{
        if (selector === '[data-message-author-role="user"]') return [];
        if (selector === '[data-message-author-role="assistant"]') return [assistant];
        if (selector === '[data-message-author-role="user"],[data-message-author-role="assistant"]') return [assistant];
        if (selector === "button") return [stop];
        return [];
      }},
    }},
    chrome: {{runtime: {{lastError: null, sendMessage(message, callback) {{
      if (message.kind === "resume-intent") {{
        callback({{
          ok: true, enabled: true, monitor_only: true,
          execution_generation: generation,
          run_id: runId, delegation_id: delegationId, delivery_id: deliveryId,
          task_sha256: taskSha, expected_runtime_head: head, prompt_sha256: promptSha,
          conversation_id: "post149conv", delivery_state: "delivered",
        }});
        return;
      }}
      if (message.kind === "status") {{
        callback({{
          ok: true, delegation_id: delegationId, delivery_id: deliveryId,
          result_state: "open", delivery_state: "delivered",
          final_observation_request_id: requestId,
        }});
        return;
      }}
      if (message.kind === "final-observation") {{
        observations.push(message.worker_generating);
        callback({{ok: true}});
        return;
      }}
      callback({{ok: true}});
    }}}}}},
  }};
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(source, context, {{filename: "content.js"}});
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
  if (observations.length !== 1) throw new Error("final-observation-count:" + observations.length);
  return observations[0];
}}
(async () => {{
  if (await runCase(true)) process.exit(40);
  if (!(await runCase(false))) process.exit(41);
}})().catch((error) => {{ console.error(error); process.exit(42); }});
"""
        self.run_node(script)


if __name__ == "__main__":
    unittest.main()
