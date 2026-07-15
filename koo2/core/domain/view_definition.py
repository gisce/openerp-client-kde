"""
FieldDefinition and ViewDefinition – parsed metadata from ``fields_get`` /
``fields_view_get``.

These are pure-Python value objects; they carry no Qt or RPC dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# FieldDefinition
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FieldDefinition:
    """Metadata for a single model field (from ``fields_get``)."""

    name: str
    field_type: str
    string: str = ""
    required: bool = False
    readonly: bool = False
    invisible: bool = False
    help: str = ""
    size: Optional[int] = None
    # Relational fields
    relation: Optional[str] = None
    # Selection fields
    selection: List[tuple] = field(default_factory=list)
    # Raw extras from the server (computed attrs, domain, etc.)
    attrs: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_server(cls, name: str, data: Dict[str, Any]) -> "FieldDefinition":
        """Build a FieldDefinition from a single ``fields_get`` entry."""
        return cls(
            name=name,
            field_type=data.get("type", "char"),
            string=data.get("string", name),
            required=bool(data.get("required", False)),
            readonly=bool(data.get("readonly", False)),
            invisible=bool(data.get("invisible", False)),
            help=data.get("help", ""),
            size=data.get("size"),
            relation=data.get("relation"),
            selection=list(data.get("selection") or []),
            attrs={
                k: v
                for k, v in data.items()
                if k
                not in {
                    "type",
                    "string",
                    "required",
                    "readonly",
                    "invisible",
                    "help",
                    "size",
                    "relation",
                    "selection",
                }
            },
        )

    @property
    def is_relational(self) -> bool:
        return self.field_type in {"many2one", "one2many", "many2many"}


# ---------------------------------------------------------------------------
# ViewDefinition
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ViewDefinition:
    """Parsed view definition (from ``fields_view_get``)."""

    view_type: str
    arch: str
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    view_id: Optional[int] = None
    model: str = ""

    @classmethod
    def from_server(
        cls,
        view_type: str,
        data: Dict[str, Any],
        model: str = "",
    ) -> "ViewDefinition":
        """Build a ViewDefinition from a ``fields_view_get`` response."""
        raw_fields: Dict[str, Dict] = data.get("fields", {})
        parsed_fields = {
            name: FieldDefinition.from_server(name, fdata)
            for name, fdata in raw_fields.items()
        }
        return cls(
            view_type=view_type,
            arch=data.get("arch", ""),
            fields=parsed_fields,
            view_id=data.get("view_id"),
            model=model or data.get("model", ""),
        )
