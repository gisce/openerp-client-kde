"""
koo2/ui/widgets/fields/base.py — AbstractFieldWidget protocol.

Every concrete field widget must implement this interface so that FormView
can interact with any field type uniformly (same as IFieldWidget in ooui).
"""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QWidget


class AbstractFieldWidget(QWidget):
    """Base class for all field widgets.

    Subclasses override :meth:`get_value` and :meth:`set_value`, and may
    override :meth:`set_read_only` when the default QWidget.setEnabled
    behaviour is not appropriate.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._read_only: bool = False

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def get_value(self) -> Any:
        """Return the current value in Python-native form."""
        raise NotImplementedError

    def set_value(self, value: Any) -> None:
        """Display *value* in the widget."""
        raise NotImplementedError

    def set_read_only(self, read_only: bool) -> None:
        """Switch the widget between editable and read-only mode."""
        self._read_only = read_only
        self._apply_read_only(read_only)

    @property
    def read_only(self) -> bool:
        return self._read_only

    # ------------------------------------------------------------------
    # Hook for subclasses
    # ------------------------------------------------------------------

    def _apply_read_only(self, read_only: bool) -> None:
        """Called by :meth:`set_read_only`.  Override for custom behaviour."""
        self.setEnabled(not read_only)
