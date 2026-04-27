from types import SimpleNamespace

from src.modules import weapon_profile_dialog as dialog_module


class _FakeBarrelList:
    def __init__(self, row):
        self._row = row
        self.set_rows = []

    def currentRow(self):
        return self._row

    def setCurrentRow(self, row):
        self.set_rows.append(row)
        self._row = row


def test_remove_selected_barrel_reselects_valid_row():
    refreshed = []
    widget = SimpleNamespace(
        barrel_list=_FakeBarrelList(1),
        barrels=[{"id": "a"}, {"id": "b"}],
        refresh_barrel_list=lambda: refreshed.append("list"),
        refresh_selected_barrel_summary=lambda: refreshed.append("summary"),
    )

    dialog_module.WeaponProfileDialog.remove_selected_barrel(widget)

    assert widget.barrels == [{"id": "a"}]
    assert widget.barrel_list.set_rows == [0]
    assert refreshed == ["list", "summary"]


def test_remove_selected_barrel_handles_last_item():
    refreshed = []
    widget = SimpleNamespace(
        barrel_list=_FakeBarrelList(0),
        barrels=[{"id": "a"}],
        refresh_barrel_list=lambda: refreshed.append("list"),
        refresh_selected_barrel_summary=lambda: refreshed.append("summary"),
    )

    dialog_module.WeaponProfileDialog.remove_selected_barrel(widget)

    assert widget.barrels == []
    assert widget.barrel_list.set_rows == []
    assert refreshed == ["list", "summary"]


def test_formatters_use_metric_units_by_default():
    widget = SimpleNamespace(
        _get_preferred_units=lambda: "metric",
    )

    length_text = dialog_module.WeaponProfileDialog._format_length_mm(widget, 660.4)
    velocity_text = dialog_module.WeaponProfileDialog._format_velocity_fps(
        widget, 2650.0
    )
    distance_text = dialog_module.WeaponProfileDialog._format_distance_m(widget, 100.0)

    assert "660.4 mm" == length_text
    assert "m/s" in velocity_text
    assert "100 m" == distance_text


def test_formatters_use_imperial_when_selected():
    widget = SimpleNamespace(
        _get_preferred_units=lambda: "imperial",
    )

    length_text = dialog_module.WeaponProfileDialog._format_length_mm(widget, 660.4)
    velocity_text = dialog_module.WeaponProfileDialog._format_velocity_fps(
        widget, 2650.0
    )
    temp_text = dialog_module.WeaponProfileDialog._format_temperature_c(widget, 20.0)
    distance_text = dialog_module.WeaponProfileDialog._format_distance_m(widget, 100.0)

    assert "in" in length_text
    assert "fps" in velocity_text
    assert "F" in temp_text
    assert "yd" in distance_text


def test_build_learning_profile_lines_summarizes_learning_status():
    widget = SimpleNamespace()

    lines = dialog_module.WeaponProfileDialog._build_learning_profile_lines(
        widget,
        {
            "confidence_label": "brukbar trygghet",
            "data_points": 7,
            "chrono_samples": 4,
            "target_samples": 2,
            "temperature_samples": 1,
            "drift_flag": "watch",
            "cold_bore_shift_moa": 0.32,
        },
    )

    assert "Læringsprofil: brukbar trygghet" in lines
    assert any("7 observasjoner" in line for line in lines)
    assert any("Driftstatus: watch" in line for line in lines)
    assert any("Cold bore-shift: 0.32 MOA" in line for line in lines)


def test_build_chamber_comparison_lines_includes_standard_vs_malt(monkeypatch):
    monkeypatch.setattr(
        dialog_module,
        "compare_chamber_to_cartridge_standard",
        lambda db, caliber, measured: {
            "status": "watch",
            "notes": [
                "Referanse: 6.5 Creedmoor CIP.",
                "Freebore 1.800 mm mot standard 1.500 mm (+0.300 mm).",
            ],
        },
    )

    widget = SimpleNamespace(
        db=object(),
        caliber_edit=SimpleNamespace(currentText=lambda: "6.5 Creedmoor"),
        _get_rifle_reference_row=lambda: {
            "freebore_mm": 1.8,
            "throat_angle_deg": 1.7,
            "throat_erosion_mm": 0.18,
        },
    )

    lines = dialog_module.WeaponProfileDialog._build_chamber_comparison_lines(
        widget,
        {"case_measurements": {"neck_diameter_mm": 7.44, "trim_length_mm": 48.5}},
    )

    assert lines[0] == "<b>Standard vs Measured</b>"
    assert any("Deviation detected" in line for line in lines)
    assert any("Freebore 1.800 mm" in line for line in lines)
