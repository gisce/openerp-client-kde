"""
view_parser/nodes.py — Pure-Python node tree produced by FormParser / TreeParser.

Mirrors the ooui.js class hierarchy (Widget → Container → Field, Button, …)
but as frozen dataclasses so tests can construct trees without any Qt or RPC
dependency.

ooui.js reference
-----------------
Widget          → WidgetNode
Container       → ContainerNode
Field           → FieldNode
Button          → ButtonNode
Notebook        → NotebookNode
Page            → PageNode
Group           → GroupNode
Label           → LabelNode
Separator       → SeparatorNode
NewLine         → NewLineNode
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class WidgetNode:
    """Base node — mirrors ooui Widget."""

    type: str = ""
    colspan: int = 1
    read_only: bool = False
    invisible: bool = False
    required: bool = False
    # Raw attributes from the XML (available to the renderer for anything
    # not captured by the typed fields above).
    attrs: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Container (maps to ooui Container)
# ---------------------------------------------------------------------------

@dataclass
class ContainerNode(WidgetNode):
    """A grid container with *columns* columns.

    *rows* is a list of rows; each row is a list of WidgetNode instances
    (including ContainerNode subclasses).  The FormParser fills this while
    walking the XML tree.
    """

    type: str = "container"
    columns: int = 4
    rows: List[List[WidgetNode]] = field(default_factory=list)

    def add_widget(self, widget: WidgetNode) -> None:
        """Append *widget* to the last row, or start a new one."""
        if not self.rows:
            self.rows.append([])
        self.rows[-1].append(widget)

    def new_row(self) -> None:
        self.rows.append([])


# ---------------------------------------------------------------------------
# Field (maps to ooui Field)
# ---------------------------------------------------------------------------

@dataclass
class FieldNode(WidgetNode):
    """A model field rendered as an editable or read-only widget."""

    type: str = "field"
    name: str = ""
    string: str = ""
    field_type: str = "char"   # char, integer, float, boolean, many2one, …
    widget_hint: str = ""      # explicit widget= override in the view XML
    help: str = ""
    nolabel: bool = False
    on_change: str = ""
    domain: str = ""
    context: str = ""
    selection: List[tuple] = field(default_factory=list)
    relation: str = ""


# ---------------------------------------------------------------------------
# Button (maps to ooui Button)
# ---------------------------------------------------------------------------

@dataclass
class ButtonNode(WidgetNode):
    """An action button."""

    type: str = "button"
    name: str = ""
    string: str = ""
    button_type: str = "object"   # object | workflow | action
    confirm: str = ""
    icon: str = ""
    states: str = ""


# ---------------------------------------------------------------------------
# Label (maps to ooui Label)
# ---------------------------------------------------------------------------

@dataclass
class LabelNode(WidgetNode):
    """A static label."""

    type: str = "label"
    string: str = ""
    name: str = ""   # optional: references the field whose label this is


# ---------------------------------------------------------------------------
# Separator
# ---------------------------------------------------------------------------

@dataclass
class SeparatorNode(WidgetNode):
    """A horizontal (or vertical) visual separator."""

    type: str = "separator"
    string: str = ""
    orientation: str = "horizontal"


# ---------------------------------------------------------------------------
# NewLine
# ---------------------------------------------------------------------------

@dataclass
class NewLineNode(WidgetNode):
    """Forces a new row in the grid layout."""

    type: str = "newline"
    colspan: int = 0


# ---------------------------------------------------------------------------
# Group (maps to ooui Group)
# ---------------------------------------------------------------------------

@dataclass
class GroupNode(WidgetNode):
    """A named group box that contains its own ContainerNode."""

    type: str = "group"
    string: str = ""
    container: ContainerNode = field(default_factory=ContainerNode)


# ---------------------------------------------------------------------------
# Notebook / Page (maps to ooui Notebook / Page)
# ---------------------------------------------------------------------------

@dataclass
class PageNode(WidgetNode):
    """A single tab inside a Notebook."""

    type: str = "page"
    string: str = ""
    container: ContainerNode = field(default_factory=ContainerNode)


@dataclass
class NotebookNode(WidgetNode):
    """A tab widget containing PageNode children."""

    type: str = "notebook"
    pages: List[PageNode] = field(default_factory=list)
