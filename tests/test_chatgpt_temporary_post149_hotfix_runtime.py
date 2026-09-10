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


    def test_temporary_ui_settle_is_bounded_before_send_authority(self) -> None:
        script = r"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const assert = require("assert/strict");

const source = fs.readFileSync(__CONTENT_PATH__, "utf8");

const prompt = "bounded exact prompt";
const promptSha =
  nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");

const digestBytes = Uint8Array.from(
  promptSha.match(/../g).map(value => parseInt(value, 16))
);

function makeNode(tagName, text = "", attrs = {}, parent = null) {
  const n = {
    nodeType: 1,
    tagName: String(tagName).toUpperCase(),
    isConnected: true,
    hidden: false,
    inert: false,
    parentElement: parent,
    textContent: text,
    innerText: text,
    value: "",
    disabled: false,
    childNodes: [],

    getBoundingClientRect() {
      return {x: 0, y: 0, width: 200, height: 40};
    },

    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(attrs, name)
        ? attrs[name]
        : null;
    },

    contains(other) {
      for (let current = other; current; current = current.parentElement) {
        if (current === n) return true;
      }
      return false;
    },

    matches(selector) {
      if (selector === ":disabled") return false;
      if (selector === "form") return n.tagName === "FORM";

      if (selector === 'main,[role="main"]') {
        return n.tagName === "MAIN";
      }

      if (selector.includes("button") && n.tagName === "BUTTON") {
        return true;
      }

      if (selector.includes("dialog") && n.tagName === "DIALOG") {
        return true;
      }

      return false;
    },

    closest(selector) {
      for (let current = n; current; current = current.parentElement) {
        if (current.matches?.(selector)) return current;
      }
      return null;
    },

    querySelectorAll() {
      return [];
    },
  };

  return n;
}


async function runCase({
  temporaryReadyAt,
  personalizationText = "Non-personalized",
}) {
  let now = 1000;
  let intervalFn = null;
  let clicks = 0;
  let authorizeCount = 0;

  const events = [];

  const main = makeNode("main");

  const composer = makeNode(
    "form",
    prompt,
    {},
    main
  );

  const editor = makeNode(
    "textarea",
    "",
    {},
    composer
  );
  editor.value = prompt;

  const send = makeNode(
    "button",
    "Send",
    {
      "data-testid": "send-button",
      "aria-disabled": "false",
    },
    composer
  );

  send.click = () => {
    clicks += 1;
  };

  const personalization = makeNode(
    "button",
    personalizationText,
    {},
    main
  );

  const title = makeNode(
    "h1",
    "Temporary Chat",
    {
      "data-testid": "temporary-chat-label",
    },
    main
  );

  const policyCopy = makeNode(
    "p",
    "This chat will not use memory, plugins, custom instructions, or appear in history.",
    {},
    main
  );

  main.querySelectorAll = selector => {
    const ready =
      temporaryReadyAt !== null &&
      now >= temporaryReadyAt;

    if (!ready) return [];

    if (
      selector ===
      'h1,h2,h3,h4,[role="heading"],div,p,span'
    ) {
      return [title, policyCopy];
    }

    if (selector === "p,div,span") {
      return [policyCopy];
    }

    return [];
  };

  const intent = {
    enabled: true,
    runId: "a".repeat(64),
    delegationId: "b".repeat(64),
    deliveryId: "c".repeat(64),
    taskSha256: "d".repeat(64),
    expectedHead: "e".repeat(40),
    promptSha256: promptSha,
    prompt,
    maxWaitMs: 300000,
    deliveryObserveMs: 20000,
    stableMs: 0,
  };

  const policy = {
    HEX64_RE: /^[0-9a-f]{64}$/,
    HEAD40_RE: /^[0-9a-f]{40}$/,

    parseIntent() {
      return intent;
    },

    findComposerEditor() {
      return editor;
    },

    exactPromptMatches(observed, expected) {
      return observed === expected;
    },

    personalizationModeFromText(text) {
      const value = String(text || "");

      if (/Non-personalized/i.test(value)) {
        return "non-personalized";
      }

      if (/Personalized/i.test(value)) {
        return "personalized";
      }

      return "unknown";
    },

    conversationId() {
      return null;
    },

    armPostDeliveryUiGuard() {
      return true;
    },

    hasExpectedPrompt() {
      return false;
    },

    invalidatePostDeliveryAuthorization() {},
    captureAuthorization() { return null; },
    singleResultBlockShape() { return false; },
    hasSingleResultBlock() { return false; },
  };

  const document = {
    querySelector(selector) {
      if (selector === 'button[data-testid="send-button"]') {
        return send;
      }

      if (selector === 'button[data-testid="stop-button"]') {
        return null;
      }

      return null;
    },

    querySelectorAll(selector) {
      if (selector === 'button[data-testid="send-button"]') {
        return [send];
      }

      if (
        selector ===
        'button,[role="button"],[aria-label],[title],[data-testid]'
      ) {
        return [send, personalization];
      }

      if (
        selector ===
        'dialog,[role="dialog"],[role="menu"],[role="listbox"]'
      ) {
        return [];
      }

      if (
        selector ===
        '[data-message-author-role="user"],[data-message-author-role="assistant"]'
      ) {
        return [];
      }

      if (selector === '[data-message-author-role="user"]') {
        return [];
      }

      if (selector === '[data-message-author-role="assistant"]') {
        return [];
      }

      if (selector === "button") {
        return [send, personalization];
      }

      return [];
    },
  };

  const context = {
    console,
    URL,
    URLSearchParams,
    TextEncoder,

    Date: class extends Date {
      static now() {
        return now;
      }
    },

    crypto: {
      subtle: {
        digest: async () => digestBytes.slice().buffer,
      },
    },

    CAPChatGPTTemporaryPolicy: policy,
    CAPChatGPTTemporaryExecutionGeneration: "9".repeat(64),

    location: {
      href: "https://chatgpt.com/?temporary-chat=true",
      origin: "https://chatgpt.com",
    },

    history: {
      state: null,
      replaceState() {},
    },

    document,

    getComputedStyle() {
      return {
        visibility: "visible",
        display: "block",
        opacity: "1",
      };
    },

    setInterval(fn) {
      intervalFn = fn;
      return 1;
    },

    clearInterval() {},

    chrome: {
      runtime: {
        lastError: null,

        sendMessage(message, callback) {
          if (message.kind === "event") {
            events.push(message);
            callback({ok: true});
            return;
          }

          if (message.kind === "authorize-send") {
            authorizeCount += 1;

            callback({
              ok: true,
              send_authorized: true,
              delivery_state: "claimed",
            });

            return;
          }

          if (message.kind === "status") {
            callback({
              ok: true,
              delegation_id: intent.delegationId,
              delivery_id: intent.deliveryId,
              result_state: "open",
              delivery_state: "claimed",
              result_status: null,
              final_observation_request_id: null,
            });

            return;
          }

          callback({ok: true});
        },
      },
    },
  };

  context.globalThis = context;

  vm.createContext(context);

  vm.runInContext(
    source,
    context,
    {filename: "content.js"}
  );

  const flush = () =>
    new Promise(resolve => setImmediate(resolve));

  async function settle() {
    await flush();
    await flush();
    await flush();
    await flush();
  }

  async function step() {
    now += 500;

    if (typeof intervalFn === "function") {
      intervalFn();
    }

    await settle();
  }

  await settle();

  return {
    async steps(count) {
      for (let i = 0; i < count; i += 1) {
        await step();
      }
    },

    get clicks() {
      return clicks;
    },

    get authorizeCount() {
      return authorizeCount;
    },

    events,
  };
}


