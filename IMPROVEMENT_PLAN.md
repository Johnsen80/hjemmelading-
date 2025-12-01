# 🚀 FORBEDRINGSPLAN FOR HJEMMELADING MANAGER

Basert på den omfattende dataanalysen, her er konkrete forbedringer prioritert etter verdi og kompleksitet:

---

## 🔥 PRIORITET 1: DATABASE SCHEMA OPPDATERINGER (Kritisk)

### **Problem:**
Rifle Profile Editor lagrer ikke data til database ennå. Chamber measurements, muzzle devices, og bullet profiles eksisterer kun i dialog-minnet.

### **Løsning:**
Utvid `database.py` med nye tabeller og kolonner:

```python
# src/database/database.py - Legg til i _create_tables()

# 1. Utvid rifles table med harmonics data
self.cursor.execute("""
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS barrel_profile TEXT;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS barrel_material TEXT;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS muzzle_diameter_mm REAL;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS breech_diameter_mm REAL;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS barrel_weight_g INTEGER;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS free_float BOOLEAN DEFAULT 1;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS bedding_type TEXT;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS stock_material TEXT;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS round_count INTEGER DEFAULT 0;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS barrel_condition TEXT;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS throat_erosion_mm REAL DEFAULT 0.0;
    ALTER TABLE rifles ADD COLUMN IF NOT EXISTS user_mode TEXT DEFAULT 'beginner';
""")

# 2. Ny tabell: rifle_muzzle_devices
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS rifle_muzzle_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rifle_id INTEGER NOT NULL,
        device_type TEXT NOT NULL,
        manufacturer TEXT,
        model TEXT,
        length_mm REAL,
        weight_g INTEGER,
        diameter_mm REAL,
        thread_pitch TEXT,
        poi_shift_horizontal_cm REAL DEFAULT 0.0,
        poi_shift_vertical_cm REAL DEFAULT 0.0,
        notes TEXT,
        date_installed TEXT,
        FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE
    )
""")

# 3. Ny tabell: rifle_chamber_specs
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS rifle_chamber_specs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rifle_id INTEGER NOT NULL UNIQUE,
        chamber_spec TEXT DEFAULT 'SAAMI Standard',
        headspace_mm REAL,
        fired_base_dia_mm REAL,
        fired_shoulder_dia_mm REAL,
        fired_length_mm REAL,
        sized_base_dia_mm REAL,
        sized_shoulder_dia_mm REAL,
        shoulder_bump_mm REAL,
        clearance_base_microns REAL,
        clearance_shoulder_microns REAL,
        measured_date TEXT,
        notes TEXT,
        FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE
    )
""")

# 4. Ny tabell: rifle_bullet_profiles (freebore per bullet type)
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS rifle_bullet_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rifle_id INTEGER NOT NULL,
        bullet_id INTEGER,
        bullet_name TEXT NOT NULL,
        bullet_weight_gr REAL,
        jam_length_cbto_mm REAL NOT NULL,
        optimal_jump_mm REAL,
        mag_max_coal_mm REAL,
        measured_date TEXT,
        notes TEXT,
        FOREIGN KEY (rifle_id) REFERENCES rifles(id) ON DELETE CASCADE,
        FOREIGN KEY (bullet_id) REFERENCES bullets(id)
    )
""")

# 5. Ny tabell: brass_lot_tracking (case lifecycle)
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS brass_lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_name TEXT NOT NULL UNIQUE,
        manufacturer TEXT NOT NULL,
        caliber TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        purchase_date TEXT,
        case_capacity_gr_h2o REAL,
        weight_gr REAL,
        wall_thickness TEXT,
        times_fired INTEGER DEFAULT 0,
        last_annealed_date TEXT,
        last_trimmed_date TEXT,
        retired_quantity INTEGER DEFAULT 0,
        notes TEXT
    )
""")

# 6. Ny tabell: brass_measurements (per-case tracking)
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS brass_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brass_lot_id INTEGER NOT NULL,
        case_number INTEGER,
        case_length_mm REAL,
        neck_diameter_mm REAL,
        base_diameter_mm REAL,
        shoulder_diameter_mm REAL,
        weight_gr REAL,
        neck_thickness_mm REAL,
        measurement_date TEXT,
        notes TEXT,
        FOREIGN KEY (brass_lot_id) REFERENCES brass_lots(id) ON DELETE CASCADE
    )
""")

# 7. Ny tabell: chronograph_sessions (velocity tracking med shot strings)
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS chronograph_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_name TEXT,
        rifle_id INTEGER,
        ammo_profile_id INTEGER,
        distance_m REAL DEFAULT 15.0,
        temperature_f REAL,
        humidity_percent REAL,
        altitude_ft REAL,
        session_date TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (rifle_id) REFERENCES rifles(id),
        FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id)
    )
""")

self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS chronograph_shots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        shot_number INTEGER NOT NULL,
        velocity_fps REAL NOT NULL,
        timestamp TEXT,
        FOREIGN KEY (session_id) REFERENCES chronograph_sessions(id) ON DELETE CASCADE
    )
""")

# 8. Ny tabell: pressure_estimation (QuickLOAD-style estimates)
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS pressure_estimations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ammo_profile_id INTEGER NOT NULL,
        rifle_id INTEGER NOT NULL,
        method TEXT NOT NULL,  -- 'quickload', 'velocity_correlation', 'case_head_expansion'
        estimated_pressure_psi INTEGER,
        confidence_level TEXT,  -- 'high', 'medium', 'low'
        case_capacity_used_gr_h2o REAL,
        load_density_percent REAL,
        velocity_measured_fps REAL,
        case_head_expansion_inch REAL,
        calculation_date TEXT,
        notes TEXT,
        FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id),
        FOREIGN KEY (rifle_id) REFERENCES rifles(id)
    )
""")

# 9. Ny tabell: true_bc_measurements (True BC från egen rifle)
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS true_bc_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ammo_profile_id INTEGER NOT NULL,
        rifle_id INTEGER NOT NULL,
        method TEXT NOT NULL,  -- 'velocity_loss', 'drop_measurement', 'tof'
        book_bc_g1 REAL,
        book_bc_g7 REAL,
        true_bc_g1 REAL,
        true_bc_g7 REAL,
        muzzle_velocity_fps REAL,
        distance_m REAL,
        velocity_at_distance_fps REAL,
        drop_measured_cm REAL,
        tof_seconds REAL,
        temperature_f REAL,
        altitude_ft REAL,
        measurement_date TEXT,
        notes TEXT,
        FOREIGN KEY (ammo_profile_id) REFERENCES ammo_profiles(id),
        FOREIGN KEY (rifle_id) REFERENCES rifles(id)
    )
""")
```

