"""Contract tests for the new GISCE ERP Qt client direction.

These tests keep the draft PR honest: the new client must be tracked against
the legacy Koo feature surface, and it must not grow runtime dependencies on
the old ``Koo/`` package while it is being built as a replacement.
"""
from __future__ import annotations

import ast
import os
import re
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MATRIX_PATH = os.path.join(ROOT, "docs", "new_client_functionality_matrix.md")
NEW_CLIENT_DIR = os.path.join(ROOT, "koo2")


class TestNewClientFunctionalityMatrix(unittest.TestCase):
    REQUIRED_CAPABILITY_IDS = {
        "F01",
        "F02",
        "F03",
        "F04",
        "F05",
        "F06",
        "F07",
        "F08",
        "F09",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
    }

    def _matrix(self):
        with open(MATRIX_PATH, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_matrix_lists_required_legacy_replacement_capabilities(self):
        matrix = self._matrix()
        found = set(re.findall(r"\|\s*(F\d{2})\s*\|", matrix))
        self.assertEqual(self.REQUIRED_CAPABILITY_IDS, found)

    def test_matrix_declares_status_for_every_capability(self):
        matrix = self._matrix()
        rows = [
            line
            for line in matrix.splitlines()
            if re.match(r"\|\s*F\d{2}\s*\|", line)
        ]
        self.assertEqual(len(self.REQUIRED_CAPABILITY_IDS), len(rows))
        for row in rows:
            self.assertRegex(row, r"\|\s*(covered|partial|missing)\s*\|")

    def test_matrix_names_the_product_as_gisce_owned_client(self):
        matrix = self._matrix()
        self.assertIn("GISCE ERP Qt Client", matrix)


class TestNewClientLegacyIndependence(unittest.TestCase):
    def test_new_client_does_not_import_legacy_koo_modules(self):
        violations = []
        for dirname, _, filenames in os.walk(NEW_CLIENT_DIR):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = os.path.join(dirname, filename)
                with open(path, "r", encoding="utf-8") as fh:
                    tree = ast.parse(fh.read(), filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == "Koo" or alias.name.startswith("Koo."):
                                violations.append(self._rel(path))
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        if module == "Koo" or module.startswith("Koo."):
                            violations.append(self._rel(path))

        self.assertEqual([], sorted(set(violations)))

    def _rel(self, path):
        return os.path.relpath(path, ROOT)


if __name__ == "__main__":
    unittest.main()
