from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import StrEnum
from typing import Any, Mapping

from .verification import ObservationRef, VerificationResult, VerificationStatus

SCHEMA_VERSION = 1
_MAX_TEXT = 1024
_MAX_MESSAGE = 4096
_MAX_REFS = 256
_MAX_HISTORY = 2048


class FailureCategory(StrEnum):
    TARGET_MISSING = "target_missing"
    TARGET_AMBIGUOUS = "target_ambiguous"
    STALE_STATE = "stale_state"
    ACTION_NO_EFFECT = "action_no_effect"
    PARTIAL_EFFECT = "partial_effect"
    UNEXPECTED_DIALOG = "unexpected_dialog"
    NAVIGATION_CHANGED = "navigation_changed"
    TOOL_UNAVAILABLE = "tool_unavailable"
    PERMISSION_DENIED = "permission_denied"
    UNSAFE_TRANSITION = "unsafe_transition"
    EXTERNAL_CHANGE = "external_change"
    VERIFICATION_FAILED = "verification_failed"
    RUNTIME_UNCERTAIN = "runtime_uncertain"
    BUDGET_EXHAUSTED = "budget_exhausted"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    ACTOR_MISMATCH = "actor_mismatch"
    EVIDENCE_MISMATCH = "evidence_mismatch"
    LOOP_DETECTED = "loop_detected"


class MutatingOutcome(StrEnum):
    VERIFIED_APPLIED = "verified_applied"
    NOT_APPLIED = "not_applied"
    APPLIED_BUT_ACK_FAILED = "applied_but_ack_failed"
    OUTCOME_UNKNOWN = "outcome_unknown"


class ReconciliationStatus(StrEnum):
    CONFIRMED_APPLIED = "confirmed_applied"
    CONFIRMED_NOT_APPLIED = "confirmed_not_applied"
    STILL_UNKNOWN = "still_unknown"


class BudgetKind(StrEnum):
    TASK = "task"
    PROCEDURE = "procedure"
    STRATEGY = "strategy"


