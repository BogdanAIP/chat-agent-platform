from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Any


_MAX_NORMALIZED_DEPTH = 12
_MAX_NORMALIZED_NODES = 4096
_MAX_COLLECTION_ITEMS = 1024
_MAX_STRING_CHARS = 65536
_MAX_KEY_CHARS = 256
_MAX_ID_CHARS = 512


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


def _require_text(value: Any, *, name: str, max_chars: int = _MAX_ID_CHARS) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def _freeze_normalized(
    value: Any,
    *,
    name: str,
    depth: int = 0,
    budget: list[int] | None = None,
) -> Any:
    """Validate and freeze bounded JSON-like evidence/predicate data.

    Only plain builtins are accepted. This keeps predicate evaluation free from
    user-defined equality/mapping behavior and prevents callers from mutating an
    observation payload after the snapshot is constructed.
    """

    if budget is None:
        budget = [0]
    budget[0] += 1
    if budget[0] > _MAX_NORMALIZED_NODES:
        raise ValueError(f"{name} exceeds {_MAX_NORMALIZED_NODES} normalized nodes")
    if depth > _MAX_NORMALIZED_DEPTH:
        raise ValueError(f"{name} exceeds normalized depth {_MAX_NORMALIZED_DEPTH}")

    value_type = type(value)
    if value is None or value_type is bool or value_type is int:
        return value
    if value_type is float:
        if not isfinite(value):
            raise ValueError(f"{name} contains a non-finite float")
        return value
    if value_type is str:
        if len(value) > _MAX_STRING_CHARS:
            raise ValueError(f"{name} contains a string longer than {_MAX_STRING_CHARS} characters")
        return value
    if value_type is list:
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise ValueError(f"{name} list exceeds {_MAX_COLLECTION_ITEMS} items")
        return tuple(
            _freeze_normalized(item, name=name, depth=depth + 1, budget=budget)
            for item in value
        )
    if value_type is dict:
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise ValueError(f"{name} mapping exceeds {_MAX_COLLECTION_ITEMS} items")
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{name} mapping keys must be strings")
            if not key:
                raise ValueError(f"{name} mapping keys must be non-empty")
            if len(key) > _MAX_KEY_CHARS:
                raise ValueError(f"{name} mapping key exceeds {_MAX_KEY_CHARS} characters")
            frozen[key] = _freeze_normalized(
                item,
                name=name,
                depth=depth + 1,
                budget=budget,
            )
        return MappingProxyType(frozen)
    raise TypeError(f"{name} must contain only plain JSON-like values")


def _thaw_normalized(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_normalized(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_thaw_normalized(item) for item in value]
    return value


def _normalized_equal(left: Any, right: Any) -> bool:
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            return False
        if set(left.keys()) != set(right.keys()):
            return False
        return all(_normalized_equal(left[key], right[key]) for key in left)
    if type(left) is tuple or type(right) is tuple:
        if type(left) is not tuple or type(right) is not tuple or len(left) != len(right):
            return False
        return all(_normalized_equal(a, b) for a, b in zip(left, right, strict=True))
    return type(left) is type(right) and left == right


@dataclass(frozen=True, slots=True)
class ObservationRef:
    """Stable reference to one concrete capability observation stream."""

    capability: str
    subject: str
    stream_id: str
    sequence: int
    fingerprint: str
    observed_at: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.capability, name="observation capability")
        _require_text(self.subject, name="observation subject")
        _require_text(self.stream_id, name="observation stream_id")
        _require_text(self.fingerprint, name="observation fingerprint", max_chars=2048)
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("observation sequence must be a non-negative integer")
        if self.observed_at is not None:
            _require_text(self.observed_at, name="observed_at", max_chars=256)

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
    """Bounded immutable normalized state supplied by a capability adapter."""

    ref: ObservationRef
    state: Mapping[str, Any]
    complete: bool = True
    ambiguous: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.ref, ObservationRef):
            raise TypeError("observation ref must be ObservationRef")
        if type(self.state) is not dict:
            raise TypeError("observation state must be a plain dict")
        if type(self.complete) is not bool or type(self.ambiguous) is not bool:
            raise TypeError("observation complete/ambiguous flags must be bool")
        object.__setattr__(
            self,
            "state",
            _freeze_normalized(self.state, name="observation state"),
        )


