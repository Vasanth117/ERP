"""Normalize browser form payloads before Pydantic validation."""

from __future__ import annotations

from typing import Any


def blank_to_none(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        return None if stripped == "" else stripped
    return value


def normalize_form_values(values: dict[str, Any]) -> dict[str, Any]:
    """Map blank strings to None; trim other strings."""
    out: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, dict):
            out[key] = normalize_form_values(value)
        elif isinstance(value, list):
            out[key] = value
        else:
            out[key] = blank_to_none(value)
    return out