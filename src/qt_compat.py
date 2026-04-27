from __future__ import annotations

import os
import sys
from types import ModuleType


def _candidate_order() -> list[str]:
    env_choice = (
        os.environ.get("HJEMMELADING_QT_API") or os.environ.get("QT_API") or ""
    ).strip()
    if env_choice in {"PyQt6", "PySide6"}:
        other = "PySide6" if env_choice == "PyQt6" else "PyQt6"
        return [env_choice, other]

    loaded: list[str] = []
    for name in ("PyQt6", "PySide6"):
        if name in sys.modules:
            loaded.append(name)
    if loaded:
        return loaded + [name for name in ("PyQt6", "PySide6") if name not in loaded]

    return ["PyQt6", "PySide6"]


def _import_binding() -> tuple[str, ModuleType, ModuleType, ModuleType]:
    last_error: Exception | None = None
    for name in _candidate_order():
        try:
            qt_core = __import__(f"{name}.QtCore", fromlist=["QtCore"])
            qt_gui = __import__(f"{name}.QtGui", fromlist=["QtGui"])
            qt_widgets = __import__(f"{name}.QtWidgets", fromlist=["QtWidgets"])
            return name, qt_core, qt_gui, qt_widgets
        except Exception as exc:
            last_error = exc
    raise RuntimeError("Neither PyQt6 nor PySide6 could be imported") from last_error


BINDING, QtCore, QtGui, QtWidgets = _import_binding()

Qt = getattr(QtCore, "Qt", None)
Signal = getattr(QtCore, "pyqtSignal", None) or getattr(QtCore, "Signal", None)
QSettings = getattr(QtCore, "QSettings", None)
QPoint = getattr(QtCore, "QPoint", None)
QSize = getattr(QtCore, "QSize", None)
QTimer = getattr(QtCore, "QTimer", None)
QUrl = getattr(QtCore, "QUrl", None)
QAction = getattr(QtGui, "QAction", None)
QDesktopServices = getattr(QtGui, "QDesktopServices", None)
QGuiApplication = getattr(QtGui, "QGuiApplication", None)
QIcon = getattr(QtGui, "QIcon", None)
QKeySequence = getattr(QtGui, "QKeySequence", None)
QMouseEvent = getattr(QtGui, "QMouseEvent", None)
QPixmap = getattr(QtGui, "QPixmap", None)
QFont = getattr(QtGui, "QFont", None)
QColor = getattr(QtGui, "QColor", None)
QApplication = getattr(QtWidgets, "QApplication", None)
QCheckBox = getattr(QtWidgets, "QCheckBox", None)
QComboBox = getattr(QtWidgets, "QComboBox", None)
QCompleter = getattr(QtWidgets, "QCompleter", None)
QDialog = getattr(QtWidgets, "QDialog", None)
QDoubleSpinBox = getattr(QtWidgets, "QDoubleSpinBox", None)
QFileDialog = getattr(QtWidgets, "QFileDialog", None)
QFrame = getattr(QtWidgets, "QFrame", None)
QFormLayout = getattr(QtWidgets, "QFormLayout", None)
QGroupBox = getattr(QtWidgets, "QGroupBox", None)
QHBoxLayout = getattr(QtWidgets, "QHBoxLayout", None)
QHeaderView = getattr(QtWidgets, "QHeaderView", None)
QLabel = getattr(QtWidgets, "QLabel", None)
QLineEdit = getattr(QtWidgets, "QLineEdit", None)
QListWidget = getattr(QtWidgets, "QListWidget", None)
QMainWindow = getattr(QtWidgets, "QMainWindow", None)
QMenu = getattr(QtWidgets, "QMenu", None)
QMessageBox = getattr(QtWidgets, "QMessageBox", None)
QProgressBar = getattr(QtWidgets, "QProgressBar", None)
QPushButton = getattr(QtWidgets, "QPushButton", None)
QRadioButton = getattr(QtWidgets, "QRadioButton", None)
QScrollArea = getattr(QtWidgets, "QScrollArea", None)
QSizePolicy = getattr(QtWidgets, "QSizePolicy", None)
QSplitter = getattr(QtWidgets, "QSplitter", None)
QSpinBox = getattr(QtWidgets, "QSpinBox", None)
QStackedWidget = getattr(QtWidgets, "QStackedWidget", None)
QStatusBar = getattr(QtWidgets, "QStatusBar", None)
QTableWidget = getattr(QtWidgets, "QTableWidget", None)
QTableWidgetItem = getattr(QtWidgets, "QTableWidgetItem", None)
QTabWidget = getattr(QtWidgets, "QTabWidget", None)
QTextEdit = getattr(QtWidgets, "QTextEdit", None)
QVBoxLayout = getattr(QtWidgets, "QVBoxLayout", None)
QWidget = getattr(QtWidgets, "QWidget", None)
QWizard = getattr(QtWidgets, "QWizard", None)
QWizardPage = getattr(QtWidgets, "QWizardPage", None)

__all__ = [
    "QAction",
    "QApplication",
    "BINDING",
    "QComboBox",
    "QCompleter",
    "QDesktopServices",
    "QDialog",
    "QFileDialog",
    "QFont",
    "QFrame",
    "QFormLayout",
    "QGroupBox",
    "QGuiApplication",
    "QHBoxLayout",
    "QHeaderView",
    "QIcon",
    "QKeySequence",
    "QLabel",
    "QLineEdit",
    "QListWidget",
    "QMainWindow",
    "QMenu",
    "QMouseEvent",
    "QMessageBox",
    "QPixmap",
    "QPoint",
    "QPushButton",
    "QRadioButton",
    "QSize",
    "QStackedWidget",
    "QStatusBar",
    "QSettings",
    "Signal",
    "QTableWidget",
    "QTableWidgetItem",
    "QTabWidget",
    "QTextEdit",
    "QTimer",
    "QUrl",
    "QVBoxLayout",
    "QWidget",
    "QWizard",
    "QWizardPage",
    "Qt",
    "QtCore",
    "QtGui",
    "QtWidgets",
]
