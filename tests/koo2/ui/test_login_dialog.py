"""
Tests for koo2.ui.dialogs.login_dialog

Uses QT_QPA_PLATFORM=offscreen.
Skipped automatically when PySide6 is not installed.
"""
import sys
import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestLoginDialog:
    def test_dialog_created(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        assert dialog is not None

    def test_default_url_is_localhost(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        assert "localhost" in dialog._url_field.text

    def test_credentials_returns_tuple(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        result = dialog.credentials()
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_error_shown_on_empty_fields(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        # Clear all fields
        dialog._url_field.setText("")
        dialog._db_field.setText("")
        dialog._user_field.setText("")
        dialog._pass_field.setText("")
        dialog._on_connect()
        assert dialog._error_label.isVisible()

    def test_set_error_shows_message(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        dialog.set_error("Test error")
        assert dialog._error_label.isVisible()
        assert "Test error" in dialog._error_label.text()

    def test_clear_error_hides_label(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        dialog.set_error("Error")
        dialog.clear_error()
        assert not dialog._error_label.isVisible()

    def test_login_requested_signal_emitted(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        received = []
        dialog.login_requested.connect(lambda *args: received.append(args))
        dialog._url_field.setText("http://localhost")
        dialog._db_field.setText("mydb")
        dialog._user_field.setText("admin")
        dialog._pass_field.setText("admin")
        dialog._on_connect()
        assert len(received) == 1
        url, db, user, pwd = received[0]
        assert url == "http://localhost"
        assert db == "mydb"
        assert user == "admin"
        assert pwd == "admin"

    def test_window_title(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        assert "OpenERP" in dialog.windowTitle()
