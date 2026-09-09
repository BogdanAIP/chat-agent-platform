from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryCaptureLinearizationRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_pending_ancestor_mutation_is_drained_before_capture_authorization(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert/strict");

let now = 1000;
let intervalCallback = null;
let observer = null;
const assistantText = "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END";
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
  "bounded task body",
  `TASK_END:${{taskSha}}`,
].join("\\n");

function rect() {{ return {{width: 500, height: 80}}; }}
function visibleStyle() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }}

let editor;
const form = {{
  nodeType: 1, tagName: "FORM", isConnected: true, parentElement: null,
  hidden: false, inert: false, getBoundingClientRect: rect,
  getAttribute() {{ return null; }}, matches() {{ return false; }}, closest() {{ return null; }},
  querySelector(selector) {{
    return selector.includes("prompt-textarea") || selector.includes("contenteditable") || selector.includes("textarea")
      ? editor : null;
  }},
}};
editor = {{
  nodeType: 1, tagName: "DIV", isConnected: true, parentElement: form,
  hidden: false, inert: false, isContentEditable: true, innerText: "", textContent: "",
  getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "contenteditable" ? "true" : null; }},
  closest(selector) {{ return selector === "form" ? form : null; }}, matches() {{ return false; }},
  querySelector() {{ return null; }},
}};
let userNode;
const userAncestor = {{
  nodeType: 1, isConnected: true, parentElement: null,
  hidden: false, inert: false, getBoundingClientRect: rect,
  getAttribute() {{ return null; }}, matches() {{ return false; }}, closest() {{ return null; }},
  querySelector(selector) {{ return selector.includes('data-message-author-role="user"') ? userNode : null; }},
}};
userNode = {{
  nodeType: 1, isConnected: true, parentElement: userAncestor,
  innerText: userText, textContent: userText,
  hidden: false, inert: false, getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "data-message-author-role" ? "user" : null; }},
  matches(selector) {{ return selector.includes('data-message-author-role="user"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }}, querySelector() {{ return null; }},
}};
const assistantNode = {{
  nodeType: 1, isConnected: true, parentElement: null,
  innerText: assistantText, textContent: assistantText,
  hidden: false, inert: false, getBoundingClientRect: rect,
  getAttribute(name) {{ return name === "data-message-author-role" ? "assistant" : null; }},
  matches(selector) {{ return selector.includes('data-message-author-role="assistant"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }}, querySelector() {{ return null; }},
}};
const root = {{
  nodeType: 1, isConnected: true, parentElement: null,
  getBoundingClientRect: rect, getAttribute() {{ return null; }},
  matches() {{ return false; }}, closest() {{ return null; }}, querySelector() {{ return null; }},
}};

class FakeMutationObserver {{
  constructor(callback) {{ this.callback = callback; this.pending = []; this.takeCount = 0; observer = this; }}
  observe() {{}}
  takeRecords() {{ this.takeCount += 1; const value = this.pending; this.pending = []; return value; }}
  queue(record) {{ this.pending.push(record); }}
}}

const context = {{
  console, URL, URLSearchParams,
  Date: class extends Date {{ static now() {{ return now; }} }},
  MutationObserver: FakeMutationObserver,
  setInterval(callback) {{ intervalCallback = callback; return 1; }}, clearInterval() {{}},
  getComputedStyle: visibleStyle,
  location: {{href: "https://chatgpt.com/c/linearization-test", origin: "https://chatgpt.com"}},
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
      if (selector === "button") return [];
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
assert.ok(observer);

function qualify() {{
  intervalCallback();
  now += 8001;
  intervalCallback();
  const authorization = policy.captureAuthorization();
  assert.ok(authorization);
  return authorization;
}}

const first = qualify();
const firstEpoch = first.guardEpoch;
const beforeDrainCount = observer.takeCount;
observer.queue({{type: "attributes", target: form, addedNodes: [], removedNodes: []}});
assert.equal(policy.captureAuthorization(), null);
assert.ok(observer.takeCount > beforeDrainCount);

const second = qualify();
assert.notEqual(second.guardEpoch, firstEpoch);
observer.queue({{type: "attributes", target: userAncestor, addedNodes: [], removedNodes: []}});
assert.equal(policy.captureAuthorization(), null);
const third = qualify();
assert.notEqual(third.guardEpoch, second.guardEpoch);
observer.callback([{{type: "attributes", target: form, addedNodes: [], removedNodes: []}}]);
assert.equal(policy.captureAuthorization(), null);
"""
        completed = subprocess.run(
            [self.node, "-e", script], text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_capture_dispatch_is_immediately_after_final_browser_authorization(self) -> None:
        source = CONTENT.read_text(encoding="utf-8").replace("\r\n", "\n")
        start = source.index("    async function captureResult(text) {")
        end = source.index("\n\n    async function pollControllerStatus()", start)
        function_source = source[start:end]
        recheck = "const current = policy.captureAuthorization();"
        dispatch = 'const response = await sendMessage("capture", {'
        recheck_index = function_source.index(recheck)
        dispatch_index = function_source.index(dispatch, recheck_index)
        between = function_source[recheck_index + len(recheck):dispatch_index]
        self.assertNotIn("await ", between)
        self.assertIn("current.cleanupToken !== authorization.cleanupToken", between)
        self.assertIn("current.guardEpoch !== captureGuardEpoch", between)
        self.assertIn("result_text: text", function_source[dispatch_index:])


if __name__ == "__main__":
    unittest.main()
