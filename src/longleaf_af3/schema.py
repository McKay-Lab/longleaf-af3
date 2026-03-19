"""AF3 input JSON schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def _load_schema() -> dict:
    """Load the AF3 JSON schema."""
    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "schema"
        / "af3_input.schema.json"
    )
    return json.loads(schema_path.read_text())


def validate_input(data: dict) -> list[str]:
    """Validate an AF3 input dict against the schema. Returns a list of error messages."""
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [_format_error(e) for e in errors]


def _format_error(error: jsonschema.ValidationError) -> str:
    """Format a validation error into a readable message."""
    path = ".".join(str(p) for p in error.absolute_path)
    if path:
        return f"{path}: {error.message}"
    return error.message
