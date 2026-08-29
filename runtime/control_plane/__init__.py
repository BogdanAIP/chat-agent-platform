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

# Stage 26.3C is supported for consequence-bearing workspace mutation on
# Windows. Bind the already-researched namespace-pinned create primitive before
# the procedure module imports its internal helper by value. Non-Windows hosted
# tests retain the portable helper and do not claim the Windows namespace gate.
if os.name == "nt":
    from . import _verified_workspace_artifact_support as _workspace_artifact_support
    from .windows_file_pin import create_file_in_pinned_namespace as _pinned_workspace_create

    _workspace_artifact_support._exclusive_create_file = _pinned_workspace_create

from .verified_workspace_artifact import (
    PROCEDURE_ID,
    PROCEDURE_VERSION,
    run_verified_workspace_artifact,
)
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
