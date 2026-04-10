"""
Record – lightweight value object representing a single server-side record.

Records carry raw field values and track modification state without any Qt or
RPC dependency.  Higher-level concerns (loading, saving) live in the
repository layer.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Record:
    """A single ERP record with field values and modification tracking.

    Design notes
    ------------
    * ``id`` is ``None`` for unsaved (new) records.
    * ``original_values`` stores the server-side snapshot so we can detect
      dirty fields without another round-trip.
    * This class is **not** thread-safe; always mutate from the UI thread.
    """

    model: str
    id: Optional[int] = None
    values: Dict[str, Any] = field(default_factory=dict)
    original_values: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Identity helpers
    # ------------------------------------------------------------------
    @property
    def is_new(self) -> bool:
        """``True`` for records that have never been saved to the server."""
        return self.id is None

    @property
    def is_modified(self) -> bool:
        """``True`` when any field differs from the server snapshot."""
        for key, value in self.values.items():
            if self.original_values.get(key) != value:
                return True
        return False

    @property
    def dirty_fields(self) -> Dict[str, Any]:
        """Return a dict of only the fields that have changed."""
        return {
            k: v
            for k, v in self.values.items()
            if self.original_values.get(k) != v
        }

    # ------------------------------------------------------------------
    # Value access
    # ------------------------------------------------------------------
    def get(self, field_name: str, default: Any = None) -> Any:
        """Return the current (possibly unsaved) value for *field_name*."""
        return self.values.get(field_name, default)

    def set(self, field_name: str, value: Any) -> None:
        """Update a field value (marks the record as modified)."""
        self.values[field_name] = value

    def set_many(self, values: Dict[str, Any]) -> None:
        """Bulk-update several fields at once."""
        self.values.update(values)

    # ------------------------------------------------------------------
    # Snapshot management
    # ------------------------------------------------------------------
    def mark_saved(self, server_id: Optional[int] = None) -> None:
        """Accept the current values as the new server snapshot.

        Call this after a successful ``write`` or ``create`` to clear the
        modification flag.
        """
        if server_id is not None:
            self.id = server_id
        self.original_values = deepcopy(self.values)

    def discard(self) -> None:
        """Revert all unsaved changes back to the last server snapshot."""
        self.values = deepcopy(self.original_values)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_server(cls, model: str, data: Dict[str, Any]) -> "Record":
        """Create a clean (unmodified) record from a server ``read`` result."""
        record_id: Optional[int] = data.get("id")
        values = deepcopy(data)
        return cls(
            model=model,
            id=record_id,
            values=values,
            original_values=deepcopy(values),
        )

    @classmethod
    def new(cls, model: str, defaults: Optional[Dict[str, Any]] = None) -> "Record":
        """Create an empty new record with optional default values."""
        values = deepcopy(defaults or {})
        return cls(model=model, id=None, values=values, original_values={})
