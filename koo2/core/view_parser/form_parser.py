"""
view_parser/form_parser.py — XML arch → ContainerNode tree.

Mirrors the ooui.js ``Form.ts`` ``parse()`` / ``parseNode()`` logic, adapted
for Python + OpenERP XML conventions.

Usage
-----
    from koo2.core.view_parser import FormParser
    from koo2.core.domain.view_definition import ViewDefinition

    view_def = ViewDefinition.from_server("form", fields_view_get_result, model)
    parser = FormParser()
    root, title = parser.parse(view_def.arch, view_def.fields)
    # root: ContainerNode  — pass to WidgetFactory to build PySide6 widgets
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple

from koo2.core.domain.view_definition import FieldDefinition
from .attr_parser import parse_bool, parse_int, parse_str
from .nodes import (
    ButtonNode,
    ContainerNode,
    FieldNode,
    GroupNode,
    LabelNode,
    NewLineNode,
    NotebookNode,
    PageNode,
    SeparatorNode,
    WidgetNode,
)


class FormParser:
    """Parse a ``fields_view_get`` XML *arch* string into a ContainerNode tree.

    The parser is stateless: call :meth:`parse` as many times as needed.
    """

    def parse(
        self,
        arch: str,
        fields: Dict[str, FieldDefinition],
        read_only: bool = False,
    ) -> Tuple[ContainerNode, Optional[str]]:
        """Parse *arch* XML and return ``(root_container, form_title)``.

        Parameters
        ----------
        arch:
            Raw XML string from ``fields_view_get``'s ``arch`` key.
        fields:
            Field metadata dict — value of ``fields_view_get``'s ``fields`` key,
            already parsed into :class:`FieldDefinition` objects.
        read_only:
            When True every field node inherits ``read_only=True``.

        Returns
        -------
        (ContainerNode, title_or_None)
        """
        root_el = ET.fromstring(arch)
        columns = parse_int(root_el.attrib.get("col", root_el.attrib.get("cols", "4")), 4)
        title = parse_str(root_el.attrib.get("string")) or None
        container = ContainerNode(columns=columns)
        container.rows.append([])

        self._parse_children(root_el, container, fields, read_only)
        return container, title

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_children(
        self,
        parent_el: ET.Element,
        container: ContainerNode,
        fields: Dict[str, FieldDefinition],
        read_only: bool,
    ) -> None:
        for el in parent_el:
            tag = el.tag
            if tag == "field":
                node = self._parse_field(el, fields, read_only)
            elif tag == "button":
                node = self._parse_button(el, read_only)
            elif tag == "label":
                node = self._parse_label(el)
            elif tag == "separator":
                node = self._parse_separator(el)
            elif tag == "newline":
                container.new_row()
                continue
            elif tag == "group":
                node = self._parse_group(el, fields, read_only)
            elif tag == "notebook":
                node = self._parse_notebook(el, fields, read_only)
            elif tag in ("form", "tree"):
                # Embedded sub-views (e.g. one2many inline) — skip for now
                continue
            else:
                # Unknown tag: create a minimal placeholder
                node = WidgetNode(type=tag, attrs=dict(el.attrib))

            self._apply_common_attrs(node, el, read_only)
            container.add_widget(node)

    def _apply_common_attrs(
        self, node: WidgetNode, el: ET.Element, read_only: bool
    ) -> None:
        """Fill shared WidgetNode attributes from *el* attribs.

        FieldNode.read_only is handled entirely inside _parse_field (it merges
        the field metadata with the XML attribute).  For all other node types
        we apply the XML readonly attr here.
        """
        a = el.attrib
        node.colspan = parse_int(a.get("colspan", "1"), 1)
        node.invisible = parse_bool(a.get("invisible", "0"))
        node.required = parse_bool(a.get("required", "0"))
        if read_only:
            node.read_only = True
        elif not isinstance(node, FieldNode):
            node.read_only = parse_bool(a.get("readonly", "0"))

    # ------------------------------------------------------------------
    # Node builders
    # ------------------------------------------------------------------

    def _parse_field(
        self,
        el: ET.Element,
        fields: Dict[str, FieldDefinition],
        read_only: bool,
    ) -> FieldNode:
        a = el.attrib
        name = parse_str(a.get("name"))
        meta: Optional[FieldDefinition] = fields.get(name)

        node = FieldNode(name=name)
        node.widget_hint = parse_str(a.get("widget"))
        node.nolabel = parse_bool(a.get("nolabel", "0"))
        node.on_change = parse_str(a.get("on_change"))
        node.domain = parse_str(a.get("domain"))
        node.context = parse_str(a.get("context"))

        if meta:
            node.string = parse_str(a.get("string") or meta.string)
            node.field_type = meta.field_type
            node.help = meta.help or ""
            node.selection = list(meta.selection) if meta.selection else []
            node.relation = meta.relation or ""
            if not read_only:
                node.read_only = meta.readonly or parse_bool(a.get("readonly", "0"))
            node.required = meta.required or parse_bool(a.get("required", "0"))
            node.invisible = meta.invisible or parse_bool(a.get("invisible", "0"))
        else:
            node.string = parse_str(a.get("string") or name)

        return node

    def _parse_button(self, el: ET.Element, read_only: bool) -> ButtonNode:
        a = el.attrib
        return ButtonNode(
            name=parse_str(a.get("name")),
            string=parse_str(a.get("string") or a.get("name")),
            button_type=parse_str(a.get("type", "object")),
            confirm=parse_str(a.get("confirm")),
            icon=parse_str(a.get("icon")),
            states=parse_str(a.get("states")),
            read_only=read_only,
        )

    def _parse_label(self, el: ET.Element) -> LabelNode:
        a = el.attrib
        return LabelNode(
            string=parse_str(a.get("string")),
            name=parse_str(a.get("for", a.get("name", ""))),
        )

    def _parse_separator(self, el: ET.Element) -> SeparatorNode:
        a = el.attrib
        return SeparatorNode(
            string=parse_str(a.get("string")),
            orientation=parse_str(a.get("orientation", "horizontal")),
        )

    def _parse_group(
        self,
        el: ET.Element,
        fields: Dict[str, FieldDefinition],
        read_only: bool,
    ) -> GroupNode:
        a = el.attrib
        columns = parse_int(a.get("col", a.get("cols", "4")), 4)
        inner = ContainerNode(columns=columns)
        inner.rows.append([])
        self._parse_children(el, inner, fields, read_only)
        return GroupNode(
            string=parse_str(a.get("string")),
            container=inner,
        )

    def _parse_notebook(
        self,
        el: ET.Element,
        fields: Dict[str, FieldDefinition],
        read_only: bool,
    ) -> NotebookNode:
        pages: list[PageNode] = []
        for page_el in el:
            if page_el.tag != "page":
                continue
            a = page_el.attrib
            columns = parse_int(a.get("col", a.get("cols", "4")), 4)
            inner = ContainerNode(columns=columns)
            inner.rows.append([])
            self._parse_children(page_el, inner, fields, read_only)
            page = PageNode(
                string=parse_str(a.get("string", "Page")),
                invisible=parse_bool(a.get("invisible", "0")),
                container=inner,
            )
            pages.append(page)
        return NotebookNode(pages=pages)
