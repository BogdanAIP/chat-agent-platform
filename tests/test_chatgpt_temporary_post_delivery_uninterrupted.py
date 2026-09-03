from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension" / "policy.js"


class ChatGPTTemporaryPostDeliveryUninterruptedTests(unittest.TestCase):
    def test_repeated_cleanup_resets_stability_window(self) -> None:
        policy = POLICY.read_text(encoding="utf-8")
        cleanup = policy[
            policy.index("function guardClearBoundComposer") :
            policy.index("function guardDeliveryVisible")
        ]
        self.assertIn("return { clean: true, changed: false };", cleanup)
        self.assertIn("return { clean: false, changed: false };", cleanup)
        self.assertIn("return { clean: false, changed: true };", cleanup)
        self.assertIn("return { clean: guardComposerState(intent).clean, changed: true };", cleanup)

        guard = policy[
            policy.index("function startPostDeliveryUiGuard") :
            policy.index("function conversationId")
        ]
        self.assertIn("const composer = guardClearBoundComposer(intent);", guard)
        self.assertIn("const clean = urlClean && composer.clean;", guard)
        self.assertIn("if (!clean || composer.changed)", guard)
        self.assertLess(
            guard.index("if (!clean || composer.changed)"),
            guard.index("now - stableSince < POST_DELIVERY_UI_STABLE_MS"),
        )


if __name__ == "__main__":
    unittest.main()
