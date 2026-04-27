from types import SimpleNamespace

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.modules import inventory_manager as inventory_module
from src.modules import rifle_database_manager as rifle_db_module
from src.modules import rifle_optic_manager as optic_module
from src.modules import safety_dashboard as safety_dashboard_module


class _FakeItem:
    def __init__(self, value):
        self._value = value

    def data(self, role):
        if role == Qt.ItemDataRole.UserRole:
            return self._value
        return None

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

    def get_all(self, table):
        return []


class _FakeSafetyDashboardDb:
    def execute_query(self, query, params=()):
        normalized = " ".join(query.split())

        if normalized == "SELECT id, name FROM ammo_profiles ORDER BY name":
            return [(1, "6.5 Creedmoor")]
        if (
            normalized
            == "SELECT ammo_profile_id FROM load_development_sessions WHERE id = ?"
        ):
            assert params == (33,)
            return [(1,)]
        if normalized.startswith(
            "SELECT ammo_profile_id FROM batch_projects WHERE source_workflow = ? AND ammo_profile_id IS NOT NULL"
        ):
            assert params == ("workflow:12",)
            return [(1,)]
        if (
            normalized
            == "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'LAV'"
        ):
            return [(0,)]
        if (
            normalized
            == "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'MODERAT'"
        ):
            return [(0,)]
        if (
            normalized
            == "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'HØY'"
        ):
            return [(1,)]
        if (
            normalized
            == "SELECT COUNT(*) FROM pressure_signs WHERE severity_level = 'KRITISK'"
        ):
            return [(0,)]
        if "WHERE ps.severity_level IN ('HØY', 'KRITISK')" in normalized:
            return [
                (
                    "2026-04-08",
                    "6.5 Creedmoor",
                    42.6,
                    "HØY",
                    0,
                    1,
                    0,
                    0,
                    "reports/primer-step-5.jpg",
                    "good",
                    "light crater around the firing pin",
                    "medium",
                )
            ]
        if normalized.startswith(
            "SELECT ps.date, ap.name, ps.charge_weight, ps.pressure_score,"
        ):
            return [
                (
                    "2026-04-08",
                    "6.5 Creedmoor",
                    42.6,
                    3,
                    "MODERAT",
                    "reports/primer-step-5.jpg",
                    "good",
                    "light crater around the firing pin",
                    "medium",
                    "Chrono looked normal",
                )
            ]
        if normalized.startswith(
            "SELECT ps.date, ap.name, ps.charge_weight, ps.flat_primer,"
        ):
            return [
                (
                    "2026-04-08",
                    "6.5 Creedmoor",
                    42.6,
                    0,
                    1,
                    0,
                    0,
                    "reports/primer-step-5.jpg",
                    "good",
                    "light crater around the firing pin",
                    "medium",
                    3,
                )
            ]
        if normalized.startswith(
            "SELECT DISTINCT ap.id, ap.name, ps.rifle_id, ps.barrel_id, ps.barrel_name FROM pressure_signs ps"
        ):
            return [(1, "6.5 Creedmoor", 7, "B1", "24in Match")]
        if normalized.startswith(
            "SELECT MAX(charge_weight) FROM pressure_signs WHERE ammo_profile_id = ? AND pressure_score < 3 AND rifle_id = ? AND barrel_id = ?"
        ):
            assert params == (1, 7, "B1")
            return [(42.3,)]
        if normalized.startswith(
            "SELECT MIN(charge_weight) FROM pressure_signs WHERE ammo_profile_id = ? AND pressure_score >= 3 AND rifle_id = ? AND barrel_id = ?"
        ):
            assert params == (1, 7, "B1")
            return [(42.6,)]
        if normalized.startswith("SELECT COUNT(*), SUM( CASE"):
            assert params == (1, 7, "B1")
            return [(1, 1, 1, 1, 1)]

        return []

    def execute_update(self, query, params=()):
        return None


def test_inventory_manager_edit_powder_handles_missing_record(monkeypatch):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        inventory_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        powder_table=_FakeTable(1),
        load_powder=lambda: refreshed.__setitem__("called", True),
    )

    inventory_module.InventoryManager.edit_powder(manager)

    assert warnings
    assert refreshed["called"] is True


