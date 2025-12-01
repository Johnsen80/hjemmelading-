# 🥉 Brass/Hylse Manager - Brukerveiledning

## Oversikt
Brass Manager er en komplett lifecycle tracking modul for hylser fra kjøp til retirement.

## Database Schema

### Extended `cases` Table
**11 nye kolonner** lagt til:
- `lot_number TEXT` - Batch ID fra produsent
- `purchase_date TEXT` - Kjøpsdato
- `case_capacity_gr_h2o REAL` - Vannkapasitet (grains H2O) - KRITISK for QuickLOAD!
- `avg_weight_gr REAL` - Gjennomsnittsvekt
- `wall_thickness TEXT` - Tykkelse (Thin/Medium/Thick/Extra Thick)
- `neck_thickness_mm REAL` - Halstyin, påvirker bullet tension
- `retired_quantity INTEGER` - Antall retirerte hylser
- `last_trimmed_date TEXT` - Sist trimmet
- `trim_length_mm REAL` - Nåværende lengde
- `primer_pocket_uniformed BOOLEAN` - Pocket uniformert
- `flash_hole_deburred BOOLEAN` - Flash hole deburred

### New Table: `case_measurements`
Sporer dimensjoner over tid:
- `measurement_type` - 'new', 'fired', 'sized', 'after_trim'
- `case_length_mm` - Total lengde
- `neck_diameter_mm` - Halsdiameter
- `neck_thickness_mm` - Halstykkelse
- `base_diameter_mm` - Bunn diameter
- `shoulder_diameter_mm` - Skulder diameter
- `case_weight_gr` - Vekt
- `concentricity_tir_mm` - TIR (Total Indicator Reading) - rundhet

**Bruk:**
- Mål nye hylser for baseline
- Mål etter firing for ekspansjon
- Mål etter sizing for å sjekke die setup
- Mål etter trimming for å dokumentere lengde

### New Table: `case_firing_log`
Logger hver skyting:
- `rounds_fired INTEGER` - Antall skudd
- `pressure_level TEXT` - 'low', 'medium', 'high', 'max'
- `case_head_expansion_inch REAL` - **KRITISK TRYKKINDIKATOR!**
  - 0.0002" = ~60,000 PSI
  - 0.0001" = ~50,000 PSI
  - 0.0003" = FARLIG! Over 70k PSI
- `primer_condition TEXT` - 'good', 'flattened', 'cratered', 'pierced'
- `annealing_due BOOLEAN` - Auto-flagg (hver 3. gang for match brass)
- `trim_due BOOLEAN` - Auto-flagg ved lengde > SAAMI max
- `rifle_id INTEGER` - Foreign key til rifle
- `ammo_profile_id INTEGER` - Foreign key til ammunisjon

**Bruk:**
- Logg etter hver shooting session
- Spor pressure signs
- Auto-alert når annealing trengs

### New Table: `case_annealing_log`
Annealing historie:
- `method TEXT` - 'flame', 'induction', 'amp'
- `temperature_f INTEGER` - Temperatur (750°F standard for brass shoulder)
- `time_seconds REAL` - Tid (3-4 sekunder for flame)
- `templaq_verified BOOLEAN` - Templaq paint brukt for verifisering

**Bruk:**
- Dokumenter annealing settings
- Spor consistency
- Korrelere annealing med case life

### New Table: `case_prep_log`
Alle prep operasjoner:
- `trimmed BOOLEAN`
- `trim_length_mm REAL`
- `chamfered BOOLEAN`
- `deburred BOOLEAN`
- `primer_pocket_uniformed BOOLEAN`
- `flash_hole_deburred BOOLEAN`
- `neck_turned BOOLEAN`
- `neck_thickness_final_mm REAL`
- `weight_sorted BOOLEAN`

**Bruk:**
- Full audit trail av prep
- Dokumenter batch prep sessions
- QC tracking

## GUI Features

### Main Table View
**Color-Coded Times Fired:**
- 🟢 Green (0-2): Fresh brass
- 🟡 Yellow (3-4): Consider annealing
- 🟠 Orange (5-9): Watch closely, anneal regularly
- 🔴 Red (10+): Consider retirement

**Columns:**
1. ID
2. Lot/Navn
3. Produsent
4. Kaliber
5. Antall
6. Times Fired (color-coded)
7. Sist Annealed
8. Anneal Due? (⚠️ warning if true)
9. Avg Weight
10. Capacity (H2O grains)
11. Retired
12. Status

### Toolbar Buttons

#### ➕ Nytt Hylse-Lot
Legg til nytt brass lot:
- Lot navn og nummer
- Produsent (dropdown med Lapua, Peterson, Alpha, ADG, etc.)
- Kaliber
- Antall
- Kjøpsdato
- Case capacity (H2O grains) - **VIKTIG for QuickLOAD pressure estimation!**
- Avg weight
- Wall thickness (Thin/Medium/Thick/Extra Thick)

