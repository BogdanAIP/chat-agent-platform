from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryCurrentHeadP1RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_send_temporary_and_closed_profile_findings_execute_production_content(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const assert = require("assert/strict");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const prompt = "bounded exact prompt";
const promptSha = nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");

function makeNode(text, attrs = {{}}, options = {{}}) {{
  return {{
    isConnected: options.connected !== false,
    hidden: options.hidden === true,
    inert: false,
    parentElement: options.parentElement || null,
    textContent: text || "",
    innerText: text || "",
    disabled: options.disabled === true,
    getBoundingClientRect() {{
      return options.visible === false ? {{width: 0, height: 0}} : {{width: 120, height: 32}};
    }},
    getAttribute(name) {{ return Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name] : null; }},
    contains() {{ return false; }},
    matches() {{ return false; }},
  }};
}}

async function runScenario(config) {{
  let intervalFn = null;
  let clicks = 0;
  let clicked = false;
  let authorizeMessage = null;
  const events = [];
  const composer = makeNode("", {{}}, {{}});
  composer.tagName = "FORM";
  composer.textContent = prompt;
  const editorAttrs = {{}};
  if (config.composerTemporary) editorAttrs.placeholder = "Temporary Chat";
  const editor = makeNode("", editorAttrs, {{parentElement: composer}});
  editor.tagName = "TEXTAREA";
  editor.value = prompt;
  editor.closest = selector => selector === "form" ? composer : null;
  composer.contains = node => node === editor;

  function sendButton(name, visible = true) {{
    const button = makeNode(name, {{"aria-disabled": "false"}}, {{parentElement: composer, visible}});
    button.tagName = "BUTTON";
    button.closest = selector => selector === "form" ? composer : null;
    button.click = () => {{
      clicks += 1;
      clicked = true;
      if (config.removeSendAfterClick) sendButtons = [];
      composer.textContent = "";
      editor.value = "";
    }};
    return button;
  }}

  let sendButtons = [];
  if (config.hiddenAndVisibleSend) sendButtons = [sendButton("hidden", false), sendButton("visible", true)];
  else if (config.duplicateVisibleSend) sendButtons = [sendButton("one", true), sendButton("two", true)];
  else sendButtons = [sendButton("only", true)];

  const temporaryAttrs = config.externalTemporaryActive ? {{"aria-pressed": "true"}} : {{}};
  const temporaryEntry = makeNode("Temporary Chat", temporaryAttrs);
  const personalization = makeNode("Non-personalized");
  const plugin = makeNode(config.pluginName || "");
  const controls = [temporaryEntry, personalization];
  if (config.pluginName) controls.push(plugin);
  const userTurn = makeNode(prompt);

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
      const value = String(text);
      if (/Non-personalized/i.test(value)) return "non-personalized";
      if (/Personalized/i.test(value)) return "personalized";
      return "unknown";
    }},
    conversationId() {{ return null; }},
    armPostDeliveryUiGuard() {{ return true; }},
    hasExpectedPrompt(text) {{ return String(text || "") === prompt; }},
    invalidatePostDeliveryAuthorization() {{}},
    captureAuthorization() {{ return null; }},
    singleResultBlockShape() {{ return false; }},
    hasSingleResultBlock() {{ return false; }},
  }};

  const document = {{
    querySelector(selector) {{
      if (selector === 'button[data-testid="send-button"]') return sendButtons[0] || null;
      if (selector === 'button[data-testid="stop-button"]') return null;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector === 'button[data-testid="send-button"]') return sendButtons;
      if (selector === 'button,[role="button"],[aria-label],[title],[data-testid]') return controls;
      if (selector === '[data-message-author-role="user"],[data-message-author-role="assistant"]') return clicked ? [userTurn] : [];
      if (selector === '[data-message-author-role="user"]') return clicked ? [userTurn] : [];
      if (selector === '[data-message-author-role="assistant"]') return [];
      if (selector === "button") return sendButtons;
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
    location: {{href: "https://chatgpt.com/", origin: "https://chatgpt.com"}},
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
            delivery_state: clicked ? "claimed" : "prepared",
            result_state: "open",
            result_status: null,
            final_observation_request_id: null,
          }});
          return;
        }}
        if (message.kind === "delivery") {{
          callback({{ok: true, delivery_state: "delivered", result_state: "open"}});
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
  const inactive = await runScenario({{composerTemporary: false, externalTemporaryActive: false}});
  assert.equal(inactive.clicks, 0, "plain Temporary entry affordance must not authorize Send");
  assert.equal(inactive.authorizeMessage, null);
  assert.ok(inactive.events.some(event => event.event === "temporary-ui-not-proven"));

  const composerActive = await runScenario({{composerTemporary: true, externalTemporaryActive: false}});
  assert.equal(composerActive.clicks, 1, "current composer Temporary placeholder must prove active mode");

  const externalActive = await runScenario({{composerTemporary: false, externalTemporaryActive: true}});
  assert.equal(externalActive.clicks, 1, "explicit active-state Temporary control must remain valid evidence");

  const hiddenAndVisible = await runScenario({{composerTemporary: true, hiddenAndVisibleSend: true}});
  assert.equal(hiddenAndVisible.clicks, 1, "hidden stale Send must not suppress the current visible Send");

  const duplicate = await runScenario({{composerTemporary: true, duplicateVisibleSend: true}});
  assert.equal(duplicate.clicks, 0, "two visible eligible Send controls must fail closed");
  assert.equal(duplicate.authorizeMessage, null);

  const closedProfile = await runScenario({{composerTemporary: true, pluginName: "Slack"}});
  assert.equal(closedProfile.clicks, 1, "closed Temporary profile must not depend on a finite plugin brand list");
  assert.ok(closedProfile.authorizeMessage);
  assert.equal(Array.isArray(closedProfile.authorizeMessage.plugin_markers), true);
  assert.equal(closedProfile.authorizeMessage.plugin_markers.length, 0);

  const cleanupWithoutSend = await runScenario({{composerTemporary: true, removeSendAfterClick: true}});
  assert.equal(cleanupWithoutSend.clicks, 1);
  assert.ok(cleanupWithoutSend.events.some(event => event.event === "post-delivery-cleanup-complete"),
    "post-delivery cleanup must not require Send control persistence");
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