def test_inventory_manager_edit_bullet_handles_missing_record(monkeypatch):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        inventory_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        bullets_table=_FakeTable(2),
        load_bullets=lambda: refreshed.__setitem__("called", True),
    )

    inventory_module.InventoryManager.edit_bullet(manager)

    assert warnings
    assert refreshed["called"] is True


def test_inventory_manager_edit_primer_handles_missing_record(monkeypatch):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        inventory_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        primers_table=_FakeTable(3),
        load_primers=lambda: refreshed.__setitem__("called", True),
    )

    inventory_module.InventoryManager.edit_primer(manager)

    assert warnings
    assert refreshed["called"] is True


def test_inventory_manager_edit_case_handles_missing_record(monkeypatch):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        inventory_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        cases_table=_FakeTable(4),
        load_cases=lambda: refreshed.__setitem__("called", True),
    )

    inventory_module.InventoryManager.edit_case(manager)

    assert warnings
    assert refreshed["called"] is True


def test_rifle_optic_manager_edit_rifle_handles_missing_record(monkeypatch):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        optic_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        rifles_table=_FakeTable(5),
        load_rifles=lambda: refreshed.__setitem__("called", True),
    )

    optic_module.RifleOpticManager.edit_rifle(manager)

    assert warnings
    assert refreshed["called"] is True


def test_rifle_optic_manager_edit_optic_handles_missing_record(monkeypatch):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        optic_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        optics_table=_FakeTable(6),
        load_optics=lambda: refreshed.__setitem__("called", True),
    )

    optic_module.RifleOpticManager.edit_optic(manager)

    assert warnings
    assert refreshed["called"] is True


def test_rifle_database_manager_manage_accuracy_tests_handles_missing_rifle(
    monkeypatch,
):
    warnings = []
    refreshed = {"called": False}
    monkeypatch.setattr(
        rifle_db_module.QMessageBox, "warning", lambda *a, **k: warnings.append((a, k))
    )

    manager = SimpleNamespace(
        db=_MissingDb(),
        table=_FakeTable(7),
        load_rifles=lambda: refreshed.__setitem__("called", True),
    )

    rifle_db_module.RifleDatabaseManager.manage_accuracy_tests(manager)

    assert warnings
    assert refreshed["called"] is True


