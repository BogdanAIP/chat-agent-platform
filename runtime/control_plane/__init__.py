"""Deterministic verified-procedure Control Plane.

Ordinary ChatGPT remains the general planner.  This package only progresses
explicitly registered procedures through bounded, current-state-verified
transitions.  It does not expose generic code execution or persist private
reasoning.
"""

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

__all__ = [
    "ExpectedEffect",
    "FILE_ARTIFACT_CAPABILITY",
    "FileArtifactObservationStream",
    "FinishGateResult",
    "FinishStatus",
    "ObservationRef",
    "ObservationSnapshot",
    "PredicateOperator",
    "PROCEDURE_ID",
    "PROCEDURE_VERSION",
    "StatePredicate",
    "VerificationResult",
    "VerificationStatus",
    "WINDOWS_DESKTOP_CAPABILITY",
    "WINDOWS_DESKTOP_EFFECT_ID",
    "WindowsDesktopObservationStream",
    "build_windows_desktop_effect",
    "evaluate_finish_gate",
    "run_verified_workspace_artifact",
    "verify_expected_effect",
    "verify_windows_desktop_transition",
]
