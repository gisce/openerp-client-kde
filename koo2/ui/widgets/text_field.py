"""
MaterialTextField – MD3 filled text field with floating label support.

The widget wraps a QLineEdit inside a QWidget container so that the floating
label colour changes with focus state.  Focus tracking is implemented via
QObject.installEventFilter() rather than monkey-patching event methods.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette


class _FocusFilter(QObject):
    """Event filter that notifies the parent text field on focus changes."""

    def __init__(self, text_field: "MaterialTextField") -> None:
        super().__init__(text_field)
        self._field = text_field

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.FocusIn:
            self._field._on_focus_in()
        elif event.type() == QEvent.Type.FocusOut:
            self._field._on_focus_out()
        return super().eventFilter(watched, event)


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

        # Line edit – use an event filter instead of monkey-patching events
        self._edit = QLineEdit(self)
        if placeholder:
            self._edit.setPlaceholderText(placeholder)

        self._focus_filter = _FocusFilter(self)
        self._edit.installEventFilter(self._focus_filter)

        layout.addWidget(self._label)
        layout.addWidget(self._edit)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _on_focus_in(self) -> None:
        self._label.setStyleSheet(
            f"color: {self._palette.primary.color}; background: transparent;"
        )

    def _on_focus_out(self) -> None:
        self._label.setStyleSheet(
            f"color: {self._palette.on_surface_variant}; background: transparent;"
        )

