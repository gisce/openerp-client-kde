"""
view_parser/tree_parser.py — XML arch → list of ColumnNode.

Parses the ``<tree>`` arch from ``fields_view_get`` into a flat list of
column descriptors that the TreeView can use to build a QTableWidget /
QAbstractTableModel.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from koo2.core.domain.view_definition import FieldDefinition
from .attr_parser import parse_bool, parse_int, parse_str


@dataclass
class ColumnNode:
    """One column in a tree/list view."""

    name: str
    string: str = ""
    field_type: str = "char"
    widget_hint: str = ""
    read_only: bool = False
    invisible: bool = False
    optional: str = ""     # 'show' | 'hide' | '' — QGIS columns can be toggled
    width: Optional[int] = None
    attrs: Dict = field(default_factory=dict)


class TreeParser:
    """Parse a ``<tree>`` arch XML string into a list of :class:`ColumnNode`."""

    def parse(
        self,
        arch: str,
        fields: Dict[str, FieldDefinition],
        read_only: bool = False,
    ) -> List[ColumnNode]:
        """Return an ordered list of ColumnNode objects.

        Parameters
        ----------
        arch:
            Raw XML string from ``fields_view_get``.
        fields:
            FieldDefinition dict for the model.
        read_only:
            When True all columns inherit ``read_only=True``.
        """
        root_el = ET.fromstring(arch)
        columns: List[ColumnNode] = []
        for el in root_el:
            if el.tag != "field":
                continue
            a = el.attrib
            name = parse_str(a.get("name"))
            meta: Optional[FieldDefinition] = fields.get(name)

            col = ColumnNode(name=name)
            col.widget_hint = parse_str(a.get("widget"))
            col.invisible = parse_bool(a.get("invisible", "0"))
            col.optional = parse_str(a.get("optional", ""))
            raw_width = a.get("width")
            if raw_width:
                col.width = parse_int(raw_width, 0) or None

            if meta:
                col.string = parse_str(a.get("string") or meta.string)
                col.field_type = meta.field_type
                if read_only:
                    col.read_only = True
                else:
                    col.read_only = meta.readonly or parse_bool(a.get("readonly", "0"))
            else:
                col.string = parse_str(a.get("string") or name)

            columns.append(col)
        return columns
