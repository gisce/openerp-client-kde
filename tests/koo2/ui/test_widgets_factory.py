"""Tests for koo2/ui/widgets — WidgetFactory + field widgets + containers."""
from __future__ import annotations

import sys
import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qt_app():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


from koo2.core.view_parser.nodes import (
    ButtonNode,
    FieldNode,
    GroupNode,
    LabelNode,
    NotebookNode,
    SeparatorNode,
    ContainerNode,
)
from koo2.ui.widgets.factory import WidgetFactory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def factory(qt_app):
    return WidgetFactory()


# ---------------------------------------------------------------------------
# WidgetFactory — field types
# ---------------------------------------------------------------------------

class TestWidgetFactoryFields:
    def test_char_field(self, factory):
        from koo2.ui.widgets.fields import CharWidget
        node = FieldNode(name="x", field_type="char")
        w = factory.create_field(node)
        assert isinstance(w, CharWidget)

    def test_text_field(self, factory):
        from koo2.ui.widgets.fields import TextWidget
        node = FieldNode(name="x", field_type="text")
        assert isinstance(factory.create_field(node), TextWidget)

    def test_integer_field(self, factory):
        from koo2.ui.widgets.fields import IntegerWidget
        node = FieldNode(name="x", field_type="integer")
        assert isinstance(factory.create_field(node), IntegerWidget)

    def test_float_field(self, factory):
        from koo2.ui.widgets.fields import FloatWidget
        node = FieldNode(name="x", field_type="float")
        assert isinstance(factory.create_field(node), FloatWidget)

    def test_boolean_field(self, factory):
        from koo2.ui.widgets.fields import BooleanWidget
        node = FieldNode(name="x", field_type="boolean")
        assert isinstance(factory.create_field(node), BooleanWidget)

    def test_date_field(self, factory):
        from koo2.ui.widgets.fields import DateWidget
        node = FieldNode(name="x", field_type="date")
        assert isinstance(factory.create_field(node), DateWidget)

    def test_datetime_field(self, factory):
        from koo2.ui.widgets.fields import DateTimeWidget
        node = FieldNode(name="x", field_type="datetime")
        assert isinstance(factory.create_field(node), DateTimeWidget)

    def test_many2one_field(self, factory):
        from koo2.ui.widgets.fields import Many2oneWidget
        node = FieldNode(name="x", field_type="many2one")
        assert isinstance(factory.create_field(node), Many2oneWidget)

    def test_selection_field(self, factory):
        from koo2.ui.widgets.fields import SelectionWidget
        node = FieldNode(name="x", field_type="selection",
                         selection=[("a", "Alpha"), ("b", "Beta")])
        w = factory.create_field(node)
        assert isinstance(w, SelectionWidget)

    def test_one2many_returns_label(self, factory):
        from PySide6.QtWidgets import QLabel
        node = FieldNode(name="x", field_type="one2many")
        w = factory.create_field(node)
        assert isinstance(w, QLabel)

    def test_widget_hint_overrides_type(self, factory):
        """widget_hint='text' on a char field should produce TextWidget."""
        from koo2.ui.widgets.fields import TextWidget
        node = FieldNode(name="x", field_type="char", widget_hint="text")
        assert isinstance(factory.create_field(node), TextWidget)

    def test_readonly_propagated(self, factory):
        node = FieldNode(name="x", field_type="char", read_only=True)
        w = factory.create_field(node)
        assert w.read_only is True

    def test_register_custom_type(self, factory):
        from koo2.ui.widgets.fields import CharWidget
        factory.register("mytype", CharWidget)
        node = FieldNode(name="x", field_type="mytype")
        assert isinstance(factory.create_field(node), CharWidget)


# ---------------------------------------------------------------------------
# WidgetFactory — structural nodes
# ---------------------------------------------------------------------------

class TestWidgetFactoryStructural:
    def test_label_node(self, factory):
        from PySide6.QtWidgets import QLabel
        node = LabelNode(string="My Label")
        w = factory.create_label(node)
        assert isinstance(w, QLabel)
        assert w.text() == "My Label"

    def test_button_node(self, factory):
        from PySide6.QtWidgets import QPushButton
        node = ButtonNode(name="act", string="Confirm")
        w = factory.create_button(node)
        assert isinstance(w, QPushButton)
        assert w.text() == "Confirm"

    def test_group_node(self, factory):
        from koo2.ui.widgets.containers import GroupWidget
        node = GroupNode(string="Details", container=ContainerNode(columns=2))
        w = factory.create_group(node)
        assert isinstance(w, GroupWidget)
        assert w.title() == "Details"

    def test_notebook_node(self, factory):
        from koo2.ui.widgets.containers import NotebookWidget
        node = NotebookNode()
        w = factory.create_notebook(node)
        assert isinstance(w, NotebookWidget)


