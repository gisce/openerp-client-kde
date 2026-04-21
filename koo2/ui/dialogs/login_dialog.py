"""
LoginDialog – Material Design 3 login window.

Two-tab design:

* **Simple** (default) — URL + username + password.
  Authenticates via REST API token (no database required).
  Emits :attr:`login_simple_requested`.

* **Advanced** — URL + database + protocol + username + password.
  Authenticates via XML-RPC / erppeek (full manual config).
  Emits :attr:`login_requested` (unchanged signal for back-compat).
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette
from koo2.ui.widgets.button import ButtonVariant, MaterialButton
from koo2.ui.widgets.card import CardElevation, MaterialCard
from koo2.ui.widgets.text_field import MaterialTextField


class LoginDialog(QDialog):
    """MD3 login dialog with Simple and Advanced tabs.

    Signals
    -------
    login_simple_requested(url, username, password)
        Emitted from the *Simple* tab — REST API token login.

    login_requested(url, database, username, password)
        Emitted from the *Advanced* tab — XML-RPC / erppeek login.
    """

    login_simple_requested = Signal(str, str, str)
    login_requested = Signal(str, str, str, str)

    def __init__(
        self,
        palette: Palette = DEFAULT_LIGHT,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._palette = palette
        self.setWindowTitle("OpenERP – Connect")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._build_ui()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_error(self, message: str) -> None:
        """Display an error message below the tabs."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def clear_error(self) -> None:
        self._error_label.setVisible(False)

    def simple_credentials(self) -> tuple[str, str, str]:
        """Return ``(url, username, password)`` from the Simple tab."""
        return (
            self._s_url_field.text.strip(),
            self._s_user_field.text.strip(),
            self._s_pass_field.text.strip(),
        )

    def credentials(self) -> tuple[str, str, str, str]:
        """Return ``(url, database, username, password)`` from the Advanced tab."""
        return (
            self._a_url_field.text.strip(),
            self._a_db_field.text.strip(),
            self._a_user_field.text.strip(),
            self._a_pass_field.text.strip(),
        )

    @property
    def is_simple_mode(self) -> bool:
        """True when the Simple tab is active."""
        return self._tabs.currentIndex() == 0

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(0)

        card = MaterialCard(elevation=CardElevation.LEVEL2, palette=self._palette)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        layout = card.body_layout
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # Title
        title = QLabel("Connect to OpenERP")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.Weight.Medium)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {self._palette.on_surface};")
        layout.addWidget(title)
        layout.addSpacing(8)

        # --- Tabs ---------------------------------------------------------
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            f"QTabBar::tab {{ min-width: 140px; padding: 6px 16px; }}"
        )
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._build_simple_tab(), "🔑  Simple")
        self._tabs.addTab(self._build_advanced_tab(), "⚙  Advanced")

        # Error label
        self._error_label = QLabel()
        self._error_label.setStyleSheet(
            f"color: {self._palette.error.color}; font-size: 13px;"
        )
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        layout.addSpacing(4)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        cancel_btn = MaterialButton("Cancel", variant=ButtonVariant.TEXT)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        connect_btn = MaterialButton("Connect", variant=ButtonVariant.FILLED)
        connect_btn.setDefault(True)
        connect_btn.clicked.connect(self._on_connect)
        btn_row.addWidget(connect_btn)
        layout.addLayout(btn_row)

    def _build_simple_tab(self) -> QWidget:
        """Simple tab: URL + user + password (REST API)."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 16, 0, 8)
        layout.setSpacing(12)

        hint = QLabel(
            "Connect with your username and password.\n"
            "No database or port configuration needed."
        )
        hint.setStyleSheet(
            f"color: {self._palette.on_surface_variant}; font-size: 13px;"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._s_url_field = MaterialTextField(
            label="Server URL", palette=self._palette
        )
        self._s_url_field.setText("https://erp.example.com")
        layout.addWidget(self._s_url_field)

        self._s_user_field = MaterialTextField(
            label="Username", palette=self._palette
        )
        layout.addWidget(self._s_user_field)

        self._s_pass_field = MaterialTextField(
            label="Password", palette=self._palette
        )
        self._s_pass_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._s_pass_field)

        return w

    def _build_advanced_tab(self) -> QWidget:
        """Advanced tab: full XML-RPC config (URL + database + user + password)."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 16, 0, 8)
        layout.setSpacing(12)

        hint = QLabel(
            "Manual connection to a specific host, port and database."
        )
        hint.setStyleSheet(
            f"color: {self._palette.on_surface_variant}; font-size: 13px;"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._a_url_field = MaterialTextField(
            label="Server URL  (e.g. http://localhost:8069)",
            palette=self._palette,
        )
        self._a_url_field.setText("http://localhost:8069")
        layout.addWidget(self._a_url_field)

        self._a_db_field = MaterialTextField(
            label="Database", palette=self._palette
        )
        layout.addWidget(self._a_db_field)

        self._a_user_field = MaterialTextField(
            label="Username", palette=self._palette
        )
        layout.addWidget(self._a_user_field)

        self._a_pass_field = MaterialTextField(
            label="Password", palette=self._palette
        )
        self._a_pass_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._a_pass_field)

        return w

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        self.clear_error()
        if self.is_simple_mode:
            url, user, password = self.simple_credentials()
            if not url or not user:
                self.set_error("Please enter a server URL and username.")
                return
            self.login_simple_requested.emit(url, user, password)
        else:
            url, db, user, password = self.credentials()
            if not url or not db or not user:
                self.set_error("Please fill in all required fields.")
                return
            self.login_requested.emit(url, db, user, password)
