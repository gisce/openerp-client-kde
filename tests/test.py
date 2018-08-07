import unittest
from Koo.Model.Field import *
from Koo.Model.Record import Record
from Koo.Model.Group import RecordGroup


class TestRecord(unittest.TestCase):
    def test_record_modified(self):
        """
        Tests that the record is modifed

        :return: None
        """
        rg = RecordGroup("res.partner")
        rec = Record(1, rg)
        self.assertFalse(rec.isModified())
        rec.set({"name": "hola"}, True, False)
        self.assertTrue(rec.isModified())

    def test_record_field_exist(self):
        """
        Test that fieldExists works

        :return:
        """
        rg = RecordGroup("res.partner", {"name": {"type": "char"}})
        rec = Record(1, rg)
        self.assertTrue(rec.fieldExists("name"))
        self.assertFalse(rec.fieldExists("fail"))

    def test_readonly(self):
        """
        Test readonly field works

        :return:
        """
        fields = {
            "name": {"type": "char", "readonly": True},
            "name2": {"type": "char", "readonly": "True"},
            "name_writable": {"type": "char", "readonly": False},
            "name_writable2": {"type": "char", "readonly": 'False'}
        }

        rg = RecordGroup("res.partner", fields)
        rec = Record(1, rg,)
        # Test isFieldReadOnly with boolean value
        self.assertTrue(rec.isFieldReadOnly("name"))
        self.assertFalse(rec.isFieldReadOnly("name_writeable"))

        # Test isFieldReadOnly with str value
        self.assertTrue(rec.isFieldReadOnly("name2"))
        self.assertFalse(rec.isFieldReadOnly("name_writable2"))

        # Checks if a non existing filed readonly is false
        self.assertFalse(rec.isFieldReadOnly("fail"))


    def test_required(self):
        """
        Test required field works

        :return:
        """
        fields = {
            "name_required": {"type": "char", "required": True},
            "name_required2": {"type": "char", "required": "True"},
            "name_no_required": {"type": "char", "required": False},
            "name_no_required2": {"type": "char", "required": 'False'}
        }

        rg = RecordGroup("res.partner", fields)
        rec = Record(1, rg,)
        # Test isFieldReadOnly with boolean value
        self.assertTrue(rec.isFieldRequired("name_required"))
        self.assertFalse(rec.isFieldRequired("name_no_required"))

        # Test isFieldReadOnly with str value
        self.assertTrue(rec.isFieldRequired("name_required"))
        self.assertFalse(rec.isFieldRequired("name_no_required2"))

        # Checks if a non existing filed readonly is false
        self.assertFalse(rec.isFieldRequired("fail"))

    def test_get(self):
        """
        Test the get method

        :return: None
        """

        fields = {
            "name": {"type": "char", "required": True},
        }

        rg = RecordGroup("res.partner", fields)
        rec = Record(1, rg)
        rec.set({"name": "ok"}, True, False)
        # To avoid to try to load from XML RPC connection
        rec._loaded = True
        self.assertDictEqual(rec.get(), {"name": "ok"})

    def test_defaults(self):
        """
        Tets the defaults

        :return: None
        """

        fields = {
            "name": {"type": "char", "required": True},
        }

        rg = RecordGroup("res.partner", fields)
        rec = Record(1, rg)
        defaults = {
            "name": "default value",
            "no_exists": "somthing"
        }
        rec.setDefaults(defaults)
        self.assertDictEqual(rec.defaults(), {"name": "default value"})
        self.assertEqual(rec.default("name"), "default value")

    def test_isFullyLoaded(self):
        """
        Test the function isFullyLoaded

        :return: None
        """
        fields = {
            "name": {"type": "char"},
        }

        rg = RecordGroup("res.partner", fields)
        rec = Record(1, rg)
        self.assertFalse(rec.isFullyLoaded())
        rec._loaded = True
        self.assertFalse(rec.isFullyLoaded())
        rec.set({"name": "ok"})
        self.assertTrue(rec.isFullyLoaded())

    def test_missingFields(self):
        """
        Test the function isFullyLoaded

        :return: None
        """
        fields = {
            "name": {"type": "char"},
        }

        rg = RecordGroup("res.partner", fields)
        rec = Record(1, rg)
        self.assertEqual(["name"], rec.missingFields())
        rec.set({"name": "ok"})
        self.assertEqual(rec.missingFields(), [])

    def test_value(self):
        """
        Tests the value function

        :return:
        """
        def empty_function(self):
            pass
        fields = {
            "name": {"type": "integer"},
        }
        rg = RecordGroup("res.partner", fields)

        rec = Record(1, rg)
        rg.records = [1]
        rg.ensureRecordLoaded = empty_function
        #rg.recordById(1).set(1, signal=False)
        rec.setValue("name", 1)

        rec.value("name")


if __name__ == '__main__':
    unittest.main()