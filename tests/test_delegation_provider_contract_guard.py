import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "project-context" / "DELEGATION_PROVIDER_CONTRACT.md"


class DelegationProviderContractGuardTests(unittest.TestCase):

    def test_contract_exists(self):
        self.assertTrue(CONTRACT.exists())

    def test_cap_ownership_boundary_is_explicit(self):
        text = CONTRACT.read_text(encoding="utf-8").casefold()

        self.assertIn("delegation identity", text)
        self.assertIn("authority and scope", text)
        self.assertIn("verification decisions", text)
        self.assertIn("reconciliation decisions", text)

    def test_provider_is_execution_only(self):
        text = CONTRACT.read_text(encoding="utf-8").casefold()

        self.assertIn("execution mechanics", text)
        self.assertIn("provider receipts and observations", text)

        self.assertNotIn("provider owns verification", text)
        self.assertNotIn("provider decides authority", text)

    def test_provider_result_does_not_equal_verified_effect(self):
        text = CONTRACT.read_text(encoding="utf-8").casefold()

        self.assertIn(
            "does not by itself prove that the requested external effect occurred",
            text,
        )

    def test_contract_does_not_define_runtime_or_orchestration(self):
        text = CONTRACT.read_text(encoding="utf-8").casefold()

        self.assertIn("multi-agent orchestration", text)
        self.assertIn("scheduler behavior", text)
        self.assertIn("worker pools", text)
        self.assertIn("planner logic", text)


if __name__ == "__main__":
    unittest.main()