from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


class ChatGPTTemporaryPromptFailClosedRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def _run_node(self, script: str) -> None:
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

    def test_policy_rejects_legacy_prompt_query(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert/strict");
const source = fs.readFileSync({json.dumps(str(POLICY))}, "utf8");
const context = {{
  URL,
  URLSearchParams,
  setInterval() {{ return 1; }},
  clearInterval() {{}},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{filename: "policy.js"}});
const policy = context.CAPChatGPTTemporaryPolicy;
const url = "https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1" +
  "&cap_delegation_id=" + "b".repeat(64) +
  "&cap_delivery_id=" + "c".repeat(64) +
  "&cap_task_sha256=" + "d".repeat(64) +
  "&cap_expected_head=" + "e".repeat(40) +
  "&cap_prompt_sha256=" + "f".repeat(64) +
  "&prompt=" + encodeURIComponent("review_run_id=" + "9".repeat(64)) +
  "#cap_run_id=" + "a".repeat(64);
const parsed = policy.parseIntent(url);
assert.equal(parsed.enabled, false);
assert.equal(parsed.reason, "prompt-in-url");
"""
        self._run_node(script)

    def test_digest_mismatch_never_starts_adapter_or_send_authority(self) -> None:
        script = self._content_case(
            editor_value="",
            response_prompt='prompt + "\\ncorrupted"',
            expected_stopped_reason=None,
            expect_interval=True,
        )
        self._run_node(script)

    def test_nonempty_unrelated_composer_is_not_overwritten_and_never_sent(self) -> None:
        script = self._content_case(
            editor_value="unrelated user draft",
            response_prompt="prompt",
            expected_stopped_reason="composer-not-empty-before-prompt-handoff",
            expect_interval=True,
        )
        self._run_node(script)

    def _content_case(
        self,
        *,
        editor_value: str,
        response_prompt: str,
        expected_stopped_reason: str | None,
        expect_interval: bool,
    ) -> str:
        return f"""
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
  "TASK_BEGIN:" + "d".repeat(64),
  "REVIEW_REQUEST_V1",
  "review_run_id=" + "8".repeat(64),
  "TASK_END:" + "d".repeat(64),
  "",
  "CAP_WORKER_RESULT_V1_BEGIN",
  "{{}}",
  "CAP_WORKER_RESULT_V1_END",
].join("\\n");
const promptSha = nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");
let intervals = 0;
let tick = null;
let authorizeCalls = 0;
const events = [];

function rect() {{ return {{width: 500, height: 80}}; }}
function style() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }}
const composer = {{
  nodeType: 1,
  tagName: "FORM",
  isConnected: true,
  hidden: false,
  inert: false,
  disabled: false,
  parentElement: null,
  getBoundingClientRect: rect,
  getAttribute() {{ return null; }},
  matches(selector) {{ return selector === "form"; }},
  closest(selector) {{ return selector === "form" ? composer : null; }},
  contains(node) {{ return node === editor; }},
}};
const editor = {{
  nodeType: 1,
  tagName: "TEXTAREA",
  isConnected: true,
  hidden: false,
  inert: false,
  disabled: false,
  readOnly: false,
  parentElement: composer,
  value: {json.dumps(editor_value)},
  childNodes: [],
  getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "data-mode" ? "Temporary Chat" : null; }},
  matches(selector) {{ return selector === ":disabled" ? false : false; }},
  closest(selector) {{ return selector === "form" ? composer : null; }},
  dispatchEvent() {{ return true; }},
}};

const personalization = {{
  nodeType: 1,
  tagName: "BUTTON",
  isConnected: true,
  hidden: false,
  inert: false,
  disabled: false,
  parentElement: null,
  textContent: "Non-personalized",
  getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "aria-label" ? "Non-personalized" : null; }},
}};

