"""Utilities for converting snake_case structures to camelCase."""

from __future__ import annotations

from typing import Any, Dict, Iterable


def to_camel_case(value: str) -> str:
    """Convert ``snake_case`` or ``kebab-case`` strings to ``camelCase``."""

    if not value:
        return value

    value = value.replace("-", "_")
    parts = value.split("_")
    if len(parts) == 1:
        return parts[0]
    head, *rest = parts
    return head + "".join(token.capitalize() if token else "" for token in rest)


def camelize(value: Any) -> Any:
    """Recursively convert dictionary keys to camelCase."""

    if isinstance(value, dict):
        return {to_camel_case(str(key)): camelize(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(camelize(item) for item in value)
    return value
