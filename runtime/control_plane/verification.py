from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class VerificationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class PredicateOperator(StrEnum):
    EQUALS = "equals"
    PRESENT = "present"
    ABSENT = "absent"


class FinishStatus(StrEnum):
    DONE = "done"
    NOT_DONE = "not_done"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationRef:
    """Stable reference to one concrete capability observation.

    ``sequence`` is owned by the observing adapter/session and must increase for
    every fresh observation of the same subject.  It is deliberately preferred
    over wall-clock freshness so verification does not depend on clock skew.
    """

    capability: str
    subject: str
    sequence: int
    fingerprint: str
    observed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.capability or not self.capability.strip():
            raise ValueError("observation capability must be non-empty")
        if not self.subject or not self.subject.strip():
            raise ValueError("observation subject must be non-empty")
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("observation sequence must be a non-negative integer")
        if not self.fingerprint or not self.fingerprint.strip():
            raise ValueError("observation fingerprint must be non-empty")

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "subject": self.subject,
            "sequence": self.sequence,
            "fingerprint": self.fingerprint,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True, slots=True)
class ObservationSnapshot:
    """Normalized current-state evidence supplied by a capability adapter.

    The kernel never obtains authority from ``state`` contents.  Capability
    adapters decide what state is safe/truthful to expose and whether it is a
    complete observation for the requested subject.
    """

    ref: ObservationRef
    state: Mapping[str, Any]
    complete: bool = True
    ambiguous: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state, Mapping):
            raise TypeError("observation state must be a mapping")


@dataclass(frozen=True, slots=True)
class StatePredicate:
    path: tuple[str, ...]
    operator: PredicateOperator
    expected: Any = None

    def __post_init__(self) -> None:
        if not self.path or any(not isinstance(part, str) or not part for part in self.path):
            raise ValueError("predicate path must contain non-empty string components")
        if not isinstance(self.operator, PredicateOperator):
            raise TypeError("predicate operator must be PredicateOperator")
        if self.operator in {PredicateOperator.PRESENT, PredicateOperator.ABSENT} and self.expected is not None:
            raise ValueError("present/absent predicates do not accept an expected value")

    @classmethod
    def equals(cls, *path: str, expected: Any) -> StatePredicate:
        return cls(path=tuple(path), operator=PredicateOperator.EQUALS, expected=expected)

    @classmethod
    def present(cls, *path: str) -> StatePredicate:
        return cls(path=tuple(path), operator=PredicateOperator.PRESENT)

    @classmethod
    def absent(cls, *path: str) -> StatePredicate:
        return cls(path=tuple(path), operator=PredicateOperator.ABSENT)


@dataclass(frozen=True, slots=True)
class ExpectedEffect:
    effect_id: str
    before: ObservationRef
    predicates: tuple[StatePredicate, ...]
    require_unambiguous: bool = True

    def __post_init__(self) -> None:
        if not self.effect_id or not self.effect_id.strip():
            raise ValueError("effect_id must be non-empty")
        if not self.predicates:
            raise ValueError("ExpectedEffect requires at least one predicate")
        if any(not isinstance(item, StatePredicate) for item in self.predicates):
            raise TypeError("ExpectedEffect predicates must be StatePredicate instances")


@dataclass(frozen=True, slots=True)
class PredicateResult:
    path: tuple[str, ...]
    operator: PredicateOperator
    status: VerificationStatus
    expected: Any
    observed: Any
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": list(self.path),
            "operator": self.operator.value,
            "status": self.status.value,
            "expected": self.expected,
            "observed": self.observed,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class VerificationResult:
    effect_id: str
    status: VerificationStatus
    reason: str
    observation: ObservationRef | None
    predicate_results: tuple[PredicateResult, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "status": self.status.value,
            "reason": self.reason,
            "observation": self.observation.as_dict() if self.observation is not None else None,
            "predicate_results": [item.as_dict() for item in self.predicate_results],
        }


@dataclass(frozen=True, slots=True)
class FinishGateResult:
    status: FinishStatus
    reason: str
    task_success: VerificationStatus
    safety: VerificationStatus
    goals: VerificationStatus
    constraints: VerificationStatus
    freshness: VerificationStatus
    unresolved: tuple[str, ...]
    candidate_done: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "task_success": self.task_success.value,
            "safety": self.safety.value,
            "goals": self.goals.value,
            "constraints": self.constraints.value,
            "freshness": self.freshness.value,
            "unresolved": list(self.unresolved),
            "candidate_done": self.candidate_done,
        }


_MISSING = object()


