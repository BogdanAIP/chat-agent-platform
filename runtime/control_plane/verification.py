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
    """Stable reference to one concrete capability observation stream.

    ``stream_id`` binds sequence numbers to one adapter/session-owned stream.
    ``sequence`` must increase for every fresh observation of the same subject
    inside that stream.  This is deliberately preferred over wall-clock
    freshness so verification does not depend on clock skew.
    """

    capability: str
    subject: str
    stream_id: str
    sequence: int
    fingerprint: str
    observed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.capability or not self.capability.strip():
            raise ValueError("observation capability must be non-empty")
        if not self.subject or not self.subject.strip():
            raise ValueError("observation subject must be non-empty")
        if not self.stream_id or not self.stream_id.strip():
            raise ValueError("observation stream_id must be non-empty")
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("observation sequence must be a non-negative integer")
        if not self.fingerprint or not self.fingerprint.strip():
            raise ValueError("observation fingerprint must be non-empty")

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "subject": self.subject,
            "stream_id": self.stream_id,
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
        if not isinstance(self.ref, ObservationRef):
            raise TypeError("observation ref must be ObservationRef")
        if not isinstance(self.state, Mapping):
            raise TypeError("observation state must be a mapping")
        if type(self.complete) is not bool or type(self.ambiguous) is not bool:
            raise TypeError("observation complete/ambiguous flags must be bool")


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
        if not isinstance(self.before, ObservationRef):
            raise TypeError("ExpectedEffect before must be ObservationRef")
        if not self.predicates:
            raise ValueError("ExpectedEffect requires at least one predicate")
        if any(not isinstance(item, StatePredicate) for item in self.predicates):
            raise TypeError("ExpectedEffect predicates must be StatePredicate instances")
        if type(self.require_unambiguous) is not bool:
            raise TypeError("require_unambiguous must be bool")


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

    def __post_init__(self) -> None:
        if not self.effect_id or not self.effect_id.strip():
            raise ValueError("verification result effect_id must be non-empty")
        if not isinstance(self.status, VerificationStatus):
            raise TypeError("verification result status must be VerificationStatus")
        if not self.reason or not self.reason.strip():
            raise ValueError("verification result reason must be non-empty")
        if self.observation is not None and not isinstance(self.observation, ObservationRef):
            raise TypeError("verification result observation must be ObservationRef or None")
        if any(not isinstance(item, PredicateResult) for item in self.predicate_results):
            raise TypeError("verification result predicate_results must contain PredicateResult")

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
    if any(not isinstance(item, VerificationStatus) for item in statuses):
        raise TypeError("statuses must contain VerificationStatus values")
    if any(item is VerificationStatus.FAIL for item in statuses):
        return VerificationStatus.FAIL
    if any(item is VerificationStatus.UNKNOWN for item in statuses):
        return VerificationStatus.UNKNOWN
    return VerificationStatus.PASS


def verify_expected_effect(effect: ExpectedEffect, after: ObservationSnapshot) -> VerificationResult:
    """Verify one effect against a fresh observation, without authorizing action.

    Stream/capability/subject mismatch, stale observation sequence, ambiguity, or
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
    if after.ref.stream_id != effect.before.stream_id:
        return VerificationResult(
            effect_id=effect.effect_id,
            status=VerificationStatus.UNKNOWN,
            reason="observation_stream_mismatch",
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
    if any(not isinstance(item, VerificationResult) for item in results):
        raise TypeError("results must contain VerificationResult values")
    return combine_statuses(tuple(item.status for item in results), empty=empty)


def _optional_dimension_status(results: Sequence[VerificationResult] | None) -> VerificationStatus:
    """None means the task declares no such dimension; empty means evidence is missing."""

    if results is None:
        return VerificationStatus.PASS
    return aggregate_results(results, empty=VerificationStatus.UNKNOWN)


def evaluate_finish_gate(
    *,
    candidate_done: bool,
    goal_results: Sequence[VerificationResult],
    safety_results: Sequence[VerificationResult],
    constraint_results: Sequence[VerificationResult] | None = None,
    freshness_results: Sequence[VerificationResult] | None = None,
    unresolved: Sequence[str] = (),
) -> FinishGateResult:
    """Independently decide task completion from fresh verification evidence.

    ``candidate_done`` is only a planner proposal.  Goal and safety evidence are
    always required.  For constraint/freshness dimensions, ``None`` explicitly
    means the task declares no such dimension, while an empty sequence means the
    dimension exists but has no evidence and therefore remains ``UNKNOWN``.

    Task-success, unresolved completion requirements and safety remain distinct
    outputs/gates even when they deny final completion together.
    """

    if type(candidate_done) is not bool:
        raise TypeError("candidate_done must be bool")

    goals = aggregate_results(goal_results, empty=VerificationStatus.UNKNOWN)
    constraints = _optional_dimension_status(constraint_results)
    freshness = _optional_dimension_status(freshness_results)
    safety = aggregate_results(safety_results, empty=VerificationStatus.UNKNOWN)
    task_success = combine_statuses((goals, constraints, freshness))

    normalized_unresolved = tuple(str(item) for item in unresolved if str(item))

    if not candidate_done:
        status = FinishStatus.NOT_DONE
        reason = "candidate_done_not_proposed"
    elif task_success is VerificationStatus.FAIL or safety is VerificationStatus.FAIL:
        status = FinishStatus.NOT_DONE
        reason = "completion_predicate_failed"
    elif normalized_unresolved:
        status = FinishStatus.UNKNOWN
        reason = "unresolved_completion_requirement"
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
