"""Run the Measurement Session UI dialog for manual testing.

This script creates a QApplication and shows the `MeasurementSessionDialog`.
Run it from the repo root with the project's Python environment.

Example:
  C:/.../.tool-venv/Scripts/python.exe tools/run_measurement_wizard.py
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.modules.measurement_wizard import MeasurementSessionDialog
from PyQt6.QtWidgets import QApplication


def main():
    app = QApplication.instance() or QApplication([])
    dlg = MeasurementSessionDialog()
    dlg.show()
    app.exec()


if __name__ == '__main__':
    main()
