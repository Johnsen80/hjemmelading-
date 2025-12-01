# Rifle Profile Editor - Beginner/Expert Mode Implementation

## Oversikt
Rifle Profile Editor har nå full støtte for **Nybegynner** og **Ekspert** modus, som gjør det enkelt for nye brukere samtidig som erfarne skyttere får tilgang til alle avanserte harmonics beregninger.

## Funksjonalitet

### 🌱 Nybegynner Modus
**Formål**: Enkel, strømlinjeformet opplevelse for casual reloadere

**Tabs som vises**:
1. **📋 Grunnleggende** - Rifle navn, produsent, kaliber, action type, serienummer
2. **🔫 Pipe** - Forenklet visning:
   - Pipe lengde (mm/tommer toggle)
   - Twist rate
   - Pipe type (Standard/Medium/Tung/Bull)

**Felter som skjules**:
- ❌ Muzzle diameter, breech diameter, pipe vekt
- ❌ Free-floating, bedding type, stock material
- ❌ Lyddemper/brems detaljer (vekt, lengde, POI shift)
- ❌ Kammer toleranser (fired vs sized brass)
- ❌ Kule profiler (freebore per bullet)
- ❌ Visuell forhåndsvisning

**Info melding**: Viser at dette er forenklet visning med oppfordring til å bytte til ekspert hvis nødvendig.

---

### 🎓 Ekspert Modus
**Formål**: Komplett harmonics analyse og presisjonsskyting

**Alle 6 tabs**:
1. **📋 Grunnleggende** - Samme som nybegynner
2. **🔫 Pipe Detaljer** - Full pipe profil:
   - Dimensjoner: lengde, twist, muzzle/breech diameter
   - Konstruksjon: profil type (straight/taper/bull/fluted), materiale, vekt
   - Montering: free-floating, bedding type, stock material
   - Tilstand: skudteller, pipe condition, throat erosion
3. **🔇 Lyddemper/Brems** - Kritisk for harmonics:
   - Device type (suppressor/brake/flash_hider)
   - Fysiske specs: lengde, vekt, diameter
   - Thread pitch
   - POI shift tracking (horizontal/vertical @ 100m)
4. **📏 Kammer & Toleranser** - ES/SD analyse:
   - Chamber spec (SAAMI/CIP/Match/Custom)
   - Fired case measurements (base, shoulder, length)
   - Sized case measurements
   - **Auto-calculated clearances** med fargekoding:
     - 🟢 <50μm = Match grade (excellent)
     - 🟠 <100μm = OK
     - 🔴 >100μm = Løs (høy ES)
5. **🎯 Kule Profiler** - Freebore per bullet:
   - Bullet navn, vekt
   - Jam length (CBTO)
   - Optimal jump
   - Max COAL for magasin
6. **👁️ Visuell Oversikt** - HTML preview av hele profilen

---

## Brukergrensesnitt

### Mode Toggle
Øverst i dialogen finnes to radio buttons:
- **🌱 Nybegynner (Enkelt)**
- **🎓 Ekspert (Full detaljer)**

**Interaksjon**:
- Bytter mellom modusene umiddelbart
- Ved bytte fra Ekspert → Nybegynner: Advarsel at data ikke slettes, bare skjules
- Tabs rebuildes automatisk basert på valgt modus

### Visuell Styling
```python
mode_widget.setStyleSheet("""
    QWidget {
        background-color: #ecf0f1;
        padding: 10px;
        border-radius: 5px;
    }
    QRadioButton {
        font-weight: bold;
    }
""")
```

---

## Implementasjonsdetaljer

### Kode Struktur

#### `__init__` parameter
```python
def __init__(self, parent=None, rifle_id: Optional[int] = None, user_mode: str = "beginner"):
    super().__init__(parent)
    self.db = get_database()
    self.rifle_id = rifle_id
    self.rifle_data = {}
    self.user_mode = user_mode  # "beginner" or "expert"
```

