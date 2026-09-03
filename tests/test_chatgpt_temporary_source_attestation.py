from __future__ import annotations

import unittest

from runtime.agent_sessions import source_attestation
from runtime.control_plane.delegation_state import DelegationStateError


EXECUTION_GENERATION = "9" * 64
ASSETS = {
    "manifest.json": "1" * 64,
    "execution_generation.js": "5" * 64,
    "policy.js": "2" * 64,
    "background.js": "3" * 64,
    "content.js": "4" * 64,
}


class ChatGPTTemporarySourceAttestationTests(unittest.TestCase):
    def expected_value(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "adapter_id": source_attestation.ADAPTER_ID,
            "expected_head": "a" * 40,
            "execution_generation": EXECUTION_GENERATION,
            "assets": dict(ASSETS),
        }

    def report_value(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "adapter_id": source_attestation.ADAPTER_ID,
            "execution_generation": EXECUTION_GENERATION,
            "assets": dict(ASSETS),
        }

    def test_exact_running_extension_report_is_accepted(self) -> None:
        expected = source_attestation.parse_expected_runtime_attestation(self.expected_value())
        digest = source_attestation.validate_runtime_attestation(
            self.report_value(), expected=expected
        )
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_stale_executing_generation_is_rejected_even_when_resource_hashes_match(self) -> None:
        expected = source_attestation.parse_expected_runtime_attestation(self.expected_value())
        report = self.report_value()
        report["execution_generation"] = "8" * 64
        with self.assertRaisesRegex(DelegationStateError, "execution generation mismatch"):
            source_attestation.validate_runtime_attestation(report, expected=expected)

    def test_any_running_extension_asset_mismatch_is_rejected(self) -> None:
        expected = source_attestation.parse_expected_runtime_attestation(self.expected_value())
        for name in source_attestation.RUNTIME_ASSETS:
            with self.subTest(name=name):
                report = self.report_value()
                report_assets = dict(report["assets"])
                report_assets[name] = "f" * 64
                report["assets"] = report_assets
                with self.assertRaisesRegex(DelegationStateError, "runtime attestation mismatch"):
                    source_attestation.validate_runtime_attestation(report, expected=expected)

    def test_missing_or_extra_asset_fails_closed(self) -> None:
        expected = source_attestation.parse_expected_runtime_attestation(self.expected_value())
        missing = self.report_value()
        missing_assets = dict(missing["assets"])
        missing_assets.pop("content.js")
        missing["assets"] = missing_assets
        with self.assertRaisesRegex(DelegationStateError, "keys mismatch"):
            source_attestation.validate_runtime_attestation(missing, expected=expected)

        extra = self.report_value()
        extra_assets = dict(extra["assets"])
        extra_assets["foreign.js"] = "6" * 64
        extra["assets"] = extra_assets
        with self.assertRaisesRegex(DelegationStateError, "keys mismatch"):
            source_attestation.validate_runtime_attestation(extra, expected=expected)

    def test_expected_attestation_requires_exact_head_generation_and_schema(self) -> None:
        bad_head = self.expected_value()
        bad_head["expected_head"] = "a" * 39
        with self.assertRaisesRegex(DelegationStateError, "head is invalid"):
            source_attestation.parse_expected_runtime_attestation(bad_head)

        bad_generation = self.expected_value()
        bad_generation["execution_generation"] = "9" * 63
        with self.assertRaisesRegex(DelegationStateError, "execution generation is invalid"):
            source_attestation.parse_expected_runtime_attestation(bad_generation)

        wrong_adapter = self.expected_value()
        wrong_adapter["adapter_id"] = "other"
        with self.assertRaisesRegex(DelegationStateError, "schema or adapter mismatch"):
            source_attestation.parse_expected_runtime_attestation(wrong_adapter)


if __name__ == "__main__":
    unittest.main()
