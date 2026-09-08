from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from runtime.agent_sessions.chatgpt_temporary import (
    RAW_RESULT_BEGIN,
    RAW_RESULT_END,
    normalize_worker_result_text,
)
from runtime.control_plane.delegation_state import parse_delegation_identity


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
POLICY = EXTENSION / "policy.js"
CONTENT = EXTENSION / "content.js"


class ChatGPTTemporaryFinalReviewClosureRuntimeTests(unittest.TestCase):
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

    def test_digest_fences_are_required_and_result_payload_markers_are_data(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert/strict");
vm.runInThisContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), {{filename: "policy.js"}});
const policy = CAPChatGPTTemporaryPolicy;
const delegationId = "a".repeat(64);
const deliveryId = "b".repeat(64);
const taskSha = "c".repeat(64);
const intent = {{delegationId, deliveryId, taskSha256: taskSha}};
const header = [
  "WORKER_TASK_V1",
  `delegation_id=${{delegationId}}`,
  `delivery_id=${{deliveryId}}`,
  `task_sha256=${{taskSha}}`,
].join("\\n");
const fenced = [
  header,
  `TASK_BEGIN:${{taskSha}}`,
  "bounded task body",
  `TASK_END:${{taskSha}}`,
].join("\\n");
assert.equal(policy.hasExpectedPrompt(fenced, intent), true);
assert.equal(policy.hasExpectedPrompt(header, intent), false, "both digest fences are mandatory");
assert.equal(policy.hasExpectedPrompt(fenced.replace(`TASK_BEGIN:${{taskSha}}\\n`, ""), intent), false);
assert.equal(policy.hasExpectedPrompt(fenced.replace(`\\nTASK_END:${{taskSha}}`, ""), intent), false);