#### Mode Change Handler
```python
def on_mode_changed(self, checked):
    """Handle user mode toggle"""
    if not checked:
        return
    
    new_mode = "beginner" if self.mode_beginner.isChecked() else "expert"
    
    if new_mode == self.user_mode:
        return
    
    # Warn if switching from expert to beginner
    if new_mode == "beginner":
        reply = QMessageBox.question(...)
        if reply == QMessageBox.StandardButton.No:
            self.mode_expert.setChecked(True)
            return
    
    self.user_mode = new_mode
    self.rebuild_tabs()
```

#### Tab Rebuilding
```python
def rebuild_tabs(self):
    """Rebuild tabs based on current user mode"""
    # Clear all tabs
    while self.tabs.count() > 0:
        self.tabs.removeTab(0)
    
    # Re-add tabs based on mode
    self.tabs.addTab(self.create_basic_tab(), "📋 Grunnleggende")
    
    if self.user_mode == "beginner":
        self.tabs.addTab(self.create_barrel_tab_simple(), "🔫 Pipe")
    else:
        # All expert tabs...
        self.tabs.addTab(self.create_barrel_tab(), "🔫 Pipe Detaljer")
        self.tabs.addTab(self.create_muzzle_tab(), "🔇 Lyddemper/Brems")
        # ... etc
```

#### Simplified Barrel Tab
```python
def create_barrel_tab_simple(self) -> QWidget:
    """Simplified barrel tab for beginners"""
    widget = QWidget()
    layout = QVBoxLayout()
    
    # Info box explaining simplified view
    info = QLabel(
        "ℹ️ Dette er forenklet visning. Bytt til Ekspert modus for detaljerte "
        "harmonics beregninger og kammer toleranser."
    )
    info.setStyleSheet(...)
    layout.addWidget(info)
    
    # Simple form - just essentials
    form = QFormLayout()
    
    # Barrel length with mm/inch toggle
    self.barrel_length = QDoubleSpinBox()
    self.barrel_length.setRange(250, 900)
    self.barrel_length.setValue(610)
    self.barrel_length.setSuffix(" mm")
    
    # Twist rate
    self.twist_rate = QComboBox()
    self.twist_rate.addItems(["1:7\"", "1:8\"", "1:9\"", ...])
    
    # Simple profile
    self.barrel_profile_simple = QComboBox()
    self.barrel_profile_simple.addItems([
        "Standard/Sporter",
        "Medium/Varmint",
        "Tung/Heavy",
        "Bull Barrel"
    ])
    
    return widget
```

#### Save Profile - Mode Aware
```python
def save_profile(self):
    """Save complete rifle profile"""
    # Basic data (always)
    rifle_data = {
        'name': self.name.text(),
        'manufacturer': self.manufacturer.text(),
        'caliber': self.caliber.currentText(),
        'action_type': self.action_type.currentText(),
        'serial_number': self.serial.text(),
        'barrel_length': self.barrel_length.value(),
        'twist_rate': self.twist_rate.currentText(),
        'notes': self.notes.toPlainText(),
        'user_mode': self.user_mode
    }
    
    # Beginner: simplified profile
    if self.user_mode == "beginner":
        rifle_data['barrel_profile'] = self.barrel_profile_simple.currentText()
    else:
        # Expert: all detailed data
        rifle_data.update({
            'barrel_profile': self.barrel_profile.currentText(),
            'barrel_material': self.barrel_material.currentText(),
            'barrel_weight': self.barrel_weight.value(),
            'free_float': self.free_float.isChecked(),
            'has_muzzle_device': self.has_device.isChecked(),
            'device_weight': self.device_weight.value(),
            'fired_base_dia': self.fired_base.value(),
            'sized_base_dia': self.sized_base.value(),
            # ... etc
        })
    
    self.rifle_saved.emit(rifle_data)
```

---

## Testing

### Test Script
`test_rifle_profile.py` er inkludert i root directory:

```bash
# Test nybegynner modus
python test_rifle_profile.py beginner

# Test ekspert modus
python test_rifle_profile.py expert
```

### Manuell Testing
1. Åpne rifle profile editor
2. Verifiser at **Nybegynner** er default
3. Verifiser kun 2 tabs vises (Grunnleggende + Pipe)
4. Bytt til **Ekspert** modus
5. Verifiser at alle 6 tabs vises
6. Fyll inn noe data
7. Bytt tilbake til **Nybegynner**
8. Verifiser advarsel vises
9. Verifiser data ikke forsvinner (lagret i minnet)
10. Lagre profil
11. Verifiser `user_mode` er inkludert i saved data

