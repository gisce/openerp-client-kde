"""
FormView – Material Design 3 form view.

Renders a single record in an editable form using the XML ``arch`` from the
ERP view definition (mirrors react-ooui FormView philosophy):

  ViewDefinition.arch (XML)
        ↓
  FormParser.parse()  →  ContainerNode tree
        ↓
  WidgetFactory       →  PySide6 widgets placed in FormGrid / GroupWidget / NotebookWidget

Architecture notes (SOLID)
--------------------------
* SRP  – FormView only handles presentation; validation is in field widgets.
* OCP  – New field types are registered in WidgetFactory; FormView never
         needs to be modified for new types.
* DIP  – FormView depends on AbstractFieldWidget protocol, not concrete widgets.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from koo2.core.domain.record import Record
from koo2.core.domain.view_definition import FieldDefinition, ViewDefinition
from koo2.core.view_parser.form_parser import FormParser
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
    WidgetNode,
)
from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette
from koo2.ui.views.base_view import BaseView
from koo2.ui.widgets.containers import FormGrid, GroupWidget, NotebookWidget
from koo2.ui.widgets.factory import WidgetFactory
from koo2.ui.widgets.fields.base import AbstractFieldWidget


class FormView(BaseView):
    """Material Design form view for a single record.

    When the :class:`~koo2.core.domain.view_definition.ViewDefinition` contains
    an ``arch`` XML string the form is laid out exactly as the ERP specifies
    (columns, groups, notebooks, labels, separators, newlines).

    If no arch is present the view falls back to a plain vertical list of
    fields (backward-compatible with the old behaviour).
    """

    def __init__(
        self,
        view_definition: Optional[ViewDefinition] = None,
        read_only: bool = False,
        palette: Palette = DEFAULT_LIGHT,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(view_definition=view_definition, read_only=read_only, parent=parent)
        self._palette = palette
        self._factory = WidgetFactory()
        self._field_widgets: Dict[str, AbstractFieldWidget] = {}  # field_name → widget

        self._build_ui()
        if view_definition:
            self._populate_from_definition(view_definition)

    # ------------------------------------------------------------------
    # IView
    # ------------------------------------------------------------------
    def view_type(self) -> str:
        return "form"

    def shows_multiple_records(self) -> bool:
        return False

    def display(self, record: Any, records: Any = None) -> None:
        super().display(record, records)
        if isinstance(record, Record):
            self._fill_widgets(record)

    def store(self) -> None:
        """Flush widget values into the current record."""
        if self._current_record is None:
            return
        for field_name, widget in self._field_widgets.items():
            if not widget.read_only:
                self._current_record.set(field_name, widget.get_value())

    def reset(self) -> None:
        for widget in self._field_widgets.values():
            pass  # extend when per-widget validation indicators are added

    def _on_read_only_changed(self, read_only: bool) -> None:
        for widget in self._field_widgets.values():
            widget.set_read_only(read_only)

    # ------------------------------------------------------------------
    # Build UI scaffold
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._scroll_container = QWidget()
        scroll.setWidget(self._scroll_container)

        self._scroll_layout = QVBoxLayout(self._scroll_container)
        self._scroll_layout.setContentsMargins(16, 16, 16, 16)
        self._scroll_layout.setSpacing(8)
        self._scroll_layout.addStretch(1)

        self._root_layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Populate from ViewDefinition
    # ------------------------------------------------------------------
    def _populate_from_definition(self, view_def: ViewDefinition) -> None:
        """Build the form layout from *view_def*."""
        # Remove the trailing stretch so widgets appear above it
        count = self._scroll_layout.count()
        if count > 0:
            item = self._scroll_layout.itemAt(count - 1)
            if item and item.spacerItem():
                self._scroll_layout.removeItem(item)

        if view_def.arch:
            self._populate_from_arch(view_def)
        else:
            self._populate_fields_fallback(view_def)

        self._scroll_layout.addStretch(1)

    def _populate_from_arch(self, view_def: ViewDefinition) -> None:
        """Use FormParser to build the layout from the XML arch."""
        container, _title = FormParser().parse(
            view_def.arch, view_def.fields, read_only=self._read_only
        )
        columns = container.columns or 4
        root_grid = FormGrid(columns=columns, parent=self._scroll_container)
        self._scroll_layout.addWidget(root_grid)
        self._render_container(container, root_grid)

    def _render_container(self, container: ContainerNode, grid: FormGrid) -> None:
        """Recursively place nodes from *container* into *grid*."""
        for row in container.rows:
            for node in row:
                self._render_node(node, grid)

    def _render_node(self, node: WidgetNode, grid: FormGrid) -> None:  # noqa: C901
        """Dispatch a single node to the correct rendering method."""
        if node.invisible:
            return

        if isinstance(node, NewLineNode):
            grid.new_row()

        elif isinstance(node, FieldNode):
            widget = self._factory.create_field(node, parent=grid)
            if isinstance(widget, AbstractFieldWidget):
                self._field_widgets[node.name] = widget
            # Use colspan*2 because each field takes label + widget columns
            label_widget = QLabel(node.string or node.name, grid)
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.add_widget(label_widget, colspan=1)
            colspan = max(1, (node.colspan or 1) - 1)
            grid.add_widget(widget, colspan=colspan)

        elif isinstance(node, LabelNode):
            w = self._factory.create_label(node, parent=grid)
            grid.add_widget(w, colspan=node.colspan or 1)

        elif isinstance(node, SeparatorNode):
            w = self._factory.create_separator_label(node, parent=grid)
            grid.add_widget(w, colspan=node.colspan or 1)

        elif isinstance(node, ButtonNode):
            w = self._factory.create_button(node, parent=grid)
            grid.add_widget(w, colspan=node.colspan or 1)

        elif isinstance(node, GroupNode):
            group_widget = self._factory.create_group(node, parent=grid)
            grid.add_widget(group_widget, colspan=node.colspan or grid._columns)
            if node.container:
                self._render_container(node.container, group_widget.inner_grid)

        elif isinstance(node, NotebookNode):
            nb_widget = self._factory.create_notebook(node, parent=grid)
            grid.add_widget(nb_widget, colspan=node.colspan or grid._columns)
            for page in node.pages:
                page_grid = nb_widget.add_page(
                    title=page.string or "",
                    columns=page.container.columns if page.container else 4,
                )
                if page.container:
                    self._render_container(page.container, page_grid)

    # ------------------------------------------------------------------
    # Fallback: no arch XML (plain field list)
    # ------------------------------------------------------------------
    def _populate_fields_fallback(self, view_def: ViewDefinition) -> None:
        """Simple vertical field list when no arch is available."""
        from PySide6.QtWidgets import QFormLayout
        form_widget = QWidget(self._scroll_container)
        layout = QFormLayout(form_widget)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(8)
        self._scroll_layout.addWidget(form_widget)

        for field_name, field_def in view_def.fields.items():
            if field_def.invisible:
                continue
            node = FieldNode(
                name=field_name,
                field_type=field_def.field_type or "char",
                string=field_def.string or field_name,
                read_only=self._read_only or field_def.readonly,
            )
            widget = self._factory.create_field(node)
            if isinstance(widget, AbstractFieldWidget):
                self._field_widgets[field_name] = widget
            lbl = QLabel(field_def.string or field_name)
            layout.addRow(lbl, widget)

    # ------------------------------------------------------------------
    # Fill widget values from a Record
    # ------------------------------------------------------------------
    def _fill_widgets(self, record: Record) -> None:
        for field_name, widget in self._field_widgets.items():
            value = record.get(field_name)
            widget.set_value(value)

