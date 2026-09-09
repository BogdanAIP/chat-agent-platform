from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryCurrentPageStateRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_dedicated_temporary_page_is_positive_evidence_without_reauthorizing_menu_text(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const assert = require("assert/strict");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const prompt = "bounded exact prompt";
const promptSha = nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");

function makeNode(tagName, text = "", attrs = {{}}, parent = null) {{
  const node = {{
    nodeType: 1,
    tagName: String(tagName || "DIV").toUpperCase(),
    isConnected: true,
    hidden: false,
    inert: false,
    parentElement: parent,
    textContent: text,
    innerText: text,
    disabled: false,
    value: "",
    childNodes: [],
    getBoundingClientRect() {{ return {{width: 240, height: 48}}; }},
    getAttribute(name) {{ return Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name] : null; }},
    contains(other) {{
      for (let current = other; current; current = current.parentElement) {{
        if (current === node) return true;
      }}
      return false;
    }},
    matches(selector) {{
      if (selector === ":disabled") return false;
      if (selector === "form") return node.tagName === "FORM";
      if (selector === 'main,[role="main"]') return node.tagName === "MAIN" || attrs.role === "main";
      if (selector.includes("button") && node.tagName === "BUTTON") return true;
      if (selector.includes("a") && node.tagName === "A") return true;
      if (selector.includes('[role="button"]') && attrs.role === "button") return true;
      if (selector.includes('[role="menuitem"]') && attrs.role === "menuitem") return true;
      if (selector.includes('[role="option"]') && attrs.role === "option") return true;
      if (selector.includes('[role="tab"]') && attrs.role === "tab") return true;
      if (selector.includes('[role="switch"]') && attrs.role === "switch") return true;
      if (selector.includes('[role="dialog"]') && attrs.role === "dialog") return true;
      if (selector.includes('[role="menu"]') && attrs.role === "menu") return true;
      if (selector.includes('[role="listbox"]') && attrs.role === "listbox") return true;
      if (selector.includes("dialog") && node.tagName === "DIALOG") return true;
      return false;
    }},
    closest(selector) {{
      for (let current = node; current; current = current.parentElement) {{
        if (current.matches?.(selector)) return current;
      }}
      return null;
    }},
    querySelectorAll() {{ return []; }},
  }};
  return node;
}}

