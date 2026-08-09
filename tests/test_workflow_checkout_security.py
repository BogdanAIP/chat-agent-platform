import pathlib
import unittest


class WorkflowCheckoutSecurityTests(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(__file__).resolve().parents[1]
        self.workflows = sorted((self.repo / ".github" / "workflows").glob("*.yml"))

    def test_every_checkout_disables_persisted_credentials(self):
        self.assertTrue(self.workflows, "GitHub Actions workflows must exist")
        checkout_count = 0
        for workflow in self.workflows:
            text = workflow.read_text(encoding="utf-8")
            uses_count = text.count("actions/checkout@")
            if uses_count == 0:
                continue
            checkout_count += uses_count
            disabled_count = text.count("persist-credentials: false")
            self.assertEqual(
                uses_count,
                disabled_count,
                f"{workflow.name}: every checkout must set persist-credentials: false",
            )
        self.assertGreater(checkout_count, 0, "expected at least one checkout step")

    def test_main_ci_is_present_on_every_pull_request(self):
        workflow = (self.repo / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("pull_request:", workflow)
        self.assertNotIn("paths-ignore:", workflow)
        self.assertNotIn("paths:", workflow)
        self.assertIn("name: ci", workflow)
        self.assertIn("  verify-windows:\n", workflow)


if __name__ == "__main__":
    unittest.main()
