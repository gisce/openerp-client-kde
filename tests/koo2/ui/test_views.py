"""
Tests for koo2.ui.views.base_view and koo2.ui.views.form / tree.

Uses QT_QPA_PLATFORM=offscreen (set in conftest.py).
Skipped automatically when PySide6 is not installed.
"""
import sys
import pytest

pytest.importorskip("PySide6")

from koo2.core.domain.record import Record
from koo2.core.domain.view_definition import FieldDefinition, ViewDefinition


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def simple_view_definition():
    data = {
        "arch": "<form><field name='name'/><field name='email'/></form>",
        "fields": {
            "name": {"type": "char", "string": "Name"},
            "email": {"type": "char", "string": "Email"},
        },
    }
    return ViewDefinition.from_server("form", data, model="res.partner")


@pytest.fixture
def sample_record():
    return Record.from_server("res.partner", {"id": 1, "name": "ACME", "email": "acme@acme.com"})


# ---------------------------------------------------------------------------
# BaseView
# ---------------------------------------------------------------------------
class TestBaseView:
    def test_base_view_read_only_default(self, qapp):
        from koo2.ui.views.base_view import BaseView

        class ConcreteView(BaseView):
            def view_type(self): return "test"

        view = ConcreteView()
        assert not view.is_read_only()

    def test_base_view_set_read_only(self, qapp):
        from koo2.ui.views.base_view import BaseView

        class ConcreteView(BaseView):
            def view_type(self): return "test"

        view = ConcreteView()
        view.set_read_only(True)
        assert view.is_read_only()

    def test_base_view_selected_records_empty_by_default(self, qapp):
        from koo2.ui.views.base_view import BaseView

        class ConcreteView(BaseView):
            def view_type(self): return "test"

        view = ConcreteView()
        assert view.selected_records() == []

    def test_base_view_display_sets_current_record(self, qapp, sample_record):
        from koo2.ui.views.base_view import BaseView

        class ConcreteView(BaseView):
            def view_type(self): return "test"

        view = ConcreteView()
        view.display(sample_record)
        assert view.current_record == sample_record

    def test_base_view_selected_after_display(self, qapp, sample_record):
        from koo2.ui.views.base_view import BaseView

        class ConcreteView(BaseView):
            def view_type(self): return "test"

        view = ConcreteView()
        view.display(sample_record)
        assert sample_record in view.selected_records()

    def test_base_view_shows_single_record_by_default(self, qapp):
        from koo2.ui.views.base_view import BaseView

        class ConcreteView(BaseView):
            def view_type(self): return "test"

        view = ConcreteView()
        assert not view.shows_multiple_records()

    def test_view_type_raises_without_override(self, qapp):
        from koo2.ui.views.base_view import BaseView
        view = BaseView.__new__(BaseView)
        BaseView.__init__(view)
        with pytest.raises(NotImplementedError):
            view.view_type()


# ---------------------------------------------------------------------------
# FormView
# ---------------------------------------------------------------------------
class TestFormView:
    def test_view_type_is_form(self, qapp):
        from koo2.ui.views.form.form_view import FormView
        view = FormView()
        assert view.view_type() == "form"

    def test_shows_single_record(self, qapp):
        from koo2.ui.views.form.form_view import FormView
        view = FormView()
        assert not view.shows_multiple_records()

    def test_populate_fields_from_view_definition(self, qapp, simple_view_definition):
        from koo2.ui.views.form.form_view import FormView
        view = FormView(view_definition=simple_view_definition)
        assert "name" in view._field_widgets
        assert "email" in view._field_widgets

    def test_display_fills_widgets(self, qapp, simple_view_definition, sample_record):
        from koo2.ui.views.form.form_view import FormView
        from koo2.ui.widgets.text_field import MaterialTextField
        view = FormView(view_definition=simple_view_definition)
        view.display(sample_record)
        name_widget = view._field_widgets["name"]
        assert isinstance(name_widget, MaterialTextField)
        assert name_widget.text == "ACME"

    def test_store_updates_record(self, qapp, simple_view_definition, sample_record):
        from koo2.ui.views.form.form_view import FormView
        from koo2.ui.widgets.text_field import MaterialTextField
        view = FormView(view_definition=simple_view_definition)
        view.display(sample_record)
        name_widget = view._field_widgets["name"]
        if isinstance(name_widget, MaterialTextField):
            name_widget.setText("New Name")
        view.store()
        assert view.current_record.get("name") == "New Name"

    def test_read_only_disables_widgets(self, qapp, simple_view_definition):
        from koo2.ui.views.form.form_view import FormView
        view = FormView(view_definition=simple_view_definition, read_only=True)
        for widget in view._field_widgets.values():
            if hasattr(widget, "_edit"):
                assert widget._edit.isReadOnly()


