from types import SimpleNamespace

from src.modules import terrain_map as terrain_module
from src.modules import terrain_map_baseline as terrain_baseline


def test_analyze_terrain_risk_from_profile_reports_low_for_calm_profile():
    summary = terrain_module.analyze_terrain_risk_from_profile(
        [
            (60.0, 11.0, 100.0),
            (60.0, 11.1, 101.0),
            (60.0, 11.2, 100.5),
            (60.0, 11.3, 101.0),
        ],
        {"wind_speed_mps": 1.5},
    )

    assert summary["level"] == "low"
    assert summary["profile_summary"]["relief_m"] <= 2.0


def test_analyze_terrain_risk_from_profile_reports_high_for_valley_and_ridge():
    summary = terrain_module.analyze_terrain_risk_from_profile(
        [
            (60.0, 11.0, 210.0),
            (60.0, 11.1, 150.0),
            (60.0, 11.2, 120.0),
            (60.0, 11.3, 180.0),
            (60.0, 11.4, 250.0),
        ],
        {"wind_speed_mps": 5.5},
    )

    assert summary["level"] == "high"
    assert any(
        "channeling" in item.lower() or "turbulence" in item.lower()
        for item in summary["checks"]
    )


def test_integrate_map_with_ballistics_returns_terrain_risk(monkeypatch):
    monkeypatch.setattr(
        terrain_module,
        "compute_geo_solution",
        lambda shot: SimpleNamespace(slant_range_m=340.0, inclination_deg=4.0),
    )
    monkeypatch.setattr(
        terrain_module,
        "solve_trajectory",
        lambda ballistic_input, shot_scenario, atmosphere: {"ok": True},
    )

    result = terrain_module.integrate_map_with_ballistics(
        60.0,
        11.0,
        60.1,
        11.2,
        {
            "temperature_c": 12.0,
            "pressure_hpa": 1005.0,
            "humidity_pct": 55.0,
            "altitude_m": 300.0,
            "wind_speed_mps": 4.5,
            "wind_dir_deg": 220.0,
            "terrain_profile": [
                (60.0, 11.0, 220.0),
                (60.05, 11.1, 150.0),
                (60.1, 11.2, 240.0),
            ],
        },
        ballistic_input=SimpleNamespace(),
    )

    assert "terrain_risk" in result
    assert result["terrain_risk"]["title"] == "Terrain Risk"
    assert result["terrain_risk"]["level"] in {"medium", "high"}


def test_format_terrain_risk_text_includes_title_score_and_checks():
    text = terrain_baseline.format_terrain_risk_text(
        {
            "title": "Terrengrisiko",
            "score": 3.5,
            "message": "Profilen er krevende.",
            "checks": ["Kanalvind mulig", "Rygg kan gi turbulens"],
        }
    )

    assert "Terrengrisiko" in text
    assert "Score: 3.5" in text
    assert "- Kanalvind mulig" in text


def test_update_terrain_risk_sets_text(monkeypatch):
    class _Display:
        def __init__(self):
            self.value = ""

        def setText(self, text):
            self.value = text

    viewer = terrain_baseline.TerrainMapViewer.__new__(
        terrain_baseline.TerrainMapViewer
    )
    viewer.terrain_risk_display = _Display()
    viewer._build_simple_terrain_profile = lambda: [
        (60.0, 11.0, 220.0),
        (60.1, 11.1, 150.0),
        (60.2, 11.2, 240.0),
    ]
    monkeypatch.setattr(
        terrain_baseline.importlib,
        "import_module",
        lambda name: SimpleNamespace(
            analyze_terrain_risk_from_profile=lambda profile, env: {
                "title": "Terrengrisiko",
                "score": 4.0,
                "message": "Krevende profil.",
                "checks": ["Rygg", "Dal"],
            }
        ),
    )

    terrain_baseline.TerrainMapViewer.update_terrain_risk(viewer)

    assert "Terrengrisiko" in viewer.terrain_risk_display.value
    assert "Krevende profil." in viewer.terrain_risk_display.value
