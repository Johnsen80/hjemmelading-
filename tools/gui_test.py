import sys
import traceback
from pathlib import Path

logfile = Path('gui_test_log.txt')

try:
    with open(logfile, 'w', encoding='utf-8') as f:
        f.write('Starting GUI test...\n')
    from PyQt6.QtWidgets import QApplication, QLabel
    from PyQt6.QtCore import QTimer

    app = QApplication(sys.argv)
    lbl = QLabel('GUI test: If you see this window, Qt works. Close to exit.')
    lbl.setWindowTitle('GUI Test')
    lbl.resize(480, 120)
    lbl.show()

    # Also write to log after show
    with open(logfile, 'a', encoding='utf-8') as f:
        f.write('Window shown (show() called)\n')

    # Ensure we exit after 20 seconds in case window is hidden
    QTimer.singleShot(20000, app.quit)
    code = app.exec()
    with open(logfile, 'a', encoding='utf-8') as f:
        f.write(f'Event loop exited with code: {code}\n')
    print('GUI test finished, wrote gui_test_log.txt')
except Exception as e:
    tb = traceback.format_exc()
    with open(logfile, 'a', encoding='utf-8') as f:
        f.write('Exception during GUI test:\n')
        f.write(tb + '\n')
    print('GUI test failed, see gui_test_log.txt')
    raise
