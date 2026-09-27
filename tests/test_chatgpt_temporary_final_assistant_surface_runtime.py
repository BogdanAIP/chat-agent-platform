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


class ChatGPTTemporaryFinalAssistantSurfaceRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def run_helper(self, source_path: Path) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(source_path))}, "utf8").replace(/\\r\\n?/g, "\\n");
const start = source.indexOf("function conversationTurnNodes(role) {{");
if (start < 0) process.exit(70);
const end = source.indexOf("\\n  function ", start + 1);
if (end <= start) process.exit(71);
const helper = source.slice(start, end) + "\\nthis.turnNodes = conversationTurnNodes;";

const result = [
  "CAP_WORKER_RESULT_V1_BEGIN",
  "{{\\"schema_version\\":1}}",
  "CAP_WORKER_RESULT_V1_END",
].join("\\n");
const owner = {{}};
const broad = {{
  innerText: "Thought for 12s\\n" + result + "\\nCopy",
  textContent: "Thought for 12s\\n" + result + "\\nCopy",
  closest(selector) {{ return selector === '[data-turn-key]' ? owner : null; }},
}};
const finalNode = {{
  innerText: result,
  textContent: result,
  closest(selector) {{ return selector === '[data-turn-key]' ? owner : null; }},
}};

const context = {{
  document: {{
    querySelectorAll(selector) {{
      if (selector === '[data-local-conversation-final-assistant]') return [finalNode];
      if (selector === '[data-conversation-role="assistant"]') return [broad];
      if (selector.startsWith('[data-turn-key]:has(')) return [owner];
      return [];
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(helper, context, {{ filename: "turn-helper.js" }});
const nodes = context.turnNodes("assistant");
if (nodes.length !== 1) process.exit(72);
if (nodes[0] !== finalNode) process.exit(73);
if ((nodes[0].innerText || "").trim() !== result) process.exit(74);
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_content_prefers_final_assistant_surface_inside_grouped_turn(self) -> None:
        self.run_helper(CONTENT)

    def test_policy_prefers_final_assistant_surface_inside_grouped_turn(self) -> None:
        self.run_helper(POLICY)

    def test_final_surface_precedes_broad_assistant_surfaces(self) -> None:
        for source_path in (CONTENT, POLICY):
            source = source_path.read_text(encoding="utf-8")
            start = source.index("function conversationTurnNodes(role)")
            helper = source[start : source.index("\n  function ", start + 1)]
            self.assertLess(
                helper.index("'[data-local-conversation-final-assistant]'"),
                helper.index("'[data-conversation-role=\"assistant\"]'"),
            )


if __name__ == "__main__":
    unittest.main()
