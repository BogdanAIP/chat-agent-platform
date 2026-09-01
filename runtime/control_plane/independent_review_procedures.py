from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .independent_review_state import (
    ReviewStateError,
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
    """Prepare one exact review operation and fail closed before browser dispatch.

    This production slice deliberately does not implement reviewer-authority
    qualification, browser launch, or MV3 Send claiming. Those mechanisms are a
    later accepted boundary. Preparing the operation here preserves the durable
    exact identity and private nonce while ensuring no caller can mistake this
    contract-only wiring for a completed automatic launch.
    """

    value = _require_plain_request(request, label="launch independent review")
    _require_exact_request_keys(
        value,
        {"procedure", *_IDENTITY_KEYS},
        label="launch independent review",
    )
    _require_procedure(value, LAUNCH_PROCEDURE_ID, label="launch independent review")
    identity = _identity_from_procedure_request(value)
    prepared = prepare_review_operation(identity, state_root=state_root)

    if prepared.result_state != "open":
        reason = "review_result_already_recorded"
    elif prepared.dispatch_state != "prepared":
        reason = "review_dispatch_already_attempted"
    else:
        reason = "reviewer_authority_unqualified"

    return {
        "schema_version": 1,
        "status": "abstained",
        "procedure_id": LAUNCH_PROCEDURE_ID,
        "operation_key": prepared.operation_key,
        "dispatch_state": prepared.dispatch_state,
        "result_state": prepared.result_state,
        "automatic_launch_performed": False,
        "automatic_submission_open": (
            prepared.dispatch_state == "dispatch-attempted" and prepared.result_state == "open"
        ),
        "escalation_reason": reason,
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
