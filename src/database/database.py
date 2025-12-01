"""
Database modul for Reloading Workshop Manager
Håndterer alle database-operasjoner med SQLite
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.utils.i18n import tr
from .caliber_standard_data import get_example_caliber_standards
from .caliber_standard import CaliberStandard
from src.logging_config import configure_logging, get_logger

# Configure logging for database module
configure_logging()
logger = get_logger(__name__)
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey

# SQLAlchemy ORM base
Base = declarative_base()

# ORM-modell for PowderData
class PowderData(Base):
    __tablename__ = 'powder_data'
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
class BulletData(Base):
    __tablename__ = 'bullet_data'
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
"""
Database modul for Reloading Workshop Manager
Håndterer alle database-operasjoner med SQLite
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.utils.i18n import tr
from .caliber_standard_data import get_example_caliber_standards
from .caliber_standard import CaliberStandard
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey

# SQLAlchemy ORM base
Base = declarative_base()

class CaseProfile(Base):
    __tablename__ = 'case_profile'
    id = Column(Integer, primary_key=True)
    caliber = Column(String)
    manufacturer = Column(String)
    nominal_length = Column(Float)
    nominal_weight = Column(Float)
    nominal_volume = Column(Float)
    notes = Column(String)
    # ...eventuelt flere felter...

class CaseLotMeasurement(Base):
    __tablename__ = 'case_lot_measurement'
    id = Column(Integer, primary_key=True)
    case_profile_id = Column(Integer, ForeignKey('case_profile.id'))
    lot_number = Column(String)
    avg_length = Column(Float)
    avg_weight = Column(Float)
    avg_volume = Column(Float)
    count = Column(Integer)
    notes = Column(String)
    case_profile = relationship('CaseProfile')
    # ...eventuelt flere felter...

