import importlib.util
import subprocess
import sys
import traceback

import pytest


# Simple import smoke test to detect import-time crashes in key modules
@pytest.mark.core
def test_import_ui_modules():
    modules = [
        "HjemmeladingApp.ui.settings_dialog",
        "src.ui.main_window",
        "src.modules.batch_workspace",
        "src.modules.batch_analyzer",
        "src.database.batch_manager",
        "src.assets.logo",
        "src.ui.logo_helper",
        "src.ui.reloading_theme",
    ]
    failed = []
    has_qt = importlib.util.find_spec("PyQt6") is not None
    for m in modules:
        if not has_qt and (
            "settings_dialog" in m
            or "main_window" in m
            or "logo" in m
            or "logo_helper" in m
        ):
            # Skip GUI-only modules if PyQt6 is not available
            continue
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {m}"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failed.append(
                    (
                        m,
                        result.stderr.strip()
                        or result.stdout.strip()
                        or f"subprocess exited with {result.returncode}",
                    )
                )
        except Exception:
            failed.append((m, traceback.format_exc()))
    assert not failed, "Import failures:\n" + "\n".join(
        f"{m}: {tb}" for m, tb in failed
    )
