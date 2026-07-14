import unittest

from koo2.core.domain.record import Record
from koo2.core.services.record_lifecycle_service import (
    RecordLifecycleError,
    RecordLifecycleService,
)


class FakeRepository:
    def __init__(self):
        self.model_name = "res.partner"
        self.records = {
            1: {"id": 1, "name": "ACME", "email": "acme@example.test"},
        }
        self.next_id = 10
        self.saved = []
        self.deleted = []

    def get(self, record_id, fields=None, context=None):
        data = self.records.get(record_id)
        if data is None:
            return None
        if fields:
            filtered = {"id": record_id}
            for name in fields:
                if name in data:
                    filtered[name] = data[name]
            data = filtered
        return Record.from_server(self.model_name, data)

    def save(self, record, context=None):
        if record.is_new:
            record_id = self.next_id
            self.next_id += 1
            self.records[record_id] = dict(record.values, id=record_id)
            record.mark_saved(server_id=record_id)
            self.saved.append(("create", record_id, dict(record.values), context))
            return record

        self.records[record.id].update(record.dirty_fields)
        self.saved.append(("write", record.id, dict(record.dirty_fields), context))
        record.mark_saved()
        return record

    def delete(self, record_id, context=None):
        self.deleted.append((record_id, context))
        self.records.pop(record_id, None)


class RecordLifecycleServiceTest(unittest.TestCase):
    def setUp(self):
        self.repo = FakeRepository()
        self.service = RecordLifecycleService(self.repo)

    def test_new_record_uses_repository_model(self):
        record = self.service.new({"name": "New"})

        self.assertEqual(record.model, "res.partner")
        self.assertTrue(record.is_new)
        self.assertEqual(record.get("name"), "New")

    def test_load_returns_clean_record(self):
        record = self.service.load(1)

        self.assertEqual(record.id, 1)
        self.assertFalse(record.is_modified)

    def test_load_missing_record_raises_domain_error(self):
        with self.assertRaises(RecordLifecycleError):
            self.service.load(404)

    def test_save_new_record_creates_and_marks_saved(self):
        record = self.service.new({"name": "Created"})

        saved = self.service.save(record, context={"lang": "ca_ES"})

        self.assertIs(saved, record)
        self.assertEqual(record.id, 10)
        self.assertFalse(record.is_new)
        self.assertFalse(record.is_modified)
        self.assertEqual(self.repo.saved[0][0], "create")
        self.assertEqual(self.repo.saved[0][3], {"lang": "ca_ES"})

    def test_save_modified_record_writes_dirty_fields_only(self):
        record = self.service.load(1)
        record.set("name", "Changed")

        self.service.save(record)

        self.assertEqual(self.repo.saved[0][0], "write")
        self.assertEqual(self.repo.saved[0][2], {"name": "Changed"})
        self.assertFalse(record.is_modified)

    def test_save_clean_existing_record_does_not_write(self):
        record = self.service.load(1)

        self.service.save(record)

        self.assertEqual(self.repo.saved, [])

    def test_delete_saved_record_removes_it(self):
        record = self.service.load(1)

        self.service.delete(record)

        self.assertEqual(self.repo.deleted, [(1, None)])
        self.assertNotIn(1, self.repo.records)

    def test_delete_unsaved_record_raises(self):
        with self.assertRaises(RecordLifecycleError):
            self.service.delete(self.service.new())

    def test_duplicate_returns_unsaved_copy_without_id(self):
        record = self.service.load(1)

        duplicate = self.service.duplicate(record, overrides={"name": "ACME copy"})

        self.assertIsNone(duplicate.id)
        self.assertTrue(duplicate.is_new)
        self.assertEqual(duplicate.get("name"), "ACME copy")
        self.assertNotIn("id", duplicate.values)

    def test_discard_reverts_changes(self):
        record = self.service.load(1)
        record.set("name", "Temporary")

        self.service.discard(record)

        self.assertEqual(record.get("name"), "ACME")
        self.assertFalse(record.is_modified)

    def test_reload_fetches_fresh_server_state(self):
        record = self.service.load(1)
        self.repo.records[1]["name"] = "Server value"

        reloaded = self.service.reload(record)

        self.assertEqual(reloaded.get("name"), "Server value")
        self.assertFalse(reloaded.is_modified)

    def test_reload_unsaved_record_raises(self):
        with self.assertRaises(RecordLifecycleError):
            self.service.reload(self.service.new())

    def test_rejects_record_from_other_model(self):
        record = Record.from_server("res.users", {"id": 1, "name": "Admin"})

        with self.assertRaises(RecordLifecycleError):
            self.service.save(record)


if __name__ == "__main__":
    unittest.main()
