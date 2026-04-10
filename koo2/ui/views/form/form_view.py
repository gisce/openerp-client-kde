"""
FormView – Material Design 3 form view.

Renders a single record in an editable form with field widgets arranged in a
responsive grid.  The layout is built dynamically from a :class:`ViewDefinition`
so no ``.ui`` files are required.

Architecture notes (SOLID)
--------------------------
* SRP  – FormView only handles presentation; validation is in field widgets.
* OCP  – New field types are registered in FieldWidgetFactory; FormView never
         needs to be modified for new types.
* DIP  – FormView depends on IFieldWidget protocol, not concrete widgets.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QWidget,
)

from koo2.core.domain.record import Record
from koo2.core.domain.view_definition import FieldDefinition, ViewDefinition
from koo2.ui.theme.palette import DEFAULT_LIGHT, Palette
from koo2.ui.views.base_view import BaseView
from koo2.ui.widgets.text_field import MaterialTextField


class FormView(BaseView):
    """Material Design form view for a single record.

    For each field in the ViewDefinition the appropriate widget is created and
    arranged in a QFormLayout inside a scroll area.
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
        self._field_widgets: Dict[str, Any] = {}  # field_name → widget

        self._build_ui()
        if view_definition:
            self._populate_fields(view_definition)

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
            value = self._read_widget_value(widget)
            if value is not None:
                self._current_record.set(field_name, value)

    def reset(self) -> None:
        for widget in self._field_widgets.values():
            self._reset_widget_validation(widget)

    def _on_read_only_changed(self, read_only: bool) -> None:
        for widget in self._field_widgets.values():
            if hasattr(widget, "setReadOnly"):
                widget.setReadOnly(read_only)

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Scroll area so the form works for records with many fields
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        scroll.setWidget(container)

        self._form_layout = QFormLayout(container)
        self._form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self._form_layout.setHorizontalSpacing(16)
        self._form_layout.setVerticalSpacing(8)
        self._form_layout.setContentsMargins(16, 16, 16, 16)

        self._root_layout.addWidget(scroll)

    def _populate_fields(self, view_def: ViewDefinition) -> None:
        """Create a widget row for each field in *view_def*."""
        for field_name, field_def in view_def.fields.items():
            if field_def.invisible:
                continue
            label = QLabel(field_def.string or field_name)
            label.setProperty("caption", True)
            widget = self._create_field_widget(field_def)
            self._field_widgets[field_name] = widget
            self._form_layout.addRow(label, widget)

    def _create_field_widget(self, field_def: FieldDefinition) -> QWidget:
        """Return the appropriate widget for *field_def*."""
        widget: QWidget
        if field_def.field_type in ("char", "text", "many2one"):
            tf = MaterialTextField(palette=self._palette)
            tf.setReadOnly(self._read_only)
            widget = tf
        elif field_def.field_type in ("integer", "float", "monetary"):
            tf = MaterialTextField(palette=self._palette)
            tf.setReadOnly(self._read_only)
            widget = tf
        else:
            # Fallback to a plain read-only label for unsupported types
            lbl = QLabel()
            lbl.setProperty("caption", True)
            widget = lbl

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return widget

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _fill_widgets(self, record: Record) -> None:
        for field_name, widget in self._field_widgets.items():
            value = record.get(field_name, "")
            display_value = "" if value is None else str(value)
            if isinstance(widget, MaterialTextField):
                widget.setText(display_value)
            elif isinstance(widget, QLabel):
                widget.setText(display_value)

    @staticmethod
    def _read_widget_value(widget: Any) -> Optional[str]:
        if isinstance(widget, MaterialTextField):
            return widget.text
        return None

    @staticmethod
    def _reset_widget_validation(widget: Any) -> None:
        pass  # Extend when per-widget validation indicators are added