#### 🔥 Logg Skyting (+1 Firing)
Incrementer `times_fired` og logg session:
- Dato
- Antall skudd
- Rifle (dropdown)
- Ammunisjon (dropdown)
- Trykkfnivå
- **Case head expansion** (inches) - Måles med mikrometer før/etter firing
- Primer condition

**Auto-functions:**
- Auto-incrementer `times_fired`
- Auto-flagg `annealing_due` hvis `times_fired % 3 == 0`
- Alert hvis annealing due

#### ♨️ Logg Annealing
Reset annealing counter:
- Dato
- Metode (flame/induction/AMP)
- Temperatur (standard 750°F)
- Tid (3-4 sek for flame)
- Templaq verifisert?

**Auto-functions:**
- Update `last_annealed`
- Reset `needs_annealing` til false

#### 🔧 Logg Prep (Trim/Uniform)
Checkboxes for alle prep steps:
- Trimmed (med lengde)
- Chamfered
- Deburred
- Primer pocket uniformed
- Flash hole deburred
- Neck turned (med final thickness)
- Weight sorted

**Auto-functions:**
- Update `last_trimmed_date` hvis trimmed
- Update `trim_length_mm`
- Update flags

#### 📏 Legg til Måling
Logg dimensjoner:
- Measurement type (new/fired/sized/after_trim)
- Case length
- Neck diameter
- Neck thickness
- Base diameter
- Shoulder diameter
- Weight
- Concentricity (TIR)

**Bruk:**
- Mål nye hylser for baseline
- Mål etter firing for ekspansjon tracking
- Mål etter sizing for die setup verification

#### 🗑️ Retirer Hylser
Retire damaged cases:
- Input: Antall å retire
- `quantity` reduseres
- `retired_quantity` økes
- Cases beholder historie (ikke slettet)

### Details View (Double-Click)
4 tabs med full historie:

#### 🔥 Firing History
- Alle firing sessions
- Dato, skudd, trykk, case head expansion, primer condition

#### ♨️ Annealing History
- Alle annealing sessions
- Metode, temp, tid, Templaq verified

#### 🔧 Prep History
- Alle prep sessions
- Checkboxes for hva som ble gjort

#### 📏 Målinger
- Alle measurements over tid
- Type, dimensjoner, weight

## Best Practices

### For Match Brass (Benchrest/F-Class)
1. **Weight sort** nye hylser (±0.5gr tolerance)
2. **Measure capacity** med H2O (±0.3gr tolerance)
3. **Uniform primer pockets** og **deburr flash holes**
4. **Anneal every 3 firings** (max 2 firings for absolute consistency)
5. **Neck turn** hvis neck thickness varierer >0.002"
6. **Measure case head expansion** - ikke overskrid 0.0002"
7. **Retire** ved 8-10 firings eller første crack/split

### For Hunting Brass
1. Weight sorting kan hoppes over (±2gr OK)
2. Annealing hver 5. gang
3. Primer pocket uniforming valgfritt
4. Neck turning bare hvis accuracy problems
5. Case head expansion sjekk bare for nye loads
6. Retire ved 12-15 firings eller visible damage

### For Plinking Brass
1. Minimal prep (just trim og deburr)
2. Annealing bare når nødvendig (stiff necks)
3. Retire ved splits eller pockets too loose
4. Kan bruke til 20+ firings med low-pressure loads

## Critical Measurements Explained

### Case Head Expansion
**Hvorfor dette er viktig:**
- Best non-pressure-trace pressure indicator!
- Måles med mikrometer før og etter firing
- 0.0001" = ~50,000 PSI
- 0.0002" = ~60,000 PSI
- 0.0003" = FARLIG! Over 70k PSI

**Hvordan måle:**
1. Mål base diameter før firing med mikrometer
2. Fire case
3. Mål igjen umiddelbart (før sizing)
4. Differanse = expansion
5. Logg i case_firing_log

**Interpretation:**
- 0.0001" eller mindre = Low pressure, safe
- 0.0002" = SAAMI max for many cartridges
- 0.0003"+ = OVER-PRESSURE! Reduce load!

### Case Capacity (H2O grains)
**Hvorfor dette er viktig:**
- Direkte påvirker load density
- Brukes i QuickLOAD for pressure estimation
- Variasjon mellom lots kan endre pressure 3-5%

**Hvordan måle:**
1. Uniform flash hole og primer pocket
2. Vei tom case
3. Fyll med H2O til flush with case mouth
4. Vei igjen
5. Differanse = H2O capacity
6. Dokumenter i database

**Typical values:**
- 6.5 Creedmoor: 52-53gr H2O
- .308 Winchester: 53-55gr H2O
- .223 Remington: 28-31gr H2O

