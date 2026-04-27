"""Quick test script for Rifle Profile Editor with beginner/expert mode."""

import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

if __name__ != "__main__":
    _run_ui_tests = os.environ.get("RUN_UI_TESTS", "").lower() in ("1", "true", "yes")
    if not _run_ui_tests:
        import pytest

        pytest.skip(
            "Legacy UI tests are manual. Set RUN_UI_TESTS=1 to enable.",
            allow_module_level=True,
        )

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from src.modules.rifle_profile_editor import RifleProfileEditor


def _run_editor(user_mode: str, run_event_loop: bool) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    editor = RifleProfileEditor(user_mode=user_mode)
    editor.show()
    if run_event_loop:
        QTimer.singleShot(200, editor.close)
        QTimer.singleShot(250, app.quit)
        app.exec()
    else:
        app.processEvents()
        editor.close()
        app.processEvents()


def test_beginner_mode() -> None:
    """Smoke test in beginner mode."""
    _run_editor("beginner", run_event_loop=False)


def test_expert_mode() -> None:
    """Smoke test in expert mode."""
    _run_editor("expert", run_event_loop=False)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "beginner"
    _run_editor(mode, run_event_loop=True)