async function runScenario(config) {{
  let intervalFn = null;
  let clicks = 0;
  let authorizeMessage = null;
  const events = [];

  const main = makeNode("main");
  const composer = makeNode("form", "", {{}}, main);
  const editor = makeNode("textarea", "", {{}}, composer);
  editor.value = prompt;
  editor.closest = selector => selector === "form" ? composer :
    selector === 'main,[role="main"]' ? main : null;
  composer.closest = selector => selector === 'main,[role="main"]' ? main :
    selector === "form" ? composer : null;
  composer.contains = other => other === editor;

  const send = makeNode("button", "Send", {{"aria-disabled": "false"}}, composer);
  send.closest = selector => selector === "form" ? composer :
    selector === 'main,[role="main"]' ? main : null;
  send.click = () => {{ clicks += 1; }};

  const personalization = makeNode("button", "Без персонализации", {{}}, main);
  const plainEntry = config.plainEntry ? makeNode("button", "Временный чат", {{}}, main) : null;

  let pageParent = main;
  let dialog = null;
  if (config.dialog) {{
    dialog = makeNode("div", "", {{role: "dialog"}}, main);
    pageParent = dialog;
  }}
  const title = config.title ? makeNode("h2", "Временный чат", {{}}, pageParent) : null;
  const policyCopy = config.policyCopy ? makeNode(
    "p",
    "В этом чате не будут учитываться память, плагины и пользовательские инструкции, и он не появится в истории.",
    {{}},
    pageParent,
  ) : null;

  const pageNodes = [title, policyCopy].filter(Boolean);
  main.querySelectorAll = selector => {{
    if (selector === 'h1,h2,h3,h4,[role="heading"],div,p,span') return pageNodes;
    if (selector === "p,div,span") return policyCopy ? [policyCopy] : [];
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
      const value = String(text || "");
      if (/Без персонализац/i.test(value) || /Non-personalized/i.test(value)) return "non-personalized";
      if (/Personalized/i.test(value) || /Персонализ/i.test(value)) return "personalized";
      return "unknown";
    }},
    conversationId() {{ return null; }},
    armPostDeliveryUiGuard() {{ return true; }},
    hasExpectedPrompt() {{ return false; }},
    invalidatePostDeliveryAuthorization() {{}},
    captureAuthorization() {{ return null; }},
    singleResultBlockShape() {{ return false; }},
    hasSingleResultBlock() {{ return false; }},
  }};

  const controls = [personalization];
  if (plainEntry) controls.push(plainEntry);

  const document = {{
    querySelector(selector) {{
      if (selector === 'button[data-testid="send-button"]') return send;
      if (selector === 'button[data-testid="stop-button"]') return null;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector === 'button[data-testid="send-button"]') return [send];
      if (selector === 'button,[role="button"],[aria-label],[title],[data-testid]') return controls;
      if (selector === 'dialog,[role="dialog"],[role="menu"],[role="listbox"]') return dialog ? [dialog] : [];
      if (selector === '[data-message-author-role="user"],[data-message-author-role="assistant"]') return [];
      if (selector === '[data-message-author-role="user"]') return [];
      if (selector === '[data-message-author-role="assistant"]') return [];
      if (selector === "button") return [send, ...controls];
      return [];
    }},
  }};

  const context = {{
    console,
    URL,
    URLSearchParams,
    TextEncoder,
    crypto: nodeCrypto.webcrypto,
    CAPChatGPTTemporaryPolicy: policy,
    CAPChatGPTTemporaryExecutionGeneration: "9".repeat(64),
    location: {{href: "https://chatgpt.com/?temporary-chat=true", origin: "https://chatgpt.com"}},
    history: {{state: null, replaceState() {{}}}},
    document,
    getComputedStyle() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }},
    setInterval(fn) {{ intervalFn = fn; return 1; }},
    clearInterval() {{}},
    chrome: {{runtime: {{
      lastError: null,
      sendMessage(message, callback) {{
        if (message.kind === "event") events.push(message);
        if (message.kind === "authorize-send") {{
          authorizeMessage = message;
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
        callback({{ok: true}});
      }},
    }}}},
  }};
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(source, context, {{filename: "content.js"}});

  const flush = () => new Promise(resolve => setImmediate(resolve));
  for (let i = 0; i < 12; i += 1) {{
    await flush();
    if (typeof intervalFn === "function") intervalFn();
  }}
  return {{clicks, authorizeMessage, events}};
}}

(async () => {{
  const active = await runScenario({{title: true, policyCopy: true}});
  assert.equal(active.clicks, 1, "dedicated Temporary page title + provider policy copy must prove the live active page");
  assert.ok(active.authorizeMessage);
  assert.equal(active.authorizeMessage.temporary_mode, true);
  assert.equal(active.authorizeMessage.fresh_context, true);
  assert.equal(active.authorizeMessage.personalization_disabled, true);
  assert.deepEqual(Array.from(active.authorizeMessage.plugin_markers), []);

  const titleOnly = await runScenario({{title: true, policyCopy: false}});
  assert.equal(titleOnly.clicks, 0, "page title without Temporary policy copy must fail closed");
  assert.equal(titleOnly.authorizeMessage, null);
  assert.ok(titleOnly.events.some(event => event.event === "temporary-ui-not-proven"));

  const dialog = await runScenario({{title: true, policyCopy: true, dialog: true}});
  assert.equal(dialog.clicks, 0, "Temporary help/dialog content must not become active-page authority");
  assert.equal(dialog.authorizeMessage, null);

  const menu = await runScenario({{title: false, policyCopy: true, plainEntry: true}});
  assert.equal(menu.clicks, 0, "plain Temporary menu entry remains insufficient even beside explanatory copy");
  assert.equal(menu.authorizeMessage, null);
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        self.assertEqual(0, completed.returncode, output)


if __name__ == "__main__":
    unittest.main()