---

## Neste Steg

### Database Schema Update
Oppdater `database.py` for å lagre all harmonics data:

```sql
-- Add columns to rifles table
ALTER TABLE rifles ADD COLUMN barrel_profile TEXT;
ALTER TABLE rifles ADD COLUMN barrel_material TEXT;
ALTER TABLE rifles ADD COLUMN muzzle_diameter REAL;
ALTER TABLE rifles ADD COLUMN barrel_weight INTEGER;
ALTER TABLE rifles ADD COLUMN free_float BOOLEAN;
ALTER TABLE rifles ADD COLUMN user_mode TEXT DEFAULT 'beginner';

-- New table: rifle_muzzle_devices
CREATE TABLE rifle_muzzle_devices (
    id INTEGER PRIMARY KEY,
    rifle_id INTEGER,
    device_type TEXT,
    length REAL,
    weight INTEGER,
    diameter REAL,
    poi_shift_h REAL,
    poi_shift_v REAL,
    FOREIGN KEY (rifle_id) REFERENCES rifles(id)
);

-- New table: rifle_chamber_specs
CREATE TABLE rifle_chamber_specs (
    id INTEGER PRIMARY KEY,
    rifle_id INTEGER,
    chamber_spec TEXT,
    fired_base_dia REAL,
    fired_shoulder_dia REAL,
    sized_base_dia REAL,
    sized_shoulder_dia REAL,
    clearance_microns_base REAL,
    clearance_microns_shoulder REAL,
    FOREIGN KEY (rifle_id) REFERENCES rifles(id)
);

-- New table: rifle_bullet_profiles
CREATE TABLE rifle_bullet_profiles (
    id INTEGER PRIMARY KEY,
    rifle_id INTEGER,
    bullet_id INTEGER,
    jam_length REAL,
    optimal_jump REAL,
    mag_max_coal REAL,
    FOREIGN KEY (rifle_id) REFERENCES rifles(id),
    FOREIGN KEY (bullet_id) REFERENCES bullets(id)
);
```

### Integration med Workflow Hub
Legg til rifle profile editor i workflow hub under "🔫 Rifles & Utstyr":

```python
# workflow_hub.py
("rifle_profile_editor", "🎯", "Advanced Rifle Profile", "Detaljert profil med harmonics"),
```

### Integration med Rifle & Optikk Manager
Erstatt enkel rifle dialog med RifleProfileEditor:

```python
# rifle_optic_manager.py
def add_rifle(self):
    editor = RifleProfileEditor(self, user_mode=self.current_user_mode)
    editor.rifle_saved.connect(self.on_rifle_saved)
    editor.exec()
```

### Harmonics Calculator Module
Bruk rifle profile data for OBT (Optimal Barrel Time) beregninger:

```python
# harmonics_calculator.py
def calculate_obt(rifle_data):
    """Calculate Optimal Barrel Time based on rifle profile"""
    barrel_length = rifle_data['barrel_length']
    barrel_weight = rifle_data['barrel_weight']
    device_weight = rifle_data.get('device_weight', 0)
    
    # Chris Long's OBT formula
    total_weight = barrel_weight + device_weight
    stiffness = calculate_stiffness(rifle_data)
    
    obt = (barrel_length / 10000) * sqrt(total_weight / stiffness)
    
    return {
        'obt_seconds': obt,
        'optimal_velocity': barrel_length / obt,
        'node_positions': calculate_nodes(barrel_length, obt)
    }
```

---

## Konklusjon

✅ **Ferdig implementert**:
- Beginner/expert mode toggle med visuell indikator
- Conditional tab visning basert på mode
- Simplified barrel tab for beginners
- Mode-aware save_profile()
- Mode-aware preview generation
- Rebuild tabs on mode change
- Warning dialog ved bytte fra expert til beginner

✅ **Testing**:
- Ingen compile errors
- Test script inkludert

⏳ **Neste oppgaver**:
- Database schema update
- Integration i workflow hub
- Integration i rifle_optic_manager
- Harmonics calculator module
- AI recommendations engine med rifle profile data
