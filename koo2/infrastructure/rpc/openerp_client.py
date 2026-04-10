"""
OpenErpRpcClient – IRpcClient adapter that delegates to the existing
Koo.Rpc.Session + Koo.Rpc.RpcProxy infrastructure.

This keeps the proven XMLRPC / msgpack / socket transport stack intact while
exposing a clean, typed interface to the rest of koo2.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from koo2.core.domain.session import Session, SessionState


class RpcError(Exception):
    """Raised when the server returns an error."""


class RpcAuthError(RpcError):
    """Raised on invalid credentials."""


class OpenErpRpcClient:
    """Concrete IRpcClient implementation backed by Koo.Rpc.Session.

    The underlying ``Koo.Rpc`` module is imported lazily so that unit-tests
    that do *not* touch the network can import this module without needing a
    running server.
    """

    def __init__(self) -> None:
        self._session: Optional[Any] = None  # Koo.Rpc.Session instance
        self._current: Session = Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_koo_session(self) -> Any:
        """Return the Koo.Rpc.Session singleton (lazy import)."""
        if self._session is None:
            import importlib  # noqa: PLC0415
            KooRpc = importlib.import_module("Koo.Rpc")
            self._session = KooRpc.session
        return self._session

    def _proxy(self, model: str) -> Any:
        """Return a Koo.Rpc.RpcProxy for *model*."""
        from Koo.Rpc import RpcProxy  # noqa: PLC0415
        return RpcProxy(model)

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
        """Authenticate against the server.

        On success the internal Session is updated and ``True`` is returned.
        Raises ``RpcAuthError`` on invalid credentials and ``RpcError`` for
        other server-side failures.
        """
        import importlib  # noqa: PLC0415
        koo_session = self._get_koo_session()
        login_url = f"{url}/{username}:{password}@{database}"
        result = koo_session.login(login_url, database)

        # Lazily resolve the Koo Session constants so the import happens
        # after sys.modules is patched in tests.
        koo_rpc_rpc = importlib.import_module("Koo.Rpc.Rpc")
        logged_in_code = koo_rpc_rpc.Session.LoggedIn
        invalid_code = koo_rpc_rpc.Session.InvalidCredentials

        if result == logged_in_code:
            self._current = Session(
                url=url,
                database=database,
                username=username,
                uid=koo_session.uid,
                state=SessionState.LOGGED_IN,
                context=dict(koo_session.context or {}),
            )
            return True
        elif result == invalid_code:
            self._current = self._current.failed(invalid_credentials=True)
            raise RpcAuthError("Invalid username or password")
        else:
            self._current = self._current.failed()
            raise RpcError("Login failed")

    def logout(self) -> None:
        koo_session = self._get_koo_session()
        koo_session.logout()
        self._current = Session()

    @property
    def is_logged_in(self) -> bool:
        return self._current.is_logged_in

    @property
    def current_session(self) -> Session:
        return self._current

    # ------------------------------------------------------------------
    # Data access (thin wrappers around RpcProxy.__call__)
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
        args: List[Any] = [domain or [], offset, limit or False, order or False]
        return self._proxy(model).search(*args, context=context or {})

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        args: List[Any] = [ids]
        if fields is not None:
            args.append(fields)
        return self._proxy(model).read(*args, context=context or {})

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> bool:
        return self._proxy(model).write(ids, values, context=context or {})

    def create(
        self,
        model: str,
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> int:
        return self._proxy(model).create(values, context=context or {})

    def unlink(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict] = None,
    ) -> bool:
        return self._proxy(model).unlink(ids, context=context or {})

    def execute(
        self,
        model: str,
        method: str,
        *args: Any,
        context: Optional[Dict] = None,
    ) -> Any:
        return self._proxy(model).__getattr__(method)(*args, context=context or {})

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
        return self._proxy(model).fields_get(*args, context=context or {})

    def fields_view_get(
        self,
        model: str,
        view_id: Optional[int] = None,
        view_type: str = "form",
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        return self._proxy(model).fields_view_get(
            view_id or False, view_type, context=context or {}
        )
