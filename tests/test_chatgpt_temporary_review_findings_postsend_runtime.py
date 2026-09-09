from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
POLICY = EXTENSION / "policy.js"
CONTENT = EXTENSION / "content.js"


class ChatGPTTemporaryPostSendReviewFindingsRuntimeTests(unittest.TestCase):
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

    def test_post_send_correlation_is_exact_line_bounded_and_ambiguity_rejecting(self) -> None:
        script = rf"""
const fs = require("fs");
const vm = require("vm");
const policySource = fs.readFileSync({json.dumps(str(POLICY))}, "utf8");

const delegationId = "a".repeat(64);
const deliveryId = "b".repeat(64);
const taskSha = "c".repeat(64);
const intent = {{ delegationId, deliveryId, taskSha256: taskSha }};
const base = [
  "WORKER_TASK_V1",
  `delegation_id=${{delegationId}}`,
  `delivery_id=${{deliveryId}}`,
  `task_sha256=${{taskSha}}`,
  `TASK_BEGIN:${{taskSha}}`,
  "Do one bounded task.",
  `TASK_END:${{taskSha}}`,
].join("\n");
let userNodes = [];
const context = {{
  console,
  getComputedStyle() {{ return {{visibility: "visible", display: "block", opacity: "1"}}; }},
  document: {{
    querySelectorAll(selector) {{
      if (selector.includes('data-message-author-role="user"')) return userNodes;
      return [];
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(policySource, context, {{ filename: "policy.js" }});
const policy = context.CAPChatGPTTemporaryPolicy;
if (!policy || typeof policy.hasExpectedPrompt !== "function") process.exit(70);
const node = (text) => ({{ innerText: text, textContent: text, isConnected: true,
  getBoundingClientRect() {{ return {{width: 500, height: 80}}; }} }});
const proves = (text, nodes = [text]) => {{
  userNodes = nodes.map(node);
  return policy.hasExpectedPrompt(text, intent);
}};

if (!proves(base + "\nРазвернуть")) process.exit(71);
if (!proves(base + "\nExpand")) process.exit(72);
if (proves(base.replace(`delivery_id=${{deliveryId}}`, `delivery_id=${{deliveryId}}suffix`))) process.exit(73);
if (proves(base.replace(`delivery_id=${{deliveryId}}`, `xdelivery_id=${{deliveryId}}`))) process.exit(74);
if (proves(base.replace(`delivery_id=${{deliveryId}}`, `delivery_id=${{deliveryId}}\ndelivery_id=${{deliveryId}}`))) process.exit(75);
if (proves(base.replace(`task_sha256=${{taskSha}}\n`, ""))) process.exit(76);
if (proves(base.replace("WORKER_TASK_V1", "prefix-WORKER_TASK_V1"))) process.exit(77);
if (proves(base.replace(`TASK_BEGIN:${{taskSha}}\n`, ""))) process.exit(81);
if (proves(base.replace(`\nTASK_END:${{taskSha}}`, ""))) process.exit(82);

const malformed = base.replace(`delivery_id=${{deliveryId}}`, `delivery_id=${{deliveryId}}suffix`);
if (proves(base, [base, malformed])) process.exit(78);
if (proves(base, [base, base])) process.exit(79);
if (!proves(base, ["ordinary unrelated user text", base + "\nExpand"])) process.exit(80);
"""
        self.run_node(script)

    def test_post_delivery_composer_guard_rejects_hidden_stale_and_multiple_live_editors(self) -> None:
        script = rf"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(POLICY))}, "utf8").replace(/\r\n?/g, "\n");
const start = source.indexOf("  function guardEditorText(editor) {{");
const end = source.indexOf("\n\n  function guardLaunchUrlClean()", start);
if (start < 0 || end <= start) process.exit(70);
const snippet =
  "function hasExpectedPrompt() {{ return false; }}\n" +
  source.slice(start, end) +
  "\nthis.guardComposerState = guardComposerState;";

const form = {{
  isConnected: true,
  getBoundingClientRect() {{ return {{ width: 500, height: 100 }}; }},
}};
function editor({{ text = "", visible = true, ariaHidden = false, disabled = false, formOwner = form }}) {{
  return {{
    isConnected: true,
    tagName: "DIV",
    isContentEditable: true,
    innerText: text,
    textContent: text,
    disabled,
    getBoundingClientRect() {{ return visible ? {{ width: 400, height: 60 }} : {{ width: 0, height: 0 }}; }},
    getAttribute(name) {{
      if (name === "aria-hidden") return ariaHidden ? "true" : null;
      if (name === "contenteditable") return "true";
      if (name === "aria-disabled") return disabled ? "true" : null;
      return null;
    }},
    closest(selector) {{ return selector === "form" ? formOwner : null; }},
  }};
}}

let primary = null;
let editors = [];
const context = {{
  console,
  getComputedStyle(node) {{ return {{ visibility: "visible", display: "block", opacity: "1" }}; }},
  document: {{
    querySelector(selector) {{ return selector === "#prompt-textarea" ? primary : null; }},
    querySelectorAll() {{ return editors; }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(snippet, context, {{ filename: "composer-guard-snippet.js" }});
const state = () => context.guardComposerState({{}});

const hiddenStale = editor({{ text: "", visible: false }});
const activeDirty = editor({{ text: "UNSAFE ACTIVE COMPOSER" }});
primary = hiddenStale;
editors = [hiddenStale, activeDirty];
if (state().clean !== false || state().editor !== activeDirty) process.exit(71);
const activeEmpty = editor({{ text: "" }});
editors = [hiddenStale, activeEmpty];
if (state().clean !== true || state().editor !== activeEmpty) process.exit(72);
const secondLive = editor({{ text: "" }});
primary = activeEmpty;
editors = [activeEmpty, secondLive];
if (state().clean !== false || state().editor !== null) process.exit(73);
const hiddenOnly = editor({{ text: "", ariaHidden: true }});
primary = hiddenOnly;
editors = [hiddenOnly];
if (state().clean !== false || state().editor !== null) process.exit(74);
const ownerless = editor({{ text: "", formOwner: null }});
primary = ownerless;
editors = [ownerless];
if (state().clean !== false || state().editor !== null) process.exit(75);
"""
        self.run_node(script)

    def test_existing_one_send_and_pre_send_exactness_are_unchanged(self) -> None:
        content = CONTENT.read_text(encoding="utf-8")
        self.assertEqual(1, content.count("button.click();"))
        exact = content[
            content.index("function exactComposerPromptMatches") :
            content.index("function launchIntentState")
        ]
        self.assertIn("policy.exactPromptMatches(observed, intent.prompt)", exact)
        send = content[
            content.index("if (sendAuthorized && !sendClickedAt)") :
            content.index("if (!sendClickedAt) return")
        ]
        self.assertIn("exactComposerPromptMatches(composer)", send)
        self.assertLess(send.index("exactComposerPromptMatches(composer)"), send.index("button.click();"))


if __name__ == "__main__":
    unittest.main()
