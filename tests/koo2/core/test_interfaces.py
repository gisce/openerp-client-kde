"""
Tests for koo2.core.interfaces

Verify that the Protocol classes correctly describe the expected interface
surface and that runtime_checkable works for duck-typing checks.
"""
import pytest

from koo2.core.interfaces.rpc_client import IRpcClient
from koo2.core.interfaces.view import IView
from koo2.core.interfaces.field_widget import IFieldWidget
from koo2.core.interfaces.repository import IRepository


class _FakeRpcClient:
    """Minimal duck-type implementation of IRpcClient."""
    def login(self, url, database, username, password): return True
    def logout(self): pass
    @property
    def is_logged_in(self): return False
    def search(self, model, domain=None, offset=0, limit=None, order=None, context=None): return []
    def read(self, model, ids, fields=None, context=None): return []
    def write(self, model, ids, values, context=None): return True
    def create(self, model, values, context=None): return 1
    def unlink(self, model, ids, context=None): return True
    def execute(self, model, method, *args, context=None): return None
    def fields_get(self, model, fields=None, context=None): return {}
    def fields_view_get(self, model, view_id=None, view_type="form", context=None): return {}


class _FakeView:
    """Minimal duck-type implementation of IView."""
    def view_type(self): return "form"
    def display(self, record, records): pass
    def store(self): pass
    def reset(self): pass
    def selected_records(self): return []
    def set_selected(self, record): pass
    def is_read_only(self): return False
    def set_read_only(self, value): pass
    def shows_multiple_records(self): return False
    def start_editing(self): pass


class _FakeFieldWidget:
    """Minimal duck-type implementation of IFieldWidget."""
    @property
    def field_name(self): return "name"
    def set_value(self, value): pass
    def get_value(self): return None
    def is_valid(self): return True
    def set_read_only(self, read_only): pass
    def set_required(self, required): pass
    def reset_validity(self): pass


class _FakeRepository:
    """Minimal duck-type implementation of IRepository."""
    @property
    def model_name(self): return "res.partner"
    def find(self, domain=None, fields=None, offset=0, limit=None, order=None, context=None): return []
    def get(self, record_id, fields=None, context=None): return None
    def save(self, record_id, values, context=None): return 1
    def delete(self, record_id, context=None): pass
    def get_field_definitions(self, context=None): return {}
    def get_view_definition(self, view_type="form", view_id=None, context=None): return {}


class TestIRpcClient:
    def test_fake_client_satisfies_protocol(self):
        assert isinstance(_FakeRpcClient(), IRpcClient)

    def test_non_conforming_object_does_not_satisfy(self):
        assert not isinstance(object(), IRpcClient)


class TestIView:
    def test_fake_view_satisfies_protocol(self):
        assert isinstance(_FakeView(), IView)

    def test_non_conforming_object_does_not_satisfy(self):
        assert not isinstance(object(), IView)


class TestIFieldWidget:
    def test_fake_widget_satisfies_protocol(self):
        assert isinstance(_FakeFieldWidget(), IFieldWidget)

    def test_non_conforming_object_does_not_satisfy(self):
        assert not isinstance(object(), IFieldWidget)


class TestIRepository:
    def test_fake_repo_satisfies_protocol(self):
        assert isinstance(_FakeRepository(), IRepository)

    def test_non_conforming_object_does_not_satisfy(self):
        assert not isinstance(object(), IRepository)
