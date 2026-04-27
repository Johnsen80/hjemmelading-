from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.core
def test_release_scripts_reference_standard_entrypoint() -> None:
    files = [
        PROJECT_ROOT / "run_hjemmelading.ps1",
        PROJECT_ROOT / "run_hjemmelading.bat",
        PROJECT_ROOT / "run_valkyrie.ps1",
        PROJECT_ROOT / "run_valkyrie.bat",
        PROJECT_ROOT / "launch_hjemmelading.bat",
        PROJECT_ROOT / "launch_hjemmelading.vbs",
        PROJECT_ROOT / "create_shortcut.py",
        PROJECT_ROOT / "tools" / "create_lnk.vbs",
        PROJECT_ROOT / "tools" / "create_desktop_shortcut.vbs",
        PROJECT_ROOT / "tools" / "build_windows.ps1",
        PROJECT_ROOT / "scripts" / "build_windows.ps1",
        PROJECT_ROOT / "run_with_qt.py",
        PROJECT_ROOT / "tools" / "run_pyentry_debug.ps1",
        PROJECT_ROOT / "tools" / "run_pyentry_interactive.ps1",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "main.py" in text, f"{path} should reference the standardized entrypoint"
        assert (
            "HjemmeladingApp\\main.py" not in text
        ), f"{path} still references the legacy entrypoint"
        assert (
            "HjemmeladingApp/main.py" not in text
        ), f"{path} still references the legacy entrypoint"


@pytest.mark.core
def test_packaging_specs_reference_standard_entrypoint() -> None:
    files = [
        PROJECT_ROOT / "Hjemmelading.spec",
        PROJECT_ROOT / "VALKYRIE_BALLISTICS.spec",
        PROJECT_ROOT / "VALKYRIE_BALLISTICS_DEBUG.spec",
        PROJECT_ROOT / "build_release" / "VALKYRIE_BALLISTICS.spec",
        PROJECT_ROOT / "packaging" / "hjemmelading_onedir.spec",
        PROJECT_ROOT / "tools" / "VALKYRIE_BALLISTICS_DIR.spec",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "main.py" in text, f"{path} should package the standardized entrypoint"
        assert (
            "HjemmeladingApp\\main.py" not in text
        ), f"{path} still packages the legacy entrypoint"
        assert (
            "HjemmeladingApp/main.py" not in text
        ), f"{path} still packages the legacy entrypoint"


@pytest.mark.core
def test_installer_references_packaged_executable() -> None:
    path = PROJECT_ROOT / "installer" / "VALKYRIE_BALLISTICS_installer.iss"
    text = path.read_text(encoding="utf-8")
    assert "VALKYRIE_BALLISTICS.exe" in text
    assert "Hjemmelading.exe" not in text