### **Implementasjon i RifleProfileEditor:**
```python
# src/modules/rifle_profile_editor.py - save_profile() method

def save_profile(self):
    """Save complete rifle profile"""
    if not self.name.text():
        QMessageBox.warning(self, "Mangler navn", "Rifle må ha et navn!")
        return
    
    try:
        # 1. Save basic rifle data to rifles table
        if self.rifle_id:
            # Update existing
            self.db.execute_query("""
                UPDATE rifles SET 
                    name = ?, manufacturer = ?, caliber = ?, action_type = ?,
                    serial_number = ?, barrel_length = ?, twist_rate = ?,
                    barrel_profile = ?, barrel_material = ?, barrel_weight_g = ?,
                    free_float = ?, bedding_type = ?, stock_material = ?,
                    round_count = ?, barrel_condition = ?, notes = ?, user_mode = ?
                WHERE id = ?
            """, (..., self.rifle_id))
        else:
            # Insert new
            self.rifle_id = self.db.execute_query("""
                INSERT INTO rifles (...) VALUES (...)
            """, (...))
        
        # 2. Save muzzle device (if expert mode)
        if self.user_mode == "expert" and self.has_device.isChecked():
            # Check if device exists
            existing = self.db.execute_query(
                "SELECT id FROM rifle_muzzle_devices WHERE rifle_id = ?",
                (self.rifle_id,)
            )
            
            if existing:
                # Update
                self.db.execute_query("""
                    UPDATE rifle_muzzle_devices SET
                        device_type = ?, length_mm = ?, weight_g = ?, ...
                    WHERE rifle_id = ?
                """, (...))
            else:
                # Insert
                self.db.execute_query("""
                    INSERT INTO rifle_muzzle_devices (rifle_id, ...) VALUES (?, ...)
                """, (...))
        
        # 3. Save chamber specs (if measurements entered)
        if self.user_mode == "expert" and self.fired_base.value() > 0:
            # Calculate clearances
            clearance_base = (self.fired_base.value() - self.sized_base.value()) * 1000  # μm
            clearance_shoulder = (self.fired_shoulder.value() - self.sized_shoulder.value()) * 1000
            
            self.db.execute_query("""
                INSERT OR REPLACE INTO rifle_chamber_specs 
                (rifle_id, chamber_spec, fired_base_dia_mm, ..., clearance_base_microns, ...)
                VALUES (?, ?, ?, ..., ?, ...)
            """, (...))
        
        # 4. Save bullet profiles (from table)
        if self.user_mode == "expert":
            # Delete old profiles
            self.db.execute_query(
                "DELETE FROM rifle_bullet_profiles WHERE rifle_id = ?",
                (self.rifle_id,)
            )
            
            # Insert new profiles
            for row in range(self.bullet_profiles_table.rowCount()):
                bullet_name = self.bullet_profiles_table.item(row, 0).text()
                # ... extract other data
                self.db.execute_query("""
                    INSERT INTO rifle_bullet_profiles (rifle_id, bullet_name, ...)
                    VALUES (?, ?, ...)
                """, (...))
        
        self.db.commit()
        
        # Emit signal
        rifle_data = {...}  # Full data dict
        self.rifle_saved.emit(rifle_data)
        
        QMessageBox.information(self, "✅ Lagret", 
            f"Rifle profil '{self.name.text()}' er lagret!")
        self.accept()
        
    except Exception as e:
        QMessageBox.critical(self, "Feil", f"Kunne ikke lagre: {str(e)}")
```

