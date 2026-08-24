"""Deterministic verified-procedure Control Plane.

Ordinary ChatGPT remains the general planner.  This package only progresses
explicitly registered procedures through bounded, current-state-verified
transitions.  It does not expose generic code execution or persist private
reasoning.
"""

from .verified_workspace_artifact import (
    PROCEDURE_ID,
    PROCEDURE_VERSION,
    run_verified_workspace_artifact,
)

__all__ = [
    "PROCEDURE_ID",
    "PROCEDURE_VERSION",
    "run_verified_workspace_artifact",
]
