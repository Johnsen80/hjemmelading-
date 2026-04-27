"""
Database modul for Reloading Workshop Manager
Håndterer alle database-operasjoner med SQLite
"""

import datetime
import json
import math
import os
import shutil
import sqlite3
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

from HjemmeladingApp.utils.qt_compat import QSettings
from src.logging_config import configure_logging, get_logger
from src.utils.i18n import tr

from .caliber_standard import CaliberStandard
from .caliber_standard_data import get_example_caliber_standards

# Configure logging for database module
configure_logging()
logger = get_logger(__name__)
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Session, declarative_base, relationship

_DB_INSTANCE = None
_DB_PATH = None
_APP_STORAGE_DIRNAME = ".vault"
_DB_FILENAME = "reloading.db"


def _mark_path_hidden(path: Path) -> None:
    if os.name != "nt" or not path.exists():
        return
    try:
        import ctypes

        FILE_ATTRIBUTE_HIDDEN = 0x02
        FILE_ATTRIBUTE_SYSTEM = 0x04
        current = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if current == -1:
            return
        target_flags = current | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
        ctypes.windll.kernel32.SetFileAttributesW(str(path), target_flags)
    except Exception:
        pass


def get_private_storage_root() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        base_root = Path(local_appdata)
    else:
        base_root = Path.home() / "AppData" / "Local"
    return base_root / "Hjemmelading" / _APP_STORAGE_DIRNAME


def _legacy_db_candidates() -> list[Path]:
    candidates: list[Path] = []

    project_path = os.environ.get("HJEMMELADING_PROJECT_PATH")
    if not project_path and QSettings is not None:
        try:
            project_path = str(
                QSettings("ReloadingWorkshop", "ReloadingManager").value(
                    "workspace/current_project", ""
                )
                or ""
            ).strip()
        except Exception:
            project_path = ""

    if project_path:
        candidates.append(Path(project_path) / "data" / _DB_FILENAME)

    candidates.append(Path.cwd() / "data" / _DB_FILENAME)
    return [candidate for candidate in candidates if candidate.exists()]


def _prepare_private_db_path() -> str:
    storage_root = get_private_storage_root()
    target_path = storage_root / _DB_FILENAME
    storage_root.mkdir(parents=True, exist_ok=True)
    _mark_path_hidden(storage_root)

    if not target_path.exists():
        for legacy_path in _legacy_db_candidates():
            try:
                if legacy_path.resolve() == target_path.resolve():
                    break
            except Exception:
                pass
            try:
                shutil.copy2(legacy_path, target_path)
                break
            except Exception:
                continue

    if target_path.exists():
        _mark_path_hidden(target_path)

    return str(target_path)


def get_default_db_path() -> str:
    env_path = os.environ.get("HJEMMELADING_DB_PATH")
    if env_path:
        return env_path
    return _prepare_private_db_path()


def get_database(db_path: str | None = None, language: str = "en") -> "Database":
    global _DB_INSTANCE, _DB_PATH
    path = db_path or get_default_db_path()
    db_password = os.environ.get("HJEMMELADING_DB_PASSWORD") or None
    if _DB_INSTANCE is None or _DB_PATH != path:
        try:
            if _DB_INSTANCE is not None:
                _DB_INSTANCE.close()
        except Exception:
            pass
        _DB_INSTANCE = Database(
            db_path=path, language=language, db_password=db_password
        )
        _DB_PATH = path
    return _DB_INSTANCE


# SQLAlchemy ORM base
# Type Base as Any so mypy accepts using it as a runtime-generated base class
Base: Any = declarative_base()


# ORM-modell for PowderData
class PowderData(Base):  # type: ignore[misc]
    __tablename__ = "powder_data"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    manufacturer = Column(String)
    type = Column(String)
    burn_rate = Column(Float)
    energy_density = Column(Float)
    recommended_charge_min = Column(Float)
    recommended_charge_max = Column(Float)
    reference = Column(String)
    notes = Column(String)
    created_date = Column(String)


# ORM-modell for BulletData
class BulletData(Base):  # type: ignore[misc]
    __tablename__ = "bullet_data"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    manufacturer = Column(String)
    diameter = Column(Float)
    weight = Column(Float)
    bc = Column(Float)
    type = Column(String)
    length = Column(Float)
    recommended_twist = Column(Float)
    reference = Column(String)
    notes = Column(String)
    created_date = Column(String)


class CaseProfile(Base):  # type: ignore[misc]
    __tablename__ = "case_profile"
    id = Column(Integer, primary_key=True)
    caliber = Column(String)
    manufacturer = Column(String)
    nominal_length = Column(Float)
    nominal_weight = Column(Float)
    nominal_volume = Column(Float)
    notes = Column(String)
    # ...eventuelt flere felter...


class CaseLotMeasurement(Base):  # type: ignore[misc]
    __tablename__ = "case_lot_measurement"
    id = Column(Integer, primary_key=True)
    case_profile_id = Column(Integer, ForeignKey("case_profile.id"))
    lot_number = Column(String)
    avg_length = Column(Float)
    avg_weight = Column(Float)
    avg_volume = Column(Float)
    count = Column(Integer)
    notes = Column(String)
    case_profile = relationship("CaseProfile")
    # ...eventuelt flere felter...