### **Estimert tid:** 4-6 timer

---

## 🔥 PRIORITET 2: QUICKLOAD-STYLE PRESSURE ESTIMATOR

### **Problem:**
Ingen måte å estimere trykk fra velocity data. Brukere vet ikke om de er nær SAAMI max.

### **Løsning:**
Implementer pressure estimation engine basert på velocity correlation og case measurements.

```python
# src/utils/pressure_estimator.py (NYE FILEN)

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PressureEstimate:
    """Pressure estimation result"""
    estimated_psi: int
    confidence: str  # 'high', 'medium', 'low'
    method: str
    saami_max_psi: int
    percentage_of_max: float
    safety_rating: str  # 'safe', 'caution', 'danger'
    warnings: list

class PressureEstimator:
    """
    Estimates chamber pressure from various methods
    Based on empirical data and physics
    """
    
    # SAAMI max pressures (PSI)
    SAAMI_MAX = {
        '6.5 Creedmoor': 62000,
        '.308 Winchester': 62000,
        '.223 Remington': 55000,
        '.30-06 Springfield': 60000,
        '6mm Creedmoor': 62000,
        '.300 Win Mag': 64000,
        '6.5x55 Swedish': 55114,  # CIP
    }
    
    def __init__(self):
        pass
    
    def estimate_from_velocity(
        self,
        caliber: str,
        bullet_weight_gr: float,
        powder_type: str,
        charge_weight_gr: float,
        measured_velocity_fps: float,
        barrel_length_inch: float,
        book_data: Dict
    ) -> PressureEstimate:
        """
        Estimate pressure from velocity using reloading manual data
        
        book_data should contain:
        {
            'min_charge': 38.0,
            'min_velocity': 2488,
            'min_pressure': 47500,
            'max_charge': 41.5,
            'max_velocity': 2726,
            'max_pressure': 62000
        }
        """
        warnings = []
        
        # Linear interpolation between min and max
        charge_range = book_data['max_charge'] - book_data['min_charge']
        charge_position = (charge_weight_gr - book_data['min_charge']) / charge_range
        
        if charge_position < 0:
            warnings.append("Below minimum book load!")
            charge_position = 0
        elif charge_position > 1:
            warnings.append("ABOVE MAXIMUM BOOK LOAD - DANGEROUS!")
            charge_position = 1
        
        # Velocity interpolation
        velocity_range = book_data['max_velocity'] - book_data['min_velocity']
        velocity_position = (measured_velocity_fps - book_data['min_velocity']) / velocity_range
        
        # Pressure is NON-LINEAR with velocity
        # Rule: +1% velocity ≈ +15% pressure (approximately)
        pressure_range = book_data['max_pressure'] - book_data['min_pressure']
        
        # Use velocity position with non-linear curve
        # Pressure increases exponentially
        pressure_curve_factor = velocity_position ** 1.3  # Non-linear
        estimated_psi = int(book_data['min_pressure'] + (pressure_range * pressure_curve_factor))
        
        # Sanity check: if velocity > book max, extrapolate dangerously
        if measured_velocity_fps > book_data['max_velocity']:
            overspeed_percent = (measured_velocity_fps - book_data['max_velocity']) / book_data['max_velocity']
            pressure_increase_factor = 1 + (overspeed_percent * 15)  # 15x multiplier
            estimated_psi = int(book_data['max_pressure'] * pressure_increase_factor)
            warnings.append(f"Velocity {overspeed_percent*100:.1f}% over book max - DANGER!")
        
        # Determine confidence
        if 'min_pressure' in book_data and 'max_pressure' in book_data:
            confidence = 'medium'
        else:
            confidence = 'low'
            warnings.append("No book pressure data - estimate is rough")
        
        # Safety rating
        saami_max = self.SAAMI_MAX.get(caliber, 62000)
        percentage = (estimated_psi / saami_max) * 100
        
        if percentage < 85:
            safety = 'safe'
        elif percentage < 95:
            safety = 'caution'
            warnings.append("Approaching maximum pressure - use caution")
        else:
            safety = 'danger'
            warnings.append("AT OR ABOVE MAXIMUM PRESSURE - STOP!")
        
        return PressureEstimate(
            estimated_psi=estimated_psi,
            confidence=confidence,
            method='velocity_correlation',
            saami_max_psi=saami_max,
            percentage_of_max=percentage,
            safety_rating=safety,
            warnings=warnings
        )
    
    def estimate_from_case_head_expansion(
        self,
        case_head_before_mm: float,
        case_head_after_mm: float,
        caliber: str
    ) -> PressureEstimate:
        """
        Estimate pressure from case head expansion
        Most reliable method without Pressure Trace!
        
        Brass yields at ~40,000 PSI
        Expansion is proportional to pressure above yield
        """
        expansion_mm = case_head_after_mm - case_head_before_mm
        expansion_inch = expansion_mm / 25.4
        
        warnings = []
        
        # Empirical correlation (brass yield stress)
        # 0.0001" = ~55k PSI
        # 0.0002" = ~60k PSI
        # 0.0003" = ~63k PSI
        # 0.0005" = ~68k PSI (dangerous!)
        
        if expansion_inch < 0.00005:
            estimated_psi = 50000
            confidence = 'low'
            warnings.append("Very low expansion - measurement may be inaccurate")
        elif expansion_inch < 0.00015:
            estimated_psi = 55000
            confidence = 'high'
        elif expansion_inch < 0.00025:
            estimated_psi = 60000
            confidence = 'high'
        elif expansion_inch < 0.00035:
            estimated_psi = 63000
            confidence = 'high'
            warnings.append("High pressure detected")
        else:
            estimated_psi = int(65000 + (expansion_inch - 0.0003) * 100000)
            confidence = 'high'
            warnings.append("EXCESSIVE CASE HEAD EXPANSION - OVERPRESSURE!")
        
        saami_max = self.SAAMI_MAX.get(caliber, 62000)
        percentage = (estimated_psi / saami_max) * 100
        
        if percentage < 90:
            safety = 'safe'
        elif percentage < 100:
            safety = 'caution'
        else:
            safety = 'danger'
        
        return PressureEstimate(
            estimated_psi=estimated_psi,
            confidence=confidence,
            method='case_head_expansion',
            saami_max_psi=saami_max,
            percentage_of_max=percentage,
            safety_rating=safety,
            warnings=warnings
        )
    
    def estimate_from_chamber_clearance(
        self,
        clearance_microns: float,
        velocity_sd_fps: float,
        caliber: str
    ) -> Dict:
        """
        Estimate pressure consistency from chamber clearance
        Tight chamber = consistent pressure = low ES/SD
        """
        # This doesn't estimate absolute pressure, but predicts ES/SD
        
        if clearance_microns < 25:
            predicted_sd = 5  # Excellent
            quality = "Match grade"
        elif clearance_microns < 50:
            predicted_sd = 8  # Very good
            quality = "Tight chamber"
        elif clearance_microns < 100:
            predicted_sd = 12  # Good
            quality = "SAAMI spec"
        else:
            predicted_sd = 18  # Poor
            quality = "Loose chamber"
        
        return {
            'clearance_microns': clearance_microns,
            'predicted_sd_fps': predicted_sd,
            'actual_sd_fps': velocity_sd_fps,
            'chamber_quality': quality,
            'recommendation': 'Consider custom reamer' if clearance_microns > 100 else 'Chamber OK'
        }
```

