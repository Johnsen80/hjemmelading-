import os
import sys

# Ensure project parent dir is on sys.path so tests can import package
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
PARENT = os.path.dirname(PROJECT_ROOT)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)
