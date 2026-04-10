"""
MaterialCard – MD3 elevated / filled card container.

A card is a rectangular surface that holds related content.  This
implementation provides two elevation variants:

* ``Elevation.NONE``     – flat surface (filled card)
* ``Elevation.LEVEL1``   – 1dp shadow  (elevated card)
* ``Elevation.LEVEL2``   – 3dp shadow
"""
from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QVBoxLayout, QWidget, QGraphicsDropShadowEffect

from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette


class CardElevation(Enum):
    NONE = auto()
    LEVEL1 = auto()
    LEVEL2 = auto()


_SHADOW_PARAMS = {
    CardElevation.NONE: None,
    CardElevation.LEVEL1: (2, 1, 3, 0.15),
    CardElevation.LEVEL2: (6, 2, 8, 0.20),
}


class MaterialCard(QWidget):
    """MD3 card container with optional drop-shadow elevation.

    Use as a plain QWidget container::

        card = MaterialCard(elevation=CardElevation.LEVEL1)
        layout = card.body_layout
        layout.addWidget(some_widget)
    """

    def __init__(
        self,
        elevation: CardElevation = CardElevation.LEVEL1,
        palette: Palette = DEFAULT_LIGHT,
        parent: QWidget | None = None,
        radius: int = 12,
    ) -> None:
        super().__init__(parent)
        self._palette = palette
        self._radius = radius

        # Content layout callers can add widgets to
        self._body = QVBoxLayout(self)
        self._body.setContentsMargins(16, 16, 16, 16)
        self._body.setSpacing(8)

        self.setObjectName("MaterialCard")
        self.setAutoFillBackground(True)
        self._apply_elevation(elevation)

    @property
    def body_layout(self) -> QVBoxLayout:
        """The inner layout clients should add widgets to."""
        return self._body

    def set_elevation(self, elevation: CardElevation) -> None:
        self._apply_elevation(elevation)

    # ------------------------------------------------------------------
    def _apply_elevation(self, elevation: CardElevation) -> None:
        params = _SHADOW_PARAMS[elevation]
        if params is None:
            self.setGraphicsEffect(None)
        else:
            blur, x_offset, y_offset, alpha = params
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(blur * 4)
            shadow.setXOffset(x_offset)
            shadow.setYOffset(y_offset)
            color = QColor(0, 0, 0)
            color.setAlphaF(alpha)
            shadow.setColor(color)
            self.setGraphicsEffect(shadow)

        self.setStyleSheet(
            f"#MaterialCard {{ "
            f"  background-color: {self._palette.surface}; "
            f"  border-radius: {self._radius}px; "
            f"}}"
        )
