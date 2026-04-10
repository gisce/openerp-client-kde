"""
Tests for koo2.infrastructure.rpc.openerp_client

These tests use sys.modules mocking to avoid needing PySide6 or a real
OpenERP server.  The KooSession constants are patched at module level
before any import of Koo.Rpc.Rpc occurs.
"""
import sys
import types
import pytest
from unittest.mock import MagicMock, patch

from koo2.core.domain.session import SessionState


# ---------------------------------------------------------------------------
# Module-level mock for Koo.Rpc (avoids PySide6 dependency in this env)
# ---------------------------------------------------------------------------
def _make_koo_rpc_mock():
    """Return a stub that satisfies all imports from Koo.Rpc.*."""
    mock_session_cls = MagicMock()
    mock_session_cls.LoggedIn = 1
    mock_session_cls.Exception = 2
    mock_session_cls.InvalidCredentials = 3

    mock_rpc_mod = types.ModuleType("Koo.Rpc.Rpc")
    mock_rpc_mod.Session = mock_session_cls

    mock_rpc_pkg = types.ModuleType("Koo.Rpc")
    mock_rpc_pkg.session = MagicMock()

    mock_koo = types.ModuleType("Koo")

    return mock_koo, mock_rpc_pkg, mock_rpc_mod, mock_session_cls


@pytest.fixture()
def koo_rpc_mocks():
    """
    Inject fake Koo.Rpc modules into sys.modules for the duration of a test.
    """
    mock_koo, mock_rpc_pkg, mock_rpc_mod, mock_session_cls = _make_koo_rpc_mock()

    modules_to_patch = {
        "Koo": mock_koo,
        "Koo.Rpc": mock_rpc_pkg,
        "Koo.Rpc.Rpc": mock_rpc_mod,
    }
    original = {k: sys.modules.get(k) for k in modules_to_patch}
    sys.modules.update(modules_to_patch)
    yield mock_rpc_pkg, mock_session_cls
    # Restore
    for k, v in original.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestOpenErpRpcClientLoginSuccess:
    def test_login_sets_logged_in_state(self, koo_rpc_mocks):
        from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient

        mock_rpc_pkg, mock_session_cls = koo_rpc_mocks
        mock_rpc_pkg.session.uid = 1
        mock_rpc_pkg.session.context = {"lang": "en_US"}
        mock_rpc_pkg.session.login.return_value = 1   # LoggedIn

        client = OpenErpRpcClient()
        client._session = mock_rpc_pkg.session

        result = client.login("http://localhost", "mydb", "admin", "admin")

        assert result is True
        assert client.is_logged_in

    def test_login_stores_uid(self, koo_rpc_mocks):
        from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient

        mock_rpc_pkg, mock_session_cls = koo_rpc_mocks
        mock_rpc_pkg.session.uid = 7
        mock_rpc_pkg.session.context = {}
        mock_rpc_pkg.session.login.return_value = 1

        client = OpenErpRpcClient()
        client._session = mock_rpc_pkg.session
        client.login("http://localhost", "mydb", "admin", "admin")

        assert client.current_session.uid == 7


class TestOpenErpRpcClientLoginFailure:
    def test_invalid_credentials_raises_auth_error(self, koo_rpc_mocks):
        from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient, RpcAuthError

        mock_rpc_pkg, mock_session_cls = koo_rpc_mocks
        mock_rpc_pkg.session.login.return_value = 3   # InvalidCredentials

        client = OpenErpRpcClient()
        client._session = mock_rpc_pkg.session

        with pytest.raises(RpcAuthError):
            client.login("http://localhost", "mydb", "admin", "wrong")

    def test_other_error_raises_rpc_error(self, koo_rpc_mocks):
        from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient, RpcError

        mock_rpc_pkg, mock_session_cls = koo_rpc_mocks
        mock_rpc_pkg.session.login.return_value = 2   # Exception

        client = OpenErpRpcClient()
        client._session = mock_rpc_pkg.session

        with pytest.raises(RpcError):
            client.login("http://localhost", "mydb", "admin", "wrong")

    def test_not_logged_in_by_default(self):
        from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient
        client = OpenErpRpcClient()
        assert not client.is_logged_in


class TestOpenErpRpcClientLogout:
    def test_logout_clears_session(self, koo_rpc_mocks):
        from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient

        mock_rpc_pkg, mock_session_cls = koo_rpc_mocks
        mock_rpc_pkg.session.uid = 1
        mock_rpc_pkg.session.context = {}
        mock_rpc_pkg.session.login.return_value = 1

        client = OpenErpRpcClient()
        client._session = mock_rpc_pkg.session
        client.login("http://localhost", "mydb", "admin", "admin")
        assert client.is_logged_in

        client.logout()
        assert not client.is_logged_in