# ---------------------------------------------------------------------------
# Field widget values
# ---------------------------------------------------------------------------

class TestCharWidgetValues:
    def test_set_get(self, qt_app):
        from koo2.ui.widgets.fields import CharWidget
        w = CharWidget()
        w.set_value("hello")
        assert w.get_value() == "hello"

    def test_none_value(self, qt_app):
        from koo2.ui.widgets.fields import CharWidget
        w = CharWidget()
        w.set_value(None)
        assert w.get_value() == ""

    def test_read_only(self, qt_app):
        from koo2.ui.widgets.fields import CharWidget
        w = CharWidget()
        w.set_read_only(True)
        assert w.read_only is True


class TestIntegerWidgetValues:
    def test_set_get(self, qt_app):
        from koo2.ui.widgets.fields import IntegerWidget
        w = IntegerWidget()
        w.set_value(42)
        assert w.get_value() == 42

    def test_invalid_value(self, qt_app):
        from koo2.ui.widgets.fields import IntegerWidget
        w = IntegerWidget()
        w.set_value("bad")
        assert w.get_value() == 0


class TestBooleanWidgetValues:
    def test_true(self, qt_app):
        from koo2.ui.widgets.fields import BooleanWidget
        w = BooleanWidget()
        w.set_value(True)
        assert w.get_value() is True

    def test_false(self, qt_app):
        from koo2.ui.widgets.fields import BooleanWidget
        w = BooleanWidget()
        w.set_value(False)
        assert w.get_value() is False


class TestSelectionWidgetValues:
    def test_set_get(self, qt_app):
        from koo2.ui.widgets.fields import SelectionWidget
        w = SelectionWidget(selection=[("a", "Alpha"), ("b", "Beta")])
        w.set_value("b")
        assert w.get_value() == "b"

    def test_unknown_value(self, qt_app):
        from koo2.ui.widgets.fields import SelectionWidget
        w = SelectionWidget(selection=[("a", "Alpha")])
        w.set_value("z")
        assert w.get_value() == "a"  # stays at first item


class TestMany2oneWidgetValues:
    def test_list_value(self, qt_app):
        from koo2.ui.widgets.fields import Many2oneWidget
        w = Many2oneWidget()
        w.set_value([5, "ACME Corp"])
        assert w.get_value() == [5, "ACME Corp"]

    def test_none_value(self, qt_app):
        from koo2.ui.widgets.fields import Many2oneWidget
        w = Many2oneWidget()
        w.set_value(None)
        assert w.get_value() is None


# ---------------------------------------------------------------------------
# Container widgets
# ---------------------------------------------------------------------------

class TestFormGrid:
    def test_add_widgets_advances_columns(self, qt_app):
        from PySide6.QtWidgets import QLabel
        from koo2.ui.widgets.containers import FormGrid
        grid = FormGrid(columns=2)
        lbl1, lbl2 = QLabel("a"), QLabel("b")
        grid.add_widget(lbl1, colspan=1)
        grid.add_widget(lbl2, colspan=1)
        # Both fit in row 0
        assert grid._current_row == 0

    def test_overflow_wraps_row(self, qt_app):
        from PySide6.QtWidgets import QLabel
        from koo2.ui.widgets.containers import FormGrid
        grid = FormGrid(columns=2)
        for _ in range(3):
            grid.add_widget(QLabel("x"), colspan=1)
        # Third widget starts row 1
        assert grid._current_row == 1

    def test_new_row(self, qt_app):
        from PySide6.QtWidgets import QLabel
        from koo2.ui.widgets.containers import FormGrid
        grid = FormGrid(columns=4)
        grid.add_widget(QLabel("x"), colspan=1)
        grid.new_row()
        assert grid._current_row == 1
        assert grid._current_col == 0


class TestGroupWidget:
    def test_title(self, qt_app):
        from koo2.ui.widgets.containers import GroupWidget
        g = GroupWidget(title="My Group", columns=2)
        assert g.title() == "My Group"

    def test_inner_grid_accessible(self, qt_app):
        from koo2.ui.widgets.containers import GroupWidget, FormGrid
        g = GroupWidget(columns=2)
        assert isinstance(g.inner_grid, FormGrid)


class TestNotebookWidget:
    def test_add_page(self, qt_app):
        from koo2.ui.widgets.containers import NotebookWidget, FormGrid
        nb = NotebookWidget()
        grid = nb.add_page("General")
        assert isinstance(grid, FormGrid)
        assert nb.count() == 1
        assert nb.tabText(0) == "General"
