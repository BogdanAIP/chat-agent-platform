from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime.agent_sessions import chatgpt_temporary_controller as controller_module
from runtime.agent_sessions.chatgpt_temporary_controller import TemporaryControllerRuntime
from runtime.control_plane import delegation_state
from tests.test_chatgpt_temporary_controller import (
    EXECUTION_GENERATION,
    TASK,
    expected_runtime_attestation,
    identity_dict,
    runtime_report,
)


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "background.js"
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class PreflightCommitControllerCrashTests(unittest.TestCase):
    def test_restart_after_durable_launch_before_projection_reconstructs_reconcilable_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_root = root / "private-state"
            first_output = root / "first"
            runtime = TemporaryControllerRuntime(
                identity_value=identity_dict(),
                task=TASK,
                expected_runtime_attestation_value=expected_runtime_attestation(),
                state_root=state_root,
                output_dir=first_output,
            )
            assert runtime.preflight_id is not None
            request = {
                "schema_version": 1,
                "preflight_id": runtime.preflight_id,
                "execution_generation": EXECUTION_GENERATION,
                "runtime_attestation": runtime_report(),
            }
            prepared = runtime.prepare_live_handoff(request)
            commit = {**request, "launch_handle": prepared["launch_handle"]}

            real_atomic_write = controller_module._atomic_json_write
            failed = False

            def fail_first_launch_projection(path: Path, value: dict[str, object]) -> None:
                nonlocal failed
                if path.name == "launch.json" and not failed:
                    failed = True
                    raise OSError("simulated crash before launch projection")
                real_atomic_write(path, value)

            with patch.object(controller_module, "_atomic_json_write", side_effect=fail_first_launch_projection):
                with self.assertRaisesRegex(OSError, "simulated crash"):
                    runtime.commit_live_handoff(commit)

            snapshot = delegation_state.load_delegation(identity_dict(), state_root=state_root)
            self.assertEqual("launch-attempted", snapshot.launch_state)
            self.assertEqual("prepared", snapshot.delivery_state)
            self.assertEqual("open", snapshot.result_state)
            self.assertFalse((first_output / "launch.json").exists())

            restarted = TemporaryControllerRuntime(
                identity_value=identity_dict(),
                task=TASK,
                expected_runtime_attestation_value=expected_runtime_attestation(),
                state_root=state_root,
                output_dir=root / "restart",
            )
            self.assertEqual("ready", restarted.health()["status"])
            state = restarted.require_state()
            self.assertFalse(state.launch.launch_now)
            self.assertEqual(prepared["run_id"], state.token)
            status = state.status()
            self.assertEqual(prepared["delegation_id"], status["delegation_id"])
            self.assertEqual(prepared["delivery_id"], status["delivery_id"])
            self.assertEqual("launch-attempted", status["launch_state"])
            self.assertEqual("prepared", status["delivery_state"])
            self.assertEqual("open", status["result_state"])
            self.assertEqual(prepared["expected_runtime_head"], status["expected_runtime_head"])
            self.assertEqual(EXECUTION_GENERATION, status["execution_generation"])
            self.assertEqual(prepared["prompt_sha256"], status["prompt_sha256"])


