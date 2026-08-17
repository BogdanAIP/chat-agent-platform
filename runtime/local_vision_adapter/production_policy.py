"""Deterministic promotion policy for Stage 25.1 browser visual grounding.

The Stage 25 benchmark adapter intentionally records richer diagnostic output than
production may authorize.  This module turns that diagnostic row into a narrow,
model-neutral authorization result using only behavior already demonstrated on
the target machine.

Safety rule: benchmark success does not automatically promote every target class.
Repeated-row and tiny-target actions remain fail-closed until separate target
acceptance demonstrates reliable clicks for those classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProductionGroundingDecision:
    status: str  # "resolved" | "abstain" | "error"
    reason: str
    point: tuple[float, float] | None = None

    @property
    def authorized(self) -> bool:
        return self.status == "resolved" and self.point is not None


_PROMOTED_KINDS = frozenset({"labeled_button", "icon_only", "visual_state"})
_NOT_YET_PROMOTED = {
    "repeated_similar_control": "target-class-not-promoted:repeated-similar-control",
    "tiny_target": "target-class-not-promoted:tiny-target",
}


def _point_from_row(row: Mapping[str, Any]) -> tuple[float, float] | None:
    raw = row.get("prediction_point")
    if not isinstance(raw, Mapping):
        return None
    x = raw.get("x")
    y = raw.get("y")
    if (
        isinstance(x, bool)
        or isinstance(y, bool)
        or not isinstance(x, (int, float))
        or not isinstance(y, (int, float))
    ):
        return None
    return (float(x), float(y))


def authorize_native_grounding(row: Mapping[str, Any]) -> ProductionGroundingDecision:
    """Authorize only target classes/guards already supported by measured evidence.

    This is deliberately stricter than the benchmark adapter.  It is expected to
    over-abstain while Stage 25.1 is being promoted.
    """

    if not isinstance(row, Mapping):
        return ProductionGroundingDecision("error", "malformed-grounding-row")

    parse_error = row.get("parse_error")
    if parse_error:
        return ProductionGroundingDecision("error", "grounding-provider-or-parse-error")

    kind = row.get("kind")
    if not isinstance(kind, str) or not kind:
        return ProductionGroundingDecision("error", "missing-target-kind")

    if kind in _NOT_YET_PROMOTED:
        return ProductionGroundingDecision("abstain", _NOT_YET_PROMOTED[kind])

    if kind == "absent_target":
        return ProductionGroundingDecision("abstain", "target-declared-absent")

    if kind not in _PROMOTED_KINDS:
        return ProductionGroundingDecision("abstain", f"target-class-unreviewed:{kind}")

    if row.get("decision") != "accepted":
        decision = row.get("decision")
        suffix = decision if isinstance(decision, str) and decision else "not-accepted"
        return ProductionGroundingDecision("abstain", f"grounder-{suffix}")

    point = _point_from_row(row)
    if point is None:
        return ProductionGroundingDecision("error", "accepted-result-missing-valid-point")

    pass2_count = row.get("pass2_detection_count")
    if pass2_count != 1:
        return ProductionGroundingDecision("abstain", "refinement-not-unique")

    target_text = row.get("target_text")
    if kind in {"labeled_button", "visual_state"}:
        if not isinstance(target_text, str) or not target_text.strip():
            return ProductionGroundingDecision("error", "text-class-missing-target-text")
        if row.get("inventory_match_count") != 1:
            return ProductionGroundingDecision("abstain", "text-inventory-not-unique")
        # Do not impose a global/high IoU threshold here.  Valid target-machine
        # text inventory/refinement evidence includes very low positive overlap.
        return ProductionGroundingDecision("resolved", "promoted-text-inventory", point)

    # icon_only: current target evidence promoted Search only when both passes
    # are unique and overlap positively.  This rule intentionally does not
    # apply to inventory-backed text targets.
    if target_text not in (None, ""):
        return ProductionGroundingDecision("error", "icon-class-must-not-use-target-text")
    if row.get("pass1_detection_count") != 1:
        return ProductionGroundingDecision("abstain", "icon-pass1-not-unique")

    consistency_iou = row.get("coarse_refined_iou")
    if (
        isinstance(consistency_iou, bool)
        or not isinstance(consistency_iou, (int, float))
        or float(consistency_iou) <= 0.0
    ):
        return ProductionGroundingDecision("abstain", "icon-passes-inconsistent")

    return ProductionGroundingDecision("resolved", "promoted-icon-consistent", point)
