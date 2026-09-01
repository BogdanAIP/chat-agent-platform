from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


class ChatGPTTemporaryPolicyRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.node = shutil.which("node")
        if self.node is None:
            self.skipTest("node is unavailable")

    def run_policy(self, expression: str) -> object:
        script = f"""
const fs = require("fs");
const vm = require("vm");
vm.runInThisContext(fs.readFileSync({json.dumps(str(POLICY))}, "utf8"), {{ filename: "policy.js" }});
const value = ({expression});
process.stdout.write(JSON.stringify(value));
"""
        completed = subprocess.run(
            [self.node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_exact_intent_binds_fragment_capability_and_model_visible_identity(self) -> None:
        run_id = "a" * 64
        delegation_id = "b" * 64
        delivery_id = "c" * 64
        task_sha = "d" * 64
        prompt = (
            "WORKER_TASK_V1\n"
            f"delegation_id={delegation_id}\n"
            f"delivery_id={delivery_id}\n"
            f"task_sha256={task_sha}\n"
            "CAP_WORKER_RESULT_V1_BEGIN\nCAP_WORKER_RESULT_V1_END"
        )
        query = (
            "?temporary-chat=true&cap_agent_delegate=1"
            f"&cap_delegation_id={delegation_id}"
            f"&cap_delivery_id={delivery_id}"
            f"&cap_task_sha256={task_sha}"
            f"&prompt=${{encodeURIComponent({json.dumps(prompt)})}}"
            f"#cap_run_id={run_id}"
        )
        value = self.run_policy(
            f"CAPChatGPTTemporaryPolicy.parseIntent(`https://chatgpt.com/${{{json.dumps(query)}}}`)"
        )
        self.assertTrue(value["enabled"])
        self.assertEqual(run_id, value["runId"])
        self.assertEqual(delegation_id, value["delegationId"])
        self.assertEqual(delivery_id, value["deliveryId"])
        self.assertEqual(task_sha, value["taskSha256"])

    def test_private_run_capability_in_query_is_rejected(self) -> None:
        run_id = "a" * 64
        delegation_id = "b" * 64
        delivery_id = "c" * 64
        task_sha = "d" * 64
        prompt = (
            "WORKER_TASK_V1\n"
            f"delegation_id={delegation_id}\n"
            f"delivery_id={delivery_id}\n"
            f"task_sha256={task_sha}\n"
            "CAP_WORKER_RESULT_V1_BEGIN\nCAP_WORKER_RESULT_V1_END"
        )
        expression = f"""(() => {{
  const u = new URL("https://chatgpt.com/");
  u.searchParams.set("temporary-chat", "true");
  u.searchParams.set("cap_agent_delegate", "1");
  u.searchParams.set("cap_run_id", {json.dumps(run_id)});
  u.searchParams.set("cap_delegation_id", {json.dumps(delegation_id)});
  u.searchParams.set("cap_delivery_id", {json.dumps(delivery_id)});
  u.searchParams.set("cap_task_sha256", {json.dumps(task_sha)});
  u.searchParams.set("prompt", {json.dumps(prompt)});
  u.hash = "cap_run_id={run_id}";
  return CAPChatGPTTemporaryPolicy.parseIntent(u.toString());
}})()"""
        value = self.run_policy(expression)
        self.assertFalse(value["enabled"])
        self.assertEqual("private-run-id-in-query", value["reason"])

    def test_private_run_capability_in_worker_prompt_is_rejected(self) -> None:
        run_id = "a" * 64
        delegation_id = "b" * 64
        delivery_id = "c" * 64
        task_sha = "d" * 64
        expression = f"""(() => {{
  const u = new URL("https://chatgpt.com/");
  u.searchParams.set("temporary-chat", "true");
  u.searchParams.set("cap_agent_delegate", "1");
  u.searchParams.set("cap_delegation_id", {json.dumps(delegation_id)});
  u.searchParams.set("cap_delivery_id", {json.dumps(delivery_id)});
  u.searchParams.set("cap_task_sha256", {json.dumps(task_sha)});
  u.searchParams.set("prompt", `WORKER_TASK_V1\ndelegation_id={delegation_id}\ndelivery_id={delivery_id}\ntask_sha256={task_sha}\nCAP_WORKER_RESULT_V1_BEGIN\n${{ {json.dumps(run_id)} }}\nCAP_WORKER_RESULT_V1_END`);
  u.hash = "cap_run_id={run_id}";
  return CAPChatGPTTemporaryPolicy.parseIntent(u.toString());
}})()"""
        value = self.run_policy(expression)
        self.assertFalse(value["enabled"])
        self.assertEqual("private-run-id-leaked-to-prompt", value["reason"])

    def test_result_block_must_be_single_and_unwrapped(self) -> None:
        good = "CAP_WORKER_RESULT_V1_BEGIN\n{}\nCAP_WORKER_RESULT_V1_END"
        duplicate = good + "\n" + good
        wrapped = "prefix\n" + good
        expression = (
            "({good: CAPChatGPTTemporaryPolicy.hasSingleResultBlock("
            + json.dumps(good)
            + "), duplicate: CAPChatGPTTemporaryPolicy.hasSingleResultBlock("
            + json.dumps(duplicate)
            + "), wrapped: CAPChatGPTTemporaryPolicy.hasSingleResultBlock("
            + json.dumps(wrapped)
            + ")})"
        )
        value = self.run_policy(expression)
        self.assertEqual({"good": True, "duplicate": False, "wrapped": False}, value)

    def test_conversation_id_is_bounded_to_chat_route(self) -> None:
        value = self.run_policy(
            "({good: CAPChatGPTTemporaryPolicy.conversationId(\"https://chatgpt.com/c/abcDEF_123456\"), bad: CAPChatGPTTemporaryPolicy.conversationId(\"https://chatgpt.com/g/g-123\")})"
        )
        self.assertEqual("abcDEF_123456", value["good"])
        self.assertIsNone(value["bad"])


if __name__ == "__main__":
    unittest.main()
