"""Tests for koo2/core/view_parser — FormParser, TreeParser, nodes, attr_parser."""
from __future__ import annotations

import pytest

from koo2.core.domain.view_definition import FieldDefinition
from koo2.core.view_parser.attr_parser import parse_bool, parse_int, parse_str
from koo2.core.view_parser.nodes import (
    ButtonNode,
    ContainerNode,
    FieldNode,
    GroupNode,
    LabelNode,
    NewLineNode,
    NotebookNode,
    PageNode,
    SeparatorNode,
)
from koo2.core.view_parser.form_parser import FormParser
from koo2.core.view_parser.tree_parser import TreeParser, ColumnNode


# ---------------------------------------------------------------------------
# attr_parser helpers
# ---------------------------------------------------------------------------

class TestParseBool:
    def test_truthy_strings(self):
        for v in ("1", "True", "true", "TRUE"):
            assert parse_bool(v) is True

    def test_falsy_strings(self):
        for v in ("0", "False", "false", "", "no"):
            assert parse_bool(v) is False

    def test_int_values(self):
        assert parse_bool(1) is True
        assert parse_bool(0) is False

    def test_none_returns_default(self):
        assert parse_bool(None) is False
        assert parse_bool(None, default=True) is True


class TestParseInt:
    def test_valid(self):
        assert parse_int("4") == 4
        assert parse_int(2) == 2

    def test_invalid_returns_default(self):
        assert parse_int(None) == 1
        assert parse_int("abc", default=0) == 0


# ---------------------------------------------------------------------------
# FormParser — basic flat form
# ---------------------------------------------------------------------------

SIMPLE_ARCH = """
<form string="Partner" col="2">
  <field name="name"/>
  <field name="phone"/>
</form>
"""

FIELDS = {
    "name": FieldDefinition(name="name", field_type="char", string="Name"),
    "phone": FieldDefinition(name="phone", field_type="char", string="Phone"),
}


