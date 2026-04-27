"""Tests for the ammo_test module — services and models."""

import pytest

from src.ammo_test import services
from src.ammo_test.models import (
    AmmoLot,
    AmmoTestSession,
    AmmoTestShot,
    LotComparisonResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db():
    import tempfile

    from src.database.database import Database

    tmp = tempfile.mktemp(suffix=".db")
    db = Database(db_path=tmp)
    return db


def _lot(db, brand="Norma", model="Oryx", caliber=".308 Win", lot="L001") -> int:
    lot_obj = AmmoLot(
        id=None,
        brand=brand,
        model=model,
        caliber=caliber,
        bullet_weight_gr=180.0,
        lot_number=lot,
        purchase_date="2026-01-15",
        purchase_price=450.0,
        store="Intersport",
        count_purchased=100,
        count_remaining=80,
        expiry_date=None,
        storage_notes=None,
        notes="Testlot",
    )
    return services.save_lot(db, lot_obj)


def _session(db, lot_id: int, rifle_name: str = "R1", distance: float = 100.0) -> int:
    s = AmmoTestSession(
        id=None,
        lot_id=lot_id,
        rifle_id=None,
        rifle_name=rifle_name,
        barrel_configuration_id=None,
        barrel_name="",
        test_date="2026-04-21",
        distance_m=distance,
        temp_c=12.0,
        wind_mps=2.5,
        wind_dir_deg=90,
        barometric_pressure_hpa=1013.0,
        barrel_state="cold",
        shots_in_prior_string=0,
        group_size_mm=18.5,
        poi_x_mm=2.0,
        poi_y_mm=-1.5,
        image_path=None,
        notes="Test sesjon",
    )
    return services.save_session(db, s)


def _shots(session_id: int) -> list[AmmoTestShot]:
    vels = [2840.0, 2855.0, 2861.0, 2848.0, 2852.0]
    return [
        AmmoTestShot(
            id=None,
            session_id=session_id,
            shot_number=i + 1,
            velocity_fps=v,
            is_cold_bore=(i == 0),
        )
        for i, v in enumerate(vels)
    ]


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestAmmoLotModel:
    def test_from_row_basic(self):
        row = {
            "id": 1,
            "brand": "Lapua",
            "model": "Scenar",
            "caliber": "6.5 CM",
            "bullet_weight_gr": 139.0,
            "lot_number": "X42",
        }
        lot = AmmoLot.from_row(row)
        assert lot.brand == "Lapua"
        assert lot.bullet_weight_gr == 139.0
        assert lot.lot_number == "X42"

    def test_from_row_missing_optional(self):
        row = {
            "id": 2,
            "brand": "Federal",
            "model": "GMM",
            "caliber": ".308 Win",
            "lot_number": "F99",
        }
        lot = AmmoLot.from_row(row)
        assert lot.bullet_weight_gr is None
        assert lot.purchase_price is None
        assert lot.store is None

    def test_from_row_empty_strings_become_empty(self):
        row = {"id": 3, "brand": "", "model": "", "caliber": "", "lot_number": ""}
        lot = AmmoLot.from_row(row)
        assert lot.brand == ""


class TestAmmoTestSessionModel:
    def test_from_row(self):
        row = {
            "id": 10,
            "lot_id": 1,
            "rifle_id": 5,
            "rifle_name": "Tikka T3",
            "barrel_configuration_id": None,
            "barrel_name": "",
            "test_date": "2026-04-21",
            "distance_m": 100.0,
            "temp_c": 15.0,
            "wind_mps": 1.0,
            "wind_dir_deg": 180,
            "barometric_pressure_hpa": 1010.0,
            "barrel_state": "cold",
            "shots_in_prior_string": 0,
            "group_size_mm": 22.0,
            "poi_x_mm": 1.5,
            "poi_y_mm": -3.0,
            "image_path": None,
            "notes": "",
        }
        s = AmmoTestSession.from_row(row)
        assert s.rifle_name == "Tikka T3"
        assert s.group_size_mm == 22.0
        assert s.temp_c == 15.0


class TestAmmoTestShotModel:
    def test_from_row_flags(self):
        row = {
            "id": 1,
            "session_id": 10,
            "shot_number": 1,
            "velocity_fps": 2855.0,
            "is_cold_bore": 1,
            "is_calibration": 0,
            "is_dud": 0,
            "is_light_strike": 0,
            "is_ftf": 0,
            "is_fte": 0,
            "notes": None,
        }
        shot = AmmoTestShot.from_row(row)
        assert shot.is_cold_bore is True
        assert shot.is_dud is False
        assert shot.velocity_fps == 2855.0


class TestLotComparisonResult:
    def test_avg_vel_no_sessions(self):
        lot = AmmoLot.from_row(
            {"id": 1, "brand": "X", "model": "Y", "caliber": "Z", "lot_number": "L1"}
        )
        result = LotComparisonResult(lots=[lot], sessions_by_lot={1: []})
        assert result.avg_vel(1) is None

    def test_avg_vel_computed(self):
        lot = AmmoLot.from_row(
            {"id": 1, "brand": "X", "model": "Y", "caliber": "Z", "lot_number": "L1"}
        )
        s1 = AmmoTestSession.from_row(
            {
                "id": 1,
                "lot_id": 1,
                "rifle_id": None,
                "rifle_name": "R",
                "barrel_configuration_id": None,
                "barrel_name": "",
                "test_date": "2026-04-21",
            }
        )
        s1.avg_vel_fps = 2850.0
        s2 = AmmoTestSession.from_row(
            {
                "id": 2,
                "lot_id": 1,
                "rifle_id": None,
                "rifle_name": "R",
                "barrel_configuration_id": None,
                "barrel_name": "",
                "test_date": "2026-04-21",
            }
        )
        s2.avg_vel_fps = 2870.0
        result = LotComparisonResult(lots=[lot], sessions_by_lot={1: [s1, s2]})
        assert result.avg_vel(1) == 2860.0

    def test_reliability_all_good(self):
        lot = AmmoLot.from_row(
            {"id": 1, "brand": "X", "model": "Y", "caliber": "Z", "lot_number": "L1"}
        )
        s = AmmoTestSession.from_row(
            {
                "id": 1,
                "lot_id": 1,
                "rifle_id": None,
                "rifle_name": "R",
                "barrel_configuration_id": None,
                "barrel_name": "",
                "test_date": "2026-04-21",
            }
        )
        s.shot_count = 20
        s.dud_count = 0
        s.light_strike_count = 0
        s.ftf_count = 0
        s.fte_count = 0
        result = LotComparisonResult(lots=[lot], sessions_by_lot={1: [s]})
        assert result.reliability_pct(1) == 100.0

    def test_reliability_with_failures(self):
        lot = AmmoLot.from_row(
            {"id": 1, "brand": "X", "model": "Y", "caliber": "Z", "lot_number": "L1"}
        )
        s = AmmoTestSession.from_row(
            {
                "id": 1,
                "lot_id": 1,
                "rifle_id": None,
                "rifle_name": "R",
                "barrel_configuration_id": None,
                "barrel_name": "",
                "test_date": "2026-04-21",
            }
        )
        s.shot_count = 20
        s.dud_count = 1
        s.light_strike_count = 0
        s.ftf_count = 0
        s.fte_count = 0
        result = LotComparisonResult(lots=[lot], sessions_by_lot={1: [s]})
        assert result.reliability_pct(1) == 95.0


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestLotServices:
    def test_save_and_get_lot(self):
        db = _make_db()
        lot_id = _lot(db)
        assert lot_id > 0
        retrieved = services.get_lot(db, lot_id)
        assert retrieved is not None
        assert retrieved.brand == "Norma"
        assert retrieved.model == "Oryx"
        assert retrieved.lot_number == "L001"

    def test_list_lots_empty(self):
        db = _make_db()
        assert services.list_lots(db) == []

    def test_list_lots_with_filter(self):
        db = _make_db()
        _lot(db, brand="Norma", caliber=".308 Win")
        _lot(db, brand="Lapua", caliber="6.5 CM", lot="L002")
        all_lots = services.list_lots(db)
        assert len(all_lots) == 2
        norma = services.list_lots(db, brand="Norma")
        assert len(norma) == 1
        assert norma[0].brand == "Norma"

    def test_update_lot(self):
        db = _make_db()
        lot_id = _lot(db)
        lot = services.get_lot(db, lot_id)
        lot.count_remaining = 50
        services.save_lot(db, lot)
        updated = services.get_lot(db, lot_id)
        assert updated.count_remaining == 50

    def test_delete_lot(self):
        db = _make_db()
        lot_id = _lot(db)
        services.delete_lot(db, lot_id)
        assert services.get_lot(db, lot_id) is None

    def test_list_brands(self):
        db = _make_db()
        _lot(db, brand="Norma")
        _lot(db, brand="Lapua", lot="L2")
        _lot(db, brand="Norma", lot="L3")
        brands = services.list_brands(db)
        assert "Norma" in brands
        assert "Lapua" in brands
        assert brands.count("Norma") == 1  # deduplicated

    def test_find_similar_lots(self):
        db = _make_db()
        _lot(db, brand="Norma", model="Oryx", caliber=".308 Win", lot="L001")
        _lot(db, brand="Norma", model="Oryx", caliber=".308 Win", lot="L002")
        _lot(db, brand="Lapua", model="Scenar", caliber="6.5 CM", lot="L003")
        similar = services.find_similar_lots(db, "Norma", "Oryx", ".308 Win")
        assert len(similar) == 2
        assert all(lot.brand == "Norma" for lot in similar)


class TestSessionServices:
    def test_save_and_get_session(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        assert sid > 0
        sessions = services.get_sessions_for_lot(db, lot_id)
        assert len(sessions) == 1
        assert sessions[0].distance_m == 100.0
        assert sessions[0].group_size_mm == 18.5

    def test_session_stats_from_shots(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        services.save_shots(db, sid, _shots(sid))
        sessions = services.get_sessions_for_lot(db, lot_id)
        s = sessions[0]
        assert s.shot_count == 5
        assert s.avg_vel_fps is not None
        assert 2840 < s.avg_vel_fps < 2870
        assert s.es_fps is not None
        assert s.es_fps == pytest.approx(21.0, abs=1)
        assert s.sd_fps is not None

    def test_session_reliability_stats(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        shots = _shots(sid)
        shots[2].is_dud = True  # one dud
        services.save_shots(db, sid, shots)
        sessions = services.get_sessions_for_lot(db, lot_id)
        assert sessions[0].dud_count == 1

    def test_delete_session(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        services.delete_session(db, sid)
        assert services.get_sessions_for_lot(db, lot_id) == []

    def test_shots_deleted_with_session(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        services.save_shots(db, sid, _shots(sid))
        services.delete_session(db, sid)
        shots = services.get_shots_for_session(db, sid)
        assert shots == []


class TestShotServices:
    def test_save_and_reload_shots(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        services.save_shots(db, sid, _shots(sid))
        shots = services.get_shots_for_session(db, sid)
        assert len(shots) == 5
        assert shots[0].is_cold_bore is True
        assert shots[1].is_cold_bore is False

    def test_overwrite_shots(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        services.save_shots(db, sid, _shots(sid))
        new_shots = [
            AmmoTestShot(id=None, session_id=sid, shot_number=1, velocity_fps=2900.0)
        ]
        services.save_shots(db, sid, new_shots)
        shots = services.get_shots_for_session(db, sid)
        assert len(shots) == 1
        assert shots[0].velocity_fps == 2900.0

    def test_cold_bore_flag_persists(self):
        db = _make_db()
        lot_id = _lot(db)
        sid = _session(db, lot_id)
        shots = [
            AmmoTestShot(
                id=None,
                session_id=sid,
                shot_number=1,
                velocity_fps=2830.0,
                is_cold_bore=True,
            )
        ]
        services.save_shots(db, sid, shots)
        loaded = services.get_shots_for_session(db, sid)
        assert loaded[0].is_cold_bore is True


class TestComparisonServices:
    def test_lot_comparison_two_lots(self):
        db = _make_db()
        lid1 = _lot(db, lot="A001")
        lid2 = _lot(db, lot="A002")
        sid1 = _session(db, lid1, rifle_name="Tikka")
        sid2 = _session(db, lid2, rifle_name="Tikka")
        services.save_shots(db, sid1, _shots(sid1))
        services.save_shots(db, sid2, _shots(sid2))
        result = services.build_lot_comparison(db, [lid1, lid2])
        assert len(result.lots) == 2
        assert result.avg_vel(lid1) is not None
        assert result.avg_group(lid1) == pytest.approx(18.5, abs=0.01)

    def test_weapon_matrix_single_rifle(self):
        db = _make_db()
        lid = _lot(db)
        sid = _session(db, lid, rifle_name="SakoA7")
        services.save_shots(db, sid, _shots(sid))
        matrix = services.build_weapon_matrix(db, lid)
        assert len(matrix) == 1
        assert matrix[0]["rifle_name"] == "SakoA7"
        assert matrix[0]["session_count"] == 1

    def test_weapon_matrix_multi_rifle(self):
        db = _make_db()
        lid = _lot(db)
        _session(db, lid, rifle_name="Tikka")
        _session(db, lid, rifle_name="Sako")
        _session(db, lid, rifle_name="Tikka")
        matrix = services.build_weapon_matrix(db, lid)
        assert len(matrix) == 2
        tikka = next(r for r in matrix if r["rifle_name"] == "Tikka")
        assert tikka["session_count"] == 2

    def test_build_report_data(self):
        db = _make_db()
        lid1 = _lot(db, lot="R001")
        lid2 = _lot(db, lot="R002")
        sid1 = _session(db, lid1)
        services.save_shots(db, sid1, _shots(sid1))
        data = services.build_report_data(db, [lid1, lid2])
        assert data["lot_count"] == 2
        assert len(data["rows"]) == 2

    def test_sessions_deleted_with_lot(self):
        db = _make_db()
        lid = _lot(db)
        _session(db, lid)
        services.delete_lot(db, lid)
        assert services.get_sessions_for_lot(db, lid) == []
