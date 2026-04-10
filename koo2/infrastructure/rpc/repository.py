"""
OpenErpRepository – IRepository implementation backed by OpenErpRpcClient.

One repository instance corresponds to one OpenERP model.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from koo2.core.domain.record import Record
from koo2.core.domain.view_definition import FieldDefinition, ViewDefinition
from koo2.infrastructure.rpc.openerp_client import OpenErpRpcClient


class OpenErpRepository:
    """Generic CRUD repository for a single OpenERP model.

    Usage::

        client = OpenErpRpcClient()
        client.login(url, db, user, password)
        repo = OpenErpRepository('res.partner', client)
        partners = repo.find([('is_company', '=', True)], limit=10)
    """

    def __init__(self, model_name: str, client: OpenErpRpcClient) -> None:
        self._model = model_name
        self._client = client

    @property
    def model_name(self) -> str:
        return self._model

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def find(
        self,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> List[Record]:
        ids = self._client.search(
            self._model,
            domain=domain,
            offset=offset,
            limit=limit,
            order=order,
            context=context,
        )
        if not ids:
            return []
        raw = self._client.read(self._model, ids, fields=fields, context=context)
        return [Record.from_server(self._model, row) for row in raw]

    def get(
        self,
        record_id: int,
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> Optional[Record]:
        rows = self._client.read(self._model, [record_id], fields=fields, context=context)
        if not rows:
            return None
        return Record.from_server(self._model, rows[0])

    def save(
        self,
        record: Record,
        context: Optional[Dict] = None,
    ) -> Record:
        """Persist *record* to the server; returns an updated Record."""
        if record.is_new:
            new_id = self._client.create(self._model, record.values, context=context)
            record.mark_saved(server_id=new_id)
        else:
            dirty = record.dirty_fields
            if dirty:
                self._client.write(self._model, [record.id], dirty, context=context)
            record.mark_saved()
        return record

    def delete(
        self,
        record_id: int,
        context: Optional[Dict] = None,
    ) -> None:
        self._client.unlink(self._model, [record_id], context=context)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    def get_field_definitions(
        self,
        context: Optional[Dict] = None,
    ) -> Dict[str, FieldDefinition]:
        raw = self._client.fields_get(self._model, context=context)
        return {
            name: FieldDefinition.from_server(name, data)
            for name, data in raw.items()
        }

    def get_view_definition(
        self,
        view_type: str = "form",
        view_id: Optional[int] = None,
        context: Optional[Dict] = None,
    ) -> ViewDefinition:
        raw = self._client.fields_view_get(
            self._model, view_id=view_id, view_type=view_type, context=context
        )
        return ViewDefinition.from_server(view_type, raw, model=self._model)
