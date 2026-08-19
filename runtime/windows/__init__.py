"""Production Windows runtime foundations.

This package contains bounded, non-planning primitives promoted from the
physically qualified Stage 26 Windows harnesses.  It intentionally exposes no
public Chat/MCP surface on its own.
"""

from .actuation import bounded_input, send_unicode_text
from .verifier import (
    VerificationResult,
    VerificationStatus,
    Verifier,
    verify_expected_fields,
)
from .window_scoped_uia import ResolverStats, WindowScopedUiaResolver

__all__ = [
    "ResolverStats",
    "VerificationResult",
    "VerificationStatus",
    "Verifier",
    "WindowScopedUiaResolver",
    "bounded_input",
    "send_unicode_text",
    "verify_expected_fields",
]
