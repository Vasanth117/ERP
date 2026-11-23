"""Structured form validation payloads for college-admin creation flows."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import AppError


def scroll_field(
    field_key: str,
    *,
    label: str,
    message: str,
    action_label: str | None = None,
) -> dict[str, Any]:
    return {
        "field_key": field_key,
        "label": label,
        "message": message,
        "action_type": "scroll",
        "action_label": action_label or f"Go to {label}",
        "action_href": None,
    }


def navigate_field(
    field_key: str,
    *,
    label: str,
    message: str,
    action_label: str,
    action_href: str,
) -> dict[str, Any]:
    return {
        "field_key": field_key,
        "label": label,
        "message": message,
        "action_type": "navigate",
        "action_label": action_label,
        "action_href": action_href,
    }


def raise_validation_error(message: str, details: list[dict[str, Any]]) -> None:
    raise AppError(
        code="VALIDATION_ERROR",
        message=message,
        status_code=422,
        details=details,
    )