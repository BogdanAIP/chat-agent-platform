from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryPostSendDuplicateRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_full_prompt_duplicate_is_cleared_without_second_send(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const assert = require("assert/strict");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");

const prompt = [
  "WORKER_TASK_V1",
  "delegation_id=" + "b".repeat(64),
  "delivery_id=" + "c".repeat(64),
  "worker_kind=code-review",
  "worker_profile=fresh_readonly_worker_v1",
  "result_contract_id=review_result_v1",
  "task_sha256=" + "d".repeat(64),
  "",
  "You are one fresh bounded read-only worker for exactly this task.",
  "",
  "TASK_BEGIN:" + "d".repeat(64),
  "REVIEW_REQUEST_V1",
  "repository=BogdanAIP/chat-agent-platform",
  "pr_number=159",
  "TASK_END:" + "d".repeat(64),
  "",
  "CAP_WORKER_RESULT_V1_BEGIN",
  "{{\"schema_version\":1}}",
  "CAP_WORKER_RESULT_V1_END",
].join("\n");
const promptSha = nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");

let now = 1000;
let tick = null;
let clicks = 0;
let userTurns = [];
const deliveries = [];
const events = [];

function rect() {{ return {{width: 500, height: 80}}; }}
function style() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }}
function node(tagName, text = "", attrs = {{}}, parent = null) {{
  const value = {{
    nodeType: 1,
    tagName: String(tagName).toUpperCase(),
    isConnected: true,
    hidden: false,
    inert: false,
    parentElement: parent,
    textContent: text,
    innerText: text,
    disabled: false,
    readOnly: false,
    childNodes: [],
    getBoundingClientRect: rect,
    getAttribute(name) {{
      return Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name] : null;
    }},
    matches(selector) {{
      if (selector === ":disabled") return false;
      if (selector === "form") return value.tagName === "FORM";
      if (selector === 'main,[role="main"]') return value.tagName === "MAIN";
      if (selector.includes("button") && value.tagName === "BUTTON") return true;
      return false;
    }},
    closest(selector) {{
      for (let current = value; current; current = current.parentElement) {{
        if (current.matches?.(selector)) return current;
      }}
      return null;
    }},
    contains(other) {{
      for (let current = other; current; current = current.parentElement) {{
        if (current === value) return true;
      }}
      return false;
    }},
    querySelectorAll() {{ return []; }},
  }};
  return value;
}}

const main = node("main");
const composer = node("form", "", {{}}, main);
const editor = node("textarea", "", {{}}, composer);
editor.value = prompt;
editor.dispatchEvent = () => true;
editor.closest = selector => selector === "form" ? composer :
  selector === 'main,[role="main"]' ? main : null;
composer.contains = other => other === editor;
composer.closest = selector => selector === 'main,[role="main"]' ? main :
  selector === "form" ? composer : null;

const userNode = node("div", "", {{"data-message-author-role": "user"}}, main);
const send = node("button", "Send", {{"data-testid": "send-button", "aria-disabled": "false"}}, composer);
send.closest = selector => selector === "form" ? composer :
  selector === 'main,[role="main"]' ? main : null;
send.click = () => {{
  clicks += 1;
  // Physical regression: the provider renders the complete submitted user turn
  // but leaves the complete original prompt in the composer.
  userNode.innerText = prompt;
  userNode.textContent = prompt;
  userTurns = [userNode];
  editor.value = prompt;
}};

const personalization = node("button", "Non-personalized", {{}}, main);
const title = node("h2", "Temporary Chat", {{}}, main);
const copy = node(
  "p",
  "This chat will not use memory, plugins, custom instructions, or history.",
  {{}},
  main,
);
main.querySelectorAll = selector => {{
  if (selector === 'h1,h2,h3,h4,[role="heading"],div,p,span') return [title, copy];
  if (selector === "p,div,span") return [copy];
  return [];
}};

const intent = {{
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
}};