### **GUI Integration:**
```python
# src/modules/pressure_analyzer.py (NY MODUL)

from PyQt6.QtWidgets import *
from src.utils.pressure_estimator import PressureEstimator, PressureEstimate

class PressureAnalyzer(QWidget):
    """Widget for pressure estimation"""
    
    def __init__(self):
        super().__init__()
        self.estimator = PressureEstimator()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Method selection
        method_group = QGroupBox("📊 Velg Estimeringsmetode")
        method_layout = QVBoxLayout()
        
        self.method_velocity = QRadioButton("Fra Hastighet (chronograph + manual data)")
        self.method_case = QRadioButton("Fra Case Head Expansion (mest nøyaktig!)")
        self.method_chamber = QRadioButton("Fra Chamber Clearance (ES/SD prediksjon)")
        
        self.method_velocity.setChecked(True)
        
        method_layout.addWidget(self.method_velocity)
        method_layout.addWidget(self.method_case)
        method_layout.addWidget(self.method_chamber)
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Input tabs (different inputs for each method)
        self.input_tabs = QTabWidget()
        self.input_tabs.addTab(self.create_velocity_tab(), "Velocity Method")
        self.input_tabs.addTab(self.create_case_head_tab(), "Case Head Expansion")
        self.input_tabs.addTab(self.create_chamber_tab(), "Chamber Clearance")
        layout.addWidget(self.input_tabs)
        
        # Calculate button
        calc_btn = QPushButton("🔬 Beregn Trykk")
        calc_btn.clicked.connect(self.calculate_pressure)
        layout.addWidget(calc_btn)
        
        # Results display
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMinimumHeight(300)
        layout.addWidget(self.results)
        
        self.setLayout(layout)
    
    def calculate_pressure(self):
        """Calculate pressure estimate"""
        if self.method_velocity.isChecked():
            result = self.calculate_from_velocity()
        elif self.method_case.isChecked():
            result = self.calculate_from_case_head()
        else:
            result = self.calculate_from_chamber()
        
        self.display_results(result)
    
    def display_results(self, result: PressureEstimate):
        """Display estimation results with color coding"""
        html = "<h2>🔬 Trykk Estimering</h2>"
        
        # Pressure gauge visual
        percentage = result.percentage_of_max
        if result.safety_rating == 'safe':
            color = '#27ae60'
            emoji = '✅'
        elif result.safety_rating == 'caution':
            color = '#f39c12'
            emoji = '⚠️'
        else:
            color = '#e74c3c'
            emoji = '🔴'
        
        html += f"<div style='background-color: {color}; color: white; padding: 20px; border-radius: 10px;'>"
        html += f"<h1>{emoji} {result.estimated_psi:,} PSI</h1>"
        html += f"<p><b>{percentage:.1f}% av SAAMI max ({result.saami_max_psi:,} PSI)</b></p>"
        html += f"<p>Metode: {result.method}</p>"
        html += f"<p>Confidence: {result.confidence.upper()}</p>"
        html += "</div>"
        
        # Warnings
        if result.warnings:
            html += "<h3>⚠️ Advarsler:</h3><ul>"
            for warning in result.warnings:
                html += f"<li><b>{warning}</b></li>"
            html += "</ul>"
        
        # Safety recommendations
        html += "<h3>📋 Anbefalinger:</h3>"
        if result.safety_rating == 'safe':
            html += "<p style='color: green;'>✅ Trygg ladning. Fortsett testing.</p>"
        elif result.safety_rating == 'caution':
            html += "<p style='color: orange;'>⚠️ Nærmer seg max. Sjekk pressure signs!</p>"
        else:
            html += "<p style='color: red;'><b>🔴 STOPP! Reduser ladningen umiddelbart!</b></p>"
        
        self.results.setHtml(html)
```