class GuardStatus(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"


def _text(value: Any, *, name: str, max_chars: int = _MAX_TEXT) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def _optional_text(value: Any, *, name: str) -> str | None:
    return None if value is None else _text(value, name=name)


def _refs(values: Any, *, name: str) -> tuple[str, ...]:
    if type(values) not in (tuple, list):
        raise TypeError(f"{name} must be a tuple/list")
    if len(values) > _MAX_REFS:
        raise ValueError(f"{name} exceeds {_MAX_REFS} items")
    return tuple(_text(item, name=f"{name} item") for item in values)


def _items(values: Any, *, name: str) -> tuple[Any, ...]:
    if type(values) not in (tuple, list):
        raise TypeError(f"{name} must be a tuple/list")
    if len(values) > _MAX_HISTORY:
        raise ValueError(f"{name} exceeds {_MAX_HISTORY} items")
    return tuple(values)


def _json_value(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, ObservationRef):
        return value.as_dict()
    if is_dataclass(value):
        return {item.name: _json_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) in (tuple, list):
        return [_json_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise TypeError(f"unsupported durable WorkingState value: {type(value).__name__}")


def _plain_dict(value: Any, *, name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise TypeError(f"{name} must be an object")
    return value


def _shape(value: Any, *, name: str, keys: set[str]) -> dict[str, Any]:
    raw = _plain_dict(value, name=name)
    missing = keys - set(raw)
    unknown = set(raw) - keys
    if missing or unknown:
        raise ValueError(
            f"{name} shape mismatch; missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    return raw


def _observation(value: Any, *, name: str) -> ObservationRef:
    if isinstance(value, ObservationRef):
        return value
    raw = _shape(
        value,
        name=name,
        keys={"capability", "subject", "stream_id", "sequence", "fingerprint", "observed_at"},
    )
    return ObservationRef(
        capability=raw["capability"],
        subject=raw["subject"],
        stream_id=raw["stream_id"],
        sequence=raw["sequence"],
        fingerprint=raw["fingerprint"],
        observed_at=raw["observed_at"],
    )


def _same_stream(left: ObservationRef, right: ObservationRef) -> bool:
    return (
        left.capability == right.capability
        and left.subject == right.subject
        and left.stream_id == right.stream_id
    )


def reconciliation_effect_id(
    operation_id: str,
    attempt_revision: int,
    status: ReconciliationStatus,
) -> str:
    _text(operation_id, name="reconciliation operation_id")
    if type(attempt_revision) is not int or attempt_revision <= 0:
        raise ValueError("reconciliation attempt_revision must be positive")
    if not isinstance(status, ReconciliationStatus):
        raise TypeError("reconciliation status must be ReconciliationStatus")
    return f"reconcile:{operation_id}:{attempt_revision}:{status.value}"


@dataclass(frozen=True, slots=True)
class FailureReason:
    code: str
    category: FailureCategory
    message: str
    retryable: bool
    reconciliation_required: bool = False
    operation_id: str | None = None
    strategy_id: str | None = None
    outcome: MutatingOutcome | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.code, name="failure code")
        if not isinstance(self.category, FailureCategory):
            raise TypeError("failure category must be FailureCategory")
        _text(self.message, name="failure message", max_chars=_MAX_MESSAGE)
        if type(self.retryable) is not bool or type(self.reconciliation_required) is not bool:
            raise TypeError("failure retry flags must be bool")
        _optional_text(self.operation_id, name="failure operation_id")
        _optional_text(self.strategy_id, name="failure strategy_id")
        if self.outcome is not None and not isinstance(self.outcome, MutatingOutcome):
            raise TypeError("failure outcome must be MutatingOutcome or None")
        object.__setattr__(
            self, "evidence_refs", _refs(self.evidence_refs, name="failure evidence_refs")
        )
        if self.outcome is MutatingOutcome.OUTCOME_UNKNOWN and not self.reconciliation_required:
            raise ValueError("OUTCOME_UNKNOWN failure must require reconciliation")
        if self.outcome is MutatingOutcome.APPLIED_BUT_ACK_FAILED:
            if self.retryable:
                raise ValueError("APPLIED_BUT_ACK_FAILED failure cannot be directly retryable")
            if not self.reconciliation_required:
                raise ValueError("APPLIED_BUT_ACK_FAILED failure must require reconciliation")

    def as_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True, slots=True)
class BudgetState:
    kind: BudgetKind
    scope_id: str
    limit: int
    used: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.kind, BudgetKind):
            raise TypeError("budget kind must be BudgetKind")
        _text(self.scope_id, name="budget scope_id")
        if type(self.limit) is not int or self.limit <= 0:
            raise ValueError("budget limit must be positive")
        if type(self.used) is not int or not 0 <= self.used <= self.limit:
            raise ValueError("budget used must be within 0..limit")

    @property
    def remaining(self) -> int:
        return self.limit - self.used

    def consume(self) -> "BudgetState":
        if self.remaining <= 0:
            raise ValueError("budget exhausted")
        return replace(self, used=self.used + 1)


@dataclass(frozen=True, slots=True)
class AttemptIntent:
    operation_id: str
    strategy_id: str
    action_fingerprint: str
    observation_ref: ObservationRef
    actor_ref: str | None = None
    execution_environment_ref: str | None = None
    evidence_scope_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.operation_id, name="attempt operation_id")
        _text(self.strategy_id, name="attempt strategy_id")
        _text(self.action_fingerprint, name="action fingerprint", max_chars=2048)
        if not isinstance(self.observation_ref, ObservationRef):
            raise TypeError("attempt observation_ref must be ObservationRef")
        _optional_text(self.actor_ref, name="attempt actor_ref")
        _optional_text(self.execution_environment_ref, name="attempt execution_environment_ref")
        _optional_text(self.evidence_scope_ref, name="attempt evidence_scope_ref")
        object.__setattr__(
            self, "evidence_refs", _refs(self.evidence_refs, name="attempt evidence_refs")
        )
        if self.evidence_scope_ref is not None and self.observation_ref.stream_id != self.evidence_scope_ref:
            raise ValueError("attempt observation stream must match evidence_scope_ref")

    @property
    def pre_state_fingerprint(self) -> str:
        return self.observation_ref.fingerprint

    @property
    def physical_fingerprint(self) -> str:
        payload = {
            "action": self.action_fingerprint,
            "pre_state": self.observation_ref.fingerprint,
            "capability": self.observation_ref.capability,
            "subject": self.observation_ref.subject,
            "stream": self.observation_ref.stream_id,
            "actor": self.actor_ref,
            "environment": self.execution_environment_ref,
            "evidence_scope": self.evidence_scope_ref,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @property
    def authorization_fingerprint(self) -> str:
        payload = {
            "operation_id": self.operation_id,
            "strategy_id": self.strategy_id,
            "action_fingerprint": self.action_fingerprint,
            "observation": self.observation_ref.as_dict(),
            "actor_ref": self.actor_ref,
            "execution_environment_ref": self.execution_environment_ref,
            "evidence_scope_ref": self.evidence_scope_ref,
            "evidence_refs": list(self.evidence_refs),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    intent: AttemptIntent
    outcome: MutatingOutcome
    revision_before: int
    revision_after: int
    failure: FailureReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.intent, AttemptIntent) or not isinstance(self.outcome, MutatingOutcome):
            raise TypeError("attempt record has invalid intent/outcome")
        if type(self.revision_before) is not int or self.revision_before < 0:
            raise ValueError("attempt revision_before must be non-negative")
        if type(self.revision_after) is not int or self.revision_after != self.revision_before + 1:
            raise ValueError("attempt revision_after must equal revision_before + 1")
        if self.outcome is MutatingOutcome.VERIFIED_APPLIED:
            if self.failure is not None:
                raise ValueError("VERIFIED_APPLIED attempt cannot carry failure")
        elif not isinstance(self.failure, FailureReason):
            raise ValueError("non-successful mutating outcome requires structured failure")
        if self.failure is not None:
            if self.failure.outcome is not self.outcome:
                raise ValueError("attempt failure outcome mismatch")
            if self.failure.operation_id not in (None, self.intent.operation_id):
                raise ValueError("attempt failure operation mismatch")
            if self.failure.strategy_id not in (None, self.intent.strategy_id):
                raise ValueError("attempt failure strategy mismatch")


@dataclass(frozen=True, slots=True)
class ReconciliationRecord:
    operation_id: str
    attempt_revision: int
    status: ReconciliationStatus
    revision_after: int
    observation_ref: ObservationRef
    verification_effect_id: str
    evidence_batch_id: str

    def __post_init__(self) -> None:
        _text(self.operation_id, name="reconciliation operation_id")
        if type(self.attempt_revision) is not int or self.attempt_revision <= 0:
            raise ValueError("reconciliation attempt_revision must be positive")
        if not isinstance(self.status, ReconciliationStatus):
            raise TypeError("reconciliation status must be ReconciliationStatus")
        if type(self.revision_after) is not int or self.revision_after <= self.attempt_revision:
            raise ValueError("reconciliation revision_after must follow attempt revision")
        if not isinstance(self.observation_ref, ObservationRef):
            raise TypeError("reconciliation observation_ref must be ObservationRef")
        _text(self.verification_effect_id, name="reconciliation verification_effect_id")
        _text(self.evidence_batch_id, name="reconciliation evidence_batch_id")


@dataclass(frozen=True, slots=True)
class GuardDecision:
    status: GuardStatus
    state_revision: int
    authorization_fingerprint: str
    failure: FailureReason | None = None

    @property
    def allowed(self) -> bool:
        return self.status is GuardStatus.ALLOW


@dataclass(frozen=True, slots=True)
class LoopGuardPolicy:
    max_identical_physical_attempts: int = 1
    oscillation_window: int = 4

    def __post_init__(self) -> None:
        if type(self.max_identical_physical_attempts) is not int or self.max_identical_physical_attempts < 1:
            raise ValueError("max_identical_physical_attempts must be >= 1")
        if type(self.oscillation_window) is not int or self.oscillation_window < 4 or self.oscillation_window % 2:
            raise ValueError("oscillation_window must be an even integer >= 4")


@dataclass(frozen=True, slots=True)
class StagnationReport:
    task_id: str
    state_revision: int
    recovery_epoch: int
    reason_code: str
    last_failure: FailureReason | None
    recent_physical_fingerprints: tuple[str, ...]
    exhausted_budgets: tuple[str, ...]
    candidate_done_current: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "stagnation_report",
            "authority": "diagnostic_only",
            **_json_value(self),
        }


