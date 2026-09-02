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

    @staticmethod
    def intent_expression(
        *,
        run_id: str,
        delegation_id: str,
        delivery_id: str,
        task_sha: str,
        prompt: str,
        run_in_query: bool = False,
    ) -> str:
        run_query_line = (
            f'u.searchParams.set("cap_run_id", {json.dumps(run_id)});'
            if run_in_query
            else ""
        )
        return f"""(() => {{
  const u = new URL("https://chatgpt.com/");
  u.searchParams.set("temporary-chat", "true");
  u.searchParams.set("cap_agent_delegate", "1");
  {run_query_line}
  u.searchParams.set("cap_delegation_id", {json.dumps(delegation_id)});
  u.searchParams.set("cap_delivery_id", {json.dumps(delivery_id)});
  u.searchParams.set("cap_task_sha256", {json.dumps(task_sha)});
  u.searchParams.set("prompt", {json.dumps(prompt)});
  u.hash = "cap_run_id={run_id}";
  return CAPChatGPTTemporaryPolicy.parseIntent(u.toString());
}})()"""

    @staticmethod
    def valid_prompt(*, delegation_id: str, delivery_id: str, task_sha: str) -> str:
        return (
            "WORKER_TASK_V1\n"
            f"delegation_id={delegation_id}\n"
            f"delivery_id={delivery_id}\n"
            f"task_sha256={task_sha}\n"
            "CAP_WORKER_RESULT_V1_BEGIN\nCAP_WORKER_RESULT_V1_END"
        )

    def test_exact_intent_binds_fragment_capability_and_model_visible_identity(self) -> None:
        run_id = "a" * 64
        delegation_id = "b" * 64
        delivery_id = "c" * 64
        task_sha = "d" * 64
        prompt = self.valid_prompt(
            delegation_id=delegation_id,
            delivery_id=delivery_id,
            task_sha=task_sha,
        )
        value = self.run_policy(
            self.intent_expression(
                run_id=run_id,
                delegation_id=delegation_id,
                delivery_id=delivery_id,
                task_sha=task_sha,
                prompt=prompt,
            )
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
        prompt = self.valid_prompt(
            delegation_id=delegation_id,
            delivery_id=delivery_id,
            task_sha=task_sha,
        )
        value = self.run_policy(
            self.intent_expression(
                run_id=run_id,
                delegation_id=delegation_id,
                delivery_id=delivery_id,
                task_sha=task_sha,
                prompt=prompt,
                run_in_query=True,
            )
        )
        self.assertFalse(value["enabled"])
        self.assertEqual("private-run-id-in-query", value["reason"])

    def test_private_run_capability_in_worker_prompt_is_rejected(self) -> None:
        run_id = "a" * 64
        delegation_id = "b" * 64
        delivery_id = "c" * 64
        task_sha = "d" * 64
        prompt = self.valid_prompt(
            delegation_id=delegation_id,
            delivery_id=delivery_id,
            task_sha=task_sha,
        ) + "\n" + run_id
        value = self.run_policy(
            self.intent_expression(
                run_id=run_id,
                delegation_id=delegation_id,
                delivery_id=delivery_id,
                task_sha=task_sha,
                prompt=prompt,
            )
        )
        self.assertFalse(value["enabled"])
        self.assertEqual("private-run-id-leaked-to-prompt", value["reason"])

    def test_personalization_labels_are_classified_fail_closed(self) -> None:
        labels = {
            "english_non": "Non-personalized",
            "english_yes": "Personalized",
            "russian_non": "Без персонализации",
            "russian_yes": "Персонализированный",
            "german_non": "Nicht personalisiert",
            "german_yes": "Personalisiert",
            "temporary_only": "Temporary Chat",
        }
        expression = "({" + ",".join(
            f"{key}: CAPChatGPTTemporaryPolicy.personalizationModeFromText({json.dumps(value)})"
            for key, value in labels.items()
        ) + "})"
        value = self.run_policy(expression)
        self.assertEqual(
            {
                "english_non": "non-personalized",
                "english_yes": "personalized",
                "russian_non": "non-personalized",
                "russian_yes": "personalized",
                "german_non": "non-personalized",
                "german_yes": "personalized",
                "temporary_only": "unknown",
            },
            value,
        )

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