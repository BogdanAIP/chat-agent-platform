from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
EXECUTION_GENERATION = EXTENSION / "execution_generation.js"
BACKGROUND = EXTENSION / "background.js"


class ChatGPTTemporaryExtensionLoopbackAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def run_node(self, script: str) -> dict[str, object]:
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        return json.loads(completed.stdout)

    def test_fake_loopback_listener_cannot_supply_preflight_status_or_send_authority(self) -> None:
        script = f"""
const fs = require("fs");
const vm = require("vm");
const nodeCrypto = require("crypto");
const executionSource = fs.readFileSync({json.dumps(str(EXECUTION_GENERATION))}, "utf8");
const backgroundSource = fs.readFileSync({json.dumps(str(BACKGROUND))}, "utf8");
const preflightId = "1".repeat(64);
const runId = "2".repeat(64);
const launchHandle = "3".repeat(64);
const delegationId = "4".repeat(64);
const deliveryId = "5".repeat(64);
const taskSha = "6".repeat(64);
const head = "7".repeat(40);
const promptSha = "8".repeat(64);
const controllerOrigin = "http://127.0.0.1:3078";
const captured = [];

function fakeControllerBody(path) {{
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
    launch_url: `https://chatgpt.com/?temporary-chat=true&cap_agent_delegate=1#cap_run_id=${{launchHandle}}`,
  }};
  if (path === "/status") return {{
    schema_version: 1,
    status: "ready",
    delegation_id: delegationId,
    delivery_id: deliveryId,
    launch_state: "launch-attempted",
    delivery_state: "prepared",
    result_state: "open",
    expected_runtime_head: head,
    execution_generation: "9".repeat(64),
    prompt_sha256: promptSha,
  }};
  if (path === "/authorize-send") return {{
    schema_version: 1,
    status: "send-authorized",
    send_authorized: true,
    delivery_state: "claimed",
  }};
  return {{ schema_version: 1, status: "ok" }};
}}

async function nativeFetch(input, init = {{}}) {{
  const url = new URL(input instanceof Request ? input.url : String(input));
  if (url.origin !== controllerOrigin) {{
    return new Response("exact-extension-asset", {{ status: 200 }});
  }}
  const headers = new Headers(init.headers || {{}});
  captured.push({{
    path: url.pathname,
    method: String(init.method || "GET").toUpperCase(),
    headers: Object.fromEntries(headers.entries()),
    body: init.body === undefined ? null : String(init.body),
  }});
  return new Response(JSON.stringify(fakeControllerBody(url.pathname)), {{
    status: 200,
    headers: {{ "Content-Type": "application/json" }},
  }});
}}

const context = {{
  console,
  URL,
  URLSearchParams,
  Headers,
  Request,
  Response,
  TextEncoder,
  crypto: nodeCrypto.webcrypto,
  fetch: nativeFetch,
  captured,
  preflightId,
  runId,
  launchHandle,
  delegationId,
  deliveryId,
  taskSha,
  head,
  promptSha,
  controllerOrigin,
  importScripts() {{}},
  chrome: {{
    runtime: {{
      getURL(name) {{ return `chrome-extension://cap/${{name}}`; }},
      onInstalled: {{ addListener() {{}} }},
      onStartup: {{ addListener() {{}} }},
      onMessage: {{ addListener() {{}} }},
    }},
  }},
}};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(`
  class CAPTestServiceWorkerScope {{}}
  globalThis.ServiceWorkerGlobalScope = CAPTestServiceWorkerScope;
  Object.setPrototypeOf(globalThis, CAPTestServiceWorkerScope.prototype);
`, context);
vm.runInContext(executionSource, context, {{ filename: "execution_generation.js" }});
vm.runInContext(backgroundSource, context, {{ filename: "background.js" }});

(async () => {{
  context.sender = {{
    url: `https://chatgpt.com/?cap_agent_preflight=1#cap_preflight_id=${{preflightId}}`,
    tab: {{ id: 17 }},
  }};
  let preflightError = "";
  try {{
    await vm.runInContext("prepareLiveLaunch(preflightId, sender)", context);
  }} catch (error) {{
    preflightError = String(error && error.message || error);
  }}

  async function directAttempt(path, init) {{
    try {{
      await context.fetch(controllerOrigin + path, init);
      return "accepted";
    }} catch (error) {{
      return String(error && error.message || error);
    }}
  }}

  const statusError = await directAttempt("/status", {{
    method: "GET",
    headers: {{ "X-CAP-Agent-Token": runId }},
    cache: "no-store",
  }});
  const authorizeError = await directAttempt("/authorize-send", {{
    method: "POST",
    headers: {{
      "Content-Type": "application/json",
      "X-CAP-Agent-Token": runId,
    }},
    body: JSON.stringify({{
      schema_version: 1,
      run_id: runId,
      delegation_id: delegationId,
      delivery_id: deliveryId,
      child_evidence: {{ run_id: runId, session_id: "chrome-tab:17" }},
    }}),
    cache: "no-store",
  }});

  const result = vm.runInContext(`({{
    liveLaunches: LIVE_LAUNCHES.size,
    livePreSendClaims: LIVE_PRE_SEND_CLAIMS.size,
  }})`, context);
  process.stdout.write(JSON.stringify({{
    preflightError,
    statusError,
    authorizeError,
    liveLaunches: result.liveLaunches,
    livePreSendClaims: result.livePreSendClaims,
    captured,
  }}));
}})().catch((error) => {{ console.error(error); process.exit(20); }});
"""
        value = self.run_node(script)
        self.assertIn("controller-auth-response-headers-invalid", value["preflightError"])
        self.assertIn("controller-auth-response-headers-invalid", value["statusError"])
        self.assertIn("controller-auth-response-headers-invalid", value["authorizeError"])
        self.assertEqual(0, value["liveLaunches"])
        self.assertEqual(0, value["livePreSendClaims"])

        requests = {request["path"]: request for request in value["captured"]}
        self.assertIn("/preflight", requests)
        self.assertIn("/status", requests)
        self.assertIn("/authorize-send", requests)

        for request in requests.values():
            headers = request["headers"]
            self.assertNotIn("x-cap-agent-preflight", headers)
            self.assertNotIn("x-cap-agent-token", headers)
            self.assertEqual("1", headers["x-cap-agent-auth-version"])
            self.assertRegex(headers["x-cap-agent-auth-nonce"], r"^[0-9a-f]{64}$")
            self.assertRegex(headers["x-cap-agent-auth-mac"], r"^[0-9a-f]{64}$")

        preflight_body = json.loads(requests["/preflight"]["body"])
        self.assertNotIn("preflight_id", preflight_body)
        self.assertNotIn("run_id", preflight_body)
        self.assertNotIn("1" * 64, requests["/preflight"]["body"])

        authorize_body = json.loads(requests["/authorize-send"]["body"])
        self.assertNotIn("run_id", authorize_body)
        self.assertNotIn("run_id", authorize_body["child_evidence"])
        self.assertNotIn("2" * 64, requests["/authorize-send"]["body"])


if __name__ == "__main__":
    unittest.main()
