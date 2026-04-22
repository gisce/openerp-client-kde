"""
IView – interface protocol for all view types (form, tree, calendar, chart …).

Every concrete view must satisfy this protocol.  Views are pure presentation
objects: they receive data from the model layer and emit signals when the user
makes changes.
"""
from __future__ import annotations

from typing import Any, List, Protocol, runtime_checkable


@runtime_checkable
class IView(Protocol):
    """Contract shared by every view type."""

    def view_type(self) -> str:
        """Return a lowercase identifier, e.g. ``'form'``, ``'tree'``."""
        ...

    def display(self, record: Any, records: Any) -> None:
        """Render *record* (and optionally the full *records* group)."""
        ...

    def store(self) -> None:
        """Flush any in-progress edits back to the model."""
        ...

    def reset(self) -> None:
        """Reset validation state without discarding data."""
        ...

    def selected_records(self) -> List[Any]:
        """Return the list of currently selected records."""
        ...

    def set_selected(self, record: Any) -> None:
        """Programmatically select *record*."""
        ...

    def is_read_only(self) -> bool:
        """``True`` when the view is in read-only mode."""
        ...

    def set_read_only(self, value: bool) -> None:
        """Switch between read-only and editable mode."""
        ...

    def shows_multiple_records(self) -> bool:
        """``True`` for list-like views (tree, calendar, chart)."""
        ...

    def start_editing(self) -> None:
        """Enter edit mode on the focused element (tree rows, etc.)."""
        ...