# ---------------------------------------------------------------------------
# TreeView + RecordTableModel
# ---------------------------------------------------------------------------
class TestRecordTableModel:
    def test_row_count_empty(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        model = RecordTableModel()
        assert model.rowCount() == 0

    def test_row_count_with_records(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        records = [
            Record.from_server("res.partner", {"id": i, "name": f"Partner {i}"})
            for i in range(5)
        ]
        model = RecordTableModel(records=records, columns=["name"])
        assert model.rowCount() == 5

    def test_column_count(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        model = RecordTableModel(columns=["name", "email"])
        assert model.columnCount() == 2

    def test_data_display_role(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        from PySide6.QtCore import Qt, QModelIndex
        records = [Record.from_server("res.partner", {"id": 1, "name": "ACME"})]
        model = RecordTableModel(records=records, columns=["name"])
        idx = model.index(0, 0)
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == "ACME"

    def test_data_user_role_returns_record(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        from PySide6.QtCore import Qt
        rec = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        model = RecordTableModel(records=[rec], columns=["name"])
        idx = model.index(0, 0)
        assert model.data(idx, Qt.ItemDataRole.UserRole) is rec

    def test_load_records_resets_model(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        model = RecordTableModel()
        records = [Record.from_server("res.partner", {"id": 1, "name": "X"})]
        model.load_records(records, columns=["name"])
        assert model.rowCount() == 1

    def test_record_at_valid_index(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        rec = Record.from_server("res.partner", {"id": 1, "name": "X"})
        model = RecordTableModel(records=[rec], columns=["name"])
        assert model.record_at(0) is rec

    def test_record_at_invalid_index_returns_none(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        model = RecordTableModel()
        assert model.record_at(99) is None

    def test_header_data_horizontal(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        from PySide6.QtCore import Qt
        model = RecordTableModel(columns=["name"], headers={"name": "Name"})
        assert model.headerData(0, Qt.Orientation.Horizontal) == "Name"

    def test_header_data_vertical(self, qapp):
        from koo2.ui.views.tree.tree_view import RecordTableModel
        from PySide6.QtCore import Qt
        model = RecordTableModel(columns=["name"])
        assert model.headerData(0, Qt.Orientation.Vertical) == "1"


class TestTreeView:
    def test_view_type_is_tree(self, qapp):
        from koo2.ui.views.tree.tree_view import TreeView
        view = TreeView()
        assert view.view_type() == "tree"

    def test_shows_multiple_records(self, qapp):
        from koo2.ui.views.tree.tree_view import TreeView
        view = TreeView()
        assert view.shows_multiple_records()

    def test_display_list_of_records(self, qapp):
        from koo2.ui.views.tree.tree_view import TreeView
        view = TreeView()
        records = [Record.from_server("res.partner", {"id": i}) for i in range(3)]
        view.display(None, records=records)
        assert view._table_model.rowCount() == 3

    def test_selected_records_empty_by_default(self, qapp):
        from koo2.ui.views.tree.tree_view import TreeView
        view = TreeView()
        assert view.selected_records() == []
