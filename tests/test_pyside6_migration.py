#!/usr/bin/env python3
"""
Tests to verify the PySide6 migration is complete and correct.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestPySide6Imports(unittest.TestCase):
    """Verify that all core Koo modules import PySide6 correctly."""

    def test_pyside6_available(self):
        """PySide6 must be importable."""
        import PySide6
        self.assertIsNotNone(PySide6.__version__)

    def test_pyside6_core(self):
        """PySide6.QtCore must be importable with Signal/Slot."""
        from PySide6.QtCore import Signal, Slot, QObject
        self.assertTrue(callable(Signal))
        self.assertTrue(callable(Slot))

    def test_no_pyqt5_in_koo_model_field(self):
        """Koo.Model.Field must not import PyQt5."""
        import importlib
        import ast
        import os
        field_path = os.path.join(
            os.path.dirname(__file__), '..', 'Koo', 'Model', 'Field.py')
        with open(field_path) as f:
            source = f.read()
        self.assertNotIn('PyQt5', source,
                         'Field.py still references PyQt5')
        self.assertIn('PySide6', source,
                      'Field.py should reference PySide6')

    def test_no_pyqt5_in_koo_model_record(self):
        """Koo.Model.Record must not import PyQt5."""
        import os
        record_path = os.path.join(
            os.path.dirname(__file__), '..', 'Koo', 'Model', 'Record.py')
        with open(record_path) as f:
            source = f.read()
        self.assertNotIn('PyQt5', source,
                         'Record.py still references PyQt5')

    def test_no_pyqt5_in_koo_model_group(self):
        """Koo.Model.Group must not import PyQt5."""
        import os
        group_path = os.path.join(
            os.path.dirname(__file__), '..', 'Koo', 'Model', 'Group.py')
        with open(group_path) as f:
            source = f.read()
        self.assertNotIn('PyQt5', source,
                         'Group.py still references PyQt5')

    def test_signal_used_instead_of_pyqtsignal(self):
        """Signal() should be used instead of pyqtSignal() everywhere in Koo."""
        import os
        import glob
        koo_dir = os.path.join(os.path.dirname(__file__), '..', 'Koo')
        py_files = glob.glob(os.path.join(koo_dir, '**', '*.py'), recursive=True)
        violations = []
        for f in py_files:
            with open(f) as fh:
                content = fh.read()
            if 'pyqtSignal' in content:
                violations.append(f.replace(koo_dir, 'Koo'))
        self.assertEqual([], violations,
                         'These files still use pyqtSignal: %s' % violations)

    def test_slot_used_instead_of_pyqtslot(self):
        """Slot() should be used instead of pyqtSlot() everywhere in Koo."""
        import os
        import glob
        koo_dir = os.path.join(os.path.dirname(__file__), '..', 'Koo')
        py_files = glob.glob(os.path.join(koo_dir, '**', '*.py'), recursive=True)
        violations = []
        for f in py_files:
            with open(f) as fh:
                content = fh.read()
            if 'pyqtSlot' in content:
                violations.append(f.replace(koo_dir, 'Koo'))
        self.assertEqual([], violations,
                         'These files still use pyqtSlot: %s' % violations)

    def test_no_pyqt5_imports_in_koo(self):
        """No Koo source file should import from PyQt5."""
        import os
        import glob
        koo_dir = os.path.join(os.path.dirname(__file__), '..', 'Koo')
        py_files = glob.glob(os.path.join(koo_dir, '**', '*.py'), recursive=True)
        violations = []
        for f in py_files:
            with open(f) as fh:
                content = fh.read()
            if 'from PyQt5' in content or 'import PyQt5' in content:
                violations.append(f.replace(koo_dir, 'Koo'))
        self.assertEqual([], violations,
                         'These files still import from PyQt5: %s' % violations)

    def test_requirements_uses_pyside6(self):
        """requirements.txt must reference PySide6, not PyQt5."""
        import os
        req_path = os.path.join(
            os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path) as f:
            content = f.read()
        self.assertIn('PySide6', content,
                      'requirements.txt must list PySide6')
        self.assertNotIn('PyQt5', content,
                         'requirements.txt must not list PyQt5')
        self.assertNotIn('PyQtWebKit', content,
                         'requirements.txt must not list PyQtWebKit')

    def test_model_imports_pyside6(self):
        """Key Koo model modules must import from PySide6."""
        from Koo.Model import Field, Record, Group
        # If they import without error, PySide6 is being used
        self.assertIsNotNone(Field)
        self.assertIsNotNone(Record)
        self.assertIsNotNone(Group)

    def test_signal_declared_with_pyside6(self):
        """Signal objects in model classes must be PySide6 Signals."""
        from PySide6.QtCore import Signal
        from Koo.Model.Record import Record
        from Koo.Model.Group import RecordGroup
        # Check that recordChanged is a Signal descriptor (not pyqtSignal)
        self.assertIsInstance(Record.recordChanged, Signal)
        self.assertIsInstance(RecordGroup.recordsInserted, Signal)


if __name__ == '__main__':
    unittest.main()
