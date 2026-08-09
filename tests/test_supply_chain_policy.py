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
        self.assertIn("MIT-0", allowed)
        self.assertIn("Apache-2.0", allowed)
        self.assertNotIn("ISC", allowed)
        self.assertNotIn("MPL-2.0", allowed)
        self.assertEqual(licenses["confidence-threshold"], 0.8)
        self.assertNotIn("exceptions", licenses)

        workflow = (
            self.repo / ".github" / "workflows" / "supply-chain.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("check licenses bans sources", workflow)

    def test_cargo_deny_binary_is_checksum_pinned_without_action_wrapper(self):
        workflow = (
            self.repo / ".github" / "workflows" / "supply-chain.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('version="0.20.2"', workflow)
        self.assertIn(
            'expected_sha256="9f12ed4c49936e09b48bf862b595cde2fe64fcbd9d74dfacac6131ca824c8d5f"',
            workflow,
        )
        self.assertIn("sha256sum --check --strict", workflow)
        self.assertIn("check advisories", workflow)
        self.assertNotIn("EmbarkStudios/cargo-deny-action@", workflow)


if __name__ == "__main__":
    unittest.main()
