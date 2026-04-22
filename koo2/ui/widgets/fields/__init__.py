"""Field widgets: Char, Text, Integer, Float, Boolean, Date, DateTime,
Selection, Many2one.  All inherit AbstractFieldWidget."""
from __future__ import annotations

from typing import Any, List, Optional, Tuple

from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QDoubleSpinBox,
    QWidget,
)

from .base import AbstractFieldWidget


# ---------------------------------------------------------------------------
# Char
# ---------------------------------------------------------------------------

class CharWidget(AbstractFieldWidget):
    """Single-line text field — mirrors ooui Char."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._edit = QLineEdit(self)
        self._edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._edit)

    def get_value(self) -> str:
        return self._edit.text()

    def set_value(self, value: Any) -> None:
        self._edit.setText("" if value is None else str(value))

    def _apply_read_only(self, read_only: bool) -> None:
        self._edit.setReadOnly(read_only)


# ---------------------------------------------------------------------------
# Text (multiline)
# ---------------------------------------------------------------------------

class TextWidget(AbstractFieldWidget):
    """Multiline text — mirrors ooui Text."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._edit = QPlainTextEdit(self)
        self._edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._edit)

    def get_value(self) -> str:
        return self._edit.toPlainText()

    def set_value(self, value: Any) -> None:
        self._edit.setPlainText("" if value is None else str(value))

    def _apply_read_only(self, read_only: bool) -> None:
        self._edit.setReadOnly(read_only)


# ---------------------------------------------------------------------------
# Integer
# ---------------------------------------------------------------------------

class IntegerWidget(AbstractFieldWidget):
    """Integer spin box — mirrors ooui Integer."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._spin = QSpinBox(self)
        self._spin.setRange(-2_147_483_648, 2_147_483_647)
        self._spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._spin)

    def get_value(self) -> int:
        return self._spin.value()

    def set_value(self, value: Any) -> None:
        try:
            self._spin.setValue(int(value) if value is not None else 0)
        except (TypeError, ValueError):
            self._spin.setValue(0)

    def _apply_read_only(self, read_only: bool) -> None:
        self._spin.setReadOnly(read_only)


# ---------------------------------------------------------------------------
# Float
# ---------------------------------------------------------------------------

class FloatWidget(AbstractFieldWidget):
    """Float spin box — mirrors ooui Float."""

    def __init__(self, decimals: int = 2, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._spin = QDoubleSpinBox(self)
        self._spin.setDecimals(decimals)
        self._spin.setRange(-1e12, 1e12)
        self._spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._spin)

    def get_value(self) -> float:
        return self._spin.value()

    def set_value(self, value: Any) -> None:
        try:
            self._spin.setValue(float(value) if value is not None else 0.0)
        except (TypeError, ValueError):
            self._spin.setValue(0.0)

    def _apply_read_only(self, read_only: bool) -> None:
        self._spin.setReadOnly(read_only)


# ---------------------------------------------------------------------------
# Boolean
# ---------------------------------------------------------------------------

class BooleanWidget(AbstractFieldWidget):
    """Check box — mirrors ooui Boolean."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._check = QCheckBox(self)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._check)

    def get_value(self) -> bool:
        return self._check.isChecked()

    def set_value(self, value: Any) -> None:
        self._check.setChecked(bool(value))

    def _apply_read_only(self, read_only: bool) -> None:
        self._check.setEnabled(not read_only)


# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------

class DateWidget(AbstractFieldWidget):
    """Date picker — mirrors ooui Date."""

    _DATE_FMT = "yyyy-MM-dd"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._edit = QDateEdit(self)
        self._edit.setDisplayFormat(self._DATE_FMT)
        self._edit.setCalendarPopup(True)
        self._edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._edit)

    def get_value(self) -> Optional[str]:
        if not self._edit.date().isValid():
            return None
        return self._edit.date().toString(self._DATE_FMT)

    def set_value(self, value: Any) -> None:
        if value:
            d = QDate.fromString(str(value)[:10], self._DATE_FMT)
            if d.isValid():
                self._edit.setDate(d)
                return
        self._edit.setDate(QDate.currentDate())

    def _apply_read_only(self, read_only: bool) -> None:
        self._edit.setReadOnly(read_only)


# ---------------------------------------------------------------------------
# DateTime
# ---------------------------------------------------------------------------

class DateTimeWidget(AbstractFieldWidget):
    """Date + time picker — mirrors ooui DateTime."""

    _FMT = "yyyy-MM-dd HH:mm:ss"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._edit = QDateTimeEdit(self)
        self._edit.setDisplayFormat(self._FMT)
        self._edit.setCalendarPopup(True)
        self._edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._edit)

    def get_value(self) -> Optional[str]:
        if not self._edit.dateTime().isValid():
            return None
        return self._edit.dateTime().toString(self._FMT)

    def set_value(self, value: Any) -> None:
        if value:
            dt = QDateTime.fromString(str(value), self._FMT)
            if dt.isValid():
                self._edit.setDateTime(dt)
                return
        self._edit.setDateTime(QDateTime.currentDateTime())

    def _apply_read_only(self, read_only: bool) -> None:
        self._edit.setReadOnly(read_only)


# ---------------------------------------------------------------------------
# Selection (combo box)
# ---------------------------------------------------------------------------

class SelectionWidget(AbstractFieldWidget):
    """Combo box for selection fields — mirrors ooui Selection."""

    def __init__(
        self,
        selection: Optional[List[Tuple[str, str]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._combo = QComboBox(self)
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._values: List[str] = []
        if selection:
            self.set_selection(selection)
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._combo)

    def set_selection(self, selection: List[Tuple[str, str]]) -> None:
        self._combo.clear()
        self._values = []
        for key, label in selection:
            self._combo.addItem(str(label))
            self._values.append(str(key))

    def get_value(self) -> Optional[str]:
        idx = self._combo.currentIndex()
        if idx < 0 or idx >= len(self._values):
            return None
        return self._values[idx]

    def set_value(self, value: Any) -> None:
        key = str(value) if value is not None else ""
        if key in self._values:
            self._combo.setCurrentIndex(self._values.index(key))

    def _apply_read_only(self, read_only: bool) -> None:
        self._combo.setEnabled(not read_only)


# ---------------------------------------------------------------------------
# Many2one (text + lookup button placeholder)
# ---------------------------------------------------------------------------

class Many2oneWidget(AbstractFieldWidget):
    """Many2one: display name in a line edit (lookup TBD) — mirrors ooui Many2one."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText("Search…")
        self._edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Store the underlying id alongside the display name
        self._id: Optional[int] = None
        from PySide6.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._edit)

    def get_value(self) -> Optional[list]:
        """Return [id, name] or None."""
        if self._id is None:
            return None
        return [self._id, self._edit.text()]

    def set_value(self, value: Any) -> None:
        """Accept [id, name], (id, name), an id int, or a name string."""
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            self._id = value[0]
            self._edit.setText(str(value[1]))
        elif isinstance(value, int):
            self._id = value
            self._edit.setText(str(value))
        elif value:
            self._id = None
            self._edit.setText(str(value))
        else:
            self._id = None
            self._edit.setText("")

    def _apply_read_only(self, read_only: bool) -> None:
        self._edit.setReadOnly(read_only)
