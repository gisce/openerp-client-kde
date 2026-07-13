"""Load and normalize ERP menus/actions through the RPC interface."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from koo2.core.domain.action import ActionDefinition, MenuItem
from koo2.core.interfaces.rpc_client import IRpcClient


class ActionNotFoundError(Exception):
    """Raised when an action reference cannot be resolved."""


class UnsupportedActionError(Exception):
    """Raised when an action type is not executable by the new client yet."""


class ActionService:
    """Service that converts OpenERP action metadata into a stable contract."""

    MENU_FIELDS = ["name", "parent_id", "action", "sequence"]
    ACTION_FIELDS = [
        "name",
        "type",
        "res_model",
        "view_mode",
        "view_id",
        "domain",
        "context",
        "target",
        "report_name",
        "url",
    ]

    def __init__(self, rpc_client: IRpcClient) -> None:
        self._rpc = rpc_client

    def load_menus(
        self,
        root_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[MenuItem]:
        """Return the visible ERP menu tree ordered by sequence/name."""
        domain: List[Any] = []
        if root_id is not None:
            domain.append(("parent_id", "child_of", [root_id]))
        menu_ids = self._rpc.search(
            "ir.ui.menu",
            domain=domain,
            order="sequence,name",
            context=context,
        )
        rows = self._rpc.read(
            "ir.ui.menu",
            menu_ids,
            fields=self.MENU_FIELDS,
            context=context,
        )
        return self._build_menu_tree(rows, root_id=root_id)

    def resolve_action(
        self,
        action_ref: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ActionDefinition:
        """Resolve ``ir.actions.*`` references from menu metadata."""
        model, action_id = self._parse_action_ref(action_ref)
        rows = self._rpc.read(
            model,
            [action_id],
            fields=self.ACTION_FIELDS,
            context=context,
        )
        if not rows:
            raise ActionNotFoundError("Action %s,%s not found" % (model, action_id))
        return self._normalize_action(model, rows[0])

    def executable_kind(self, action: ActionDefinition) -> str:
        """Classify how the shell should execute *action*."""
        if action.opens_wizard:
            return "wizard"
        if action.opens_model:
            return "model"
        if action.opens_report:
            return "report"
        if action.opens_url:
            return "url"
        raise UnsupportedActionError("Unsupported action type: %s" % action.action_type)

    def _build_menu_tree(
        self,
        rows: Iterable[Dict[str, Any]],
        root_id: Optional[int] = None,
    ) -> List[MenuItem]:
        by_id: Dict[int, MenuItem] = {}
        child_ids: Dict[Optional[int], List[int]] = {}

        for row in rows:
            menu_id = int(row["id"])
            parent_id = self._many2one_id(row.get("parent_id"))
            by_id[menu_id] = MenuItem(
                id=menu_id,
                name=row.get("name", ""),
                parent_id=parent_id,
                action_ref=row.get("action") or "",
                sequence=int(row.get("sequence") or 0),
            )
            child_ids.setdefault(parent_id, []).append(menu_id)

        def attach(menu_id: int) -> MenuItem:
            menu = by_id[menu_id]
            children = [
                attach(child_id)
                for child_id in self._sort_ids(child_ids.get(menu_id, []), by_id)
            ]
            return MenuItem(
                id=menu.id,
                name=menu.name,
                parent_id=menu.parent_id,
                action_ref=menu.action_ref,
                sequence=menu.sequence,
                children=children,
            )

        if root_id is not None and root_id in by_id:
            roots = child_ids.get(root_id, [])
        else:
            row_ids = set(by_id)
            roots = [
                menu_id
                for menu_id, menu in by_id.items()
                if menu.parent_id not in row_ids or menu.parent_id == root_id
            ]
        return [attach(menu_id) for menu_id in self._sort_ids(roots, by_id)]

    def _sort_ids(self, ids: Iterable[int], by_id: Dict[int, MenuItem]) -> List[int]:
        return sorted(
            ids,
            key=lambda menu_id: (by_id[menu_id].sequence, by_id[menu_id].name),
        )

    def _normalize_action(self, model: str, row: Dict[str, Any]) -> ActionDefinition:
        action_type = row.get("type") or model
        return ActionDefinition(
            id=int(row["id"]),
            action_type=action_type,
            name=row.get("name", ""),
            model=row.get("res_model", ""),
            view_mode=row.get("view_mode", ""),
            view_id=self._many2one_id(row.get("view_id")),
            domain=row.get("domain"),
            context=row.get("context") or {},
            target=row.get("target") or "current",
            report_name=row.get("report_name", ""),
            url=row.get("url", ""),
            raw=dict(row),
        )

    def _parse_action_ref(self, action_ref: Any) -> Tuple[str, int]:
        if isinstance(action_ref, str):
            if "," not in action_ref:
                raise ActionNotFoundError("Invalid action reference: %s" % action_ref)
            model, raw_id = action_ref.split(",", 1)
            return model.strip(), int(raw_id)
        if isinstance(action_ref, (tuple, list)) and len(action_ref) >= 2:
            return str(action_ref[0]), int(action_ref[1])
        raise ActionNotFoundError("Invalid action reference: %r" % (action_ref,))

    def _many2one_id(self, value: Any) -> Optional[int]:
        if not value:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, (tuple, list)) and value:
            return int(value[0])
        return int(value)
