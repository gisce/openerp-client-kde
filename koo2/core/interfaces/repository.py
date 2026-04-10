"""
IRepository – generic read/write repository protocol.

Abstracts the data-access layer so views never depend on a specific RPC
backend.  See ``koo2.infrastructure.rpc`` for the concrete implementation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class IRepository(Protocol):
    """Generic CRUD repository for a single OpenERP model."""

    @property
    def model_name(self) -> str:
        """The technical model name, e.g. ``'res.partner'``."""
        ...

    def find(
        self,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Search and read in a single call; returns a list of value dicts."""
        ...

    def get(
        self,
        record_id: int,
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return the value dict for a single record, or ``None``."""
        ...

    def save(
        self,
        record_id: Optional[int],
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> int:
        """Create (``record_id=None``) or update an existing record.

        Returns the final record id.
        """
        ...

    def delete(
        self,
        record_id: int,
        context: Optional[Dict] = None,
    ) -> None:
        """Permanently delete a record."""
        ...

    def get_field_definitions(
        self,
        context: Optional[Dict] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Return the ``fields_get`` metadata dict for this model."""
        ...

    def get_view_definition(
        self,
        view_type: str = "form",
        view_id: Optional[int] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Return the ``fields_view_get`` dict (arch + fields)."""
        ...
