"""
LoginDialog – Material Design 3 login window.

Presents server URL, database, username and password fields inside a
centred card.  It emits :attr:`login_requested` with the four credentials
when the user clicks *Connect*; the caller is responsible for the actual
RPC call so that the dialog remains testable without a network connection.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette
from koo2.ui.widgets.button import ButtonVariant, MaterialButton
from koo2.ui.widgets.card import CardElevation, MaterialCard
from koo2.ui.widgets.text_field import MaterialTextField


class LoginDialog(QDialog):
    """MD3 login dialog.

    Signals
    -------
    login_requested(url, database, username, password)
        Emitted when the user clicks *Connect*.
    """

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
        self.setMinimumWidth(400)
        self._build_ui()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_error(self, message: str) -> None:
        """Display an error message below the form fields."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def clear_error(self) -> None:
        self._error_label.setVisible(False)

    def credentials(self) -> tuple[str, str, str, str]:
        """Return ``(url, database, username, password)``."""
        return (
            self._url_field.text.strip(),
            self._db_field.text.strip(),
            self._user_field.text.strip(),
            self._pass_field.text.strip(),
        )

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(0)

        # --- Centred card -------------------------------------------------
        card = MaterialCard(
            elevation=CardElevation.LEVEL2,
            palette=self._palette,
        )
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

        # Subtitle
        subtitle = QLabel("Enter your server connection details")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            f"color: {self._palette.on_surface_variant}; font-size: 14px;"
        )
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        # Fields
        self._url_field = MaterialTextField(label="Server URL", palette=self._palette)
        self._url_field.setText("http://localhost:8069")
        layout.addWidget(self._url_field)

        self._db_field = MaterialTextField(label="Database", palette=self._palette)
        layout.addWidget(self._db_field)

        self._user_field = MaterialTextField(label="Username", palette=self._palette)
        layout.addWidget(self._user_field)

        self._pass_field = MaterialTextField(label="Password", palette=self._palette)
        self._pass_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._pass_field)

        # Error label (hidden until set_error() is called)
        self._error_label = QLabel()
        self._error_label.setStyleSheet(
            f"color: {self._palette.error.color}; font-size: 13px;"
        )
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        layout.addSpacing(8)

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

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_connect(self) -> None:
        url, db, user, password = self.credentials()
        if not url or not db or not user:
            self.set_error("Please fill in all required fields.")
            return
        self.clear_error()
        self.login_requested.emit(url, db, user, password)
