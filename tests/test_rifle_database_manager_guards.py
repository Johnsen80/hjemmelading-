from types import SimpleNamespace

from src.modules import rifle_database_manager as rifle_db_module


class _FakeItem:
    def __init__(self, value):
        self._value = value

    def text(self):
        return str(self._value)


class _FakeTable:
    def __init__(self, record_id):
        self._record_id = record_id

    def currentRow(self):
        return 0

    def item(self, row, column):
        assert row == 0
        return _FakeItem(self._record_id)


class _MissingDb:
    def get_by_id(self, table, record_id):
        return None


def test_add_rounds_fired_handles_missing_rifle(monkeypatch):
    warnings = []
    refreshed = {"called": False}

    monkeypatch.setattr(
        rifle_db_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        table=_FakeTable(10),
        load_rifles=lambda: refreshed.__setitem__("called", True),
    )

    rifle_db_module.RifleDatabaseManager.add_rounds_fired(manager)

    assert warnings
    assert refreshed["called"] is True


def test_log_maintenance_handles_missing_rifle(monkeypatch):
    warnings = []
    refreshed = {"called": False}

    monkeypatch.setattr(
        rifle_db_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        table=_FakeTable(11),
        load_rifles=lambda: refreshed.__setitem__("called", True),
    )

    rifle_db_module.RifleDatabaseManager.log_maintenance(manager)

    assert warnings
    assert refreshed["called"] is True


def test_build_chamber_comparison_html_renders_watch_status(monkeypatch):
    monkeypatch.setattr(
        rifle_db_module,
        "compare_chamber_to_cartridge_standard",
        lambda db, caliber, measured: {
            "status": "watch",
            "notes": [
                "Referanse: .308 Winchester SAAMI.",
                "Registrert neck 8.710 mm mot standard 8.720 mm (indikativ klaring +0.010 mm).",
            ],
        },
    )

    html = rifle_db_module.build_chamber_comparison_html(
        object(),
        {"caliber": ".308 Winchester", "freebore_mm": 1.45},
        {"chamber_neck_diameter_mm": 8.71},
    )

    assert "Standard vs Measured" in html
    assert "Status:</b> Watch" in html
    assert ".308 Winchester SAAMI" in html


def test_describe_jump_measurement_barrel_formats_barrel_context():
    assert (
        rifle_db_module.describe_jump_measurement_barrel(
            {"barrel_name": "26in Match", "barrel_id": "pipe-a"}
        )
        == "26in Match"
    )
    assert (
        rifle_db_module.describe_jump_measurement_barrel({"barrel_id": "pipe-b"})
        == "Barrel pipe-b"
    )
    assert rifle_db_module.describe_jump_measurement_barrel({}) == "Legacy rifle-level"


def test_load_details_shows_barrel_column_for_jump_history(monkeypatch):
    monkeypatch.setattr(
        rifle_db_module,
        "build_chamber_comparison_html",
        lambda *args, **kwargs: "<p>comparison</p>",
    )
    monkeypatch.setattr(
        rifle_db_module,
        "build_harmonics_html",
        lambda *args, **kwargs: "<p>harmonics</p>",
    )
    monkeypatch.setattr(rifle_db_module, "QTableWidgetItem", _FakeItem)

    class _HtmlSink:
        def __init__(self):
            self.html = ""

        def setHtml(self, value):
            self.html = value

    class _CaptureTable:
        def __init__(self):
            self.items = {}
            self.rows = 0

        def setRowCount(self, count):
            self.rows = count

        def setItem(self, row, column, item):
            self.items[(row, column)] = item.text()

    class _DetailDb:
        def get_by_id(self, table, record_id):
            if table == "rifles":
                return {
                    "id": record_id,
                    "name": "Match Rifle",
                    "manufacturer": "Tikka",
                    "model": "T3x",
                    "caliber": "6.5 Creedmoor",
                    "action_type": "Bolt",
                    "serial_number": "ABC123",
                    "barrel_length_inches": 24.0,
                    "barrel_length_mm": 610.0,
                    "barrel_contour": "Medium",
                    "barrel_material": "Steel",
                    "barrel_finish": "Blued",
                    "twist_rate": "1:8",
                    "twist_direction": "right",
                    "rifling_type": "5R",
                    "round_count": 120,
                    "accuracy_life_estimate": 2500,
                    "bore_condition": "good",
                    "throat_erosion_mm": 0.12,
                    "accuracy_baseline_moa": 0.45,
                }
            if table == "bullets":
                return {"name": "ELD-M"}
            return None

        def execute_query(self, query, params=()):
            normalized = " ".join(query.split())
            if "FROM rifle_profile_details" in normalized:
                return []
            if "FROM rifle_bullet_jump_measurements" in normalized:
                return [
                    {
                        "measurement_date": "2026-04-09",
                        "bullet_id": 7,
                        "barrel_name": "26in Match",
                        "jam_coal_mm": 71.2,
                        "jam_cbto_mm": 56.1,
                        "measurement_method": "hornady_oal_gauge",
                        "rounds_fired_at_measurement": 120,
                    },
                    {
                        "measurement_date": "2025-10-01",
                        "bullet_id": 7,
                        "jam_coal_mm": 71.0,
                        "jam_cbto_mm": 55.9,
                        "measurement_method": "legacy",
                        "rounds_fired_at_measurement": 60,
                    },
                ]
            if "FROM rifle_accuracy_tests" in normalized:
                return []
            if "FROM rifle_maintenance_log" in normalized:
                return []
            return []

    dialog = SimpleNamespace(
        db=_DetailDb(),
        rifle_id=4,
        info_display=_HtmlSink(),
        harmonics_display=_HtmlSink(),
        bullet_jump_table=_CaptureTable(),
        accuracy_table=_CaptureTable(),
        maintenance_table=_CaptureTable(),
    )

    rifle_db_module.RifleDetailsDialog.load_details(dialog)

    assert dialog.bullet_jump_table.rows == 2
    assert dialog.bullet_jump_table.items[(0, 2)] == "26in Match"
    assert dialog.bullet_jump_table.items[(1, 2)] == "Legacy rifle-level"