def test_inventory_bullet_bc_summary_prefers_segmented_bc():
    summary = inventory_module._format_bullet_bc_summary(
        {
            "bc_g1": 0.462,
            "bc_g7": 0.235,
            "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        }
    )

    assert summary == "SEG 0.245 @ 2600-3000"


def test_inventory_bullet_dialog_saves_segmented_bc_json():
    QApplication.instance() or QApplication([])
    dialog = inventory_module.BulletDialog()
    try:
        dialog.name.setText("Test")
        dialog.caliber.setText(".308")
        dialog.weight.setValue(175)
        dialog.bc_segments.setPlainText(
            '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]'
        )

        data = dialog.get_data()

        assert data["bc_segments_json"] == (
            '[{"model": "AUTO", "velocity_fps_min": 2600.0, "velocity_fps_max": 3000.0, '
            '"bc_g1": null, "bc_g7": 0.245, "bc": null}]'
        )
    finally:
        dialog.close()


def test_pressure_sign_dialog_returns_primer_image_metadata():
    QApplication.instance() or QApplication([])

    from src.modules.safety_dashboard import PressureSignDialog

    dialog = PressureSignDialog()
    try:
        dialog.primer_image_path.setText("reports/primer-step-5.jpg")
        dialog.primer_image_quality.setCurrentIndex(3)
        dialog.primer_image_confidence.setCurrentIndex(1)
        dialog.workflow_id.setText("12")
        dialog.rifle_id.setText("7")
        dialog.barrel_id.setText("B1")
        dialog.barrel_name.setText("24in Match")
        dialog.load_session_id.setText("33")
        dialog.session_name.setText("Batch A")
        dialog.primer_image_observation.setPlainText(
            "light crater around the firing pin"
        )

        data = dialog.get_data()

        assert data["primer_image_path"] == "reports/primer-step-5.jpg"
        assert data["primer_image_quality"] == "good"
        assert data["primer_image_confidence"] == "medium"
        assert data["workflow_id"] == "12"
        assert data["rifle_id"] == "7"
        assert data["barrel_id"] == "B1"
        assert data["barrel_name"] == "24in Match"
        assert data["load_session_id"] == "33"
        assert data["session_name"] == "Batch A"
        assert data["primer_image_observation"] == "light crater around the firing pin"
    finally:
        dialog.close()


def test_safety_dashboard_reads_active_workflow_context(monkeypatch):
    class _FakeSettings:
        def value(self, key, default=None):
            mapping = {
                "workflow_context/workflow_id": "12",
                "workflow_context/workflow_name": "OCW Test",
                "workflow_context/load_session_id": "33",
                "workflow_context/ammo_profile_id": "1",
                "workflow_context/rifle_id": "7",
                "workflow_context/barrel_id": "B1",
                "workflow_context/barrel_name": "24in Match",
                "workflow_context/barrel_configuration_id": "cfg-supp",
                "workflow_context/barrel_configuration_name": "Suppressed",
                "workflow_context/created_date": "2026-03-20",
            }
            return mapping.get(key, default)

    monkeypatch.setattr(
        safety_dashboard_module, "QSettings", lambda *args, **kwargs: _FakeSettings()
    )

    context = safety_dashboard_module._get_active_workflow_context()

    assert context["workflow_id"] == 12
    assert context["load_session_id"] == 33
    assert context["ammo_profile_id"] == 1
    assert context["rifle_id"] == 7
    assert context["barrel_id"] == "B1"
    assert context["barrel_name"] == "24in Match"
    assert context["barrel_configuration_id"] == "cfg-supp"
    assert context["barrel_configuration_name"] == "Suppressed"


def test_pressure_sign_dialog_prefills_active_workflow_context(monkeypatch):
    QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        safety_dashboard_module,
        "get_database",
        lambda: _FakeSafetyDashboardDb(),
    )

    dialog = safety_dashboard_module.PressureSignDialog(
        context={
            "workflow_id": 12,
            "workflow_name": "OCW Test",
            "load_session_id": 33,
            "ammo_profile_id": 1,
            "rifle_id": 7,
            "barrel_id": "B1",
            "barrel_name": "24in Match",
        }
    )
    try:
        assert dialog.ammo_combo.currentData() == 1
        assert dialog.workflow_id.text() == "12"
        assert dialog.load_session_id.text() == "33"
        assert dialog.rifle_id.text() == "7"
        assert dialog.barrel_id.text() == "B1"
        assert dialog.barrel_name.text() == "24in Match"
        assert dialog.session_name.text() == "OCW Test"
    finally:
        dialog.close()


def test_pressure_sign_dialog_resolves_ammo_profile_from_load_session(monkeypatch):
    QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        safety_dashboard_module,
        "get_database",
        lambda: _FakeSafetyDashboardDb(),
    )

    dialog = safety_dashboard_module.PressureSignDialog(
        context={
            "workflow_id": 12,
            "workflow_name": "OCW Test",
            "load_session_id": 33,
            "rifle_id": 7,
            "barrel_id": "B1",
            "barrel_name": "24in Match",
        }
    )
    try:
        assert dialog.ammo_combo.currentData() == 1
    finally:
        dialog.close()


def test_safety_dashboard_surfaces_primer_image_evidence(monkeypatch):
    QApplication.instance() or QApplication([])
    monkeypatch.setattr(
        safety_dashboard_module,
        "get_database",
        lambda: _FakeSafetyDashboardDb(),
    )

    dashboard = safety_dashboard_module.SafetyDashboard()
    try:
        recent_summary = dashboard.recent_alerts_table.item(0, 5).text()
        log_summary = dashboard.log_table.item(0, 5).text()
        history_summary = dashboard.history_table.item(0, 7).text()

        assert "light crater around the firing pin" in recent_summary
        assert "light crater around the firing pin" in log_summary
        assert (
            safety_dashboard_module.tr("safety_dashboard_primer_image_quality_good")
            in log_summary
        )
        assert recent_summary == log_summary
        assert log_summary == history_summary

        dashboard.run_analysis()
        analysis_text = dashboard.analysis_results.toPlainText()

        assert "1/1" in analysis_text
        assert (
            safety_dashboard_module.tr("safety_dashboard_primer_image_analysis_label")
            in analysis_text
        )
        assert "rifle #7" in analysis_text.lower()
        assert "24in match" in analysis_text.lower()
        assert "barrel" in analysis_text.lower()
    finally:
        dashboard.close()
