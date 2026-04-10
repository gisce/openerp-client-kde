"""
Tests for koo2.core.domain.record

These tests are pure-Python and require no Qt or network.
"""
import pytest
from copy import deepcopy

from koo2.core.domain.record import Record


class TestRecordIdentity:
    def test_new_record_is_new(self):
        r = Record.new("res.partner")
        assert r.is_new

    def test_server_record_is_not_new(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        assert not r.is_new

    def test_server_record_has_id(self):
        r = Record.from_server("res.partner", {"id": 42})
        assert r.id == 42


class TestRecordModification:
    def test_fresh_server_record_is_not_modified(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        assert not r.is_modified

    def test_new_record_without_changes_not_modified(self):
        r = Record.new("res.partner")
        assert not r.is_modified

    def test_set_marks_record_modified(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        r.set("name", "New Name")
        assert r.is_modified

    def test_set_many_marks_record_modified(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        r.set_many({"name": "X", "email": "x@x.com"})
        assert r.is_modified

    def test_dirty_fields_returns_changed_fields_only(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME", "email": "a@a.com"})
        r.set("name", "New Name")
        assert r.dirty_fields == {"name": "New Name"}
        assert "email" not in r.dirty_fields

    def test_setting_same_value_not_modified(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        r.set("name", "ACME")
        assert not r.is_modified


class TestRecordValueAccess:
    def test_get_existing_field(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        assert r.get("name") == "ACME"

    def test_get_missing_field_returns_default(self):
        r = Record.new("res.partner")
        assert r.get("name") is None
        assert r.get("name", "N/A") == "N/A"

    def test_set_and_get(self):
        r = Record.new("res.partner")
        r.set("name", "Hello")
        assert r.get("name") == "Hello"


class TestRecordSnapshot:
    def test_mark_saved_clears_modification_flag(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        r.set("name", "New Name")
        assert r.is_modified
        r.mark_saved()
        assert not r.is_modified

    def test_mark_saved_assigns_id_to_new_record(self):
        r = Record.new("res.partner")
        r.set("name", "New Co")
        r.mark_saved(server_id=99)
        assert r.id == 99
        assert not r.is_new

    def test_discard_reverts_changes(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        r.set("name", "Changed")
        r.discard()
        assert r.get("name") == "ACME"
        assert not r.is_modified

    def test_from_server_original_values_immutable(self):
        data = {"id": 1, "name": "ACME"}
        r = Record.from_server("res.partner", data)
        data["name"] = "Modified"
        assert r.get("name") == "ACME"

    def test_discard_isolates_from_original_values(self):
        r = Record.from_server("res.partner", {"id": 1, "name": "ACME"})
        r.set("name", "Temp")
        r.discard()
        r.set("name", "Again")
        assert r.get("name") == "Again"
        r.discard()
        assert r.get("name") == "ACME"


class TestRecordFactory:
    def test_new_with_defaults(self):
        r = Record.new("res.partner", {"name": "Default Co", "active": True})
        assert r.get("name") == "Default Co"
        assert r.get("active") is True

    def test_from_server_all_fields(self):
        data = {"id": 5, "name": "Partner", "email": "p@p.com"}
        r = Record.from_server("res.partner", data)
        assert r.get("email") == "p@p.com"
        assert r.model == "res.partner"
