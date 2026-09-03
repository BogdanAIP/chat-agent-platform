from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


class RecoveredGuardRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_cleaned_url_reload_requires_explicit_rearm_before_capture(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");

const runId = "a".repeat(64);
const delegationId = "b".repeat(64);
const deliveryId = "c".repeat(64);
const taskSha = "d".repeat(64);
const result = "CAP_WORKER_RESULT_V1_BEGIN\\n{{}}\\nCAP_WORKER_RESULT_V1_END";
let href = "https://chatgpt.com/c/recovered-session-1234";
let now = 1000;
let intervalFn = null;
const editor = {{ textContent: "", innerText: "" }};
const userTurn = {{
  innerText: `delegation_id=${{delegationId}}\\ndelivery_id=${{deliveryId}}\\ntask_sha256=${{taskSha}}`,
  textContent: "",
}};

global.location = {{ get href() {{ return href; }} }};
global.history = {{ state: null, replaceState(_state, _title, next) {{ href = new URL(next, href).toString(); }} }};
global.document = {{
  querySelector(selector) {{ return selector === "#prompt-textarea" ? editor : null; }},
  querySelectorAll(selector) {{ return selector.includes('data-message-author-role="user"') ? [userTurn] : []; }},
}};
global.CAPChatGPTTemporaryExecutionGeneration = "e".repeat(64);
global.chrome = {{ runtime: {{ sendMessage(_message, callback) {{ callback({{ ok: true }}); }} }} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};
Date.now = () => now;

vm.runInThisContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), {{ filename: "policy.js" }});

// A cleaned URL contains no launch intent, so browser capture must fail closed
// until content.js supplies its authenticated resume-intent to the same guard.
if (CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(10);
const recovered = {{ runId, delegationId, deliveryId, taskSha256: taskSha }};
if (!CAPChatGPTTemporaryPolicy.armPostDeliveryUiGuard(recovered)) process.exit(11);
if (typeof intervalFn !== "function") process.exit(12);
if (CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(13);

intervalFn();
now = 9501;
intervalFn();
if (!CAPChatGPTTemporaryPolicy.hasSingleResultBlock(result)) process.exit(14);
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
