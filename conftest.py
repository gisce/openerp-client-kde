"""
Root conftest.py – add the project root to sys.path so that both `Koo`
and `koo2` packages are importable from the tests directory.
"""
import os
import sys

# Ensure the project root is on the Python path
ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
