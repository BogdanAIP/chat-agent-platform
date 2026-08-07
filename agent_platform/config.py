from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ValidationError


def load_yaml_compatible(path: Path) -> dict[str, Any]:
    """Load JSON-compatible YAML without adding a dependency for Stage 0–1."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot load config {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"Config root must be an object: {path}")
    return value