@dataclass(frozen=True, slots=True)
class WorkingState:
    task_id: str
    revision: int
    recovery_epoch: int
    actor_ref: str | None
    delegation_ref: str | None
    execution_environment_ref: str | None
    evidence_scope_ref: str | None
    procedure_ref: str | None
    observation_ref: ObservationRef
    user_constraints: tuple[str, ...]
    subgoal_refs: tuple[str, ...]
    verified_achievements: tuple[str, ...]
    fact_refs: tuple[str, ...]
    open_ambiguities: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    capability_grant_refs: tuple[str, ...]
    budgets: tuple[BudgetState, ...]
    attempts: tuple[AttemptRecord, ...] = ()
    failures: tuple[FailureReason, ...] = ()
    reconciliations: tuple[ReconciliationRecord, ...] = ()
    candidate_done: bool = False
    candidate_done_revision: int | None = None

    def __post_init__(self) -> None:
        _text(self.task_id, name="task_id")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("revision must be non-negative")
        if type(self.recovery_epoch) is not int or self.recovery_epoch < 0:
            raise ValueError("recovery_epoch must be non-negative")
        for name in (
            "actor_ref", "delegation_ref", "execution_environment_ref",
            "evidence_scope_ref", "procedure_ref",
        ):
            _optional_text(getattr(self, name), name=name)
        if not isinstance(self.observation_ref, ObservationRef):
            raise TypeError("WorkingState observation_ref must be ObservationRef")
        if (
            self.evidence_scope_ref is not None
            and self.observation_ref.stream_id != self.evidence_scope_ref
        ):
            raise ValueError("WorkingState observation stream must match evidence_scope_ref")
        for name in (
            "user_constraints", "subgoal_refs", "verified_achievements", "fact_refs",
            "open_ambiguities", "evidence_refs", "capability_grant_refs",
        ):
            object.__setattr__(self, name, _refs(getattr(self, name), name=name))

        budgets = _items(self.budgets, name="budgets")
        if not budgets or any(not isinstance(item, BudgetState) for item in budgets):
            raise ValueError("WorkingState requires explicit BudgetState values")
        if len({(item.kind, item.scope_id) for item in budgets}) != len(budgets):
            raise ValueError("budget kind/scope pairs must be unique")
        object.__setattr__(self, "budgets", budgets)

        for name, item_type in (
            ("attempts", AttemptRecord),
            ("failures", FailureReason),
            ("reconciliations", ReconciliationRecord),
        ):
            items = _items(getattr(self, name), name=name)
            if any(not isinstance(item, item_type) for item in items):
                raise ValueError(f"{name} history is invalid")
            object.__setattr__(self, name, items)

        if any(attempt.revision_after > self.revision for attempt in self.attempts):
            raise ValueError("attempt history revision exceeds WorkingState revision")
        if any(
            left.revision_after >= right.revision_after
            for left, right in zip(self.attempts, self.attempts[1:])
        ):
            raise ValueError("attempt history revisions must be strictly increasing")

        for attempt in self.attempts:
            for name in (
                "actor_ref",
                "execution_environment_ref",
                "evidence_scope_ref",
            ):
                if getattr(attempt.intent, name) != getattr(self, name):
                    raise ValueError(
                        f"attempt {name} does not match WorkingState"
                    )
            if not _same_stream(attempt.intent.observation_ref, self.observation_ref):
                raise ValueError("attempt observation stream does not match WorkingState")
        if any(
            right.intent.observation_ref.sequence
            <= left.intent.observation_ref.sequence
            for left, right in zip(self.attempts, self.attempts[1:])
        ):
            raise ValueError("attempt observations must advance between physical attempts")
        if self.attempts:
            latest_observation = self.attempts[-1].intent.observation_ref
            if self.observation_ref.sequence < latest_observation.sequence:
                raise ValueError("current observation is older than latest attempt")
            if (
                self.observation_ref.sequence == latest_observation.sequence
                and self.observation_ref != latest_observation
            ):
                raise ValueError("current observation conflicts with latest attempt sequence")

        if any(
            reconciliation.revision_after > self.revision
            for reconciliation in self.reconciliations
        ):
            raise ValueError("reconciliation revision exceeds WorkingState revision")
        if any(
            left.revision_after >= right.revision_after
            for left, right in zip(self.reconciliations, self.reconciliations[1:])
        ):
            raise ValueError("reconciliation revisions must be strictly increasing")

        event_revisions = [item.revision_after for item in self.attempts] + [
            item.revision_after for item in self.reconciliations
        ]
        if len(event_revisions) != len(set(event_revisions)):
            raise ValueError("attempt/reconciliation event revisions must be unique")

        attempts_by_key = {
            (attempt.intent.operation_id, attempt.revision_after): attempt
            for attempt in self.attempts
        }
        latest_reconciliation_by_key: dict[
            tuple[str, int], ReconciliationRecord
        ] = {}
        for reconciliation in self.reconciliations:
            key = (reconciliation.operation_id, reconciliation.attempt_revision)
            attempt = attempts_by_key.get(key)
            if attempt is None:
                raise ValueError("reconciliation references unknown attempt")
            if attempt.outcome not in {
                MutatingOutcome.OUTCOME_UNKNOWN,
                MutatingOutcome.APPLIED_BUT_ACK_FAILED,
            }:
                raise ValueError("reconciliation references non-ambiguous attempt")
            if (
                attempt.outcome is MutatingOutcome.APPLIED_BUT_ACK_FAILED
                and reconciliation.status is ReconciliationStatus.CONFIRMED_NOT_APPLIED
            ):
                raise ValueError("ack-failed outcome cannot reconcile as not applied")
            if reconciliation.verification_effect_id != reconciliation_effect_id(
                reconciliation.operation_id,
                reconciliation.attempt_revision,
                reconciliation.status,
            ):
                raise ValueError("durable reconciliation effect_id mismatch")
            if not _same_stream(
                attempt.intent.observation_ref,
                reconciliation.observation_ref,
            ):
                raise ValueError("durable reconciliation observation stream mismatch")
            if (
                reconciliation.observation_ref.sequence
                <= attempt.intent.observation_ref.sequence
            ):
                raise ValueError("durable reconciliation observation is not fresh")
            if reconciliation.observation_ref.sequence > self.observation_ref.sequence:
                raise ValueError("reconciliation observation exceeds current WorkingState")
            if (
                reconciliation.observation_ref.sequence == self.observation_ref.sequence
                and reconciliation.observation_ref != self.observation_ref
            ):
                raise ValueError("conflicting observation identity at current sequence")

            prior = latest_reconciliation_by_key.get(key)
            if prior is not None:
                if prior.status is not ReconciliationStatus.STILL_UNKNOWN:
                    raise ValueError("resolved reconciliation cannot be replaced")
                if reconciliation.revision_after <= prior.revision_after:
                    raise ValueError("reconciliation revision must advance")
                if (
                    reconciliation.observation_ref.sequence
                    <= prior.observation_ref.sequence
                ):
                    raise ValueError("reconciliation refinement must use fresher evidence")
            latest_reconciliation_by_key[key] = reconciliation

        pending_reconciliation: set[tuple[str, int]] = set()
        applied_operations: set[str] = set()
        events: list[tuple[int, str, Any]] = [
            (item.revision_after, "attempt", item) for item in self.attempts
        ] + [
            (item.revision_after, "reconciliation", item)
            for item in self.reconciliations
        ]
        for _, kind, item in sorted(events, key=lambda event: event[0]):
            if kind == "attempt":
                attempt = item
                if pending_reconciliation:
                    raise ValueError("attempt occurred while reconciliation was pending")
                if attempt.intent.operation_id in applied_operations:
                    raise ValueError("applied logical operation was replayed in durable history")
                if attempt.outcome is MutatingOutcome.VERIFIED_APPLIED:
                    applied_operations.add(attempt.intent.operation_id)
                elif attempt.outcome in {
                    MutatingOutcome.OUTCOME_UNKNOWN,
                    MutatingOutcome.APPLIED_BUT_ACK_FAILED,
                }:
                    pending_reconciliation.add(
                        (attempt.intent.operation_id, attempt.revision_after)
                    )
                continue

            reconciliation = item
            key = (reconciliation.operation_id, reconciliation.attempt_revision)
            if key not in pending_reconciliation:
                raise ValueError("reconciliation did not match a pending ambiguous attempt")
            if reconciliation.status is ReconciliationStatus.STILL_UNKNOWN:
                continue
            pending_reconciliation.remove(key)
            if reconciliation.status is ReconciliationStatus.CONFIRMED_APPLIED:
                applied_operations.add(reconciliation.operation_id)

        expected_usage: dict[tuple[BudgetKind, str], int] = {}
        for attempt in self.attempts:
            for kind in (BudgetKind.TASK, BudgetKind.PROCEDURE, BudgetKind.STRATEGY):
                scope = self._budget_scope(kind, attempt.intent.strategy_id)
                expected_usage[(kind, scope)] = expected_usage.get((kind, scope), 0) + 1
        for budget in self.budgets:
            expected = expected_usage.get((budget.kind, budget.scope_id), 0)
            if budget.used != expected:
                raise ValueError(
                    f"budget history mismatch for {budget.kind.value}:{budget.scope_id}; "
                    f"used={budget.used} expected={expected}"
                )

        if type(self.candidate_done) is not bool:
            raise TypeError("candidate_done must be bool")
        if self.candidate_done_revision is not None and (
            type(self.candidate_done_revision) is not int
            or not 0 <= self.candidate_done_revision <= self.revision
        ):
            raise ValueError("candidate_done_revision is invalid")
        if self.candidate_done != (self.candidate_done_revision is not None):
            raise ValueError("candidate_done and candidate_done_revision must agree")

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        task_budget: int,
        procedure_budget: int,
        strategy_budgets: Mapping[str, int],
        observation_ref: ObservationRef,
        actor_ref: str | None = None,
        delegation_ref: str | None = None,
        execution_environment_ref: str | None = None,
        evidence_scope_ref: str | None = None,
        procedure_ref: str | None = None,
        user_constraints: tuple[str, ...] = (),
        subgoal_refs: tuple[str, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        capability_grant_refs: tuple[str, ...] = (),
    ) -> "WorkingState":
        if type(strategy_budgets) is not dict:
            raise TypeError("strategy_budgets must be a plain dict")
        if not isinstance(observation_ref, ObservationRef):
            raise TypeError("observation_ref must be ObservationRef")
        procedure_scope = procedure_ref or task_id
        budgets = (
            BudgetState(BudgetKind.TASK, task_id, task_budget),
            BudgetState(BudgetKind.PROCEDURE, procedure_scope, procedure_budget),
            *(
                BudgetState(BudgetKind.STRATEGY, key, value)
                for key, value in sorted(strategy_budgets.items())
            ),
        )
        return cls(
            task_id=task_id,
            revision=0,
            recovery_epoch=0,
            actor_ref=actor_ref,
            delegation_ref=delegation_ref,
            execution_environment_ref=execution_environment_ref,
            evidence_scope_ref=evidence_scope_ref,
            procedure_ref=procedure_ref,
            observation_ref=observation_ref,
            user_constraints=user_constraints,
            subgoal_refs=subgoal_refs,
            verified_achievements=(),
            fact_refs=(),
            open_ambiguities=(),
            evidence_refs=evidence_refs,
            capability_grant_refs=capability_grant_refs,
            budgets=budgets,
        )

    @property
    def candidate_done_current(self) -> bool:
        return self.candidate_done and self.candidate_done_revision == self.revision

    def _budget_scope(self, kind: BudgetKind, strategy_id: str) -> str:
        if kind is BudgetKind.TASK:
            return self.task_id
        if kind is BudgetKind.PROCEDURE:
            return self.procedure_ref or self.task_id
        return strategy_id

    def budget(self, kind: BudgetKind, *, strategy_id: str) -> BudgetState | None:
        scope = self._budget_scope(kind, strategy_id)
        matches = [
            item for item in self.budgets
            if item.kind is kind and item.scope_id == scope
        ]
        return matches[0] if len(matches) == 1 else None

    def _consume_attempt_budgets(self, strategy_id: str) -> tuple[BudgetState, ...]:
        required = {BudgetKind.TASK, BudgetKind.PROCEDURE, BudgetKind.STRATEGY}
        consumed: set[BudgetKind] = set()
        result: list[BudgetState] = []
        for item in self.budgets:
            if item.kind in required and item.scope_id == self._budget_scope(item.kind, strategy_id):
                result.append(item.consume())
                consumed.add(item.kind)
            else:
                result.append(item)
        if consumed != required:
            raise ValueError("missing explicit task/procedure/strategy budget")
        return tuple(result)

    def latest_attempt(self, operation_id: str) -> AttemptRecord | None:
        return next(
            (
                item for item in reversed(self.attempts)
                if item.intent.operation_id == operation_id
            ),
            None,
        )

    def reconciliation_for(self, attempt: AttemptRecord) -> ReconciliationRecord | None:
        return next(
            (
                item for item in reversed(self.reconciliations)
                if item.operation_id == attempt.intent.operation_id
                and item.attempt_revision == attempt.revision_after
            ),
            None,
        )

    def unresolved_attempts(self) -> tuple[AttemptRecord, ...]:
        unresolved: list[AttemptRecord] = []
        for attempt in self.attempts:
            if attempt.outcome not in {
                MutatingOutcome.OUTCOME_UNKNOWN,
                MutatingOutcome.APPLIED_BUT_ACK_FAILED,
            }:
                continue
            reconciliation = self.reconciliation_for(attempt)
            if reconciliation is None or reconciliation.status is ReconciliationStatus.STILL_UNKNOWN:
                unresolved.append(attempt)
        return tuple(unresolved)

    def record_attempt(
        self,
        intent: AttemptIntent,
        outcome: MutatingOutcome,
        failure: FailureReason | None,
        *,
        expected_revision: int,
        guard: "LoopGuard | None" = None,
    ) -> "WorkingState":
        if expected_revision != self.revision:
            raise ValueError("stale WorkingState revision")
        if not isinstance(intent, AttemptIntent) or not isinstance(outcome, MutatingOutcome):
            raise TypeError("attempt requires AttemptIntent and MutatingOutcome")
        active_guard = guard or LoopGuard()
        decision = active_guard.evaluate(
            self,
            intent,
            expected_revision=expected_revision,
        )
        if not decision.allowed:
            code = decision.failure.code if decision.failure is not None else "blocked"
            raise ValueError(f"LoopGuard blocked attempt: {code}")
        new_revision = self.revision + 1
        record = AttemptRecord(intent, outcome, self.revision, new_revision, failure)
        return replace(
            self,
            revision=new_revision,
            recovery_epoch=self.recovery_epoch + (1 if failure is not None else 0),
            budgets=self._consume_attempt_budgets(intent.strategy_id),
            attempts=self.attempts + (record,),
            failures=self.failures + ((failure,) if failure is not None else ()),
        )

    def record_failure(
        self,
        failure: FailureReason,
        *,
        expected_revision: int,
        begin_recovery: bool = True,
    ) -> "WorkingState":
        if expected_revision != self.revision:
            raise ValueError("stale WorkingState revision")
        if not isinstance(failure, FailureReason):
            raise TypeError("failure must be FailureReason")
        return replace(
            self,
            revision=self.revision + 1,
            recovery_epoch=self.recovery_epoch + (1 if begin_recovery else 0),
            failures=self.failures + (failure,),
        )

    def record_observation(
        self,
        observation_ref: ObservationRef,
        *,
        expected_revision: int,
        begin_recovery: bool = False,
    ) -> "WorkingState":
        if expected_revision != self.revision:
            raise ValueError("stale WorkingState revision")
        if not isinstance(observation_ref, ObservationRef):
            raise TypeError("observation_ref must be ObservationRef")
        if not _same_stream(self.observation_ref, observation_ref):
            raise ValueError("observation stream does not match current WorkingState")
        if observation_ref.sequence <= self.observation_ref.sequence:
            raise ValueError("observation must be fresher than current WorkingState")
        return replace(
            self,
            revision=self.revision + 1,
            recovery_epoch=self.recovery_epoch + (1 if begin_recovery else 0),
            observation_ref=observation_ref,
        )

    def record_reconciliation(
        self,
        *,
        operation_id: str,
        attempt_revision: int,
        status: ReconciliationStatus,
        verification: VerificationResult,
        expected_revision: int,
    ) -> "WorkingState":
        if expected_revision != self.revision:
            raise ValueError("stale WorkingState revision")
        _text(operation_id, name="reconciliation operation_id")
        if type(attempt_revision) is not int or attempt_revision <= 0:
            raise ValueError("reconciliation attempt_revision must be positive")
        if not isinstance(status, ReconciliationStatus):
            raise TypeError("reconciliation status must be ReconciliationStatus")
        if not isinstance(verification, VerificationResult):
            raise TypeError("reconciliation requires VerificationResult")
        if verification.observation is None:
            raise ValueError("reconciliation verification requires an observation")
        if verification.evidence_batch_id is None:
            raise ValueError("reconciliation verification requires evidence_batch_id")

        latest = self.latest_attempt(operation_id)
        if latest is None or latest.revision_after != attempt_revision:
            raise ValueError("reconciliation is not bound to latest logical attempt")
        if latest.outcome not in {
            MutatingOutcome.OUTCOME_UNKNOWN,
            MutatingOutcome.APPLIED_BUT_ACK_FAILED,
        }:
            raise ValueError("reconciliation requires ambiguous/ack-failed outcome")
        if (
            latest.outcome is MutatingOutcome.APPLIED_BUT_ACK_FAILED
            and status is ReconciliationStatus.CONFIRMED_NOT_APPLIED
        ):
            raise ValueError("ack-failed outcome cannot reconcile as not applied")

        existing = self.reconciliation_for(latest)
        if (
            existing is not None
            and existing.status is not ReconciliationStatus.STILL_UNKNOWN
        ):
            raise ValueError("resolved reconciliation cannot be replaced")

        expected_effect_id = reconciliation_effect_id(
            operation_id,
            attempt_revision,
            status,
        )
        if verification.effect_id != expected_effect_id:
            raise ValueError("reconciliation verification effect_id mismatch")
        if status is ReconciliationStatus.STILL_UNKNOWN:
            if verification.status is not VerificationStatus.UNKNOWN:
                raise ValueError("STILL_UNKNOWN requires UNKNOWN verification")
        elif verification.status is not VerificationStatus.PASS:
            raise ValueError("confirmed reconciliation requires PASS verification")

        observation = verification.observation
        if not _same_stream(latest.intent.observation_ref, observation):
            raise ValueError("reconciliation observation stream mismatch")
        if not _same_stream(self.observation_ref, observation):
            raise ValueError("reconciliation observation does not match current WorkingState stream")
        if observation.sequence <= latest.intent.observation_ref.sequence:
            raise ValueError("reconciliation observation is not fresh relative to attempt")
        if observation.sequence < self.observation_ref.sequence:
            raise ValueError("reconciliation observation is stale relative to WorkingState")
        if (
            observation.sequence == self.observation_ref.sequence
            and observation != self.observation_ref
        ):
            raise ValueError("reconciliation observation conflicts with current sequence")
        if existing is not None and observation.sequence <= existing.observation_ref.sequence:
            raise ValueError("reconciliation refinement requires fresher evidence")

        new_revision = self.revision + 1
        record = ReconciliationRecord(
            operation_id=operation_id,
            attempt_revision=attempt_revision,
            status=status,
            revision_after=new_revision,
            observation_ref=observation,
            verification_effect_id=verification.effect_id,
            evidence_batch_id=verification.evidence_batch_id,
        )
        return replace(
            self,
            revision=new_revision,
            recovery_epoch=self.recovery_epoch + 1,
            observation_ref=observation,
            reconciliations=self.reconciliations + (record,),
        )

    def mark_candidate_done(self, *, expected_revision: int) -> "WorkingState":
        if expected_revision != self.revision:
            raise ValueError("stale WorkingState revision")
        revision = self.revision + 1
        return replace(
            self,
            revision=revision,
            candidate_done=True,
            candidate_done_revision=revision,
        )

    def stagnation_report(
        self,
        reason_code: str,
        *,
        recent_limit: int = 8,
    ) -> StagnationReport:
        if type(recent_limit) is not int or not 1 <= recent_limit <= 64:
            raise ValueError("recent_limit must be within 1..64")
        physical = [item.intent.physical_fingerprint for item in self.attempts]
        exhausted = tuple(
            f"{item.kind.value}:{item.scope_id}"
            for item in self.budgets
            if item.remaining == 0
        )
        return StagnationReport(
            self.task_id,
            self.revision,
            self.recovery_epoch,
            reason_code,
            self.failures[-1] if self.failures else None,
            tuple(physical[-recent_limit:]),
            exhausted,
            self.candidate_done_current,
        )

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **_json_value(self)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkingState":
        raw = _shape(
            value,
            name="WorkingState",
            keys={
                "schema_version", "task_id", "revision", "recovery_epoch", "actor_ref",
                "delegation_ref", "execution_environment_ref", "evidence_scope_ref",
                "procedure_ref", "observation_ref", "user_constraints", "subgoal_refs",
                "verified_achievements", "fact_refs", "open_ambiguities", "evidence_refs",
                "capability_grant_refs", "budgets", "attempts", "failures",
                "reconciliations", "candidate_done", "candidate_done_revision",
            },
        )
        if raw["schema_version"] != SCHEMA_VERSION:
            raise ValueError("WorkingState schema_version is unsupported")

        def failure(item: Any) -> FailureReason:
            item = _shape(
                item,
                name="failure",
                keys={
                    "code", "category", "message", "retryable",
                    "reconciliation_required", "operation_id", "strategy_id",
                    "outcome", "evidence_refs",
                },
            )
            return FailureReason(
                item["code"],
                FailureCategory(item["category"]),
                item["message"],
                item["retryable"],
                item["reconciliation_required"],
                item["operation_id"],
                item["strategy_id"],
                MutatingOutcome(item["outcome"]) if item["outcome"] is not None else None,
                _refs(item["evidence_refs"], name="failure evidence_refs"),
            )

        def intent(item: Any) -> AttemptIntent:
            item = _shape(
                item,
                name="attempt intent",
                keys={
                    "operation_id", "strategy_id", "action_fingerprint",
                    "observation_ref", "actor_ref", "execution_environment_ref",
                    "evidence_scope_ref", "evidence_refs",
                },
            )
            return AttemptIntent(
                item["operation_id"],
                item["strategy_id"],
                item["action_fingerprint"],
                _observation(item["observation_ref"], name="attempt observation_ref"),
                item["actor_ref"],
                item["execution_environment_ref"],
                item["evidence_scope_ref"],
                _refs(item["evidence_refs"], name="attempt evidence_refs"),
            )

        def budget(item: Any) -> BudgetState:
            item = _shape(
                item,
                name="budget",
                keys={"kind", "scope_id", "limit", "used"},
            )
            return BudgetState(
                BudgetKind(item["kind"]),
                item["scope_id"],
                item["limit"],
                item["used"],
            )

        def attempt(item: Any) -> AttemptRecord:
            item = _shape(
                item,
                name="attempt record",
                keys={"intent", "outcome", "revision_before", "revision_after", "failure"},
            )
            return AttemptRecord(
                intent(item["intent"]),
                MutatingOutcome(item["outcome"]),
                item["revision_before"],
                item["revision_after"],
                failure(item["failure"]) if item["failure"] is not None else None,
            )

        def reconciliation(item: Any) -> ReconciliationRecord:
            item = _shape(
                item,
                name="reconciliation record",
                keys={
                    "operation_id", "attempt_revision", "status", "revision_after",
                    "observation_ref", "verification_effect_id", "evidence_batch_id",
                },
            )
            return ReconciliationRecord(
                item["operation_id"],
                item["attempt_revision"],
                ReconciliationStatus(item["status"]),
                item["revision_after"],
                _observation(
                    item["observation_ref"],
                    name="reconciliation observation_ref",
                ),
                item["verification_effect_id"],
                item["evidence_batch_id"],
            )

        budgets_raw = _items(raw["budgets"], name="budgets")
        attempts_raw = _items(raw["attempts"], name="attempts")
        failures_raw = _items(raw["failures"], name="failures")
        reconciliations_raw = _items(raw["reconciliations"], name="reconciliations")

        return cls(
            task_id=raw["task_id"],
            revision=raw["revision"],
            recovery_epoch=raw["recovery_epoch"],
            actor_ref=raw["actor_ref"],
            delegation_ref=raw["delegation_ref"],
            execution_environment_ref=raw["execution_environment_ref"],
            evidence_scope_ref=raw["evidence_scope_ref"],
            procedure_ref=raw["procedure_ref"],
            observation_ref=_observation(
                raw["observation_ref"],
                name="WorkingState observation_ref",
            ),
            user_constraints=_refs(raw["user_constraints"], name="user_constraints"),
            subgoal_refs=_refs(raw["subgoal_refs"], name="subgoal_refs"),
            verified_achievements=_refs(
                raw["verified_achievements"],
                name="verified_achievements",
            ),
            fact_refs=_refs(raw["fact_refs"], name="fact_refs"),
            open_ambiguities=_refs(raw["open_ambiguities"], name="open_ambiguities"),
            evidence_refs=_refs(raw["evidence_refs"], name="evidence_refs"),
            capability_grant_refs=_refs(
                raw["capability_grant_refs"],
                name="capability_grant_refs",
            ),
            budgets=tuple(budget(item) for item in budgets_raw),
            attempts=tuple(attempt(item) for item in attempts_raw),
            failures=tuple(failure(item) for item in failures_raw),
            reconciliations=tuple(
                reconciliation(item) for item in reconciliations_raw
            ),
            candidate_done=raw["candidate_done"],
            candidate_done_revision=raw["candidate_done_revision"],
        )