class PreflightCommitBrowserRuntimeTests(unittest.TestCase):
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

    def test_commit_ack_loss_keeps_live_mapping_and_reconciles_one_navigation(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const generation = "9".repeat(64);
const preflightId = "1".repeat(64);
const launchHandle = "2".repeat(64);
const runId = "3".repeat(64);
const delegationId = "4".repeat(64);
const deliveryId = "5".repeat(64);
const taskSha = "6".repeat(64);
const head = "7".repeat(40);
const promptSha = "8".repeat(64);
const taskUrl = `https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=${{launchHandle}}`;
const sender = {{ url: `https://chatgpt.com/?cap_agent_preflight=1#cap_preflight_id=${{preflightId}}`, tab: {{ id: 17 }} }};

const context = {{
  console,
  URL,
  importScripts() {{}},
  CAPChatGPTTemporaryExecutionGeneration: generation,
  preflightId,
  launchHandle,
  runId,
  delegationId,
  deliveryId,
  taskSha,
  head,
  promptSha,
  taskUrl,
  sender,
  commitApplied: false,
  commitCalls: 0,
  statusCalls: 0,
  chrome: {{ runtime: {{
    onInstalled: {{ addListener() {{}} }},
    onStartup: {{ addListener() {{}} }},
    onMessage: {{ addListener() {{}} }},
  }} }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{ filename: "background.js" }});
vm.runInContext(`
  runtimeAttestation = async () => ({{ schema_version: 1, adapter_id: "chatgpt-temporary", execution_generation: generation, assets: {{}} }});
  preflightPost = async (id, path, body) => {{
    if (path === "/preflight") return {{
      schema_version: 1,
      status: "handoff-prepared",
      launch_handle: launchHandle,
      run_id: runId,
      delegation_id: delegationId,
      delivery_id: deliveryId,
      task_sha256: taskSha,
      expected_runtime_head: head,
      prompt_sha256: promptSha,
      launch_url: taskUrl,
    }};
    if (path === "/preflight-commit") {{
      commitCalls += 1;
      commitApplied = true;
      throw new Error("simulated-commit-ack-loss");
    }}
    throw new Error("unexpected-path:" + path);
  }};
  controllerStatusWithRun = async (_live) => {{
    statusCalls += 1;
    if (!commitApplied) throw new Error("not-committed");
    return {{
      schema_version: 1,
      status: "ready",
      delegation_id: delegationId,
      delivery_id: deliveryId,
      launch_state: "launch-attempted",
      delivery_state: "prepared",
      result_state: "open",
      expected_runtime_head: head,
      execution_generation: generation,
      prompt_sha256: promptSha,
    }};
  }};
`, context);

(async () => {{
  const response = await vm.runInContext("prepareLiveLaunch(preflightId, sender)", context);
  if (response.ok !== true || response.status !== "preflight-navigation-ready") process.exit(10);
  if (response.navigate_url !== taskUrl) process.exit(11);
  if (context.commitCalls !== 1 || context.statusCalls !== 1) process.exit(12);
  if (vm.runInContext("LIVE_LAUNCHES.size", context) !== 1) process.exit(13);
  if (vm.runInContext("LIVE_LAUNCHES.get(launchHandle).commit_state", context) !== "committed") process.exit(14);
  if (vm.runInContext("LIVE_LAUNCHES.get(launchHandle).owner_tab_id", context) !== 17) process.exit(15);
}})().catch((error) => {{ console.error(error); process.exit(20); }});
"""
        self.run_node(script)

    def test_restart_after_commit_uses_surviving_owner_status_without_recommit(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const generation = "9".repeat(64);
const preflightId = "1".repeat(64);
const launchHandle = "2".repeat(64);
const runId = "3".repeat(64);
const delegationId = "4".repeat(64);
const deliveryId = "5".repeat(64);
const taskSha = "6".repeat(64);
const head = "7".repeat(40);
const promptSha = "8".repeat(64);
const taskUrl = `https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=${{launchHandle}}`;
const sender = {{ url: `https://chatgpt.com/?cap_agent_preflight=1#cap_preflight_id=${{preflightId}}`, tab: {{ id: 17 }} }};
const context = {{
  console, URL, importScripts() {{}}, CAPChatGPTTemporaryExecutionGeneration: generation,
  preflightId, launchHandle, runId, delegationId, deliveryId, taskSha, head, promptSha, taskUrl, sender,
  commitCalls: 0,
  chrome: {{ runtime: {{ onInstalled: {{ addListener() {{}} }}, onStartup: {{ addListener() {{}} }}, onMessage: {{ addListener() {{}} }} }} }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{ filename: "background.js" }});
vm.runInContext(`
  LIVE_LAUNCHES.set(launchHandle, {{
    run_id: runId,
    delegation_id: delegationId,
    delivery_id: deliveryId,
    task_sha256: taskSha,
    expected_runtime_head: head,
    prompt_sha256: promptSha,
    launch_url: taskUrl,
    owner_tab_id: 17,
    preflight_id: preflightId,
    commit_state: "ambiguous",
  }});
  controllerStatusWithRun = async (_live) => ({{
    schema_version: 1,
    status: "ready",
    delegation_id: delegationId,
    delivery_id: deliveryId,
    launch_state: "launch-attempted",
    delivery_state: "prepared",
    result_state: "open",
    expected_runtime_head: head,
    execution_generation: generation,
    prompt_sha256: promptSha,
  }});
  preflightPost = async () => {{ commitCalls += 1; throw new Error("recommit-forbidden"); }};
`, context);
(async () => {{
  const response = await vm.runInContext("prepareLiveLaunch(preflightId, sender)", context);
  if (response.ok !== true || response.status !== "preflight-navigation-ready") process.exit(30);
  if (response.navigate_url !== taskUrl) process.exit(31);
  if (context.commitCalls !== 0) process.exit(32);
  if (vm.runInContext("LIVE_LAUNCHES.get(launchHandle).owner_tab_id", context) !== 17) process.exit(33);
}})().catch((error) => {{ console.error(error); process.exit(40); }});
"""
        self.run_node(script)

    def test_restart_before_commit_rebinds_new_handle_without_transferring_navigation_owner(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const generation = "9".repeat(64);
const oldPreflight = "1".repeat(64);
const newPreflight = "2".repeat(64);
const oldHandle = "3".repeat(64);
const newHandle = "4".repeat(64);
const runId = "5".repeat(64);
const delegationId = "6".repeat(64);
const deliveryId = "7".repeat(64);
const taskSha = "8".repeat(64);
const head = "9".repeat(40);
const promptSha = "a".repeat(64);
const oldUrl = `https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=${{oldHandle}}`;
const newUrl = `https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=${{newHandle}}`;
const oldOwner = {{ url: `https://chatgpt.com/?cap_agent_preflight=1#cap_preflight_id=${{oldPreflight}}`, tab: {{ id: 17 }} }};
const newTab = {{ url: `https://chatgpt.com/?cap_agent_preflight=1#cap_preflight_id=${{newPreflight}}`, tab: {{ id: 18 }} }};
const context = {{
  console, URL, importScripts() {{}}, CAPChatGPTTemporaryExecutionGeneration: generation,
  oldPreflight, newPreflight, oldHandle, newHandle, runId, delegationId, deliveryId, taskSha, head, promptSha,
  oldUrl, newUrl, oldOwner, newTab,
  commitCalls: [],
  chrome: {{ runtime: {{ onInstalled: {{ addListener() {{}} }}, onStartup: {{ addListener() {{}} }}, onMessage: {{ addListener() {{}} }} }} }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(source, context, {{ filename: "background.js" }});
vm.runInContext(`
  LIVE_LAUNCHES.set(oldHandle, {{
    run_id: runId,
    delegation_id: delegationId,
    delivery_id: deliveryId,
    task_sha256: taskSha,
    expected_runtime_head: head,
    prompt_sha256: promptSha,
    launch_url: oldUrl,
    owner_tab_id: 17,
    preflight_id: oldPreflight,
    commit_state: "prepared",
  }});
  runtimeAttestation = async () => ({{ schema_version: 1, adapter_id: "chatgpt-temporary", execution_generation: generation, assets: {{}} }});
  preflightPost = async (id, path, body) => {{
    if (path === "/preflight") return {{
      schema_version: 1,
      status: "handoff-prepared",
      launch_handle: newHandle,
      run_id: runId,
      delegation_id: delegationId,
      delivery_id: deliveryId,
      task_sha256: taskSha,
      expected_runtime_head: head,
      prompt_sha256: promptSha,
      launch_url: newUrl,
    }};
    if (path === "/preflight-commit") {{
      commitCalls.push({{ id, launch_handle: body.launch_handle }});
      return {{
        schema_version: 1,
        status: "launch-committed",
        delegation_id: delegationId,
        delivery_id: deliveryId,
        launch_state: "launch-attempted",
      }};
    }}
    throw new Error("unexpected-path:" + path);
  }};
`, context);
(async () => {{
  const nonOwner = await vm.runInContext("prepareLiveLaunch(newPreflight, newTab)", context);
  if (nonOwner.ok !== true || nonOwner.status !== "preflight-owned-by-other-tab") process.exit(50);
  if (Object.prototype.hasOwnProperty.call(nonOwner, "navigate_url")) process.exit(51);
  if (vm.runInContext("LIVE_LAUNCHES.has(oldHandle)", context)) process.exit(52);
  if (!vm.runInContext("LIVE_LAUNCHES.has(newHandle)", context)) process.exit(53);
  if (vm.runInContext("LIVE_LAUNCHES.get(newHandle).owner_tab_id", context) !== 17) process.exit(54);
  if (vm.runInContext("LIVE_LAUNCHES.get(newHandle).preflight_id", context) !== newPreflight) process.exit(55);

  const owner = await vm.runInContext("prepareLiveLaunch(oldPreflight, oldOwner)", context);
  if (owner.ok !== true || owner.status !== "preflight-navigation-ready") process.exit(56);
  if (owner.navigate_url !== newUrl) process.exit(57);
  if (context.commitCalls.length !== 1) process.exit(58);
  if (context.commitCalls[0].id !== newPreflight || context.commitCalls[0].launch_handle !== newHandle) process.exit(59);
}})().catch((error) => {{ console.error(error); process.exit(60); }});
"""
        self.run_node(script)

    def test_preflight_content_navigates_only_after_exact_navigation_ready_proof(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8");
const generation = "9".repeat(64);
const preflightId = "1".repeat(64);
const launchHandle = "2".repeat(64);
const delegationId = "3".repeat(64);
const deliveryId = "4".repeat(64);
const target = `https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=${{launchHandle}}`;
let intervalFn = null;
let calls = 0;
const replacements = [];

const policy = {{
  HEX64_RE: /^[0-9a-f]{{64}}$/,
  HEAD40_RE: /^[0-9a-f]{{40}}$/,
  parseIntent(url) {{
    if (url === target) return {{ enabled: true, delegationId, deliveryId }};
    return {{ enabled: false }};
  }},
}};

global.CAPChatGPTTemporaryPolicy = policy;
global.CAPChatGPTTemporaryExecutionGeneration = generation;
global.location = {{
  href: `https://chatgpt.com/?cap_agent_preflight=1#cap_preflight_id=${{preflightId}}`,
  origin: "https://chatgpt.com",
  replace(next) {{ replacements.push(next); this.href = next; }},
}};
global.document = {{ querySelectorAll() {{ return []; }} }};
global.chrome = {{ runtime: {{
  lastError: null,
  sendMessage(message, callback) {{
    if (message.kind !== "resume-intent") throw new Error("unexpected-message:" + message.kind);
    calls += 1;
    if (calls === 1) {{
      callback({{ ok: false, status: "preflight-commit-unresolved", execution_generation: generation }});
      return;
    }}
    callback({{
      ok: true,
      status: "preflight-navigation-ready",
      execution_generation: generation,
      navigate_url: target,
      delegation_id: delegationId,
      delivery_id: deliveryId,
    }});
  }},
}} }};
global.setInterval = (fn, _ms) => {{ intervalFn = fn; return 1; }};
global.clearInterval = (_id) => {{}};

function flush() {{ return new Promise((resolve) => setImmediate(resolve)); }}

(async () => {{
  vm.runInThisContext(source, {{ filename: "content.js" }});
  await flush();
  await flush();
  if (replacements.length !== 0) process.exit(70);
  if (typeof intervalFn !== "function") process.exit(71);
  intervalFn();
  await flush();
  await flush();
  if (replacements.length !== 1 || replacements[0] !== target) process.exit(72);
}})().catch((error) => {{ console.error(error); process.exit(80); }});
"""
        self.run_node(script)


if __name__ == "__main__":
    unittest.main()
