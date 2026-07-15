"""
koo2/infrastructure/rpc/restapi_client.py — RestApiRpcClient

Token-based REST API transport using py-gisce-client (pygisceclient).

Login flow (identical to webgis):
  GET backend_url/token  (Basic auth: user:password)
  → JWT token
  → RestApiClient(backend_url, token=token)

Advantages over erppeek/XML-RPC:
  - User only needs URL + credentials (no host/port/database)
  - Same transport used by webclient and webgis
  - JSON over HTTP/HTTPS — firewall-friendly
  - Token refresh without re-login
"""
from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional

import requests

from koo2.core.domain.session import Session, SessionState


class RpcError(Exception):
    """Raised on server errors."""


class RpcAuthError(RpcError):
    """Raised on invalid credentials."""


class RestApiRpcClient:
    """IRpcClient implementation backed by py-gisce-client RestApiClient.

    The ``gisce`` package is imported lazily so tests can patch sys.modules.
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None   # gisce.RestApiClient
        self._token: Optional[str] = None
        self._backend_url: Optional[str] = None
        self._current: Session = Session()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, url: str, username: str, password: str) -> bool:
        """Obtain a JWT token from ``url/token`` and build a RestApiClient.

        Raises :exc:`RpcAuthError` for 401 / bad credentials.
        Raises :exc:`RpcError` for other failures.
        """
        token_url = url.rstrip("/") + "/token"
        try:
            resp = requests.get(token_url, auth=(username, password), timeout=15)
        except requests.exceptions.ConnectionError as exc:
            raise RpcError(f"Cannot connect to {url}: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise RpcError(f"Timeout connecting to {url}") from exc

        if resp.status_code == 401:
            self._current = self._current.failed(invalid_credentials=True)
            raise RpcAuthError("Invalid username or password")
        if not resp.ok:
            raise RpcError(f"Token endpoint returned {resp.status_code}")

        token = resp.json().get("token")
        if not token:
            raise RpcError("Server returned no token")

        uid = self._uid_from_token(token)

        from gisce import RestApiClient  # lazy import
        self._client = RestApiClient(url.rstrip("/"), token=token)
        self._token = token
        self._backend_url = url.rstrip("/")

        self._current = Session(
            url=url,
            database=None,   # REST API hides the DB name
            username=username,
            uid=uid,
            state=SessionState.LOGGED_IN,
        )
        return True

    def logout(self) -> None:
        self._client = None
        self._token = None
        self._current = Session()

    @property
    def is_logged_in(self) -> bool:
        return self._current.is_logged_in

    @property
    def current_session(self) -> Session:
        return self._current

    @property
    def token(self) -> Optional[str]:
        return self._token

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _uid_from_token(token: str) -> Optional[int]:
        """Decode the UID from the JWT payload (no signature validation)."""
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))
            return int(payload.get("uid", 0)) or None
        except Exception:
            return None

    def _require_client(self) -> Any:
        if self._client is None:
            raise RpcError("Not logged in")
        return self._client

    def _model(self, model: str) -> Any:
        return self._require_client().model(model)

    # ------------------------------------------------------------------
    # Data access (same interface as ErppeekRpcClient)
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
        m = self._model(model)
        kwargs: Dict[str, Any] = {}
        if offset:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        if context:
            kwargs["context"] = context
        return m.search(domain or [], **kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        m = self._model(model)
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context
        if fields is not None:
            return m.read(ids, fields, **kwargs)
        return m.read(ids, **kwargs)

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> bool:
        m = self._model(model)
        kwargs = {"context": context} if context else {}
        return m.write(ids, values, **kwargs)

    def create(
        self,
        model: str,
        values: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> int:
        m = self._model(model)
        kwargs = {"context": context} if context else {}
        return m.create(values, **kwargs)

    def unlink(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict] = None,
    ) -> bool:
        m = self._model(model)
        kwargs = {"context": context} if context else {}
        return m.unlink(ids, **kwargs)

    def execute(
        self,
        model: str,
        method: str,
        *args: Any,
        context: Optional[Dict] = None,
    ) -> Any:
        m = self._model(model)
        fn = getattr(m, method)
        kwargs = {"context": context} if context else {}
        return fn(*args, **kwargs)

    def fields_get(
        self,
        model: str,
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Dict[str, Any]]:
        m = self._model(model)
        kwargs = {"context": context} if context else {}
        if fields is not None:
            return m.fields_get(fields, **kwargs)
        return m.fields_get(**kwargs)

    def fields_view_get(
        self,
        model: str,
        view_id: Optional[int] = None,
        view_type: str = "form",
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        m = self._model(model)
        kwargs = {"context": context} if context else {}
        return m.fields_view_get(view_id or False, view_type, **kwargs)
