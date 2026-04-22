"""
Tests for koo2.core.domain.view_definition

Pure-Python; no Qt or network required.
"""
import pytest

from koo2.core.domain.view_definition import FieldDefinition, ViewDefinition


class TestFieldDefinition:
    def test_from_server_basic(self):
        fdef = FieldDefinition.from_server("name", {"type": "char", "string": "Name"})
        assert fdef.name == "name"
        assert fdef.field_type == "char"
        assert fdef.string == "Name"

    def test_from_server_defaults(self):
        fdef = FieldDefinition.from_server("active", {"type": "boolean"})
        assert not fdef.required
        assert not fdef.readonly
        assert not fdef.invisible

    def test_from_server_required(self):
        fdef = FieldDefinition.from_server("name", {"type": "char", "required": True})
        assert fdef.required

    def test_from_server_selection(self):
        fdef = FieldDefinition.from_server(
            "state",
            {"type": "selection", "selection": [("draft", "Draft"), ("done", "Done")]},
        )
        assert fdef.selection == [("draft", "Draft"), ("done", "Done")]

    def test_from_server_relation(self):
        fdef = FieldDefinition.from_server(
            "partner_id",
            {"type": "many2one", "relation": "res.partner"},
        )
        assert fdef.relation == "res.partner"
        assert fdef.is_relational

    def test_non_relational_field(self):
        fdef = FieldDefinition.from_server("name", {"type": "char"})
        assert not fdef.is_relational

    def test_extra_attrs_stored(self):
        fdef = FieldDefinition.from_server("amount", {"type": "float", "digits": [16, 2]})
        assert fdef.attrs.get("digits") == [16, 2]

    def test_field_definition_is_frozen(self):
        fdef = FieldDefinition.from_server("name", {"type": "char"})
        with pytest.raises((AttributeError, TypeError)):
            fdef.name = "other"  # type: ignore[misc]


class TestViewDefinition:
    def test_from_server_basic(self):
        data = {
            "arch": "<form><field name='name'/></form>",
            "fields": {"name": {"type": "char", "string": "Name"}},
        }
        vdef = ViewDefinition.from_server("form", data, model="res.partner")
        assert vdef.view_type == "form"
        assert vdef.model == "res.partner"
        assert "<form>" in vdef.arch

    def test_from_server_fields_parsed(self):
        data = {
            "arch": "<tree><field name='name'/><field name='email'/></tree>",
            "fields": {
                "name": {"type": "char", "string": "Name"},
                "email": {"type": "char", "string": "Email"},
            },
        }
        vdef = ViewDefinition.from_server("tree", data)
        assert "name" in vdef.fields
        assert "email" in vdef.fields
        assert isinstance(vdef.fields["name"], FieldDefinition)

    def test_from_server_empty_fields(self):
        data = {"arch": "<form/>", "fields": {}}
        vdef = ViewDefinition.from_server("form", data)
        assert vdef.fields == {}

    def test_from_server_view_id(self):
        data = {"arch": "<form/>", "fields": {}, "view_id": 123}
        vdef = ViewDefinition.from_server("form", data)
        assert vdef.view_id == 123

    def test_view_definition_is_frozen(self):
        data = {"arch": "<form/>", "fields": {}}
        vdef = ViewDefinition.from_server("form", data)
        with pytest.raises((AttributeError, TypeError)):
            vdef.view_type = "tree"  # type: ignore[misc]
