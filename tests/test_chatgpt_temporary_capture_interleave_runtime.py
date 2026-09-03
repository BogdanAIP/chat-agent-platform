from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


class CaptureInterleaveRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_draft_restoration_between_polls_closes_result_gate_immediately(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");

const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const prompt = [
  "WORKER_TASK_V1",
  `delegation_id=${{delegationId}}`,
  `delivery_id=${{deliveryId}}`,
  `task_sha256=${{taskSha}}`,
  "CAP_WORKER_RESULT_V1_BEGIN",
  "CAP_WORKER_RESULT_V1_END",
].join("\\n");
const result = "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END";

const launch = new URL("https://chatgpt.com/");
launch.searchParams.set("temporary-chat", "true");
launch.searchParams.set("cap_agent_delegate", "1");
launch.searchParams.set("cap_delegation_id", delegationId);
launch.searchParams.set("cap_delivery_id", deliveryId);
launch.searchParams.set("cap_task_sha256", taskSha);
launch.searchParams.set("prompt", prompt);
launch.hash = `cap_run_id=${{runId}}`;
let href = launch.toString();
let now = 1000;
let intervalFn = null;

const editor = {{ textContent: "", innerText: "" }};
const userTurn = {{
  innerText: `delegation_id=${{delegationId}}\\ndelivery_id=${{deliveryId}}\\ntask_sha256=${{taskSha}}`,
  textContent: "",
}};

global.location = {{ get href() {{ return href; }} }};
global.history = {{
  state: null,
  replaceState(_state, _title, next) {{ href = new URL(next, href).toString(); }},
}};
global.document = {{
  querySelector(selector) {{
    if (selector === "#prompt-textarea") return editor;
    return null;
  }},
  querySelectorAll(selector) {{
    if (selector.includes('data-message-author-role="user"')) return [userTurn];
    return [];
  }},
}};
global.chrome = {{ runtime: {{ sendMessage(_message, callback) {{ callback({{ ok: true }}); }} }} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};
Date.now = () => now;

vm.runInThisContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), {{ filename: "policy.js" }});
if (typeof intervalFn !== "function") process.exit(10);

// First observation sanitizes the launch URL and begins the stable-clean interval.
intervalFn();
now = 9501;
// More than 8 seconds later, the controller ACK is simulated synchronously.
intervalFn();
if (!CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(11);

// Restore the exact bound draft without giving the 500 ms poll another turn.
editor.textContent = prompt;
editor.innerText = prompt;
if (CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(12);

// Cleaning the composer again permits the gate only because current DOM is clean.
editor.textContent = "";
editor.innerText = "";
if (!CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(13);
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
