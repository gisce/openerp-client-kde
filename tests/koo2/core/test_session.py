"""
Tests for koo2.core.domain.session

These tests are pure-Python and require no Qt or network.
"""
import pytest

from koo2.core.domain.session import Session, SessionState


class TestSessionInitialState:
    def test_default_session_is_disconnected(self):
        s = Session()
        assert s.state == SessionState.DISCONNECTED

    def test_default_session_is_not_logged_in(self):
        s = Session()
        assert not s.is_logged_in

    def test_default_display_name(self):
        s = Session()
        assert "(not logged in)" in s.display_name


class TestSessionWithCredentials:
    def test_with_credentials_creates_new_session(self):
        s = Session()
        s2 = s.with_credentials("http://localhost", "mydb", "admin")
        assert s2.url == "http://localhost"
        assert s2.database == "mydb"
        assert s2.username == "admin"
        assert s2 is not s

    def test_with_credentials_state_is_disconnected(self):
        s = Session()
        s2 = s.with_credentials("http://localhost", "mydb", "admin")
        assert s2.state == SessionState.DISCONNECTED

    def test_with_credentials_uid_is_none(self):
        s = Session()
        s2 = s.with_credentials("http://localhost", "mydb", "admin")
        assert s2.uid is None


class TestSessionAuthenticated:
    def test_authenticated_returns_new_session(self):
        s = Session(url="http://localhost", database="mydb", username="admin")
        s2 = s.authenticated(uid=1)
        assert s2 is not s

    def test_authenticated_state_is_logged_in(self):
        s = Session(url="http://localhost", database="mydb", username="admin")
        s2 = s.authenticated(uid=1)
        assert s2.state == SessionState.LOGGED_IN
        assert s2.is_logged_in

    def test_authenticated_uid_is_set(self):
        s = Session(url="http://localhost", database="mydb", username="admin")
        s2 = s.authenticated(uid=7)
        assert s2.uid == 7

    def test_authenticated_display_name(self):
        s = Session(url="http://localhost", database="mydb", username="admin")
        s2 = s.authenticated(uid=1)
        assert "admin" in s2.display_name
        assert "mydb" in s2.display_name

    def test_authenticated_preserves_context(self):
        s = Session(context={"lang": "ca_ES"})
        s2 = s.authenticated(uid=1, context={"lang": "en_US"})
        assert s2.context["lang"] == "en_US"

    def test_authenticated_copies_context_if_none_given(self):
        s = Session(context={"lang": "ca_ES"})
        s2 = s.authenticated(uid=1)
        assert s2.context["lang"] == "ca_ES"


class TestSessionFailed:
    def test_failed_state_is_error(self):
        s = Session(url="http://localhost", database="mydb", username="admin")
        s2 = s.failed()
        assert s2.state == SessionState.ERROR

    def test_failed_invalid_credentials_state(self):
        s = Session(url="http://localhost", database="mydb", username="admin")
        s2 = s.failed(invalid_credentials=True)
        assert s2.state == SessionState.INVALID_CREDENTIALS

    def test_failed_uid_is_none(self):
        s = Session()
        s2 = s.failed()
        assert s2.uid is None

    def test_failed_returns_new_session(self):
        s = Session()
        s2 = s.failed()
        assert s2 is not s
