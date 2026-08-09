import pathlib
import re
import unittest


class WorkflowActionPinTests(unittest.TestCase):
    def test_first_party_actions_use_immutable_commit_shas(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        workflows = sorted((repo / ".github" / "workflows").glob("*.yml"))
        self.assertTrue(workflows, "GitHub Actions workflows must exist")

        seen = 0
        for workflow in workflows:
            text = workflow.read_text(encoding="utf-8")
            for action, ref in re.findall(r"uses:\s+(actions/[\w-]+)@([^\s#]+)", text):
                seen += 1
                self.assertRegex(
                    ref,
                    r"^[0-9a-f]{40}$",
                    f"{workflow.name}: {action} must use an immutable commit SHA",
                )
        self.assertGreater(seen, 0, "expected at least one first-party action reference")


if __name__ == "__main__":
    unittest.main()