class TestFormParserSimple:
    def setup_method(self):
        self.parser = FormParser()

    def test_returns_container_and_title(self):
        container, title = self.parser.parse(SIMPLE_ARCH, FIELDS)
        assert isinstance(container, ContainerNode)
        assert title == "Partner"

    def test_container_columns(self):
        container, _ = self.parser.parse(SIMPLE_ARCH, FIELDS)
        assert container.columns == 2

    def test_fields_present(self):
        container, _ = self.parser.parse(SIMPLE_ARCH, FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        names = [n.name for n in all_nodes if isinstance(n, FieldNode)]
        assert names == ["name", "phone"]

    def test_field_metadata_merged(self):
        container, _ = self.parser.parse(SIMPLE_ARCH, FIELDS)
        name_node = [n for row in container.rows for n in row if isinstance(n, FieldNode) and n.name == "name"][0]
        assert name_node.string == "Name"
        assert name_node.field_type == "char"


# ---------------------------------------------------------------------------
# FormParser — group and notebook
# ---------------------------------------------------------------------------

GROUP_ARCH = """
<form string="Contact" col="4">
  <group string="Personal" col="2">
    <field name="name"/>
    <field name="age"/>
  </group>
</form>
"""

GROUP_FIELDS = {
    "name": FieldDefinition(name="name", field_type="char", string="Name"),
    "age": FieldDefinition(name="age", field_type="integer", string="Age"),
}


class TestFormParserGroup:
    def test_group_node_created(self):
        parser = FormParser()
        container, _ = parser.parse(GROUP_ARCH, GROUP_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        groups = [n for n in all_nodes if isinstance(n, GroupNode)]
        assert len(groups) == 1
        assert groups[0].string == "Personal"

    def test_group_inner_fields(self):
        parser = FormParser()
        container, _ = parser.parse(GROUP_ARCH, GROUP_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        group = next(n for n in all_nodes if isinstance(n, GroupNode))
        inner = [n for row in group.container.rows for n in row if isinstance(n, FieldNode)]
        assert [n.name for n in inner] == ["name", "age"]


NOTEBOOK_ARCH = """
<form string="Employee" col="1">
  <notebook>
    <page string="General">
      <field name="name"/>
    </page>
    <page string="Extra">
      <field name="notes"/>
    </page>
  </notebook>
</form>
"""

NOTEBOOK_FIELDS = {
    "name": FieldDefinition(name="name", field_type="char", string="Name"),
    "notes": FieldDefinition(name="notes", field_type="text", string="Notes"),
}


class TestFormParserNotebook:
    def test_notebook_node_created(self):
        parser = FormParser()
        container, _ = parser.parse(NOTEBOOK_ARCH, NOTEBOOK_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        notebooks = [n for n in all_nodes if isinstance(n, NotebookNode)]
        assert len(notebooks) == 1

    def test_pages(self):
        parser = FormParser()
        container, _ = parser.parse(NOTEBOOK_ARCH, NOTEBOOK_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        nb = next(n for n in all_nodes if isinstance(n, NotebookNode))
        assert len(nb.pages) == 2
        assert nb.pages[0].string == "General"
        assert nb.pages[1].string == "Extra"

    def test_page_fields(self):
        parser = FormParser()
        container, _ = parser.parse(NOTEBOOK_ARCH, NOTEBOOK_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        nb = next(n for n in all_nodes if isinstance(n, NotebookNode))
        general_fields = [n for row in nb.pages[0].container.rows for n in row if isinstance(n, FieldNode)]
        assert general_fields[0].name == "name"


# ---------------------------------------------------------------------------
# FormParser — button, separator, label
# ---------------------------------------------------------------------------

MISC_ARCH = """
<form col="4">
  <button name="action_confirm" string="Confirm" type="object"/>
  <separator string="Section A"/>
  <label string="Note:" for="name"/>
  <field name="name"/>
</form>
"""

MISC_FIELDS = {
    "name": FieldDefinition(name="name", field_type="char", string="Name"),
}


class TestFormParserMisc:
    def test_button_node(self):
        parser = FormParser()
        container, _ = parser.parse(MISC_ARCH, MISC_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        buttons = [n for n in all_nodes if isinstance(n, ButtonNode)]
        assert len(buttons) == 1
        assert buttons[0].name == "action_confirm"
        assert buttons[0].string == "Confirm"

    def test_separator_node(self):
        parser = FormParser()
        container, _ = parser.parse(MISC_ARCH, MISC_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        seps = [n for n in all_nodes if isinstance(n, SeparatorNode)]
        assert len(seps) == 1
        assert seps[0].string == "Section A"

    def test_label_node(self):
        parser = FormParser()
        container, _ = parser.parse(MISC_ARCH, MISC_FIELDS)
        all_nodes = [n for row in container.rows for n in row]
        labels = [n for n in all_nodes if isinstance(n, LabelNode)]
        assert len(labels) == 1
        assert labels[0].string == "Note:"


# ---------------------------------------------------------------------------
# FormParser — read_only propagation
# ---------------------------------------------------------------------------

class TestFormParserReadOnly:
    def test_readonly_form_propagates(self):
        parser = FormParser()
        container, _ = parser.parse(SIMPLE_ARCH, FIELDS, read_only=True)
        all_nodes = [n for row in container.rows for n in row]
        fields = [n for n in all_nodes if isinstance(n, FieldNode)]
        assert all(f.read_only for f in fields)

    def test_field_readonly_from_metadata(self):
        fields = {
            "name": FieldDefinition(name="name", field_type="char", string="Name", readonly=True),
            "phone": FieldDefinition(name="phone", field_type="char", string="Phone"),
        }
        parser = FormParser()
        container, _ = parser.parse(SIMPLE_ARCH, fields)
        all_nodes = [n for row in container.rows for n in row]
        name_node = next(n for n in all_nodes if isinstance(n, FieldNode) and n.name == "name")
        phone_node = next(n for n in all_nodes if isinstance(n, FieldNode) and n.name == "phone")
        assert name_node.read_only is True
        assert phone_node.read_only is False


# ---------------------------------------------------------------------------
# TreeParser
# ---------------------------------------------------------------------------

TREE_ARCH = """
<tree string="Partners">
  <field name="name"/>
  <field name="phone"/>
  <field name="active" invisible="1"/>
</tree>
"""

TREE_FIELDS = {
    "name": FieldDefinition(name="name", field_type="char", string="Name"),
    "phone": FieldDefinition(name="phone", field_type="char", string="Phone"),
    "active": FieldDefinition(name="active", field_type="boolean", string="Active"),
}


class TestTreeParser:
    def test_returns_column_list(self):
        parser = TreeParser()
        columns = parser.parse(TREE_ARCH, TREE_FIELDS)
        assert len(columns) == 3

    def test_column_names_in_order(self):
        parser = TreeParser()
        columns = parser.parse(TREE_ARCH, TREE_FIELDS)
        assert [c.name for c in columns] == ["name", "phone", "active"]

    def test_invisible_column(self):
        parser = TreeParser()
        columns = parser.parse(TREE_ARCH, TREE_FIELDS)
        assert columns[2].invisible is True

    def test_field_type_from_metadata(self):
        parser = TreeParser()
        columns = parser.parse(TREE_ARCH, TREE_FIELDS)
        assert columns[0].field_type == "char"
        assert columns[2].field_type == "boolean"

    def test_readonly_propagates(self):
        parser = TreeParser()
        columns = parser.parse(TREE_ARCH, TREE_FIELDS, read_only=True)
        assert all(c.read_only for c in columns)
