"""
IFieldWidget – interface protocol for field-level input widgets.

A field widget is responsible for displaying and editing a single field value
inside a form or inline-edit tree.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class IFieldWidget(Protocol):
    """Contract shared by every field widget."""

    @property
    def field_name(self) -> str:
        """The model field name this widget is bound to."""
        ...

    def set_value(self, value: Any) -> None:
        """Update the displayed value without triggering model writes."""
        ...

    def get_value(self) -> Any:
        """Return the current (possibly unsaved) widget value."""
        ...

    def is_valid(self) -> bool:
        """``True`` if the current value satisfies all constraints."""
        ...

    def set_read_only(self, read_only: bool) -> None:
        """Switch between editable and read-only display."""
        ...

    def set_required(self, required: bool) -> None:
        """Mark / unmark the field as required."""
        ...

    def reset_validity(self) -> None:
        """Clear any visual validation indicators."""
        ...
