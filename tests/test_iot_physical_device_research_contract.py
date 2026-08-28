from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "project-context" / "IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md"
ROADMAP = ROOT / "project-context" / "ROADMAP.md"
BASELINE = ROOT / "project-context" / "ARCHITECTURE_REUSE_BASELINE.md"

_DECISION_RE = re.compile(
    r"<!-- IOT_PHYSICAL_DEVICE_DECISION_V1\n(?P<body>.*?)\n-->",
    re.DOTALL,
)


def _decision_fields(text: str) -> dict[str, str]:
    matches = list(_DECISION_RE.finditer(text))
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one structured IoT research decision, got {len(matches)}"
        )
    fields: dict[str, str] = {}
    for line in matches[0].group("body").splitlines():
        key, separator, value = line.partition("=")
        if not separator or not key or not value:
            raise AssertionError(f"invalid decision field: {line!r}")
        if key in fields:
            raise AssertionError(f"duplicate decision field: {key}")
        fields[key] = value
    return fields


class IoTPhysicalDeviceResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = RESEARCH.read_text(encoding="utf-8")
        self.roadmap = ROADMAP.read_text(encoding="utf-8")
        self.baseline = BASELINE.read_text(encoding="utf-8")
        self.decision = _decision_fields(self.text)

    def test_decision_is_future_only_and_fail_closed(self) -> None:
        self.assertEqual(
            self.decision,
            {
                "stage_decision": "DEFER",
                "production_iot": "BLOCKED",
                "future_capability_family": "RESEARCH_SELECTED",
                "first_backend_candidate": "HOME_ASSISTANT",
                "mhs_dependency": "REFERENCE_ONLY",
                "critical_path_change": "NO",
            },
        )
        self.assertIn(
            "structured `IOT_PHYSICAL_DEVICE_DECISION_V1` block above is the sole implementation-decision representation",
            self.text,
        )
        self.assertIn("Production IoT/device-control work is **blocked**", self.text)
        self.assertIn("Stage 26.3C and the current release-critical sequence do not change", self.text)
        self.assertNotRegex(
            self.text,
            r"(?im)^\s*(?:top-level\s+)?stage research (?:result|decision)\s*[:=]\s*`?(?:PROCEED|NARROW)`?\s*$",
        )

    def test_home_assistant_is_candidate_not_project_authority(self) -> None:
        for phrase in (
            "Home Assistant is the preferred first backend candidate for future re-entry",
            "not an accepted production dependency",
            "hub/service success is evidence, never project `PASS`",
            "project operation/recovery history remains above the hub",
            "backend cannot broaden project scope",
            "service/API completion alone is never sufficient for project `PASS`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_source_code_evidence_is_pinned_and_independent(self) -> None:
        for ref in (
            "home-assistant/core@3fb456fa1fe4abbe6b89367b98f282043e9b02dd",
            "openhab/openhab-core@4bb2ebf810ba84563c9f3ebc04b0443218444ab2",
        ):
            with self.subTest(ref=ref):
                self.assertIn(ref, self.text)

        for phrase in (
            "`OPEN_IMPLEMENTED` for the state/service/registry mechanics",
            "`OPEN_PARTIAL` for the broader adapter role",
            "command-versus-state separation",
            "`DOCUMENTED_ONLY` / `OPEN_PARTIAL`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_identity_and_observation_quality_are_not_entity_id_only(self) -> None:
        for phrase in (
            "`entity_id` alone must not be the durable subject identity",
            "`unique_id`",
            "`device_id`",
            "assumed_state",
            "unable to access the real state of the entity",
            "HA instance identity",
            "stable registry/integration/device subject identity",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_action_result_requires_fresh_reobservation(self) -> None:
        for phrase in (
            "HA service handler completed\n!=\nproject ExpectedEffect proven",
            "fresh post-action state/event observation before project verification",
            "backend action delivery\n -> fresh state/event/sensor evidence\n -> project ExpectedEffect verification",
            "PASS | FAIL | UNKNOWN",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_raw_backend_dispatch_and_parallel_protocol_stacks_are_not_selected(self) -> None:
        for phrase in (
            "Do **not** expose a generic public `ha.call_service(anything)` capability",
            "Direct Matter/MQTT/vendor adapters remain measured-gap-only",
            "`REJECT` as default architecture strategy",
            "Direct MQTT is not “free”",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_recovery_invariant_does_not_preselect_idempotency_primitive(self) -> None:
        for phrase in (
            "fresh reconciliation before any retry",
            "concrete idempotency primitive requires separate research",
            "No row selects an exactly-once, lock, transaction, queue or durable-dedup implementation",
            "Do not infer a concrete lock/ledger/idempotency-key implementation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_high_risk_devices_keep_external_interlocks_below_llm_authority(self) -> None:
        for phrase in (
            "LLM is never the final safety authority",
            "independent hardware/process safety interlocks",
            "qualified deterministic procedure",
            "required safety interlock unavailable",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_experience_to_procedure_is_validation_seam_not_auto_promotion(self) -> None:
        for phrase in (
            "adaptive attempts\n -> verified successful traces\n -> candidate procedure\n -> independent validation",
            "not automatically trusted automation",
            "a successful trace is evidence, not automatically trusted code",
            "remove the LLM from timing-sensitive inner loops",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_roadmap_and_reuse_baseline_remember_the_future_role(self) -> None:
        self.assertIn("Future research seam — Physical Device / IoT Capability Family", self.roadmap)
        self.assertIn("Home Assistant", self.roadmap)
        self.assertIn("measured gap", self.roadmap.lower())
        self.assertIn("does not change the current release-critical sequence", self.roadmap)

        rows = [
            line
            for line in self.baseline.splitlines()
            if line.startswith("| Physical device / IoT normalization")
        ]
        self.assertEqual(len(rows), 1)
        cells = [cell.strip() for cell in rows[0].strip().strip("|").split("|")]
        self.assertEqual(len(cells), 7)
        self.assertIn("Home Assistant", cells[1])
        self.assertIn("state/event observation", cells[2])
        self.assertIn("Control Plane", cells[3])
        self.assertIn("IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md", cells[5])
        self.assertEqual(cells[6], "`PREFERRED_CANDIDATE_REVALIDATE_BEFORE_ADOPTION`")


if __name__ == "__main__":
    unittest.main()
