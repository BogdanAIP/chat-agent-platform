from __future__ import annotations

import json
import sysconfig
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .errors import ValidationError


SOURCE_CONTRACT_ROOT = Path(__file__).resolve().parents[1] / "contracts"
INSTALLED_CONTRACT_ROOT = Path(sysconfig.get_path("data")) / "contracts"


@lru_cache(maxsize=None)
def load_schema(filename: str) -> dict[str, Any]:
    source_path = SOURCE_CONTRACT_ROOT / filename
    path = source_path if source_path.exists() else INSTALLED_CONTRACT_ROOT / filename
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        raise ValidationError(f"Invalid contract schema {filename}: {exc}") from exc
    return schema


def validate_contract(instance: Any, filename: str) -> None:
    validator = Draft202012Validator(load_schema(filename))
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    if not errors:
        return
    first = errors[0]
    location = ".".join(str(item) for item in first.absolute_path) or "<root>"
    raise ValidationError(f"Contract {filename} failed at {location}: {first.message}")
