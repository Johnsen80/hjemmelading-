import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.rifle_harmonics import calculate_harmonics_profile, normalize_node_bands


@pytest.mark.core
def test_normalize_node_bands_parses_json_text():
    bands = normalize_node_bands(
        '[{"start_mm": 120, "end_mm": 140, "robustness": 0.8, "label": "node-a"}]'
    )
    assert len(bands) == 1
    assert bands[0]["start_mm"] == 120.0
    assert bands[0]["end_mm"] == 140.0
    assert bands[0]["robustness"] == 0.8


@pytest.mark.core
def test_calculate_harmonics_profile_returns_summary():
    rifle = {
        "barrel_length_mm": 610,
        "barrel_contour": "heavy",
        "muzzle_diameter_mm": 18.5,
        "breech_diameter_mm": 30.0,
        "barrel_weight_grams": 2500,
    }
    details = {
        "barrel_profile": "heavy",
        "harmonics": {
            "free_float_length_mm": 20,
            "tuner_mass_g": 120,
            "tuner_position_mm": 80,
            "action_stiffness": "rigid",
            "support_type": "rest",
        },
    }

    summary = calculate_harmonics_profile(rifle, details)

    assert summary["estimated_frequency_hz"] > 0
    assert summary["harmonic_score"] >= 0
    assert summary["node_bands"]
    assert summary["stability_tier"] in {
        "very-stable",
        "stable",
        "moderate",
        "sensitive",
    }
    assert summary["harmonics_confidence"] in {"low", "medium", "high"}


@pytest.mark.core
def test_calculate_harmonics_profile_uses_selected_barrel_details():
    rifle = {
        "name": "Systemrifle",
        "barrel_length_mm": 610,
        "barrel_contour": "medium",
        "muzzle_diameter_mm": 18.5,
        "breech_diameter_mm": 30.0,
        "barrel_weight_grams": 2500,
    }
    details = {
        "active_barrel_id": "barrel-2",
        "barrels": [
            {"id": "barrel-1", "name": "Trening", "length_mm": 600},
            {
                "id": "barrel-2",
                "name": "Konkurranse",
                "length_mm": 710,
                "barrel_attachment_type": "quick_change",
                "barrel_torque_nm": 6.0,
                "barrel_return_to_zero": "verify after swap",
                "muzzle_device_type": "suppressor",
                "muzzle_device_weight_g": 420,
                "muzzle_device_length_mm": 180,
            },
        ],
    }

    summary = calculate_harmonics_profile(rifle, details)

    assert summary["barrel_name"] == "Konkurranse"
    assert summary["barrel_length_mm"] == 710.0
    assert summary["barrel_attachment_type"] == "quick_change"
    assert summary["barrel_return_to_zero"] == "verify after swap"
    assert summary["barrel_torque_nm"] == 6.0
    assert summary["has_muzzle_device"] is True
    assert summary["muzzle_device_mass_g"] == 420.0
    assert any("Quick-change system" in note for note in summary["notes"])


@pytest.mark.core
def test_calculate_harmonics_profile_reports_missing_required_inputs():
    rifle = {
        "name": "Minimal rifle",
        "barrel_length_mm": 610,
        "barrel_weight_grams": 2400,
    }

    summary = calculate_harmonics_profile(rifle, {})

    assert summary["harmonics_confidence"] == "low"
    assert "attachment_type" in summary["missing_required_inputs"]
    assert "barrel_profile" in summary["missing_required_inputs"]


@pytest.mark.core
def test_calculate_harmonics_profile_uses_chamber_comparison_to_raise_sensitivity(
    monkeypatch,
):
    class _FakeDb:
        def list_cartridge_standards(self):
            return [
                {
                    "caliber_name": "6.5 Creedmoor",
                    "standard_body": "CIP",
                    "freebore_mm": 1.5,
                    "throat_angle_deg": 1.5,
                    "neck_diameter_mm": 7.45,
                }
            ]

    monkeypatch.setattr("src.utils.rifle_harmonics.get_database", lambda: _FakeDb())

    rifle = {
        "caliber": "6.5 Creedmoor",
        "barrel_length_mm": 610,
        "barrel_contour": "heavy",
        "muzzle_diameter_mm": 18.5,
        "breech_diameter_mm": 30.0,
        "barrel_weight_grams": 2500,
        "freebore_mm": 1.8,
        "throat_angle_deg": 1.7,
        "throat_erosion_mm": 0.18,
    }
    details = {
        "barrel_profile": "heavy",
        "case_measurements": {
            "neck_diameter_mm": 7.44,
            "trim_length_mm": 48.50,
        },
    }

    summary = calculate_harmonics_profile(rifle, details)

    assert summary["chamber_comparison"]["status"] == "watch"
    assert summary["sensitivity"]["seating_depth"] > 1.3
    assert summary["sensitivity"]["neck_tension"] > 1.1
    assert any("Freebore" in note for note in summary["notes"])
    assert any("Throat-erosjon" in note for note in summary["notes"])
