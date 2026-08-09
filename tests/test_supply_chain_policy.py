import pathlib
import tomllib
import unittest


class SupplyChainPolicyTests(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(__file__).resolve().parents[1]

    def test_dependency_license_gate_is_explicit_and_enforced(self):
        deny = tomllib.loads((self.repo / "deny.toml").read_text(encoding="utf-8"))
        licenses = deny["licenses"]
        allowed = set(licenses["allow"])

        self.assertIn("MIT", allowed)
        self.assertIn("Apache-2.0", allowed)
        self.assertEqual(licenses["confidence-threshold"], 0.8)
        self.assertNotIn("exceptions", licenses)

        workflow = (
            self.repo / ".github" / "workflows" / "supply-chain.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("command: check licenses bans sources", workflow)


if __name__ == "__main__":
    unittest.main()
