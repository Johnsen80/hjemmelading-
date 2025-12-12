"""
Standalone starter for Modern Reloading Workspace
"""

import sys

from PyQt6.QtWidgets import QApplication
from src.modules.modern_reloading_workspace import ModernReloadingWorkspace

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernReloadingWorkspace()
    window.show()
    sys.exit(app.exec())
