from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


class ChatGPTTemporaryCaptureContinuityPolicyRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_transient_dom_loss_and_assistant_change_invalidate_capture_authority(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert/strict");

let now = 1000;
let intervalCallback = null;
let mutationCallback = null;
let assistantText = "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END";
let stopPresent = false;

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
].join("\\n");

function rect() {{ return {{width: 500, height: 80}}; }}
function style() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }}

const form = {{
  nodeType: 1,
  isConnected: true,
  parentElement: null,
  hidden: false,
  inert: false,
  getBoundingClientRect: rect,
  getAttribute() {{ return null; }},
  matches() {{ return false; }},
}};
const editor = {{
  nodeType: 1,
  tagName: "DIV",
  isConnected: true,
  parentElement: form,
  hidden: false,
  inert: false,
  isContentEditable: true,
  innerText: "",
  textContent: "",
  getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "contenteditable" ? "true" : null; }},
  closest(selector) {{ return selector === "form" ? form : null; }},
  matches() {{ return false; }},
}};
const userNode = {{
  nodeType: 1,
  isConnected: true,
  parentElement: null,
  innerText: userText,
  textContent: userText,
  getBoundingClientRect: rect,
  getAttribute() {{ return null; }},
  matches(selector) {{ return selector.includes('data-message-author-role="user"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }},
  querySelector() {{ return null; }},
}};
const assistantNode = {{
  nodeType: 1,
  isConnected: true,
  parentElement: null,
  get innerText() {{ return assistantText; }},
  get textContent() {{ return assistantText; }},
  getBoundingClientRect: rect,
  getAttribute() {{ return null; }},
  matches(selector) {{ return selector.includes('data-message-author-role="assistant"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }},
  querySelector() {{ return null; }},
}};
const root = {{
  nodeType: 1,
  matches() {{ return false; }},
  closest() {{ return null; }},
  querySelector() {{ return null; }},
}};

class FakeMutationObserver {{
  constructor(callback) {{ mutationCallback = callback; }}
  observe() {{}}
}}

const context = {{
  console,
  URL,
  URLSearchParams,
  Date: class extends Date {{ static now() {{ return now; }} }},
  MutationObserver: FakeMutationObserver,
  setInterval(callback) {{ intervalCallback = callback; return 1; }},
  clearInterval() {{}},
  getComputedStyle: style,
  location: {{ href: "https://chatgpt.com/c/continuity-test", origin: "https://chatgpt.com" }},
  history: {{ state: null, replaceState() {{}} }},
  document: {{
    documentElement: root,
    querySelector(selector) {{
      if (selector === "#prompt-textarea") return editor;
      if (selector === 'button[data-testid="stop-button"]') return stopPresent ? {{}} : null;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector === '#prompt-textarea,[contenteditable="true"],textarea') return [editor];
      if (selector.includes('data-message-author-role="user"')) return [userNode];
      if (selector.includes('data-message-author-role="assistant"')) return [assistantNode];
      if (selector === "button") return [];
      return [];
    }},
  }},
  chrome: {{ runtime: {{
    sendMessage(message, callback) {{
      if (message.kind === "event" && message.event === "delivery-visible") {{
        callback({{ok: true, cleanup_token: "9".repeat(64)}});
        return;
      }}
      callback({{ok: true}});
    }},
  }}}},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), context);
const policy = context.CAPChatGPTTemporaryPolicy;
const intent = {{runId, delegationId, deliveryId, taskSha256: taskSha, expectedHead, promptSha256: promptSha}};
assert.equal(policy.armPostDeliveryUiGuard(intent), true);
assert.equal(typeof intervalCallback, "function");
assert.equal(typeof mutationCallback, "function");

// First uninterrupted 8-second qualification.
intervalCallback();
now = 9001;
intervalCallback();
const first = policy.captureAuthorization();
assert.ok(first);
const firstEpoch = first.guardEpoch;

// A transient relevant mutation is seen immediately even if the DOM is already
// restored before the next 500ms poll. Old capture authority must disappear.
mutationCallback([{{type: "childList", target: root, addedNodes: [], removedNodes: [userNode]}}]);
assert.equal(policy.captureAuthorization(), null);

// Requalify on a fresh uninterrupted interval.
now = 10000;
intervalCallback();
now = 18001;
intervalCallback();
const second = policy.captureAuthorization();
assert.ok(second);
assert.notEqual(second.guardEpoch, firstEpoch);

// The assistant result itself is part of current capture authority. A text
// change must be detected synchronously even without waiting for the observer.
assistantText = "CAP_WORKER_RESULT_V1_BEGIN\\n{{\"changed\":true}}\\nCAP_WORKER_RESULT_V1_END";
assert.equal(policy.captureAuthorization(), null);

// Requalify again, then prove an active generating/stop state also fails closed.
now = 19000;
intervalCallback();
now = 27001;
intervalCallback();
assert.ok(policy.captureAuthorization());
stopPresent = true;
assert.equal(policy.captureAuthorization(), null);
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
