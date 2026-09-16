from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .independent_review_delegation import (
    prepare_review_delegation,
    review_delegation_state_root,
    settle_review_from_delegation,
    spawn_review_worker,
    validate_review_worker_runtime,
)
from .independent_review_state import (
    ReviewStateError,
    mark_dispatch_attempted,
    parse_review_identity,
    prepare_review_operation,
    reconcile_independent_review_result,
    submit_independent_review_result,
)


LAUNCH_PROCEDURE_ID = "launch_independent_review_v1"
SUBMIT_PROCEDURE_ID = "submit_independent_review_result_v1"
RECONCILE_PROCEDURE_ID = "reconcile_independent_review_result_v1"

_IDENTITY_KEYS = {
    "repository",
    "pr_number",
    "base_sha",
    "head_sha",
    "review_skill",
    "review_skill_version",
}


def _require_plain_request(request: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    if type(request) is not dict:
        raise ReviewStateError(f"{label} request must be a plain object")
    return request


def _require_exact_request_keys(
    request: Mapping[str, Any],
    expected: set[str],
    *,
    label: str,
) -> None:
    actual = set(request)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ReviewStateError(
            f"{label} request keys mismatch: missing={missing or 'none'} "
            f"unexpected={unexpected or 'none'}"
        )


def _require_procedure(request: Mapping[str, Any], expected: str, *, label: str) -> None:
    if request.get("procedure") != expected:
        raise ReviewStateError(f"{label} procedure must be {expected}")


def _identity_from_procedure_request(request: Mapping[str, Any]) -> dict[str, Any]:
    value = {key: request[key] for key in _IDENTITY_KEYS}
    identity = parse_review_identity(value, exact_keys=True)
    return identity.as_dict()


def run_launch_independent_review(
    request: Mapping[str, Any],
    *,
    state_root: Path,
) -> dict[str, Any]:
    """Start at most one automatic reviewer over the generic Delegation lifecycle."""

    value = _require_plain_request(request, label="launch independent review")
    _require_exact_request_keys(
        value,
        {"procedure", *_IDENTITY_KEYS},
        label="launch independent review",
    )
    _require_procedure(value, LAUNCH_PROCEDURE_ID, label="launch independent review")
    identity_value = _identity_from_procedure_request(value)
    identity = parse_review_identity(identity_value, exact_keys=True)
    prepared = prepare_review_operation(identity_value, state_root=state_root)

    if prepared.result_state != "open":
        summary = reconcile_independent_review_result(identity_value, state_root=state_root)
        return {
            **summary,
            "procedure_id": LAUNCH_PROCEDURE_ID,
            "automatic_launch_performed": False,
        }

    if prepared.dispatch_state != "prepared":
        settlement = None
        try:
            delegation_state_root = review_delegation_state_root()
        except ReviewStateError:
            delegation_state_root = None
        if delegation_state_root is not None:
            settlement = settle_review_from_delegation(
                identity_value,
                reviewer_state_root=state_root,
                delegation_state_root=delegation_state_root,
            )
        if settlement is not None and settlement.get("status") in {"recorded", "already_recorded"}:
            summary = reconcile_independent_review_result(identity_value, state_root=state_root)
            return {
                **summary,
                "procedure_id": LAUNCH_PROCEDURE_ID,
                "automatic_launch_performed": False,
            }
        return {
            "schema_version": 1,
            "status": "pending",
            "procedure_id": LAUNCH_PROCEDURE_ID,
            "operation_key": prepared.operation_key,
            "dispatch_state": prepared.dispatch_state,
            "result_state": prepared.result_state,
            "automatic_launch_performed": False,
            "automatic_submission_open": prepared.dispatch_state == "dispatch-attempted",
            **(
                {
                    "automatic_worker_status": settlement.get("worker_status"),
                    "automatic_worker_result_sha256": settlement.get("result_sha256"),
                }
                if settlement is not None
                and settlement.get("status") == "worker_terminal_noncompleting"
                else (
                    {
                        "automatic_review_status": settlement.get("review_status"),
                        "automatic_review_validity": settlement.get("review_validity"),
                        "automatic_worker_result_sha256": settlement.get("result_sha256"),
                    }
                    if settlement is not None
                    and settlement.get("status") == "review_terminal_noncompleting"
                    else {}
                )
            ),
        }

    try:
        validate_review_worker_runtime(state_root=state_root)
        delegation_state_root = review_delegation_state_root()
    except ReviewStateError:
        return {
            "schema_version": 1,
            "status": "abstained",
            "procedure_id": LAUNCH_PROCEDURE_ID,
            "operation_key": prepared.operation_key,
            "dispatch_state": prepared.dispatch_state,
            "result_state": prepared.result_state,
            "automatic_launch_performed": False,
            "automatic_submission_open": False,
            "escalation_reason": "reviewer_runtime_unavailable",
        }

    # Create/load the deterministic generic Delegation while reviewer dispatch
    # is still prepared. A crash here leaves reviewer launch authority intact
    # because no physical child launch has yet been authorized.
    prepare_review_delegation(
        prepared.identity,
        review_run_id=prepared.review_run_id,
        delegation_state_root=delegation_state_root,
    )

    # Reviewer launch authority is consumed before the external process starts.
    # If process creation fails or its acknowledgement is lost, automatic
    # relaunch is permanently forbidden for this exact review operation.
    dispatch = mark_dispatch_attempted(identity_value, state_root=state_root)
    try:
        spawn_review_worker(identity, state_root=state_root)
    except ReviewStateError:
        return {
            "schema_version": 1,
            "status": "abstained",
            "procedure_id": LAUNCH_PROCEDURE_ID,
            "operation_key": prepared.operation_key,
            "dispatch_state": dispatch["dispatch_state"],
            "result_state": dispatch["result_state"],
            "automatic_launch_performed": False,
            "automatic_submission_open": True,
            "escalation_reason": "reviewer_worker_spawn_failed",
        }

    return {
        "schema_version": 1,
        "status": "pending",
        "procedure_id": LAUNCH_PROCEDURE_ID,
        "operation_key": prepared.operation_key,
        "dispatch_state": dispatch["dispatch_state"],
        "result_state": dispatch["result_state"],
        "automatic_launch_performed": True,
        "automatic_submission_open": True,
    }


def run_submit_independent_review_result(
    request: Mapping[str, Any],
    *,
    state_root: Path,
) -> dict[str, Any]:
    value = _require_plain_request(request, label="submit independent review result")
    _require_exact_request_keys(
        value,
        {"procedure", "review_run_id", "result"},
        label="submit independent review result",
    )
    _require_procedure(value, SUBMIT_PROCEDURE_ID, label="submit independent review result")
    return submit_independent_review_result(
        {
            "review_run_id": value["review_run_id"],
            "result": value["result"],
        },
        state_root=state_root,
    )


def run_reconcile_independent_review_result(
    request: Mapping[str, Any],
    *,
    state_root: Path,
) -> dict[str, Any]:
    value = _require_plain_request(request, label="reconcile independent review result")
    allowed = {"procedure", *_IDENTITY_KEYS, "manual_result"}
    required = {"procedure", *_IDENTITY_KEYS}
    actual = set(value)
    missing = sorted(required - actual)
    unexpected = sorted(actual - allowed)
    if missing or unexpected:
        raise ReviewStateError(
            f"reconcile independent review result request keys mismatch: "
            f"missing={missing or 'none'} unexpected={unexpected or 'none'}"
        )
    _require_procedure(value, RECONCILE_PROCEDURE_ID, label="reconcile independent review result")
    identity = _identity_from_procedure_request(value)

    state_request: dict[str, Any] = dict(identity)
    if "manual_result" in value:
        state_request["manual_result"] = value["manual_result"]
        return reconcile_independent_review_result(state_request, state_root=state_root)

    # A terminal reviewer result is already authoritative. In particular, a
    # manual fallback that committed first must not be made unreadable by a
    # later generic worker result that can no longer claim the automatic slot.
    current = reconcile_independent_review_result(state_request, state_root=state_root)
    if current.get("result_state") in {
        "automatic-result-recorded",
        "manual-fallback-recorded",
    }:
        return current

    settlement: dict[str, Any] | None = None
    try:
        delegation_state_root = review_delegation_state_root()
    except ReviewStateError:
        delegation_state_root = None
    if delegation_state_root is not None:
        try:
            settlement = settle_review_from_delegation(
                identity,
                reviewer_state_root=state_root,
                delegation_state_root=delegation_state_root,
            )
        except ReviewStateError:
            # Close the automatic/manual race without hiding real invalid
            # automatic results. If manual fallback won while settlement was
            # attempting the automatic commit, return that now-authoritative
            # result. Otherwise preserve the fail-closed validation error.
            raced = reconcile_independent_review_result(
                state_request,
                state_root=state_root,
            )
            if raced.get("result_state") == "manual-fallback-recorded":
                return raced
            raise

    result = reconcile_independent_review_result(state_request, state_root=state_root)

    if settlement is not None and settlement.get("status") == "worker_terminal_noncompleting":
        result = {
            **result,
            "automatic_worker_status": settlement.get("worker_status"),
            "automatic_worker_result_sha256": settlement.get("result_sha256"),
        }
    elif settlement is not None and settlement.get("status") == "review_terminal_noncompleting":
        result = {
            **result,
            "automatic_review_status": settlement.get("review_status"),
            "automatic_review_validity": settlement.get("review_validity"),
            "automatic_worker_result_sha256": settlement.get("result_sha256"),
        }
    return result
