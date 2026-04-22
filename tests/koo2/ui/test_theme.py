"""
Tests for koo2.ui.theme.palette and koo2.ui.theme.stylesheet

No Qt display required for palette tests; stylesheet tests need a
QApplication but run with QT_QPA_PLATFORM=offscreen.
"""
import os
import re
import pytest

# -----------------------------------------------------------------------
# Pure-Python palette tests (no Qt required)
# -----------------------------------------------------------------------
from koo2.ui.theme.palette import DEFAULT_LIGHT, DEFAULT_DARK, Palette, ColorRole


class TestColorRole:
    def test_color_is_hex(self):
        role = ColorRole(color="#1565C0", on_color="#FFFFFF")
        assert role.color.startswith("#")
        assert len(role.color) == 7

    def test_on_color_is_hex(self):
        role = ColorRole(color="#1565C0", on_color="#FFFFFF")
        assert role.on_color.startswith("#")


class TestDefaultLightPalette:
    def test_primary_color_defined(self):
        assert DEFAULT_LIGHT.primary.color != ""

    def test_surface_is_hex(self):
        assert DEFAULT_LIGHT.surface.startswith("#")

    def test_error_defined(self):
        assert DEFAULT_LIGHT.error.color != ""

    def test_outline_defined(self):
        assert DEFAULT_LIGHT.outline.startswith("#")

    def test_primary_container_defined(self):
        assert DEFAULT_LIGHT.primary_container.startswith("#")

    def test_state_layer_opacities_in_range(self):
        p = DEFAULT_LIGHT
        for val in (
            p.hover_state_layer_opacity,
            p.pressed_state_layer_opacity,
            p.focused_state_layer_opacity,
            p.dragged_state_layer_opacity,
        ):
            assert 0.0 <= val <= 1.0

    def test_dark_and_light_have_different_primary(self):
        assert DEFAULT_LIGHT.primary.color != DEFAULT_DARK.primary.color

    def test_palette_is_frozen(self):
        with pytest.raises((AttributeError, TypeError)):
            DEFAULT_LIGHT.surface = "#000000"  # type: ignore[misc]


class TestDefaultTypography:
    def test_body_medium_size_positive(self):
        from koo2.ui.theme.typography import DEFAULT_TYPOGRAPHY
        assert DEFAULT_TYPOGRAPHY.body_medium.size > 0

    def test_headline_larger_than_body(self):
        from koo2.ui.theme.typography import DEFAULT_TYPOGRAPHY
        assert DEFAULT_TYPOGRAPHY.headline_large.size > DEFAULT_TYPOGRAPHY.body_large.size

    def test_title_family_set(self):
        from koo2.ui.theme.typography import DEFAULT_TYPOGRAPHY
        assert DEFAULT_TYPOGRAPHY.title_large.family != ""


# -----------------------------------------------------------------------
# Stylesheet tests (also pure-Python – just string generation)
# -----------------------------------------------------------------------
from koo2.ui.theme.stylesheet import build_stylesheet


class TestBuildStylesheet:
    def test_returns_string(self):
        css = build_stylesheet()
        assert isinstance(css, str)

    def test_contains_qwidget_rule(self):
        css = build_stylesheet()
        assert "QWidget" in css

    def test_contains_primary_color(self):
        css = build_stylesheet(DEFAULT_LIGHT)
        assert DEFAULT_LIGHT.primary.color in css

    def test_contains_button_rule(self):
        css = build_stylesheet()
        assert "QPushButton" in css

    def test_contains_line_edit_rule(self):
        css = build_stylesheet()
        assert "QLineEdit" in css

    def test_contains_table_view_rule(self):
        css = build_stylesheet()
        assert "QTableView" in css

    def test_dark_palette_produces_dark_colors(self):
        css = build_stylesheet(DEFAULT_DARK)
        assert DEFAULT_DARK.primary.color in css

    def test_hex_with_alpha_helper(self):
        from koo2.ui.theme.stylesheet import _hex_with_alpha
        result = _hex_with_alpha("#FF0000", 0.5)
        assert result.startswith("rgba(255, 0, 0,")
