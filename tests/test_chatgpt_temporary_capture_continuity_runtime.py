from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTINUITY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "capture_continuity.js"


class ChatGPTTemporaryCaptureContinuityRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def run_node(self, body: str) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert/strict");

let baseEpoch = 17;
let invalidations = 0;
let assistantText = "RESULT_A";
let stopPresent = false;
let observerCallback = null;

const assistantNode = {{
  nodeType: 1,
  innerText: assistantText,
  textContent: assistantText,
  matches(selector) {{ return selector.includes('data-message-author-role="assistant"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }},
  querySelector() {{ return null; }},
}};
const userNode = {{
  nodeType: 1,
  matches(selector) {{ return selector.includes('data-message-author-role="user"'); }},
  closest(selector) {{ return this.matches(selector) ? this : null; }},
  querySelector() {{ return null; }},
}};
const documentElement = {{ nodeType: 1, matches() {{ return false; }}, closest() {{ return null; }}, querySelector() {{ return null; }} }};

const policy = {{
  armPostDeliveryUiGuard() {{ return true; }},
  captureAuthorization() {{ return {{ cleanupToken: "a".repeat(64), guardEpoch: baseEpoch }}; }},
  invalidatePostDeliveryAuthorization() {{ invalidations += 1; baseEpoch += 1; return true; }},
}};

class FakeMutationObserver {{
  constructor(callback) {{ observerCallback = callback; }}
  observe() {{}}
}}

const context = {{
  console,
  MutationObserver: FakeMutationObserver,
  CAPChatGPTTemporaryPolicy: policy,
  document: {{
    documentElement,
    querySelector(selector) {{
      if (selector === 'button[data-testid="stop-button"]') return stopPresent ? {{}} : null;
      return null;
    }},
    querySelectorAll(selector) {{
      if (selector.includes('data-message-author-role="assistant"')) {{
        assistantNode.innerText = assistantText;
        assistantNode.textContent = assistantText;
        return [assistantNode];
      }}
      if (selector === "button") return [];
      return [];
    }},
  }},
}};
vm.createContext(context);
vm.runInContext(fs.readFileSync({json.dumps(str(CONTINUITY))}, "utf8"), context);

{body}
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_transient_relevant_mutation_advances_capture_epoch_even_if_state_restores(self) -> None:
        self.run_node(r'''
assert.equal(policy.armPostDeliveryUiGuard({}), true);
const before = policy.captureAuthorization();
assert.equal(before.guardEpoch, 17);
assert.equal(typeof observerCallback, "function");
observerCallback([{
  type: "childList",
  target: documentElement,
  addedNodes: [],
  removedNodes: [userNode],
}]);
const after = policy.captureAuthorization();
assert.equal(invalidations, 1);
assert.equal(after.guardEpoch, 18);
''')

    def test_synchronous_capture_recheck_rejects_changed_or_generating_assistant_result(self) -> None:
        self.run_node(r'''
assert.equal(policy.armPostDeliveryUiGuard({}), true);
const first = policy.captureAuthorization();
assert.equal(first.guardEpoch, 17);
assistantText = "RESULT_B";
const changed = policy.captureAuthorization();
assert.equal(changed, null);
assert.equal(invalidations, 1);
const fresh = policy.captureAuthorization();
assert.equal(fresh.guardEpoch, 18);
stopPresent = true;
const generating = policy.captureAuthorization();
assert.equal(generating, null);
assert.equal(invalidations, 2);
''')


if __name__ == "__main__":
    unittest.main()
