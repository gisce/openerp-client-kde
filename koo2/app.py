"""
koo2.app – Application bootstrap.

Creates the QApplication, applies the Material Design stylesheet, and
opens the LoginDialog.  On successful authentication it instantiates the
main window (to be implemented in a future phase).

Usage::

    python -m koo2.app
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient, RpcAuthError, RpcError
from koo2.ui.dialogs.login_dialog import LoginDialog
from koo2.ui.theme.palette import DEFAULT_LIGHT
from koo2.ui.theme.stylesheet import apply_to_app


def _make_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("koo2")
    app.setOrganizationName("GISCE-TI")
    apply_to_app(app, DEFAULT_LIGHT)
    return app


def run() -> int:
    """Entry point; returns the process exit code."""
    app = _make_app()
    rpc_client = OpenErpRpcClient()

    dialog = LoginDialog(palette=DEFAULT_LIGHT)

    def _do_login(url: str, db: str, user: str, password: str) -> None:
        try:
            rpc_client.login(url, db, user, password)
            dialog.accept()
            # TODO: open MainWindow once it is implemented
            QMessageBox.information(
                None,
                "Connected",
                f"Logged in as {user}@{db}",
            )
        except RpcAuthError:
            dialog.set_error("Invalid username or password.")
        except RpcError as exc:
            dialog.set_error(f"Connection error: {exc}")

    dialog.login_requested.connect(_do_login)
    dialog.exec()

    return 0


if __name__ == "__main__":
    sys.exit(run())
