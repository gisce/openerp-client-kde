"""
MaterialButton – MD3-styled QPushButton with three variants.

Variants
--------
filled   (default) – elevated blue button for primary actions
outlined           – border-only button for secondary actions
text               – no background, used for tertiary actions
"""
from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy


class ButtonVariant(Enum):
    FILLED = auto()
    OUTLINED = auto()
    TEXT = auto()


class MaterialButton(QPushButton):
    """A QPushButton styled according to MD3 button specifications.

    The button's CSS variant is applied via Qt dynamic properties so that
    the QSS stylesheet can target ``QPushButton[outlined="true"]`` etc.
    without subclassing.
    """

    def __init__(
        self,
        text: str = "",
        variant: ButtonVariant = ButtonVariant.FILLED,
        parent=None,
    ) -> None:
        super().__init__(text, parent)
        self._variant = variant
        self._apply_variant()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def variant(self) -> ButtonVariant:
        return self._variant

    @variant.setter
    def variant(self, value: ButtonVariant) -> None:
        self._variant = value
        self._apply_variant()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _apply_variant(self) -> None:
        """Set Qt dynamic properties consumed by the QSS rules."""
        # Reset all variant properties first
        for prop in ("flat", "outlined"):
            self.setProperty(prop, False)

        if self._variant == ButtonVariant.TEXT:
            self.setProperty("flat", True)
        elif self._variant == ButtonVariant.OUTLINED:
            self.setProperty("outlined", True)

        # Force the style engine to re-evaluate property-based selectors
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
