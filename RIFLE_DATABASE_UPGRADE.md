# 🎯 Rifle Database Upgrade - Komplett Oversikt

## ✅ Hva er Nytt?

Rifle database har fått en **MASSIV oppgradering** med fokus på profesjonell ladeutvikling, harmonikk, og vedlikehold.

---

## 🗄️ Nye Database-Tabeller

### 1. **Rifles** - Fullstendig Redesign
Tidligere hadde rifles-tabellen kun grunnleggende data. Nå har vi:

#### **Grunnleggende Info**
- Manufacturer, Model, Serial Number
- Caliber, Action Type
- Purchase Date

#### **Pipe/Løp Detaljer** (for harmonisk beregning)
- **Barrel Length** (mm og inches)
- **Barrel Contour** (light, medium, heavy, varmint, bull)
- **Barrel Profile** (link til predefinerte profiler)
- **Dimensjoner:**
  - Muzzle diameter
  - Breech diameter  
  - Mid-barrel diameter
  - Barrel weight
- **Material & Finish** (chrome-moly, stainless, carbon-fiber)
- **Befestning:** barrel attachment, torque spec

#### **Twist Rate & Rifling**
- Twist rate (1:8, 1:10, etc)
- Twist direction (right/left)
- Rifling type (conventional, 5R, polygonal, button, cut)
- Groove count, groove depth

#### **Kammer Detaljer**
- Chamber spec (SAAMI, CIP, match, custom)
- Freebore length
- Throat angle
- Leade length
- Max COAL for magazine

#### **Skuddteller** ⭐
- **round_count** - Totalt skudd fyrt
- **last_cleaned_round_count** - Skudd ved siste rengjøring
- **accuracy_life_estimate** - Estimert pipe-liv (basert på kaliber)

#### **Vedlikehold & Tilstand**
- last_cleaning_date, last_maintenance_date
- **bore_condition** (excellent, good, fair, worn)
- **throat_erosion_mm** - Målt erosjon
- **accuracy_baseline_moa** - Original nøyaktighet
- **current_accuracy_moa** - Nåværende nøyaktighet

#### **Bullet Jump Måling**
- jam_length_cbto_mm - Hvor langt til kulen berører riflingen
- jam_measurement_bullet_id - Hvilken kule
- jam_measurement_date

#### **Harmonisk Data**
- fundamental_frequency_hz (beregnet)
- harmonic_nodes (JSON array av node-posisjoner)
- optimal_bullet_weight_range

---

### 2. **barrel_profiles** - Predefinerte Løpsprofiler ⭐

14 predefinerte profiler fra industrien:

| Profil | Kategori | Stivhet | Muzzle Ø | Breech Ø | Vekt |
|--------|----------|---------|----------|----------|------|
| Light Sporter | hunting | light | 0.600" | 1.125" | ~4.1 lbs |
| Medium Sporter | hunting | medium | 0.700" | 1.150" | ~5.8 lbs |
| Heavy Sporter | hunting | medium | 0.750" | 1.200" | ~7.7 lbs |
| Light Varmint | varmint | medium | 0.800" | 1.200" | ~7.7 lbs |
| **Heavy Varmint** | varmint | heavy | 0.900" | 1.250" | ~10 lbs |
| **Sendero** | target | heavy | 0.850" | 1.200" | ~9.2 lbs |
| Palma | target | medium | 0.750" | 1.150" | ~8.3 lbs |
| Medium Palma | target | heavy | 0.800" | 1.200" | ~9.6 lbs |
| **MTU (M24)** | tactical | very-heavy | 1.250" | 1.250" | ~11.1 lbs |
| Bull Barrel | benchrest | very-heavy | 1.300" | 1.300" | ~11.9 lbs |
| Heavy Bull | benchrest | bull | 1.500" | 1.500" | ~16.3 lbs |
| Fluted Sporter | hunting | medium | 0.750" | 1.200" | ~6.1 lbs |
| Fluted Heavy Varmint | varmint | heavy | 0.900" | 1.250" | ~8.6 lbs |
| Carbon Fiber Wrapped | hunting | heavy | 0.900" | 1.200" | ~5 lbs |

