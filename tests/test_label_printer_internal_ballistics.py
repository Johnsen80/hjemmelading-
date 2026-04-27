import sqlite3

from src.utils.label_printer import generate_label_text


class _Db:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE ammo_profiles (
                id INTEGER PRIMARY KEY,
                name TEXT,
                rifle_id INTEGER,
                caliber TEXT,
                powder_charge REAL,
                coal REAL,
                cbto REAL,
                bullet_id INTEGER,
                powder_id INTEGER,
                primer_id INTEGER,
                case_id INTEGER,
                component_context_json TEXT
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE bullets (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE powder (
                id INTEGER PRIMARY KEY,
                name TEXT,
                density REAL
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE primers (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE cases (
                id INTEGER PRIMARY KEY,
                name TEXT,
                case_capacity_gr_h2o REAL
            )
            """
        )


def test_generate_label_text_includes_internal_ballistics_from_db_context():
    db = _Db()
    db.cursor.execute("INSERT INTO bullets (id, name) VALUES (1, '175 SMK')")
    db.cursor.execute("INSERT INTO powder (id, name, density) VALUES (1, 'N150', 0.91)")
    db.cursor.execute("INSERT INTO primers (id, name) VALUES (1, 'Federal 210M')")
    db.cursor.execute(
        "INSERT INTO cases (id, name, case_capacity_gr_h2o) VALUES (1, 'Lapua .308', 56.0)"
    )
    db.cursor.execute(
        """
        INSERT INTO ammo_profiles (
            id, name, rifle_id, caliber, powder_charge, coal, cbto,
            bullet_id, powder_id, primer_id, case_id
        ) VALUES (1, '308 Match', 10, '.308 Win', 45.0, 71.1, 56.0, 1, 1, 1, 1)
        """
    )
    db.conn.commit()

    text = generate_label_text(db, ammo_profile_id=1)

    assert "Internballistikk" in text
    assert "Fyllrate:" in text
    assert "Krutttetthet:" in text


def test_generate_label_text_prefers_explicit_internal_ballistics_summary():
    db = _Db()
    db.cursor.execute(
        """
        INSERT INTO ammo_profiles (
            id, name, rifle_id, caliber, powder_charge, coal, cbto
        ) VALUES (1, '308 Match', 10, '.308 Win', 45.0, 71.1, 56.0)
        """
    )
    db.conn.commit()

    text = generate_label_text(
        db,
        ammo_profile_id=1,
        internal_ballistics_summary={
            "title": "Internballistikk",
            "message": "Fyllrate 98.2%, kompresjon 1.01x.",
            "metrics": [{"name": "Fyllrate", "value": "98.2%"}],
        },
    )

    assert "Internballistikk" in text
    assert "98.2%" in text


def test_generate_label_text_includes_component_context_summary():
    db = _Db()
    db.cursor.execute(
        """
        INSERT INTO ammo_profiles (
            id, name, rifle_id, caliber, powder_charge, coal, cbto, component_context_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "308 Match",
            10,
            ".308 Win",
            45.0,
            71.1,
            56.0,
            '{"bullet":{"name":"ELD-M","lot_number":"LOT-140A","uses_measured_lot_stats":true},"powder":{"name":"N540","lot_number":"N540-24A","lot_learning_title":"Merkbart lotavvik"}}',
        ),
    )
    db.conn.commit()

    text = generate_label_text(db, ammo_profile_id=1)

    assert "Component context:" in text
    assert "measured lot averages active" in text
    assert "Merkbart lotavvik" in text
