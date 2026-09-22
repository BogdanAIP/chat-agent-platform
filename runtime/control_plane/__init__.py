"""Provider-neutral CAP Control Plane contract surface.

Ordinary ChatGPT remains the general planner. Importing this package exposes
only project-owned authority/state/verification contracts and performs no
provider-, browser-, Windows- or application-specific runtime wiring.

Concrete capability/procedure compatibility exports remain available lazily so
existing callers keep working without making them part of the trust-core import
path.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

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


_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "FILE_ARTIFACT_CAPABILITY": (
        "runtime.control_plane.file_artifact_observation",
        "FILE_ARTIFACT_CAPABILITY",
    ),
    "FileArtifactObservationStream": (
        "runtime.control_plane.file_artifact_observation",
        "FileArtifactObservationStream",
    ),
    "PROCEDURE_ID": (
        "runtime.control_plane.verified_workspace_artifact",
        "PROCEDURE_ID",
    ),
    "PROCEDURE_VERSION": (
        "runtime.control_plane.verified_workspace_artifact",
        "PROCEDURE_VERSION",
    ),
    "run_verified_workspace_artifact": (
        "runtime.control_plane.verified_workspace_artifact",
        "run_verified_workspace_artifact",
    ),
    "WINDOWS_DESKTOP_CAPABILITY": (
        "runtime.control_plane.windows_observation",
        "WINDOWS_DESKTOP_CAPABILITY",
    ),
    "WindowsDesktopObservationStream": (
        "runtime.control_plane.windows_observation",
        "WindowsDesktopObservationStream",
    ),
    "WINDOWS_DESKTOP_EFFECT_ID": (
        "runtime.control_plane.windows_transition",
        "WINDOWS_DESKTOP_EFFECT_ID",
    ),
    "build_windows_desktop_effect": (
        "runtime.control_plane.windows_transition",
        "build_windows_desktop_effect",
    ),
    "verify_windows_desktop_transition": (
        "runtime.control_plane.windows_transition",
        "verify_windows_desktop_transition",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


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
