from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modules import gordon_extractor_temp as extractor_mod


class _FakeDb:
    def __init__(self) -> None:
        self.profiles = [
            {
                "id": 1,
                "name": "Demo Load 308",
                "coal": 71.8,
            }
        ]
        self.rows: list[dict] = []
        self.seed_grt: dict[int, dict[str, float]] = {}

    def get_all(self, table: str, order_by: str = "id"):  # noqa: ARG002
        if table == "ammo_profiles":
            return list(self.profiles)
        return []

    def execute_query(self, query: str, params: tuple = ()):  # noqa: ARG002
        if "FROM grt_data" in query:
            ammo_profile_id = params[0]
            if "predicted_velocity" in query and ammo_profile_id in self.seed_grt:
                return [dict(self.seed_grt[ammo_profile_id])]
            for idx, row in enumerate(self.rows, start=1):
                if row["ammo_profile_id"] == ammo_profile_id:
                    return [{"id": idx}]
        return []

    def insert(self, table: str, data: dict):
        assert table == "grt_data"
        self.rows.append(dict(data))
        return len(self.rows)

    def update(
        self, table: str, data: dict, condition: str, params: tuple = ()
    ):  # noqa: ARG002
        assert table == "grt_data"
        row_id = params[0]
        self.rows[row_id - 1] = dict(data)


def _sample_tab_results_payload() -> dict:
    return {
        "active_tab": {
            "active": {
                "tabhandle": 123,
                "caption": "Demo Load 308",
            },
            "tab": {
                "tabhandle": 123,
                "caption": "Demo Load 308",
                "file": "C:/loads/demo.grtload",
            },
        },
        "results": {
            "MaxPressure": "3347.4831159072783 bar",
            "EndVelocity": "850.50579100633934 m/s",
            "EndEnergy": "3984.2004144201014 joule",
            "EndTime": "1.39346279789998 ms",
            "BurnoutInBarrel": "true",
            "LoadingDensity": "96.4",
            "CartridgeOAL": "71.8",
            "chunks": [
                {
                    "chunkIndex": 0,
                    "data": [
                        {"x": 0.0, "p": 250.0, "v": 0.0},
                        {"x": 1.0, "p": 500.0, "v": 10.0},
                    ],
                }
            ],
        },
    }


def test_candidate_conversion_and_matching(monkeypatch, tmp_path):
    fake_db = _FakeDb()
    monkeypatch.setattr(extractor_mod, "get_database", lambda: fake_db)

    widget = extractor_mod.GordonExtractorTemp()
    widget.export_dir = tmp_path / "export"
    widget.export_dir.mkdir()
    widget.plugin_dump_dir = tmp_path / "dumps"
    widget.plugin_dump_dir.mkdir()

    dump_path = widget.plugin_dump_dir / "20260403_000000_tab_results.json"
    dump_path.write_text(json.dumps(_sample_tab_results_payload()), encoding="utf-8")

    candidate_rows = widget._build_candidate_rows()
    assert len(candidate_rows) == 1

    candidate = candidate_rows[0]["candidate"]
    match = candidate_rows[0]["match"]

    assert candidate["profile_name"] == "Demo Load 308"
    assert candidate["predicted_velocity"] is not None
    assert candidate["max_pressure_psi"] is not None
    assert candidate["max_pressure_bar"] == 3347.5
    assert candidate["optimal_coal"] == 71.8
    assert match["id"] == 1


def test_import_candidates_to_db(monkeypatch, tmp_path):
    fake_db = _FakeDb()
    monkeypatch.setattr(extractor_mod, "get_database", lambda: fake_db)
    monkeypatch.setattr(
        extractor_mod.QMessageBox, "information", staticmethod(lambda *a, **k: None)
    )

    widget = extractor_mod.GordonExtractorTemp()
    widget.export_dir = tmp_path / "export"
    widget.export_dir.mkdir()
    widget.plugin_dump_dir = tmp_path / "dumps"
    widget.plugin_dump_dir.mkdir()

    dump_path = widget.plugin_dump_dir / "20260403_000000_tab_results.json"
    dump_path.write_text(json.dumps(_sample_tab_results_payload()), encoding="utf-8")

    widget._import_candidates_to_db()

    assert len(fake_db.rows) == 1
    inserted = fake_db.rows[0]
    assert inserted["ammo_profile_id"] == 1
    assert inserted["predicted_velocity"] is not None
    assert inserted["max_pressure_psi"] is not None
    assert inserted["optimal_coal"] == 71.8


def test_match_by_source_file_and_seeded_grt(monkeypatch, tmp_path):
    fake_db = _FakeDb()
    fake_db.profiles = [
        {
            "id": 1,
            "name": "Load A",
            "coal": None,
            "component_context_json": json.dumps(
                {"source_file": r"C:\loads\same_file.grtload", "charge_grains": 49.0}
            ),
        },
        {
            "id": 2,
            "name": "Load B",
            "coal": None,
            "component_context_json": json.dumps(
                {"source_file": r"C:\loads\same_file.grtload", "charge_grains": 53.0}
            ),
        },
    ]
    fake_db.seed_grt = {
        1: {"predicted_velocity": 2678.0, "max_pressure_bar": 3538.7},
        2: {"predicted_velocity": 2917.8, "max_pressure_bar": 4003.7},
    }
    monkeypatch.setattr(extractor_mod, "get_database", lambda: fake_db)

    widget = extractor_mod.GordonExtractorTemp()
    widget.export_dir = tmp_path / "export"
    widget.export_dir.mkdir()
    widget.plugin_dump_dir = tmp_path / "dumps"
    widget.plugin_dump_dir.mkdir()

    payload = {
        "active_tab": {
            "active": {"tabhandle": 10, "caption": "Imported load"},
            "tab": {
                "tabhandle": 10,
                "caption": "Imported load",
                "file": "C:/loads/same_file.grtload",
            },
        },
        "results": {
            "MaxPressure": "4004.0 bar",
            "EndVelocity": "889.3 m/s",
            "LoadingDensity": "97.8",
            "CartridgeOAL": "84.58",
            "chunks": [],
        },
    }
    dump_path = widget.plugin_dump_dir / "20260403_010000_tab_results.json"
    dump_path.write_text(json.dumps(payload), encoding="utf-8")

    candidate_rows = widget._build_candidate_rows()
    assert len(candidate_rows) == 1
    assert candidate_rows[0]["match"]["id"] == 2