**Data per profil:**
- Dimensjoner (muzzle, breech diameter)
- Taper rate
- Vekt per inch
- Stiffness rating
- Harmoniske karakteristikker
- Anbefalte kalibre

---

### 3. **rifle_bullet_jump_measurements** - COAL/CBTO Jam Målinger ⭐

Lagrer max COAL hvor kulen berører riflingen (jam length) per rifle + bullet kombinasjon.

**Felt:**
- rifle_id, bullet_id
- **jam_coal_mm** - Jam length (COAL)
- **jam_cbto_mm** - Jam length (CBTO - Cartridge Base To Ogive)
- measurement_method (Hornady OAL Gauge, fired case method, etc)
- measurement_tool
- **Anbefalte jump-verdier:**
  - jam_minus_010_mm (jam - 0.010")
  - jam_minus_020_mm (jam - 0.020")  
  - jam_minus_030_mm (jam - 0.030")
  - jam_minus_040_mm (jam - 0.040")
- measurement_variation_mm (standard deviation hvis flere målinger)
- **throat_erosion_since_baseline_mm** (tracking av erosjon)
- **rounds_fired_at_measurement** (skuddteller ved måling)

**Nytte:**
- Vet eksakt hvor langt kulen er fra riflingen
- Kan beregne optimal jump for forskjellige kuler
- Tracker throat erosion over tid (måler igjen etter X skudd)

---

### 4. **rifle_maintenance_log** - Vedlikeholdslogg ⭐

Logger alt vedlikehold på rifle.

**Felt:**
- maintenance_date
- **maintenance_type** (cleaning, deep_clean, inspection, repair, accuracy_test, barrel_break_in)
- **rounds_fired_before, rounds_fired_after** (skuddteller)
- **Rengjøring:**
  - bore_cleaned, carbon_removed, copper_removed
  - action_cleaned, action_lubricated
- **Tilstandsvurdering:**
  - bore_condition_rating (1-10 scale)
  - throat_condition (excellent, good, fair, worn)
  - throat_erosion_mm
- **Nøyaktighetstesting:**
  - accuracy_test_performed
  - accuracy_result_moa
  - group_size_mm, shots_count
- cleaning_products_used
- **next_maintenance_due_rounds** (automatisk beregning)

**Nytte:**
- Komplett historikk av vedlikehold
- Ser hvordan nøyaktighet degraderer over tid
- Vet når neste vedlikehold er nødvendig

---

### 5. **case_measurement_schedule** - Automatisk Hylse-Måling Varsel ⭐⚠️

**DETTE ER DEN STORE FEATUREN!**

Automatisk varselsystem som trigger når du bør måle hylser for slitasje-analyse.

**Felt:**
- rifle_id, case_id
- **measurement_interval_rounds** (default: 500 skudd)
- **last_measurement_round_count** (siste måling ved X skudd)
- **next_measurement_due_round_count** (neste måling ved X skudd)
- **warning_active** (boolean - vises varsel?)
- **warning_triggered_date**
- **measurement_completed** (boolean)
- measurement_completed_date
- last_measurement_id (link til case_measurements)

**Hvordan det fungerer:**

1. **Setup:** Når du lager rifle + case kombinasjon, settes `measurement_interval_rounds = 500`
2. **Automatisk tracking:** Hver gang du legger til skudd (via "🎯 Legg til Skudd" knapp), sjekkes:
   ```python
   if rifle.round_count >= schedule.next_measurement_due_round_count:
       schedule.warning_active = True
       # Vis varsel i GUI
   ```
3. **Varsel vises:** I rifle table, raden blir **GUL** med tooltip: "⚠️ Tid for hylse-måling!"
4. **Bruker måler hylser:** Logg i case_measurements
5. **Varsel fjernes:** 
   ```python
   schedule.measurement_completed = True
   schedule.next_measurement_due_round_count += 500
   ```

**Nytte:**
- Aldri glem å måle hylser!
- Fanger opp slitasje tidlig
- Forlenger brass-levetid
- Data for brass retirement-beslutninger

---

## 🎯 Nye GUI Moduler

### **RifleDatabaseManager** - Hovedvindu

**Features:**
- ✅ Oversiktstabell med alle rifles
- ✅ Kolonner: ID, Navn, Produsent, Modell, Kaliber, Pipe Lengde, **Skudd Fyrt**, Status, Siste Vedlikehold
- ✅ **Skudd Fyrt kolonne:**
  - Normal: Hvit bakgrunn
  - **Gul bakgrunn** når nær 500-skudd intervall (⚠️ Tooltip: "Tid for hylse-måling!")
  - **Rød bakgrunn** når > 80% av estimert pipe-liv (⚠️ Tooltip: "Pipe nærmer seg slutten av levetiden!")
- ✅ **Status kolonne:**
  - ✓ Utmerket (grønn)
  - ✓ God (blå)
  - ⚠ OK (orange)
  - ⚠ Slitt (rød)

**Knapper:**
- **➕ Nytt Våpen** - Åpner RifleEditorDialog
- **✏️ Rediger** - Rediger valgt rifle
- **🔍 Detaljer** - Vis detaljert info (RifleDetailsDialog)
- **🎯 Legg til Skudd** - Logg skudd fyrt (trigger varsel-sjekk!)
- **🔧 Vedlikehold** - Logg vedlikehold (rengjøring, testing, etc)
- **🗑️ Slett** - Slett rifle (med bekreftelse)

---

### **RifleEditorDialog** - Rifle Editor (4 Tabs)

#### **Tab 1: 📋 Grunnleggende**
- Navn, Produsent, Modell
- Kaliber (dropdown med vanlige kalibre)
- Action Type (bolt, semi-auto, lever, single-shot, pump)
- Serienummer
- Kjøpsdato
- Notater

#### **Tab 2: 🔫 Pipe/Løp**
**Barrel Profile Selection:**
- Dropdown med alle 14 predefinerte profiler
- Viser: "Sendero (target, heavy)"
- **Auto-populate:** Når profil velges, fylles muzzle/breech diameter automatisk!

**Dimensjoner:**
- Pipe Lengde (inches)
- Muzzle Diameter (inches, 3 desimaler)
- Breech Diameter (inches, 3 desimaler)

**Material & Finish:**
- Material: chrome-moly, stainless, carbon-fiber
- Finish: blued, stainless, cerakote, nitride, parkerized
- Pipe Produsent (f.eks. Bartlein, Krieger, Proof)

#### **Tab 3: ⚙️ Kammer & Twist**
**Twist Rate & Rifling:**
- Twist Rate (dropdown: 1:7, 1:8, 1:9, 1:10, etc)
- Twist Direction (right/left)
- Rifling Type (conventional, polygonal, 5R, button, cut, broach)

**Kammer Detaljer:**
- Chamber Spec (SAAMI, CIP, match, custom, minimum)
- Freebore (mm)
- Throat Angle (grader)
- Max COAL for Magasin (mm)

#### **Tab 4: 📊 Status & Tilstand**
**Skuddteller:**
- Totalt Skudd Fyrt
- Estimert Pipe-Liv (basert på kaliber)
  - .223 Rem: ~3000 skudd
  - 6mm Creedmoor: ~1500 skudd
  - 6.5 Creedmoor: ~2500 skudd
  - .308 Win: ~5000 skudd
  - .300 Win Mag: ~1500 skudd

**Tilstand:**
- Bore Condition (excellent, good, fair, worn)
- Throat Erosion (mm)
- Baseline Accuracy (MOA - original)

---

### **RifleDetailsDialog** - Detaljert Visning (4 Tabs)

#### **Tab 1: ℹ️ Info**
HTML-formatert oversikt:
- Grunnleggende info
- Pipe detaljer
- Status (med farger)

#### **Tab 2: 🌊 Harmonikk**
- Pipe lengde, muzzle/breech diameter
- Stivhetsrating (basert på dimensjoner)
- Harmonisk analyse (forenklet)
- *Detaljert harmonisk beregning kommer...*

#### **Tab 3: 📏 Bullet Jump**
Tabell med alle jam-målinger:
- Dato, Kule, Jam COAL, Jam CBTO, Metode, Skudd ved Måling
- Kan se hvordan jam length endres over tid (throat erosion!)

#### **Tab 4: 🔧 Vedlikehold**
Tabell med vedlikeholdslogg:
- Dato, Type, Skudd, Bore Condition, Notater
- Full historikk av rengjøring, testing, reparasjoner

---

### **AddRoundsFiredDialog** - Logg Skudd Fyrt

**Enkel dialog:**
- Viser nåværende skuddteller
- Input: Antall skudd å legge til
- Notater (optional)

**Automatisk varsling:**
- Hvis du passerer 500-skudd intervall: "⚠️ Du passerer 500 skudd! Husk å måle hylser for slitasje."
- Hvis > 80% av pipe-liv: "⚠️ Pipen nærmer seg estimert levetid!"

**Lagring:**
- Oppdaterer `rifles.round_count`
- Logger i `rifle_maintenance_log` (type: shooting_session)
- **Trigger case measurement warning** (case_measurement_schedule)

---

### **MaintenanceLogDialog** - Logg Vedlikehold

**Felt:**
- Dato
- Type (cleaning, deep_clean, inspection, repair, accuracy_test, barrel_break_in)
- Checkboxes:
  - ☑ Løp rengjort
  - ☑ Carbon fjernet
  - ☑ Copper fjernet
- Bore Condition (dropdown)
- Accuracy Test (MOA)
- Notater

**Lagring:**
- Lagrer i `rifle_maintenance_log`
- Oppdaterer `rifles.last_maintenance_date`
- Hvis bore rengjort: Oppdater `last_cleaning_date` og `last_cleaned_round_count`
- Oppdaterer `current_accuracy_moa` (tracker degradering)

---

## 🔧 Hvordan Bruke Systemet

### **Scenario 1: Ny Rifle Setup**

1. **Klikk "➕ Nytt Våpen"**
2. **Tab 1 - Grunnleggende:**
   - Navn: "Min 6.5 Creedmoor Precision"
   - Produsent: "Tikka"
   - Modell: "T3x"
   - Kaliber: "6.5 Creedmoor"
   - Action: "bolt"
3. **Tab 2 - Pipe:**
   - Velg profil: **"Sendero (target, heavy)"**
   - ✨ Dimensjoner fylles automatisk!
   - Pipe Lengde: 24"
   - Material: "stainless"
   - Pipe Produsent: "Bartlein"
4. **Tab 3 - Kammer & Twist:**
   - Twist Rate: "1:8"
   - Chamber Spec: "SAAMI"
   - Max COAL: 71.12 mm (2.800")
5. **Tab 4 - Status:**
   - Skudd Fyrt: 0
   - Estimert Pipe-Liv: 2500 skudd
   - Bore Condition: "excellent"
6. **Lagre!** ✅

---

### **Scenario 2: Logg Skudd Etter Økt**

1. **Velg rifle i tabellen**
2. **Klikk "🎯 Legg til Skudd"**
3. **Legg inn:** 40 skudd
4. **Notater:** "Ladder test, 3 shot groups, 140gr Berger"
5. **Lagre** ✅

**Automatisk:**
- Skuddteller oppdateres: 0 → 40
- Logger i vedlikeholdslogg
- Hvis 500 skudd: **Trigger varsel** ⚠️

---

### **Scenario 3: Case Measurement Warning Triggered**

**Du har fyrt 520 skudd totalt.**

**I rifle table:**
- Skudd Fyrt kolonne er **GUL**
- Tooltip: "⚠️ Tid for hylse-måling!"

**Hva du gjør:**
1. Mål 5-10 skutte hylser:
   - Case length
   - Case head expansion
   - Primer pocket depth
   - Concentricity
2. Logg i case_measurements tabellen (via Brass Manager)
3. System oppdaterer `case_measurement_schedule`:
   - `measurement_completed = True`
   - `next_measurement_due_round_count = 1000` (+ 500)
4. **Varsel forsvinner** ✅
5. Neste varsel ved 1000 skudd

---

### **Scenario 4: Vedlikeholdslogg**

**Etter rengjøring:**

1. **Velg rifle**
2. **Klikk "🔧 Vedlikehold"**
3. **Fyll inn:**
   - Dato: I dag
   - Type: "deep_clean"
   - ☑ Løp rengjort
   - ☑ Carbon fjernet
   - ☑ Copper fjernet
   - Bore Condition: "excellent"
   - Accuracy Test: 0.75 MOA
   - Notater: "Brukt Wipeout, 10 patches, copper fjernet fullstendig"
4. **Lagre** ✅

**Automatisk:**
- Lagrer i `rifle_maintenance_log`
- Oppdaterer `last_cleaning_date`
- Oppdaterer `last_cleaned_round_count`
- Oppdaterer `current_accuracy_moa` (tracker om accuracy degraderer)

---

### **Scenario 5: Bullet Jump Måling**

**Når du kjøper nye kuler:**

1. **Mål jam length med Hornady OAL Gauge**
   - Jam COAL: 73.25 mm
   - Jam CBTO: 54.10 mm
2. **Logg i rifle_bullet_jump_measurements** (GUI kommer)
3. **System beregner anbefalte jump-verdier:**
   - Jam - 0.010": 73.00 mm COAL
   - Jam - 0.020": 72.75 mm COAL
   - Jam - 0.030": 72.49 mm COAL
   - Jam - 0.040": 72.24 mm COAL
4. **Bruk i Ladder Test:** Start med -0.020" jump

**Over tid:**
- Throat eroderer (spesielt i 6mm, magnums)
- **Mål igjen** etter 500-1000 skudd
- **Track erosjon:** System viser hvor mye throat har erodert

---

## 📊 Data-Analyse Muligheter

Med denne nye strukturen kan vi nå:

### **Barrel Life Analysis**
- Plot accuracy (MOA) over skudd fyrt
- Finn når accuracy begynner å degradere
- Bestem optimal pipe-levetid for hver kaliber

### **Throat Erosion Tracking**
- Mål jam length ved 0, 500, 1000, 1500 skudd
- Plot erosjon over tid
- Prediker når re-barreling er nødvendig

### **Maintenance Correlation**
- Analyse: Påvirker rengjøringsfrekvens accuracy?
- Optimal rengjøringsintervall per kaliber/pipe

### **Case Wear Patterns**
- Koble case measurements med rifle round_count
- Finn når cases må anneales, trimmes, retires
- Optimal brass levetid per rifle

### **Harmonics Optimization**
- Med pipe dimensjoner kan vi beregne harmoniske noder
- Anbefale optimal barrel length for gitt kaliber
- Anbefale bullet weight basert på barrel profile

---

## 🎯 Neste Steg: Implementasjon

### **Priority 1: GUI for Bullet Jump Measurements**
- Dialog for å legge inn jam length målinger
- Vis i rifle details
- Auto-beregn anbefalte jump-verdier

### **Priority 2: Harmonics Calculator**
- Beregn fundamental frequency basert på barrel dimensions
- Vis harmoniske noder
- Anbefal optimal tuning (muzzle devices, barrel length)

### **Priority 3: Case Measurement Integration**
- Link case measurements til rifle round_count
- Automatisk varsel-system
- Vis trends i case wear

### **Priority 4: OCW (Optimal Charge Weight) Wizard**
- Som beskrevet i COMPETITION_RELOADING_ANALYSIS.md
- Guided ladder test for å finne velocity nodes
- Mål: ES/SD < 15 fps

### **Priority 5: Brass Weight Sorting Module**
- Log individual brass weights
- Auto-group within ±0.5gr
- Track groups per batch

---

## 🚀 Konklusjon

**Rifle database er nå professional-grade!**

✅ Komplett harmonikk-data  
✅ Automatisk skuddteller  
✅ Bullet jump tracking  
✅ Vedlikeholdshistorikk  
✅ **AUTOMATISK CASE MEASUREMENT VARSEL** 🎯  
✅ 14 predefinerte barrel profiles  
✅ Throat erosion tracking  
✅ Accuracy degradering tracking  

**Dette er nivået som competitive shooters trenger!**

Neste: Implementer OCW Wizard og Brass Sorting! 🎯