(async () => {
  const delayed = await runCase({
    temporaryReadyAt: 3000,
  });

  assert.equal(delayed.authorizeCount, 0);
  assert.equal(delayed.clicks, 0);

  await delayed.steps(3);

  assert.equal(
    delayed.authorizeCount,
    0,
    "Send authority must not exist before Temporary UI proof"
  );

  assert.equal(delayed.clicks, 0);

  await delayed.steps(1);

  assert.equal(
    delayed.authorizeCount,
    1,
    "exactly one Send authority request must occur after Temporary UI proof"
  );

  assert.equal(
    delayed.clicks,
    0,
    "authority acquisition and physical click remain separate observations"
  );

  await delayed.steps(1);

  assert.equal(delayed.authorizeCount, 1);
  assert.equal(delayed.clicks, 1);

  assert.equal(
    delayed.events.some(
      event =>
        event.event === "stopped" &&
        event.details?.reason === "child-qualification-failed"
    ),
    false
  );


  const absent = await runCase({
    temporaryReadyAt: null,
  });

  await absent.steps(21);

  assert.equal(
    absent.authorizeCount,
    0,
    "authority must never be requested without Temporary UI proof"
  );

  assert.equal(absent.clicks, 0);

  assert.ok(
    absent.events.some(
      event =>
        event.event === "stopped" &&
        event.details?.reason === "child-qualification-failed"
    ),
    "Temporary UI that never appears must fail closed after the bounded window"
  );


  const personalized = await runCase({
    temporaryReadyAt: null,
    personalizationText: "Personalized",
  });

  assert.equal(personalized.authorizeCount, 0);
  assert.equal(personalized.clicks, 0);

  assert.ok(
    personalized.events.some(
      event =>
        event.event === "stopped" &&
        event.details?.reason === "child-qualification-failed"
    ),
    "non-Temporary failures must not receive the settlement grace period"
  );
})().catch(error => {
  console.error(error);
  process.exit(1);
});
"""

        script = script.replace(
            "__CONTENT_PATH__",
            json.dumps(str(CONTENT)),
        )

        self.run_node(script)



if __name__ == "__main__":
    unittest.main()