@dataclass(frozen=True, slots=True)
class StatePredicate:
    path: tuple[str, ...]
    operator: PredicateOperator
    expected: Any = None

    def __post_init__(self) -> None:
        if type(self.path) is not tuple or not self.path:
            raise ValueError("predicate path must be a non-empty tuple")
        if any(type(part) is not str or not part or len(part) > _MAX_KEY_CHARS for part in self.path):
            raise ValueError("predicate path must contain bounded non-empty string components")
        if not isinstance(self.operator, PredicateOperator):
            raise TypeError("predicate operator must be PredicateOperator")
        if self.operator in {PredicateOperator.PRESENT, PredicateOperator.ABSENT}:
            if self.expected is not None:
                raise ValueError("present/absent predicates do not accept an expected value")
        else:
            object.__setattr__(
                self,
                "expected",
                _freeze_normalized(self.expected, name="predicate expected value"),
            )

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
        _require_text(self.effect_id, name="effect_id")
        if not isinstance(self.before, ObservationRef):
            raise TypeError("ExpectedEffect before must be ObservationRef")
        if type(self.predicates) is not tuple or not self.predicates:
            raise ValueError("ExpectedEffect requires a non-empty predicate tuple")
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
            "expected": _thaw_normalized(self.expected),
            "observed": _thaw_normalized(self.observed),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class VerificationResult:
    effect_id: str
    status: VerificationStatus
    reason: str
    observation: ObservationRef | None
    evidence_batch_id: str | None = None
    predicate_results: tuple[PredicateResult, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.effect_id, name="verification result effect_id")
        if not isinstance(self.status, VerificationStatus):
            raise TypeError("verification result status must be VerificationStatus")
        _require_text(self.reason, name="verification result reason")
        if self.observation is not None and not isinstance(self.observation, ObservationRef):
            raise TypeError("verification result observation must be ObservationRef or None")
        if self.evidence_batch_id is not None:
            _require_text(self.evidence_batch_id, name="evidence_batch_id")
        if type(self.predicate_results) is not tuple:
            raise TypeError("verification result predicate_results must be a tuple")
        if any(not isinstance(item, PredicateResult) for item in self.predicate_results):
            raise TypeError("verification result predicate_results must contain PredicateResult")

    def as_dict(self) -> dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "status": self.status.value,
            "reason": self.reason,
            "observation": self.observation.as_dict() if self.observation is not None else None,
            "evidence_batch_id": self.evidence_batch_id,
            "predicate_results": [item.as_dict() for item in self.predicate_results],
        }


@dataclass(frozen=True, slots=True)
class FinishGateResult:
    status: FinishStatus
    reason: str
    evidence_batch_id: str
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
            "evidence_batch_id": self.evidence_batch_id,
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
        if _normalized_equal(observed, predicate.expected):
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
    if not isinstance(empty, VerificationStatus):
        raise TypeError("empty must be VerificationStatus")
    if not statuses:
        return empty
    if any(not isinstance(item, VerificationStatus) for item in statuses):
        raise TypeError("statuses must contain VerificationStatus values")
    if any(item is VerificationStatus.FAIL for item in statuses):
        return VerificationStatus.FAIL
    if any(item is VerificationStatus.UNKNOWN for item in statuses):
        return VerificationStatus.UNKNOWN
    return VerificationStatus.PASS


