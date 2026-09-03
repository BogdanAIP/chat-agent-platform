from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryPostDeliveryGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = POLICY.read_text(encoding="utf-8")
        self.content = CONTENT.read_text(encoding="utf-8")

    def test_result_capture_is_gated_on_acked_stable_ui_disarm(self) -> None:
        for phrase in (
            "const POST_DELIVERY_UI_STABLE_MS = 8000;",
            "let postDeliveryUiDisarmed = false;",
            "let browserGuardRequired = false;",
            "function guardDeliveryVisible(intent)",
            "function guardSanitizeLaunchUrl()",
            "function guardClearBoundComposer(intent)",
            'post_delivery_ui_disarmed: true',
            'launch_url_clean: true',
            'composer_clean: true',
            "(response) => callback(Boolean(response?.ok))",
            "browserGuardRequired = true;",
            "return postDeliveryUiDisarmed === true;",
            "startPostDeliveryUiGuard();",
        ):
            self.assertIn(phrase, self.policy)

        gate = self.policy[
            self.policy.index("function hasSingleResultBlock") :
            self.policy.index("function guardEditorText")
        ]
        self.assertIn("singleResultBlockShape", gate)
        self.assertIn("browserGuardRequired", gate)
        self.assertIn("postDeliveryUiDisarmed", gate)
        self.assertNotIn("parseIntent(location.href)", gate)

        guard = self.policy[
            self.policy.index("function startPostDeliveryUiGuard") :
            self.policy.index("function conversationId")
        ]
        self.assertIn("guardDeliveryVisible(intent)", guard)
        self.assertIn("guardSanitizeLaunchUrl()", guard)
        self.assertIn("guardClearBoundComposer(intent)", guard)
        self.assertIn("now - stableSince < POST_DELIVERY_UI_STABLE_MS", guard)
        self.assertIn("guardRecordCleanup(intent", guard)
        self.assertIn("postDeliveryUiDisarmed = true", guard)
        self.assertLess(
            guard.index("guardRecordCleanup(intent"),
            guard.index("postDeliveryUiDisarmed = true"),
        )

    def test_guard_removes_all_launch_capabilities_and_requires_empty_editor(self) -> None:
        for key in (
            '"temporary-chat"',
            '"cap_agent_delegate"',
            '"cap_delegation_id"',
            '"cap_delivery_id"',
            '"cap_task_sha256"',
            '"prompt"',
        ):
            self.assertIn(key, self.policy)
        self.assertIn('fragment.delete("cap_run_id")', self.policy)
        self.assertIn('history.replaceState(history.state, "", nextUrl)', self.policy)
        self.assertIn('document.querySelector("#prompt-textarea")', self.policy)
        self.assertIn("clean: text.trim().length === 0", self.policy)
        self.assertIn("if (!state.bound) return false;", self.policy)

    def test_one_send_authority_remains_unchanged(self) -> None:
        self.assertEqual(1, self.content.count("button.click();"))
        self.assertNotIn("button.click();", self.policy)

    def test_policy_still_parses_and_pure_result_shape_works_under_node(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is unavailable")
        script = f'''require({str(POLICY)!r});
const p = globalThis.CAPChatGPTTemporaryPolicy;
const good = `${{p.RESULT_BEGIN}}\n{{"x":1}}\n${{p.RESULT_END}}`;
if (!p.singleResultBlockShape(good)) process.exit(2);
if (!p.hasSingleResultBlock(good)) process.exit(3);
'''
        completed = subprocess.run(
            [node, "-e", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
