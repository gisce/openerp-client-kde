"""Tests for koo2.infrastructure.rpc.restapi_client — RestApiRpcClient."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock
import base64
import json

import pytest

from koo2.core.domain.session import SessionState
from koo2.infrastructure.rpc.restapi_client import (
    RestApiRpcClient,
    RpcAuthError,
    RpcError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(uid: int = 1) -> str:
    """Create a minimal JWT-like token with uid in payload."""
    payload = base64.b64encode(json.dumps({"uid": uid}).encode()).decode()
    return f"header.{payload}.sig"


def _mock_response(status_code: int = 200, json_data: dict | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = status_code < 400
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestRestApiLogin:
    def test_successful_login(self):
        token = _make_token(uid=5)
        resp = _mock_response(200, {"token": token})
        with patch("requests.get", return_value=resp), \
             patch("gisce.RestApiClient") as mock_cls:
            client = RestApiRpcClient()
            result = client.login("http://erp.example.com", "admin", "secret")

        assert result is True
        assert client.is_logged_in
        assert client.current_session.uid == 5
        assert client.current_session.state == SessionState.LOGGED_IN
        assert client.token == token
        mock_cls.assert_called_once_with("http://erp.example.com", token=token)

    def test_url_trailing_slash_stripped(self):
        token = _make_token()
        resp = _mock_response(200, {"token": token})
        with patch("requests.get", return_value=resp) as mock_get, \
             patch("gisce.RestApiClient"):
            RestApiRpcClient().login("http://erp.example.com/", "u", "p")
        assert mock_get.call_args[0][0] == "http://erp.example.com/token"

    def test_401_raises_rpc_auth_error(self):
        resp = _mock_response(status_code=401)
        with patch("requests.get", return_value=resp):
            client = RestApiRpcClient()
            with pytest.raises(RpcAuthError):
                client.login("http://server", "bad", "bad")
        assert not client.is_logged_in

    def test_non_401_error_raises_rpc_error(self):
        resp = _mock_response(status_code=500)
        with patch("requests.get", return_value=resp):
            with pytest.raises(RpcError):
                RestApiRpcClient().login("http://server", "u", "p")

    def test_connection_error_raises_rpc_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.ConnectionError("unreachable")):
            with pytest.raises(RpcError, match="Cannot connect"):
                RestApiRpcClient().login("http://bad", "u", "p")

    def test_timeout_raises_rpc_error(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.Timeout()):
            with pytest.raises(RpcError, match="Timeout"):
                RestApiRpcClient().login("http://slow", "u", "p")

    def test_missing_token_in_response_raises_rpc_error(self):
        resp = _mock_response(200, {})   # no 'token' key
        with patch("requests.get", return_value=resp):
            with pytest.raises(RpcError, match="no token"):
                RestApiRpcClient().login("http://server", "u", "p")


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestRestApiLogout:
    def test_logout_clears_session(self):
        token = _make_token()
        with patch("requests.get", return_value=_mock_response(200, {"token": token})), \
             patch("gisce.RestApiClient"):
            c = RestApiRpcClient()
            c.login("http://s", "u", "p")
        assert c.is_logged_in
        c.logout()
        assert not c.is_logged_in
        assert c.token is None

    def test_not_logged_in_by_default(self):
        assert not RestApiRpcClient().is_logged_in


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

def _logged_in_client() -> RestApiRpcClient:
    token = _make_token(uid=3)
    mock_gisce = MagicMock()
    with patch("requests.get", return_value=_mock_response(200, {"token": token})), \
         patch("gisce.RestApiClient", return_value=mock_gisce):
        c = RestApiRpcClient()
        c.login("http://s", "u", "p")
    return c


class TestRestApiSearch:
    def test_search_delegates_to_model(self):
        c = _logged_in_client()
        c._client.model.return_value.search.return_value = [1, 2]
        ids = c.search("res.partner", [("active", "=", True)])
        assert ids == [1, 2]
        c._client.model.assert_called_with("res.partner")

    def test_not_logged_raises(self):
        with pytest.raises(RpcError, match="Not logged in"):
            RestApiRpcClient().search("res.partner")


class TestRestApiRead:
    def test_read_with_fields(self):
        c = _logged_in_client()
        c._client.model.return_value.read.return_value = [{"id": 1, "name": "X"}]
        result = c.read("res.partner", [1], ["name"])
        assert result[0]["name"] == "X"

    def test_read_without_fields(self):
        c = _logged_in_client()
        c._client.model.return_value.read.return_value = []
        c.read("res.partner", [1])
        c._client.model.return_value.read.assert_called_once_with([1])


class TestRestApiCreate:
    def test_create_returns_id(self):
        c = _logged_in_client()
        c._client.model.return_value.create.return_value = 99
        assert c.create("res.partner", {"name": "New"}) == 99


class TestRestApiTokenDecoding:
    def test_uid_extracted_from_token(self):
        token = _make_token(uid=42)
        uid = RestApiRpcClient._uid_from_token(token)
        assert uid == 42

    def test_malformed_token_returns_none(self):
        assert RestApiRpcClient._uid_from_token("bad") is None
