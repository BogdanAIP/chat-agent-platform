"""Production Windows runtime foundations.

This package contains bounded, non-planning primitives promoted from the
physically qualified Stage 26 Windows harnesses.  It intentionally exposes no
public Chat/MCP surface on its own.
"""

from .actuation import bounded_input, send_unicode_text
from .grounder import (
    DesktopGrounderError,
    GrounderPoint,
    GrounderProposal,
    GrounderRegion,
    locate_desktop_target,
)
from .observation import (
    ControlObservation,
    DesktopState,
    EvidenceProvenance,
    Rect,
    build_desktop_state,
    observe_bound_window,
)
from .verifier import (
    VerificationResult,
    VerificationStatus,
    Verifier,
    verify_expected_fields,
)
from .window_scoped_uia import ResolverStats, WindowScopedUiaResolver

__all__ = [
    "ControlObservation",
    "DesktopGrounderError",
    "DesktopState",
    "EvidenceProvenance",
    "GrounderPoint",
    "GrounderProposal",
    "GrounderRegion",
    "Rect",
    "ResolverStats",
    "VerificationResult",
    "VerificationStatus",
    "Verifier",
    "WindowScopedUiaResolver",
    "bounded_input",
    "build_desktop_state",
    "locate_desktop_target",
    "observe_bound_window",
    "send_unicode_text",
    "verify_expected_fields",
]
