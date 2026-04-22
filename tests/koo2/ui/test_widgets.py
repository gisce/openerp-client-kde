"""
Tests for koo2.ui.widgets (MaterialButton, MaterialTextField, MaterialCard)

Uses QT_QPA_PLATFORM=offscreen (set in conftest.py) so no display is required.
Skipped automatically when PySide6 is not installed.
"""
import os
import sys
import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication for widget tests."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestMaterialButton:
    def test_filled_variant_default(self, qapp):
        from koo2.ui.widgets.button import MaterialButton, ButtonVariant
        btn = MaterialButton("OK")
        assert btn.variant == ButtonVariant.FILLED

    def test_text_matches(self, qapp):
        from koo2.ui.widgets.button import MaterialButton
        btn = MaterialButton("Save")
        assert btn.text() == "Save"

    def test_outlined_variant(self, qapp):
        from koo2.ui.widgets.button import MaterialButton, ButtonVariant
        btn = MaterialButton("Cancel", variant=ButtonVariant.OUTLINED)
        assert btn.variant == ButtonVariant.OUTLINED

    def test_text_variant(self, qapp):
        from koo2.ui.widgets.button import MaterialButton, ButtonVariant
        btn = MaterialButton("Skip", variant=ButtonVariant.TEXT)
        assert btn.variant == ButtonVariant.TEXT

    def test_change_variant(self, qapp):
        from koo2.ui.widgets.button import MaterialButton, ButtonVariant
        btn = MaterialButton("X")
        btn.variant = ButtonVariant.OUTLINED
        assert btn.variant == ButtonVariant.OUTLINED

    def test_disabled_state(self, qapp):
        from koo2.ui.widgets.button import MaterialButton
        btn = MaterialButton("X")
        btn.setEnabled(False)
        assert not btn.isEnabled()


class TestMaterialTextField:
    def test_initial_text_empty(self, qapp):
        from koo2.ui.widgets.text_field import MaterialTextField
        tf = MaterialTextField(label="Name")
        assert tf.text == ""

    def test_set_text(self, qapp):
        from koo2.ui.widgets.text_field import MaterialTextField
        tf = MaterialTextField()
        tf.setText("Hello")
        assert tf.text == "Hello"

    def test_set_read_only(self, qapp):
        from koo2.ui.widgets.text_field import MaterialTextField
        tf = MaterialTextField()
        tf.setReadOnly(True)
        assert tf._edit.isReadOnly()

    def test_echo_mode_password(self, qapp):
        from koo2.ui.widgets.text_field import MaterialTextField
        from PySide6.QtWidgets import QLineEdit
        tf = MaterialTextField()
        tf.setEchoMode(QLineEdit.EchoMode.Password)
        assert tf._edit.echoMode() == QLineEdit.EchoMode.Password

    def test_text_changed_signal(self, qapp):
        from koo2.ui.widgets.text_field import MaterialTextField
        tf = MaterialTextField()
        received = []
        tf.textChanged.connect(received.append)
        tf.setText("Test")
        assert "Test" in received


class TestMaterialCard:
    def test_card_created(self, qapp):
        from koo2.ui.widgets.card import MaterialCard
        card = MaterialCard()
        assert card is not None

    def test_card_has_body_layout(self, qapp):
        from koo2.ui.widgets.card import MaterialCard
        card = MaterialCard()
        assert card.body_layout is not None

    def test_card_elevation_none(self, qapp):
        from koo2.ui.widgets.card import MaterialCard, CardElevation
        card = MaterialCard(elevation=CardElevation.NONE)
        assert card.graphicsEffect() is None

    def test_card_elevation_level1(self, qapp):
        from koo2.ui.widgets.card import MaterialCard, CardElevation
        card = MaterialCard(elevation=CardElevation.LEVEL1)
        assert card.graphicsEffect() is not None

    def test_card_elevation_level2(self, qapp):
        from koo2.ui.widgets.card import MaterialCard, CardElevation
        card = MaterialCard(elevation=CardElevation.LEVEL2)
        assert card.graphicsEffect() is not None

    def test_set_elevation(self, qapp):
        from koo2.ui.widgets.card import MaterialCard, CardElevation
        card = MaterialCard(elevation=CardElevation.LEVEL2)
        card.set_elevation(CardElevation.NONE)
        assert card.graphicsEffect() is None
