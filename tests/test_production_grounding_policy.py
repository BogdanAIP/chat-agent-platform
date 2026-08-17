from __future__ import annotations

import unittest

from runtime.local_vision_adapter.production_policy import authorize_native_grounding


def accepted_row(kind: str, *, target_text: str | None = None) -> dict:
    return {
        "kind": kind,
        "target_text": target_text,
        "decision": "accepted",
        "parse_error": None,
        "prediction_point": {"x": 50.0, "y": 40.0},
        "pass1_detection_count": 1,
        "pass2_detection_count": 1,
        "inventory_match_count": 1 if target_text else None,
        "coarse_refined_iou": 0.2,
    }


class ProductionGroundingPolicyTests(unittest.TestCase):
    def test_text_inventory_accepts_measured_low_overlap_without_global_iou_gate(self) -> None:
        row = accepted_row("labeled_button", target_text="Send")
        row["coarse_refined_iou"] = 0.00949

        decision = authorize_native_grounding(row)

        self.assertTrue(decision.authorized)
        self.assertEqual(decision.status, "resolved")
        self.assertEqual(decision.reason, "promoted-text-inventory")
        self.assertEqual(decision.point, (50.0, 40.0))

    def test_state_inventory_uses_same_unique_text_guard(self) -> None:
        row = accepted_row("visual_state", target_text="Send")

        decision = authorize_native_grounding(row)

        self.assertTrue(decision.authorized)
        self.assertEqual(decision.reason, "promoted-text-inventory")

    def test_text_inventory_ambiguity_fails_closed(self) -> None:
        row = accepted_row("labeled_button", target_text="Send")
        row["inventory_match_count"] = 2

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "abstain")
        self.assertEqual(decision.reason, "text-inventory-not-unique")

    def test_icon_requires_unique_two_pass_positive_overlap(self) -> None:
        row = accepted_row("icon_only")
        row["coarse_refined_iou"] = 0.17668

        decision = authorize_native_grounding(row)

        self.assertTrue(decision.authorized)
        self.assertEqual(decision.reason, "promoted-icon-consistent")

    def test_icon_zero_overlap_fails_closed(self) -> None:
        row = accepted_row("icon_only")
        row["coarse_refined_iou"] = 0.0

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "abstain")
        self.assertEqual(decision.reason, "icon-passes-inconsistent")

    def test_repeated_row_is_not_promoted_even_if_benchmark_row_says_accepted(self) -> None:
        row = accepted_row("repeated_similar_control")

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "abstain")
        self.assertEqual(
            decision.reason,
            "target-class-not-promoted:repeated-similar-control",
        )

    def test_tiny_target_is_not_promoted_even_if_benchmark_row_says_accepted(self) -> None:
        row = accepted_row("tiny_target")

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "abstain")
        self.assertEqual(decision.reason, "target-class-not-promoted:tiny-target")

    def test_absent_target_never_authorizes_action(self) -> None:
        row = accepted_row("absent_target", target_text="Export CSV")

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "abstain")
        self.assertEqual(decision.reason, "target-declared-absent")

    def test_provider_error_remains_error(self) -> None:
        row = accepted_row("icon_only")
        row["parse_error"] = "VisionProviderError: transport failed"

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "error")
        self.assertEqual(decision.reason, "grounding-provider-or-parse-error")

    def test_nonaccepted_grounder_decision_fails_closed(self) -> None:
        row = accepted_row("icon_only")
        row["decision"] = "inconsistent-pass2"
        row["prediction_point"] = None

        decision = authorize_native_grounding(row)

        self.assertFalse(decision.authorized)
        self.assertEqual(decision.status, "abstain")
        self.assertEqual(decision.reason, "grounder-inconsistent-pass2")


if __name__ == "__main__":
    unittest.main()
