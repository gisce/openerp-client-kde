"""
conftest.py for koo2 tests.

Sets QT_QPA_PLATFORM=offscreen before any Qt imports so all widget tests
work in headless CI environments.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
