"""
MD3 typography scale.

Maps MD3 type role names to (font-family, weight, size-in-px, line-height)
tuples so they can be consumed by both the QSS generator and widget code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TypeStyle:
    """A single MD3 typescale entry."""

    family: str
    weight: int          # CSS numeric weight, e.g. 400, 500, 700
    size: int            # px
    line_height: int     # px
    letter_spacing: float = 0.0   # px


# Family constants
_ROBOTO = "Roboto, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


@dataclass(frozen=True)
class Typography:
    """Complete MD3 type scale."""

    display_large: TypeStyle
    display_medium: TypeStyle
    display_small: TypeStyle

    headline_large: TypeStyle
    headline_medium: TypeStyle
    headline_small: TypeStyle

    title_large: TypeStyle
    title_medium: TypeStyle
    title_small: TypeStyle

    label_large: TypeStyle
    label_medium: TypeStyle
    label_small: TypeStyle

    body_large: TypeStyle
    body_medium: TypeStyle
    body_small: TypeStyle


DEFAULT_TYPOGRAPHY = Typography(
    display_large=TypeStyle(_ROBOTO, 400, 57, 64, -0.25),
    display_medium=TypeStyle(_ROBOTO, 400, 45, 52),
    display_small=TypeStyle(_ROBOTO, 400, 36, 44),
    headline_large=TypeStyle(_ROBOTO, 400, 32, 40),
    headline_medium=TypeStyle(_ROBOTO, 400, 28, 36),
    headline_small=TypeStyle(_ROBOTO, 400, 24, 32),
    title_large=TypeStyle(_ROBOTO, 400, 22, 28),
    title_medium=TypeStyle(_ROBOTO, 500, 16, 24, 0.15),
    title_small=TypeStyle(_ROBOTO, 500, 14, 20, 0.1),
    label_large=TypeStyle(_ROBOTO, 500, 14, 20, 0.1),
    label_medium=TypeStyle(_ROBOTO, 500, 12, 16, 0.5),
    label_small=TypeStyle(_ROBOTO, 500, 11, 16, 0.5),
    body_large=TypeStyle(_ROBOTO, 400, 16, 24, 0.5),
    body_medium=TypeStyle(_ROBOTO, 400, 14, 20, 0.25),
    body_small=TypeStyle(_ROBOTO, 400, 12, 16, 0.4),
)
