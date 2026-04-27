from pathlib import Path

from src.ballistics import services as services_module
from src.ballistics.services import LoadAnalysisRequest, LoadAnalysisService
from src.database.database import Database


def test_analyze_load_uses_selected_primer_profile_from_database(monkeypatch) -> None:
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/ballistics_primer_service.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        rifle_id = database.insert(
            "rifles",
            {
                "name": "Primer Test Rifle",
                "caliber": "223 Rem",
                "twist_rate": "1:8",
                "barrel_length_inches": 24.0,
            },
        )
        bullet_id = database.insert(
            "bullets",
            {
                "name": "77 TMK",
                "manufacturer": "Sierra",
                "caliber": ".224",
                "weight_grains": 77.0,
                "diameter_mm": 5.69,
                "length_mm": 24.2,
                "bc_g7": 0.19,
            },
        )
        powder_id = database.insert(
            "powder",
            {
                "name": "N140",
                "manufacturer": "Vihtavuori",
                "density": 0.92,
                "burn_rate": "medium",
            },
        )
        primer_id = database.insert(
            "primers",
            {
                "name": "450",
                "manufacturer": "CCI",
                "primer_family": "small_rifle_magnum",
                "ignition_strength_class": "magnum",
                "pressure_tolerance_class": "high",
                "cup_hardness_class": "hard",
                "cold_weather_suitability": "good",
                "recommended_pressure_min_psi": 50000.0,
                "recommended_pressure_max_psi": 62000.0,
            },
        )

        service = LoadAnalysisService(database)

        class _FakeEngine:
            @staticmethod
            def calculate_load(*args, **kwargs):
                return {
                    "muzzle_velocity_fps": 2765.0,
                    "peak_pressure_psi": 55250.0,
                    "max_pressure_psi": 62000.0,
                    "load_density_percent": 93.0,
                    "safety_margin_percent": 10.9,
                }

        class _FakeAdvancedEngine:
            @staticmethod
            def calculate_trajectory(*args, **kwargs):
                return []

            @staticmethod
            def get_drop_at_distance(*args, **kwargs):
                return None

        monkeypatch.setattr(service, "engine", _FakeEngine())
        monkeypatch.setattr(service, "advanced_engine", _FakeAdvancedEngine())

        analysis = service.analyze_load(
            LoadAnalysisRequest(
                rifle_id=rifle_id,
                bullet_id=bullet_id,
                powder_id=powder_id,
                primer_id=primer_id,
                charge_weight_gr=23.7,
                coal_mm=57.4,
                temperature_c=2.0,
            )
        )

        assert analysis["primer"]["id"] == primer_id
        assert analysis["primer_profile"]["family"] == "small_rifle_magnum"
        assert analysis["primer_profile"]["pressure_tolerance_class"] == "high"
        assert any(
            "Anbefalt trykkvindu" in note
            for note in analysis["primer_profile"]["notes"]
        )
    finally:
        database.close()


def test_recommendation_window_stays_wide_when_evidence_is_thin() -> None:
    recommendation = services_module._recommendation_window(
        result={"charge_weight_gr": 23.7, "max_pressure_psi": 55250.0},
        harmonics={
            "sensitivity": {"charge": 1.0, "seating_depth": 1.0},
            "harmonic_score": 10.0,
        },
        pressure_assessment={"level": "ok"},
        stability_assessment={"level": "ok"},
        internal_ballistics={"level": "ok"},
        terminal_summary={"level": "ok"},
        input_quality={"level": "low", "score": 1.8},
        observation_summary={"chrono_count": 0, "accuracy_count": 0},
        usage_profile="precision",
        subsonic_mode=False,
    )

    assert recommendation["charge_step_gr"] == 0.4
    assert recommendation["seating_step_mm"] == 0.3
    assert recommendation["baseline_readiness"]["charge_can_freeze"] is False
    assert any("holdt bredt" in note for note in recommendation["notes"])


