from __future__ import annotations

import unittest

from koo2.core.services.action_service import (
    ActionNotFoundError,
    ActionService,
    UnsupportedActionError,
)


class FakeRpcClient:
    def __init__(self):
        self.calls = []
        self.menu_rows = [
            {
                "id": 10,
                "name": "Sales",
                "parent_id": False,
                "action": False,
                "sequence": 20,
            },
            {
                "id": 11,
                "name": "Customers",
                "parent_id": [10, "Sales"],
                "action": "ir.actions.act_window,101",
                "sequence": 5,
            },
            {
                "id": 12,
                "name": "Invoices",
                "parent_id": [10, "Sales"],
                "action": "ir.actions.report.xml,201",
                "sequence": 10,
            },
        ]
        self.actions = {
            ("ir.actions.act_window", 101): {
                "id": 101,
                "name": "Customers",
                "type": "ir.actions.act_window",
                "res_model": "res.partner",
                "view_mode": "tree,form",
                "view_id": [33, "Partner tree"],
                "domain": [("customer", "=", True)],
                "context": {"search_default_customer": 1},
                "target": "current",
            },
            ("ir.actions.act_window", 102): {
                "id": 102,
                "name": "Payment Wizard",
                "type": "ir.actions.act_window",
                "res_model": "account.payment.wizard",
                "view_mode": "form",
                "target": "new",
            },
            ("ir.actions.report.xml", 201): {
                "id": 201,
                "name": "Invoice PDF",
                "type": "ir.actions.report.xml",
                "report_name": "account.invoice",
            },
            ("ir.actions.act_url", 301): {
                "id": 301,
                "name": "External map",
                "type": "ir.actions.act_url",
                "url": "https://example.invalid/map",
            },
        }

    def search(self, model, domain=None, offset=0, limit=None, order=None, context=None):
        self.calls.append(("search", model, domain, order, context))
        if model == "ir.ui.menu":
            return [row["id"] for row in self.menu_rows]
        return []

    def read(self, model, ids, fields=None, context=None):
        self.calls.append(("read", model, ids, fields, context))
        if model == "ir.ui.menu":
            return [row for row in self.menu_rows if row["id"] in ids]
        return [
            self.actions[(model, action_id)]
            for action_id in ids
            if (model, action_id) in self.actions
        ]

    def login(self, url, database, username, password):
        return True

    def logout(self):
        pass

    @property
    def is_logged_in(self):
        return True

    def write(self, model, ids, values, context=None):
        return True

    def create(self, model, values, context=None):
        return 1

    def unlink(self, model, ids, context=None):
        return True

    def execute(self, model, method, *args, context=None):
        return None

    def fields_get(self, model, fields=None, context=None):
        return {}

    def fields_view_get(self, model, view_id=None, view_type="form", context=None):
        return {}


class TestActionServiceMenus(unittest.TestCase):
    def test_load_menus_builds_ordered_tree(self):
        service = ActionService(FakeRpcClient())

        menus = service.load_menus()

        self.assertEqual(["Sales"], [menu.name for menu in menus])
        self.assertEqual(
            ["Customers", "Invoices"],
            [menu.name for menu in menus[0].children],
        )
        self.assertEqual("ir.actions.act_window,101", menus[0].children[0].action_ref)

    def test_load_menus_uses_root_domain_when_requested(self):
        rpc = FakeRpcClient()
        service = ActionService(rpc)

        service.load_menus(root_id=10, context={"lang": "ca_ES"})

        self.assertEqual(
            (
                "search",
                "ir.ui.menu",
                [("parent_id", "child_of", [10])],
                "sequence,name",
                {"lang": "ca_ES"},
            ),
            rpc.calls[0],
        )


class TestActionServiceResolution(unittest.TestCase):
    def test_resolve_window_action(self):
        service = ActionService(FakeRpcClient())

        action = service.resolve_action("ir.actions.act_window,101")

        self.assertEqual("Customers", action.name)
        self.assertEqual("res.partner", action.model)
        self.assertEqual("tree,form", action.view_mode)
        self.assertEqual(33, action.view_id)
        self.assertTrue(action.opens_model)
        self.assertEqual("model", service.executable_kind(action))

    def test_resolve_wizard_action(self):
        service = ActionService(FakeRpcClient())

        action = service.resolve_action(("ir.actions.act_window", 102))

        self.assertTrue(action.opens_wizard)
        self.assertEqual("wizard", service.executable_kind(action))

    def test_resolve_report_action(self):
        service = ActionService(FakeRpcClient())

        action = service.resolve_action("ir.actions.report.xml,201")

        self.assertEqual("account.invoice", action.report_name)
        self.assertTrue(action.opens_report)
        self.assertEqual("report", service.executable_kind(action))

    def test_resolve_url_action(self):
        service = ActionService(FakeRpcClient())

        action = service.resolve_action("ir.actions.act_url,301")

        self.assertEqual("https://example.invalid/map", action.url)
        self.assertTrue(action.opens_url)
        self.assertEqual("url", service.executable_kind(action))

    def test_missing_action_raises(self):
        service = ActionService(FakeRpcClient())

        with self.assertRaises(ActionNotFoundError):
            service.resolve_action("ir.actions.act_window,999")

    def test_unsupported_action_raises(self):
        service = ActionService(FakeRpcClient())
        action = service.resolve_action("ir.actions.act_window,101")
        broken = action.__class__(id=1, action_type="ir.actions.client")

        with self.assertRaises(UnsupportedActionError):
            service.executable_kind(broken)


if __name__ == "__main__":
    unittest.main()
