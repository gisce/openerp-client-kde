"""Domain objects for ERP menus and actions.

These objects are intentionally UI-neutral so QGIS, a Qt shell, or tests can
all consume the same normalized action contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MenuItem:
    """ERP menu entry with its optional action binding."""

    id: int
    name: str
    parent_id: Optional[int] = None
    action_ref: str = ""
    sequence: int = 0
    children: List["MenuItem"] = field(default_factory=list)


@dataclass(frozen=True)
class ActionDefinition:
    """Normalized ERP action returned by ``ir.actions.*`` metadata."""

    id: int
    action_type: str
    name: str = ""
    model: str = ""
    view_mode: str = ""
    view_id: Optional[int] = None
    domain: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    target: str = "current"
    report_name: str = ""
    url: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def opens_model(self) -> bool:
        return self.action_type == "ir.actions.act_window" and bool(self.model)

    @property
    def opens_wizard(self) -> bool:
        return self.opens_model and self.target in {"new", "inline"}

    @property
    def opens_report(self) -> bool:
        return self.action_type in {"ir.actions.report.xml", "ir.actions.report"}

    @property
    def opens_url(self) -> bool:
        return self.action_type == "ir.actions.act_url" and bool(self.url)
