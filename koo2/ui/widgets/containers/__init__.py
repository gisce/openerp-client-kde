"""Container widgets: FormGrid, GroupWidget, NotebookWidget."""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QTabWidget,
    QWidget,
    QVBoxLayout,
)


class FormGrid(QWidget):
    """Grid layout container mirroring ooui Container (columns + colspan).

    The ERP form XML defines a number of columns (``col`` attribute).  Each
    child widget occupies *colspan* columns (default 1).  When a row is full
    (total colspan == columns) the next widget starts a new row.
    """

    def __init__(self, columns: int = 4, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._columns = columns
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(8)
        self._grid.setVerticalSpacing(4)
        self._current_row = 0
        self._current_col = 0

    def add_widget(self, widget: QWidget, colspan: int = 1) -> None:
        """Place *widget* in the grid, advancing columns/rows automatically."""
        colspan = max(1, min(colspan, self._columns))
        if self._current_col + colspan > self._columns:
            self._current_row += 1
            self._current_col = 0
        self._grid.addWidget(widget, self._current_row, self._current_col, 1, colspan)
        self._current_col += colspan

    def new_row(self) -> None:
        """Force a row break (mirrors ooui NewLine)."""
        if self._current_col > 0:
            self._current_row += 1
            self._current_col = 0


class GroupWidget(QGroupBox):
    """Named group box — mirrors ooui Group.

    Contains a :class:`FormGrid` that callers populate via
    :attr:`inner_grid`.
    """

    def __init__(
        self,
        title: str = "",
        columns: int = 4,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(title, parent)
        self._inner = FormGrid(columns=columns, parent=self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.addWidget(self._inner)

    @property
    def inner_grid(self) -> FormGrid:
        return self._inner


class NotebookWidget(QTabWidget):
    """Tab widget — mirrors ooui Notebook.

    Each tab is a :class:`FormGrid`; callers access them via
    :meth:`add_page` which returns the inner grid.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

    def add_page(self, title: str, columns: int = 4) -> FormGrid:
        """Add a new tab with *title* and return its inner :class:`FormGrid`."""
        grid = FormGrid(columns=columns)
        self.addTab(grid, title)
        return grid
