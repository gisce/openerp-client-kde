"""
IRpcClient – interface protocol for the OpenERP RPC layer.

Concrete implementations live in koo2.infrastructure.rpc.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class IRpcClient(Protocol):
    """Minimal contract that every RPC backend must satisfy."""

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def login(self, url: str, database: str, username: str, password: str) -> bool:
        """Authenticate against the server.

        Returns True on success, raises RpcError on failure.
        """
        ...

    def logout(self) -> None:
        """Close the current session."""
        ...

    @property
    def is_logged_in(self) -> bool:
        """True when a valid session is active."""
        ...

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------
    def search(
        self,
        model: str,
        domain: Optional[List] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> List[int]:
        """Return a list of record ids matching *domain*."""
        ...

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Return field values for each id in *ids*."""
        ...

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> bool:
        """Update *values* on all records in *ids*."""
        ...

    def create(
        self,
        model: str,
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> int:
        """Create a new record and return its id."""
        ...

    def unlink(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict] = None,
    ) -> bool:
        """Delete records identified by *ids*."""
        ...

    def execute(
        self,
        model: str,
        method: str,
        *args: Any,
        context: Optional[Dict] = None,
    ) -> Any:
        """Call an arbitrary model method."""
        ...

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------
    def fields_get(
        self,
        model: str,
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Return field metadata for *model*."""
        ...

    def fields_view_get(
        self,
        model: str,
        view_id: Optional[int] = None,
        view_type: str = "form",
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Return the view definition (arch + fields) for *model*."""
        ...
