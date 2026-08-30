"""Deterministic verified-procedure Control Plane.

Ordinary ChatGPT remains the general planner.  This package only progresses
explicitly registered procedures through bounded, current-state-verified
transitions.  It does not expose generic code execution or persist private
reasoning.
"""

import os

from .file_artifact_observation import (
    FILE_ARTIFACT_CAPABILITY,
    FileArtifactObservationStream,
)
from .verification import (
    ExpectedEffect,
    FinishGateResult,
    FinishStatus,
    ObservationRef,
    ObservationSnapshot,
    PredicateOperator,
    StatePredicate,
    VerificationResult,
    VerificationStatus,
    evaluate_finish_gate,
    verify_expected_effect,
)

# Stage 26.3C binds stage-create delivery to an in-process proof before the
# procedure module imports its internal create helper by value. On Windows the
# proof owns the newly-created file handle and trusted descendant namespace
# until the staged_verified receipt is durably checkpointed. Hosted non-Windows
# tests keep only an in-process marker and make no Windows pinning claim.
from . import _verified_workspace_artifact_support as _workspace_artifact_support
from . import windows_file_pin as _windows_file_pin

_original_portable_workspace_create = _workspace_artifact_support._exclusive_create_file
if os.name == "nt":
    _workspace_artifact_support._exclusive_create_file = (
        _windows_file_pin.create_file_in_pinned_namespace
    )
else:
    def _portable_workspace_create_with_delivery_proof(path, data):
        if _windows_file_pin.stage_create_delivery_proof_live():
            raise RuntimeError("another stage-create delivery proof is already live")
        _original_portable_workspace_create(path, data)
        _windows_file_pin.mark_portable_stage_create_delivery_proof(path)

    _workspace_artifact_support._exclusive_create_file = (
        _portable_workspace_create_with_delivery_proof
    )

from . import verified_workspace_artifact as _workspace_artifact


# A prepared stage_create has no durable file identity before its transition
# receipt. Fresh post-restart bytes therefore cannot authenticate themselves as
# the object created by the dead process. Only the still-live in-process
# delivery proof may authorize CONFIRMED_APPLIED; a missing staging+target pair
# remains safe to confirm as NOT_APPLIED and retry within the existing budget.
_original_workspace_direct_reconciliation_status = (
    _workspace_artifact._direct_reconciliation_status
)
_original_workspace_reconciliation_predicates = (
    _workspace_artifact._reconciliation_predicates
)
_original_workspace_write_checkpoint = _workspace_artifact._write_checkpoint
_original_workspace_run = _workspace_artifact.run_verified_workspace_artifact


def _bound_workspace_direct_reconciliation_status(
    transition_id,
    snapshot,
    *,
    content_size,
    expected_sha,
    staging_identity,
    target_identity=None,
):
    if (
        transition_id == "stage_create"
        and not _windows_file_pin.stage_create_delivery_proof_live()
    ):
        if (
            _workspace_artifact._is_missing(snapshot, "staging")
            and _workspace_artifact._is_missing(snapshot, "target")
        ):
            return _workspace_artifact.ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return _workspace_artifact.ReconciliationStatus.STILL_UNKNOWN
    return _original_workspace_direct_reconciliation_status(
        transition_id,
        snapshot,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=staging_identity,
        target_identity=target_identity,
    )


def _bound_workspace_reconciliation_predicates(
    transition_id,
    status,
    snapshot,
    *,
    content_size,
    expected_sha,
    staging_identity,
    target_identity,
):
    if (
        transition_id == "stage_create"
        and status is _workspace_artifact.ReconciliationStatus.CONFIRMED_APPLIED
        and not _windows_file_pin.stage_create_delivery_proof_live()
    ):
        return None
    return _original_workspace_reconciliation_predicates(
        transition_id,
        status,
        snapshot,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=staging_identity,
        target_identity=target_identity,
    )


def _write_checkpoint_with_stage_create_proof(state_root, task_state):
    _original_workspace_write_checkpoint(state_root, task_state)
    if (
        _windows_file_pin.stage_create_delivery_proof_live()
        and (
            task_state.get("prepared_intent") is None
            or task_state.get("status") != "running"
        )
    ):
        # Release only after the durable write succeeds. The normal success path
        # therefore keeps the exact created object/namespace pinned through the
        # fresh AFTER, Kernel result, staged_verified receipt and checkpoint.
        _windows_file_pin.release_stage_create_delivery_proof()


def _run_workspace_artifact_with_stage_create_proof_cleanup(*args, **kwargs):
    try:
        return _original_workspace_run(*args, **kwargs)
    finally:
        # A failed checkpoint may leave no durable receipt by design. Do not leak
        # the live handle into another call on this process/thread; a later resume
        # will see no proof and therefore fail closed instead of adopting bytes.
        _windows_file_pin.release_stage_create_delivery_proof()


_workspace_artifact._direct_reconciliation_status = (
    _bound_workspace_direct_reconciliation_status
)
_workspace_artifact._reconciliation_predicates = _bound_workspace_reconciliation_predicates
_workspace_artifact._write_checkpoint = _write_checkpoint_with_stage_create_proof
_workspace_artifact.run_verified_workspace_artifact = (
    _run_workspace_artifact_with_stage_create_proof_cleanup
)

PROCEDURE_ID = _workspace_artifact.PROCEDURE_ID
PROCEDURE_VERSION = _workspace_artifact.PROCEDURE_VERSION
run_verified_workspace_artifact = _workspace_artifact.run_verified_workspace_artifact

from .windows_observation import (
    WINDOWS_DESKTOP_CAPABILITY,
    WindowsDesktopObservationStream,
)
from .windows_transition import (
    WINDOWS_DESKTOP_EFFECT_ID,
    build_windows_desktop_effect,
    verify_windows_desktop_transition,
)
from .working_state import (
    AttemptIntent,
    AttemptRecord,
    BudgetKind,
    BudgetState,
    FailureCategory,
    FailureReason,
    GuardDecision,
    GuardStatus,
    LoopGuard,
    LoopGuardPolicy,
    MutatingOutcome,
    ReconciliationRecord,
    ReconciliationStatus,
    StagnationReport,
    WorkingState,
    reconciliation_effect_id,
)

__all__ = [
    "AttemptIntent",
    "AttemptRecord",
    "BudgetKind",
    "BudgetState",
    "ExpectedEffect",
    "FailureCategory",
    "FailureReason",
    "FILE_ARTIFACT_CAPABILITY",
    "FileArtifactObservationStream",
    "FinishGateResult",
    "FinishStatus",
    "GuardDecision",
    "GuardStatus",
    "LoopGuard",
    "LoopGuardPolicy",
    "MutatingOutcome",
    "ObservationRef",
    "ObservationSnapshot",
    "PredicateOperator",
    "PROCEDURE_ID",
    "PROCEDURE_VERSION",
    "ReconciliationRecord",
    "ReconciliationStatus",
    "StagnationReport",
    "StatePredicate",
    "VerificationResult",
    "VerificationStatus",
    "WINDOWS_DESKTOP_CAPABILITY",
    "WINDOWS_DESKTOP_EFFECT_ID",
    "WindowsDesktopObservationStream",
    "WorkingState",
    "build_windows_desktop_effect",
    "evaluate_finish_gate",
    "reconciliation_effect_id",
    "run_verified_workspace_artifact",
    "verify_expected_effect",
    "verify_windows_desktop_transition",
]