const payload = JSON.stringify({{
  schema_version: 1,
  payload: `literal ${{policy.RESULT_BEGIN}} and ${{policy.RESULT_END}} are task data`,
}});
const valid = `${{policy.RESULT_BEGIN}}\\n${{payload}}\\n${{policy.RESULT_END}}`;
assert.equal(policy.singleResultBlockShape(valid), true, "payload marker strings are JSON data");
assert.equal(policy.singleResultBlockShape(valid + "\\n" + valid), false);
assert.equal(policy.singleResultBlockShape("prefix\\n" + valid), false);
"""
        self.run_node(script)

    def test_transient_stop_record_and_hidden_assistant_revoke_capture_authority(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert/strict");
let now = 1000;
let intervalCallback = null;
let observer = null;
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
const genericButton = {{nodeType: 1, tagName: "BUTTON", isConnected: true, parentElement: null,
  textContent: "Regenerate", ariaLabel: "Regenerate",
  getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "aria-label" ? this.ariaLabel : null; }},
  matches() {{ return false; }}, closest(selector) {{ return selector === "button" ? this : null; }},
  querySelectorAll() {{ return []; }}}};
const root = {{nodeType: 1, isConnected: true, parentElement: null,
  getBoundingClientRect: rect, getAttribute() {{ return null; }}, matches() {{ return false; }},
  closest() {{ return null; }}, querySelector() {{ return null; }}, querySelectorAll() {{ return []; }}}};
class FakeMutationObserver {{
  constructor(callback) {{ this.callback = callback; this.pending = []; observer = this; }}
  observe() {{}}
  takeRecords() {{ const value = this.pending; this.pending = []; return value; }}
  queue(record) {{ this.pending.push(record); }}
}}
const context = {{
  console, URL, URLSearchParams,
  Date: class extends Date {{ static now() {{ return now; }} }},
  MutationObserver: FakeMutationObserver,
  setInterval(callback) {{ intervalCallback = callback; return 1; }}, clearInterval() {{}},
  getComputedStyle: style,
  location: {{href: "https://chatgpt.com/c/final-review", origin: "https://chatgpt.com"}},
  history: {{state: null, replaceState() {{}}}},
  document: {{
    documentElement: root,
    querySelector(selector) {{
      if (selector === "#prompt-textarea") return editor;
      if (selector === 'button[data-testid="stop-button"]') return null;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector === '#prompt-textarea,[contenteditable="true"],textarea') return [editor];
      if (selector.includes('data-message-author-role="user"')) return [userNode];
      if (selector.includes('data-message-author-role="assistant"')) return [assistantNode];
      if (selector === "button") return [genericButton];
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
vm.runInContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), context);
const policy = context.CAPChatGPTTemporaryPolicy;
const intent = {{runId, delegationId, deliveryId, taskSha256: taskSha, expectedHead, promptSha256: promptSha}};
assert.equal(policy.armPostDeliveryUiGuard(intent), true);
function qualify() {{
  intervalCallback();
  now += 8001;
  intervalCallback();
  const value = policy.captureAuthorization();
  assert.ok(value);
  return value;
}}
const first = qualify();
observer.queue({{type: "attributes", attributeName: "aria-label", target: genericButton, addedNodes: [], removedNodes: []}});
assert.equal(policy.captureAuthorization(), null, "pending fallback Stop transition must revoke old epoch");
const second = qualify();
assert.notEqual(second.guardEpoch, first.guardEpoch);
assistantNode.hidden = true;
observer.callback([{{type: "attributes", attributeName: "hidden", target: assistantNode, addedNodes: [], removedNodes: []}}]);
intervalCallback();
now += 8001;
intervalCallback();
assert.equal(policy.captureAuthorization(), null, "hidden-only assistant cannot regain capture authority");
"""
        self.run_node(script)

    def test_send_requalifies_environment_immediately_before_click(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const prompt = "bounded exact prompt";
const promptSha = nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");
const intent = {{enabled: true, runId: "a".repeat(64), delegationId: "b".repeat(64),
  deliveryId: "c".repeat(64), taskSha256: "d".repeat(64), expectedHead: "e".repeat(40),
  promptSha256: promptSha, prompt, maxWaitMs: 300000, deliveryObserveMs: 20000, stableMs: 3000}};
let intervalFn = null;
let clicks = 0;
let authorizeCalls = 0;
let personalized = false;
const events = [];
function rect() {{ return {{width: 400, height: 80}}; }}
const composer = {{isConnected: true, parentElement: null, getBoundingClientRect: rect,
  contains() {{ return false; }}}};
const editor = {{tagName: "TEXTAREA", value: prompt, isConnected: true, parentElement: composer,
  getBoundingClientRect: rect, closest(selector) {{ return selector === "form" ? composer : null; }}}};
const button = {{isConnected: true, disabled: false, parentElement: composer,
  getAttribute(name) {{ return name === "aria-disabled" ? "false" : null; }},
  closest(selector) {{ return selector === "form" ? composer : null; }}, click() {{ clicks += 1; }}};
const temporaryNode = {{isConnected: true, parentElement: null, textContent: "Temporary Chat",
  getBoundingClientRect: rect, getAttribute() {{ return null; }}, contains() {{ return false; }}}};
const personalizationNode = {{isConnected: true, parentElement: null,
  get textContent() {{ return personalized ? "Personalized" : "Non-personalized"; }},
  getBoundingClientRect: rect, getAttribute() {{ return null; }}, contains() {{ return false; }}}};
const policy = {{
  HEX64_RE: /^[0-9a-f]{{64}}$/, HEAD40_RE: /^[0-9a-f]{{40}}$/,
  parseIntent() {{ return intent; }},
  findComposerEditor() {{ return editor; }},
  exactPromptMatches(observed, expected) {{ return observed === expected; }},
  personalizationModeFromText(text) {{
    const value = String(text);
    if (/Non-personalized/i.test(value)) return "non-personalized";
    if (/Personalized/i.test(value)) return "personalized";
    return "unknown";
  }},
  conversationId() {{ return null; }}, armPostDeliveryUiGuard() {{ return true; }},
  hasExpectedPrompt() {{ return false; }}, invalidatePostDeliveryAuthorization() {{}},
  captureAuthorization() {{ return null; }}, singleResultBlockShape() {{ return false; }},
  hasSingleResultBlock() {{ return false; }},
}};
global.crypto = nodeCrypto.webcrypto;
global.TextEncoder = TextEncoder;
global.CAPChatGPTTemporaryPolicy = policy;
global.CAPChatGPTTemporaryExecutionGeneration = "9".repeat(64);
global.location = {{href: "https://chatgpt.com/", origin: "https://chatgpt.com"}};
global.history = {{state: null, replaceState() {{}}}};
global.getComputedStyle = () => ({{visibility: "visible", display: "block", opacity: "1"}});
global.document = {{
  querySelector(selector) {{ return selector === 'button[data-testid="send-button"]' ? button : null; }},
  querySelectorAll(selector) {{
    if (selector === 'button,[role="button"],[aria-label],[title],[data-testid]') return [temporaryNode, personalizationNode];
    if (selector === '[data-message-author-role="user"],[data-message-author-role="assistant"]') return [];
    if (selector.includes('data-message-author-role="user"') || selector.includes('data-message-author-role="assistant"')) return [];
    if (selector === "button") return [];
    return [];
  }},
}};
global.chrome = {{runtime: {{lastError: null, sendMessage(message, callback) {{
  if (message.kind === "authorize-send") {{ authorizeCalls += 1; callback({{ok: true, send_authorized: true, delivery_state: "claimed"}}); return; }}
  if (message.kind === "event") events.push(message);
  callback({{ok: true}});
}}}}}};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};
vm.runInThisContext(source, {{filename: "content.js"}});
function flush() {{ return new Promise((resolve) => setImmediate(resolve)); }}
(async () => {{
  for (let i = 0; i < 10 && authorizeCalls === 0; i += 1) await flush();
  if (authorizeCalls !== 1) process.exit(70);
  personalized = true;
  intervalFn();
  await flush();
  if (clicks !== 0) process.exit(71);
  if (!events.some((event) => event.event === "temporary-ui-changed-before-send")) process.exit(72);
}})().catch((error) => {{ console.error(error); process.exit(73); }});
"""
        self.run_node(script)

    def test_assistant_selection_is_visibility_filtered_in_content_runtime(self) -> None:
        source = CONTENT.read_text(encoding="utf-8")
        self.assertIn("function visibleConversationTurns(role)", source)
        self.assertGreaterEqual(source.count('visibleConversationTurns("assistant")'), 2)
        self.assertIn(".filter((node) => visible(node))", source)

    def test_python_result_parser_accepts_protocol_marker_text_inside_payload(self) -> None:
        task = "bounded parser regression"
        task_sha = hashlib.sha256(task.encode("utf-8")).hexdigest()
        identity = parse_delegation_identity(
            {
                "parent_task_id": "result-framing-regression",
                "subgoal_id": "payload-markers-are-data",
                "worker_kind": "researcher",
                "worker_profile": "fresh_readonly_worker_v1",
                "task_sha256": task_sha,
                "result_contract_id": "research-result-v1",
            }
        )
        delegation_id = "a" * 64
        delivery_id = "b" * 64
        payload = f"literal {RAW_RESULT_BEGIN} and {RAW_RESULT_END} are payload data"
        value = {
            "schema_version": 1,
            "delegation_id": delegation_id,
            "delivery_id": delivery_id,
            "worker_kind": "researcher",
            "result_contract_id": "research-result-v1",
            "status": "COMPLETED",
            "payload": payload,
        }
        text = RAW_RESULT_BEGIN + "\n" + json.dumps(value, separators=(",", ":")) + "\n" + RAW_RESULT_END
        normalized = normalize_worker_result_text(
            text,
            identity=identity,
            delegation_id=delegation_id,
            delivery_id=delivery_id,
        )
        self.assertEqual(payload, normalized.value["payload"])


if __name__ == "__main__":
    unittest.main()