### Neck Thickness
**Hvorfor dette er viktig:**
- Biggest factor i bullet tension consistency!
- Tension påvirker ES/SD (extreme spread / standard deviation)
- Variasjon >0.002" = problematisk

**Hvordan måle:**
1. Bruk ball micrometer eller tubing micrometer
2. Mål 4 steder rundt neck (90° intervals)
3. Dokumenter thickest og thinnest
4. Hvis variance >0.002", consider neck turning

**Interpretation:**
- Lapua: Typisk 0.014" ±0.0005" (excellent!)
- Peterson: ~0.015" ±0.001" (very good)
- Winchester/Federal: 0.012-0.016" (variable, consider sorting)

## Integration with Other Modules

### QuickLOAD Pressure Estimator (P2)
Brass Manager data feeds:
- Case capacity → Load density calculation
- Case head expansion → Pressure correlation
- Primer condition → Pressure sign detection

### True BC Calculator (P3)
Links to brass tracking:
- Consistent brass = consistent results
- Weight variance affects BC measurements
- Neck tension affects BC (muzzle velocity variance)

### Rifle Profile Editor
Links firing_log to rifle_id:
- Spor hvilke rifles bruker hvilke brass lots
- Rifle-specific pressure signs
- Barrel life correlation

## Keyboard Shortcuts
- **Ctrl+N** - Nytt hylse-lot
- **Ctrl+F** - Logg firing
- **Ctrl+A** - Logg annealing
- **Ctrl+P** - Logg prep
- **Ctrl+M** - Legg til måling
- **Delete** - Retirer selected cases
- **F5** - Refresh table
- **Enter/Double-click** - View details

## Future Enhancements

### Phase 2 (Not Yet Implemented)
- **QR Code Generation**: Print labels for case boxes
- **Annealing Schedule Alerts**: Desktop notifications
- **Case Lifecycle Visualization**: Chart showing firing history, annealing, measurements
- **Batch Comparison**: Compare multiple lots side-by-side
- **Export to CSV/Excel**: For external analysis
- **Import from other tools**: LabRadar, GRT, etc.

### Phase 3 (Future)
- **ML-Based Retirement Prediction**: AI predicts when to retire based on measurements
- **Optimal Annealing Schedule**: ML determines best annealing frequency for your loads
- **Pressure Correlation**: Auto-correlate case head expansion with velocity/primer signs
- **Image Recognition**: OCR for lot numbers, photo documentation of primer condition

## Troubleshooting

### Database Migration
If you have existing database, run:
```sql
-- Add new columns to cases table
ALTER TABLE cases ADD COLUMN lot_number TEXT;
ALTER TABLE cases ADD COLUMN purchase_date TEXT;
ALTER TABLE cases ADD COLUMN case_capacity_gr_h2o REAL;
ALTER TABLE cases ADD COLUMN avg_weight_gr REAL;
ALTER TABLE cases ADD COLUMN wall_thickness TEXT;
ALTER TABLE cases ADD COLUMN neck_thickness_mm REAL;
ALTER TABLE cases ADD COLUMN retired_quantity INTEGER DEFAULT 0;
ALTER TABLE cases ADD COLUMN last_trimmed_date TEXT;
ALTER TABLE cases ADD COLUMN trim_length_mm REAL;
ALTER TABLE cases ADD COLUMN primer_pocket_uniformed BOOLEAN DEFAULT 0;
ALTER TABLE cases ADD COLUMN flash_hole_deburred BOOLEAN DEFAULT 0;

-- Create new tables (see database.py for full DDL)
```

### Common Issues
**Q: Times fired ikke incrementer?**
A: Sjekk at du bruker "🔥 Logg Skyting" button, ikke manual edit

**Q: Annealing alert vises ikke?**
A: Flagget setter hver 3. firing. Sjekk `annealing_due` column i database.

**Q: Case head expansion measurements virker feil?**
A: Må måles i inches! 0.0002" er 0.005mm (5 microns)

## Technical Details

### Foreign Key Cascade
Alle related tables har `ON DELETE CASCADE`:
- Sletter du et case lot, slettes også:
  - case_measurements
  - case_firing_log
  - case_annealing_log
  - case_prep_log

### Performance
- SQLite indexes på `case_id`, `firing_date`, `annealing_date`, `prep_date`
- Queries optimized for <50ms response time
- Table view updates async for large datasets (1000+ lots)

### Data Privacy
All data er lokal SQLite - ingen cloud sync (ennå).

## Links
- [REALISTIC_MEASURABLE_DATA_ANALYSIS.md](REALISTIC_MEASURABLE_DATA_ANALYSIS.md) - Data analysis guide
- [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) - Full roadmap

---

**Version:** 1.0  
**Last Updated:** 2025-01-25  
**Status:** ✅ Database foundation complete, GUI implemented, integrated in workflow_hub