class Database:
    """Hovedklasse for database-operasjoner"""

    def __init__(
        self,
        db_path: str | None = None,
        language: str = "en",
        db_password: str | None = None,
    ):
        """Initialiserer database-tilkobling"""
        if not db_path:
            db_path = get_default_db_path()
        self.db_path = db_path
        self.language = language
        self.db_password = (
            db_password or os.environ.get("HJEMMELADING_DB_PASSWORD") or None
        )
        self._closed = False

        # Sørg for at data-mappen eksisterer
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

        # Typed as Any so static analysis does not assume "None" at call-sites
        # `_connect()` will initialise these before use at runtime.
        self.conn: Any = None
        self.cursor: Any = None
        self._connect()
        self._create_tables()
        self._ensure_default_case_profiles()
        self._ensure_default_primer_profiles()
        self._seed_barrel_profiles()
        self._seed_rifles_from_json()

    def _connect(self):
        """Oppretter tilkobling til database, med støtte for kryptering hvis passord er satt"""
        if self.db_password:
            try:
                import sqlcipher3

                self.conn = sqlcipher3.connect(self.db_path)
                self.conn.execute(f"PRAGMA key='{self.db_password}';")
                self.conn.row_factory = sqlcipher3.dbapi2.Row
                self.cursor = self.conn.cursor()
            except Exception as exc:
                logger.error(f"SQLCipher-tilkobling feilet: {exc}")
                raise
        else:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Returnerer rader som dictionaries
            self.cursor = self.conn.cursor()
        _mark_path_hidden(Path(self.db_path))
        self._closed = False

    def close(self) -> None:
        """Close the database connection safely."""
        if self._closed:
            return
        try:
            if self.cursor is not None:
                self.cursor.close()
        except Exception:
            pass
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            pass
        self._closed = True

    def _ensure_column(self, table: str, column: str, column_def: str) -> None:
        """Best-effort migration to add missing columns on existing tables."""
        try:
            if self.conn is None or self.cursor is None:
                return
            existing = {
                row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")
            }
            if column in existing:
                return
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        except Exception as exc:
            logger.warning("Failed to ensure column %s on %s: %s", column, table, exc)

    def _create_tables(self):
        """Oppretter alle nødvendige tabeller"""

        # App/research settings + research-friendly structures
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS firearm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                caliber TEXT NOT NULL,
                barrel_length_mm INTEGER,
                twist TEXT,
                muzzle_device TEXT CHECK (
                    muzzle_device IN ('none', 'suppressor', 'brake')
                ) DEFAULT 'none',
                muzzle_device_weight_g INTEGER
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_bullet (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT,
                model TEXT,
                weight_gr REAL,
                bc REAL,
                diameter_mm REAL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_powder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT,
                name TEXT NOT NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_primer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                make TEXT,
                model TEXT
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_case (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT,
                model TEXT
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS load_recipe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firearm_id INTEGER,
                bullet_id INTEGER,
                powder_id INTEGER,
                primer_id INTEGER,
                case_id INTEGER,
                case_firings INTEGER,
                powder_charge_gr REAL,
                col_mm REAL,
                jump_mm REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (firearm_id) REFERENCES firearm(id) ON DELETE SET NULL,
                FOREIGN KEY (bullet_id) REFERENCES component_bullet(id) ON DELETE SET NULL,
                FOREIGN KEY (powder_id) REFERENCES component_powder(id) ON DELETE SET NULL,
                FOREIGN KEY (primer_id) REFERENCES component_primer(id) ON DELETE SET NULL,
                FOREIGN KEY (case_id) REFERENCES component_case(id) ON DELETE SET NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firearm_id INTEGER,
                label TEXT NOT NULL,
                distance_m INTEGER,
                temperature_c REAL,
                chronograph_type TEXT,
                status TEXT NOT NULL CHECK (status IN ('draft', 'locked')),
                started_at TEXT,
                locked_at TEXT,
                FOREIGN KEY (firearm_id) REFERENCES firearm(id) ON DELETE SET NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_session_id INTEGER NOT NULL,
                load_recipe_id INTEGER NOT NULL,
                shots_n INTEGER,
                velocity_avg_mps REAL,
                velocity_sd_mps REAL,
                velocity_es_mps REAL,
                group_size_mm REAL,
                group_moa REAL,
                pressure_signs_reported INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (test_session_id) REFERENCES test_session(id) ON DELETE CASCADE,
                FOREIGN KEY (load_recipe_id) REFERENCES load_recipe(id) ON DELETE CASCADE
            )
            """
        )

        # Tabell for målskiver (targets)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS targets_db (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                manufacturer TEXT,
                distance_m INTEGER,
                zone_data_json TEXT,  -- JSON med soneinndeling, poeng, diameter osv.
                metadata_json TEXT,   -- Ekstra info (f.eks. bilde, beskrivelse)
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Chronograph sessions and readings
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chronograph_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ammo_profile_id INTEGER,
                device_type TEXT NOT NULL,
                session_name TEXT,
                session_date TEXT NOT NULL,
                avg_velocity_fps REAL,
                es_fps REAL,
                sd_fps REAL,
                min_velocity_fps REAL,
                max_velocity_fps REAL,
                shot_count INTEGER,
                temperature_f REAL,
                notes TEXT,
                raw_data_json TEXT,
                import_source TEXT,
                import_meta_json TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id) ON DELETE SET NULL
            )
            """
        )
        self._ensure_column(
            "chronograph_sessions", "import_source", "import_source TEXT"
        )
        self._ensure_column(
            "chronograph_sessions", "import_meta_json", "import_meta_json TEXT"
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chronograph_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                shot_number INTEGER,
                velocity_fps REAL,
                timestamp TEXT,
                temperature_f REAL,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES chronograph_sessions(id) ON DELETE CASCADE
            )
            """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chronograph_sessions_date ON chronograph_sessions(session_date)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chronograph_readings_session ON chronograph_readings(session_id)"
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed')),
                retry_count INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TEXT,
                last_error TEXT
            )
            """
        )

        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_result_session ON test_result(test_session_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_result_recipe ON test_result(load_recipe_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_research_outbox_status ON research_outbox(status)"
        )

        # Rifles tabell - KOMPLETT MED HARMONISK DATA
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rifles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,

                -- Grunnleggende info
                manufacturer TEXT,
                model TEXT,
                weapon_type TEXT DEFAULT 'rifle',
                caliber TEXT NOT NULL,
                action_type TEXT,  -- 'bolt', 'semi-auto', 'lever', 'single-shot'
                preferred_units TEXT DEFAULT 'metric',
                serial_number TEXT,
                purchase_date TEXT,

                -- Pipe/Løp detaljer
                barrel_length_mm REAL,
                barrel_length_inches REAL,
                barrel_contour TEXT,  -- 'light', 'medium', 'heavy', 'varmint', 'bull', 'custom'
                barrel_profile_id INTEGER,  -- FK til barrel_profiles tabell
                barrel_manufacturer TEXT,
                barrel_material TEXT,  -- 'chrome-moly', 'stainless', 'carbon-fiber'
                barrel_finish TEXT,  -- 'blued', 'stainless', 'cerakote', 'nitride'

                -- Twist rate og rifling
                twist_rate TEXT,  -- '1:8', '1:10', etc
                twist_rate_inches REAL,  -- 8.0, 10.0 for calculations
                twist_direction TEXT,  -- 'right', 'left'
                rifling_type TEXT,  -- 'conventional', 'polygonal', '5R', 'button', 'cut'
                groove_count INTEGER,  -- 4, 6, etc
                groove_depth_mm REAL,

                -- Dimensjoner for harmonisk beregning
                muzzle_diameter_mm REAL,
                breech_diameter_mm REAL,
                mid_barrel_diameter_mm REAL,
                barrel_weight_grams REAL,

                -- Befestning/mounting
                barrel_attachment TEXT,  -- 'threaded', 'press-fit', 'pinned', 'tension-barrel'
                action_threads TEXT,  -- 'Remington 700', 'Savage small shank', etc
                thread_pitch TEXT,  -- '16 TPI', '20 TPI'
                barrel_nut BOOLEAN DEFAULT 0,
                torque_spec_nm REAL,  -- Torque specification

                -- Kammerdetaljer
                chamber_spec TEXT,  -- 'SAAMI', 'CIP', 'match', 'custom'
                freebore_mm REAL,
                throat_angle_deg REAL,
                leade_length_mm REAL,

                -- Skuddteller
                round_count INTEGER DEFAULT 0,
                last_cleaned_round_count INTEGER DEFAULT 0,
                accuracy_life_estimate INTEGER,  -- Estimated accurate barrel life

                -- Vedlikehold og tilstand
                last_cleaning_date TEXT,
                last_maintenance_date TEXT,
                bore_condition TEXT,  -- 'excellent', 'good', 'fair', 'worn'
                throat_erosion_mm REAL,
                accuracy_baseline_moa REAL,  -- Original accuracy
                current_accuracy_moa REAL,  -- Current accuracy (tracks degradation)

                -- Max COAL for magazine
                max_coal_magazine_mm REAL,
                max_coal_magazine_inches REAL,

                -- Bullet jump measurement (for specific bullet)
                jam_length_cbto_mm REAL,  -- Measured with specific bullet
                jam_measurement_bullet_id INTEGER,
                jam_measurement_date TEXT,

                -- Harmonisk data
                fundamental_frequency_hz REAL,  -- Calculated or measured
                harmonic_nodes TEXT,  -- JSON array of calculated node positions
                optimal_bullet_weight_range TEXT,  -- 'e.g., 139-147gr'

                -- Notater og konfigurasjon
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT,

                FOREIGN KEY (barrel_profile_id) REFERENCES barrel_profiles(id),
                FOREIGN KEY (jam_measurement_bullet_id) REFERENCES bullets(id)
            )
        """
        )

        # Extended rifle profile details (stored as JSON)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rifle_profile_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL UNIQUE,
                profile_json TEXT NOT NULL,
                updated_at TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE
            )
        """
        )
        self._ensure_column("rifles", "weapon_type", "weapon_type TEXT DEFAULT 'rifle'")
        self._ensure_column(
            "rifles", "preferred_units", "preferred_units TEXT DEFAULT 'metric'"
        )

        # Self-learning barrel / lop profile (digital twin groundwork)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS barrel_learning_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                barrel_id TEXT NOT NULL,
                barrel_name TEXT,
                status TEXT DEFAULT 'insufficient_data',
                confidence_score REAL DEFAULT 0,
                data_points INTEGER DEFAULT 0,
                chrono_samples INTEGER DEFAULT 0,
                target_samples INTEGER DEFAULT 0,
                temperature_samples INTEGER DEFAULT 0,
                calibration_offset_fps REAL DEFAULT 0,
                temp_sensitivity_fps_per_c REAL,
                typical_es_fps REAL,
                typical_sd_fps REAL,
                cold_bore_shift_moa REAL,
                warm_bore_shift_moa REAL,
                throat_erosion_mm REAL,
                estimated_barrel_life_used_percent REAL,
                drift_flag TEXT,
                notes TEXT,
                profile_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                UNIQUE(rifle_id, barrel_id)
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cartridge_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caliber_name TEXT NOT NULL,
                alt_name TEXT,
                standard_body TEXT,
                standard_label TEXT,
                pressure_method TEXT,
                max_pressure_bar REAL,
                max_pressure_psi REAL,
                oal_mm REAL,
                case_length_mm REAL,
                case_capacity_ml REAL,
                bullet_diameter_mm REAL,
                neck_diameter_mm REAL,
                shoulder_diameter_mm REAL,
                base_diameter_mm REAL,
                rim_diameter_mm REAL,
                freebore_mm REAL,
                throat_angle_deg REAL,
                drawing_pdf_url TEXT,
                drawing_image_url TEXT,
                source TEXT,
                source_kind TEXT,
                evidence_level TEXT,
                user_defined INTEGER DEFAULT 0,
                raw_json TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cartridge_standards_name ON cartridge_standards(caliber_name)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cartridge_standards_body ON cartridge_standards(standard_body)"
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_reference_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_system TEXT NOT NULL,
                component_type TEXT NOT NULL,
                manufacturer TEXT,
                model_name TEXT,
                display_name TEXT,
                caliber TEXT,
                weight_grains REAL,
                diameter_mm REAL,
                length_mm REAL,
                lot_number TEXT,
                source_file TEXT,
                source_label TEXT,
                evidence_level TEXT,
                profile_json TEXT,
                raw_json TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_component_reference_snapshots_lookup ON component_reference_snapshots(source_system, component_type, manufacturer, model_name, caliber)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_barrel_learning_profiles_rifle ON barrel_learning_profiles(rifle_id)"
        )

        # Optikk tabell
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS optics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manufacturer TEXT,
                magnification TEXT,
                reticle TEXT,
                click_value_elevation REAL NOT NULL,
                click_value_windage REAL NOT NULL,
                click_unit TEXT NOT NULL,
                zero_distance REAL DEFAULT 100,
                rifle_id INTEGER,
                notes TEXT,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id)
            )
        """
        )

        # Kalibere tabell (for GRT import)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calibers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                case_length_mm REAL,
                case_capacity_ml REAL,
                max_pressure_bar REAL,
                bullet_diameter_mm REAL,
                neck_diameter_mm REAL,
                base_diameter_mm REAL,
                rim_diameter_mm REAL,
                description TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Rimfire (22LR) ammo database
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rimfire_ammo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                velocity_fps REAL,
                bc REAL,
                country TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rimfire_ammo_brand ON rimfire_ammo(brand)"
        )

        # Rimfire (22LR) lot testing and observations
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rimfire_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ammo_id INTEGER,
                ammo_name TEXT,
                lot_number TEXT NOT NULL,
                factory_velocity_fps REAL,
                factory_bc REAL,
                test_velocity_fps REAL,
                group_mm REAL,
                notes TEXT,
                image_path TEXT,
                weapon_type TEXT,
                pistol_target_type TEXT,
                pistol_trigger TEXT,
                pistol_magazin INTEGER,
                pistol_score TEXT,
                pistol_image_path TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ammo_id) REFERENCES rimfire_ammo(id) ON DELETE SET NULL
            )
            """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rimfire_lots_ammo ON rimfire_lots(ammo_id)"
        )

        # Rimfire (22LR) weather logging
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rimfire_weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature_c REAL,
                wind_ms REAL,
                wind_dir_deg REAL,
                pressure_hpa REAL,
                humidity_percent REAL,
                cloud_percent REAL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Ammo test reports - lot testing tied to weapon/barrel context
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ammo_test_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id TEXT UNIQUE NOT NULL,
                ammo_profile_id INTEGER,
                ammo_profile_name TEXT,
                lot_number TEXT NOT NULL,
                manufacturer TEXT,
                model TEXT,
                caliber TEXT,
                test_date TEXT,
                log_time TEXT,
                velocity_list TEXT,
                group_size_list TEXT,
                case_spec TEXT,
                bullet_spec TEXT,
                powder_spec TEXT,
                primer_spec TEXT,
                weapon_weight REAL,
                notes TEXT,
                image_path TEXT,
                rifle_id INTEGER,
                rifle_name TEXT,
                barrel_id TEXT,
                barrel_name TEXT,
                ammo_type TEXT DEFAULT 'centerfire',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE SET NULL,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id) ON DELETE SET NULL
            )
            """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ammo_test_reports_model ON ammo_test_reports(caliber, manufacturer, model)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ammo_test_reports_rifle ON ammo_test_reports(rifle_id, barrel_id)"
        )
        self._ensure_column(
            "ammo_test_reports", "ammo_profile_id", "ammo_profile_id INTEGER"
        )
        self._ensure_column(
            "ammo_test_reports", "ammo_profile_name", "ammo_profile_name TEXT"
        )
        self._ensure_column("ammo_test_reports", "rifle_id", "rifle_id INTEGER")
        self._ensure_column("ammo_test_reports", "rifle_name", "rifle_name TEXT")
        self._ensure_column("ammo_test_reports", "barrel_id", "barrel_id TEXT")
        self._ensure_column("ammo_test_reports", "barrel_name", "barrel_name TEXT")
        self._ensure_column(
            "ammo_test_reports", "ammo_type", "ammo_type TEXT DEFAULT 'centerfire'"
        )

        # Komponenter - Krutt
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS powder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manufacturer TEXT,
                type TEXT,
                burn_rate TEXT,
                density REAL,
                quantity_grams REAL DEFAULT 0,
                cost_per_unit REAL,
                purchase_date TEXT,
                notes TEXT,
                description TEXT
            )
        """
        )
        self._ensure_column("powder", "source", "source TEXT")
        self._ensure_column("powder", "source_kind", "source_kind TEXT")
        self._ensure_column("powder", "evidence_level", "evidence_level TEXT")
        self._ensure_column("powder", "source_version", "source_version TEXT")
        self._ensure_column("powder", "external_id", "external_id TEXT")
        self._ensure_column("powder", "external_ref", "external_ref TEXT")
        self._ensure_column("powder", "display_name", "display_name TEXT")
        self._ensure_column("powder", "source_label", "source_label TEXT")
        self._ensure_column("powder", "profile_json", "profile_json TEXT")
        self._ensure_column("powder", "raw_json", "raw_json TEXT")

        # Barrel Profiles - Predefinerte løpsprofiler med mål for harmonisk beregning
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS barrel_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                category TEXT,  -- 'hunting', 'target', 'tactical', 'benchrest', 'varmint'

                -- Dimensjoner (typiske verdier)
                muzzle_diameter_mm REAL NOT NULL,
                muzzle_diameter_inches REAL,
                breech_diameter_mm REAL NOT NULL,
                breech_diameter_inches REAL,

                -- Konturdetaljer
                taper_type TEXT,  -- 'straight', 'tapered', 'stepped', 'fluted'
                taper_rate_per_inch REAL,  -- mm reduction per inch
                typical_length_inches REAL,

                -- Vektberegning
                weight_per_inch_grams REAL,
                typical_total_weight_grams REAL,

                -- Stivhet og harmonikk
                stiffness_rating TEXT,  -- 'very-light', 'light', 'medium', 'heavy', 'very-heavy', 'bull'
                harmonic_characteristics TEXT,  -- Description of typical behavior

                -- Anbefalt bruk
                recommended_for TEXT,  -- 'precision', 'hunting', 'competition', 'tactical'
                typical_calibers TEXT,  -- '.223, .308, 6.5CM'

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Komponenter - Kuler
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bullets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manufacturer TEXT,
                caliber TEXT NOT NULL,
                weight_grains REAL NOT NULL,
                diameter_mm REAL,
                length_mm REAL,
                bc_g1 REAL,
                bc_g7 REAL,
                bc_segments_json TEXT,
                bullet_type TEXT,
                quantity INTEGER DEFAULT 0,
                cost_per_unit REAL,
                notes TEXT,
                description TEXT
            )
        """
        )
        self._ensure_column("bullets", "source", "source TEXT")
        self._ensure_column("bullets", "source_kind", "source_kind TEXT")
        self._ensure_column("bullets", "evidence_level", "evidence_level TEXT")
        self._ensure_column("bullets", "source_version", "source_version TEXT")
        self._ensure_column("bullets", "external_id", "external_id TEXT")
        self._ensure_column("bullets", "external_ref", "external_ref TEXT")
        self._ensure_column("bullets", "display_name", "display_name TEXT")
        self._ensure_column("bullets", "source_label", "source_label TEXT")
        self._ensure_column("bullets", "profile_json", "profile_json TEXT")
        self._ensure_column("bullets", "raw_json", "raw_json TEXT")

        # Komponenter - Tennhetter
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS primers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manufacturer TEXT,
                type TEXT,
                size TEXT,
                quantity INTEGER DEFAULT 0,
                cost_per_unit REAL,
                notes TEXT
            )
        """
        )
        self._ensure_column("primers", "product_line", "product_line TEXT")
        self._ensure_column("primers", "part_number", "part_number TEXT")
        self._ensure_column("primers", "source_kind", "source_kind TEXT")
        self._ensure_column(
            "primers", "manufacturer_source", "manufacturer_source TEXT"
        )
        self._ensure_column("primers", "match_grade", "match_grade INTEGER DEFAULT 0")
        self._ensure_column("primers", "magnum", "magnum INTEGER DEFAULT 0")
        self._ensure_column("primers", "ar_variant", "ar_variant INTEGER DEFAULT 0")
        self._ensure_column(
            "primers", "nominal_diameter_in", "nominal_diameter_in REAL"
        )
        self._ensure_column("primers", "used_for", "used_for TEXT")
        self._ensure_column("primers", "box_count", "box_count INTEGER")
        self._ensure_column("primers", "case_count", "case_count INTEGER")
        self._ensure_column("primers", "composition_class", "composition_class TEXT")
        self._ensure_column(
            "primers", "non_corrosive", "non_corrosive INTEGER DEFAULT 1"
        )
        self._ensure_column("primers", "lead_free", "lead_free INTEGER DEFAULT 0")
        self._ensure_column("primers", "temperature_claim", "temperature_claim TEXT")
        self._ensure_column("primers", "primer_family", "primer_family TEXT")
        self._ensure_column("primers", "cup_thickness_in", "cup_thickness_in REAL")
        self._ensure_column("primers", "cup_hardness_class", "cup_hardness_class TEXT")
        self._ensure_column(
            "primers",
            "pressure_tolerance_class",
            "pressure_tolerance_class TEXT",
        )
        self._ensure_column(
            "primers",
            "ignition_strength_class",
            "ignition_strength_class TEXT",
        )
        self._ensure_column(
            "primers",
            "recommended_pressure_min_psi",
            "recommended_pressure_min_psi REAL",
        )
        self._ensure_column(
            "primers",
            "recommended_pressure_max_psi",
            "recommended_pressure_max_psi REAL",
        )
        self._ensure_column(
            "primers",
            "cold_weather_suitability",
            "cold_weather_suitability TEXT",
        )
        self._ensure_column(
            "primers",
            "primer_sign_interpretation",
            "primer_sign_interpretation TEXT",
        )
        self._ensure_column("primers", "evidence_level", "evidence_level TEXT")
        self._ensure_column("primers", "reference_source", "reference_source TEXT")

        # Komponenter - Hylser (Brass/Case Management)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                manufacturer TEXT,
                caliber TEXT NOT NULL,
                material TEXT DEFAULT 'brass',
                quantity INTEGER DEFAULT 0,
                times_fired INTEGER DEFAULT 0,
                last_annealed TEXT,
                needs_annealing BOOLEAN DEFAULT 0,
                notes TEXT,
                -- Nye kolonner for avansert tracking
                lot_number TEXT,
                purchase_date TEXT,
                case_capacity_gr_h2o REAL,
                avg_weight_gr REAL,
                wall_thickness TEXT,
                neck_thickness_mm REAL,
                retired_quantity INTEGER DEFAULT 0,
                last_trimmed_date TEXT,
                trim_length_mm REAL,
                primer_pocket_uniformed BOOLEAN DEFAULT 0,
                flash_hole_deburred BOOLEAN DEFAULT 0
            )
        """
        )
        self._ensure_column("cases", "material", "material TEXT DEFAULT 'brass'")
        self._ensure_column("cases", "quantity", "quantity INTEGER DEFAULT 0")
        self._ensure_column("cases", "times_fired", "times_fired INTEGER DEFAULT 0")
        self._ensure_column("cases", "last_annealed", "last_annealed TEXT")
        self._ensure_column(
            "cases", "needs_annealing", "needs_annealing BOOLEAN DEFAULT 0"
        )
        self._ensure_column("cases", "notes", "notes TEXT")
        self._ensure_column("cases", "lot_number", "lot_number TEXT")
        self._ensure_column("cases", "purchase_date", "purchase_date TEXT")
        self._ensure_column(
            "cases", "case_capacity_gr_h2o", "case_capacity_gr_h2o REAL"
        )
        self._ensure_column("cases", "avg_weight_gr", "avg_weight_gr REAL")
        self._ensure_column("cases", "wall_thickness", "wall_thickness TEXT")
        self._ensure_column("cases", "neck_thickness_mm", "neck_thickness_mm REAL")
        self._ensure_column(
            "cases", "retired_quantity", "retired_quantity INTEGER DEFAULT 0"
        )
        self._ensure_column("cases", "last_trimmed_date", "last_trimmed_date TEXT")
        self._ensure_column("cases", "trim_length_mm", "trim_length_mm REAL")
        self._ensure_column(
            "cases",
            "primer_pocket_uniformed",
            "primer_pocket_uniformed BOOLEAN DEFAULT 0",
        )
        self._ensure_column(
            "cases",
            "flash_hole_deburred",
            "flash_hole_deburred BOOLEAN DEFAULT 0",
        )

        # Case Measurements (detaljert måling per hylse eller batch)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS case_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                measurement_date TEXT NOT NULL,
                case_length_mm REAL,
                neck_diameter_mm REAL,
                neck_thickness_mm REAL,
                base_diameter_mm REAL,
                shoulder_diameter_mm REAL,
                case_weight_gr REAL,
                primer_pocket_depth_mm REAL,
                flash_hole_diameter_mm REAL,
                concentricity_tir_mm REAL,
                measurement_type TEXT,  -- 'new', 'fired', 'sized', 'after_trim'
                notes TEXT,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS case_learning_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL UNIQUE,
                status TEXT DEFAULT 'insufficient_data',
                confidence_score REAL DEFAULT 0,
                data_points INTEGER DEFAULT 0,
                h2o_samples INTEGER DEFAULT 0,
                firing_events INTEGER DEFAULT 0,
                prep_events INTEGER DEFAULT 0,
                anneal_events INTEGER DEFAULT 0,
                avg_case_capacity_h2o REAL,
                capacity_spread_h2o REAL,
                avg_case_weight_gr REAL,
                typical_times_fired REAL,
                estimated_remaining_cycles REAL,
                drift_flag TEXT,
                notes TEXT,
                profile_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_case_learning_profiles_case ON case_learning_profiles(case_id)"
        )

        # Case Firing Log (logg hver gang et batch skyttes)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS case_firing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                firing_date TEXT NOT NULL,
                rounds_fired INTEGER NOT NULL,
                rifle_id INTEGER,
                ammo_profile_id INTEGER,
                pressure_level TEXT,  -- 'low', 'medium', 'high', 'max'
                case_head_expansion_inch REAL,
                primer_condition TEXT,  -- 'good', 'flattened', 'cratered'
                annealing_due BOOLEAN DEFAULT 0,
                trim_due BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id),
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id)
            )
        """
        )

        # Rifle Bullet Jump Measurements - COAL/CBTO jam målinger per rifle+bullet
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rifle_bullet_jump_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                barrel_id TEXT,
                barrel_name TEXT,
                bullet_id INTEGER NOT NULL,

                -- Måling dato
                measurement_date TEXT NOT NULL,

                -- Jam length målinger (der kulen berører riflingen)
                jam_coal_mm REAL NOT NULL,
                neck_tension_inches REAL,  -- NY: Gjennomsnittlig neck tension (innsatt kule vs neck ID)
                jam_coal_inches REAL,
                jam_cbto_mm REAL,
                jam_cbto_inches REAL,

                -- Målemetode
                measurement_method TEXT,  -- 'hornady_oal_gauge', 'fired_case_method', 'split_neck', 'comparator'
                measurement_tool TEXT,  -- 'Hornady Lock-N-Load', 'Davidson', 'Manual'

                -- Anbefalte verdier basert på målingen
                recommended_jam_minus_010_mm REAL,  -- Jam - 0.010"
                recommended_jam_minus_020_mm REAL,  -- Jam - 0.020"
                recommended_jam_minus_030_mm REAL,  -- Jam - 0.030"
                recommended_jam_minus_040_mm REAL,  -- Jam - 0.040"

                -- Variasjoner (hvis gjentatt måling)
                measurement_variation_mm REAL,  -- Standard deviation hvis flere målinger
                measurements_count INTEGER DEFAULT 1,

                -- Throat erosjon tracking
                throat_erosion_since_baseline_mm REAL,
                rounds_fired_at_measurement INTEGER,  -- Hvor mange skudd var fyrt ved denne målingen

                notes TEXT,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                FOREIGN KEY (bullet_id) REFERENCES bullets(id) ON DELETE CASCADE,
                UNIQUE(rifle_id, bullet_id, measurement_date)  -- Kan ha flere målinger over tid
            )
        """
        )
        self._ensure_column(
            "rifle_bullet_jump_measurements", "barrel_id", "barrel_id TEXT"
        )
        self._ensure_column(
            "rifle_bullet_jump_measurements", "barrel_name", "barrel_name TEXT"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_jump_measurements_barrel ON rifle_bullet_jump_measurements(rifle_id, barrel_id, bullet_id, measurement_date)"
        )

        # Case Annealing Log
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS case_annealing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                annealing_date TEXT NOT NULL,
                method TEXT,  -- 'flame', 'induction', 'amp'
                temperature_f INTEGER,
                time_seconds REAL,
                templaq_verified BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )

        # Case Prep Log (trimming, uniforming, etc.)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS case_prep_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                prep_date TEXT NOT NULL,
                trimmed BOOLEAN DEFAULT 0,
                trim_length_mm REAL,
                chamfered BOOLEAN DEFAULT 0,
                deburred BOOLEAN DEFAULT 0,
                primer_pocket_uniformed BOOLEAN DEFAULT 0,
                flash_hole_deburred BOOLEAN DEFAULT 0,
                neck_turned BOOLEAN DEFAULT 0,
                neck_thickness_final_mm REAL,
                weight_sorted BOOLEAN DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """
        )

        # Rifle Maintenance Log - Skuddteller og vedlikehold
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rifle_maintenance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                maintenance_date TEXT NOT NULL,
                maintenance_type TEXT NOT NULL,  -- 'cleaning', 'deep_clean', 'inspection', 'repair', 'accuracy_test'

                -- Skuddteller ved tidspunkt
                rounds_fired_before INTEGER,
                rounds_fired_after INTEGER,

                -- Vedlikeholdsdetaljer
                bore_cleaned BOOLEAN DEFAULT 0,
                carbon_removed BOOLEAN DEFAULT 0,
                copper_removed BOOLEAN DEFAULT 0,
                action_cleaned BOOLEAN DEFAULT 0,
                action_lubricated BOOLEAN DEFAULT 0,

                -- Tilstandsvurdering
                bore_condition_rating INTEGER,  -- 1-10 scale
                throat_condition TEXT,  -- 'excellent', 'good', 'fair', 'worn'
                throat_erosion_mm REAL,

                -- Nøyaktighetstesting
                accuracy_test_performed BOOLEAN DEFAULT 0,
                accuracy_result_moa REAL,
                group_size_mm REAL,
                group_size_inches REAL,
                shots_count INTEGER,

                -- Produkter brukt
                cleaning_products_used TEXT,
                bore_guide_used BOOLEAN DEFAULT 0,

                notes TEXT,
                next_maintenance_due_rounds INTEGER,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE
            )
        """
        )

        # Case Wear Warning System - Når skal hylser måles
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS case_measurement_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                case_id INTEGER NOT NULL,

                -- Syklus innstillinger
                measurement_interval_rounds INTEGER DEFAULT 500,  -- Mål hver 500 skudd
                last_measurement_round_count INTEGER DEFAULT 0,
                next_measurement_due_round_count INTEGER,

                -- Varsel status
                warning_active BOOLEAN DEFAULT 0,
                warning_triggered_date TEXT,
                measurement_completed BOOLEAN DEFAULT 0,
                measurement_completed_date TEXT,

                -- Link til målingene
                last_measurement_id INTEGER,  -- FK til case_measurements

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (last_measurement_id) REFERENCES case_measurements(id),
                UNIQUE(rifle_id, case_id)  -- Én schedule per rifle+case kombinasjon
            )
        """
        )

        # Ammunisjonsprofiler
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ammo_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rifle_id INTEGER,
                caliber TEXT NOT NULL,
                bullet_id INTEGER,
                bullet_weight REAL NOT NULL,
                powder_id INTEGER,
                powder_charge REAL NOT NULL,
                primer_id INTEGER,
                case_id INTEGER,
                coal REAL,
                cbto REAL,
                velocity_fps REAL,
                bc_g1 REAL,
                bc_g7 REAL,
                bc_segments_json TEXT,
                bullet_runout_tir REAL,  -- NY: Total Indicated Runout (TIR) på kule
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (bullet_id) REFERENCES bullets (id),
                FOREIGN KEY (powder_id) REFERENCES powder (id),
                FOREIGN KEY (primer_id) REFERENCES primers (id),
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """
        )
        self._ensure_column("bullets", "bc_segments_json", "bc_segments_json TEXT")
        self._ensure_column(
            "ammo_profiles", "bc_segments_json", "bc_segments_json TEXT"
        )
        self._ensure_column(
            "ammo_profiles", "component_context_json", "component_context_json TEXT"
        )

        # Ladder Tests
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ladder_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                load_session_id INTEGER,
                rifle_id INTEGER,
                date TEXT NOT NULL,
                caliber TEXT NOT NULL,
                bullet_id INTEGER,
                powder_id INTEGER,
                primer_id INTEGER,
                case_id INTEGER,
                start_charge REAL NOT NULL,
                end_charge REAL NOT NULL,
                step_size REAL NOT NULL,
                distance_meters REAL,
                temperature REAL,
                humidity REAL,
                notes TEXT,
                FOREIGN KEY (load_session_id) REFERENCES load_development_sessions (id),
                FOREIGN KEY (rifle_id) REFERENCES rifles (id)
            )
        """
        )

        # Test Resultater
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ladder_test_id INTEGER,
                load_session_id INTEGER,
                charge_weight REAL NOT NULL,
                velocity_1 REAL,
                velocity_2 REAL,
                velocity_3 REAL,
                velocity_avg REAL,
                velocity_es REAL,
                velocity_sd REAL,
                group_size_mm REAL,
                group_size_moa REAL,
                vertical_spread REAL,
                horizontal_spread REAL,
                pressure_signs TEXT,
                image_path TEXT,
                notes TEXT,
                case_head_expansion_inches REAL,  -- NY: Base ekspansjon målt med mikrometer
                bullet_runout_tir REAL,  -- NY: Total Indicated Runout (TIR) på kule
                FOREIGN KEY (load_session_id) REFERENCES load_development_sessions (id),
                FOREIGN KEY (ladder_test_id) REFERENCES ladder_tests (id)
            )
        """
        )

        # Load Development Workflows
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS load_development_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rifle_id INTEGER,
                barrel_id TEXT,
                barrel_name TEXT,
                bullet_id INTEGER,
                powder_id INTEGER,
                usage_profile TEXT,
                caliber TEXT NOT NULL,
                test_protocol TEXT,
                status TEXT DEFAULT 'active',
                stage TEXT DEFAULT 'load_created',
                progress INTEGER DEFAULT 0,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                test_date TEXT,
                completed_date TEXT,
                target_es_sd REAL,
                target_group_size REAL,
                final_charge REAL,
                final_coal REAL,
                final_cbto REAL,
                next_action TEXT,
                notes TEXT,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (bullet_id) REFERENCES bullets (id),
                FOREIGN KEY (powder_id) REFERENCES powder (id)
            )
        """
        )

        # Canonical load-development sessions
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS load_development_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uid TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active',
                lifecycle_stage TEXT NOT NULL DEFAULT 'intake',
                rifle_id INTEGER,
                rifle_name TEXT,
                rifle_caliber TEXT,
                barrel_id TEXT,
                barrel_name TEXT,
                barrel_configuration_id TEXT,
                barrel_configuration_name TEXT,
                ammo_profile_id INTEGER,
                usage_profile_key TEXT,
                usage_profile_name TEXT,
                subsonic_mode INTEGER DEFAULT 0,
                quantity_target INTEGER,
                recommended_charge_min_gr REAL,
                recommended_charge_max_gr REAL,
                recommended_coal_min REAL,
                recommended_coal_max REAL,
                confidence_label TEXT,
                confidence_score REAL,
                safety_status TEXT,
                next_action TEXT,
                session_verdict TEXT,
                legacy_loading_session_id INTEGER,
                intake_snapshot_json TEXT,
                component_selection_json TEXT,
                component_lots_json TEXT,
                recommendation_json TEXT,
                barrel_configuration_snapshot_json TEXT,
                evidence_summary_json TEXT,
                learning_state_json TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id),
                FOREIGN KEY (legacy_loading_session_id) REFERENCES loading_sessions (id)
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_load_dev_sessions_status ON load_development_sessions(status)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_load_dev_sessions_stage ON load_development_sessions(lifecycle_stage)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_load_dev_sessions_legacy ON load_development_sessions(legacy_loading_session_id)"
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chronograph_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                ammo_profile_id INTEGER,
                load_session_id INTEGER,
                import_date TEXT DEFAULT CURRENT_TIMESTAMP,
                velocity_count INTEGER,
                velocity_avg REAL,
                velocity_es REAL,
                velocity_sd REAL,
                velocities_json TEXT,
                notes TEXT,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id) ON DELETE SET NULL,
                FOREIGN KEY (load_session_id) REFERENCES load_development_sessions(id) ON DELETE SET NULL
            )
        """
        )
        self._ensure_column(
            "chronograph_imports", "load_session_id", "load_session_id INTEGER"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chronograph_imports_load_session ON chronograph_imports(load_session_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_load_dev_sessions_rifle ON load_development_sessions(rifle_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_load_dev_sessions_legacy ON load_development_sessions(legacy_loading_session_id)"
        )
        self._ensure_column(
            "load_development_sessions",
            "barrel_configuration_id",
            "barrel_configuration_id TEXT",
        )
        self._ensure_column(
            "load_development_sessions",
            "barrel_configuration_name",
            "barrel_configuration_name TEXT",
        )
        self._ensure_column(
            "load_development_sessions",
            "subsonic_mode",
            "subsonic_mode INTEGER DEFAULT 0",
        )
        self._ensure_column(
            "load_development_sessions",
            "session_verdict",
            "session_verdict TEXT",
        )
        self._ensure_column(
            "load_development_sessions",
            "component_lots_json",
            "component_lots_json TEXT",
        )
        self._ensure_column(
            "load_development_sessions",
            "barrel_configuration_snapshot_json",
            "barrel_configuration_snapshot_json TEXT",
        )

        # Comprehensive data logs (full session snapshots)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comprehensive_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                load_id TEXT NOT NULL UNIQUE,
                load_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                session_date TEXT,
                session_time TEXT,
                session_type TEXT,
                session_location TEXT,
                session_distance_m INTEGER,
                ammo_caliber TEXT,
                rifle_name TEXT,
                data_json TEXT NOT NULL
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_comprehensive_logs_created_at ON comprehensive_logs(created_at)"
        )

        # Ladeøkter (logg)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS loading_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                project_name TEXT,
                project_path TEXT,
                ammo_profile_id INTEGER,
                quantity INTEGER NOT NULL,
                coal_min REAL,
                coal_max REAL,
                powder_weight_min REAL,
                powder_weight_max REAL,
                time_minutes INTEGER,
                total_cost REAL,
                notes TEXT,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id)
            )
        """
        )

        # Temperature Tests
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS temperature_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ammo_profile_id INTEGER,
                rifle_id INTEGER,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id),
                FOREIGN KEY (rifle_id) REFERENCES rifles (id)
            )
        """
        )

        # Temperature Test Data
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS temperature_test_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                temperature_c REAL NOT NULL,
                velocity_fps INTEGER NOT NULL,
                es_fps INTEGER,
                sd_fps REAL,
                test_date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (test_id) REFERENCES temperature_tests (id)
            )
        """
        )

        # Component Lots
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_type TEXT NOT NULL,
                component_id INTEGER NOT NULL,
                lot_number TEXT NOT NULL,
                purchase_date TEXT NOT NULL,
                quantity_initial REAL NOT NULL,
                quantity_remaining REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                performance_rating TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS seating_depth_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                barrel_id TEXT,
                barrel_name TEXT,
                bullet_id INTEGER NOT NULL,
                component_lot_id INTEGER,
                preferred_coal_mm REAL,
                preferred_cbto_mm REAL,
                preferred_jump_mm REAL,
                jam_cbto_mm REAL,
                standard_oal_mm REAL,
                evidence_level TEXT,
                source TEXT,
                notes TEXT,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                FOREIGN KEY (bullet_id) REFERENCES bullets(id) ON DELETE CASCADE,
                FOREIGN KEY (component_lot_id) REFERENCES component_lots(id) ON DELETE SET NULL
            )
        """
        )
        self._ensure_column("seating_depth_profiles", "barrel_id", "barrel_id TEXT")
        self._ensure_column("seating_depth_profiles", "barrel_name", "barrel_name TEXT")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_seating_depth_profiles_lookup ON seating_depth_profiles(rifle_id, bullet_id, component_lot_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_seating_depth_profiles_barrel_lookup ON seating_depth_profiles(rifle_id, barrel_id, bullet_id, component_lot_id)"
        )
        self._ensure_column("component_lots", "supplier", "supplier TEXT")
        self._ensure_column("component_lots", "unit_cost", "unit_cost REAL")
        self._ensure_column(
            "component_lots", "storage_location", "storage_location TEXT"
        )
        self._ensure_column("component_lots", "source", "source TEXT")
        self._ensure_column("component_lots", "external_ref", "external_ref TEXT")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_component_lots_component ON component_lots(component_type, component_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_component_lots_number ON component_lots(lot_number)"
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_measurement_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_lot_id INTEGER NOT NULL,
                measured_by TEXT,
                measured_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sample_size INTEGER,
                measured_all INTEGER DEFAULT 0,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (component_lot_id) REFERENCES component_lots(id) ON DELETE CASCADE
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_measurement_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                item_index INTEGER,
                weight_grains REAL,
                length_mm REAL,
                diameter_mm REAL,
                thickness_mm REAL,
                base_to_ogive_mm REAL,
                case_weight_gr REAL,
                case_capacity_gr_h2o REAL,
                passed_qc INTEGER,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES component_measurement_sessions(id) ON DELETE CASCADE
            )
        """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_component_measurement_values_session ON component_measurement_values(session_id)"
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_lot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_lot_id INTEGER NOT NULL UNIQUE,
                sample_count INTEGER DEFAULT 0,
                weight_avg_grains REAL,
                weight_min_grains REAL,
                weight_max_grains REAL,
                weight_stddev_grains REAL,
                length_avg_mm REAL,
                length_min_mm REAL,
                length_max_mm REAL,
                length_stddev_mm REAL,
                diameter_avg_mm REAL,
                diameter_min_mm REAL,
                diameter_max_mm REAL,
                diameter_stddev_mm REAL,
                thickness_avg_mm REAL,
                thickness_min_mm REAL,
                thickness_max_mm REAL,
                thickness_stddev_mm REAL,
                base_to_ogive_avg_mm REAL,
                base_to_ogive_min_mm REAL,
                base_to_ogive_max_mm REAL,
                base_to_ogive_stddev_mm REAL,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (component_lot_id) REFERENCES component_lots(id) ON DELETE CASCADE
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_lot_learning_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_lot_id INTEGER NOT NULL UNIQUE,
                component_type TEXT NOT NULL,
                component_id INTEGER NOT NULL,
                lot_number TEXT NOT NULL,
                status TEXT DEFAULT 'insufficient_data',
                confidence_score REAL DEFAULT 0,
                data_points INTEGER DEFAULT 0,
                batch_samples INTEGER DEFAULT 0,
                chrono_samples INTEGER DEFAULT 0,
                temperature_samples INTEGER DEFAULT 0,
                avg_velocity_fps REAL,
                velocity_offset_fps REAL,
                temp_sensitivity_fps_per_c REAL,
                typical_es_fps REAL,
                best_recorded_moa REAL,
                pressure_watch_count INTEGER DEFAULT 0,
                drift_flag TEXT,
                notes TEXT,
                profile_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (component_lot_id) REFERENCES component_lots(id) ON DELETE CASCADE
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bullet_lot_learning_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bullet_lot_id INTEGER NOT NULL UNIQUE,
                bullet_id INTEGER NOT NULL,
                lot_number TEXT NOT NULL,
                status TEXT DEFAULT 'insufficient_data',
                confidence_score REAL DEFAULT 0,
                data_points INTEGER DEFAULT 0,
                qc_samples INTEGER DEFAULT 0,
                batch_samples INTEGER DEFAULT 0,
                avg_weight_grains REAL,
                weight_std_dev REAL,
                avg_bto_inches REAL,
                bto_std_dev REAL,
                qc_pass_rate_percent REAL,
                typical_group_moa REAL,
                best_recorded_moa REAL,
                drift_flag TEXT,
                notes TEXT,
                profile_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bullet_lot_id) REFERENCES bullet_lots(id) ON DELETE CASCADE
            )
        """
        )

        # QC Batches
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qc_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_charge REAL,
                charge_tolerance REAL,
                target_coal REAL,
                coal_tolerance REAL,
                batch_size INTEGER NOT NULL,
                status TEXT DEFAULT 'in_progress',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_date TEXT
            )
        """
        )

        # Inventory lots (QC design schema)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_type TEXT NOT NULL,
                component_id INTEGER,
                lot_number TEXT,
                quantity_initial INTEGER DEFAULT 0,
                quantity_remaining INTEGER DEFAULT 0,
                purchase_date TEXT,
                supplier TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Migrate older inventory_lots schema before creating indexes.
        self._ensure_column("inventory_lots", "component_type", "component_type TEXT")
        self._ensure_column("inventory_lots", "component_id", "component_id INTEGER")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_inventory_lots_component ON inventory_lots(component_type, component_id)"
        )

        # Measurement sessions (QC sampling)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS measurement_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                measured_by TEXT,
                datetime TEXT DEFAULT CURRENT_TIMESTAMP,
                sample_size INTEGER,
                measured_all INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (lot_id) REFERENCES inventory_lots (id) ON DELETE CASCADE
            )
            """
        )

        # Measurement values (per item)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS measurement_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                item_index INTEGER,
                weight_grains REAL,
                length_mm REAL,
                neck_thickness_mm REAL,
                case_weight_gr REAL,
                passed_qc INTEGER,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES measurement_sessions (id) ON DELETE CASCADE
            )
            """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_measurement_session ON measurement_values(session_id)"
        )

        # Brass batches (used by ballistics engine)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS brass_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                batch_name TEXT,
                lot_number TEXT,
                times_fired_avg INTEGER DEFAULT 0,
                case_capacity_h2o_gr REAL,
                neck_tension_inches REAL,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE SET NULL
            )
            """
        )

        # Prep sessions (brass prep history)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prep_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brass_batch_id INTEGER,
                method TEXT,
                anneal_date TEXT,
                trim_mm REAL,
                neck_bushing_size_inches REAL,
                neck_tension_notes TEXT,
                measured_after INTEGER DEFAULT 0,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brass_batch_id) REFERENCES brass_batches (id) ON DELETE SET NULL
            )
            """
        )

        # Component inventory entries (dashboard + cost tracking)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                manufacturer TEXT,
                lot_number TEXT,
                quantity REAL NOT NULL,
                unit TEXT,
                cost_per_unit REAL,
                location TEXT,
                purchase_date TEXT,
                expiry_date TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_inventory_items_type ON inventory_items(component_type)"
        )

        # QC Measurements
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS qc_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                patron_number INTEGER NOT NULL,
                measurement_type TEXT NOT NULL,
                value REAL NOT NULL,
                target_value REAL,
                delta REAL,
                is_outlier BOOLEAN DEFAULT 0,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES qc_batches (id)
            )
        """
        )

        # Skyte-økter
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS shooting_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                project_name TEXT,
                project_path TEXT,
                load_session_id INTEGER,
                rifle_id INTEGER,
                ammo_profile_id INTEGER,
                distance_meters REAL,
                rounds_fired INTEGER,
                best_group_mm REAL,
                avg_group_mm REAL,
                temperature REAL,
                humidity REAL,
                wind_speed REAL,
                notes TEXT,
                FOREIGN KEY (load_session_id) REFERENCES load_development_sessions(id) ON DELETE SET NULL,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id)
            )
        """
        )

        # Settedybde-tester (Harmonic Wizard)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS seating_depth_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                rifle_id INTEGER,
                barrel_length REAL,
                barrel_contour TEXT,
                muzzle_device TEXT,
                muzzle_device_weight REAL,
                bullet_id INTEGER,
                powder_id INTEGER,
                powder_charge REAL,
                primer_id INTEGER,
                case_id INTEGER,
                start_coal REAL NOT NULL,
                end_coal REAL NOT NULL,
                coal_step REAL NOT NULL,
                rounds_per_coal INTEGER DEFAULT 3,
                distance_meters REAL,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (bullet_id) REFERENCES bullets (id),
                FOREIGN KEY (powder_id) REFERENCES powder (id),
                FOREIGN KEY (primer_id) REFERENCES primers (id),
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """
        )

        # Settedybde-resultater
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS seating_depth_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                coal REAL NOT NULL,
                group_size_mm REAL,
                velocity_avg REAL,
                velocity_es REAL,
                velocity_sd REAL,
                poi_horizontal REAL,
                poi_vertical REAL,
                notes TEXT,
                FOREIGN KEY (test_id) REFERENCES seating_depth_tests (id)
            )
        """
        )

        # GRT (Gordon Reloading Tool) integrasjon
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS grt_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ammo_profile_id INTEGER NOT NULL UNIQUE,
                predicted_velocity REAL,
                max_pressure_psi REAL,
                max_pressure_bar REAL,
                case_fill_percent REAL,
                predicted_accuracy_potential TEXT,
                burn_rate_position INTEGER,
                optimal_coal REAL,
                grt_data TEXT,
                import_date TEXT,
                notes TEXT,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id)
            )
        """
        )

        # Trykkindikasjoner (Pressure Signs)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pressure_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooting_session_id INTEGER,
                ladder_test_id INTEGER,
                ammo_profile_id INTEGER,
                charge_weight REAL,
                flat_primer INTEGER DEFAULT 0,
                primer_crater INTEGER DEFAULT 0,
                ejector_mark INTEGER DEFAULT 0,
                extractor_mark INTEGER DEFAULT 0,
                heavy_bolt_lift INTEGER DEFAULT 0,
                case_head_expansion REAL,
                velocity_spike INTEGER DEFAULT 0,
                pressure_score INTEGER,
                severity_level TEXT,
                notes TEXT,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shooting_session_id) REFERENCES shooting_sessions (id),
                FOREIGN KEY (ladder_test_id) REFERENCES ladder_tests (id),
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id)
            )
        """
        )
        self._ensure_column(
            "pressure_signs",
            "primer_image_path",
            "primer_image_path TEXT",
        )
        self._ensure_column(
            "pressure_signs",
            "primer_image_quality",
            "primer_image_quality TEXT",
        )
        self._ensure_column(
            "pressure_signs",
            "primer_image_observation",
            "primer_image_observation TEXT",
        )
        self._ensure_column(
            "pressure_signs",
            "primer_image_confidence",
            "primer_image_confidence TEXT",
        )
        self._ensure_column(
            "pressure_signs",
            "workflow_id",
            "workflow_id INTEGER",
        )
        self._ensure_column(
            "pressure_signs",
            "load_session_id",
            "load_session_id INTEGER",
        )
        self._ensure_column(
            "pressure_signs",
            "session_name",
            "session_name TEXT",
        )
        self._ensure_column(
            "pressure_signs",
            "batch_id",
            "batch_id INTEGER",
        )
        self._ensure_column(
            "pressure_signs",
            "batch_session_id",
            "batch_session_id INTEGER",
        )
        self._ensure_column(
            "pressure_signs",
            "rifle_id",
            "rifle_id INTEGER",
        )
        self._ensure_column(
            "pressure_signs",
            "barrel_id",
            "barrel_id TEXT",
        )
        self._ensure_column(
            "pressure_signs",
            "barrel_name",
            "barrel_name TEXT",
        )

        # Environmental Data (Manuell værdata)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS environmental_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                location_name TEXT,
                latitude REAL,
                longitude REAL,
                elevation_m REAL,
                temperature_c REAL,
                pressure_hpa REAL,
                humidity_percent INTEGER,
                wind_speed_ms REAL,
                wind_direction_deg INTEGER,
                density_altitude_ft REAL,
                instruments TEXT,
                notes TEXT,
                data_source TEXT DEFAULT 'MANUAL',
                shooting_session_id INTEGER,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shooting_session_id) REFERENCES shooting_sessions (id)
            )
        """
        )

        # Engine calibrations (mapping predicted -> measured)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS engine_calibrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine_name TEXT,
                ammo_profile_id INTEGER,
                slope REAL,
                intercept REAL,
                sample_count INTEGER,
                mse REAL,
                notes TEXT,
                accepted BOOLEAN DEFAULT 0,
                accepted_date TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id)
            )
            """
        )
        self._ensure_column("engine_calibrations", "engine_name", "engine_name TEXT")
        self._ensure_column(
            "engine_calibrations", "ammo_profile_id", "ammo_profile_id INTEGER"
        )
        self._ensure_column(
            "engine_calibrations", "accepted", "accepted BOOLEAN DEFAULT 0"
        )
        self._ensure_column(
            "engine_calibrations", "accepted_date", "accepted_date TEXT"
        )
        self._ensure_column("engine_calibrations", "created_date", "created_date TEXT")

        # Engine benchmark runs (predicted vs measured summary)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS engine_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine_name TEXT,
                sample_count INTEGER,
                mae REAL,
                rmse REAL,
                bias REAL,
                r2 REAL,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._ensure_column("engine_benchmarks", "engine_name", "engine_name TEXT")
        self._ensure_column("engine_benchmarks", "sample_count", "sample_count INTEGER")
        self._ensure_column("engine_benchmarks", "mae", "mae REAL")
        self._ensure_column("engine_benchmarks", "rmse", "rmse REAL")
        self._ensure_column("engine_benchmarks", "bias", "bias REAL")
        self._ensure_column("engine_benchmarks", "r2", "r2 REAL")
        self._ensure_column("engine_benchmarks", "notes", "notes TEXT")
        self._ensure_column("engine_benchmarks", "created_date", "created_date TEXT")

        # AI assistant settings (persisted configuration)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enabled BOOLEAN DEFAULT 0,
                model TEXT,
                api_key TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Plot snapshots (store summarized or full series for later analysis)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plot_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_type TEXT,
                metadata TEXT,
                series_json TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Optimizer suggestions (record suggested next charges and basis)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS optimizer_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggested_charge REAL,
                basis_text TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Cold Bore Shots (Første skudd fra kald rifle)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cold_bore_shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                ammo_profile_id INTEGER NOT NULL,
                distance_m REAL NOT NULL,
                temperature_c REAL,
                time_since_last_shot_hrs INTEGER,
                poi_horizontal_cm REAL NOT NULL,
                poi_vertical_cm REAL NOT NULL,
                notes TEXT,
                date TEXT NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id)
            )
        """
        )

        # Barrel Log (Løpstilstand og skudd-telling)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS barrel_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
                rounds_fired INTEGER NOT NULL,
                group_size_moa REAL,
                event_type TEXT NOT NULL,
                notes TEXT,
                date TEXT NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id)
            )
        """
        )

        # Rifle Accuracy Tests - Systematisk testing per rifle over tid
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rifle_accuracy_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,

                -- Test Info
                test_date TEXT NOT NULL,
                round_count_at_test INTEGER NOT NULL,  -- Skudd ved test (for tracking utvikling)
                test_type TEXT,  -- 'baseline', '500_round_check', 'load_development', 'verification', 'cold_bore', 'group_test', 'ladder_test'
                distance_meters REAL NOT NULL,
                groups_fired INTEGER NOT NULL,
                shots_per_group INTEGER NOT NULL,

                -- Group Results
                group_sizes_mm TEXT,  -- JSON array av alle gruppestørrelser
                average_group_size_mm REAL,
                best_group_mm REAL,
                worst_group_mm REAL,
                average_moa REAL,
                best_moa REAL,
                worst_moa REAL,

                -- Environmental Conditions
                temperature_c REAL,
                wind_condition TEXT,  -- 'none', 'light', 'moderate', 'strong'
                conditions TEXT,  -- Fritekst beskrivelse

                -- Load Data (snapshot av ladningen brukt i testen)
                case_id INTEGER,
                case_times_fired INTEGER,
                case_length_mm REAL,
                powder_id INTEGER,
                charge_weight_grains REAL,
                bullet_id INTEGER,
                coal_mm REAL,
                cbto_mm REAL,
                seating_depth_jump_mm REAL,
                primer_id INTEGER,

                -- Velocity Data
                velocities_fps TEXT,  -- JSON array av alle hastigheter
                average_velocity_fps REAL,
                extreme_spread_fps REAL,  -- ES
                standard_deviation_fps REAL,  -- SD
                min_velocity_fps REAL,
                max_velocity_fps REAL,

                -- Photos/Documentation
                target_photo_path TEXT,  -- Path til bilde av målskive
                setup_photo_path TEXT,   -- Path til bilde av setup
                additional_photos TEXT,  -- JSON array av ekstra bilder

                -- Analysis
                accuracy_rating TEXT,  -- 'excellent', 'good', 'average', 'poor'
                compared_to_baseline_percent REAL,  -- % endring fra baseline
                notes TEXT,

                -- Metadata
                test_completed BOOLEAN DEFAULT 0,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                FOREIGN KEY (case_id) REFERENCES cases(id),
                FOREIGN KEY (powder_id) REFERENCES powder(id),
                FOREIGN KEY (bullet_id) REFERENCES bullets(id),
                FOREIGN KEY (primer_id) REFERENCES primers(id)
            )
        """
        )

        # Rifle Accuracy Test Individual Shots - Detaljerte skudddata
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rifle_accuracy_test_shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                shot_number INTEGER NOT NULL,  -- Skudd nr (1, 2, 3...)
                group_number INTEGER NOT NULL,  -- Hvilken gruppe (1, 2, 3...)

                -- Shot Data
                velocity_fps REAL,
                poi_x_mm REAL,  -- Point of Impact X (fra senter)
                poi_y_mm REAL,  -- Point of Impact Y (fra senter)
                distance_from_center_mm REAL,

                -- Conditions per shot
                temperature_c REAL,
                wind_value INTEGER,  -- 0-10 scale

                notes TEXT,

                FOREIGN KEY (test_id) REFERENCES rifle_accuracy_tests(id) ON DELETE CASCADE
            )
        """
        )

        # Load Data - Manufacturer published load data (Vihtavuori, Hodgdon, Lapua, Hornady, etc)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS load_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                cartridge TEXT NOT NULL,
                bullet_id INTEGER,
                bullet_weight_grains REAL NOT NULL,
                bullet_name TEXT NOT NULL,
                powder_id INTEGER,
                powder_name TEXT NOT NULL,
                min_charge_grains REAL NOT NULL,
                max_charge_grains REAL NOT NULL,
                min_velocity_fps INTEGER,
                max_velocity_fps INTEGER,
                min_pressure_psi INTEGER,
                max_pressure_psi INTEGER,
                coal_inches REAL,
                case_capacity_grains REAL,
                barrel_length_inches REAL,
                test_barrel_twist TEXT,
                primer_type TEXT,
                notes TEXT,
                warning_text TEXT,
                data_source_url TEXT,
                import_date TEXT DEFAULT CURRENT_TIMESTAMP,
                verified INTEGER DEFAULT 0,
                FOREIGN KEY (bullet_id) REFERENCES bullets (id),
                FOREIGN KEY (powder_id) REFERENCES powder (id)
            )
        """
        )
        self._ensure_column("shooting_sessions", "project_name", "project_name TEXT")
        self._ensure_column("shooting_sessions", "project_path", "project_path TEXT")
        self._ensure_column(
            "shooting_sessions", "load_session_id", "load_session_id INTEGER"
        )
        self._ensure_column("loading_sessions", "project_name", "project_name TEXT")
        self._ensure_column("loading_sessions", "project_path", "project_path TEXT")
        self._ensure_column(
            "loading_sessions", "load_session_id", "load_session_id INTEGER"
        )
        self._ensure_column(
            "ladder_tests", "load_session_id", "load_session_id INTEGER"
        )
        self._ensure_column(
            "test_results", "load_session_id", "load_session_id INTEGER"
        )
        self._ensure_column(
            "chronograph_imports", "load_session_id", "load_session_id INTEGER"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_shooting_sessions_load_session ON shooting_sessions(load_session_id)"
        )
        self._ensure_column("load_development_workflows", "barrel_id", "barrel_id TEXT")
        self._ensure_column(
            "load_development_workflows", "barrel_name", "barrel_name TEXT"
        )
        self._ensure_column(
            "load_development_workflows", "usage_profile", "usage_profile TEXT"
        )

        # Batch Projects - user-facing load development workspace
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS batch_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_number TEXT NOT NULL UNIQUE,
                batch_name TEXT NOT NULL,
                rifle_id INTEGER NOT NULL,
                barrel_id TEXT,
                barrel_name TEXT,
                barrel_configuration_id TEXT,
                barrel_configuration_name TEXT,
                load_session_id INTEGER,
                ammo_profile_id INTEGER,
                load_recipe_id INTEGER,
                brass_batch_id INTEGER,
                bullet_id INTEGER,
                powder_id INTEGER,
                primer_id INTEGER,
                case_id INTEGER,
                source_workflow TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                usage_profile_key TEXT,
                subsonic_mode INTEGER DEFAULT 0,
                target_distance_m INTEGER,
                target_group_mm REAL,
                target_es_fps REAL,
                charge_weight_grains REAL,
                coal_mm REAL,
                cbto_mm REAL,
                neck_tension_inches REAL,
                barrel_configuration_snapshot_json TEXT,
                component_snapshot_json TEXT,
                analysis_json TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
                finalized_date TEXT,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                FOREIGN KEY (load_session_id) REFERENCES load_development_sessions(id) ON DELETE SET NULL,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id) ON DELETE SET NULL,
                FOREIGN KEY (load_recipe_id) REFERENCES load_recipe(id) ON DELETE SET NULL
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS batch_project_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                note_type TEXT DEFAULT 'note',
                title TEXT,
                note_text TEXT NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batch_projects(id) ON DELETE CASCADE
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS batch_project_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                attachment_type TEXT NOT NULL DEFAULT 'photo',
                file_path TEXT NOT NULL,
                caption TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batch_projects(id) ON DELETE CASCADE
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS batch_project_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                load_session_id INTEGER,
                rifle_id INTEGER,
                barrel_id TEXT,
                barrel_name TEXT,
                barrel_configuration_id TEXT,
                barrel_configuration_name TEXT,
                session_name TEXT,
                session_date TEXT NOT NULL,
                session_type TEXT NOT NULL DEFAULT 'range',
                distance_m INTEGER,
                temperature_c REAL,
                wind_speed_mps REAL,
                humidity_percent REAL,
                suppressor_used INTEGER,
                muzzle_device_type TEXT,
                shot_count INTEGER,
                group_size_mm REAL,
                group_size_moa REAL,
                function_status TEXT,
                tester_verdict TEXT,
                chronograph_import_id INTEGER,
                target_photo_path TEXT,
                setup_photo_path TEXT,
                additional_photos_json TEXT,
                notes TEXT,
                primer_observation_json TEXT,
                chronograph_summary_json TEXT,
                analysis_json TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batch_projects(id) ON DELETE CASCADE,
                FOREIGN KEY (load_session_id) REFERENCES load_development_sessions(id) ON DELETE SET NULL
            )
        """
        )
        self._ensure_column(
            "batch_projects", "load_session_id", "load_session_id INTEGER"
        )
        self._ensure_column(
            "batch_project_sessions", "load_session_id", "load_session_id INTEGER"
        )
        self._ensure_column("batch_projects", "barrel_id", "barrel_id TEXT")
        self._ensure_column("batch_projects", "barrel_name", "barrel_name TEXT")
        self._ensure_column(
            "batch_projects", "barrel_configuration_id", "barrel_configuration_id TEXT"
        )
        self._ensure_column(
            "batch_projects",
            "barrel_configuration_name",
            "barrel_configuration_name TEXT",
        )
        self._ensure_column(
            "batch_projects",
            "barrel_configuration_snapshot_json",
            "barrel_configuration_snapshot_json TEXT",
        )
        self._ensure_column(
            "batch_projects", "usage_profile_key", "usage_profile_key TEXT"
        )
        self._ensure_column(
            "batch_projects", "subsonic_mode", "subsonic_mode INTEGER DEFAULT 0"
        )
        self._ensure_column("batch_project_sessions", "rifle_id", "rifle_id INTEGER")
        self._ensure_column("batch_project_sessions", "barrel_id", "barrel_id TEXT")
        self._ensure_column("batch_project_sessions", "barrel_name", "barrel_name TEXT")
        self._ensure_column(
            "batch_project_sessions",
            "barrel_configuration_id",
            "barrel_configuration_id TEXT",
        )
        self._ensure_column(
            "batch_project_sessions",
            "barrel_configuration_name",
            "barrel_configuration_name TEXT",
        )
        self._ensure_column(
            "batch_project_sessions",
            "suppressor_used",
            "suppressor_used INTEGER",
        )
        self._ensure_column(
            "batch_project_sessions",
            "muzzle_device_type",
            "muzzle_device_type TEXT",
        )
        self._ensure_column(
            "batch_project_sessions",
            "function_status",
            "function_status TEXT",
        )
        self._ensure_column(
            "batch_project_sessions",
            "tester_verdict",
            "tester_verdict TEXT",
        )
        self._ensure_column(
            "batch_project_sessions",
            "primer_observation_json",
            "primer_observation_json TEXT",
        )
        self._ensure_column(
            "batch_project_sessions",
            "chronograph_summary_json",
            "chronograph_summary_json TEXT",
        )

        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_projects_rifle ON batch_projects(rifle_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_projects_status ON batch_projects(status)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_projects_load_session ON batch_projects(load_session_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_project_notes_batch ON batch_project_notes(batch_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_project_attachments_batch ON batch_project_attachments(batch_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_project_sessions_batch ON batch_project_sessions(batch_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_batch_project_sessions_load_session ON batch_project_sessions(load_session_id)"
        )

        # Pressure history log (predicted pressures from simulations and imports)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pressure_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                rifle_id INTEGER,
                ammo_profile_id INTEGER,
                charge_weight REAL,
                coal_mm REAL,
                cbto_mm REAL,
                predicted_pressure_psi REAL,
                saami_max_psi REAL,
                note TEXT
            )
            """
        )

        # UI settings - small key/value store for lightweight persistent UI options
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Engine calibration records (slope/intercept for predicted -> measured mapping)
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS engine_calibrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                slope REAL,
                intercept REAL,
                sample_count INTEGER,
                mse REAL,
                notes TEXT
            )
            """
        )

        # ========================================================================
        # ADVANCED BATCH MANAGEMENT SYSTEM - Professional Load Development
        # ========================================================================

        # Bullet Lots - Track bullet purchases with lot numbers and QC data
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bullet_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bullet_id INTEGER NOT NULL,

                -- Purchase Info
                lot_number TEXT NOT NULL,
                purchase_date TEXT NOT NULL,
                quantity_purchased INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                cost_total REAL,
                cost_per_unit REAL,
                supplier TEXT,

                -- QC Measurements (from sample)
                qc_performed BOOLEAN DEFAULT 0,
                qc_date TEXT,
                qc_sample_size INTEGER,  -- How many bullets measured

                -- Weight QC
                weight_avg_grains REAL,
                weight_min_grains REAL,
                weight_max_grains REAL,
                weight_std_dev REAL,
                weight_variance_grains REAL,  -- max - min

                -- Length QC (Base to Ogive)
                length_bto_avg_inches REAL,
                length_bto_min_inches REAL,
                length_bto_max_inches REAL,
                length_bto_std_dev REAL,
                length_bto_variance_inches REAL,

                -- Overall Length
                length_oal_avg_inches REAL,
                length_oal_std_dev REAL,

                -- Quality Rating
                quality_rating TEXT,  -- 'excellent', 'good', 'average', 'poor'
                qc_pass_rate_percent REAL,  -- % of bullets within tolerance
                rejected_count INTEGER DEFAULT 0,

                -- Storage
                storage_location TEXT,
                storage_conditions TEXT,  -- 'climate_controlled', 'dry_cabinet', 'normal'

                -- Status
                is_active BOOLEAN DEFAULT 1,
                retired_date TEXT,

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (bullet_id) REFERENCES bullets(id) ON DELETE CASCADE,
                UNIQUE(bullet_id, lot_number)
            )
        """
        )

        # Bullet QC Measurements - Individual bullet measurements from QC sample
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bullet_qc_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                measurement_date TEXT NOT NULL,

                -- Individual Bullet Data
                bullet_number INTEGER NOT NULL,  -- 1, 2, 3... in sample
                weight_grains REAL NOT NULL,
                length_bto_inches REAL,
                length_oal_inches REAL,

                -- Visual Inspection
                visual_defects TEXT,  -- 'none', 'minor_blemish', 'tip_damage', 'jacket_flaw'
                meplat_condition TEXT,  -- 'perfect', 'good', 'irregular'
                base_condition TEXT,  -- 'perfect', 'good', 'minor_defect'

                -- Pass/Fail
                passed_qc BOOLEAN DEFAULT 1,
                rejection_reason TEXT,

                notes TEXT,

                FOREIGN KEY (lot_id) REFERENCES bullet_lots(id) ON DELETE CASCADE
            )
        """
        )

        # Brass Batches - Subdivide large brass purchases into manageable batches
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS brass_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,  -- Link to cases (brass type)

                -- Batch Info
                batch_name TEXT NOT NULL,  -- 'Lapua-308-Batch-A', user-friendly name
                batch_number TEXT,  -- System generated: 'BB-2024-001'
                parent_lot_number TEXT,  -- Original purchase lot

                -- Quantity Tracking
                cases_in_batch INTEGER NOT NULL,
                cases_active INTEGER NOT NULL,  -- Not retired
                cases_retired INTEGER DEFAULT 0,

                -- Firing History
                times_fired_min INTEGER DEFAULT 0,
                times_fired_max INTEGER DEFAULT 0,
                times_fired_avg REAL DEFAULT 0,

                -- Annealing History
                last_annealed_date TEXT,
                times_annealed INTEGER DEFAULT 0,
                annealing_due BOOLEAN DEFAULT 0,

                -- Preparation Status
                prep_status TEXT DEFAULT 'virgin',  -- 'virgin', 'prepped', 'fire_formed', 'sized', 'ready'
                weight_sorted BOOLEAN DEFAULT 0,
                length_sorted BOOLEAN DEFAULT 0,
                neck_turned BOOLEAN DEFAULT 0,
                flash_hole_uniformed BOOLEAN DEFAULT 0,
                primer_pocket_uniformed BOOLEAN DEFAULT 0,

                -- Measurements
                avg_case_weight_gr REAL,
                avg_case_length_mm REAL,
                avg_neck_thickness_mm REAL,
                case_capacity_h2o_gr REAL,

                -- Condition
                condition_rating TEXT,  -- 'excellent', 'good', 'fair', 'worn'
                retire_at_firings INTEGER,  -- Planned retirement point

                -- Usage
                dedicated_rifle_id INTEGER,  -- If fire-formed to specific rifle
                last_used_date TEXT,

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (dedicated_rifle_id) REFERENCES rifles(id)
            )
        """
        )

        # Brass Lifecycle Log - Track each brass batch through loading cycles
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS brass_lifecycle_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                event_type TEXT NOT NULL,  -- 'purchased', 'prepped', 'fired', 'sized', 'annealed', 'trimmed', 'retired'

                -- Event Details
                cases_affected INTEGER NOT NULL,  -- How many cases
                times_fired_before INTEGER,
                times_fired_after INTEGER,

                -- Related Records
                rifle_id INTEGER,  -- If fired
                loaded_batch_id INTEGER,  -- If loaded into ammo

                -- Process Details
                sized BOOLEAN DEFAULT 0,
                sizing_die_used TEXT,
                shoulder_bump_inches REAL,
                neck_sized_diameter_inches REAL,

                trimmed BOOLEAN DEFAULT 0,
                trim_length_mm REAL,

                annealed BOOLEAN DEFAULT 0,
                annealing_method TEXT,  -- 'AMP', 'Annie', 'flame'
                annealing_program TEXT,  -- AMP program number or settings

                -- Condition Assessment
                condition_after TEXT,  -- 'excellent', 'good', 'fair', 'poor'
                primer_pocket_condition TEXT,  -- 'tight', 'normal', 'loose'
                neck_condition TEXT,  -- 'good', 'minor_splits', 'cracked'
                case_head_condition TEXT,  -- 'good', 'expansion_signs', 'separation_risk'

                -- Retirements
                cases_retired INTEGER DEFAULT 0,
                retirement_reason TEXT,  -- 'primer_pocket_loose', 'neck_split', 'case_head_separation', 'excessive_length'

                notes TEXT,

                FOREIGN KEY (batch_id) REFERENCES brass_batches(id) ON DELETE CASCADE,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id),
                FOREIGN KEY (loaded_batch_id) REFERENCES loaded_ammo_batches(id)
            )
        """
        )

        # Die Settings - Document die setup per rifle + brass combination
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS die_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Combination
                rifle_id INTEGER NOT NULL,
                case_id INTEGER NOT NULL,  -- Brass type
                brass_batch_id INTEGER,  -- Specific batch (optional)

                -- Die Information
                die_type TEXT NOT NULL,  -- 'full_length', 'neck_sizing', 'body', 'seating', 'crimp'
                die_manufacturer TEXT NOT NULL,
                die_model TEXT NOT NULL,
                die_serial_number TEXT,

                -- Setup Details
                setup_date TEXT NOT NULL,
                press_type TEXT,
                shell_holder TEXT,

                -- SIZING DIE SETTINGS
                sizing_die_depth TEXT,  -- 'shell_holder_contact_+_1/4_turn', measurement
                bushing_size_inches REAL,  -- For bushing dies
                expander_used BOOLEAN DEFAULT 0,
                expander_size_inches REAL,
                decapping_pin_removed BOOLEAN DEFAULT 0,

                -- Shoulder Bump
                shoulder_bump_target_inches REAL NOT NULL,  -- e.g., 0.002"
                shoulder_bump_actual_inches REAL,  -- Measured
                shoulder_datum_fired_inches REAL,  -- Before sizing
                shoulder_datum_sized_inches REAL,  -- After sizing

                -- Neck Tension
                neck_tension_target_inches REAL,  -- e.g., 0.002" interference
                neck_od_sized_inches REAL,
                neck_tension_actual_inches REAL,  -- Calculated

                -- SEATING DIE SETTINGS
                seating_die_depth TEXT,
                seating_stem_type TEXT,  -- 'VLD', 'standard', 'competition'
                micrometer_reading TEXT,  -- Micrometer number
                seating_depth_cbto_target_inches REAL,
                seating_depth_cbto_actual_inches REAL,

                -- Verification Measurements
                case_runout_tir_inches REAL,  -- Total Indicated Runout after sizing
                loaded_runout_tir_inches REAL,  -- TIR after seating bullet
                headspace_go_gauge BOOLEAN,
                headspace_no_go_gauge BOOLEAN,

                -- Lubrication
                case_lube_used TEXT,  -- 'Imperial Sizing Wax', 'Hornady One Shot', 'Imperial Dry Neck'
                neck_lube_separate BOOLEAN DEFAULT 0,
                neck_lube_type TEXT,

                -- Performance Notes
                consistency_rating TEXT,  -- 'excellent', 'good', 'needs_adjustment'
                adjustment_notes TEXT,
                spring_back_inches REAL,  -- How much brass springs back after sizing

                -- Active Status
                is_current BOOLEAN DEFAULT 1,
                superseded_by_id INTEGER,  -- If settings were updated
                superseded_date TEXT,

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used_date TEXT,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
                FOREIGN KEY (case_id) REFERENCES cases(id),
                FOREIGN KEY (brass_batch_id) REFERENCES brass_batches(id),
                FOREIGN KEY (superseded_by_id) REFERENCES die_settings(id)
            )
        """
        )

        # Annealing Log - Professional annealing tracking
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS annealing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- What was annealed
                brass_batch_id INTEGER NOT NULL,
                cases_annealed INTEGER NOT NULL,
                annealing_date TEXT NOT NULL,

                -- Annealing Equipment
                method TEXT NOT NULL,  -- 'AMP', 'Annie_induction', 'flame_bench_source', 'flame_manual'
                equipment_model TEXT,

                -- AMP Annealer Settings
                amp_program_number TEXT,  -- e.g., '#0457'
                amp_aztec_reading INTEGER,  -- Aztec mode reading
                amp_aztec_spec_min INTEGER,  -- Expected range
                amp_aztec_spec_max INTEGER,

                -- Induction Annealer Settings (Annie, etc)
                induction_power_percent REAL,
                induction_time_seconds REAL,

                -- Flame Annealer Settings
                flame_propane BOOLEAN,
                flame_time_seconds REAL,
                flame_rotation_rpm REAL,

                -- Temperature Verification
                templaq_used BOOLEAN DEFAULT 0,
                templaq_temperature_f INTEGER,  -- 450F, 750F, etc
                templaq_result TEXT,  -- 'melted' (too hot), 'not_melted' (good), 'not_used'

                -- Quality Control
                qc_sample_size INTEGER,  -- How many cases checked
                qc_pass_count INTEGER,
                qc_fail_count INTEGER,
                qc_pass_rate_percent REAL,

                -- Results
                uniformity_rating TEXT,  -- 'excellent', 'good', 'fair', 'poor'
                color_consistency TEXT,  -- 'uniform', 'slight_variation', 'inconsistent'
                neck_feel_test TEXT,  -- 'consistent', 'variable' (when seating bullets after)

                -- Performance Impact
                es_sd_before TEXT,  -- ES/SD before annealing
                es_sd_after TEXT,  -- ES/SD after annealing (if tested)
                accuracy_impact TEXT,  -- 'improved', 'no_change', 'degraded'

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (brass_batch_id) REFERENCES brass_batches(id) ON DELETE CASCADE
            )
        """
        )

        # Loaded Ammo Batches - THE CORE OF THE SYSTEM
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS loaded_ammo_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Batch Identification
                batch_number TEXT NOT NULL UNIQUE,  -- Auto-generated: 'LAB-2024-11-24-001'
                batch_name TEXT,  -- User-friendly name: 'Match Load for NM', '42.0gr H4350 Test'

                -- What rifle is this for
                rifle_id INTEGER NOT NULL,

                -- Load Date
                loaded_date TEXT NOT NULL,
                loaded_by TEXT,  -- User name/initials

                -- Components Used (with lot tracking)
                brass_batch_id INTEGER NOT NULL,
                bullet_lot_id INTEGER NOT NULL,
                powder_id INTEGER NOT NULL,
                powder_lot_number TEXT,
                primer_id INTEGER NOT NULL,
                primer_lot_number TEXT,

                -- Load Recipe
                charge_weight_grains REAL NOT NULL,
                charge_weight_tolerance_grains REAL DEFAULT 0.1,  -- ±0.1gr

                coal_mm REAL NOT NULL,
                coal_inches REAL,
                coal_tolerance_mm REAL DEFAULT 0.02,  -- ±0.02mm

                cbto_mm REAL,
                cbto_inches REAL,
                cbto_tolerance_mm REAL DEFAULT 0.01,  -- ±0.01mm (tighter!)

                bullet_jump_mm REAL,  -- Distance from lands
                bullet_jump_inches REAL,

                neck_tension_inches REAL,  -- Measured interference
                crimp_applied BOOLEAN DEFAULT 0,
                crimp_amount_inches REAL,

                -- Die Settings Used (snapshot)
                die_settings_id INTEGER,
                sizing_die TEXT,
                seating_die TEXT,

                -- Quantity
                quantity_loaded INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                quantity_fired INTEGER DEFAULT 0,

                -- Quality Control - PER ROUND
                qc_performed BOOLEAN DEFAULT 1,
                qc_sample_size INTEGER,  -- How many rounds checked (can be all)

                -- Powder Charge QC
                powder_charge_min_grains REAL,
                powder_charge_max_grains REAL,
                powder_charge_avg_grains REAL,
                powder_charge_std_dev REAL,
                powder_out_of_spec_count INTEGER DEFAULT 0,

                -- CBTO QC
                cbto_min_mm REAL,
                cbto_max_mm REAL,
                cbto_avg_mm REAL,
                cbto_std_dev_mm REAL,
                cbto_out_of_spec_count INTEGER DEFAULT 0,

                -- Runout QC
                runout_max_tir_inches REAL,
                runout_avg_tir_inches REAL,
                runout_out_of_spec_count INTEGER DEFAULT 0,  -- >0.003" TIR

                -- Overall QC
                qc_pass_count INTEGER,
                qc_fail_count INTEGER,
                qc_pass_rate_percent REAL,
                qc_rejection_reasons TEXT,  -- JSON array

                -- Predicted Performance (from AI/ML)
                predicted_velocity_fps REAL,
                predicted_es_fps REAL,
                predicted_sd_fps REAL,
                predicted_moa REAL,
                predicted_pressure_psi REAL,
                prediction_confidence REAL,  -- 0-1 confidence score

                -- Environmental Conditions (when loaded)
                loading_temperature_c REAL,
                loading_humidity_percent REAL,

                -- Storage
                storage_location TEXT,
                storage_temperature_min_c REAL,
                storage_temperature_max_c REAL,

                -- Usage Tracking
                intended_use TEXT,  -- 'competition', 'practice', 'load_development', 'hunting', 'long_range'
                test_completed BOOLEAN DEFAULT 0,
                test_date TEXT,
                accuracy_test_id INTEGER,  -- Link to rifle_accuracy_tests

                -- Actual Performance (after testing)
                actual_velocity_avg_fps REAL,
                actual_es_fps REAL,
                actual_sd_fps REAL,
                actual_moa_avg REAL,
                actual_best_moa REAL,

                -- Safety
                pressure_signs_observed BOOLEAN DEFAULT 0,
                pressure_signs_description TEXT,
                safe_to_fire BOOLEAN DEFAULT 1,

                -- Batch Status
                batch_status TEXT DEFAULT 'loaded',  -- 'loaded', 'tested', 'in_use', 'depleted', 'retired'
                retired_date TEXT,
                retirement_reason TEXT,

                -- Cost Tracking
                cost_components REAL,
                cost_per_round REAL,

                -- Time Tracking
                loading_time_minutes INTEGER,
                rounds_per_hour REAL,

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id),
                FOREIGN KEY (brass_batch_id) REFERENCES brass_batches(id),
                FOREIGN KEY (bullet_lot_id) REFERENCES bullet_lots(id),
                FOREIGN KEY (powder_id) REFERENCES powder(id),
                FOREIGN KEY (primer_id) REFERENCES primers(id),
                FOREIGN KEY (die_settings_id) REFERENCES die_settings(id),
                FOREIGN KEY (accuracy_test_id) REFERENCES rifle_accuracy_tests(id)
            )
        """
        )

        # Per-Round QC Measurements - Individual round quality control
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS per_round_qc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,  -- 1, 2, 3... 50

                -- Measurements
                powder_charge_grains REAL NOT NULL,
                coal_mm REAL,
                cbto_mm REAL,
                runout_tir_inches REAL,  -- Concentricity

                -- Visual Inspection
                primer_seated_flush BOOLEAN DEFAULT 1,
                bullet_seated_straight BOOLEAN DEFAULT 1,
                case_mouth_condition TEXT,  -- 'good', 'dented', 'flared'
                overall_appearance TEXT,  -- 'excellent', 'good', 'acceptable', 'reject'

                -- Pass/Fail
                passed_qc BOOLEAN DEFAULT 1,
                rejection_reason TEXT,

                -- Deviations from Target
                powder_delta_grains REAL,  -- Actual - Target
                cbto_delta_mm REAL,

                -- Used/Fired
                fired BOOLEAN DEFAULT 0,
                fired_date TEXT,
                velocity_fps REAL,

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (batch_id) REFERENCES loaded_ammo_batches(id) ON DELETE CASCADE
            )
        """
        )

        # Sizing Recommendations - AI-calculated sizing guidance
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sizing_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- For which combination
                rifle_id INTEGER NOT NULL,
                case_id INTEGER NOT NULL,
                brass_batch_id INTEGER,

                -- Calculation Date
                calculation_date TEXT NOT NULL,

                -- Input Data
                chamber_spec TEXT,  -- SAAMI, Match, Custom
                chamber_headspace_inches REAL,
                fired_case_length_inches REAL,
                fired_shoulder_datum_inches REAL,
                times_fired INTEGER,

                -- Shoulder Bump Recommendations
                recommended_shoulder_bump_inches REAL NOT NULL,
                shoulder_bump_min_inches REAL,
                shoulder_bump_max_inches REAL,
                shoulder_bump_reasoning TEXT,

                -- Neck Sizing Recommendations
                bullet_diameter_inches REAL,
                neck_wall_thickness_inches REAL,
                recommended_neck_bushing_inches REAL,
                recommended_neck_tension_inches REAL,
                neck_tension_min_inches REAL,
                neck_tension_max_inches REAL,
                neck_sizing_reasoning TEXT,

                -- Case Length / Trimming
                case_length_current_inches REAL,
                case_length_max_saami_inches REAL,
                case_length_trim_to_inches REAL,
                trim_recommended BOOLEAN DEFAULT 0,
                trim_reasoning TEXT,

                -- Safety Considerations
                action_type TEXT,  -- bolt, semi-auto (affects bump amount)
                safety_margin_inches REAL,  -- Extra clearance for reliability

                -- AI Confidence
                confidence_score REAL,  -- 0-1
                data_sources TEXT,  -- What data was used for calculation

                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (rifle_id) REFERENCES rifles(id),
                FOREIGN KEY (case_id) REFERENCES cases(id),
                FOREIGN KEY (brass_batch_id) REFERENCES brass_batches(id)
            )
        """
        )

        # Powder Database - Extended powder info for pressure calculations
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS powder_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                powder_id INTEGER NOT NULL UNIQUE,

                -- Burn Rate Data (for pressure modeling)
                burn_rate_position INTEGER,  -- 1-250 scale (1=fastest)
                relative_burn_rate REAL,  -- QuickLOAD Ba value

                -- Physical Properties
                density_gcc REAL,  -- g/cc
                grain_size_mm REAL,
                grain_shape TEXT,  -- 'ball', 'extruded', 'flake', 'cylinder'

                -- Temperature Sensitivity
                temp_stable BOOLEAN DEFAULT 0,
                temp_coefficient_fps_per_f REAL,  -- Velocity change per °F

                -- Pressure Characteristics
                peak_pressure_timing TEXT,  -- 'fast', 'medium', 'slow'
                loading_density_optimal_percent REAL,  -- 85-95% typical

                -- Velocity Characteristics
                velocity_potential TEXT,  -- 'low', 'medium', 'high'

                -- Suitable Cartridges
                suitable_for_cartridges TEXT,  -- JSON array
                optimal_bullet_weight_range TEXT,

                -- QuickLOAD Data (if available)
                quickload_available BOOLEAN DEFAULT 0,
                quickload_ba_value REAL,
                quickload_weighting_factor REAL,

                notes TEXT,
                data_source TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (powder_id) REFERENCES powder(id) ON DELETE CASCADE
            )
        """
        )
        self._ensure_column("powder_database", "qex_kj_per_kg", "qex_kj_per_kg REAL")
        self._ensure_column("powder_database", "k_ratio", "k_ratio REAL")
        self._ensure_column("powder_database", "a0", "a0 REAL")
        self._ensure_column("powder_database", "z1", "z1 REAL")
        self._ensure_column("powder_database", "z2", "z2 REAL")
        self._ensure_column("powder_database", "eta_cm3_per_kg", "eta_cm3_per_kg REAL")
        self._ensure_column("powder_database", "pc_kg_m3", "pc_kg_m3 REAL")
        self._ensure_column("powder_database", "pcd_kg_m3", "pcd_kg_m3 REAL")
        self._ensure_column("powder_database", "pt_c", "pt_c REAL")
        self._ensure_column("powder_database", "tcc", "tcc REAL")
        self._ensure_column("powder_database", "tch", "tch REAL")
        self._ensure_column(
            "powder_database",
            "validation_status",
            "validation_status TEXT DEFAULT 'unverified'",
        )
        self._ensure_column(
            "powder_database",
            "usable_for_simulation",
            "usable_for_simulation INTEGER DEFAULT 0",
        )
        self._ensure_column("powder_database", "source_version", "source_version TEXT")
        self._ensure_column("powder_database", "external_ref", "external_ref TEXT")
        self._ensure_column("powder_database", "raw_json", "raw_json TEXT")

        # PowderData - Utvidet kruttinformasjon for trykkberegninger
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS powder_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                manufacturer TEXT,
                type TEXT,
                burn_rate REAL,
                energy_density REAL,
                recommended_charge_min REAL,
                recommended_charge_max REAL,
                reference TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # BulletData - Utvidet kuleinformasjon for presisjonsberegninger
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bullet_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                manufacturer TEXT,
                diameter REAL,
                weight REAL,
                bc REAL,
                type TEXT,
                length REAL,
                recommended_twist REAL,
                reference TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # --- Ammo test module (structured lot/session/shot tables) ---
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ammo_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                caliber TEXT NOT NULL,
                bullet_weight_gr REAL,
                lot_number TEXT NOT NULL,
                purchase_date TEXT,
                purchase_price REAL,
                store TEXT,
                count_purchased INTEGER,
                count_remaining INTEGER,
                expiry_date TEXT,
                storage_notes TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ammo_test_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                rifle_id INTEGER,
                rifle_name TEXT,
                barrel_configuration_id TEXT,
                barrel_name TEXT,
                test_date TEXT NOT NULL,
                distance_m REAL,
                temp_c REAL,
                wind_mps REAL,
                wind_dir_deg REAL,
                barometric_pressure_hpa REAL,
                barrel_state TEXT,
                shots_in_prior_string INTEGER,
                group_size_mm REAL,
                poi_x_mm REAL,
                poi_y_mm REAL,
                image_path TEXT,
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES ammo_lots(id) ON DELETE CASCADE,
                FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE SET NULL
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ammo_test_shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                shot_number INTEGER NOT NULL,
                velocity_fps REAL,
                is_cold_bore INTEGER DEFAULT 0,
                is_calibration INTEGER DEFAULT 0,
                is_dud INTEGER DEFAULT 0,
                is_light_strike INTEGER DEFAULT 0,
                is_ftf INTEGER DEFAULT 0,
                is_fte INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES ammo_test_sessions(id) ON DELETE CASCADE
            )
            """
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ammo_lots_brand_model "
            "ON ammo_lots(brand, model, caliber)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ammo_test_sessions_lot "
            "ON ammo_test_sessions(lot_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ammo_test_shots_session "
            "ON ammo_test_shots(session_id)"
        )

        self.conn.commit()

    # CRUD operasjoner

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        try:
            if self.conn is None or self.cursor is None:
                return []
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(tr("database_query_error", lang=self.language) + f": {str(e)}")
            return []

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """Insert a row into *table* and return the new primary key, or None on failure."""
        if self.conn is None or self.cursor is None:
            logger.error("Database not connected")
            return None

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            row_id = self.cursor.lastrowid
            if row_id is None:
                logger.error("Insert into %s did not return a row id", table)
                return None
            return int(row_id)
        except Exception as e:
            logger.error(
                tr("database_insert_error", lang=self.language) + f": {str(e)}"
            )
            return None

    def _ensure_default_case_profiles(self) -> None:
        """Seed a small internal reference set of case profiles without inventing lot inventory."""
        if self.conn is None or self.cursor is None:
            return

        defaults = [
            {
                "manufacturer": "Reference",
                "name": "Baseline Brass",
                "caliber": "6.5 Creedmoor",
                "material": "brass",
                "quantity": 0,
                "times_fired": 0,
                "case_capacity_gr_h2o": 53.8,
                "trim_length_mm": 48.77,
                "notes": "Seedet referansehylse fra intern kaliberbaseline. Verifiser kapasitet mot eget lot før presis lastutvikling.",
            },
            {
                "manufacturer": "Reference",
                "name": "Baseline Brass",
                "caliber": ".308 Winchester",
                "material": "brass",
                "quantity": 0,
                "times_fired": 0,
                "case_capacity_gr_h2o": 56.3,
                "trim_length_mm": 51.18,
                "notes": "Seedet referansehylse fra intern kaliberbaseline. Verifiser kapasitet mot eget lot før presis lastutvikling.",
            },
            {
                "manufacturer": "Reference",
                "name": "Baseline Brass",
                "caliber": ".30-06 Springfield",
                "material": "brass",
                "quantity": 0,
                "times_fired": 0,
                "case_capacity_gr_h2o": 70.7,
                "trim_length_mm": 63.35,
                "notes": "Seedet referansehylse fra intern kaliberbaseline. Verifiser kapasitet mot eget lot før presis lastutvikling.",
            },
        ]

        for payload in defaults:
            existing = self.execute_query(
                "SELECT id, case_capacity_gr_h2o, trim_length_mm, notes FROM cases WHERE manufacturer = ? AND name = ? AND caliber = ? LIMIT 1",
                (payload["manufacturer"], payload["name"], payload["caliber"]),
            )
            if existing:
                update_payload = {}
                existing_row = existing[0]
                if existing_row.get("case_capacity_gr_h2o") is None:
                    update_payload["case_capacity_gr_h2o"] = payload[
                        "case_capacity_gr_h2o"
                    ]
                if existing_row.get("trim_length_mm") is None:
                    update_payload["trim_length_mm"] = payload["trim_length_mm"]
                if not existing_row.get("notes"):
                    update_payload["notes"] = payload["notes"]
                if update_payload:
                    self.update(
                        "cases", update_payload, "id = ?", (existing_row["id"],)
                    )
                continue
            self.insert("cases", payload)

    def _ensure_default_primer_profiles(self) -> None:
        """Seed a small reference set of common primer profiles without blocking manual entries."""
        if self.conn is None or self.cursor is None:
            return

        defaults = [
            {
                "manufacturer": "CCI",
                "name": "450",
                "product_line": "CCI Primers",
                "part_number": "17",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "CCI catalog",
                "type": "Small Rifle Magnum",
                "size": "small rifle",
                "match_grade": 0,
                "magnum": 1,
                "ar_variant": 0,
                "nominal_diameter_in": 0.175,
                "used_for": "Small rifle, magnum ignition, tougher hunting conditions",
                "box_count": 100,
                "primer_family": "small_rifle_magnum",
                "cup_thickness_in": 0.025,
                "cup_hardness_class": "hard",
                "pressure_tolerance_class": "high",
                "ignition_strength_class": "magnum",
                "recommended_pressure_min_psi": 50000.0,
                "recommended_pressure_max_psi": 62000.0,
                "cold_weather_suitability": "good",
                "primer_sign_interpretation": "late_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "CCI",
                "name": "BR-4",
                "product_line": "CCI Primers",
                "part_number": "19",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "CCI catalog",
                "type": "Small Rifle Benchrest",
                "size": "small rifle",
                "match_grade": 1,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.175,
                "used_for": "Small rifle benchrest / precision reloading",
                "box_count": 100,
                "primer_family": "small_rifle_benchrest",
                "cup_thickness_in": 0.025,
                "cup_hardness_class": "hard",
                "pressure_tolerance_class": "high",
                "ignition_strength_class": "standard_plus",
                "recommended_pressure_min_psi": 50000.0,
                "recommended_pressure_max_psi": 62000.0,
                "cold_weather_suitability": "good",
                "primer_sign_interpretation": "late_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "Federal",
                "name": "205",
                "product_line": "Federal Champion",
                "part_number": "100",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "Federal catalog",
                "type": "Small Rifle",
                "size": "small rifle",
                "match_grade": 0,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.1755,
                "used_for": "Small rifle reloading",
                "box_count": 100,
                "primer_family": "small_rifle",
                "cup_thickness_in": 0.022,
                "cup_hardness_class": "medium",
                "pressure_tolerance_class": "high",
                "ignition_strength_class": "standard",
                "recommended_pressure_min_psi": 50000.0,
                "recommended_pressure_max_psi": 62000.0,
                "cold_weather_suitability": "good",
                "primer_sign_interpretation": "normal",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "Federal",
                "name": "205M",
                "product_line": "Gold Medal",
                "part_number": "GM205M",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "Federal catalog",
                "type": "Small Rifle Match",
                "size": "small rifle",
                "match_grade": 1,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.1755,
                "used_for": "Small rifle match / precision reloading",
                "box_count": 100,
                "primer_family": "small_rifle_match",
                "cup_thickness_in": 0.022,
                "cup_hardness_class": "medium",
                "pressure_tolerance_class": "high",
                "ignition_strength_class": "standard",
                "recommended_pressure_min_psi": 50000.0,
                "recommended_pressure_max_psi": 62000.0,
                "cold_weather_suitability": "good",
                "primer_sign_interpretation": "normal",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "CCI",
                "name": "400",
                "product_line": "CCI Primers",
                "part_number": "13",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "CCI catalog",
                "type": "Small Rifle",
                "size": "small rifle",
                "match_grade": 0,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.175,
                "used_for": "Small rifle reloading",
                "box_count": 100,
                "primer_family": "small_rifle",
                "cup_thickness_in": 0.020,
                "cup_hardness_class": "medium",
                "pressure_tolerance_class": "moderate",
                "ignition_strength_class": "standard",
                "recommended_pressure_min_psi": 35000.0,
                "recommended_pressure_max_psi": 50000.0,
                "cold_weather_suitability": "fair",
                "primer_sign_interpretation": "early_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "Remington",
                "name": "6 1/2",
                "product_line": "Remington Primers",
                "source_kind": "reference_inferred",
                "manufacturer_source": "Remington SDS / safety materials",
                "type": "Small Rifle",
                "size": "small rifle",
                "match_grade": 0,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.175,
                "used_for": "Moderate small-rifle pressure applications",
                "box_count": 100,
                "primer_family": "small_rifle",
                "cup_thickness_in": 0.020,
                "cup_hardness_class": "soft",
                "pressure_tolerance_class": "moderate",
                "ignition_strength_class": "standard",
                "recommended_pressure_min_psi": 35000.0,
                "recommended_pressure_max_psi": 50000.0,
                "cold_weather_suitability": "fair",
                "primer_sign_interpretation": "early_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "Remington",
                "name": "7 1/2",
                "product_line": "Remington Bench Rest",
                "source_kind": "reference_inferred",
                "manufacturer_source": "Remington SDS / safety materials",
                "type": "Small Rifle Benchrest",
                "size": "small rifle",
                "match_grade": 1,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.175,
                "used_for": "Higher-pressure small-rifle / benchrest use",
                "box_count": 100,
                "primer_family": "small_rifle_benchrest",
                "cup_thickness_in": 0.025,
                "cup_hardness_class": "hard",
                "pressure_tolerance_class": "high",
                "ignition_strength_class": "standard_plus",
                "recommended_pressure_min_psi": 50000.0,
                "recommended_pressure_max_psi": 62000.0,
                "cold_weather_suitability": "good",
                "primer_sign_interpretation": "late_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
            {
                "manufacturer": "Winchester",
                "name": "SR",
                "product_line": "Winchester Components",
                "source_kind": "manufacturer_published+reference_inferred",
                "manufacturer_source": "Winchester components / SDS",
                "type": "Small Rifle",
                "size": "small rifle",
                "match_grade": 0,
                "magnum": 0,
                "ar_variant": 0,
                "nominal_diameter_in": 0.175,
                "used_for": "Small rifle reloading",
                "box_count": 100,
                "composition_class": "lead styphnate-based",
                "non_corrosive": 1,
                "temperature_claim": "all weather",
                "primer_family": "small_rifle",
                "cup_thickness_in": 0.020,
                "cup_hardness_class": "medium",
                "pressure_tolerance_class": "moderate",
                "ignition_strength_class": "standard",
                "recommended_pressure_min_psi": 35000.0,
                "recommended_pressure_max_psi": 50000.0,
                "cold_weather_suitability": "fair",
                "primer_sign_interpretation": "early_signs_possible",
                "evidence_level": "reference_seed",
                "reference_source": "Calhoon small-rifle pressure notes",
                "notes": "Seedet primerprofil for referanse og simulering.",
                "quantity": 0,
            },
        ]

        for payload in defaults:
            existing = self.execute_query(
                "SELECT id FROM primers WHERE manufacturer = ? AND name = ? LIMIT 1",
                (payload["manufacturer"], payload["name"]),
            )
            if existing:
                continue
            self.insert("primers", payload)

    def update(
        self, table: str, data: Dict[str, Any], condition: str, params: tuple = ()
    ):
        try:
            if self.conn is None or self.cursor is None:
                logger.error("Database not connected")
                return
            set_clause = ", ".join([f"{k}=?" for k in data.keys()])
            values = tuple(data.values()) + params
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            self.cursor.execute(query, values)
            self.conn.commit()
        except Exception as e:
            logger.error(
                tr("database_update_error", lang=self.language) + f": {str(e)}"
            )

    def _seed_barrel_profiles(self) -> None:
        """Seed predefined barrel profiles on first run (idempotent)."""
        try:
            from .init_barrel_profiles import initialize_barrel_profiles

            initialize_barrel_profiles(db=self)
        except Exception:
            pass

    def _seed_rifles_from_json(self) -> None:
        """Import rifle profiles from demo_weapons.json into the rifles table if it is empty."""
        try:
            if self.conn is None or self.cursor is None:
                return
            self.cursor.execute("SELECT COUNT(*) FROM rifles")
            row = self.cursor.fetchone()
            if (
                row
                and (row[0] if isinstance(row, (list, tuple)) else row["COUNT(*)"]) > 0
            ):
                return  # already populated

            # Locate demo_weapons.json relative to this package
            import json as _json
            from datetime import datetime as _dt

            _here = Path(__file__).parent
            candidates = [
                _here.parent.parent / "data" / "demo_weapons.json",
                _here.parent / "data" / "demo_weapons.json",
                Path("data") / "demo_weapons.json",
            ]
            json_path = next((p for p in candidates if p.exists()), None)
            if json_path is None:
                return

            profiles = _json.loads(json_path.read_text(encoding="utf-8"))
            now = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
            for p in profiles:
                name = (p.get("name") or "").strip()
                caliber = (p.get("caliber") or "").strip()
                if not name or not caliber:
                    continue

                # Extract barrel data from the active barrel (or first barrel)
                barrels = p.get("barrels") or []
                active_id = p.get("active_barrel_id")
                barrel = next(
                    (b for b in barrels if str(b.get("id")) == str(active_id)),
                    barrels[0] if barrels else {},
                )
                barrel_length_mm = barrel.get("length_mm") or p.get("barrel_length_mm")
                twist_rate = barrel.get("twist") or p.get("twist") or ""

                row_data = {
                    "name": name,
                    "caliber": caliber,
                    "weapon_type": p.get("weapon_type") or "",
                    "preferred_units": p.get("preferred_units") or "",
                    "barrel_length_mm": barrel_length_mm,
                    "twist_rate": twist_rate,
                    "notes": p.get("notes") or "",
                    "created_date": now,
                    "last_updated": now,
                }
                rifle_id = self.insert("rifles", row_data)

                # Store the full JSON profile in rifle_profile_details so barrel editor etc. can read it
                if rifle_id:
                    self.insert(
                        "rifle_profile_details",
                        {
                            "rifle_id": rifle_id,
                            "profile_json": _json.dumps(p, ensure_ascii=False),
                        },
                    )
        except Exception:
            pass

    def delete(self, table: str, condition: str, params: tuple = ()):
        try:
            if self.conn is None or self.cursor is None:
                logger.error("Database not connected")
                return
            query = f"DELETE FROM {table} WHERE {condition}"
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            logger.error(
                tr("database_delete_error", lang=self.language) + f": {str(e)}"
            )

    def get_all(self, table: str, order_by: str = "id") -> List[Dict]:
        """Henter alle rader fra tabell"""
        query = f"SELECT * FROM {table} ORDER BY {order_by}"
        return self.execute_query(query)

    def list_cartridge_standards(
        self,
        caliber_name: str | None = None,
        standard_body: str | None = None,
        include_user_defined: bool = True,
    ) -> List[Dict]:
        query = "SELECT * FROM cartridge_standards WHERE 1=1"
        params: list[Any] = []
        if caliber_name:
            query += " AND caliber_name LIKE ?"
            params.append(f"%{caliber_name}%")
        if standard_body:
            query += " AND standard_body = ?"
            params.append(standard_body)
        if not include_user_defined:
            query += " AND user_defined = 0"
        query += (
            " ORDER BY caliber_name COLLATE NOCASE, standard_body COLLATE NOCASE, id"
        )
        return self.execute_query(query, tuple(params))

    def upsert_cartridge_standard(self, data: Dict[str, Any]) -> int:
        payload = dict(data or {})
        payload["caliber_name"] = str(payload.get("caliber_name") or "").strip()
        if not payload["caliber_name"]:
            raise ValueError("caliber_name is required")
        payload["standard_body"] = str(payload.get("standard_body") or "").strip()
        payload["updated_date"] = payload.get(
            "updated_date"
        ) or datetime.datetime.now().isoformat(timespec="seconds")

        row_id = payload.pop("id", None)
        if row_id:
            self.update("cartridge_standards", payload, "id = ?", (int(row_id),))
            return int(row_id)

        existing = self.execute_query(
            """
            SELECT id FROM cartridge_standards
            WHERE caliber_name = ? AND COALESCE(standard_body, '') = COALESCE(?, '')
              AND COALESCE(source, '') = COALESCE(?, '')
              AND user_defined = ?
            LIMIT 1
            """,
            (
                payload["caliber_name"],
                payload.get("standard_body"),
                payload.get("source"),
                int(payload.get("user_defined") or 0),
            ),
        )
        if existing:
            existing_id = int(existing[0]["id"])
            self.update("cartridge_standards", payload, "id = ?", (existing_id,))
            return existing_id

        payload.setdefault(
            "created_date", datetime.datetime.now().isoformat(timespec="seconds")
        )
        return self.insert("cartridge_standards", payload)

    def list_component_reference_snapshots(
        self,
        component_type: str | None = None,
        source_system: str | None = None,
    ) -> List[Dict]:
        query = "SELECT * FROM component_reference_snapshots WHERE 1=1"
        params: list[Any] = []
        if component_type:
            query += " AND component_type = ?"
            params.append(component_type)
        if source_system:
            query += " AND source_system = ?"
            params.append(source_system)
        query += " ORDER BY component_type, manufacturer COLLATE NOCASE, model_name COLLATE NOCASE, id"
        return self.execute_query(query, tuple(params))

    def upsert_component_reference_snapshot(self, data: Dict[str, Any]) -> int:
        payload = dict(data or {})
        payload["source_system"] = str(payload.get("source_system") or "").strip()
        payload["component_type"] = str(payload.get("component_type") or "").strip()
        if not payload["source_system"] or not payload["component_type"]:
            raise ValueError("source_system and component_type are required")

        payload["updated_date"] = payload.get(
            "updated_date"
        ) or datetime.datetime.now().isoformat(timespec="seconds")
        row_id = payload.pop("id", None)
        if row_id:
            self.update(
                "component_reference_snapshots", payload, "id = ?", (int(row_id),)
            )
            return int(row_id)

        existing = self.execute_query(
            """
            SELECT id FROM component_reference_snapshots
            WHERE source_system = ?
              AND component_type = ?
              AND COALESCE(source_file, '') = COALESCE(?, '')
              AND COALESCE(manufacturer, '') = COALESCE(?, '')
              AND COALESCE(model_name, '') = COALESCE(?, '')
              AND COALESCE(caliber, '') = COALESCE(?, '')
              AND COALESCE(lot_number, '') = COALESCE(?, '')
            LIMIT 1
            """,
            (
                payload["source_system"],
                payload["component_type"],
                payload.get("source_file"),
                payload.get("manufacturer"),
                payload.get("model_name"),
                payload.get("caliber"),
                payload.get("lot_number"),
            ),
        )
        if existing:
            existing_id = int(existing[0]["id"])
            self.update(
                "component_reference_snapshots", payload, "id = ?", (existing_id,)
            )
            return existing_id

        payload.setdefault(
            "created_date", datetime.datetime.now().isoformat(timespec="seconds")
        )
        return self.insert("component_reference_snapshots", payload)

    def get_by_id(self, table: str, id: int) -> Optional[Dict]:
        """Henter en rad basert på ID"""
        query = f"SELECT * FROM {table} WHERE id = ?"
        results = self.execute_query(query, (id,))
        return results[0] if results else None

    def _build_default_barrel_learning_profile(
        self,
        rifle_id: int,
        barrel_id: str,
        barrel_name: str | None = None,
    ) -> Dict[str, Any]:
        return {
            "rifle_id": rifle_id,
            "barrel_id": str(barrel_id),
            "barrel_name": barrel_name or "",
            "status": "insufficient_data",
            "confidence_score": 0.0,
            "confidence_label": "ingen data ennå",
            "data_points": 0,
            "chrono_samples": 0,
            "target_samples": 0,
            "temperature_samples": 0,
            "calibration_offset_fps": 0.0,
            "temp_sensitivity_fps_per_c": None,
            "typical_es_fps": None,
            "typical_sd_fps": None,
            "cold_bore_shift_moa": None,
            "warm_bore_shift_moa": None,
            "throat_erosion_mm": None,
            "estimated_barrel_life_used_percent": None,
            "drift_flag": None,
            "notes": "",
            "profile_data": {},
        }

    def _confidence_label_from_score(self, score: object) -> str:
        try:
            value = float(score)
        except Exception:
            value = 0.0
        if value >= 80:
            return "høy trygghet"
        if value >= 55:
            return "brukbar trygghet"
        if value >= 25:
            return "begrenset datagrunnlag"
        return "ingen data ennå"

    def _build_default_barrel_configuration_learning_profile(
        self,
        rifle_id: int,
        barrel_id: str,
        barrel_name: str | None = None,
        barrel_configuration_id: str | None = None,
        barrel_configuration_name: str | None = None,
    ) -> Dict[str, Any]:
        profile = self._build_default_barrel_learning_profile(
            rifle_id,
            barrel_id,
            barrel_name,
        )
        profile["barrel_configuration_id"] = str(barrel_configuration_id or "").strip()
        profile["barrel_configuration_name"] = str(
            barrel_configuration_name or ""
        ).strip()
        profile["configuration_scope"] = "configuration"
        return profile

    def _resolve_barrel_configuration_learning_profile(
        self,
        base_profile: Dict[str, Any],
        barrel_configuration_id: str | None,
        barrel_configuration_name: str | None = None,
    ) -> Dict[str, Any]:
        resolved_configuration_id = str(barrel_configuration_id or "").strip()
        if not resolved_configuration_id:
            profile = dict(base_profile)
            profile["barrel_configuration_id"] = None
            profile["barrel_configuration_name"] = ""
            profile["configuration_scope"] = "barrel"
            return profile

        default_profile = self._build_default_barrel_configuration_learning_profile(
            int(base_profile.get("rifle_id") or 0),
            str(base_profile.get("barrel_id") or ""),
            str(base_profile.get("barrel_name") or ""),
            resolved_configuration_id,
            barrel_configuration_name,
        )
        profile_data = (
            base_profile.get("profile_data")
            if isinstance(base_profile.get("profile_data"), dict)
            else {}
        )
        configuration_profiles = (
            profile_data.get("configuration_profiles")
            if isinstance(profile_data, dict)
            else {}
        )
        bucket = (
            configuration_profiles.get(resolved_configuration_id)
            if isinstance(configuration_profiles, dict)
            else None
        )
        if not isinstance(bucket, dict):
            return default_profile

        profile = dict(default_profile)
        for key, value in bucket.items():
            if key == "profile_data":
                continue
            profile[key] = value
        bucket_profile_data = (
            bucket.get("profile_data")
            if isinstance(bucket.get("profile_data"), dict)
            else {}
        )
        profile["profile_data"] = dict(bucket_profile_data)
        profile["confidence_label"] = self._confidence_label_from_score(
            profile.get("confidence_score")
        )
        if not profile.get("barrel_name"):
            profile["barrel_name"] = str(base_profile.get("barrel_name") or "")
        if not profile.get("barrel_configuration_name"):
            profile["barrel_configuration_name"] = str(
                barrel_configuration_name or ""
            ).strip()
        return profile

    def _update_barrel_learning_profile_row(
        self,
        rifle_id: int,
        barrel_id: str,
        column_updates: Dict[str, Any],
    ) -> None:
        if not column_updates:
            return
        payload = dict(column_updates)
        payload["updated_at"] = "CURRENT_TIMESTAMP"
        set_clause = ", ".join(
            [
                f"{key}=CURRENT_TIMESTAMP" if key == "updated_at" else f"{key}=?"
                for key in payload.keys()
            ]
        )
        values = tuple(
            value for key, value in payload.items() if key != "updated_at"
        ) + (rifle_id, str(barrel_id))
        query = (
            f"UPDATE barrel_learning_profiles SET {set_clause} "
            "WHERE rifle_id = ? AND barrel_id = ?"
        )
        if self.conn is not None and self.cursor is not None:
            self.cursor.execute(query, values)
            self.conn.commit()

    def get_barrel_learning_profile(
        self,
        rifle_id: int,
        barrel_id: str,
        barrel_name: str | None = None,
        barrel_configuration_id: str | None = None,
        barrel_configuration_name: str | None = None,
    ) -> Dict[str, Any]:
        barrel_id = str(barrel_id)
        rows = self.execute_query(
            """
            SELECT * FROM barrel_learning_profiles
            WHERE rifle_id = ? AND barrel_id = ?
            """,
            (rifle_id, barrel_id),
        )
        if not rows:
            default_profile = self._build_default_barrel_learning_profile(
                rifle_id, barrel_id, barrel_name
            )
            self.insert(
                "barrel_learning_profiles",
                {
                    "rifle_id": rifle_id,
                    "barrel_id": barrel_id,
                    "barrel_name": barrel_name or "",
                    "status": default_profile["status"],
                    "confidence_score": default_profile["confidence_score"],
                    "data_points": default_profile["data_points"],
                    "chrono_samples": default_profile["chrono_samples"],
                    "target_samples": default_profile["target_samples"],
                    "temperature_samples": default_profile["temperature_samples"],
                    "calibration_offset_fps": default_profile["calibration_offset_fps"],
                    "notes": default_profile["notes"],
                    "profile_json": json.dumps(default_profile["profile_data"]),
                },
            )
            if barrel_configuration_id not in (None, ""):
                return self._resolve_barrel_configuration_learning_profile(
                    default_profile,
                    str(barrel_configuration_id),
                    barrel_configuration_name,
                )
            default_profile["barrel_configuration_id"] = None
            default_profile["barrel_configuration_name"] = ""
            default_profile["configuration_scope"] = "barrel"
            return default_profile

        profile = dict(rows[0])
        try:
            profile_data = json.loads(profile.get("profile_json") or "{}")
        except Exception:
            profile_data = {}
        profile["profile_data"] = profile_data if isinstance(profile_data, dict) else {}
        profile["confidence_label"] = self._confidence_label_from_score(
            profile.get("confidence_score")
        )
        if barrel_name and not profile.get("barrel_name"):
            profile["barrel_name"] = barrel_name
        if barrel_configuration_id not in (None, ""):
            return self._resolve_barrel_configuration_learning_profile(
                profile,
                str(barrel_configuration_id),
                barrel_configuration_name,
            )
        profile["barrel_configuration_id"] = None
        profile["barrel_configuration_name"] = ""
        profile["configuration_scope"] = "barrel"
        return profile

    def upsert_barrel_learning_profile(
        self,
        rifle_id: int,
        barrel_id: str,
        updates: Dict[str, Any],
        barrel_name: str | None = None,
    ) -> Dict[str, Any]:
        current = self.get_barrel_learning_profile(rifle_id, barrel_id, barrel_name)
        known_columns = {
            "barrel_name",
            "status",
            "confidence_score",
            "data_points",
            "chrono_samples",
            "target_samples",
            "temperature_samples",
            "calibration_offset_fps",
            "temp_sensitivity_fps_per_c",
            "typical_es_fps",
            "typical_sd_fps",
            "cold_bore_shift_moa",
            "warm_bore_shift_moa",
            "throat_erosion_mm",
            "estimated_barrel_life_used_percent",
            "drift_flag",
            "notes",
        }
        column_updates = {
            key: value for key, value in updates.items() if key in known_columns
        }
        profile_data = dict(current.get("profile_data") or {})
        extra_updates = {
            key: value
            for key, value in updates.items()
            if key not in known_columns and key not in {"rifle_id", "barrel_id"}
        }
        profile_data.update(extra_updates)
        column_updates["profile_json"] = json.dumps(profile_data, ensure_ascii=False)
        self._update_barrel_learning_profile_row(
            rifle_id, str(barrel_id), column_updates
        )
        return self.get_barrel_learning_profile(rifle_id, str(barrel_id), barrel_name)

    def upsert_barrel_configuration_learning_profile(
        self,
        rifle_id: int,
        barrel_id: str,
        barrel_configuration_id: str,
        updates: Dict[str, Any],
        barrel_name: str | None = None,
        barrel_configuration_name: str | None = None,
    ) -> Dict[str, Any]:
        resolved_configuration_id = str(barrel_configuration_id or "").strip()
        if not resolved_configuration_id:
            return self.get_barrel_learning_profile(
                rifle_id, str(barrel_id), barrel_name
            )

        current = self.get_barrel_learning_profile(
            rifle_id, str(barrel_id), barrel_name
        )
        current_configuration = self.get_barrel_learning_profile(
            rifle_id,
            str(barrel_id),
            barrel_name,
            resolved_configuration_id,
            barrel_configuration_name,
        )
        profile_data = dict(current.get("profile_data") or {})
        configuration_profiles = (
            dict(profile_data.get("configuration_profiles") or {})
            if isinstance(profile_data.get("configuration_profiles"), dict)
            else {}
        )
        known_columns = {
            "barrel_name",
            "status",
            "confidence_score",
            "data_points",
            "chrono_samples",
            "target_samples",
            "temperature_samples",
            "calibration_offset_fps",
            "temp_sensitivity_fps_per_c",
            "typical_es_fps",
            "typical_sd_fps",
            "cold_bore_shift_moa",
            "warm_bore_shift_moa",
            "throat_erosion_mm",
            "estimated_barrel_life_used_percent",
            "drift_flag",
            "notes",
        }
        bucket = {
            key: current_configuration.get(key)
            for key in known_columns
            if key in current_configuration
        }
        bucket_profile_data = dict(current_configuration.get("profile_data") or {})
        extra_updates = {
            key: value
            for key, value in updates.items()
            if key not in known_columns and key not in {"rifle_id", "barrel_id"}
        }
        bucket_profile_data.update(extra_updates)
        bucket.update(
            {key: value for key, value in updates.items() if key in known_columns}
        )
        bucket["barrel_name"] = str(
            bucket.get("barrel_name") or barrel_name or current.get("barrel_name") or ""
        ).strip()
        bucket["barrel_configuration_id"] = resolved_configuration_id
        bucket["barrel_configuration_name"] = str(
            bucket.get("barrel_configuration_name")
            or barrel_configuration_name
            or current_configuration.get("barrel_configuration_name")
            or ""
        ).strip()
        bucket["configuration_scope"] = "configuration"
        bucket["profile_data"] = bucket_profile_data
        configuration_profiles[resolved_configuration_id] = bucket
        profile_data["configuration_profiles"] = configuration_profiles

        row_updates: Dict[str, Any] = {
            "profile_json": json.dumps(profile_data, ensure_ascii=False),
        }
        resolved_barrel_name = str(
            barrel_name or current.get("barrel_name") or ""
        ).strip()
        if resolved_barrel_name:
            row_updates["barrel_name"] = resolved_barrel_name
        self._update_barrel_learning_profile_row(rifle_id, str(barrel_id), row_updates)
        return self.get_barrel_learning_profile(
            rifle_id,
            str(barrel_id),
            barrel_name,
            resolved_configuration_id,
            barrel_configuration_name,
        )

    def _running_average(
        self, current_value: object, current_count: object, new_value: object
    ) -> float | None:
        try:
            new_float = float(new_value)
        except Exception:
            return None
        try:
            current_float = float(current_value)
            count = max(0, int(current_count or 0))
        except Exception:
            current_float = 0.0
            count = 0
        if count <= 0:
            return round(new_float, 3)
        return round(((current_float * count) + new_float) / (count + 1), 3)

    def _estimate_barrel_learning_state(
        self,
        chrono_samples: int,
        target_samples: int,
        temperature_samples: int,
    ) -> tuple[str, float]:
        confidence = min(
            95.0,
            (chrono_samples * 12.0)
            + (target_samples * 15.0)
            + (temperature_samples * 6.0),
        )
        if chrono_samples >= 3 and target_samples >= 2:
            return "learning", round(confidence, 1)
        if chrono_samples >= 2 or target_samples >= 1:
            return "calibrating", round(confidence, 1)
        return "insufficient_data", round(confidence, 1)

    def resolve_learning_barrel(
        self,
        rifle_id: int,
        barrel_id: object | None = None,
        barrel_name: object | None = None,
    ) -> Dict[str, str]:
        resolved_id = str(barrel_id).strip() if barrel_id not in (None, "") else ""
        resolved_name = (
            str(barrel_name).strip() if barrel_name not in (None, "") else ""
        )

        if resolved_id:
            return {"barrel_id": resolved_id, "barrel_name": resolved_name}

        rows = self.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (rifle_id,),
        )
        if not rows or not rows[0].get("profile_json"):
            return {}
        try:
            details = json.loads(rows[0]["profile_json"])
        except Exception:
            return {}
        if not isinstance(details, dict):
            return {}

        resolved_id = str(details.get("active_barrel_id") or "").strip()
        if not resolved_id:
            return {}

        barrels = details.get("barrels") or []
        if isinstance(barrels, list):
            for barrel in barrels:
                if isinstance(barrel, dict) and str(barrel.get("id")) == resolved_id:
                    resolved_name = str(barrel.get("name") or resolved_name).strip()
                    break
        return {"barrel_id": resolved_id, "barrel_name": resolved_name}

    def record_barrel_chronograph_observation(
        self,
        rifle_id: int,
        barrel_id: object | None,
        barrel_name: object | None,
        session_data: Dict[str, Any],
        barrel_configuration_id: object | None = None,
        barrel_configuration_name: object | None = None,
    ) -> Dict[str, Any]:
        barrel = self.resolve_learning_barrel(rifle_id, barrel_id, barrel_name)
        if not barrel.get("barrel_id"):
            return {}

        resolved_configuration_id = str(
            barrel_configuration_id
            if barrel_configuration_id not in (None, "")
            else session_data.get("barrel_configuration_id") or ""
        ).strip()
        resolved_configuration_name = str(
            barrel_configuration_name
            if barrel_configuration_name not in (None, "")
            else session_data.get("barrel_configuration_name") or ""
        ).strip()

        current = self.get_barrel_learning_profile(
            rifle_id, barrel["barrel_id"], barrel.get("barrel_name")
        )
        chrono_samples = int(current.get("chrono_samples") or 0)
        target_samples = int(current.get("target_samples") or 0)
        temperature_samples = int(current.get("temperature_samples") or 0)
        has_temperature = session_data.get("temperature_f") is not None

        next_chrono = chrono_samples + 1
        next_temp = temperature_samples + (1 if has_temperature else 0)
        status, confidence_score = self._estimate_barrel_learning_state(
            next_chrono, target_samples, next_temp
        )

        updates = {
            "barrel_name": barrel.get("barrel_name") or current.get("barrel_name"),
            "status": status,
            "confidence_score": confidence_score,
            "data_points": int(current.get("data_points") or 0) + 1,
            "chrono_samples": next_chrono,
            "temperature_samples": next_temp,
            "typical_es_fps": self._running_average(
                current.get("typical_es_fps"),
                chrono_samples,
                session_data.get("es_fps"),
            ),
            "typical_sd_fps": self._running_average(
                current.get("typical_sd_fps"),
                chrono_samples,
                session_data.get("sd_fps"),
            ),
            "last_avg_velocity_fps": session_data.get("avg_velocity_fps"),
            "last_chronograph_session_name": session_data.get("session_name"),
            "last_chronograph_session_date": session_data.get("session_date"),
        }
        if session_data.get("temperature_f") is not None:
            updates["last_temperature_f"] = session_data.get("temperature_f")

        aggregate_profile = self.upsert_barrel_learning_profile(
            rifle_id,
            barrel["barrel_id"],
            updates,
            barrel.get("barrel_name"),
        )
        if not resolved_configuration_id:
            return aggregate_profile

        configuration_current = self.get_barrel_learning_profile(
            rifle_id,
            barrel["barrel_id"],
            barrel.get("barrel_name"),
            resolved_configuration_id,
            resolved_configuration_name,
        )
        configuration_chrono_samples = int(
            configuration_current.get("chrono_samples") or 0
        )
        configuration_target_samples = int(
            configuration_current.get("target_samples") or 0
        )
        configuration_temperature_samples = int(
            configuration_current.get("temperature_samples") or 0
        )
        configuration_next_chrono = configuration_chrono_samples + 1
        configuration_next_temp = configuration_temperature_samples + (
            1 if has_temperature else 0
        )
        configuration_status, configuration_confidence_score = (
            self._estimate_barrel_learning_state(
                configuration_next_chrono,
                configuration_target_samples,
                configuration_next_temp,
            )
        )
        configuration_updates = {
            "barrel_name": barrel.get("barrel_name")
            or configuration_current.get("barrel_name"),
            "status": configuration_status,
            "confidence_score": configuration_confidence_score,
            "data_points": int(configuration_current.get("data_points") or 0) + 1,
            "chrono_samples": configuration_next_chrono,
            "temperature_samples": configuration_next_temp,
            "typical_es_fps": self._running_average(
                configuration_current.get("typical_es_fps"),
                configuration_chrono_samples,
                session_data.get("es_fps"),
            ),
            "typical_sd_fps": self._running_average(
                configuration_current.get("typical_sd_fps"),
                configuration_chrono_samples,
                session_data.get("sd_fps"),
            ),
            "last_avg_velocity_fps": session_data.get("avg_velocity_fps"),
            "last_chronograph_session_name": session_data.get("session_name"),
            "last_chronograph_session_date": session_data.get("session_date"),
        }
        if session_data.get("temperature_f") is not None:
            configuration_updates["last_temperature_f"] = session_data.get(
                "temperature_f"
            )
        return self.upsert_barrel_configuration_learning_profile(
            rifle_id,
            barrel["barrel_id"],
            resolved_configuration_id,
            configuration_updates,
            barrel.get("barrel_name"),
            resolved_configuration_name,
        )

    def record_barrel_target_observation(
        self,
        rifle_id: int,
        barrel_id: object | None,
        barrel_name: object | None,
        session_data: Dict[str, Any],
        barrel_configuration_id: object | None = None,
        barrel_configuration_name: object | None = None,
    ) -> Dict[str, Any]:
        barrel = self.resolve_learning_barrel(rifle_id, barrel_id, barrel_name)
        if not barrel.get("barrel_id"):
            return {}

        resolved_configuration_id = str(
            barrel_configuration_id
            if barrel_configuration_id not in (None, "")
            else session_data.get("barrel_configuration_id") or ""
        ).strip()
        resolved_configuration_name = str(
            barrel_configuration_name
            if barrel_configuration_name not in (None, "")
            else session_data.get("barrel_configuration_name") or ""
        ).strip()

        current = self.get_barrel_learning_profile(
            rifle_id, barrel["barrel_id"], barrel.get("barrel_name")
        )
        chrono_samples = int(current.get("chrono_samples") or 0)
        target_samples = int(current.get("target_samples") or 0)
        temperature_samples = int(current.get("temperature_samples") or 0)

        next_target = target_samples + 1
        status, confidence_score = self._estimate_barrel_learning_state(
            chrono_samples, next_target, temperature_samples
        )

        group_value = session_data.get("best_group_mm")
        updates = {
            "barrel_name": barrel.get("barrel_name") or current.get("barrel_name"),
            "status": status,
            "confidence_score": confidence_score,
            "data_points": int(current.get("data_points") or 0) + 1,
            "target_samples": next_target,
            "last_best_group_mm": group_value,
            "last_target_session_date": session_data.get("date"),
            "last_target_distance_m": session_data.get("distance_meters"),
            "typical_group_mm": self._running_average(
                current.get("profile_data", {}).get("typical_group_mm"),
                target_samples,
                group_value,
            ),
        }
        aggregate_profile = self.upsert_barrel_learning_profile(
            rifle_id,
            barrel["barrel_id"],
            updates,
            barrel.get("barrel_name"),
        )
        if not resolved_configuration_id:
            return aggregate_profile

        configuration_current = self.get_barrel_learning_profile(
            rifle_id,
            barrel["barrel_id"],
            barrel.get("barrel_name"),
            resolved_configuration_id,
            resolved_configuration_name,
        )
        configuration_chrono_samples = int(
            configuration_current.get("chrono_samples") or 0
        )
        configuration_target_samples = int(
            configuration_current.get("target_samples") or 0
        )
        configuration_temperature_samples = int(
            configuration_current.get("temperature_samples") or 0
        )
        configuration_next_target = configuration_target_samples + 1
        configuration_status, configuration_confidence_score = (
            self._estimate_barrel_learning_state(
                configuration_chrono_samples,
                configuration_next_target,
                configuration_temperature_samples,
            )
        )
        configuration_updates = {
            "barrel_name": barrel.get("barrel_name")
            or configuration_current.get("barrel_name"),
            "status": configuration_status,
            "confidence_score": configuration_confidence_score,
            "data_points": int(configuration_current.get("data_points") or 0) + 1,
            "target_samples": configuration_next_target,
            "last_best_group_mm": group_value,
            "last_target_session_date": session_data.get("date"),
            "last_target_distance_m": session_data.get("distance_meters"),
            "typical_group_mm": self._running_average(
                configuration_current.get("profile_data", {}).get("typical_group_mm"),
                configuration_target_samples,
                group_value,
            ),
        }
        return self.upsert_barrel_configuration_learning_profile(
            rifle_id,
            barrel["barrel_id"],
            resolved_configuration_id,
            configuration_updates,
            barrel.get("barrel_name"),
            resolved_configuration_name,
        )

    def _build_default_case_learning_profile(self, case_id: int) -> Dict[str, Any]:
        return {
            "case_id": case_id,
            "status": "insufficient_data",
            "confidence_score": 0.0,
            "confidence_label": "ingen data ennå",
            "data_points": 0,
            "h2o_samples": 0,
            "firing_events": 0,
            "prep_events": 0,
            "anneal_events": 0,
            "avg_case_capacity_h2o": None,
            "capacity_spread_h2o": None,
            "avg_case_weight_gr": None,
            "typical_times_fired": None,
            "estimated_remaining_cycles": None,
            "drift_flag": None,
            "notes": "",
            "profile_data": {},
        }

    def get_case_learning_profile(self, case_id: int) -> Dict[str, Any]:
        rows = self.execute_query(
            "SELECT * FROM case_learning_profiles WHERE case_id = ?",
            (case_id,),
        )
        if not rows:
            default_profile = self._build_default_case_learning_profile(case_id)
            self.insert(
                "case_learning_profiles",
                {
                    "case_id": case_id,
                    "status": default_profile["status"],
                    "confidence_score": default_profile["confidence_score"],
                    "data_points": default_profile["data_points"],
                    "h2o_samples": default_profile["h2o_samples"],
                    "firing_events": default_profile["firing_events"],
                    "prep_events": default_profile["prep_events"],
                    "anneal_events": default_profile["anneal_events"],
                    "notes": default_profile["notes"],
                    "profile_json": json.dumps(default_profile["profile_data"]),
                },
            )
            return default_profile

        profile = dict(rows[0])
        try:
            profile_data = json.loads(profile.get("profile_json") or "{}")
        except Exception:
            profile_data = {}
        profile["profile_data"] = profile_data if isinstance(profile_data, dict) else {}
        profile["confidence_label"] = self._confidence_label_from_score(
            profile.get("confidence_score")
        )
        return profile

    def upsert_case_learning_profile(
        self, case_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        current = self.get_case_learning_profile(case_id)
        known_columns = {
            "status",
            "confidence_score",
            "data_points",
            "h2o_samples",
            "firing_events",
            "prep_events",
            "anneal_events",
            "avg_case_capacity_h2o",
            "capacity_spread_h2o",
            "avg_case_weight_gr",
            "typical_times_fired",
            "estimated_remaining_cycles",
            "drift_flag",
            "notes",
        }
        column_updates = {
            key: value for key, value in updates.items() if key in known_columns
        }
        profile_data = dict(current.get("profile_data") or {})
        extra_updates = {
            key: value for key, value in updates.items() if key not in known_columns
        }
        profile_data.update(extra_updates)
        column_updates["profile_json"] = json.dumps(profile_data, ensure_ascii=False)
        column_updates["updated_at"] = "CURRENT_TIMESTAMP"

        set_clause = ", ".join(
            [
                f"{key}=CURRENT_TIMESTAMP" if key == "updated_at" else f"{key}=?"
                for key in column_updates.keys()
            ]
        )
        values = tuple(
            value for key, value in column_updates.items() if key != "updated_at"
        ) + (case_id,)
        query = f"UPDATE case_learning_profiles SET {set_clause} WHERE case_id = ?"
        if self.conn is not None and self.cursor is not None:
            self.cursor.execute(query, values)
            self.conn.commit()
        return self.get_case_learning_profile(case_id)

    def refresh_case_learning_profile(self, case_id: int) -> Dict[str, Any]:
        case_row = self.get_by_id("cases", case_id)
        if not case_row:
            return {}

        measurements = self.execute_query(
            """
            SELECT case_weight_gr
            FROM case_measurements
            WHERE case_id = ?
            ORDER BY measurement_date DESC
            """,
            (case_id,),
        )
        firings = self.execute_query(
            """
            SELECT rounds_fired, pressure_level, annealing_due, trim_due
            FROM case_firing_log
            WHERE case_id = ?
            ORDER BY firing_date DESC
            """,
            (case_id,),
        )
        annealings = self.execute_query(
            """
            SELECT id
            FROM case_annealing_log
            WHERE case_id = ?
            """,
            (case_id,),
        )
        preps = self.execute_query(
            """
            SELECT id, trimmed, neck_turned, weight_sorted
            FROM case_prep_log
            WHERE case_id = ?
            """,
            (case_id,),
        )

        h2o_values = []
        if isinstance(case_row.get("case_capacity_gr_h2o"), (int, float)):
            h2o_values.append(float(case_row["case_capacity_gr_h2o"]))
        avg_case_capacity_h2o = (
            round(sum(h2o_values) / len(h2o_values), 3) if h2o_values else None
        )
        capacity_spread_h2o = (
            round(max(h2o_values) - min(h2o_values), 3)
            if len(h2o_values) > 1
            else 0.0 if h2o_values else None
        )

        weight_values = [
            float(row["case_weight_gr"])
            for row in measurements
            if isinstance(row.get("case_weight_gr"), (int, float))
        ]
        if not weight_values and isinstance(
            case_row.get("avg_weight_gr"), (int, float)
        ):
            weight_values.append(float(case_row["avg_weight_gr"]))
        avg_case_weight_gr = (
            round(sum(weight_values) / len(weight_values), 3) if weight_values else None
        )

        times_fired = float(case_row.get("times_fired") or 0)
        quantity = int(case_row.get("quantity") or 0)
        retired_quantity = int(case_row.get("retired_quantity") or 0)
        total_quantity = max(1, quantity + retired_quantity)
        estimated_remaining_cycles = max(0.0, round(12.0 - times_fired, 2))

        firing_events = len(firings)
        prep_events = len(preps)
        anneal_events = len(annealings)
        h2o_samples = len(h2o_values)
        data_points = h2o_samples + firing_events + prep_events + anneal_events
        confidence_score = min(
            95.0,
            (h2o_samples * 20.0)
            + (firing_events * 8.0)
            + (prep_events * 5.0)
            + (anneal_events * 4.0),
        )
        if (h2o_samples >= 1 and firing_events >= 1) or data_points >= 4:
            status = "learning"
        elif firing_events >= 1 or h2o_samples >= 1:
            status = "calibrating"
        else:
            status = "insufficient_data"

        drift_flag = None
        if times_fired >= 10 or retired_quantity > 0:
            drift_flag = "watch_lifecycle"
        if firing_events and any(
            str(row.get("pressure_level") or "").lower() == "max" for row in firings
        ):
            drift_flag = "pressure_watch"

        updates = {
            "status": status,
            "confidence_score": round(confidence_score, 1),
            "data_points": data_points,
            "h2o_samples": h2o_samples,
            "firing_events": firing_events,
            "prep_events": prep_events,
            "anneal_events": anneal_events,
            "avg_case_capacity_h2o": avg_case_capacity_h2o,
            "capacity_spread_h2o": capacity_spread_h2o,
            "avg_case_weight_gr": avg_case_weight_gr,
            "typical_times_fired": times_fired,
            "estimated_remaining_cycles": estimated_remaining_cycles,
            "drift_flag": drift_flag,
            "available_quantity": quantity,
            "retired_quantity": retired_quantity,
            "lifecycle_used_ratio": round(retired_quantity / total_quantity, 3),
        }
        return self.upsert_case_learning_profile(case_id, updates)

    def _build_default_component_lot_learning_profile(
        self,
        component_lot_id: int,
        component_type: str,
        component_id: int,
        lot_number: str,
    ) -> Dict[str, Any]:
        return {
            "component_lot_id": component_lot_id,
            "component_type": component_type,
            "component_id": component_id,
            "lot_number": lot_number,
            "status": "insufficient_data",
            "confidence_score": 0.0,
            "confidence_label": "ingen data ennå",
            "data_points": 0,
            "batch_samples": 0,
            "chrono_samples": 0,
            "temperature_samples": 0,
            "avg_velocity_fps": None,
            "velocity_offset_fps": None,
            "temp_sensitivity_fps_per_c": None,
            "typical_es_fps": None,
            "best_recorded_moa": None,
            "pressure_watch_count": 0,
            "drift_flag": None,
            "notes": "",
            "profile_data": {},
        }

    def get_component_lot_learning_profile(
        self, component_lot_id: int
    ) -> Dict[str, Any]:
        rows = self.execute_query(
            "SELECT * FROM component_lot_learning_profiles WHERE component_lot_id = ?",
            (component_lot_id,),
        )
        if not rows:
            lot_row = self.get_by_id("component_lots", component_lot_id)
            if not lot_row:
                return {}
            default_profile = self._build_default_component_lot_learning_profile(
                component_lot_id,
                str(lot_row.get("component_type") or ""),
                int(lot_row.get("component_id") or 0),
                str(lot_row.get("lot_number") or ""),
            )
            self.insert(
                "component_lot_learning_profiles",
                {
                    "component_lot_id": component_lot_id,
                    "component_type": default_profile["component_type"],
                    "component_id": default_profile["component_id"],
                    "lot_number": default_profile["lot_number"],
                    "status": default_profile["status"],
                    "confidence_score": default_profile["confidence_score"],
                    "data_points": default_profile["data_points"],
                    "batch_samples": default_profile["batch_samples"],
                    "chrono_samples": default_profile["chrono_samples"],
                    "temperature_samples": default_profile["temperature_samples"],
                    "pressure_watch_count": default_profile["pressure_watch_count"],
                    "notes": default_profile["notes"],
                    "profile_json": json.dumps(
                        default_profile["profile_data"], ensure_ascii=False
                    ),
                },
            )
            return default_profile

        profile = dict(rows[0])
        try:
            profile_data = json.loads(profile.get("profile_json") or "{}")
        except Exception:
            profile_data = {}
        profile["profile_data"] = profile_data if isinstance(profile_data, dict) else {}
        profile["confidence_label"] = self._confidence_label_from_score(
            profile.get("confidence_score")
        )
        return profile

    def upsert_component_lot_learning_profile(
        self, component_lot_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        current = self.get_component_lot_learning_profile(component_lot_id)
        if not current:
            return {}
        known_columns = {
            "component_type",
            "component_id",
            "lot_number",
            "status",
            "confidence_score",
            "data_points",
            "batch_samples",
            "chrono_samples",
            "temperature_samples",
            "avg_velocity_fps",
            "velocity_offset_fps",
            "temp_sensitivity_fps_per_c",
            "typical_es_fps",
            "best_recorded_moa",
            "pressure_watch_count",
            "drift_flag",
            "notes",
        }
        column_updates = {
            key: value for key, value in updates.items() if key in known_columns
        }
        profile_data = dict(current.get("profile_data") or {})
        extra_updates = {
            key: value for key, value in updates.items() if key not in known_columns
        }
        profile_data.update(extra_updates)
        column_updates["profile_json"] = json.dumps(profile_data, ensure_ascii=False)
        column_updates["updated_at"] = "CURRENT_TIMESTAMP"

        set_clause = ", ".join(
            [
                f"{key}=CURRENT_TIMESTAMP" if key == "updated_at" else f"{key}=?"
                for key in column_updates.keys()
            ]
        )
        values = tuple(
            value for key, value in column_updates.items() if key != "updated_at"
        ) + (component_lot_id,)
        query = (
            "UPDATE component_lot_learning_profiles "
            f"SET {set_clause} WHERE component_lot_id = ?"
        )
        if self.conn is not None and self.cursor is not None:
            self.cursor.execute(query, values)
            self.conn.commit()
        return self.get_component_lot_learning_profile(component_lot_id)

    def refresh_powder_lot_learning_profile(
        self, component_lot_id: int
    ) -> Dict[str, Any]:
        lot_row = self.get_by_id("component_lots", component_lot_id)
        if not lot_row:
            return {}
        if str(lot_row.get("component_type") or "") != "powder":
            return self.get_component_lot_learning_profile(component_lot_id)

        powder_id = int(lot_row.get("component_id") or 0)
        lot_number = str(lot_row.get("lot_number") or "").strip()
        batches = self.execute_query(
            """
            SELECT actual_velocity_avg_fps, predicted_velocity_fps, actual_es_fps,
                   loading_temperature_c, pressure_signs_observed,
                   actual_best_moa, actual_moa_avg, intended_use
            FROM loaded_ammo_batches
            WHERE powder_id = ? AND powder_lot_number = ?
            ORDER BY loaded_date DESC
            """,
            (powder_id, lot_number),
        )
        chrono_rows = self.execute_query(
            """
            SELECT avg_velocity_fps, es_fps, temperature_f, import_meta_json
            FROM chronograph_sessions
            WHERE import_meta_json IS NOT NULL AND import_meta_json != ''
            ORDER BY session_date DESC, id DESC
            """
        )
        chrono_matches: list[Dict[str, Any]] = []
        for row in chrono_rows:
            try:
                import_meta = json.loads(row.get("import_meta_json") or "{}")
            except Exception:
                continue
            if not isinstance(import_meta, dict):
                continue
            batch_context = import_meta.get("batch_context")
            if not isinstance(batch_context, dict):
                continue
            batch_powder_id = batch_context.get("powder_id")
            batch_lot_number = str(batch_context.get("powder_lot_number") or "").strip()
            try:
                batch_powder_id = int(batch_powder_id)
            except Exception:
                batch_powder_id = None
            if batch_powder_id != powder_id or batch_lot_number != lot_number:
                continue
            chrono_matches.append(row)

        actual_velocities = [
            float(row["actual_velocity_avg_fps"])
            for row in batches
            if isinstance(row.get("actual_velocity_avg_fps"), (int, float))
        ]
        chrono_velocities = [
            float(row["avg_velocity_fps"])
            for row in chrono_matches
            if isinstance(row.get("avg_velocity_fps"), (int, float))
        ]
        predicted_pairs = [
            (
                float(row["actual_velocity_avg_fps"]),
                float(row["predicted_velocity_fps"]),
            )
            for row in batches
            if isinstance(row.get("actual_velocity_avg_fps"), (int, float))
            and isinstance(row.get("predicted_velocity_fps"), (int, float))
        ]
        es_values = [
            float(row["actual_es_fps"])
            for row in batches
            if isinstance(row.get("actual_es_fps"), (int, float))
        ]
        es_values.extend(
            float(row["es_fps"])
            for row in chrono_matches
            if isinstance(row.get("es_fps"), (int, float))
        )
        moa_values = [
            float(row.get("actual_best_moa"))
            for row in batches
            if isinstance(row.get("actual_best_moa"), (int, float))
        ]
        temp_velocity_points = [
            (
                float(row["loading_temperature_c"]),
                float(row["actual_velocity_avg_fps"]),
            )
            for row in batches
            if isinstance(row.get("loading_temperature_c"), (int, float))
            and isinstance(row.get("actual_velocity_avg_fps"), (int, float))
        ]
        temp_velocity_points.extend(
            (
                round((float(row["temperature_f"]) - 32.0) * (5.0 / 9.0), 2),
                float(row["avg_velocity_fps"]),
            )
            for row in chrono_matches
            if isinstance(row.get("temperature_f"), (int, float))
            and isinstance(row.get("avg_velocity_fps"), (int, float))
        )
        pressure_watch_count = sum(
            1 for row in batches if int(row.get("pressure_signs_observed") or 0) == 1
        )

        velocity_pool = actual_velocities + chrono_velocities
        avg_velocity_fps = (
            round(sum(velocity_pool) / len(velocity_pool), 1) if velocity_pool else None
        )
        velocity_offset_fps = (
            round(
                sum(actual - predicted for actual, predicted in predicted_pairs)
                / len(predicted_pairs),
                1,
            )
            if predicted_pairs
            else None
        )
        typical_es_fps = (
            round(sum(es_values) / len(es_values), 1) if es_values else None
        )
        best_recorded_moa = round(min(moa_values), 3) if moa_values else None
        temp_sensitivity_fps_per_c = None
        unique_temps = {round(temp, 2) for temp, _ in temp_velocity_points}
        if len(unique_temps) >= 2:
            sorted_points = sorted(temp_velocity_points, key=lambda item: item[0])
            low_temp, low_velocity = sorted_points[0]
            high_temp, high_velocity = sorted_points[-1]
            if high_temp != low_temp:
                temp_sensitivity_fps_per_c = round(
                    (high_velocity - low_velocity) / (high_temp - low_temp), 2
                )

        batch_samples = len(batches)
        chrono_import_samples = len(chrono_matches)
        temperature_samples = len(unique_temps)
        chrono_samples = len(velocity_pool)
        data_points = batch_samples + chrono_samples + temperature_samples
        confidence_score = min(
            95.0,
            (batch_samples * 18.0)
            + (chrono_samples * 8.0)
            + (temperature_samples * 10.0),
        )
        if batch_samples >= 3 or (chrono_samples >= 2 and temperature_samples >= 2):
            status = "learning"
        elif batch_samples >= 1 or chrono_samples >= 1:
            status = "calibrating"
        else:
            status = "insufficient_data"

        drift_flag = None
        if pressure_watch_count:
            drift_flag = "pressure_watch"
        elif velocity_offset_fps is not None and abs(velocity_offset_fps) >= 25:
            drift_flag = "offset_watch"
        elif typical_es_fps is not None and typical_es_fps >= 25:
            drift_flag = "consistency_watch"

        intended_use_counts: Dict[str, int] = {}
        for row in batches:
            intended_use = str(row.get("intended_use") or "").strip()
            if intended_use:
                intended_use_counts[intended_use] = (
                    intended_use_counts.get(intended_use, 0) + 1
                )

        updates = {
            "component_type": "powder",
            "component_id": powder_id,
            "lot_number": lot_number,
            "status": status,
            "confidence_score": round(confidence_score, 1),
            "data_points": data_points,
            "batch_samples": batch_samples,
            "chrono_samples": chrono_samples,
            "temperature_samples": temperature_samples,
            "avg_velocity_fps": avg_velocity_fps,
            "velocity_offset_fps": velocity_offset_fps,
            "temp_sensitivity_fps_per_c": temp_sensitivity_fps_per_c,
            "typical_es_fps": typical_es_fps,
            "best_recorded_moa": best_recorded_moa,
            "pressure_watch_count": pressure_watch_count,
            "drift_flag": drift_flag,
            "quantity_remaining": lot_row.get("quantity_remaining"),
            "is_active": int(lot_row.get("is_active") or 0),
            "intended_use_counts": intended_use_counts,
            "chrono_import_samples": chrono_import_samples,
        }
        return self.upsert_component_lot_learning_profile(component_lot_id, updates)

    def compare_powder_lots(
        self, component_id: int, current_lot_id: int
    ) -> Dict[str, Any]:
        rows = self.execute_query(
            """
            SELECT id, lot_number, purchase_date
            FROM component_lots
            WHERE component_type = 'powder' AND component_id = ?
            ORDER BY purchase_date DESC, created_date DESC, id DESC
            """,
            (component_id,),
        )
        if not rows:
            return {}

        current_row = next(
            (row for row in rows if int(row.get("id") or 0) == int(current_lot_id)),
            None,
        )
        if not current_row:
            return {}

        previous_row = next(
            (row for row in rows if int(row.get("id") or 0) != int(current_lot_id)),
            None,
        )
        current_profile = self.refresh_powder_lot_learning_profile(current_lot_id)
        if not previous_row:
            return {
                "current_lot_id": current_lot_id,
                "current_lot_number": current_row.get("lot_number"),
                "status": "baseline_only",
                "severity": "info",
                "title": "Første lærte kruttlot",
                "message": "Dette lotet har ingen tidligere lot å sammenligne mot ennå.",
                "recommended_action": "Bygg en kort verifiseringsserie og bruk dette som baseline for neste lotbytte.",
                "current_profile": current_profile,
            }

        previous_profile = self.refresh_powder_lot_learning_profile(
            int(previous_row["id"])
        )
        current_offset = current_profile.get("velocity_offset_fps")
        previous_offset = previous_profile.get("velocity_offset_fps")
        current_avg = current_profile.get("avg_velocity_fps")
        previous_avg = previous_profile.get("avg_velocity_fps")
        current_es = current_profile.get("typical_es_fps")
        previous_es = previous_profile.get("typical_es_fps")
        current_temp = current_profile.get("temp_sensitivity_fps_per_c")
        previous_temp = previous_profile.get("temp_sensitivity_fps_per_c")

        avg_shift = None
        if isinstance(current_avg, (int, float)) and isinstance(
            previous_avg, (int, float)
        ):
            avg_shift = round(float(current_avg) - float(previous_avg), 1)
        offset_shift = None
        if isinstance(current_offset, (int, float)) and isinstance(
            previous_offset, (int, float)
        ):
            offset_shift = round(float(current_offset) - float(previous_offset), 1)
        es_shift = None
        if isinstance(current_es, (int, float)) and isinstance(
            previous_es, (int, float)
        ):
            es_shift = round(float(current_es) - float(previous_es), 1)
        temp_shift = None
        if isinstance(current_temp, (int, float)) and isinstance(
            previous_temp, (int, float)
        ):
            temp_shift = round(float(current_temp) - float(previous_temp), 2)

        severity = "ok"
        status = "stable"
        title = "Lotene ser like ut"
        recommended_action = (
            "Kort verifiseringsserie er vanligvis nok før du bruker gamle data videre."
        )
        verification_plan = {
            "shots": 3,
            "start_delta_grains": 0.0,
            "focus": "Bekreft at hastighet, ES og trykktegn fortsatt matcher tidligere lot.",
        }
        suggested_charge_adjustment_grains = 0.0
        notes: list[str] = []

        if avg_shift is not None:
            notes.append(f"Snittfart {avg_shift:+.1f} fps")
        if offset_shift is not None:
            notes.append(f"Offset {offset_shift:+.1f} fps")
        if es_shift is not None:
            notes.append(f"ES {es_shift:+.1f}")
        if temp_shift is not None:
            notes.append(f"Temp {temp_shift:+.2f} fps/C")

        max_velocity_delta = max(
            abs(avg_shift or 0.0),
            abs(offset_shift or 0.0),
        )
        if (
            max_velocity_delta >= 25
            or current_profile.get("pressure_watch_count")
            or previous_profile.get("pressure_watch_count")
        ):
            severity = "high"
            status = "retest_required"
            title = "Tydelig lotavvik"
            recommended_action = "Start konservativt og kjør ny verifiseringsserie før gamle ladedata brukes direkte."
            if (avg_shift or 0.0) > 0 or (offset_shift or 0.0) > 0:
                suggested_charge_adjustment_grains = -0.2
                verification_plan = {
                    "shots": 5,
                    "start_delta_grains": -0.2,
                    "focus": "Start 0.2 gr under forrige bekreftede ladning og chrono de første 5 skuddene før videre testing.",
                }
            else:
                verification_plan = {
                    "shots": 5,
                    "start_delta_grains": 0.0,
                    "focus": "Kjør 5 kontrollskudd på eksisterende ladning før du vurderer endringer oppover.",
                }
        elif max_velocity_delta >= 12 or (es_shift is not None and abs(es_shift) >= 6):
            severity = "watch"
            status = "watch"
            title = "Merkbart lotavvik"
            recommended_action = "Verifiser hastighet og trykktegn med noen få kontrollskudd før videre bruk."
            if (avg_shift or 0.0) > 0 or (offset_shift or 0.0) > 0:
                suggested_charge_adjustment_grains = -0.1
                verification_plan = {
                    "shots": 3,
                    "start_delta_grains": -0.1,
                    "focus": "Start 0.1 gr under forrige ladning og chrono 3 kontrollskudd.",
                }
            else:
                verification_plan = {
                    "shots": 3,
                    "start_delta_grains": 0.0,
                    "focus": "Hold ladningen uendret og chrono 3 kontrollskudd før eventuell justering.",
                }

        message = f"Sammenlignet med forrige lot {previous_row.get('lot_number')}: " + (
            ", ".join(notes) if notes else "for lite data for detaljert sammenligning."
        )
        return {
            "current_lot_id": current_lot_id,
            "current_lot_number": current_row.get("lot_number"),
            "previous_lot_id": previous_row.get("id"),
            "previous_lot_number": previous_row.get("lot_number"),
            "status": status,
            "severity": severity,
            "title": title,
            "message": message,
            "recommended_action": recommended_action,
            "suggested_charge_adjustment_grains": suggested_charge_adjustment_grains,
            "verification_plan": verification_plan,
            "avg_velocity_shift_fps": avg_shift,
            "velocity_offset_shift_fps": offset_shift,
            "typical_es_shift_fps": es_shift,
            "temp_sensitivity_shift_fps_per_c": temp_shift,
            "current_profile": current_profile,
            "previous_profile": previous_profile,
        }

    def refresh_primer_lot_learning_profile(
        self, component_lot_id: int
    ) -> Dict[str, Any]:
        lot_row = self.get_by_id("component_lots", component_lot_id)
        if not lot_row or str(lot_row.get("component_type") or "") != "primers":
            return self.get_component_lot_learning_profile(component_lot_id)

        primer_id = int(lot_row.get("component_id") or 0)
        lot_number = str(lot_row.get("lot_number") or "").strip()

        batches = self.execute_query(
            """
            SELECT actual_velocity_avg_fps, actual_es_fps, actual_sd_fps,
                   actual_best_moa, pressure_signs_observed, quantity_remaining,
                   intended_use
            FROM loaded_ammo_batches
            WHERE primer_id = ? AND primer_lot_number = ?
            ORDER BY loaded_date DESC
            """,
            (primer_id, lot_number),
        )

        velocity_values = [
            float(row["actual_velocity_avg_fps"])
            for row in batches
            if isinstance(row.get("actual_velocity_avg_fps"), (int, float))
        ]
        es_values = [
            float(row["actual_es_fps"])
            for row in batches
            if isinstance(row.get("actual_es_fps"), (int, float))
        ]
        sd_values = [
            float(row["actual_sd_fps"])
            for row in batches
            if isinstance(row.get("actual_sd_fps"), (int, float))
        ]
        moa_values = [
            float(row["actual_best_moa"])
            for row in batches
            if isinstance(row.get("actual_best_moa"), (int, float))
        ]
        pressure_watch_count = sum(
            1 for row in batches if int(row.get("pressure_signs_observed") or 0) == 1
        )

        avg_velocity_fps = (
            round(sum(velocity_values) / len(velocity_values), 1)
            if velocity_values
            else None
        )
        typical_es_fps = (
            round(sum(es_values) / len(es_values), 1) if es_values else None
        )
        typical_sd_fps = (
            round(sum(sd_values) / len(sd_values), 1) if sd_values else None
        )
        best_recorded_moa = round(min(moa_values), 3) if moa_values else None

        batch_samples = len(batches)
        data_points = batch_samples
        confidence_score = min(
            95.0,
            (batch_samples * 16.0) + (len(es_values) * 6.0) + (len(sd_values) * 6.0),
        )
        if batch_samples >= 3:
            status = "learning"
        elif batch_samples >= 1:
            status = "calibrating"
        else:
            status = "insufficient_data"

        drift_flag = None
        if pressure_watch_count:
            drift_flag = "pressure_watch"
        elif typical_es_fps is not None and typical_es_fps >= 20:
            drift_flag = "ignition_watch"
        elif typical_sd_fps is not None and typical_sd_fps >= 10:
            drift_flag = "consistency_watch"

        intended_use_counts: Dict[str, int] = {}
        for row in batches:
            intended_use = str(row.get("intended_use") or "").strip()
            if intended_use:
                intended_use_counts[intended_use] = (
                    intended_use_counts.get(intended_use, 0) + 1
                )

        updates = {
            "component_type": "primers",
            "component_id": primer_id,
            "lot_number": lot_number,
            "status": status,
            "confidence_score": round(confidence_score, 1),
            "data_points": data_points,
            "batch_samples": batch_samples,
            "chrono_samples": 0,
            "temperature_samples": 0,
            "avg_velocity_fps": avg_velocity_fps,
            "velocity_offset_fps": None,
            "temp_sensitivity_fps_per_c": None,
            "typical_es_fps": typical_es_fps,
            "best_recorded_moa": best_recorded_moa,
            "pressure_watch_count": pressure_watch_count,
            "drift_flag": drift_flag,
            "quantity_remaining": lot_row.get("quantity_remaining"),
            "is_active": int(lot_row.get("is_active") or 0),
            "intended_use_counts": intended_use_counts,
            "typical_sd_fps": typical_sd_fps,
        }
        return self.upsert_component_lot_learning_profile(component_lot_id, updates)

    def compare_primer_lots(
        self, component_id: int, current_lot_id: int
    ) -> Dict[str, Any]:
        rows = self.execute_query(
            """
            SELECT id, lot_number, purchase_date
            FROM component_lots
            WHERE component_type = 'primers' AND component_id = ?
            ORDER BY purchase_date DESC, created_date DESC, id DESC
            """,
            (component_id,),
        )
        if not rows:
            return {}

        current_row = next(
            (row for row in rows if int(row.get("id") or 0) == int(current_lot_id)),
            None,
        )
        if not current_row:
            return {}

        current_profile = self.refresh_primer_lot_learning_profile(current_lot_id)
        previous_row = next(
            (row for row in rows if int(row.get("id") or 0) != int(current_lot_id)),
            None,
        )
        if not previous_row:
            return {
                "current_lot_id": current_lot_id,
                "current_lot_number": current_row.get("lot_number"),
                "status": "baseline_only",
                "severity": "info",
                "title": "Første lærte primerlot",
                "message": "Dette primerlotet har ingen tidligere lot å sammenligne mot ennå.",
                "recommended_action": "Bekreft ignition-konsistens med en kort chrono-serie før viktig bruk.",
                "current_profile": current_profile,
            }

        previous_profile = self.refresh_primer_lot_learning_profile(
            int(previous_row["id"])
        )
        avg_shift = None
        if isinstance(
            current_profile.get("avg_velocity_fps"), (int, float)
        ) and isinstance(previous_profile.get("avg_velocity_fps"), (int, float)):
            avg_shift = round(
                float(current_profile["avg_velocity_fps"])
                - float(previous_profile["avg_velocity_fps"]),
                1,
            )
        es_shift = None
        if isinstance(
            current_profile.get("typical_es_fps"), (int, float)
        ) and isinstance(previous_profile.get("typical_es_fps"), (int, float)):
            es_shift = round(
                float(current_profile["typical_es_fps"])
                - float(previous_profile["typical_es_fps"]),
                1,
            )
        sd_shift = None
        current_sd = current_profile.get("profile_data", {}).get("typical_sd_fps")
        previous_sd = previous_profile.get("profile_data", {}).get("typical_sd_fps")
        if isinstance(current_sd, (int, float)) and isinstance(
            previous_sd, (int, float)
        ):
            sd_shift = round(float(current_sd) - float(previous_sd), 1)

        severity = "ok"
        status = "stable"
        title = "Primerlot ser stabilt ut"
        recommended_action = (
            "Kort kontrollserie er vanligvis nok før du bruker tidligere data videre."
        )
        verification_plan = {
            "shots": 3,
            "focus": "Chrono 3 kontrollskudd og bekreft at ES/SD fortsatt matcher forventningene.",
        }
        notes: list[str] = []
        if avg_shift is not None:
            notes.append(f"Snittfart {avg_shift:+.1f} fps")
        if es_shift is not None:
            notes.append(f"ES {es_shift:+.1f}")
        if sd_shift is not None:
            notes.append(f"SD {sd_shift:+.1f}")

        current_flag = str(current_profile.get("drift_flag") or "").strip()
        if (
            current_flag in {"pressure_watch", "ignition_watch"}
            or (es_shift is not None and es_shift >= 6)
            or (sd_shift is not None and sd_shift >= 3)
        ):
            severity = "high"
            status = "retest_required"
            title = "Tydelig primerlotavvik"
            recommended_action = "Bekreft ignition-konsistens og trykktegn før du antar at tidligere ladning oppfører seg likt."
            verification_plan = {
                "shots": 5,
                "focus": "Chrono minst 5 kontrollskudd og følg spesielt med på ES/SD og tidlige trykktegn.",
            }
        elif (
            current_flag == "consistency_watch"
            or (es_shift is not None and es_shift > 0)
            or (sd_shift is not None and sd_shift > 0)
        ):
            severity = "watch"
            status = "watch"
            title = "Merkbart primerlotavvik"
            recommended_action = "Kjør en kort chrono-serie før du bruker lotet til finjustering eller jaktammo."
            verification_plan = {
                "shots": 3,
                "focus": "Chrono 3 kontrollskudd og se etter økt ES/SD eller treg/ujevn ignition.",
            }

        message = f"Sammenlignet med forrige lot {previous_row.get('lot_number')}: " + (
            ", ".join(notes) if notes else "for lite data for detaljert sammenligning."
        )
        return {
            "current_lot_id": current_lot_id,
            "current_lot_number": current_row.get("lot_number"),
            "previous_lot_id": previous_row.get("id"),
            "previous_lot_number": previous_row.get("lot_number"),
            "status": status,
            "severity": severity,
            "title": title,
            "message": message,
            "recommended_action": recommended_action,
            "verification_plan": verification_plan,
            "avg_velocity_shift_fps": avg_shift,
            "typical_es_shift_fps": es_shift,
            "typical_sd_shift_fps": sd_shift,
            "current_profile": current_profile,
            "previous_profile": previous_profile,
        }

    def _build_default_bullet_lot_learning_profile(
        self, bullet_lot_id: int, bullet_id: int, lot_number: str
    ) -> Dict[str, Any]:
        return {
            "bullet_lot_id": bullet_lot_id,
            "bullet_id": bullet_id,
            "lot_number": lot_number,
            "status": "insufficient_data",
            "confidence_score": 0.0,
            "confidence_label": "ingen data ennå",
            "data_points": 0,
            "qc_samples": 0,
            "batch_samples": 0,
            "avg_weight_grains": None,
            "weight_std_dev": None,
            "avg_bto_inches": None,
            "bto_std_dev": None,
            "qc_pass_rate_percent": None,
            "typical_group_moa": None,
            "best_recorded_moa": None,
            "drift_flag": None,
            "notes": "",
            "profile_data": {},
        }

    def get_bullet_lot_learning_profile(self, bullet_lot_id: int) -> Dict[str, Any]:
        rows = self.execute_query(
            "SELECT * FROM bullet_lot_learning_profiles WHERE bullet_lot_id = ?",
            (bullet_lot_id,),
        )
        if not rows:
            lot_row = self.get_by_id("bullet_lots", bullet_lot_id)
            if not lot_row:
                return {}
            default_profile = self._build_default_bullet_lot_learning_profile(
                bullet_lot_id,
                int(lot_row.get("bullet_id") or 0),
                str(lot_row.get("lot_number") or ""),
            )
            self.insert(
                "bullet_lot_learning_profiles",
                {
                    "bullet_lot_id": bullet_lot_id,
                    "bullet_id": default_profile["bullet_id"],
                    "lot_number": default_profile["lot_number"],
                    "status": default_profile["status"],
                    "confidence_score": default_profile["confidence_score"],
                    "data_points": default_profile["data_points"],
                    "qc_samples": default_profile["qc_samples"],
                    "batch_samples": default_profile["batch_samples"],
                    "notes": default_profile["notes"],
                    "profile_json": json.dumps(
                        default_profile["profile_data"], ensure_ascii=False
                    ),
                },
            )
            return default_profile

        profile = dict(rows[0])
        try:
            profile_data = json.loads(profile.get("profile_json") or "{}")
        except Exception:
            profile_data = {}
        profile["profile_data"] = profile_data if isinstance(profile_data, dict) else {}
        profile["confidence_label"] = self._confidence_label_from_score(
            profile.get("confidence_score")
        )
        return profile

    def upsert_bullet_lot_learning_profile(
        self, bullet_lot_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        current = self.get_bullet_lot_learning_profile(bullet_lot_id)
        if not current:
            return {}
        known_columns = {
            "bullet_id",
            "lot_number",
            "status",
            "confidence_score",
            "data_points",
            "qc_samples",
            "batch_samples",
            "avg_weight_grains",
            "weight_std_dev",
            "avg_bto_inches",
            "bto_std_dev",
            "qc_pass_rate_percent",
            "typical_group_moa",
            "best_recorded_moa",
            "drift_flag",
            "notes",
        }
        column_updates = {
            key: value for key, value in updates.items() if key in known_columns
        }
        profile_data = dict(current.get("profile_data") or {})
        extra_updates = {
            key: value for key, value in updates.items() if key not in known_columns
        }
        profile_data.update(extra_updates)
        column_updates["profile_json"] = json.dumps(profile_data, ensure_ascii=False)
        column_updates["updated_at"] = "CURRENT_TIMESTAMP"
        set_clause = ", ".join(
            [
                f"{key}=CURRENT_TIMESTAMP" if key == "updated_at" else f"{key}=?"
                for key in column_updates.keys()
            ]
        )
        values = tuple(
            value for key, value in column_updates.items() if key != "updated_at"
        ) + (bullet_lot_id,)
        query = (
            "UPDATE bullet_lot_learning_profiles "
            f"SET {set_clause} WHERE bullet_lot_id = ?"
        )
        if self.conn is not None and self.cursor is not None:
            self.cursor.execute(query, values)
            self.conn.commit()
        return self.get_bullet_lot_learning_profile(bullet_lot_id)

    def refresh_bullet_lot_learning_profile(self, bullet_lot_id: int) -> Dict[str, Any]:
        lot_row = self.get_by_id("bullet_lots", bullet_lot_id)
        if not lot_row:
            return {}

        qc_rows = self.execute_query(
            """
            SELECT weight_grains, length_bto_inches, passed_qc
            FROM bullet_qc_measurements
            WHERE lot_id = ?
            ORDER BY bullet_number ASC
            """,
            (bullet_lot_id,),
        )
        batch_rows = self.execute_query(
            """
            SELECT actual_moa_avg, actual_best_moa, predicted_moa,
                   runout_avg_tir_inches, qc_pass_rate_percent
            FROM loaded_ammo_batches
            WHERE bullet_lot_id = ?
            ORDER BY loaded_date DESC
            """,
            (bullet_lot_id,),
        )

        weight_values = [
            float(row["weight_grains"])
            for row in qc_rows
            if isinstance(row.get("weight_grains"), (int, float))
        ]
        bto_values = [
            float(row["length_bto_inches"])
            for row in qc_rows
            if isinstance(row.get("length_bto_inches"), (int, float))
        ]
        passed_count = sum(1 for row in qc_rows if int(row.get("passed_qc") or 0) == 1)
        qc_samples = len(qc_rows)

        avg_weight = (
            round(sum(weight_values) / len(weight_values), 4) if weight_values else None
        )
        weight_std = None
        if len(weight_values) >= 2:
            mean = sum(weight_values) / len(weight_values)
            weight_std = round(
                (
                    sum((value - mean) ** 2 for value in weight_values)
                    / len(weight_values)
                )
                ** 0.5,
                4,
            )
        avg_bto = round(sum(bto_values) / len(bto_values), 5) if bto_values else None
        bto_std = None
        if len(bto_values) >= 2:
            mean = sum(bto_values) / len(bto_values)
            bto_std = round(
                (sum((value - mean) ** 2 for value in bto_values) / len(bto_values))
                ** 0.5,
                5,
            )

        group_values = [
            float(row["actual_moa_avg"])
            for row in batch_rows
            if isinstance(row.get("actual_moa_avg"), (int, float))
        ]
        best_moa_values = [
            float(row["actual_best_moa"])
            for row in batch_rows
            if isinstance(row.get("actual_best_moa"), (int, float))
        ]
        batch_samples = len(batch_rows)
        typical_group_moa = (
            round(sum(group_values) / len(group_values), 3) if group_values else None
        )
        best_recorded_moa = round(min(best_moa_values), 3) if best_moa_values else None
        qc_pass_rate = (
            round((passed_count / qc_samples) * 100.0, 1) if qc_samples else None
        )
        data_points = qc_samples + batch_samples
        confidence_score = min(95.0, (qc_samples * 6.0) + (batch_samples * 18.0))
        if qc_samples >= 5 and batch_samples >= 1:
            status = "learning"
        elif qc_samples >= 3 or batch_samples >= 1:
            status = "calibrating"
        else:
            status = "insufficient_data"

        drift_flag = None
        if weight_std is not None and weight_std >= 0.2:
            drift_flag = "weight_watch"
        if bto_std is not None and bto_std >= 0.002:
            drift_flag = "ogive_watch"
        if typical_group_moa is not None and typical_group_moa >= 1.0:
            drift_flag = "precision_watch"

        updates = {
            "bullet_id": int(lot_row.get("bullet_id") or 0),
            "lot_number": str(lot_row.get("lot_number") or ""),
            "status": status,
            "confidence_score": round(confidence_score, 1),
            "data_points": data_points,
            "qc_samples": qc_samples,
            "batch_samples": batch_samples,
            "avg_weight_grains": avg_weight,
            "weight_std_dev": weight_std,
            "avg_bto_inches": avg_bto,
            "bto_std_dev": bto_std,
            "qc_pass_rate_percent": qc_pass_rate,
            "typical_group_moa": typical_group_moa,
            "best_recorded_moa": best_recorded_moa,
            "drift_flag": drift_flag,
            "quantity_remaining": lot_row.get("quantity_remaining"),
            "quality_rating": lot_row.get("quality_rating"),
            "qc_performed": int(lot_row.get("qc_performed") or 0),
        }
        return self.upsert_bullet_lot_learning_profile(bullet_lot_id, updates)

    def compare_bullet_lots(
        self, bullet_id: int, current_lot_id: int
    ) -> Dict[str, Any]:
        rows = self.execute_query(
            """
            SELECT id, lot_number, purchase_date
            FROM bullet_lots
            WHERE bullet_id = ?
            ORDER BY is_active DESC, purchase_date DESC, created_date DESC, id DESC
            """,
            (bullet_id,),
        )
        if not rows:
            return {}

        current_row = next(
            (row for row in rows if int(row.get("id") or 0) == int(current_lot_id)),
            None,
        )
        if not current_row:
            return {}

        current_profile = self.refresh_bullet_lot_learning_profile(current_lot_id)
        previous_row = next(
            (row for row in rows if int(row.get("id") or 0) != int(current_lot_id)),
            None,
        )
        if not previous_row:
            return {
                "current_lot_id": current_lot_id,
                "current_lot_number": current_row.get("lot_number"),
                "status": "baseline_only",
                "severity": "info",
                "title": "Første lærte kulelot",
                "message": "Dette lotet har ingen tidligere lot å sammenligne mot ennå.",
                "recommended_action": "Skyt en kort referanseserie før du bruker lotet til viktig match- eller jaktammo.",
                "current_profile": current_profile,
            }

        previous_profile = self.refresh_bullet_lot_learning_profile(
            int(previous_row["id"])
        )
        weight_std_shift = None
        if isinstance(
            current_profile.get("weight_std_dev"), (int, float)
        ) and isinstance(previous_profile.get("weight_std_dev"), (int, float)):
            weight_std_shift = round(
                float(current_profile["weight_std_dev"])
                - float(previous_profile["weight_std_dev"]),
                4,
            )
        bto_std_shift = None
        if isinstance(current_profile.get("bto_std_dev"), (int, float)) and isinstance(
            previous_profile.get("bto_std_dev"), (int, float)
        ):
            bto_std_shift = round(
                float(current_profile["bto_std_dev"])
                - float(previous_profile["bto_std_dev"]),
                5,
            )
        group_shift = None
        if isinstance(
            current_profile.get("typical_group_moa"), (int, float)
        ) and isinstance(previous_profile.get("typical_group_moa"), (int, float)):
            group_shift = round(
                float(current_profile["typical_group_moa"])
                - float(previous_profile["typical_group_moa"]),
                3,
            )

        severity = "ok"
        status = "stable"
        title = "Kulelot ser stabilt ut"
        recommended_action = (
            "Lotet ser brukbart ut. Bekreft gjerne med én kort kontrollserie."
        )
        verification_plan = {
            "shots": 3,
            "focus": "Skyt én kort kontrollserie og bekreft at gruppen matcher forventningene.",
        }
        notes: list[str] = []
        if weight_std_shift is not None:
            notes.append(f"Vekt-SD {weight_std_shift:+.4f} gr")
        if bto_std_shift is not None:
            notes.append(f'Ogive-SD {bto_std_shift:+.5f}"')
        if group_shift is not None:
            notes.append(f"Typisk gruppe {group_shift:+.3f} MOA")

        current_drift = str(current_profile.get("drift_flag") or "").strip()
        if (
            current_drift in {"ogive_watch", "precision_watch"}
            or (group_shift is not None and group_shift >= 0.25)
            or (bto_std_shift is not None and bto_std_shift >= 0.001)
        ):
            severity = "high"
            status = "retest_required"
            title = "Tydelig kulelotavvik"
            recommended_action = "Bruk lotet til verifiseringsserie før det brukes til finjustering, match eller jakt."
            verification_plan = {
                "shots": 5,
                "focus": "Skyt minst 5 kontrollskudd og følg spesielt med på gruppestørrelse og seating-følsomhet.",
            }
        elif (
            current_drift == "weight_watch"
            or (weight_std_shift is not None and weight_std_shift >= 0.05)
            or (group_shift is not None and group_shift > 0)
        ):
            severity = "watch"
            status = "watch"
            title = "Merkbart kulelotavvik"
            recommended_action = "Bekreft lotet med en kort serie før du antar at forrige node gjelder uendret."
            verification_plan = {
                "shots": 3,
                "focus": "Skyt 3 kontrollskudd og se etter gruppedrift eller urolig seating-respons.",
            }

        message = f"Sammenlignet med forrige lot {previous_row.get('lot_number')}: " + (
            ", ".join(notes) if notes else "for lite data for detaljert sammenligning."
        )
        return {
            "current_lot_id": current_lot_id,
            "current_lot_number": current_row.get("lot_number"),
            "previous_lot_id": previous_row.get("id"),
            "previous_lot_number": previous_row.get("lot_number"),
            "status": status,
            "severity": severity,
            "title": title,
            "message": message,
            "recommended_action": recommended_action,
            "verification_plan": verification_plan,
            "weight_std_shift": weight_std_shift,
            "bto_std_shift": bto_std_shift,
            "group_shift_moa": group_shift,
            "current_profile": current_profile,
            "previous_profile": previous_profile,
        }

    def add_system_weapon(
        self, name, manufacturer, action_type, serial_number, barrels
    ):
        """Legg til systemvåpen med flere løp og profiler"""
        # Lagre låsekasse
        self.cursor.execute(
            """
            INSERT INTO rifles (name, manufacturer, action_type, serial_number)
            VALUES (?, ?, ?, ?)
        """,
            (name, manufacturer, action_type, serial_number),
        )
        rifle_id = self.cursor.lastrowid
        # Lagre løp/profiler/kalibere
        for barrel in barrels:
            self.cursor.execute(
                """
                INSERT INTO barrel_profiles (name, description, category, muzzle_diameter_mm, breech_diameter_mm, taper_type, typical_length_inches, typical_calibers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    barrel.get("name"),
                    barrel.get("description"),
                    barrel.get("category"),
                    barrel.get("muzzle_diameter_mm"),
                    barrel.get("breech_diameter_mm"),
                    barrel.get("taper_type"),
                    barrel.get("typical_length_inches"),
                    barrel.get("typical_calibers"),
                ),
            )
            profile_id = self.cursor.lastrowid
            # Koble løp til rifle
            self.cursor.execute(
                """
                UPDATE rifles SET barrel_profile_id = ? WHERE id = ?
            """,
                (profile_id, rifle_id),
            )
        self.conn.commit()
        return rifle_id

    def add_test_weapon(self, name, manufacturer, caliber, barrel_profile_id, notes=""):
        """Legg til testvåpen under våpenprofilen"""
        self.cursor.execute(
            """
            INSERT INTO rifles (name, manufacturer, caliber, barrel_profile_id, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (name, manufacturer, caliber, barrel_profile_id, notes),
        )
        self.conn.commit()
        rid = self.cursor.lastrowid
        assert rid is not None
        return rid

    # Inventory & QC helpers
    def _numeric_stats(self, values: List[float]) -> Dict[str, Optional[float]]:
        if not values:
            return {
                "avg": None,
                "min": None,
                "max": None,
                "stddev": None,
            }
        avg_value = sum(values) / len(values)
        variance = (
            sum((value - avg_value) ** 2 for value in values) / len(values)
            if len(values) > 1
            else 0.0
        )
        return {
            "avg": round(avg_value, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "stddev": round(math.sqrt(variance), 4),
        }

    def create_component_lot(
        self,
        component_type: str,
        component_id: int,
        lot_number: str,
        quantity_initial: float,
        purchase_date: Optional[str] = None,
        supplier: Optional[str] = None,
        unit_cost: Optional[float] = None,
        storage_location: Optional[str] = None,
        notes: Optional[str] = None,
        source: Optional[str] = None,
        external_ref: Optional[str] = None,
        is_active: int = 1,
    ) -> int:
        payload = {
            "component_type": component_type,
            "component_id": component_id,
            "lot_number": lot_number,
            "purchase_date": purchase_date or "",
            "quantity_initial": quantity_initial,
            "quantity_remaining": quantity_initial,
            "is_active": is_active,
            "supplier": supplier,
            "unit_cost": unit_cost,
            "storage_location": storage_location,
            "notes": notes,
            "source": source,
            "external_ref": external_ref,
        }
        return self.insert("component_lots", payload)

    def create_component_measurement_session(
        self,
        component_lot_id: int,
        measured_by: Optional[str] = None,
        sample_size: Optional[int] = None,
        measured_all: int = 0,
        notes: Optional[str] = None,
    ) -> int:
        return self.insert(
            "component_measurement_sessions",
            {
                "component_lot_id": component_lot_id,
                "measured_by": measured_by,
                "sample_size": sample_size,
                "measured_all": measured_all,
                "notes": notes,
            },
        )

    def add_component_measurement_value(
        self,
        session_id: int,
        item_index: int,
        weight_grains: Optional[float] = None,
        length_mm: Optional[float] = None,
        diameter_mm: Optional[float] = None,
        thickness_mm: Optional[float] = None,
        base_to_ogive_mm: Optional[float] = None,
        case_weight_gr: Optional[float] = None,
        case_capacity_gr_h2o: Optional[float] = None,
        passed_qc: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        row_id = self.insert(
            "component_measurement_values",
            {
                "session_id": session_id,
                "item_index": item_index,
                "weight_grains": weight_grains,
                "length_mm": length_mm,
                "diameter_mm": diameter_mm,
                "thickness_mm": thickness_mm,
                "base_to_ogive_mm": base_to_ogive_mm,
                "case_weight_gr": case_weight_gr,
                "case_capacity_gr_h2o": case_capacity_gr_h2o,
                "passed_qc": passed_qc,
                "notes": notes,
            },
        )
        session_row = self.get_by_id("component_measurement_sessions", session_id)
        if session_row:
            self.refresh_component_lot_stats(int(session_row["component_lot_id"]))
        return row_id

    def get_component_measurement_sessions(
        self, component_lot_id: int
    ) -> List[Dict[str, Any]]:
        return self.execute_query(
            """
            SELECT * FROM component_measurement_sessions
            WHERE component_lot_id = ?
            ORDER BY measured_at DESC, id DESC
            """,
            (component_lot_id,),
        )

    def get_component_measurement_values(self, session_id: int) -> List[Dict[str, Any]]:
        return self.execute_query(
            """
            SELECT * FROM component_measurement_values
            WHERE session_id = ?
            ORDER BY item_index ASC, id ASC
            """,
            (session_id,),
        )

    def get_component_lot_stats(
        self, component_lot_id: int
    ) -> Optional[Dict[str, Any]]:
        rows = self.execute_query(
            "SELECT * FROM component_lot_stats WHERE component_lot_id = ?",
            (component_lot_id,),
        )
        return rows[0] if rows else None

    def refresh_component_lot_stats(self, component_lot_id: int) -> Dict[str, Any]:
        rows = self.execute_query(
            """
            SELECT mv.*
            FROM component_measurement_values mv
            JOIN component_measurement_sessions ms ON ms.id = mv.session_id
            WHERE ms.component_lot_id = ?
            ORDER BY mv.item_index ASC, mv.id ASC
            """,
            (component_lot_id,),
        )
        weight_values = [
            float(row["weight_grains"])
            for row in rows
            if isinstance(row.get("weight_grains"), (int, float))
        ]
        length_values = [
            float(row["length_mm"])
            for row in rows
            if isinstance(row.get("length_mm"), (int, float))
        ]
        diameter_values = [
            float(row["diameter_mm"])
            for row in rows
            if isinstance(row.get("diameter_mm"), (int, float))
        ]
        thickness_values = [
            float(row["thickness_mm"])
            for row in rows
            if isinstance(row.get("thickness_mm"), (int, float))
        ]
        bto_values = [
            float(row["base_to_ogive_mm"])
            for row in rows
            if isinstance(row.get("base_to_ogive_mm"), (int, float))
        ]

        weight_stats = self._numeric_stats(weight_values)
        length_stats = self._numeric_stats(length_values)
        diameter_stats = self._numeric_stats(diameter_values)
        thickness_stats = self._numeric_stats(thickness_values)
        bto_stats = self._numeric_stats(bto_values)
        payload = {
            "component_lot_id": component_lot_id,
            "sample_count": len(rows),
            "weight_avg_grains": weight_stats["avg"],
            "weight_min_grains": weight_stats["min"],
            "weight_max_grains": weight_stats["max"],
            "weight_stddev_grains": weight_stats["stddev"],
            "length_avg_mm": length_stats["avg"],
            "length_min_mm": length_stats["min"],
            "length_max_mm": length_stats["max"],
            "length_stddev_mm": length_stats["stddev"],
            "diameter_avg_mm": diameter_stats["avg"],
            "diameter_min_mm": diameter_stats["min"],
            "diameter_max_mm": diameter_stats["max"],
            "diameter_stddev_mm": diameter_stats["stddev"],
            "thickness_avg_mm": thickness_stats["avg"],
            "thickness_min_mm": thickness_stats["min"],
            "thickness_max_mm": thickness_stats["max"],
            "thickness_stddev_mm": thickness_stats["stddev"],
            "base_to_ogive_avg_mm": bto_stats["avg"],
            "base_to_ogive_min_mm": bto_stats["min"],
            "base_to_ogive_max_mm": bto_stats["max"],
            "base_to_ogive_stddev_mm": bto_stats["stddev"],
        }
        existing = self.get_component_lot_stats(component_lot_id)
        if existing:
            self.update(
                "component_lot_stats",
                payload,
                "component_lot_id = ?",
                (component_lot_id,),
            )
            if self.conn is not None and self.cursor is not None:
                self.cursor.execute(
                    "UPDATE component_lot_stats SET updated_date = CURRENT_TIMESTAMP WHERE component_lot_id = ?",
                    (component_lot_id,),
                )
                self.conn.commit()
        else:
            self.insert("component_lot_stats", payload)
        return self.get_component_lot_stats(component_lot_id) or payload

    def get_powder_simulation_profile(self, powder_id: int) -> Optional[Dict[str, Any]]:
        rows = self.execute_query(
            "SELECT * FROM powder_database WHERE powder_id = ?",
            (powder_id,),
        )
        return rows[0] if rows else None

    def create_inventory_lot(
        self,
        component_type: str,
        component_id: Optional[int],
        lot_number: str,
        quantity: int,
        purchase_date: Optional[str] = None,
        supplier: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Create an inventory lot and return its id."""
        self.cursor.execute(
            """
            INSERT INTO inventory_lots (component_type, component_id, lot_number, quantity_initial, quantity_remaining, purchase_date, supplier, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                component_type,
                component_id,
                lot_number,
                quantity,
                quantity,
                purchase_date,
                supplier,
                notes,
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_inventory_lot(self, lot_id: int) -> Optional[Dict[str, Any]]:
        return self.get_by_id("inventory_lots", lot_id)

    def update_inventory_quantity(self, lot_id: int, delta: int) -> None:
        """Adjust quantity_remaining by delta (can be negative)."""
        try:
            self.cursor.execute(
                "SELECT quantity_remaining FROM inventory_lots WHERE id = ?",
                (lot_id,),
            )
            row = self.cursor.fetchone()
            if not row:
                return
            new_qty = row[0] + delta
            if new_qty < 0:
                new_qty = 0
            self.cursor.execute(
                "UPDATE inventory_lots SET quantity_remaining = ? WHERE id = ?",
                (new_qty, lot_id),
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update inventory quantity: {e}")

    def create_measurement_session(
        self,
        lot_id: int,
        measured_by: Optional[str] = None,
        sample_size: Optional[int] = None,
        measured_all: int = 0,
        notes: Optional[str] = None,
    ) -> int:
        """Create a measurement session and return session id."""
        self.cursor.execute(
            "INSERT INTO measurement_sessions (lot_id, measured_by, sample_size, measured_all, notes) VALUES (?, ?, ?, ?, ?)",
            (lot_id, measured_by, sample_size, measured_all, notes),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def add_measurement_value(
        self,
        session_id: int,
        item_index: int,
        weight_grains: Optional[float] = None,
        length_mm: Optional[float] = None,
        neck_thickness_mm: Optional[float] = None,
        case_weight_gr: Optional[float] = None,
        passed_qc: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Add a single measurement value to a session."""
        self.cursor.execute(
            "INSERT INTO measurement_values (session_id, item_index, weight_grains, length_mm, neck_thickness_mm, case_weight_gr, passed_qc, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                item_index,
                weight_grains,
                length_mm,
                neck_thickness_mm,
                case_weight_gr,
                passed_qc,
                notes,
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_sessions_for_lot(self, lot_id: int) -> List[Dict[str, Any]]:
        return self.execute_query(
            "SELECT * FROM measurement_sessions WHERE lot_id = ? ORDER BY datetime DESC",
            (lot_id,),
        )

    def get_values_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        return self.execute_query(
            "SELECT * FROM measurement_values WHERE session_id = ? ORDER BY item_index",
            (session_id,),
        )

    def create_prep_session(
        self,
        brass_batch_id: int,
        method: Optional[str] = None,
        anneal_date: Optional[str] = None,
        trim_mm: Optional[float] = None,
        neck_bushing_size_inches: Optional[float] = None,
        neck_tension_notes: Optional[str] = None,
        measured_after: int = 0,
        notes: Optional[str] = None,
    ) -> int:
        self.cursor.execute(
            "INSERT INTO prep_sessions (brass_batch_id, method, anneal_date, trim_mm, neck_bushing_size_inches, neck_tension_notes, measured_after, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                brass_batch_id,
                method,
                anneal_date,
                trim_mm,
                neck_bushing_size_inches,
                neck_tension_notes,
                measured_after,
                notes,
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_prep_sessions_for_batch(self, brass_batch_id: int) -> List[Dict[str, Any]]:
        return self.execute_query(
            "SELECT * FROM prep_sessions WHERE brass_batch_id = ? ORDER BY created_date DESC",
            (brass_batch_id,),
        )

    def get_rifle_barrels(self, rifle_id: int) -> List[Dict[str, Any]]:
        details_rows = self.execute_query(
            "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
            (rifle_id,),
        )
        if details_rows:
            try:
                profile = json.loads(details_rows[0].get("profile_json", "{}"))
            except Exception:
                profile = {}
            barrels = profile.get("barrels") or []
            if isinstance(barrels, list):
                return [barrel for barrel in barrels if isinstance(barrel, dict)]
        rifle = self.get_by_id("rifles", rifle_id)
        if not rifle:
            return []
        fallback_name = rifle.get("name") or "Standard barrel"
        barrel_profile_id = rifle.get("barrel_profile_id")
        return [
            {
                "id": str(barrel_profile_id or "default"),
                "name": fallback_name,
                "caliber": rifle.get("caliber"),
                "is_active": True,
            }
        ]

    def get_ammo_profiles_for_rifle(
        self, rifle_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM ammo_profiles"
        params: list[Any] = []
        if rifle_id is not None:
            query += " WHERE rifle_id = ?"
            params.append(rifle_id)
        query += " ORDER BY caliber, name"
        return self.execute_query(query, tuple(params))

    def get_ammo_test_reports(
        self,
        rifle_id: Optional[int] = None,
        barrel_id: Optional[str] = None,
        ammo_profile_id: Optional[int] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        caliber: Optional[str] = None,
        ammo_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM ammo_test_reports WHERE 1=1"
        params: list[Any] = []
        if rifle_id is not None:
            query += " AND rifle_id = ?"
            params.append(rifle_id)
        if barrel_id:
            query += " AND barrel_id = ?"
            params.append(str(barrel_id))
        if ammo_profile_id is not None:
            query += " AND ammo_profile_id = ?"
            params.append(ammo_profile_id)
        if manufacturer:
            query += " AND manufacturer = ?"
            params.append(manufacturer)
        if model:
            query += " AND model = ?"
            params.append(model)
        if caliber:
            query += " AND caliber = ?"
            params.append(caliber)
        if ammo_type:
            query += " AND ammo_type = ?"
            params.append(ammo_type)
        query += " ORDER BY test_date DESC, log_time DESC, created_date DESC"
        return self.execute_query(query, tuple(params))

    def get_seating_depth_profile(
        self,
        rifle_id: int,
        bullet_id: int,
        component_lot_id: Optional[int] = None,
        barrel_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        resolved_barrel_id = str(barrel_id or "").strip()
        if component_lot_id is not None:
            if resolved_barrel_id:
                rows = self.execute_query(
                    """
                    SELECT *
                    FROM seating_depth_profiles
                    WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id = ?
                      AND COALESCE(barrel_id, '') = ?
                    ORDER BY updated_date DESC, created_date DESC
                    LIMIT 1
                    """,
                    (rifle_id, bullet_id, component_lot_id, resolved_barrel_id),
                )
                if rows:
                    return rows[0]
            rows = self.execute_query(
                """
                SELECT *
                FROM seating_depth_profiles
                WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id = ?
                  AND (barrel_id IS NULL OR barrel_id = '')
                ORDER BY updated_date DESC, created_date DESC
                LIMIT 1
                """,
                (rifle_id, bullet_id, component_lot_id),
            )
            if rows:
                return rows[0]
        rows = self.execute_query(
            """
            SELECT *
            FROM seating_depth_profiles
                        WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id IS NULL
                            AND (barrel_id IS NULL OR barrel_id = '')
            ORDER BY updated_date DESC, created_date DESC
            LIMIT 1
            """,
            (rifle_id, bullet_id),
        )
        return rows[0] if rows else None

    def get_best_seating_depth_evidence(
        self,
        rifle_id: int,
        bullet_id: int,
        component_lot_id: Optional[int] = None,
        lot_number: Optional[str] = None,
        target_temperature_c: Optional[float] = None,
        target_distance_m: Optional[float] = None,
        target_throat_erosion_mm: Optional[float] = None,
        barrel_id: Optional[str] = None,
        include_ranked: bool = False,
    ) -> Optional[Dict[str, Any]]:
        selected_lot_number = str(lot_number or "").strip()
        resolved_barrel_id = str(barrel_id or "").strip()
        if component_lot_id is not None and not selected_lot_number:
            lot_rows = self.execute_query(
                "SELECT lot_number FROM component_lots WHERE id = ? LIMIT 1",
                (component_lot_id,),
            )
            if lot_rows and lot_rows[0].get("lot_number"):
                selected_lot_number = str(lot_rows[0]["lot_number"]).strip()

        rows = self.execute_query(
            """
            SELECT
                bp.id AS batch_id,
                bp.batch_number,
                bp.batch_name,
                bp.barrel_id,
                bp.barrel_name,
                bp.charge_weight_grains,
                bp.coal_mm,
                bp.cbto_mm,
                bp.component_snapshot_json,
                bp.analysis_json AS batch_analysis_json,
                bp.created_date,
                bp.updated_date,
                bps.id AS session_id,
                bps.session_type,
                bps.session_date,
                bps.distance_m,
                bps.temperature_c,
                bps.shot_count,
                bps.group_size_moa,
                bps.analysis_json AS session_analysis_json
            FROM batch_projects bp
            LEFT JOIN batch_project_sessions bps ON bps.batch_id = bp.id
            WHERE bp.rifle_id = ? AND bp.bullet_id = ? AND bp.cbto_mm IS NOT NULL
                            AND (? = '' OR COALESCE(bp.barrel_id, '') = ? OR bp.barrel_id IS NULL OR bp.barrel_id = '')
            ORDER BY datetime(COALESCE(bps.session_date, bp.updated_date, bp.created_date)) DESC, bp.id DESC, bps.id DESC
            """,
            (rifle_id, bullet_id, resolved_barrel_id, resolved_barrel_id),
        )
        if not rows:
            return None

        def _json_dict(raw: Any) -> Dict[str, Any]:
            if isinstance(raw, dict):
                return dict(raw)
            text = str(raw or "").strip()
            if not text:
                return {}
            try:
                parsed = json.loads(text)
            except Exception:
                return {}
            return parsed if isinstance(parsed, dict) else {}

        def _numeric(value: Any) -> Optional[float]:
            try:
                if value in (None, ""):
                    return None
                return float(value)
            except Exception:
                return None

        def _read_seating_context(
            batch_analysis: Dict[str, Any], session_analysis: Dict[str, Any]
        ) -> Dict[str, Any]:
            for source in (
                session_analysis.get("seating_context"),
                batch_analysis.get("seating_context"),
            ):
                if isinstance(source, dict):
                    return dict(source)
            return {}

        batches: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            batch_id = row.get("batch_id")
            if batch_id in (None, ""):
                continue
            batch_id = int(batch_id)
            entry = batches.get(batch_id)
            if entry is None:
                snapshot = _json_dict(row.get("component_snapshot_json"))
                analysis = _json_dict(row.get("batch_analysis_json"))
                session_analysis = _json_dict(row.get("session_analysis_json"))
                bullet_snapshot = {}
                context = analysis.get("component_context")
                if isinstance(context, dict) and isinstance(
                    context.get("bullet"), dict
                ):
                    bullet_snapshot = dict(context.get("bullet") or {})
                elif isinstance(snapshot.get("bullet"), dict):
                    bullet_snapshot = dict(snapshot.get("bullet") or {})
                seating_context = _read_seating_context(analysis, session_analysis)

                batch_lot_number = str(
                    bullet_snapshot.get("lot_number")
                    or bullet_snapshot.get("selected_lot_number")
                    or ""
                ).strip()
                entry = {
                    "batch_id": batch_id,
                    "batch_number": row.get("batch_number"),
                    "batch_name": row.get("batch_name"),
                    "barrel_id": row.get("barrel_id"),
                    "barrel_name": row.get("barrel_name"),
                    "charge_weight_grains": _numeric(row.get("charge_weight_grains")),
                    "coal_mm": _numeric(row.get("coal_mm")),
                    "cbto_mm": _numeric(row.get("cbto_mm")),
                    "lot_number": batch_lot_number or None,
                    "temperature_c": _numeric(row.get("temperature_c"))
                    or _numeric(seating_context.get("temperature_c")),
                    "distance_m": _numeric(row.get("distance_m"))
                    or _numeric(seating_context.get("distance_m")),
                    "throat_erosion_mm": _numeric(
                        seating_context.get("throat_erosion_mm")
                    ),
                    "matches_selected_lot": bool(
                        selected_lot_number
                        and batch_lot_number
                        and batch_lot_number == selected_lot_number
                    ),
                    "matches_selected_barrel": bool(
                        resolved_barrel_id
                        and str(row.get("barrel_id") or "").strip()
                        == resolved_barrel_id
                    ),
                    "group_values": [],
                    "es_values": [],
                    "sd_values": [],
                    "velocity_values": [],
                    "session_ids": set(),
                    "latest_session_date": row.get("session_date")
                    or row.get("updated_date")
                    or row.get("created_date"),
                }
                batches[batch_id] = entry

            session_id = row.get("session_id")
            if session_id not in (None, ""):
                entry["session_ids"].add(int(session_id))
            session_analysis = _json_dict(row.get("session_analysis_json"))
            batch_analysis = _json_dict(row.get("batch_analysis_json"))
            seating_context = _read_seating_context(batch_analysis, session_analysis)
            stats = (
                session_analysis.get("stats")
                if isinstance(session_analysis.get("stats"), dict)
                else {}
            )

            if entry.get("temperature_c") in (None, ""):
                entry["temperature_c"] = _numeric(row.get("temperature_c")) or _numeric(
                    seating_context.get("temperature_c")
                )
            if entry.get("distance_m") in (None, ""):
                entry["distance_m"] = _numeric(row.get("distance_m")) or _numeric(
                    seating_context.get("distance_m")
                )
            if entry.get("throat_erosion_mm") in (None, ""):
                entry["throat_erosion_mm"] = _numeric(
                    seating_context.get("throat_erosion_mm")
                )

            group_moa = _numeric(row.get("group_size_moa"))
            if group_moa is None:
                group_moa = _numeric(session_analysis.get("group_size_moa"))
            if group_moa is not None:
                entry["group_values"].append(group_moa)

            es_fps = _numeric(stats.get("es"))
            if es_fps is None:
                es_fps = _numeric(session_analysis.get("es_fps"))
            if es_fps is not None:
                entry["es_values"].append(es_fps)

            sd_fps = _numeric(stats.get("sd"))
            if sd_fps is None:
                sd_fps = _numeric(session_analysis.get("sd_fps"))
            if sd_fps is not None:
                entry["sd_values"].append(sd_fps)

            avg_velocity = _numeric(stats.get("avg"))
            if avg_velocity is None:
                avg_velocity = _numeric(session_analysis.get("avg_velocity_fps"))
            if avg_velocity is not None:
                entry["velocity_values"].append(avg_velocity)

        candidates: List[Dict[str, Any]] = []
        for batch in batches.values():
            groups = list(batch.pop("group_values", []))
            es_values = list(batch.pop("es_values", []))
            sd_values = list(batch.pop("sd_values", []))
            velocity_values = list(batch.pop("velocity_values", []))
            session_ids = batch.pop("session_ids", set())

            best_group_moa = min(groups) if groups else None
            avg_group_moa = statistics.mean(groups) if groups else None
            best_es_fps = min(es_values) if es_values else None
            best_sd_fps = min(sd_values) if sd_values else None
            avg_velocity_fps = (
                statistics.mean(velocity_values) if velocity_values else None
            )
            evidence_count = len(groups) + len(es_values) + len(sd_values)
            session_count = len(session_ids) if session_ids else 0
            has_group = bool(groups)
            has_chrono = bool(es_values or sd_values or velocity_values)

            score = 0.0
            if best_group_moa is not None:
                score += max(0.0, 100.0 - float(best_group_moa) * 60.0)
            if best_es_fps is not None:
                score += max(0.0, 60.0 - float(best_es_fps) * 1.5)
            if best_sd_fps is not None:
                score += max(0.0, 40.0 - float(best_sd_fps) * 3.0)
            score += min(15.0, session_count * 3.0)
            score += min(10.0, evidence_count * 2.0)
            if batch.get("matches_selected_lot"):
                score += 12.0
            if batch.get("matches_selected_barrel"):
                score += 9.0
            if has_group and has_chrono:
                score += 8.0

            temperature_delta_c = None
            if target_temperature_c is not None and batch.get("temperature_c") not in (
                None,
                "",
            ):
                temperature_delta_c = abs(
                    float(batch.get("temperature_c")) - float(target_temperature_c)
                )
                score += max(0.0, 8.0 - temperature_delta_c * 0.6)

            distance_delta_m = None
            if target_distance_m is not None and batch.get("distance_m") not in (
                None,
                "",
            ):
                distance_delta_m = abs(
                    float(batch.get("distance_m")) - float(target_distance_m)
                )
                score += max(0.0, 8.0 - distance_delta_m / 35.0)

            throat_delta_mm = None
            if target_throat_erosion_mm is not None and batch.get(
                "throat_erosion_mm"
            ) not in (None, ""):
                throat_delta_mm = abs(
                    float(batch.get("throat_erosion_mm"))
                    - float(target_throat_erosion_mm)
                )
                score += max(0.0, 10.0 - throat_delta_mm * 45.0)

            confidence = "low"
            if has_group and has_chrono and evidence_count >= 4:
                confidence = "high"
            elif evidence_count >= 2:
                confidence = "medium"

            batch.update(
                {
                    "best_group_moa": best_group_moa,
                    "avg_group_moa": avg_group_moa,
                    "best_es_fps": best_es_fps,
                    "best_sd_fps": best_sd_fps,
                    "avg_velocity_fps": avg_velocity_fps,
                    "session_count": session_count,
                    "evidence_count": evidence_count,
                    "score": score,
                    "confidence": confidence,
                    "temperature_delta_c": temperature_delta_c,
                    "distance_delta_m": distance_delta_m,
                    "throat_delta_mm": throat_delta_mm,
                }
            )
            candidates.append(batch)

        if not candidates:
            return None
        candidates.sort(
            key=lambda item: (
                1 if item.get("matches_selected_lot") else 0,
                float(item.get("score") or 0.0),
                int(item.get("evidence_count") or 0),
                str(item.get("latest_session_date") or ""),
            ),
            reverse=True,
        )
        best = dict(candidates[0])
        if include_ranked:
            best["ranked_candidates"] = [dict(item) for item in candidates[:5]]
        return best

    def upsert_seating_depth_profile(self, payload: Dict[str, Any]) -> int:
        rifle_id = payload.get("rifle_id")
        bullet_id = payload.get("bullet_id")
        component_lot_id = payload.get("component_lot_id")
        resolved_barrel_id = str(payload.get("barrel_id") or "").strip()
        if not rifle_id or not bullet_id:
            raise ValueError("rifle_id and bullet_id are required")

        if component_lot_id is None:
            if resolved_barrel_id:
                rows = self.execute_query(
                    """
                    SELECT id
                    FROM seating_depth_profiles
                    WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id IS NULL
                      AND COALESCE(barrel_id, '') = ?
                    LIMIT 1
                    """,
                    (rifle_id, bullet_id, resolved_barrel_id),
                )
            else:
                rows = self.execute_query(
                    """
                    SELECT id
                    FROM seating_depth_profiles
                    WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id IS NULL
                      AND (barrel_id IS NULL OR barrel_id = '')
                    LIMIT 1
                    """,
                    (rifle_id, bullet_id),
                )
        else:
            if resolved_barrel_id:
                rows = self.execute_query(
                    """
                    SELECT id
                    FROM seating_depth_profiles
                    WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id = ?
                      AND COALESCE(barrel_id, '') = ?
                    LIMIT 1
                    """,
                    (rifle_id, bullet_id, component_lot_id, resolved_barrel_id),
                )
            else:
                rows = self.execute_query(
                    """
                    SELECT id
                    FROM seating_depth_profiles
                    WHERE rifle_id = ? AND bullet_id = ? AND component_lot_id = ?
                      AND (barrel_id IS NULL OR barrel_id = '')
                    LIMIT 1
                    """,
                    (rifle_id, bullet_id, component_lot_id),
                )

        clean_payload = dict(payload)
        if rows:
            row_id = rows[0].get("id")
            self.update("seating_depth_profiles", clean_payload, "id = ?", (row_id,))
            if self.conn is not None and self.cursor is not None:
                self.cursor.execute(
                    "UPDATE seating_depth_profiles SET updated_date = CURRENT_TIMESTAMP WHERE id = ?",
                    (row_id,),
                )
                self.conn.commit()
            return int(row_id)
        return self.insert("seating_depth_profiles", clean_payload)

    def list_seating_depth_profiles(
        self, rifle_id: int, bullet_id: int, barrel_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        resolved_barrel_id = str(barrel_id or "").strip()
        if resolved_barrel_id:
            return self.execute_query(
                """
                SELECT *
                FROM seating_depth_profiles
                WHERE rifle_id = ? AND bullet_id = ?
                  AND (COALESCE(barrel_id, '') = ? OR barrel_id IS NULL OR barrel_id = '')
                ORDER BY CASE WHEN COALESCE(barrel_id, '') = ? THEN 0 ELSE 1 END,
                         updated_date DESC,
                         created_date DESC
                """,
                (rifle_id, bullet_id, resolved_barrel_id, resolved_barrel_id),
            )
        return self.execute_query(
            """
            SELECT *
            FROM seating_depth_profiles
            WHERE rifle_id = ? AND bullet_id = ?
            ORDER BY updated_date DESC, created_date DESC
            """,
            (rifle_id, bullet_id),
        )


def initialize_example_data(db_session: Session):
    # Legg inn kaliberstandarder hvis ikke allerede i databasen
    if not db_session.query(CaliberStandard).first():
        for cal in get_example_caliber_standards():
            db_session.add(cal)
        db_session.commit()
        logger.info("Kaliberstandarder lagt inn.")
    # ...her kan du utvide med automatisk import av krutt- og kuledata...
