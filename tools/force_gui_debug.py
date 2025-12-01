"""Force a minimal Qt GUI to appear and capture any startup errors.

Run from project root with venv active:

  & .\.venv\Scripts\Activate.ps1
  $env:QT_DEBUG_PLUGINS='1'
  & .\.venv\Scripts\python.exe .\tools\force_gui_debug.py

This script writes `tools/force_gui_debug.log` with traceback or success message.
"""
import sys
import traceback
from pathlib import Path

LOG = Path(__file__).with_name('force_gui_debug.log')

def write(msg: str):
    try:
        LOG.write_text(msg, encoding='utf-8')
    except Exception:
        pass

def main():
    try:
        from PyQt6.QtWidgets import QApplication, QLabel
        app = QApplication(sys.argv)
        lbl = QLabel('If you see this window, Qt is creating windows correctly.')
        lbl.setWindowTitle('Force GUI Debug')
        lbl.resize(400, 120)
        lbl.show()
        write('SUCCESS: QApplication started and label shown.\n')
        # Run the event loop briefly (2 seconds) to ensure it appears
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, app.quit)
        app.exec()
        write('DONE: Event loop executed (2s)\n')
        print('SUCCESS: GUI shown briefly; see tools/force_gui_debug.log')
    except Exception as e:
        tb = traceback.format_exc()
        write('ERROR:\n' + tb)
        print('ERROR during GUI startup; traceback written to tools/force_gui_debug.log')
        print(tb)

if __name__ == '__main__':
    main()
