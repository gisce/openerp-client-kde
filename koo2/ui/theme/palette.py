"""
Material Design 3 color palette.

Token names follow the MD3 specification so that the palette can be updated
easily (e.g. for dark-mode support or custom brand colours).

Reference: https://m3.material.io/styles/color/the-color-system/tokens
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorRole:
    """A pair of (background, on-background) colors for a single MD3 role."""

    color: str        # CSS hex, e.g. '#1565C0'
    on_color: str     # Color used for content *on top of* `color`


@dataclass(frozen=True)
class Palette:
    """Full Material Design 3 color scheme.

    The default scheme uses a blue-dominant palette compatible with the
    Ant Design tokens used in the companion web client.
    """

    # Core roles
    primary: ColorRole
    secondary: ColorRole
    tertiary: ColorRole
    error: ColorRole

    # Surface roles
    background: str
    on_background: str
    surface: str
    on_surface: str
    surface_variant: str
    on_surface_variant: str

    # Utility
    outline: str
    outline_variant: str

    # Container variants
    primary_container: str
    on_primary_container: str
    secondary_container: str
    on_secondary_container: str

    # State layer alphas (0-255 as integers, converted where needed)
    hover_state_layer_opacity: float = 0.08
    pressed_state_layer_opacity: float = 0.12
    focused_state_layer_opacity: float = 0.12
    dragged_state_layer_opacity: float = 0.16


# ---------------------------------------------------------------------------
# Default light palette  (MD3 blue-tinted, Ant-Design compatible)
# ---------------------------------------------------------------------------
DEFAULT_LIGHT = Palette(
    primary=ColorRole(color="#1565C0", on_color="#FFFFFF"),
    secondary=ColorRole(color="#006A6A", on_color="#FFFFFF"),
    tertiary=ColorRole(color="#006C52", on_color="#FFFFFF"),
    error=ColorRole(color="#B3261E", on_color="#FFFFFF"),
    background="#FDFCFF",
    on_background="#1A1C1E",
    surface="#FDFCFF",
    on_surface="#1A1C1E",
    surface_variant="#DFE2EB",
    on_surface_variant="#43474E",
    outline="#73777F",
    outline_variant="#C3C7CF",
    primary_container="#D1E4FF",
    on_primary_container="#001D36",
    secondary_container="#9CF0F0",
    on_secondary_container="#002020",
)

# ---------------------------------------------------------------------------
# Default dark palette
# ---------------------------------------------------------------------------
DEFAULT_DARK = Palette(
    primary=ColorRole(color="#9ECAFF", on_color="#003258"),
    secondary=ColorRole(color="#4DD9D9", on_color="#003737"),
    tertiary=ColorRole(color="#6DDBB4", on_color="#003829"),
    error=ColorRole(color="#F2B8B5", on_color="#601410"),
    background="#1A1C1E",
    on_background="#E2E2E6",
    surface="#1A1C1E",
    on_surface="#E2E2E6",
    surface_variant="#43474E",
    on_surface_variant="#C3C7CF",
    outline="#8D9199",
    outline_variant="#43474E",
    primary_container="#003258",
    on_primary_container="#D1E4FF",
    secondary_container="#004F4F",
    on_secondary_container="#9CF0F0",
)
