"""
BaseView – abstract PySide6 widget base class implementing IView.

Subclasses override ``view_type()``, ``display()``, ``store()`` and the other
hooks defined in ``koo2.core.interfaces.view.IView``.

Design principles
-----------------
* Single Responsibility – only presentation; no business logic.
* Open/Closed – new view types extend this base without touching it.
* Liskov Substitution – every subclass is a valid IView.
* Interface Segregation – thin protocol; optional hooks have default no-ops.
* Dependency Inversion – depends on the IRepository protocol, not a concrete
  adapter.
"""
from __future__ import annotations

from typing import Any, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from koo2.core.domain.record import Record
from koo2.core.domain.view_definition import ViewDefinition


class BaseView(QWidget):
    """Abstract base for all koo2 views.

    Subclasses MUST override :meth:`view_type` and :meth:`display`.
    """

    # Emitted when the user modifies a field so the parent screen knows
    # the view is dirty.
    record_modified = Signal(object)   # payload: Record

    def __init__(
        self,
        view_definition: Optional[ViewDefinition] = None,
        read_only: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._view_definition = view_definition
        self._read_only = read_only
        self._current_record: Optional[Record] = None

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

    # ------------------------------------------------------------------
    # IView protocol
    # ------------------------------------------------------------------
    def view_type(self) -> str:
        """Must return e.g. ``'form'``, ``'tree'``, ``'calendar'``."""
        raise NotImplementedError

    def display(self, record: Any, records: Any = None) -> None:
        """Render *record*.  Override in subclasses."""
        self._current_record = record if isinstance(record, Record) else None

    def store(self) -> None:
        """Flush widget values back to the current record.  Override if needed."""

    def reset(self) -> None:
        """Clear validation state.  Override if needed."""

    def selected_records(self) -> List[Any]:
        if self._current_record is not None:
            return [self._current_record]
        return []

    def set_selected(self, record: Any) -> None:
        self._current_record = record if isinstance(record, Record) else None

    def is_read_only(self) -> bool:
        return self._read_only

    def set_read_only(self, value: bool) -> None:
        self._read_only = value
        self._on_read_only_changed(value)

    def shows_multiple_records(self) -> bool:
        return False

    def start_editing(self) -> None:
        """Override in list-like views (tree)."""

    # ------------------------------------------------------------------
    # Extension points for subclasses
    # ------------------------------------------------------------------
    def _on_read_only_changed(self, read_only: bool) -> None:
        """Called when the read-only state changes.  Override to update UI."""

    @property
    def view_definition(self) -> Optional[ViewDefinition]:
        return self._view_definition

    @property
    def current_record(self) -> Optional[Record]:
        return self._current_record
