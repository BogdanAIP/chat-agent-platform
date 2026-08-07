from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import load_yaml_compatible
from .errors import PolicyDenied, ValidationError


@dataclass(frozen=True)
class PolicyDecision:
    decision_id: str
    capability: str
    effective_risk: str
    enforced_by: str
    reasons: list[str]


class PolicyEnforcementPoint:
    def __init__(self, policy_path: Path):
        self._rules = load_yaml_compatible(policy_path).get("rules", {})

    def evaluate(
        self,
        capability: str,
        *,
        parameters: dict[str, Any],
        data_class: str,
        requested_risk_hint: str | None = None,
    ) -> PolicyDecision:
        rule = self._rules.get(capability)
        if not rule:
            raise PolicyDenied(f"No policy rule exists for capability {capability}")

        configured = rule.get("decision", "deny")
        allowed_classes = rule.get("allowed_data_classes", [])
        reasons = [f"configured_decision={configured}", f"data_class={data_class}"]
        if requested_risk_hint is not None:
            reasons.append("requested_risk_hint_ignored_for_enforcement")

        if configured == "deny":
            raise PolicyDenied(f"Capability denied by policy: {capability}")
        if data_class not in allowed_classes:
            raise PolicyDenied(f"Data class {data_class!r} is not allowed for {capability}")
        if parameters.get("external_destination"):
            raise PolicyDenied("media.inspect does not permit external destinations")
        if configured not in {"allow", "guarded"}:
            raise ValidationError(f"Unknown policy decision: {configured}")

        return PolicyDecision(
            decision_id=f"pol_{uuid4().hex}",
            capability=capability,
            effective_risk=configured,
            enforced_by=rule.get("enforced_by", "unknown"),
            reasons=reasons,
        )
