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

    def test_simple_tab_is_default(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        assert dialog.is_simple_mode
        assert dialog._tabs.currentIndex() == 0

    def test_two_tabs_exist(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        assert dialog._tabs.count() == 2

    def test_default_url_simple_tab(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        url, user, pwd = dialog.simple_credentials()
        assert "example.com" in url or url  # has some default

    def test_simple_credentials_returns_3_tuple(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        result = dialog.simple_credentials()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_credentials_returns_4_tuple(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        result = dialog.credentials()
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_simple_mode_error_on_empty_url(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        dialog._s_url_field.setText("")
        dialog._s_user_field.setText("")
        dialog._on_connect()
        assert not dialog._error_label.isHidden()

    def test_advanced_mode_error_on_empty_fields(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        dialog._tabs.setCurrentIndex(1)
        dialog._a_url_field.setText("")
        dialog._a_db_field.setText("")
        dialog._a_user_field.setText("")
        dialog._on_connect()
        assert not dialog._error_label.isHidden()

    def test_set_error_shows_message(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        dialog.set_error("Test error")
        assert not dialog._error_label.isHidden()
        assert "Test error" in dialog._error_label.text()

    def test_clear_error_hides_label(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        dialog.set_error("Error")
        dialog.clear_error()
        assert not dialog._error_label.isVisible()

    def test_simple_login_signal_emitted(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        received = []
        dialog.login_simple_requested.connect(lambda *args: received.append(args))
        dialog._s_url_field.setText("https://erp.example.com")
        dialog._s_user_field.setText("admin")
        dialog._s_pass_field.setText("secret")
        dialog._on_connect()
        assert len(received) == 1
        url, user, pwd = received[0]
        assert url == "https://erp.example.com"
        assert user == "admin"
        assert pwd == "secret"

    def test_advanced_login_signal_emitted(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        received = []
        dialog.login_requested.connect(lambda *args: received.append(args))
        dialog._tabs.setCurrentIndex(1)  # Switch to Advanced
        dialog._a_url_field.setText("http://localhost:8069")
        dialog._a_db_field.setText("mydb")
        dialog._a_user_field.setText("admin")
        dialog._a_pass_field.setText("admin")
        dialog._on_connect()
        assert len(received) == 1
        url, db, user, pwd = received[0]
        assert url == "http://localhost:8069"
        assert db == "mydb"
        assert user == "admin"

    def test_window_title(self, qapp):
        from koo2.ui.dialogs.login_dialog import LoginDialog
        dialog = LoginDialog()
        assert "OpenERP" in dialog.windowTitle()

