"""
koo2/infrastructure/rpc/erppeek_client.py — ErppeekRpcClient

Pure erppeek-based transport layer. Replaces OpenErpRpcClient (which delegated
to the legacy Koo.Rpc layer). Exposes the same public interface so callers can
swap implementations transparently.

Usage
-----
    client = ErppeekRpcClient()
    client.login("http://localhost:8069", "mydb", "admin", "admin")
    ids = client.search("res.partner", [("is_company", "=", True)])
    records = client.read("res.partner", ids, ["name", "email"])
    client.logout()
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from koo2.core.domain.session import Session, SessionState


class RpcError(Exception):
    """Raised when the server returns an error."""


class RpcAuthError(RpcError):
    """Raised on invalid credentials."""


class ErppeekRpcClient:
    """IRpcClient implementation backed by erppeek.

    erppeek is imported lazily so that unit-tests that mock it work without a
    running server.
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None   # erppeek.Client instance
        self._current: Session = Session()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def login(
        self,
        url: str,
        database: str,
        username: str,
        password: str,
    ) -> bool:
        """Connect and authenticate against the OpenERP/Odoo server.

        Returns ``True`` on success.  Raises :exc:`RpcAuthError` for bad
        credentials and :exc:`RpcError` for other server-side failures.
        """
        import erppeek  # lazy import so tests can patch sys.modules

        try:
            client = erppeek.Client(url, db=database, user=username, password=password)
        except erppeek.Error as exc:
            msg = str(exc)
            if "Invalid credentials" in msg or "Access denied" in msg:
                self._current = self._current.failed(invalid_credentials=True)
                raise RpcAuthError(msg) from exc
            self._current = self._current.failed()
            raise RpcError(msg) from exc
        except Exception as exc:  # connection errors, etc.
            self._current = self._current.failed()
            raise RpcError(str(exc)) from exc

        self._client = client
        self._current = Session(
            url=url,
            database=database,
            username=username,
            uid=client.uid,
            state=SessionState.LOGGED_IN,
            context=dict(client.context or {}),
        )
        return True

    def logout(self) -> None:
        """Drop the current connection."""
        self._client = None
        self._current = Session()

    @property
    def is_logged_in(self) -> bool:
        return self._current.is_logged_in

    @property
    def current_session(self) -> Session:
        return self._current

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_client(self) -> Any:
        if self._client is None:
            raise RpcError("Not logged in")
        return self._client

    def _model(self, model: str) -> Any:
        """Return an erppeek Model proxy for *model*."""
        return self._require_client().model(model)

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
        kwargs: Dict[str, Any] = {"context": context or {}}
        if offset:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self._require_client().execute(
            model, "search", domain or [], **kwargs
        )

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {"context": context or {}}
        args: List[Any] = [ids]
        if fields is not None:
            args.append(fields)
        return self._require_client().execute(model, "read", *args, **kwargs)

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> bool:
        return self._require_client().execute(
            model, "write", ids, values, context=context or {}
        )

    def create(
        self,
        model: str,
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> int:
        return self._require_client().execute(
            model, "create", values, context=context or {}
        )

    def unlink(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict] = None,
    ) -> bool:
        return self._require_client().execute(
            model, "unlink", ids, context=context or {}
        )

    def execute(
        self,
        model: str,
        method: str,
        *args: Any,
        context: Optional[Dict] = None,
    ) -> Any:
        return self._require_client().execute(
            model, method, *args, context=context or {}
        )

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------
    def fields_get(
        self,
        model: str,
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Dict[str, Any]]:
        args: List[Any] = []
        if fields is not None:
            args.append(fields)
        return self._require_client().execute(
            model, "fields_get", *args, context=context or {}
        )

    def fields_view_get(
        self,
        model: str,
        view_id: Optional[int] = None,
        view_type: str = "form",
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        return self._require_client().execute(
            model,
            "fields_view_get",
            view_id or False,
            view_type,
            context=context or {},
        )
