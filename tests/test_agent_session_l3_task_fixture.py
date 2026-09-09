from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tests" / "fixtures" / "agent_session_l3_nonreviewer_task.txt"


class AgentSessionL3TaskFixtureTests(unittest.TestCase):
    def test_fixture_is_bounded_read_only_and_not_reviewer_specific(self) -> None:
        text = TASK.read_text(encoding="utf-8")
        folded = text.casefold()
        self.assertIn("bounded read-only reasoning task", folded)
        self.assertIn("do not perform any external action", folded)
        self.assertIn("exactly three numbered points", folded)
        self.assertLessEqual(len(text.encode("utf-8")), 2048)
        for forbidden in (
            "review_request_v1",
            "review_result_v1",
            "code-review",
            "pull request",
            "github",
            "base_sha",
            "head_sha",
        ):
            self.assertNotIn(forbidden, folded)


if __name__ == "__main__":
    unittest.main()
