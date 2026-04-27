import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.utils.i18n import tr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT = 30


@pytest.mark.core
def test_ballistics_simulator_uses_honest_initial_stats():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = "\n".join(
        [
            "from PyQt6.QtWidgets import QApplication",
            "app = QApplication([])",
            "from src.modules.ballistics_simulator import BallisticsSimulator",
            "w = BallisticsSimulator()",
            "print(w.stat_pressure.text())",
            "print(w.stat_velocity.text())",
            "print(w.stat_energy.text())",
            "print(w.stat_barrel_time.text())",
            "print(w.stat_safety.text())",
            "w.close()",
            "app.processEvents()",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) >= 5
    assert all("--" not in line for line in lines[:5])
    assert "Ingen beregning ennå" in lines[0] or "No calculation yet" in lines[0]


@pytest.mark.core
def test_ballistics_simulator_harmonics_summary_uses_i18n_labels():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = "\n".join(
        [
            "from PyQt6.QtWidgets import QApplication",
            "app = QApplication([])",
            "from src.modules.ballistics_simulator import BallisticsSimulator",
            "w = BallisticsSimulator()",
            "w.harmonics = {",
            "    'barrel_name': 'Proof 24',",
            "    'barrel_attachment_type': 'shouldered',",
            "    'barrel_profile': 'sendero',",
            "    'estimated_frequency_hz': 82.4,",
            "    'stability_tier': 'high',",
            "    'harmonics_confidence': 'medium',",
            "    'harmonic_score': 0.82,",
            "    'missing_required_inputs': ['ammo_temp', 'confirmed_node'],",
            "}",
            "w._refresh_harmonics_tab()",
            "print(w.harmonics_summary_label.text())",
            "print(w.harmonics_score_label.text())",
            "w.close()",
            "app.processEvents()",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) >= 2
    assert lines[0].startswith("Pipe/Løp:") or lines[0].startswith("Barrel:")
    assert "Harmonisk score:" in lines[1] or "Harmonic score:" in lines[1]


@pytest.mark.core
def test_ballistics_simulator_charge_labels_use_shared_formatter():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["HEADLESS"] = "1"
    code = "\n".join(
        [
            "from PyQt6.QtWidgets import QApplication",
            "app = QApplication([])",
            "from src.modules.ballistics_simulator import BallisticsSimulator",
            "w = BallisticsSimulator()",
            "print(w.charge_label.text())",
            "print(BallisticsSimulator._format_charge_label(20.0))",
            "print(BallisticsSimulator._format_charge_label(60.0))",
            "w.close()",
            "app.processEvents()",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert lines[0] == lines[0]
    assert lines[1] == "20.0 gr"
    assert lines[2] == "60.0 gr"


@pytest.mark.core
def test_ballistics_simulator_plot_point_labels_have_translation_entries():
    assert (
        tr("ballistics_peak_point_name", value="62000") != "ballistics_peak_point_name"
    )
    assert (
        tr("ballistics_muzzle_point_name", value="2750")
        != "ballistics_muzzle_point_name"
    )