class LoopGuard:
    def __init__(self, policy: LoopGuardPolicy | None = None) -> None:
        self.policy = policy or LoopGuardPolicy()

    @staticmethod
    def _reason(
        code: str,
        category: FailureCategory,
        message: str,
        intent: AttemptIntent,
        *,
        reconciliation_required: bool = False,
        outcome: MutatingOutcome | None = None,
        evidence_refs: tuple[str, ...] = (),
    ) -> FailureReason:
        return FailureReason(
            code,
            category,
            message,
            False,
            reconciliation_required,
            intent.operation_id,
            intent.strategy_id,
            outcome,
            evidence_refs,
        )

    @staticmethod
    def _block(
        state: WorkingState,
        intent: AttemptIntent,
        failure: FailureReason,
    ) -> GuardDecision:
        return GuardDecision(
            GuardStatus.BLOCK,
            state.revision,
            intent.authorization_fingerprint,
            failure,
        )

    def evaluate(
        self,
        state: WorkingState,
        intent: AttemptIntent,
        *,
        expected_revision: int,
    ) -> GuardDecision:
        if expected_revision != state.revision:
            return self._block(
                state,
                intent,
                self._reason(
                    "stale_working_state",
                    FailureCategory.STALE_STATE,
                    "Caller revision does not match current WorkingState.",
                    intent,
                ),
            )

        for name, category in (
            ("actor_ref", FailureCategory.ACTOR_MISMATCH),
            ("execution_environment_ref", FailureCategory.ACTOR_MISMATCH),
            ("evidence_scope_ref", FailureCategory.EVIDENCE_MISMATCH),
        ):
            if getattr(intent, name) != getattr(state, name):
                return self._block(
                    state,
                    intent,
                    self._reason(
                        f"{name}_mismatch",
                        category,
                        f"Attempt {name} does not match current WorkingState.",
                        intent,
                        evidence_refs=intent.evidence_refs,
                    ),
                )

        if intent.observation_ref != state.observation_ref:
            return self._block(
                state,
                intent,
                self._reason(
                    "stale_or_mismatched_observation",
                    FailureCategory.EVIDENCE_MISMATCH,
                    "Attempt is not bound to the current authoritative ObservationRef.",
                    intent,
                    evidence_refs=intent.evidence_refs,
                ),
            )

        for kind in (BudgetKind.TASK, BudgetKind.PROCEDURE, BudgetKind.STRATEGY):
            budget = state.budget(kind, strategy_id=intent.strategy_id)
            if budget is None or budget.remaining <= 0:
                return self._block(
                    state,
                    intent,
                    self._reason(
                        f"{kind.value}_budget_exhausted",
                        FailureCategory.BUDGET_EXHAUSTED,
                        f"{kind.value} budget is missing or exhausted.",
                        intent,
                    ),
                )

        unresolved = state.unresolved_attempts()
        if unresolved:
            current = state.latest_attempt(intent.operation_id)
            if current not in unresolved:
                blocking = unresolved[-1]
                return self._block(
                    state,
                    intent,
                    self._reason(
                        "unresolved_mutation_blocks_other_operation",
                        FailureCategory.RECONCILIATION_REQUIRED,
                        (
                            "Another mutating operation has an unresolved outcome; "
                            "reconcile it before any further mutation."
                        ),
                        intent,
                        reconciliation_required=True,
                        outcome=blocking.outcome,
                    ),
                )

        latest = state.latest_attempt(intent.operation_id)
        if latest is not None:
            if latest.outcome is MutatingOutcome.VERIFIED_APPLIED:
                return self._block(
                    state,
                    intent,
                    self._reason(
                        "logical_operation_already_verified_applied",
                        FailureCategory.UNSAFE_TRANSITION,
                        "Logical operation is already verified as applied.",
                        intent,
                        outcome=MutatingOutcome.VERIFIED_APPLIED,
                    ),
                )

            if latest.outcome in {
                MutatingOutcome.APPLIED_BUT_ACK_FAILED,
                MutatingOutcome.OUTCOME_UNKNOWN,
            }:
                reconciliation = state.reconciliation_for(latest)
                if (
                    reconciliation is None
                    or reconciliation.status is ReconciliationStatus.STILL_UNKNOWN
                ):
                    code = (
                        "logical_operation_applied_ack_failed"
                        if latest.outcome is MutatingOutcome.APPLIED_BUT_ACK_FAILED
                        else "logical_operation_reconciliation_required"
                    )
                    return self._block(
                        state,
                        intent,
                        self._reason(
                            code,
                            FailureCategory.RECONCILIATION_REQUIRED,
                            "Previous mutating outcome must be reconciled before redelivery.",
                            intent,
                            reconciliation_required=True,
                            outcome=latest.outcome,
                        ),
                    )
                if reconciliation.status is ReconciliationStatus.CONFIRMED_APPLIED:
                    return self._block(
                        state,
                        intent,
                        self._reason(
                            "logical_operation_reconciled_applied",
                            FailureCategory.UNSAFE_TRANSITION,
                            "Fresh reconciliation proved the logical operation was applied.",
                            intent,
                            outcome=MutatingOutcome.VERIFIED_APPLIED,
                            evidence_refs=(reconciliation.evidence_batch_id,),
                        ),
                    )
                if (
                    reconciliation.status is ReconciliationStatus.CONFIRMED_NOT_APPLIED
                    and intent.observation_ref != reconciliation.observation_ref
                ):
                    return self._block(
                        state,
                        intent,
                        self._reason(
                            "retry_state_does_not_match_reconciliation",
                            FailureCategory.STALE_STATE,
                            (
                                "Retry observation is not the fresh authoritative "
                                "observation used for reconciliation."
                            ),
                            intent,
                            evidence_refs=(reconciliation.evidence_batch_id,),
                        ),
                    )

        if state.attempts:
            most_recent_attempt = state.attempts[-1]
            if (
                state.observation_ref.sequence
                <= most_recent_attempt.intent.observation_ref.sequence
            ):
                return self._block(
                    state,
                    intent,
                    self._reason(
                        "fresh_observation_required_after_attempt",
                        FailureCategory.STALE_STATE,
                        (
                            "A fresh authoritative observation after the most recent "
                            "physical attempt is required before another mutation."
                        ),
                        intent,
                        evidence_refs=intent.evidence_refs,
                    ),
                )

        identical = sum(
            1
            for item in state.attempts
            if item.intent.physical_fingerprint == intent.physical_fingerprint
        )
        if identical >= self.policy.max_identical_physical_attempts:
            return self._block(
                state,
                intent,
                self._reason(
                    "repeated_physical_attempt_fingerprint",
                    FailureCategory.LOOP_DETECTED,
                    "Same physical action from same observed state was already attempted.",
                    intent,
                    evidence_refs=intent.evidence_refs,
                ),
            )

        states = [item.intent.pre_state_fingerprint for item in state.attempts]
        tail = (states + [intent.pre_state_fingerprint])[-self.policy.oscillation_window:]
        if len(tail) == self.policy.oscillation_window:
            even, odd = tail[0::2], tail[1::2]
            if len(set(even)) == 1 and len(set(odd)) == 1 and even[0] != odd[0]:
                return self._block(
                    state,
                    intent,
                    self._reason(
                        "physical_state_oscillation",
                        FailureCategory.LOOP_DETECTED,
                        "Recent physical attempts oscillate between two state fingerprints.",
                        intent,
                        evidence_refs=intent.evidence_refs,
                    ),
                )

        return GuardDecision(
            GuardStatus.ALLOW,
            state.revision,
            intent.authorization_fingerprint,
        )