"""
view_parser/attr_parser.py — XML attribute helpers.

Mirrors the ooui.js *attributeParser.ts* utilities:
  isTrue / parseBoolAttribute → parse_bool
  parseInt-like           → parse_int
  evaluateAttributes      → eval_attrs  (simplified; full attrs-eval not needed
                                         for the initial PySide6 renderer)
"""
from __future__ import annotations

from typing import Any


def parse_bool(value: Any, default: bool = False) -> bool:
    """Return True for truthy OpenERP attribute values.

    Handles: 1, '1', True, 'True', 'true' — same logic as ooui parseBoolAttribute.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true")
    return default


def parse_int(value: Any, default: int = 1) -> int:
    """Safely parse an integer XML attribute."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_str(value: Any, default: str = "") -> str:
    """Return a stripped string or *default* when value is None/empty."""
    if value is None:
        return default
    return str(value).strip()