class Database:
    """Hovedklasse for database-operasjoner"""
    
    def __init__(self, db_path: str = "data/reloading.db", language: str = "no"):
        """Initialiserer database-tilkobling"""
        self.db_path = db_path
        self.language = language
        
        # Sørg for at data-mappen eksisterer
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Oppretter tilkobling til database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Returnerer rader som dictionaries
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        """Oppretter alle nødvendige tabeller"""
        
        # Rifles tabell - KOMPLETT MED HARMONISK DATA
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rifles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                
                -- Grunnleggende info
                manufacturer TEXT,
                model TEXT,
                caliber TEXT NOT NULL,
                action_type TEXT,  -- 'bolt', 'semi-auto', 'lever', 'single-shot'
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
        """)
        
        # Optikk tabell
        self.cursor.execute("""
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
        """)
        
        # Kalibere tabell (for GRT import)
        self.cursor.execute("""
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
        """)
        
        # Komponenter - Krutt
        self.cursor.execute("""
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
        """)
        
        # Barrel Profiles - Predefinerte løpsprofiler med mål for harmonisk beregning
        self.cursor.execute("""
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
        """)
        
        # Komponenter - Kuler
        self.cursor.execute("""
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
                bullet_type TEXT,
                quantity INTEGER DEFAULT 0,
                cost_per_unit REAL,
                notes TEXT,
                description TEXT
            )
        """)
        
        # Komponenter - Tennhetter
        self.cursor.execute("""
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
        """)
        
        # Komponenter - Hylser (Brass/Case Management)
        self.cursor.execute("""
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
        """)
        
        # Case Measurements (detaljert måling per hylse eller batch)
        self.cursor.execute("""
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
        """)
        
        # Case Firing Log (logg hver gang et batch skyttes)
        self.cursor.execute("""
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
        """)
        
        # Rifle Bullet Jump Measurements - COAL/CBTO jam målinger per rifle+bullet
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS rifle_bullet_jump_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rifle_id INTEGER NOT NULL,
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
        """)
        
        # Case Annealing Log
        self.cursor.execute("""
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
        """)
        
        # Case Prep Log (trimming, uniforming, etc.)
        self.cursor.execute("""
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
        """)
        
        # Rifle Maintenance Log - Skuddteller og vedlikehold
        self.cursor.execute("""
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
        """)
        
        # Case Wear Warning System - Når skal hylser måles
        self.cursor.execute("""
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
        """)
        
        # Ammunisjonsprofiler
        self.cursor.execute("""
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
                bullet_runout_tir REAL,  -- NY: Total Indicated Runout (TIR) på kule
                notes TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (bullet_id) REFERENCES bullets (id),
                FOREIGN KEY (powder_id) REFERENCES powder (id),
                FOREIGN KEY (primer_id) REFERENCES primers (id),
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)
        
        # Ladder Tests
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ladder_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
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
                FOREIGN KEY (rifle_id) REFERENCES rifles (id)
            )
        """)
        
        # Test Resultater
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ladder_test_id INTEGER,
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
                FOREIGN KEY (ladder_test_id) REFERENCES ladder_tests (id)
            )
        """)
        
        # Load Development Workflows
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS load_development_workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rifle_id INTEGER,
                bullet_id INTEGER,
                powder_id INTEGER,
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
        """)
        
        # Ladeøkter (logg)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS loading_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
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
        """)
        
        # Temperature Tests
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS temperature_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ammo_profile_id INTEGER,
                rifle_id INTEGER,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id),
                FOREIGN KEY (rifle_id) REFERENCES rifles (id)
            )
        """)
        
        # Temperature Test Data
        self.cursor.execute("""
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
        """)
        
        # Component Lots
        self.cursor.execute("""
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
        """)
        
        # QC Batches
        self.cursor.execute("""
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
        """)
        
        # QC Measurements
        self.cursor.execute("""
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
        """)
        
        # Skyte-økter
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shooting_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
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
                FOREIGN KEY (rifle_id) REFERENCES rifles (id),
                FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles (id)
            )
        """)
        
        # Settedybde-tester (Harmonic Wizard)
        self.cursor.execute("""
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
        """)
        
        # Settedybde-resultater
        self.cursor.execute("""
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
        """)
        
        # GRT (Gordon Reloading Tool) integrasjon
        self.cursor.execute("""
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
        """)
        
        # Trykkindikasjoner (Pressure Signs)
        self.cursor.execute("""
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
        """)
        
        # Environmental Data (Manuell værdata)
        self.cursor.execute("""
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
        """)
        
        # Cold Bore Shots (Første skudd fra kald rifle)
        self.cursor.execute("""
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
        """)
        
        # Barrel Log (Løpstilstand og skudd-telling)
        self.cursor.execute("""
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
        """)
        
        # Rifle Accuracy Tests - Systematisk testing per rifle over tid
        self.cursor.execute("""
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
        """)
        
        # Rifle Accuracy Test Individual Shots - Detaljerte skudddata
        self.cursor.execute("""
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
        """)
        
        # Load Data - Manufacturer published load data (Vihtavuori, Hodgdon, Lapua, Hornady, etc)
        self.cursor.execute("""
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
        """)
        
        # ========================================================================
        # ADVANCED BATCH MANAGEMENT SYSTEM - Professional Load Development
        # ========================================================================
        
        # Bullet Lots - Track bullet purchases with lot numbers and QC data
        self.cursor.execute("""
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
        """)
        
        # Bullet QC Measurements - Individual bullet measurements from QC sample
        self.cursor.execute("""
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
        """)
        
        # Brass Batches - Subdivide large brass purchases into manageable batches
        self.cursor.execute("""
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
        """)
        
        # Brass Lifecycle Log - Track each brass batch through loading cycles
        self.cursor.execute("""
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
        """)
        
        # Die Settings - Document die setup per rifle + brass combination
        self.cursor.execute("""
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
        """)
        
        # Annealing Log - Professional annealing tracking
        self.cursor.execute("""
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
        """)
        
        # Loaded Ammo Batches - THE CORE OF THE SYSTEM
        self.cursor.execute("""
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
        """)
        
        # Per-Round QC Measurements - Individual round quality control
        self.cursor.execute("""
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
        """)
        
        # Sizing Recommendations - AI-calculated sizing guidance
        self.cursor.execute("""
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
        """)
        
        # Powder Database - Extended powder info for pressure calculations
        self.cursor.execute("""
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
        """)
        
        # PowderData - Utvidet kruttinformasjon for trykkberegninger
        self.cursor.execute("""
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
        """)
        
        # BulletData - Utvidet kuleinformasjon for presisjonsberegninger
        self.cursor.execute("""
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
        """)
        
        self.conn.commit()
    
    def close(self):
        """Lukker database-tilkobling"""
        if self.conn:
            self.conn.close()
    
    # CRUD operasjoner
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(tr("database_error", self.language) + f": {str(e)}")
            return []
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        try:
            keys = ', '.join(data.keys())
            question_marks = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO {table} ({keys}) VALUES ({question_marks})"
            self.cursor.execute(query, values)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(tr("database_insert_error", self.language) + f": {str(e)}")
            return -1
    
    def update(self, table: str, data: Dict[str, Any], condition: str, params: tuple = ()):
        try:
            set_clause = ', '.join([f"{k}=?" for k in data.keys()])
            values = tuple(data.values()) + params
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
            self.cursor.execute(query, values)
            self.conn.commit()
        except Exception as e:
            logger.error(tr("database_update_error", self.language) + f": {str(e)}")
    
    def delete(self, table: str, condition: str, params: tuple = ()):
        try:
            query = f"DELETE FROM {table} WHERE {condition}"
            self.cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            logger.error(tr("database_delete_error", self.language) + f": {str(e)}")
    
    def get_all(self, table: str, order_by: str = "id") -> List[Dict]:
        """Henter alle rader fra tabell"""
        query = f"SELECT * FROM {table} ORDER BY {order_by}"
        return self.execute_query(query)
    
    def get_by_id(self, table: str, id: int) -> Optional[Dict]:
        """Henter en rad basert på ID"""
        query = f"SELECT * FROM {table} WHERE id = ?"
        results = self.execute_query(query, (id,))
        return results[0] if results else None
    
    def add_system_weapon(self, name, manufacturer, action_type, serial_number, barrels):
        """Legg til systemvåpen med flere løp og profiler"""
        # Lagre låsekasse
        self.cursor.execute("""
            INSERT INTO rifles (name, manufacturer, action_type, serial_number)
            VALUES (?, ?, ?, ?)
        """, (name, manufacturer, action_type, serial_number))
        rifle_id = self.cursor.lastrowid
        # Lagre løp/profiler/kalibere
        for barrel in barrels:
            self.cursor.execute("""
                INSERT INTO barrel_profiles (name, description, category, muzzle_diameter_mm, breech_diameter_mm, taper_type, typical_length_inches, typical_calibers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                barrel.get('name'),
                barrel.get('description'),
                barrel.get('category'),
                barrel.get('muzzle_diameter_mm'),
                barrel.get('breech_diameter_mm'),
                barrel.get('taper_type'),
                barrel.get('typical_length_inches'),
                barrel.get('typical_calibers')
            ))
            profile_id = self.cursor.lastrowid
            # Koble løp til rifle
            self.cursor.execute("""
                UPDATE rifles SET barrel_profile_id = ? WHERE id = ?
            """, (profile_id, rifle_id))
        self.conn.commit()
        return rifle_id
    def add_test_weapon(self, name, manufacturer, caliber, barrel_profile_id, notes=""):
        """Legg til testvåpen under våpenprofilen"""
        self.cursor.execute("""
            INSERT INTO rifles (name, manufacturer, caliber, barrel_profile_id, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (name, manufacturer, caliber, barrel_profile_id, notes))
        self.conn.commit()
        return self.cursor.lastrowid


# Singleton instance
_db_instance = None

def get_database() -> Database:
    """Returnerer singleton database-instans"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

def initialize_example_data(db_session: Session):
    # Legg inn kaliberstandarder hvis ikke allerede i databasen
    if not db_session.query(CaliberStandard).first():
        for cal in get_example_caliber_standards():
            db_session.add(cal)
        db_session.commit()
        logger.info("Kaliberstandarder lagt inn.")
    # ...her kan du utvide med automatisk import av krutt- og kuledata...
