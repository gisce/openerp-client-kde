"""
koo2/ui/widgets/factory.py — WidgetFactory

Maps FieldNode.field_type / widget_hint strings to concrete PySide6 widget
classes.  Mirrors ooui.js WidgetFactory.ts.

Usage
-----
    factory = WidgetFactory()
    widget = factory.create_field(field_node)
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QLabel, QWidget

from koo2.core.view_parser.nodes import (
    ButtonNode,
    FieldNode,
    GroupNode,
    LabelNode,
    NotebookNode,
    SeparatorNode,
    WidgetNode,
)
from koo2.ui.widgets.fields import (
    BooleanWidget,
    CharWidget,
    DateTimeWidget,
    DateWidget,
    FloatWidget,
    IntegerWidget,
    Many2oneWidget,
    SelectionWidget,
    TextWidget,
)
from koo2.ui.widgets.containers import FormGrid, GroupWidget, NotebookWidget


class WidgetFactory:
    """Create PySide6 widgets from parser nodes.

    The factory is extensible: callers can register additional mappings via
    :meth:`register` without subclassing.
    """

    # Default type → widget class mapping (mirrors WidgetFactory.ts switch)
    _FIELD_TYPE_MAP = {
        "char": CharWidget,
        "text": TextWidget,
        "html": TextWidget,
        "integer": IntegerWidget,
        "float": FloatWidget,
        "monetary": FloatWidget,
        "boolean": BooleanWidget,
        "date": DateWidget,
        "datetime": DateTimeWidget,
        "many2one": Many2oneWidget,
        # one2many / many2many rendered as embedded tree — fallback to label
        "one2many": None,
        "many2many": None,
        "selection": SelectionWidget,
        "reference": CharWidget,    # simplified
        "binary": CharWidget,       # simplified
        "url": CharWidget,
    }

    def __init__(self) -> None:
        self._map = dict(self._FIELD_TYPE_MAP)

    def register(self, field_type: str, widget_class: type) -> None:
        """Register a custom widget class for *field_type*."""
        self._map[field_type] = widget_class

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_field(
        self,
        node: FieldNode,
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """Return a PySide6 widget appropriate for *node*.

        The ``widget_hint`` attribute (explicit ``widget=`` in the XML) takes
        priority over the field's native type.
        """
        effective_type = node.widget_hint or node.field_type
        widget_class = self._map.get(effective_type)

        if widget_class is None:
            # Unknown or unsupported type — fallback to read-only label
            lbl = QLabel(parent)
            lbl.setEnabled(not node.read_only)
            return lbl

        if effective_type == "selection":
            widget = SelectionWidget(selection=node.selection, parent=parent)
        else:
            widget = widget_class(parent=parent)  # type: ignore[call-arg]

        if hasattr(widget, "set_read_only"):
            widget.set_read_only(node.read_only)

        return widget

    def create_label(self, node: LabelNode, parent: Optional[QWidget] = None) -> QLabel:
        lbl = QLabel(node.string, parent)
        return lbl

    def create_separator_label(
        self, node: SeparatorNode, parent: Optional[QWidget] = None
    ) -> QLabel:
        lbl = QLabel(node.string, parent)
        lbl.setProperty("separator", True)
        return lbl

    def create_button(
        self, node: ButtonNode, parent: Optional[QWidget] = None
    ) -> QWidget:
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton(node.string or node.name, parent)
        btn.setEnabled(not node.read_only)
        return btn

    def create_group(
        self, node: GroupNode, parent: Optional[QWidget] = None
    ) -> GroupWidget:
        columns = node.container.columns if node.container else 4
        return GroupWidget(title=node.string, columns=columns, parent=parent)

    def create_notebook(
        self, node: NotebookNode, parent: Optional[QWidget] = None
    ) -> NotebookWidget:
        return NotebookWidget(parent=parent)
