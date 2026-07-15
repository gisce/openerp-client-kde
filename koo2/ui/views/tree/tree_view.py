"""
TreeView – Material Design 3 list / table view.

Presents multiple records in a QTableView with MD3 styling: zebra striping
via the palette ``surface_variant`` colour, header typography from the MD3
label scale, and row-level selection using ``primary_container``.

The model used is a lightweight ``RecordTableModel`` that wraps a list of
:class:`~koo2.core.domain.record.Record` objects and exposes columns from the
ViewDefinition.  This keeps Qt model logic separate from presentation (SRP).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from koo2.core.domain.record import Record
from koo2.core.domain.view_definition import ViewDefinition
from koo2.ui.views.base_view import BaseView


# ---------------------------------------------------------------------------
# RecordTableModel
# ---------------------------------------------------------------------------
class RecordTableModel(QAbstractTableModel):
    """Qt model that maps a list of Records to rows × columns."""

    def __init__(
        self,
        records: Optional[List[Record]] = None,
        columns: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._records: List[Record] = records or []
        self._columns: List[str] = columns or []
        self._headers: Dict[str, str] = headers or {}

    # ------------------------------------------------------------------
    # QAbstractTableModel overrides
    # ------------------------------------------------------------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        record = self._records[index.row()]
        field_name = self._columns[index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            value = record.get(field_name)
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.UserRole:
            return record
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            col = self._columns[section]
            return self._headers.get(col, col)
        return str(section + 1)

    def record_at(self, row: int) -> Optional[Record]:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def load_records(
        self,
        records: List[Record],
        columns: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.beginResetModel()
        self._records = records
        if columns is not None:
            self._columns = columns
        if headers is not None:
            self._headers = headers
        self.endResetModel()


# ---------------------------------------------------------------------------
# TreeView
# ---------------------------------------------------------------------------
class TreeView(BaseView):
    """MD3 table view for multiple records.

    Emits :attr:`row_activated` when the user double-clicks or presses Enter
    on a row, allowing the parent screen to open a FormView for editing.
    """

    row_activated = Signal(object)   # payload: Record

    def __init__(
        self,
        view_definition: Optional[ViewDefinition] = None,
        read_only: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            view_definition=view_definition,
            read_only=read_only,
            parent=parent,
        )
        self._table_model = RecordTableModel()
        self._build_ui()

    # ------------------------------------------------------------------
    # IView
    # ------------------------------------------------------------------
    def view_type(self) -> str:
        return "tree"

    def shows_multiple_records(self) -> bool:
        return True

    def display(self, record: Any, records: Any = None) -> None:
        super().display(record, records)
        record_list: List[Record] = []
        columns: List[str] = []
        headers: Dict[str, str] = {}

        if self._view_definition:
            columns = list(self._view_definition.fields.keys())
            headers = {
                name: fdef.string or name
                for name, fdef in self._view_definition.fields.items()
                if not fdef.invisible
            }
            columns = [c for c in columns if not self._view_definition.fields[c].invisible]

        if isinstance(records, list):
            record_list = [r for r in records if isinstance(r, Record)]
        elif isinstance(record, list):
            record_list = [r for r in record if isinstance(r, Record)]

        self._table_model.load_records(record_list, columns=columns, headers=headers)

    def selected_records(self) -> List[Record]:
        rows = {idx.row() for idx in self._table.selectedIndexes()}
        return [r for r in (self._table_model.record_at(row) for row in rows) if r]

    def start_editing(self) -> None:
        current = self._table.currentIndex()
        if current.isValid():
            self._table.edit(current)

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._table = QTableView(self)
        self._table.setModel(self._table_model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)

        self._table.activated.connect(self._on_activated)

        self._root_layout.addWidget(self._table)

    def _on_activated(self, index: QModelIndex) -> None:
        record = self._table_model.record_at(index.row())
        if record is not None:
            self.row_activated.emit(record)
