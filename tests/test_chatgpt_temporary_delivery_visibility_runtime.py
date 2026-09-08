from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
CONTENT = EXTENSION / "content.js"
POLICY = EXTENSION / "policy.js"


class ChatGPTTemporaryDeliveryVisibilityRuntimeTests(unittest.TestCase):
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

    def test_provider_decorated_user_turn_still_proves_correlated_delivery(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const contentSource = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8").replace(/\\r\\n?/g, "\\n");
const policySource = fs.readFileSync({json.dumps(str(POLICY))}, "utf8");

const normalizeStart = contentSource.indexOf("  function normalizeFull(text) {{");
const normalizeEnd = contentSource.indexOf("\\n\\n  function observedRecoveryClaims()", normalizeStart);
const turnsStart = contentSource.indexOf("    function conversationTurns(role) {{");
const turnsEnd = contentSource.indexOf("\\n\\n    function stopButtonPresent()", turnsStart);
if (normalizeStart < 0 || normalizeEnd <= normalizeStart || turnsStart < 0 || turnsEnd <= turnsStart) process.exit(70);

const snippet =
  contentSource.slice(normalizeStart, normalizeEnd) + "\\n" +
  contentSource.slice(turnsStart, turnsEnd) +
  "\\nthis.deliveryVisible = userDeliveryVisible;";

const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const prompt = [
  "WORKER_TASK_V1",
  `delegation_id=${{delegationId}}`,
  `delivery_id=${{deliveryId}}`,
  `task_sha256=${{taskSha}}`,
  `TASK_BEGIN:${{taskSha}}`,
  "Do one bounded task.",
  `TASK_END:${{taskSha}}`,
].join("\\n");
let userText = prompt + "\\nРазвернуть";

const context = {{
  console,
  getComputedStyle() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }},
  recovered: false,
  intent: {{ prompt, delegationId, deliveryId, taskSha256: taskSha }},
  document: {{
    querySelectorAll(selector) {{
      if (selector.includes('data-message-author-role="user"')) {{
        return [{{ innerText: userText, textContent: userText, isConnected: true,
          getBoundingClientRect() {{ return {{width: 500, height: 80}}; }} }}];
      }}
      return [];
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(policySource, context, {{ filename: "policy.js" }});
context.policy = context.CAPChatGPTTemporaryPolicy;
vm.runInContext(snippet, context, {{ filename: "delivery-visibility-snippet.js" }});

if (typeof context.deliveryVisible !== "function") process.exit(71);
if (context.deliveryVisible() !== true) process.exit(72);
userText = userText.replace(`delivery_id=${{deliveryId}}`, `delivery_id=${{"e".repeat(64)}}`);
if (context.deliveryVisible() !== false) process.exit(73);
userText = prompt + "\\nExpand";
context.recovered = true;
if (context.deliveryVisible() !== false) process.exit(74);
"""
        self.run_node(script)

    def test_post_send_visibility_uses_markers_without_weakening_pre_send_exactness(self) -> None:
        source = CONTENT.read_text(encoding="utf-8")
        delivery = source[
            source.index("    function userDeliveryVisible()") :
            source.index("    function stopButtonPresent()")
        ]
        exact = source[
            source.index("    function exactComposerPromptMatches(composer)") :
            source.index("    function launchIntentState()")
        ]
        self.assertIn("policy.hasExpectedPrompt(text, intent)", delivery)
        self.assertNotIn("policy.exactPromptMatches", delivery)
        self.assertIn("policy.exactPromptMatches(observed, intent.prompt)", exact)
        self.assertEqual(1, source.count("button.click();"))


if __name__ == "__main__":
    unittest.main()
