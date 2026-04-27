import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT = 30


def _run_code(code: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=PROJECT_ROOT,
    )


def _lines(*parts: str) -> str:
    return "\n".join(parts)


@pytest.mark.core
def test_mainwindow_headless_smoke():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "instantiate_mainwindow_probe.py"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "MainWindow instantiated" in result.stdout


@pytest.mark.core
def test_mainwindow_can_open_modern_load_builder_headlessly():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = _lines(
        "from PyQt6.QtWidgets import QApplication, QDialog",
        "app = QApplication([])",
        "QDialog.exec = lambda self: 0",
        "from src.ui.main_window import MainWindow",
        "w = MainWindow()",
        "w.show_modern_load_builder()",
        "print('opened')",
        "w.close()",
        "app.processEvents()",
    )
    result = _run_code(code, env)
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip().splitlines()[-1] == "opened"


@pytest.mark.core
def test_construct_widget_forwards_kwargs():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = _lines(
        "from PyQt6.QtWidgets import QApplication, QWidget",
        "app = QApplication([])",
        "from src.ui.main_window import MainWindow",
        "class Dummy(QWidget):",
        "    def __init__(self, parent=None, batch_id=None):",
        "        super().__init__(parent)",
        "        self.batch_id = batch_id",
        "w = MainWindow()",
        "widget = w._construct_widget(Dummy, w, batch_id=42)",
        "print(widget.batch_id)",
        "w.close()",
        "app.processEvents()",
    )
    result = _run_code(code, env)
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip().splitlines()[-1] == "42"


@pytest.mark.core
def test_instantiate_factory_forwards_kwargs():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = _lines(
        "from PyQt6.QtWidgets import QApplication, QWidget",
        "app = QApplication([])",
        "from src.ui.main_window import MainWindow",
        "class Dummy(QWidget):",
        "    def __init__(self, parent=None, batch_id=None):",
        "        super().__init__(parent)",
        "        self.batch_id = batch_id",
        "widget = MainWindow._instantiate_factory(Dummy, None, batch_id=7)",
        "print(widget.batch_id)",
        "widget.close()",
        "app.processEvents()",
    )
    result = _run_code(code, env)
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip().splitlines()[-1] == "7"


@pytest.mark.core
def test_instantiate_factory_handles_positional_and_kwargs():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = _lines(
        "from PyQt6.QtWidgets import QApplication, QWidget",
        "app = QApplication([])",
        "from src.ui.main_window import MainWindow",
        "class Dummy(QWidget):",
        "    def __init__(self, state_manager, mode_manager, parent=None, defer_ui=False):",
        "        super().__init__(parent)",
        "        self.state_manager = state_manager",
        "        self.mode_manager = mode_manager",
        "        self.defer_ui = defer_ui",
        "widget = MainWindow._instantiate_factory(Dummy, QWidget(), 'state', 'mode', defer_ui=True)",
        "print(widget.state_manager, widget.mode_manager, widget.defer_ui)",
        "app.processEvents()",
    )
    result = _run_code(code, env)
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip().splitlines()[-1] == "state mode True"


@pytest.mark.core
def test_weapon_profile_editor_opens_with_mainwindow_parent():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = _lines(
        "from pathlib import Path",
        "from PyQt6.QtWidgets import QApplication",
        "app = QApplication([])",
        "from src.ui.main_window import MainWindow",
        "from src.ui.weapon_profile_editor import WeaponProfileEditor",
        "w = MainWindow()",
        "dlg = WeaponProfileEditor(data_path=Path('data/demo_weapons.json'), parent=w)",
        "print(type(w).__name__, type(dlg).__name__)",
        "dlg.close()",
        "w.close()",
        "app.processEvents()",
    )
    result = _run_code(code, env)
    assert result.returncode == 0, result.stderr or result.stdout
    assert result.stdout.strip().splitlines()[-1] == "MainWindow WeaponProfileEditor"


@pytest.mark.core
def test_weapon_profile_and_barrel_caliber_use_editable_library_combo():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = _lines(
        "from PyQt6.QtWidgets import QApplication",
        "app = QApplication([])",
        "from src.modules.weapon_profile_dialog import WeaponProfileDialog",
        "from src.ui.barrel_editor import BarrelEditorDialog",
        "weapon = WeaponProfileDialog()",
        "barrel = BarrelEditorDialog({'caliber': '6.5 Creedmoor'})",
        "print(type(weapon.caliber_edit).__name__, weapon.caliber_edit.isEditable(), type(barrel.caliber_edit).__name__, barrel.caliber_edit.isEditable(), barrel.caliber_edit.currentText())",
        "barrel.close()",
        "weapon.close()",
        "app.processEvents()",
    )
    result = _run_code(code, env)
    assert result.returncode == 0, result.stderr or result.stdout
    assert (
        result.stdout.strip().splitlines()[-1]
        == "QComboBox True QComboBox True 6.5 Creedmoor"
    )
