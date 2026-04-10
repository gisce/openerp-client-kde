"""
MaterialTextField – MD3 filled text field with floating label support.

The widget wraps a QLineEdit inside a QWidget container so that the floating
label animation (label moves up when focused or non-empty) can be achieved
purely in Python without a custom QSS hack.
"""
from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, Qt, QEasingCurve
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette


class MaterialTextField(QWidget):
    """MD3 filled text field with an animated floating label.

    Signals forwarded from the inner QLineEdit:
        textChanged(str)
        editingFinished()
        returnPressed()
    """

    def __init__(
        self,
        label: str = "",
        placeholder: str = "",
        palette: Palette = DEFAULT_LIGHT,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._palette = palette

        self._label_text = label
        self._build_ui(placeholder)
        self._connect_signals()

    # ------------------------------------------------------------------
    # Public API (mirrors QLineEdit)
    # ------------------------------------------------------------------
    @property
    def text(self) -> str:
        return self._edit.text()

    @text.setter
    def text(self, value: str) -> None:
        self._edit.setText(value)

    def setText(self, value: str) -> None:
        self._edit.setText(value)

    def setEchoMode(self, mode: QLineEdit.EchoMode) -> None:
        self._edit.setEchoMode(mode)

    def setReadOnly(self, read_only: bool) -> None:
        self._edit.setReadOnly(read_only)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._edit.setEnabled(enabled)

    def setPlaceholderText(self, text: str) -> None:
        self._edit.setPlaceholderText(text)

    # Signal proxy --------------------------------------------------------
    @property
    def textChanged(self):
        return self._edit.textChanged

    @property
    def editingFinished(self):
        return self._edit.editingFinished

    @property
    def returnPressed(self):
        return self._edit.returnPressed

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _build_ui(self, placeholder: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Floating label
        self._label = QLabel(self._label_text, self)
        label_font = QFont()
        label_font.setPointSize(12)
        self._label.setFont(label_font)
        self._label.setStyleSheet(
            f"color: {self._palette.on_surface_variant}; background: transparent;"
        )

        # Line edit
        self._edit = QLineEdit(self)
        if placeholder:
            self._edit.setPlaceholderText(placeholder)

        layout.addWidget(self._label)
        layout.addWidget(self._edit)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _connect_signals(self) -> None:
        self._edit.focusInEvent = self._on_focus_in  # type: ignore[assignment]
        self._edit.focusOutEvent = self._on_focus_out  # type: ignore[assignment]

    def _on_focus_in(self, event) -> None:
        self._label.setStyleSheet(
            f"color: {self._palette.primary.color}; background: transparent;"
        )
        QLineEdit.focusInEvent(self._edit, event)

    def _on_focus_out(self, event) -> None:
        self._label.setStyleSheet(
            f"color: {self._palette.on_surface_variant}; background: transparent;"
        )
        QLineEdit.focusOutEvent(self._edit, event)