def test_recommendation_window_tightens_only_with_strong_measured_support() -> None:
    recommendation = services_module._recommendation_window(
        result={"charge_weight_gr": 23.7, "max_pressure_psi": 54000.0},
        harmonics={
            "sensitivity": {"charge": 0.95, "seating_depth": 0.95},
            "harmonic_score": 15.0,
        },
        pressure_assessment={"level": "ok"},
        stability_assessment={"level": "ok"},
        internal_ballistics={"level": "ok"},
        terminal_summary={"level": "ok"},
        input_quality={"level": "high", "score": 4.4},
        observation_summary={"chrono_count": 3, "accuracy_count": 2},
        usage_profile="precision",
        subsonic_mode=False,
    )

    assert recommendation["charge_step_gr"] == 0.2
    assert recommendation["seating_step_mm"] == 0.1
    assert recommendation["baseline_readiness"]["charge_can_freeze"] is True
    assert recommendation["baseline_readiness"]["seating_can_freeze"] is True
    assert any("Sterkt maalegrunnlag" in note for note in recommendation["notes"])


def test_analyze_load_collects_pressure_sign_history_using_pressure_sign_date(
    monkeypatch,
) -> None:
    db_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/ballistics_pressure_history.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    database = Database(str(db_path))
    try:
        rifle_id = database.insert(
            "rifles",
            {
                "name": "Pressure History Rifle",
                "caliber": "223 Rem",
                "twist_rate": "1:8",
                "barrel_length_inches": 24.0,
            },
        )
        bullet_id = database.insert(
            "bullets",
            {
                "name": "77 TMK",
                "manufacturer": "Sierra",
                "caliber": ".224",
                "weight_grains": 77.0,
                "diameter_mm": 5.69,
                "length_mm": 24.2,
                "bc_g7": 0.19,
            },
        )
        powder_id = database.insert(
            "powder",
            {
                "name": "N140",
                "manufacturer": "Vihtavuori",
                "density": 0.92,
                "burn_rate": "medium",
            },
        )
        ammo_profile_id = database.insert(
            "ammo_profiles",
            {
                "name": "223 Pressure Profile",
                "caliber": "223 Rem",
                "rifle_id": rifle_id,
                "bullet_id": bullet_id,
                "bullet_weight": 77.0,
                "powder_id": powder_id,
                "powder_charge": 23.7,
                "coal": 57.4,
            },
        )
        database.insert(
            "pressure_signs",
            {
                "ammo_profile_id": ammo_profile_id,
                "charge_weight": 23.7,
                "primer_crater": 1,
                "pressure_score": 3,
                "severity_level": "MODERAT",
                "notes": "light crater",
                "date": "2026-04-08",
            },
        )

        service = LoadAnalysisService(database)

        class _FakeEngine:
            @staticmethod
            def calculate_load(*args, **kwargs):
                return {
                    "muzzle_velocity_fps": 2765.0,
                    "peak_pressure_psi": 55250.0,
                    "max_pressure_psi": 62000.0,
                    "load_density_percent": 93.0,
                    "safety_margin_percent": 10.9,
                }

        class _FakeAdvancedEngine:
            @staticmethod
            def calculate_trajectory(*args, **kwargs):
                return []

            @staticmethod
            def get_drop_at_distance(*args, **kwargs):
                return None

        monkeypatch.setattr(service, "engine", _FakeEngine())
        monkeypatch.setattr(service, "advanced_engine", _FakeAdvancedEngine())

        analysis = service.analyze_load(
            LoadAnalysisRequest(
                rifle_id=rifle_id,
                bullet_id=bullet_id,
                powder_id=powder_id,
                ammo_profile_id=ammo_profile_id,
                charge_weight_gr=23.7,
                coal_mm=57.4,
                temperature_c=2.0,
            )
        )

        assert analysis["observations"]["summary"]["pressure_event_count"] == 1
        assert analysis["observations"]["pressure_signs"][0]["notes"] == "light crater"
    finally:
        database.close()