### **Estimert tid:** 6-8 timer

---

## 🟡 PRIORITET 3: TRUE BC CALCULATOR

### **Problem:**
Book BC er sjelden nøyaktig for DIN rifle. Kan være 3-8% feil, som gir store feil @ 600m+.

### **Løsning:**
True BC calculator basert på velocity loss eller drop measurements.

```python
# src/utils/true_bc_calculator.py (NY FIL)

class TrueBCCalculator:
    """Calculate TRUE BC from your rifle's actual data"""
    
    def calculate_from_velocity_loss(
        self,
        muzzle_velocity_fps: float,
        velocity_at_distance_fps: float,
        distance_m: float,
        book_bc_g7: float,
        bullet_weight_gr: float,
        atmospheric_conditions: Dict
    ) -> Dict:
        """
        Calculate true BC from chronograph data at two distances
        Requires: Chrono @ muzzle + Chrono @ distance (e.g. 100m)
        """
        
        # Use ballistic solver to find BC that matches velocity loss
        # Iterate BC until calculated velocity @ distance matches measured
        
        best_bc = book_bc_g7
        min_error = float('inf')
        
        for bc_test in [book_bc_g7 * x for x in [0.90, 0.92, 0.94, 0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10]]:
            # Calculate velocity at distance with test BC
            calc_velocity = self._calculate_velocity_at_distance(
                muzzle_velocity_fps,
                bc_test,
                distance_m,
                atmospheric_conditions
            )
            
            error = abs(calc_velocity - velocity_at_distance_fps)
            if error < min_error:
                min_error = error
                best_bc = bc_test
        
        variance_percent = ((best_bc - book_bc_g7) / book_bc_g7) * 100
        
        return {
            'book_bc_g7': book_bc_g7,
            'true_bc_g7': best_bc,
            'variance_percent': variance_percent,
            'method': 'velocity_loss',
            'distance_m': distance_m,
            'confidence': 'high' if min_error < 10 else 'medium'
        }
    
    def calculate_from_drop(
        self,
        muzzle_velocity_fps: float,
        zero_distance_m: float,
        test_distance_m: float,
        measured_drop_cm: float,
        book_bc_g7: float,
        atmospheric_conditions: Dict
    ) -> Dict:
        """
        Calculate true BC from drop measurement
        Shoot @ 100m zero, then shoot @ 600m and measure drop
        """
        
        # Similar iteration approach
        best_bc = book_bc_g7
        min_error = float('inf')
        
        for bc_test in [...]:  # Same range
            calc_drop = self._calculate_drop(
                muzzle_velocity_fps,
                bc_test,
                zero_distance_m,
                test_distance_m,
                atmospheric_conditions
            )
            
            error = abs(calc_drop - measured_drop_cm)
            if error < min_error:
                min_error = error
                best_bc = bc_test
        
        return {...}  # Same format
```

