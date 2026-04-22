"""Tests for koo2.infrastructure.rpc.erppeek_client — ErppeekRpcClient.

All tests use mocks so no network or server is required.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from koo2.core.domain.session import SessionState
from koo2.infrastructure.rpc.erppeek_client import (
    ErppeekRpcClient,
    RpcAuthError,
    RpcError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(uid: int = 1, context: dict | None = None) -> MagicMock:
    """Return a mock erppeek.Client."""
    mock = MagicMock()
    mock.uid = uid
    mock.context = context or {"lang": "ca_ES"}
    return mock


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestErppeekLogin:
    def test_successful_login(self):
        mock_client = _make_client(uid=2)
        with patch("erppeek.Client", return_value=mock_client) as mock_cls:
            client = ErppeekRpcClient()
            result = client.login("http://server", "testdb", "admin", "secret")

        mock_cls.assert_called_once_with(
            "http://server", db="testdb", user="admin", password="secret"
        )
        assert result is True
        assert client.is_logged_in
        assert client.current_session.uid == 2
        assert client.current_session.database == "testdb"
        assert client.current_session.state == SessionState.LOGGED_IN

    def test_auth_error_raises_rpc_auth_error(self):
        import erppeek
        with patch("erppeek.Client", side_effect=erppeek.Error("Invalid credentials")):
            client = ErppeekRpcClient()
            with pytest.raises(RpcAuthError):
                client.login("http://server", "db", "bad", "bad")
        assert not client.is_logged_in

    def test_generic_error_raises_rpc_error(self):
        import erppeek
        with patch("erppeek.Client", side_effect=erppeek.Error("Connection refused")):
            client = ErppeekRpcClient()
            with pytest.raises(RpcError):
                client.login("http://server", "db", "u", "p")

    def test_network_error_raises_rpc_error(self):
        with patch("erppeek.Client", side_effect=ConnectionError("unreachable")):
            client = ErppeekRpcClient()
            with pytest.raises(RpcError):
                client.login("http://server", "db", "u", "p")

    def test_context_stored_in_session(self):
        mock_client = _make_client(context={"lang": "es_ES", "tz": "Europe/Madrid"})
        with patch("erppeek.Client", return_value=mock_client):
            client = ErppeekRpcClient()
            client.login("http://s", "db", "u", "p")
        assert client.current_session.context["lang"] == "es_ES"


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestErppeekLogout:
    def test_logout_clears_session(self):
        mock_client = _make_client()
        with patch("erppeek.Client", return_value=mock_client):
            client = ErppeekRpcClient()
            client.login("http://s", "db", "u", "p")
        assert client.is_logged_in
        client.logout()
        assert not client.is_logged_in
        assert client.current_session.uid is None

    def test_not_logged_in_by_default(self):
        client = ErppeekRpcClient()
        assert not client.is_logged_in


# ---------------------------------------------------------------------------
# Data access — requires logged-in client
# ---------------------------------------------------------------------------

def _logged_in_client() -> ErppeekRpcClient:
    mock_ep = _make_client()
    with patch("erppeek.Client", return_value=mock_ep):
        c = ErppeekRpcClient()
        c.login("http://s", "db", "u", "p")
    return c


class TestErppeekSearch:
    def test_search_calls_execute(self):
        c = _logged_in_client()
        c._client.execute.return_value = [1, 2, 3]
        ids = c.search("res.partner", [("is_company", "=", True)])
        c._client.execute.assert_called_once()
        call_args = c._client.execute.call_args
        assert call_args[0][0] == "res.partner"
        assert call_args[0][1] == "search"
        assert ids == [1, 2, 3]

    def test_search_empty_domain(self):
        c = _logged_in_client()
        c._client.execute.return_value = []
        result = c.search("res.partner")
        assert result == []

    def test_not_logged_raises(self):
        c = ErppeekRpcClient()
        with pytest.raises(RpcError, match="Not logged in"):
            c.search("res.partner")


class TestErppeekRead:
    def test_read_with_fields(self):
        c = _logged_in_client()
        c._client.execute.return_value = [{"id": 1, "name": "ACME"}]
        result = c.read("res.partner", [1], ["name"])
        c._client.execute.assert_called_once()
        assert result[0]["name"] == "ACME"

    def test_read_without_fields(self):
        c = _logged_in_client()
        c._client.execute.return_value = [{"id": 1, "name": "X"}]
        c.read("res.partner", [1])
        args = c._client.execute.call_args[0]
        # fields not passed as positional arg
        assert args == ("res.partner", "read", [1])


class TestErppeekWrite:
    def test_write_returns_true(self):
        c = _logged_in_client()
        c._client.execute.return_value = True
        assert c.write("res.partner", [1], {"name": "New"}) is True

    def test_write_calls_correct_method(self):
        c = _logged_in_client()
        c._client.execute.return_value = True
        c.write("res.partner", [1], {"name": "X"})
        call = c._client.execute.call_args[0]
        assert call[1] == "write"


class TestErppeekCreate:
    def test_create_returns_id(self):
        c = _logged_in_client()
        c._client.execute.return_value = 42
        new_id = c.create("res.partner", {"name": "New"})
        assert new_id == 42


class TestErppeekFieldsViewGet:
    def test_fields_view_get_call_structure(self):
        c = _logged_in_client()
        c._client.execute.return_value = {"arch": "<form/>", "fields": {}}
        result = c.fields_view_get("res.partner", view_type="form")
        call = c._client.execute.call_args[0]
        assert call[0] == "res.partner"
        assert call[1] == "fields_view_get"
        assert call[2] is False   # view_id=None → False
        assert call[3] == "form"
        assert result["arch"] == "<form/>"

    def test_fields_view_get_with_view_id(self):
        c = _logged_in_client()
        c._client.execute.return_value = {}
        c.fields_view_get("res.partner", view_id=99)
        call = c._client.execute.call_args[0]
        assert call[2] == 99
