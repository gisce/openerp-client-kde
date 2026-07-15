"""Tests for the legacy ``openerp_client`` import path.

The import path is kept during the draft PR, but it must resolve to the new
standalone erppeek transport instead of delegating to ``Koo.Rpc``.
"""
from __future__ import annotations

import sys
import unittest

from koo2.infrastructure.rpc.erppeek_client import (
    ErppeekRpcClient,
    RpcAuthError as ErppeekRpcAuthError,
    RpcError as ErppeekRpcError,
)
from koo2.infrastructure.rpc.openerp_client import (
    OpenErpRpcClient,
    RpcAuthError,
    RpcError,
)


class TestOpenErpClientImportPath(unittest.TestCase):
    def test_openerp_client_uses_standalone_erppeek_transport(self):
        client = OpenErpRpcClient()

        self.assertIsInstance(client, ErppeekRpcClient)

    def test_error_classes_are_shared_with_erppeek_transport(self):
        self.assertIs(RpcError, ErppeekRpcError)
        self.assertIs(RpcAuthError, ErppeekRpcAuthError)

    def test_importing_openerp_client_does_not_import_legacy_koo_modules(self):
        imported_koo_modules = [
            name for name in sys.modules if name == "Koo" or name.startswith("Koo.")
        ]

        self.assertEqual([], imported_koo_modules)


if __name__ == "__main__":
    unittest.main()
