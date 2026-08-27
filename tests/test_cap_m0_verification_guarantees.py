from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from runtime.control_plane.verification import (
    ExpectedEffect,
    ObservationRef,
    ObservationSnapshot,
    StatePredicate,
    VerificationStatus,
    verify_expected_effect,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "mutation" / "verification_guarantees.json"
TARGET = ROOT / "runtime" / "control_plane" / "verification.py"
RUNNER = ROOT / "scripts" / "run-verification-mutation-pilot.py"


def _load_runner_module():
    spec = importlib.util.spec_from_file_location("cap_m0_mutation_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load CAP-M0 mutation runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapM0VerificationGuaranteeTests(unittest.TestCase):
    def test_complete_observation_missing_equals_field_is_fail(self) -> None:
        before = ObservationRef(
            capability="files",
            subject="artifact:result.txt",
            stream_id="main",
            sequence=1,
            fingerprint="before",
        )
        effect = ExpectedEffect(
            effect_id="required-field",
            before=before,
            predicates=(StatePredicate.equals("sha256", expected="abc123"),),
        )
        after = ObservationSnapshot(
            ref=ObservationRef(
                capability="files",
                subject="artifact:result.txt",
                stream_id="main",
                sequence=2,
                fingerprint="after",
            ),
            state={"exists": True},
            complete=True,
        )

        result = verify_expected_effect(effect, after)

        self.assertEqual(result.status, VerificationStatus.FAIL)
        self.assertEqual(result.reason, "expected_effect_failed")
        self.assertEqual(result.predicate_results[0].reason, "field_missing")

    def test_mutation_manifest_is_bounded_unique_and_source_bound(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        source = TARGET.read_text(encoding="utf-8")

        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["target"], "runtime/control_plane/verification.py")
        self.assertEqual(len(manifest["mutants"]), 12)

        ids = [item["id"] for item in manifest["mutants"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item["guarantee"].strip() for item in manifest["mutants"]))
        self.assertTrue(all(item["detector"].strip() for item in manifest["mutants"]))
        self.assertTrue(
            all(
                isinstance(item.get("detector_test"), str)
                and item["detector_test"].startswith("tests.")
                for item in manifest["mutants"]
            )
        )

        for mutant in manifest["mutants"]:
            with self.subTest(mutant=mutant["id"]):
                self.assertNotEqual(mutant["find"], mutant["replace"])
                self.assertEqual(
                    source.count(mutant["find"]),
                    1,
                    f"{mutant['id']} mutation anchor must match exactly once",
                )

    def test_killed_requires_one_named_detector_assertion_failure(self) -> None:
        runner = _load_runner_module()
        selector = "tests.example.ExampleTests.test_detector"
        base = {
            "selector": selector,
            "tests_run": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expected_failures": 0,
            "unexpected_successes": 0,
        }

        assertion_failure = dict(base, failures=1)
        status, reason = runner._classify_detector_payload(
            assertion_failure,
            detector_test=selector,
        )
        self.assertEqual(status, "killed")
        self.assertEqual(reason, "named_detector_assertion_failed")

        passed = dict(base)
        self.assertEqual(
            runner._classify_detector_payload(passed, detector_test=selector)[0],
            "survived",
        )

    def test_detector_error_or_cardinality_drift_is_not_a_kill(self) -> None:
        runner = _load_runner_module()
        selector = "tests.example.ExampleTests.test_detector"
        base = {
            "selector": selector,
            "tests_run": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expected_failures": 0,
            "unexpected_successes": 0,
        }

        errored = dict(base, errors=1)
        multiple_tests = dict(base, tests_run=2, failures=1)
        skipped = dict(base, skipped=1)
        wrong_selector = dict(base, selector="tests.other.OtherTests.test_other", failures=1)

        for payload in (errored, multiple_tests, skipped, wrong_selector):
            with self.subTest(payload=payload):
                self.assertEqual(
                    runner._classify_detector_payload(payload, detector_test=selector)[0],
                    "error",
                )

    def test_detector_source_binding_requires_exact_mutated_target_path(self) -> None:
        runner = _load_runner_module()
        self.assertTrue(
            runner._detector_bound_to_target(
                {"verification_module_path": str(TARGET)},
                target=TARGET,
            )
        )
        self.assertFalse(
            runner._detector_bound_to_target(
                {"verification_module_path": str(RUNNER)},
                target=TARGET,
            )
        )
        self.assertFalse(runner._detector_bound_to_target({}, target=TARGET))


if __name__ == "__main__":
    unittest.main()