### **GUI - True BC Wizard:**
```python
# src/modules/true_bc_wizard.py

class TrueBCWizard(QDialog):
    """Wizard for calculating true BC"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 True BC Calculator")
        self.init_ui()
    
    def init_ui(self):
        # Method selection
        # Input fields for velocity/drop
        # Atmospheric conditions
        # Calculate button
        # Results with trajectory comparison (book BC vs true BC)
        pass
```

### **Estimert tid:** 6-8 timer

---

## 🟡 PRIORITET 4: BRASS LOT TRACKING & LIFECYCLE MANAGEMENT

### **Problem:**
Ingen måte å spore brass lots, firings, annealing schedule. Brukere mister oversikt over case lifecycle.

### **Løsning:**
Komplett brass management system med QR codes (fremtidig feature).

```python
# src/modules/brass_manager.py (NY MODUL)

class BrassManager(QWidget):
    """Brass lot tracking and lifecycle management"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Brass lots table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Lot Name", "Manufacturer", "Caliber", "Quantity",
            "Times Fired", "Last Annealed", "Anneal Due", "Status", "Actions", "QR"
        ])
        
        # Buttons: Add Lot, Fire Lot (+1 firing), Anneal Lot, Retire Cases, Print QR
        
        # Firing counter: Scan QR → increment fires
        
        # Annealing scheduler: Alert when >2 firings without annealing
        
        # Case prep checklist per lot
        
        # Measurements tab: Track case length, neck diameter over time
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def add_lot(self):
        """Add new brass lot"""
        dialog = BrassLotDialog()
        if dialog.exec():
            lot_data = dialog.get_data()
            # Save to brass_lots table
            # Generate QR code with lot_id
    
    def increment_firings(self, lot_id: int):
        """Increment times_fired for entire lot"""
        # UPDATE brass_lots SET times_fired = times_fired + 1
        # Check if annealing due (every 3 firings for match brass)
        # Show notification if due
    
    def schedule_annealing(self, lot_id: int):
        """Mark lot as needing annealing"""
        pass
    
    def retire_cases(self, lot_id: int, quantity: int):
        """Retire cases from lot (splits, cracks, etc.)"""
        # UPDATE brass_lots SET retired_quantity = retired_quantity + quantity
        # UPDATE quantity = quantity - quantity
```

