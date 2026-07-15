"""Backward-compatible import path for the default ERP RPC client.

The new Qt6 client must not depend on the legacy ``Koo.Rpc`` transport.  Keep
``OpenErpRpcClient`` as a temporary name for callers already using this module,
but back it with the standalone erppeek implementation.
"""
from __future__ import annotations

from koo2.infrastructure.rpc.erppeek_client import (  # noqa: F401
    ErppeekRpcClient,
    RpcAuthError,
    RpcError,
)


class OpenErpRpcClient(ErppeekRpcClient):
    """Compatibility alias for the standalone erppeek-backed RPC client."""
