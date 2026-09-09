from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryCaptureEpochRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def test_prepare_capture_continuation_rejects_guard_epoch_aba(self) -> None:
        script = f"""
const fs = require("fs");
const assert = require("assert/strict");

const source = fs.readFileSync({json.dumps(str(CONTENT))}, "utf8").replace(/\\r\\n?/g, "\\n");
const start = source.indexOf("    async function captureResult(text) {{");
const end = source.indexOf("\\n\\n    async function pollControllerStatus()", start);
if (start < 0 || end <= start) process.exit(90);
const functionSource = source.slice(start, end).trim();

(async () => {{
  const cleanupToken = "a".repeat(64);
  const captureToken = "b".repeat(64);
  let currentEpoch = 17;
  let captureStarted = false;
  let deliveryState = "delivered";
  let postDeliveryCleanupComplete = true;
  let postDeliveryCleanupStableSince = 123;
  let prepareResolve = null;
  let holdPrepare = true;
  let resetCount = 0;
  const messages = [];
  const stops = [];
  const events = [];

  const policy = {{
    HEX64_RE: /^[0-9a-f]{{64}}$/,
    captureAuthorization() {{
      return {{ cleanupToken, guardEpoch: currentEpoch }};
    }},
    invalidatePostDeliveryAuthorization() {{ return true; }},
  }};

  function resetCaptureAuthority() {{
    resetCount += 1;
    captureStarted = false;
    postDeliveryCleanupComplete = false;
    postDeliveryCleanupStableSince = 0;
    policy.invalidatePostDeliveryAuthorization();
  }}

  function staleCaptureAuthority(_reason) {{ return false; }}
  function retryableCaptureTransportFailure(_reason) {{ return false; }}
  function event(name, details = {{}}) {{ events.push({{ name, details }}); }}
  function stop(reason, details = {{}}) {{ stops.push({{ reason, details }}); }}

  async function sendMessage(kind, payload = {{}}) {{
    messages.push({{ kind, payload }});
    if (kind === "prepare-capture") {{
      if (!holdPrepare) return {{ ok: true, capture_token: captureToken }};
      return await new Promise((resolve) => {{ prepareResolve = resolve; }});
    }}
    if (kind === "capture") return {{ ok: true, worker_status: "COMPLETED" }};
    return {{ ok: true }};
  }}

  const captureResult = eval(`(${{functionSource}})`);

  const staleContinuation = captureResult("old-result-text");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(typeof prepareResolve, "function");
  assert.equal(messages.filter((item) => item.kind === "prepare-capture").length, 1);
  assert.equal(messages.filter((item) => item.kind === "capture").length, 0);

  // Simulate correlation loss/reset followed by a fresh clean interval that
  // reuses the same controller cleanup token at a new browser guard epoch.
  currentEpoch = 18;
  postDeliveryCleanupComplete = true;
  prepareResolve({{ ok: true, capture_token: captureToken }});
  await staleContinuation;

  assert.equal(messages.filter((item) => item.kind === "capture").length, 0);
  assert.equal(resetCount, 1);
  assert.equal(stops.length, 0);

  // A fresh continuation at the current epoch is still allowed to capture.
  holdPrepare = false;
  captureStarted = false;
  postDeliveryCleanupComplete = true;
  await captureResult("fresh-result-text");

  const captureMessages = messages.filter((item) => item.kind === "capture");
  assert.equal(captureMessages.length, 1);
  assert.equal(captureMessages[0].payload.cleanup_token, cleanupToken);
  assert.equal(captureMessages[0].payload.capture_token, captureToken);
  assert.equal(captureMessages[0].payload.result_text, "fresh-result-text");
  assert.equal(stops.at(-1)?.reason, "result-recorded");
}})().catch((error) => {{
  console.error(error?.stack || error);
  process.exit(91);
}});
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
