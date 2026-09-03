from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"
CONTENT = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "content.js"


class ChatGPTTemporaryPostDeliveryGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = POLICY.read_text(encoding="utf-8")
        self.content = CONTENT.read_text(encoding="utf-8")

    def test_result_capture_requires_acked_ui_disarm(self) -> None:
        for phrase in (
            "const POST_DELIVERY_UI_STABLE_MS = 8000;",
            "let postDeliveryUiDisarmed = false;",
            "let browserGuardRequired = false;",
            "function guardDeliveryVisible(intent)",
            "function guardRecordCleanup(intent, callback)",
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

        guard = self.policy[
            self.policy.index("function startPostDeliveryUiGuard") :
            self.policy.index("function conversationId")
        ]
        self.assertIn("guardRecordCleanup(intent", guard)
        self.assertIn("postDeliveryUiDisarmed = true", guard)
        self.assertLess(
            guard.index("guardRecordCleanup(intent"),
            guard.index("postDeliveryUiDisarmed = true"),
        )

    def test_guard_disarms_url_and_requires_empty_bound_editor(self) -> None:
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
        self.assertIn(
            "if (!state.bound) return { clean: false, changed: false };",
            self.policy,
        )

    def test_repeated_cleanup_resets_stability_timer(self) -> None:
        cleanup = self.policy[
            self.policy.index("function guardClearBoundComposer") :
            self.policy.index("function guardDeliveryVisible")
        ]
        self.assertIn("return { clean: true, changed: false };", cleanup)
        self.assertIn("return { clean: guardComposerState(intent).clean, changed: true };", cleanup)

        guard = self.policy[
            self.policy.index("function startPostDeliveryUiGuard") :
            self.policy.index("function conversationId")
        ]
        self.assertIn("const composer = guardClearBoundComposer(intent);", guard)
        self.assertIn("if (!clean || composer.changed)", guard)
        self.assertLess(
            guard.index("if (!clean || composer.changed)"),
            guard.index("now - stableSince < POST_DELIVERY_UI_STABLE_MS"),
        )

    def test_one_send_authority_is_unchanged(self) -> None:
        self.assertEqual(1, self.content.count("button.click();"))
        self.assertNotIn("button.click();", self.policy)


if __name__ == "__main__":
    unittest.main()