const intent = {{
  enabled: true,
  runId: "a".repeat(64),
  delegationId: "b".repeat(64),
  deliveryId: "c".repeat(64),
  taskSha256: "d".repeat(64),
  expectedHead: "e".repeat(40),
  promptSha256: promptSha,
  prompt: "",
  maxWaitMs: 300000,
  deliveryObserveMs: 20000,
  stableMs: 3000,
}};
const policy = {{
  HEX64_RE: /^[0-9a-f]{{64}}$/,
  HEAD40_RE: /^[0-9a-f]{{40}}$/,
  parseIntent() {{ return intent; }},
  promptMatchesIntent(candidate) {{
    return typeof candidate === "string" && candidate.startsWith("WORKER_TASK_V1");
  }},
  findComposerEditor() {{ return editor; }},
  exactPromptMatches(observed, expected) {{
    return String(observed || "") === String(expected || "");
  }},
  personalizationModeFromText() {{ return "non-personalized"; }},
  conversationId() {{ return null; }},
  armPostDeliveryUiGuard() {{ return true; }},
  hasExpectedPrompt() {{ return false; }},
  invalidatePostDeliveryAuthorization() {{}},
  captureAuthorization() {{ return null; }},
  singleResultBlockShape() {{ return false; }},
  hasSingleResultBlock() {{ return false; }},
}};
const context = {{
  console,
  URL,
  URLSearchParams,
  TextEncoder,
  Event: class Event {{ constructor(type, init = {{}}) {{ this.type = type; this.bubbles = Boolean(init.bubbles); }} }},
  crypto: nodeCrypto.webcrypto,
  Date,
  CAPChatGPTTemporaryPolicy: policy,
  CAPChatGPTTemporaryExecutionGeneration: "9".repeat(64),
  location: {{
    href: "https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1&cap_delegation_id=" + "b".repeat(64) +
      "&cap_delivery_id=" + "c".repeat(64) + "&cap_task_sha256=" + "d".repeat(64) +
      "&cap_expected_head=" + "e".repeat(40) + "&cap_prompt_sha256=" + promptSha +
      "#cap_run_id=" + "a".repeat(64),
    origin: "https://chatgpt.com",
  }},
  history: {{
    state: null,
    replaceState(_state, _title, nextUrl) {{
      context.location.href = new URL(nextUrl, context.location.href).href;
    }},
  }},
  document: {{
    querySelector(selector) {{
      if (selector === 'button[data-testid="stop-button"]') return null;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector === 'button,[role="button"],[aria-label],[title],[data-testid]') return [personalization];
      return [];
    }},
  }},
  getComputedStyle: style,
  setInterval(fn) {{ intervals += 1; tick = fn; return intervals; }},
  clearInterval() {{}},
  chrome: {{runtime: {{
    lastError: null,
    sendMessage(message, callback) {{
      if (message.kind === "task-prompt") {{
        callback({{
          ok: true,
          prompt: {response_prompt},
          delegation_id: intent.delegationId,
          delivery_id: intent.deliveryId,
          task_sha256: intent.taskSha256,
          expected_runtime_head: intent.expectedHead,
          prompt_sha256: intent.promptSha256,
        }});
        return;
      }}
      if (message.kind === "authorize-send") {{
        authorizeCalls += 1;
        callback({{ok: true, send_authorized: true, delivery_state: "claimed"}});
        return;
      }}
      if (message.kind === "event") {{
        events.push(message);
        callback({{ok: true}});
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
  await flush();
  await flush();
  {"assert.ok(intervals > 0); assert.equal(typeof tick, 'function'); tick(); await flush();" if expect_interval else "assert.equal(intervals, 0);"}
  assert.equal(authorizeCalls, 0);
  assert.equal(editor.value, {json.dumps(editor_value)});
  {f'assert.ok(events.some(event => event.event === "stopped" && event.details?.reason === {json.dumps(expected_stopped_reason)}));' if expected_stopped_reason else ''}
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""


if __name__ == "__main__":
    unittest.main()