def _lookup(state: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = state
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _evaluate_predicate(predicate: StatePredicate, snapshot: ObservationSnapshot) -> PredicateResult:
    observed = _lookup(snapshot.state, predicate.path)

    if predicate.operator is PredicateOperator.EQUALS:
        if observed is _MISSING:
            status = VerificationStatus.FAIL if snapshot.complete else VerificationStatus.UNKNOWN
            return PredicateResult(
                path=predicate.path,
                operator=predicate.operator,
                status=status,
                expected=predicate.expected,
                observed=None,
                reason="field_missing" if snapshot.complete else "field_not_observed",
            )
        if observed == predicate.expected:
            return PredicateResult(
                path=predicate.path,
                operator=predicate.operator,
                status=VerificationStatus.PASS,
                expected=predicate.expected,
                observed=observed,
                reason="equal",
            )
        return PredicateResult(
            path=predicate.path,
            operator=predicate.operator,
            status=VerificationStatus.FAIL,
            expected=predicate.expected,
            observed=observed,
            reason="not_equal",
        )

    if predicate.operator is PredicateOperator.PRESENT:
        if observed is _MISSING:
            status = VerificationStatus.FAIL if snapshot.complete else VerificationStatus.UNKNOWN
            return PredicateResult(
                path=predicate.path,
                operator=predicate.operator,
                status=status,
                expected=None,
                observed=None,
                reason="field_missing" if snapshot.complete else "field_not_observed",
            )
        return PredicateResult(
            path=predicate.path,
            operator=predicate.operator,
            status=VerificationStatus.PASS,
            expected=None,
            observed=observed,
            reason="present",
        )

    if observed is _MISSING:
        status = VerificationStatus.PASS if snapshot.complete else VerificationStatus.UNKNOWN
        return PredicateResult(
            path=predicate.path,
            operator=predicate.operator,
            status=status,
            expected=None,
            observed=None,
            reason="absent" if snapshot.complete else "absence_not_proven",
        )
    return PredicateResult(
        path=predicate.path,
        operator=predicate.operator,
        status=VerificationStatus.FAIL,
        expected=None,
        observed=observed,
        reason="unexpectedly_present",
    )


def combine_statuses(
    statuses: Sequence[VerificationStatus],
    *,
    empty: VerificationStatus = VerificationStatus.UNKNOWN,
) -> VerificationStatus:
    if not statuses:
        return empty
    if any(item is VerificationStatus.FAIL for item in statuses):
        return VerificationStatus.FAIL
    if any(item is VerificationStatus.UNKNOWN for item in statuses):
        return VerificationStatus.UNKNOWN
    return VerificationStatus.PASS


def verify_expected_effect(effect: ExpectedEffect, after: ObservationSnapshot) -> VerificationResult:
    """Verify one effect against a fresh observation, without authorizing action.

    Capability/subject mismatch, stale observation sequence, ambiguity, or
    incomplete required evidence yields ``UNKNOWN`` rather than guessing.
    """

    if after.ref.capability != effect.before.capability:
        return VerificationResult(
            effect_id=effect.effect_id,
            status=VerificationStatus.UNKNOWN,
            reason="capability_mismatch",
            observation=after.ref,
        )
    if after.ref.subject != effect.before.subject:
        return VerificationResult(
            effect_id=effect.effect_id,
            status=VerificationStatus.UNKNOWN,
            reason="subject_mismatch",
            observation=after.ref,
        )
    if after.ref.sequence <= effect.before.sequence:
        return VerificationResult(
            effect_id=effect.effect_id,
            status=VerificationStatus.UNKNOWN,
            reason="stale_observation",
            observation=after.ref,
        )
    if effect.require_unambiguous and after.ambiguous:
        return VerificationResult(
            effect_id=effect.effect_id,
            status=VerificationStatus.UNKNOWN,
            reason="ambiguous_observation",
            observation=after.ref,
        )

    results = tuple(_evaluate_predicate(predicate, after) for predicate in effect.predicates)
    status = combine_statuses(tuple(item.status for item in results))
    if status is VerificationStatus.PASS:
        reason = "expected_effect_verified"
    elif status is VerificationStatus.FAIL:
        reason = "expected_effect_failed"
    else:
        reason = "expected_effect_unknown"
    return VerificationResult(
        effect_id=effect.effect_id,
        status=status,
        reason=reason,
        observation=after.ref,
        predicate_results=results,
    )


def aggregate_results(
    results: Sequence[VerificationResult],
    *,
    empty: VerificationStatus = VerificationStatus.UNKNOWN,
) -> VerificationStatus:
    return combine_statuses(tuple(item.status for item in results), empty=empty)


def evaluate_finish_gate(
    *,
    candidate_done: bool,
    goal_results: Sequence[VerificationResult],
    safety_results: Sequence[VerificationResult],
    constraint_results: Sequence[VerificationResult] = (),
    freshness_results: Sequence[VerificationResult] = (),
    unresolved: Sequence[str] = (),
) -> FinishGateResult:
    """Independently decide task completion from fresh verification evidence.

    ``candidate_done`` is only a planner proposal.  The gate requires explicit
    goal and safety evidence.  Missing goal/safety evidence is ``UNKNOWN``;
    absent optional constraints/freshness dimensions are vacuously satisfied.
    Task-success and safety remain separate outputs even when final completion is
    denied.
    """

    goals = aggregate_results(goal_results, empty=VerificationStatus.UNKNOWN)
    constraints = aggregate_results(constraint_results, empty=VerificationStatus.PASS)
    freshness = aggregate_results(freshness_results, empty=VerificationStatus.PASS)
    safety = aggregate_results(safety_results, empty=VerificationStatus.UNKNOWN)

    task_success = combine_statuses((goals, constraints, freshness))
    normalized_unresolved = tuple(str(item) for item in unresolved if str(item))
    if normalized_unresolved and task_success is VerificationStatus.PASS:
        task_success = VerificationStatus.UNKNOWN

    if not candidate_done:
        status = FinishStatus.NOT_DONE
        reason = "candidate_done_not_proposed"
    elif task_success is VerificationStatus.FAIL or safety is VerificationStatus.FAIL:
        status = FinishStatus.NOT_DONE
        reason = "completion_predicate_failed"
    elif task_success is VerificationStatus.UNKNOWN or safety is VerificationStatus.UNKNOWN:
        status = FinishStatus.UNKNOWN
        reason = "completion_evidence_unknown"
    else:
        status = FinishStatus.DONE
        reason = "finish_gate_verified"

    return FinishGateResult(
        status=status,
        reason=reason,
        task_success=task_success,
        safety=safety,
        goals=goals,
        constraints=constraints,
        freshness=freshness,
        unresolved=normalized_unresolved,
        candidate_done=candidate_done,
    )
