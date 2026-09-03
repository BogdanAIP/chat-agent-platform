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

    def test_draft_restoration_seen_by_capture_requires_new_uninterrupted_clean_interval(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");

const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const expectedHead = "e".repeat(40);
const promptSha = "f".repeat(64);
const cleanupToken = "1".repeat(64);
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
launch.searchParams.set("cap_expected_head", expectedHead);
launch.searchParams.set("cap_prompt_sha256", promptSha);
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
global.CAPChatGPTTemporaryExecutionGeneration = "2".repeat(64);
global.chrome = {{ runtime: {{ sendMessage(_message, callback) {{ callback({{ ok: true, cleanup_token: cleanupToken }}); }} }} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};
Date.now = () => now;

vm.runInThisContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), {{ filename: "policy.js" }});
const intent = CAPChatGPTTemporaryPolicy.parseIntent(launch.toString());
if (!intent.enabled) process.exit(9);
if (!CAPChatGPTTemporaryPolicy.armPostDeliveryUiGuard(intent)) process.exit(10);
if (typeof intervalFn !== "function") process.exit(11);

// Begin and complete the first uninterrupted clean interval.
intervalFn();
now = 9501;
intervalFn();
if (!CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(12);

// Restore the exact bound draft without giving the 500 ms poll another turn.
// The synchronous capture path sees it and must invalidate the old ACK/token.
editor.textContent = prompt;
editor.innerText = prompt;
if (CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(13);

// Clearing immediately is not enough: the old ACK/token is no longer authoritative.
editor.textContent = "";
editor.innerText = "";
if (CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(14);

// A new clean interval begins only when the guard observes clean state again.
now = 9600;
intervalFn();
now = 17599;
intervalFn();
if (CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(15);

// Only after a fresh >8-second uninterrupted interval and ACK may capture reopen.
now = 17601;
intervalFn();
if (!CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(16);
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