### **Estimert tid:** 4-6 timer

---

## 🟢 PRIORITET 5: HARMONICS/OBT CALCULATOR

### **Problem:**
Ingen måte å beregne Optimal Barrel Time fra rifle profile data.

### **Løsning:**
Implementer Chris Long's OBT teori + node prediction.

```python
# src/utils/harmonics_calculator.py (NY FIL)

class HarmonicsCalculator:
    """Calculate barrel harmonics and Optimal Barrel Time"""
    
    def calculate_obt(
        self,
        barrel_length_mm: float,
        barrel_weight_g: float,
        barrel_profile: str,
        muzzle_device_weight_g: float,
        barrel_material: str
    ) -> Dict:
        """
        Calculate OBT using Chris Long's formula
        
        OBT = (L / 10000) * sqrt(W / S)
        Where:
          L = barrel length (inches)
          W = barrel weight (lbs)
          S = stiffness (depends on profile, material)
        """
        
        # Convert units
        length_inch = barrel_length_mm / 25.4
        total_weight_lb = (barrel_weight_g + muzzle_device_weight_g) / 453.592
        
        # Estimate stiffness from profile
        stiffness = self._estimate_stiffness(
            barrel_profile,
            length_inch,
            barrel_material
        )
        
        # Calculate OBT (milliseconds)
        obt_ms = (length_inch / 10000) * math.sqrt(total_weight_lb / stiffness)
        
        # Calculate velocity nodes
        nodes = []
        for i in range(1, 8):  # First 7 nodes
            node_time_ms = obt_ms * i
            node_velocity_fps = (length_inch * 12) / (node_time_ms / 1000)  # L / T
            nodes.append({
                'node': i,
                'time_ms': node_time_ms,
                'velocity_fps': int(node_velocity_fps)
            })
        
        return {
            'obt_ms': obt_ms,
            'nodes': nodes,
            'stiffness': stiffness,
            'total_weight_lb': total_weight_lb
        }
    
    def _estimate_stiffness(self, profile: str, length_inch: float, material: str) -> float:
        """
        Estimate barrel stiffness from profile
        
        Stiffness ∝ (E * I) / L^3
        Where:
          E = Young's modulus (material)
          I = Second moment of area (profile)
          L = Length
        """
        
        # Young's modulus (PSI)
        modulus = {
            'Chrome-moly': 30e6,
            'Stainless': 28e6,
            'Carbon Fiber': 35e6
        }.get(material, 30e6)
        
        # Relative stiffness by profile (arbitrary units)
        profile_factor = {
            'straight': 1.0,
            'light_taper': 0.85,
            'heavy_taper': 0.95,
            'bull': 1.3,
            'fluted': 0.90
        }.get(profile, 1.0)
        
        # Simplified stiffness calculation
        stiffness = (modulus * profile_factor) / (length_inch ** 2)
        
        return stiffness
```

