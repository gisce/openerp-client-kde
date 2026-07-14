"""
RecordLifecycleService - UI-neutral record lifecycle orchestration.

The service keeps form controllers and future QGIS entry points independent
from a concrete RPC backend while preserving the lifecycle expected from Koo:
new, load, save, duplicate, discard, reload and delete.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from koo2.core.domain.record import Record
from koo2.core.interfaces.repository import IRepository


class RecordLifecycleError(Exception):
    """Raised when an invalid record lifecycle transition is requested."""


class RecordLifecycleService:
    """Coordinate record lifecycle operations through an IRepository."""

    def __init__(self, repository: IRepository) -> None:
        self._repository = repository

    @property
    def model_name(self) -> str:
        return self._repository.model_name

    def new(self, defaults: Optional[Dict[str, Any]] = None) -> Record:
        """Create a new unsaved record with optional defaults."""
        return Record.new(self.model_name, defaults=defaults)

    def load(
        self,
        record_id: int,
        fields: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """Load one record or fail with a domain-specific error."""
        record = self._repository.get(record_id, fields=fields, context=context)
        if record is None:
            raise RecordLifecycleError(
                "Record %s,%s was not found" % (self.model_name, record_id)
            )
        return record

    def save(
        self,
        record: Record,
        context: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """Persist a new or modified record.

        Clean existing records are returned untouched so a refresh, close or
        focus change cannot generate unnecessary server writes.
        """
        self._ensure_model(record)
        if not record.is_new and not record.is_modified:
            return record
        return self._repository.save(record, context=context)

    def delete(
        self,
        record: Record,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Delete a saved record."""
        self._ensure_model(record)
        if record.is_new:
            raise RecordLifecycleError("Cannot delete an unsaved record")
        self._repository.delete(record.id, context=context)

    def duplicate(
        self,
        record: Record,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """Create an unsaved copy of an existing record.

        The server id is intentionally removed.  Callers may pass overrides for
        fields such as ``name`` where the UI wants to append "(copy)".
        """
        self._ensure_model(record)
        values = deepcopy(record.values)
        values.pop("id", None)
        if overrides:
            values.update(overrides)
        return Record.new(self.model_name, values)

    def discard(self, record: Record) -> Record:
        """Discard unsaved changes in-place and return the same record."""
        self._ensure_model(record)
        record.discard()
        return record

    def reload(
        self,
        record: Record,
        fields: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """Reload a saved record from the server."""
        self._ensure_model(record)
        if record.is_new:
            raise RecordLifecycleError("Cannot reload an unsaved record")
        return self.load(record.id, fields=fields, context=context)

    def _ensure_model(self, record: Record) -> None:
        if record.model != self.model_name:
            raise RecordLifecycleError(
                "Record model %s does not match repository model %s"
                % (record.model, self.model_name)
            )
