from types import SimpleNamespace

from src.modules import smart_loading_wizard as wizard_module


class _FakeProgress:
    def __init__(self):
        self.values = []

    def setValue(self, value):
        self.values.append(value)


class _FakeLabel:
    def __init__(self):
        self.text = ""

    def setText(self, text):
        self.text = text


class _FakeTextEdit:
    def __init__(self):
        self.text = ""

    def setPlainText(self, text):
        self.text = text

    def setText(self, text):
        self.text = text

    def setHtml(self, text):
        self.text = text


class _FakeTable:
    def __init__(self):
        self.row_count = None

    def setRowCount(self, count):
        self.row_count = count

    def setItem(self, *args, **kwargs):
        return None


class _FakeDb:
    def __init__(self, rifle=None, powder=None):
        self._rifle = rifle
        self._powder = powder

    def get_by_id(self, table, record_id):
        if table == "rifles":
            return self._rifle
        if table == "powder":
            return self._powder
        return None

    def execute_query(self, query, params=()):
        if "FROM load_data" in query:
            return [
                {
                    "bullet_id": 10,
                    "bullet_name": "Test bullet",
                    "powder_name": "Known powder",
                }
            ]
        if "FROM ladder_tests" in query:
            return []
        return []


def _make_page(fake_db):
    return SimpleNamespace(
        db=fake_db,
        progress=_FakeProgress(),
        label_status=_FakeLabel(),
        text_recommendation=_FakeTextEdit(),
        table_history=_FakeTable(),
        recommendation_data={},
        best_history=None,
    )


def test_analyze_and_recommend_handles_missing_rifle():
    page = _make_page(_FakeDb(rifle=None))

    wizard_module.AIRecommendationPage.analyze_and_recommend(
        page,
        rifle_id=1,
        purpose="jakt",
        components={},
    )

    assert page.label_status.text == "Rifle not found"
    assert "selected rifle could not be found" in page.text_recommendation.text
    assert page.table_history.row_count == 0


def test_analyze_and_recommend_handles_missing_powder_record():
    page = _make_page(_FakeDb(rifle={"id": 1, "caliber": ".308"}, powder=None))

    wizard_module.AIRecommendationPage.analyze_and_recommend(
        page,
        rifle_id=1,
        purpose="jakt",
        components={"powder_id": 999, "bullet_id": 10, "bullet_weight": 168},
    )

    assert page.label_status.text == "Analysis complete."


def test_preferred_bc_for_scoring_prefers_segmented_bc():
    assert (
        wizard_module._preferred_bc_for_scoring(
            {
                "bc_g1": 0.462,
                "bc_g7": 0.235,
                "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
            }
        )
        == 0.245
    )