### **GUI Integration:**
Legg til "🎵 Harmonics Analysis" i Load Development Wizard's AI Recommendations page.

### **Estimert tid:** 6-8 timer

---

## 🟢 PRIORITET 6: ADVANCED CHRONOGRAPH DATA LOGGER

### **Problem:**
Comprehensive logger har bare avg/ES/SD. Ingen shot-by-shot tracking for dype analyser.

### **Løsning:**
Shot string logger med statistikk og grafer.

```python
# src/modules/chronograph_logger.py (NY MODUL)

class ChronographLogger(QWidget):
    """Shot-by-shot chronograph data logger"""
    
    def __init__(self):
        super().__init__()
        self.shots = []
        self.init_ui()
    
    def init_ui(self):
        # Session metadata: rifle, ammo, conditions
        # Shot input: velocity per shot (or paste string: "2710, 2705, 2715, ...")
        # Live stats: Running avg, ES, SD
        # Graph: Velocity vs shot number
        # Export: CSV for external analysis
        
        # Features:
        # - Auto-calculate ES/SD after each shot
        # - Detect velocity trends (warming barrel = velocity increase)
        # - Outlier detection (flag shots >2σ from mean)
        # - Save to chronograph_sessions + chronograph_shots tables
        pass
```

### **Estimert tid:** 4-6 timer

---

## 📊 OPPSUMMERING - RESSURSBRUK

| Prioritet | Forbedring | Estimert Tid | Verdi | Kompleksitet |
|-----------|-----------|--------------|-------|--------------|
| 🔥 P1 | Database Schema Update | 4-6 timer | Kritisk | Medium |
| 🔥 P2 | Pressure Estimator | 6-8 timer | Høy | Medium-Høy |
| 🟡 P3 | True BC Calculator | 6-8 timer | Høy | Høy |
| 🟡 P4 | Brass Lot Tracking | 4-6 timer | Medium | Medium |
| 🟢 P5 | Harmonics/OBT Calculator | 6-8 timer | Medium | Høy |
| 🟢 P6 | Chronograph Logger | 4-6 timer | Medium | Lav-Medium |

**Total estimert tid: 30-42 timer**

---

## 🎯 ANBEFALT REKKEFØLGE

### **Sprint 1 (1 uke):**
1. Database Schema Update (P1) - Må gjøres først!
2. RifleProfileEditor save/load integration
3. Testing av database persistence

### **Sprint 2 (1 uke):**
4. Pressure Estimator (P2) - Stor verdi, moderate effort
5. GUI integration i workflow hub
6. Testing med real-world data

### **Sprint 3 (1 uke):**
7. True BC Calculator (P3) - Advanced feature
8. Brass Lot Tracking (P4) - QOL improvement

### **Sprint 4 (1 uke):**
9. Harmonics Calculator (P5) - Nice-to-have
10. Chronograph Logger (P6) - Polishing
11. Integration testing av alle nye features

---

## 💡 YTTERLIGERE IDEER (Backlog)

- **AI Load Recommender**: ML model trent på historical data → predict optimal charge/seating
- **Target Image Analyzer**: OpenCV for automatic group size measurement
- **Weather Station Integration**: Kestrel Bluetooth API for auto atmospheric data
- **GRT Import Enhancement**: Better parsing av Gordon Reloading Tool files
- **Ballistic Solver**: Full trajectory calculator med wind, spin drift, Coriolis
- **Mobile App**: Companion app for range - log shots via phone

---

Vil du at jeg skal begynne med noen av disse implementasjonene? P1 (Database Schema) er mest kritisk! 🚀