const policy = {{
  HEX64_RE: /^[0-9a-f]{{64}}$/,
  HEAD40_RE: /^[0-9a-f]{{40}}$/,
  parseIntent() {{ return intent; }},
  findComposerEditor() {{ return editor; }},
  exactPromptMatches(observed, expected) {{ return observed === expected; }},
  personalizationModeFromText(text) {{
    return /Non-personalized/i.test(String(text || "")) ? "non-personalized" : "unknown";
  }},
  conversationId() {{ return null; }},
  armPostDeliveryUiGuard() {{ return true; }},
  hasExpectedPrompt(text) {{
    return String(text || "") === prompt;
  }},
  invalidatePostDeliveryAuthorization() {{}},
  captureAuthorization() {{ return null; }},
  singleResultBlockShape() {{ return false; }},
  hasSingleResultBlock() {{ return false; }},
}};

const document = {{
  querySelector(selector) {{
    if (selector === 'button[data-testid="send-button"]') return send;
    if (selector === 'button[data-testid="stop-button"]') return null;
    return null;
  }},
  querySelectorAll(selector) {{
    if (selector === 'button[data-testid="send-button"]') return [send];
    if (selector === 'button,[role="button"],[aria-label],[title],[data-testid]') return [personalization];
    if (selector === 'dialog,[role="dialog"],[role="menu"],[role="listbox"]') return [];
    if (selector === '[data-message-author-role="user"],[data-message-author-role="assistant"]') return userTurns;
    if (selector === '[data-message-author-role="user"]') return userTurns;
    if (selector === '[data-message-author-role="assistant"]') return [];
    if (selector === "button") return [send, personalization];
    return [];
  }},
}};

const context = {{
  console,
  URL,
  URLSearchParams,
  TextEncoder,
  Event: class Event {{ constructor(type, init = {{}}) {{ this.type = type; this.bubbles = Boolean(init.bubbles); }} }},
  crypto: nodeCrypto.webcrypto,
  Date: {{now: () => now}},
  CAPChatGPTTemporaryPolicy: policy,
  CAPChatGPTTemporaryExecutionGeneration: "9".repeat(64),
  location: {{
    href: "https://chatgpt.com/?temporary-chat=true",
    origin: "https://chatgpt.com",
  }},
  history: {{state: null, replaceState() {{}}}},
  document,
  getComputedStyle: style,
  setInterval(fn) {{ tick = fn; return 1; }},
  clearInterval() {{}},
  chrome: {{runtime: {{
    lastError: null,
    sendMessage(message, callback) {{
      if (message.kind === "event") {{
        events.push(message);
        callback({{ok: true}});
        return;
      }}
      if (message.kind === "authorize-send") {{
        callback({{ok: true, send_authorized: true, delivery_state: "claimed"}});
        return;
      }}
      if (message.kind === "status") {{
        callback({{
          ok: true,
          delegation_id: intent.delegationId,
          delivery_id: intent.deliveryId,
          delivery_state: "claimed",
          result_state: "open",
          result_status: null,
          final_observation_request_id: null,
        }});
        return;
      }}
      if (message.kind === "delivery") {{
        deliveries.push({{outcome: message.outcome, evidence_ref: message.evidence_ref}});
        callback({{ok: true, delivery_state: message.outcome}});
        return;
      }}
      callback({{ok: true}});
    }},
  }}}},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{filename: "content.js"}});

const flush = () => new Promise(resolve => setImmediate(resolve));
(async () => {{
  for (let i = 0; i < 8; i += 1) {{
    now += 500;
    tick();
    await flush();
  }}

  assert.equal(clicks, 1, "the task may have exactly one physical Send");
  assert.equal(editor.value, "", "the exact post-Send duplicate must be cleared locally");
  assert.ok(events.some(event => event.event === "post-send-exact-duplicate-cleared"));

  tick();
  await flush();
  await flush();

  assert.equal(clicks, 1, "duplicate cleanup must never authorize a second Send");
  assert.equal(deliveries.length, 1);
  assert.equal(deliveries[0].outcome, "delivered");
  assert.match(deliveries[0].evidence_ref, /visible-and-composer-empty/);
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            0,
            completed.returncode,
            (completed.stdout or "") + (completed.stderr or ""),
        )


if __name__ == "__main__":
    unittest.main()
