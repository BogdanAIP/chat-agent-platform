from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "background.js"


class ChatGPTTemporaryPromptHandoffRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_prompt_handoff_is_owner_tab_bound_and_one_shot(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const assert = require("assert/strict");

let source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
source += "\\nglobalThis.__capPromptHandoffTest = {{ LIVE_LAUNCHES }};";

const executionGeneration = "1".repeat(64);
const launchHandle = "2".repeat(64);
const privateRunId = "3".repeat(64);
const delegationId = "4".repeat(64);
const deliveryId = "5".repeat(64);
const taskSha = "6".repeat(64);
const expectedHead = "7".repeat(40);
const reviewRunId = "8".repeat(64);
const prompt = [
  "WORKER_TASK_V1",
  "delegation_id=" + delegationId,
  "delivery_id=" + deliveryId,
  "worker_kind=code-review",
  "worker_profile=fresh_readonly_worker_v1",
  "result_contract_id=review_result_v1",
  "task_sha256=" + taskSha,
  "",
  "TASK_BEGIN:" + taskSha,
  "REVIEW_REQUEST_V1",
  "review_run_id=" + reviewRunId,
  "TASK_END:" + taskSha,
  "",
  "CAP_WORKER_RESULT_V1_BEGIN",
  "{{}}",
  "CAP_WORKER_RESULT_V1_END",
].join("\\n");
const promptSha = nodeCrypto.createHash("sha256").update(prompt, "utf8").digest("hex");
const taskUrl = "https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1" +
  "&cap_delegation_id=" + delegationId +
  "&cap_delivery_id=" + deliveryId +
  "&cap_task_sha256=" + taskSha +
  "&cap_expected_head=" + expectedHead +
  "&cap_prompt_sha256=" + promptSha +
  "#cap_run_id=" + launchHandle;

let onMessage = null;
const context = {{
  console,
  URL,
  TextEncoder,
  crypto: nodeCrypto.webcrypto,
  importScripts() {{}},
  CAPChatGPTTemporaryExecutionGeneration: executionGeneration,
  fetch() {{ throw new Error("network access is not expected in prompt-handoff test"); }},
  chrome: {{
    runtime: {{
      onInstalled: {{addListener() {{}}}},
      onStartup: {{addListener() {{}}}},
      onMessage: {{addListener(fn) {{ onMessage = fn; }}}},
      getURL(name) {{ return "chrome-extension://test/" + name; }},
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{filename: "background.js"}});
assert.equal(typeof onMessage, "function");

context.__capPromptHandoffTest.LIVE_LAUNCHES.set(launchHandle, {{
  run_id: privateRunId,
  delegation_id: delegationId,
  delivery_id: deliveryId,
  task_sha256: taskSha,
  expected_runtime_head: expectedHead,
  prompt_sha256: promptSha,
  prompt,
  prompt_claimed: false,
  launch_url: taskUrl,
  owner_tab_id: 41,
  preflight_id: "9".repeat(64),
  commit_state: "committed",
}});

const incoming = {{
  schema_version: 1,
  kind: "task-prompt",
  run_id: launchHandle,
  delegation_id: delegationId,
  delivery_id: deliveryId,
  task_sha256: taskSha,
  expected_runtime_head: expectedHead,
  prompt_sha256: promptSha,
  execution_generation: executionGeneration,
}};

function send(sender) {{
  return new Promise((resolve, reject) => {{
    let settled = false;
    const returned = onMessage(incoming, sender, (value) => {{
      settled = true;
      resolve(value);
    }});
    if (returned !== true && !settled) reject(new Error("listener did not keep or answer the message channel"));
  }});
}}

(async () => {{
  const wrongTab = await send({{url: taskUrl, tab: {{id: 99, url: taskUrl}}}});
  assert.equal(wrongTab.ok, false);
  assert.equal(wrongTab.reason, "prompt-owner-tab-mismatch");

  const wrongUrl = await send({{url: "https://chatgpt.com/", tab: {{id: 41, url: "https://chatgpt.com/"}}}});
  assert.equal(wrongUrl.ok, false);
  assert.equal(wrongUrl.reason, "prompt-sender-url-mismatch");

  const first = await send({{url: taskUrl, tab: {{id: 41, url: taskUrl}}}});
  assert.equal(first.ok, true);
  assert.equal(first.prompt, prompt);
  assert.equal(first.prompt_sha256, promptSha);
  assert.ok(first.prompt.includes(reviewRunId));
  assert.equal(Object.prototype.hasOwnProperty.call(first, "run_id"), false);

  const second = await send({{url: taskUrl, tab: {{id: 41, url: taskUrl}}}});
  assert.equal(second.ok, false);
  assert.equal(second.reason, "prompt-handoff-expired");

  const live = context.__capPromptHandoffTest.LIVE_LAUNCHES.get(launchHandle);
  assert.equal(live.prompt_claimed, true);
  assert.equal(live.prompt, "");
}})().catch(error => {{ console.error(error); process.exit(1); }});
"""
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


if __name__ == "__main__":
    unittest.main()