def test_format_bullet_label_shows_segmented_bc_first():
    label = wizard_module._format_bullet_label(
        {
            "name": "ELD-M",
            "weight_grains": 175,
            "bc_g1": 0.620,
            "bc_g7": 0.315,
            "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        }
    )

    assert "Segmented BC: 0.245 @ 2600-3000 fps" in label


class _FakeCombo:
    def __init__(self, text, value):
        self._text = text
        self._value = value

    def currentText(self):
        return self._text

    def currentData(self):
        return self._value


class _RecordingDb:
    def __init__(self):
        self.tables = {
            "loading_sessions": [],
            "load_development_sessions": [],
        }
        self.profile_details = {}

    def get_by_id(self, table, record_id):
        if table == "rifles" and record_id == 3:
            return {"id": 3, "name": "Tikka T3x", "caliber": "6.5 CM"}
        for row in self.tables.get(table, []):
            if row["id"] == record_id:
                return dict(row)
        return None

    def insert(self, table, data):
        row = dict(data)
        row["id"] = len(self.tables.setdefault(table, [])) + 1
        self.tables[table].append(row)
        return row["id"]

    def update(self, table, data, condition, params=()):
        assert condition == "id = ?"
        target_id = params[0]
        for row in self.tables.get(table, []):
            if row["id"] == target_id:
                row.update(data)
                return
        raise AssertionError(f"Missing row {target_id} in {table}")

    def execute_query(self, query, params=()):
        if "FROM rifle_profile_details" in query:
            rifle_id = params[0] if params else None
            profile = self.profile_details.get(rifle_id)
            if profile is None:
                return []
            return [{"profile_json": profile}]
        if "FROM load_development_sessions" in query:
            rows = list(self.tables["load_development_sessions"])
            if params:
                rows = [row for row in rows if row.get("status") == params[0]]
            return [dict(row) for row in rows]
        return []


def test_create_loading_session_from_wizard_creates_canonical_and_legacy_records():
    db = _RecordingDb()
    db.profile_details[3] = (
        '{"active_barrel_id":"pipe-1","barrels":[{"id":"pipe-1","name":"24in Match","muzzle_device_type":"suppressor","muzzle_device_model":"A-TEC H2","muzzle_device_weight_g":420}]}'
    )
    rifle_page = SimpleNamespace(get_selected_rifle_id=lambda: 3)
    purpose_page = SimpleNamespace(get_selected_purpose=lambda: "langhold")
    component_page = SimpleNamespace(
        combo_bullet=_FakeCombo("ELD-M 140gr", 11),
        combo_powder=_FakeCombo("H4350", 22),
        combo_primer=_FakeCombo("CCI BR-2", 33),
    )
    recommendation_page = SimpleNamespace(
        recommendation_data={
            "avg_min_charge": 41.2,
            "avg_max_charge": 42.0,
            "source_count": 4,
        },
        best_history={"charge_weight": 41.8, "group_size_moa": 0.42},
    )

    legacy_session_id, load_session_id = (
        wizard_module._create_loading_session_from_wizard(
            db,
            rifle_page,
            purpose_page,
            component_page,
            recommendation_page,
        )
    )

    assert legacy_session_id == 1
    assert load_session_id == 1
    legacy_row = db.tables["loading_sessions"][0]
    canonical_row = db.tables["load_development_sessions"][0]
    assert legacy_row["load_session_id"] == load_session_id
    assert canonical_row["legacy_loading_session_id"] == legacy_session_id
    assert canonical_row["usage_profile_key"] == "langhold"
    assert canonical_row["barrel_id"] == "pipe-1"
    assert canonical_row["barrel_configuration_id"] == "pipe-1-suppressor-a-tec-h2"
    assert canonical_row["barrel_configuration_name"] == "Suppressor On (A-TEC H2)"
    assert (
        '"muzzle_device_type":"suppressor"'
        in canonical_row["barrel_configuration_snapshot_json"]
    )
    assert "Suggested working range" in canonical_row["notes"]


def test_resolve_wizard_barrel_configuration_context_prefers_selected_named_setup():
    db = _RecordingDb()
    db.profile_details[3] = (
        '{"active_barrel_id":"pipe-1","active_barrel_configuration_id":"cfg-suppressed","barrels":[{"id":"pipe-1","name":"24in Match","muzzle_device_type":"suppressor","muzzle_device_model":"A-TEC H2"}],"barrel_configurations":[{"id":"cfg-suppressed","name":"Match Suppressed","barrel_id":"pipe-1","is_active":true,"snapshot":{"muzzle_device_type":"suppressor","muzzle_device_model":"A-TEC H2"}},{"id":"cfg-brake","name":"Brake Training","barrel_id":"pipe-1","is_active":false,"snapshot":{"muzzle_device_type":"Muzzle Brake","muzzle_device_model":"Area 419","muzzle_device_weight_g":120}}]}'
    )

    context = wizard_module._resolve_wizard_barrel_configuration_context(
        db,
        3,
        rifle_data={"id": 3, "name": "Tikka T3x", "caliber": "6.5 CM"},
        selected_configuration_id="cfg-brake",
        selected_configuration_name="Brake Training",
    )

    assert context["barrel_configuration_id"] == "cfg-brake"
    assert context["barrel_configuration_name"] == "Brake Training"
    assert context["muzzle_device_type"] == "brake"
    assert context["barrel_configuration_snapshot"]["muzzle_device_model"] == "Area 419"


def test_create_loading_session_from_wizard_uses_selected_named_setup_from_rifle_page():
    db = _RecordingDb()
    db.profile_details[3] = (
        '{"active_barrel_id":"pipe-1","barrels":[{"id":"pipe-1","name":"24in Match","muzzle_device_type":"suppressor","muzzle_device_model":"A-TEC H2"}]}'
    )
    rifle_page = SimpleNamespace(
        get_selected_rifle_id=lambda: 3,
        get_selected_barrel_configuration_context=lambda: {
            "barrel_id": "pipe-1",
            "barrel_name": "24in Match",
            "barrel_configuration_id": "cfg-brake",
            "barrel_configuration_name": "Brake Training",
            "barrel_configuration_snapshot": {
                "barrel_id": "pipe-1",
                "muzzle_device_type": "brake",
                "muzzle_device_model": "Area 419",
            },
        },
    )
    purpose_page = SimpleNamespace(get_selected_purpose=lambda: "langhold")
    component_page = SimpleNamespace(
        combo_bullet=_FakeCombo("ELD-M 140gr", 11),
        combo_powder=_FakeCombo("H4350", 22),
        combo_primer=_FakeCombo("CCI BR-2", 33),
    )
    recommendation_page = SimpleNamespace(
        recommendation_data={
            "avg_min_charge": 41.2,
            "avg_max_charge": 42.0,
            "source_count": 4,
        },
        best_history={"charge_weight": 41.8, "group_size_moa": 0.42},
    )

    _, load_session_id = wizard_module._create_loading_session_from_wizard(
        db,
        rifle_page,
        purpose_page,
        component_page,
        recommendation_page,
    )

    assert load_session_id == 1
    canonical_row = db.tables["load_development_sessions"][0]
    assert canonical_row["barrel_configuration_id"] == "cfg-brake"
    assert canonical_row["barrel_configuration_name"] == "Brake Training"
    assert (
        '"muzzle_device_type":"brake"'
        in canonical_row["barrel_configuration_snapshot_json"]
    )
    assert "Setup: Brake Training" in canonical_row["notes"]