def verify_expected_effect(
    effect: ExpectedEffect,
    after: ObservationSnapshot,
    *,
    evidence_batch_id: str | None = None,
) -> VerificationResult:
    """Verify one effect against a fresh observation, without authorizing action."""

    if not isinstance(effect, ExpectedEffect):
        raise TypeError("effect must be ExpectedEffect")
    if not isinstance(after, ObservationSnapshot):
        raise TypeError("after must be ObservationSnapshot")
    if evidence_batch_id is not None:
        _require_text(evidence_batch_id, name="evidence_batch_id")

    def result(status: VerificationStatus, reason: str) -> VerificationResult:
        return VerificationResult(
            effect_id=effect.effect_id,
            status=status,
            reason=reason,
            observation=after.ref,
            evidence_batch_id=evidence_batch_id,
        )

    if after.ref.capability != effect.before.capability:
        return result(VerificationStatus.UNKNOWN, "capability_mismatch")
    if after.ref.subject != effect.before.subject:
        return result(VerificationStatus.UNKNOWN, "subject_mismatch")
    if after.ref.stream_id != effect.before.stream_id:
        return result(VerificationStatus.UNKNOWN, "observation_stream_mismatch")
    if after.ref.sequence <= effect.before.sequence:
        return result(VerificationStatus.UNKNOWN, "stale_observation")
    if effect.require_unambiguous and after.ambiguous:
        return result(VerificationStatus.UNKNOWN, "ambiguous_observation")

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
        evidence_batch_id=evidence_batch_id,
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


def _evidence_bound_status(
    results: Sequence[VerificationResult],
    *,
    empty: VerificationStatus,
    evidence_batch_id: str,
) -> VerificationStatus:
    if not results:
        return empty
    if any(not isinstance(item, VerificationResult) for item in results):
        raise TypeError("finish-gate results must contain VerificationResult values")
    if any(item.observation is None for item in results):
        return VerificationStatus.UNKNOWN
    if any(item.evidence_batch_id != evidence_batch_id for item in results):
        return VerificationStatus.UNKNOWN
    return aggregate_results(results, empty=empty)


def _optional_dimension_status(
    results: Sequence[VerificationResult] | None,
    *,
    evidence_batch_id: str,
) -> VerificationStatus:
    """None = not declared; empty sequence = declared but evidence missing."""

    if results is None:
        return VerificationStatus.PASS
    return _evidence_bound_status(
        results,
        empty=VerificationStatus.UNKNOWN,
        evidence_batch_id=evidence_batch_id,
    )


def evaluate_finish_gate(
    *,
    evidence_batch_id: str,
    candidate_done: bool,
    goal_results: Sequence[VerificationResult],
    safety_results: Sequence[VerificationResult],
    constraint_results: Sequence[VerificationResult] | None = None,
    freshness_results: Sequence[VerificationResult] | None = None,
    unresolved: Sequence[str] = (),
) -> FinishGateResult:
    """Independently decide task completion from one evidence collection batch."""

    _require_text(evidence_batch_id, name="evidence_batch_id")
    if type(candidate_done) is not bool:
        raise TypeError("candidate_done must be bool")
    if isinstance(unresolved, (str, bytes)) or not isinstance(unresolved, Sequence):
        raise TypeError("unresolved completion requirements must be a sequence of strings")
    if any(type(item) is not str for item in unresolved):
        raise TypeError("unresolved completion requirements must be strings")
    if any(not item.strip() for item in unresolved):
        raise ValueError("unresolved completion requirements must be non-empty")
    if len(set(unresolved)) != len(unresolved):
        raise ValueError("unresolved completion requirements must be unique")

    goals = _evidence_bound_status(
        goal_results,
        empty=VerificationStatus.UNKNOWN,
        evidence_batch_id=evidence_batch_id,
    )
    constraints = _optional_dimension_status(
        constraint_results,
        evidence_batch_id=evidence_batch_id,
    )
    freshness = _optional_dimension_status(
        freshness_results,
        evidence_batch_id=evidence_batch_id,
    )
    safety = _evidence_bound_status(
        safety_results,
        empty=VerificationStatus.UNKNOWN,
        evidence_batch_id=evidence_batch_id,
    )
    task_success = combine_statuses((goals, constraints, freshness))
    normalized_unresolved = tuple(unresolved)

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
        evidence_batch_id=evidence_batch_id,
        task_success=task_success,
        safety=safety,
        goals=goals,
        constraints=constraints,
        freshness=freshness,
        unresolved=normalized_unresolved,
        candidate_done=candidate_done,
    )
