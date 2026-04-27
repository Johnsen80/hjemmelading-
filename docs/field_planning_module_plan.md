# Field Planning Module — Technical Plan

Updated: 2026-04-20
Status: Planning — not yet built

## Vision

One module that combines weapon profile data, learned ballistic data, live terrain and weather,
and produces the most physically accurate field solution available in any civilian ballistic
application. More precise than Applied Ballistics, Hornady 4DOF, or Kestrel because it uses
*your measured data* — not factory tables.

---

## Module Overview

```
FieldPlanningModule (QMainWindow or QDialog)
├── WeaponAmmoPanel          — weapon + ammo selection, zero correction
├── DopeCardPanel            — printable DOPE card from profile + conditions
└── FieldMapPanel (QTabWidget)
    ├── RangeTab             — shooting range planning
    └── HuntingTab           — hunting post + sector safety analysis
```

All three panels share one `FieldSession` context object that holds the active weapon,
ammo, conditions, and map state.

---

## File Structure (new files)

```
src/
├── field_planning/
│   ├── __init__.py
│   ├── models.py                — FieldSession, LayeredAtmosphere, TerrainSegment,
│   │                              TrajectoryVisualization, MonteCarloResult,
│   │                              HuntingSector, BackstopAnalysis, RangeTarget
│   ├── services.py              — orchestration: build_field_solution(), build_dope_from_profile()
│   ├── atmosphere.py            — LayeredAtmosphereBuilder, radiosonde fetch, Frost API
│   ├── terrain_classifier.py   — classify terrain along shot path from OSM/AR5 landuse
│   ├── backstop_analyzer.py    — safety analysis: bullet path vs terrain, habitation distance
│   ├── monte_carlo.py          — Monte Carlo dispersion with MV SD and BC uncertainty
│   ├── cdm_calibrator.py       — derive custom drag curve from multi-range drop measurements
│   └── weather_history.py      — Frost API (met.no) + session-based weather history

src/ui/
├── field_planning_window.py    — main QMainWindow
├── weapon_ammo_panel.py        — weapon + ammo selection + zero shift
├── dope_card_panel.py          — DOPE card display + print
├── field_map_panel.py          — map tab container
├── range_tab.py                — shooting range map + target markers + click table
├── hunting_tab.py              — hunting post + sector polygon + backstop overlay
├── bullet_journey_widget.py    — THE visualization: side view + top view + graphs
└── atmosphere_layer_widget.py  — show atmospheric layers with warnings

src/utils/
└── ballistics_profile_bridge.py — extract BallisticInput from weapon profile + learning data
```

---

## Core Data Models (`field_planning/models.py`)

### FieldSession
```python
@dataclass
class FieldSession:
    rifle_id: int
    rifle_name: str
    barrel_configuration_id: str | None
    ammo_profile_id: int | None
    # From load learning
    learned_mv_fps: float           # calibrated from chrono sessions
    learned_mv_sd_fps: float        # actual SD from chrono sessions
    learned_bc: float               # back-calculated from drop measurements
    learned_bc_type: str            # "G7" or "CDM"
    mv_temperature_curve: list[tuple[float, float]]  # [(temp_c, mv_fps), ...]
    cold_bore_offset_moa: float     # learned cold bore correction
    # Weapon physical data
    twist_rate: float
    twist_direction: str
    sight_height_mm: float
    zero_distance_m: float
    latitude_deg: float             # from saved shooting location or GPS
    # Active conditions
    atmosphere: LayeredAtmosphere
    weather_source: str             # "live_yr", "manual", "cached"
```

### LayeredAtmosphere
```python
@dataclass
class AtmosphereLayer:
    altitude_m: float               # base altitude of this layer
    temperature_c: float
    pressure_hpa: float
    humidity_pct: float
    wind_speed_mps: float
    wind_dir_deg: float
    density_ratio: float            # relative to ICAO standard
    density_altitude_m: float
    source: str                     # "surface", "radiosonde", "lapse_rate_estimate"

@dataclass
class LayeredAtmosphere:
    layers: list[AtmosphereLayer]   # sorted by altitude, at least 1 (surface)
    inversion_detected: bool
    inversion_altitude_m: float | None
    thermal_risk_level: str         # "low", "moderate", "high"
    surface_type_primary: str       # "rock", "water", "swamp", "forest", "snow", "field"
    katabatic_risk: bool            # cold air pooling in valley likely
```

### TerrainSegment
```python
@dataclass
class TerrainSegment:
    start_m: float                  # distance along shot path
    end_m: float
    surface_type: str               # "rock", "water", "swamp", "forest", "snow", "field", "urban"
    elevation_m: float              # mean terrain height in segment
    thermal_contribution: str       # "none", "low", "moderate", "high"
    wind_factor: float              # multiplier on reported wind (Venturi/sheltering)
    ricochet_risk: bool             # flat surface + shallow angle
```

### EnrichedTrajectoryPoint (extends existing TrajectoryPoint)
```python
@dataclass
class EnrichedTrajectoryPoint:
    # All fields from existing TrajectoryPoint
    distance_m: float
    time_s: float
    velocity_fps: float
    mach: float                     # NEW: velocity / speed_of_sound at this point
    drop_cm: float
    drop_moa: float
    windage_cm: float
    windage_moa: float
    energy_ftlbs: float
    energy_joules: float            # NEW
    stability_sg: float             # NEW: gyroscopic stability factor at this point
    phase: str                      # NEW: "supersonic", "transonic", "subsonic"
    # Terrain context at this point
    segment: TerrainSegment | None
    atmosphere_layer: AtmosphereLayer  # layer active at bullet altitude
    # For visualization
    bullet_altitude_m: float        # actual height above sea level at this point
    height_above_ground_m: float    # clearance above terrain
```

### MonteCarloResult
```python
@dataclass
class MonteCarloResult:
    iterations: int                 # typically 10_000
    cep50_cm: float                 # 50% of shots within this radius
    cep90_cm: float
    cep99_cm: float
    vertical_sd_cm: float
    horizontal_sd_cm: float
    mv_contribution_cm: float       # how much MV SD contributes
    bc_contribution_cm: float       # how much BC uncertainty contributes
    wind_contribution_cm: float     # how much wind uncertainty contributes
    impact_points: list[tuple[float, float]]  # (x, y) offsets in cm, for scatter plot
```

### HuntingSector
```python
@dataclass
class HuntingPost:
    position: GeoPoint
    max_effective_range_m: float    # max ethical kill range for selected game
    min_kill_energy_j: float        # ethical threshold for selected game type

@dataclass
class HuntingSector:
    post: HuntingPost
    polygon: list[GeoPoint]         # kill sector boundary
    known_points: list[GeoPoint]    # marked aim points within sector
    game_type: str                  # "deer", "moose", "small_game", etc.

@dataclass
class BackstopAnalysis:
    point: GeoPoint
    bearing_deg: float
    slant_range_m: float
    # Bullet path analysis
    ground_intersection_m: float | None  # where bullet hits ground (None = no hit in range)
    max_ordinate_m: float           # highest point of bullet above ground
    bullet_energy_at_ground_j: float
    bullet_velocity_at_ground_fps: float
    is_subsonic_at_ground: bool
    # Habitation check
    nearest_habitation_m: float | None
    nearest_habitation_bearing_deg: float | None
    # Safety verdict
    verdict: str                    # "safe", "caution", "unsafe"
    verdict_reason: str
    # Color for map overlay
    color: str                      # "green", "orange", "red"
```

---

## Key Algorithms

### 1. Build BallisticInput from weapon profile + learning

**File**: `src/utils/ballistics_profile_bridge.py`

```python
def build_ballistic_input_from_profile(
    db: Database,
    rifle_id: int,
    ammo_profile_id: int | None,
    session: FieldSession,
) -> BallisticInput:
    """
    Priority chain (highest wins):
    1. Learned BC from cdm_calibrator (if multi-range drops exist)
    2. Learned BC back-calculated from single drop measurement
    3. BC from ammo_profile (db)
    4. G7 BC from bullet library
    """
```

Priority chain ensures we always use the best data available.

### 2. Multi-layer trajectory solve

**File**: `src/field_planning/services.py`

Split trajectory into segments matching atmospheric layers:
```
Segment 0–400m:   layer = surface (temp=8°C, press=1008hPa, wind=1m/s NW)
Segment 400–800m: layer = mid (temp=2°C, press=960hPa, wind=4m/s W)
Segment 800m+:    layer = upper (temp=-3°C, press=920hPa, wind=6m/s W)
```

Each segment uses the layer-correct density altitude for drag computation.
Pass exit velocity of one segment as entry velocity of next.

### 3. Terrain classifier along shot path

**File**: `src/field_planning/terrain_classifier.py`

1. Interpolate 20 sample points along GeoShot path
2. Query OSM Overpass API for land use at each point (or use cached AR5 data)
3. Query Kartverket elevation at each point
4. Classify each segment: surface_type, thermal_risk, wind_factor, ricochet_risk
5. Return list[TerrainSegment]

**Offline fallback**: If no network, use elevation-only analysis (valley detection, slope angle)

### 4. Monte Carlo dispersion

**File**: `src/field_planning/monte_carlo.py`

```python
def run_monte_carlo(
    base_input: BallisticInput,
    scenario: ShotScenario,
    atmosphere: LayeredAtmosphere,
    mv_sd_fps: float,
    bc_uncertainty_pct: float = 0.02,   # 2% BC uncertainty default
    wind_uncertainty_mps: float = 0.5,  # ±0.5 m/s wind uncertainty
    iterations: int = 10_000,
) -> MonteCarloResult:
```

Vary MV (normal dist around learned MV, SD from chrono data), BC (±2%), wind speed
(±0.5 m/s). Run full trajectory for each. Collect impact points. Compute CEP.

### 5. Gyroscopic stability Sg along trajectory

```python
def compute_sg(
    bullet_diameter_mm: float,
    bullet_length_mm: float,
    bullet_mass_gr: float,
    twist_rate_in: float,           # inches per turn
    velocity_fps: float,
    density_ratio: float,
) -> float:
    """Miller stability formula. Sg < 1.0 → unstable. Sg > 1.4 → optimal."""
    twist_m = twist_rate_in * 0.0254
    d = bullet_diameter_mm / 1000
    m = bullet_mass_gr * 0.0000648
    l = bullet_length_mm / 1000
    v = velocity_fps * 0.3048
    # Miller: Sg = (30 * m) / (density_ratio * d^3 * l * (1 + l²/d²)) * (v / twist_m)²
```

### 6. CDM calibration from drop measurements

**File**: `src/field_planning/cdm_calibrator.py`

Given measured drops at 3+ ranges, back-solve BC at each range using bisection search.
Fit a Mach-based drag multiplier curve. Use this instead of G1/G7 at runtime.

### 7. Backstop safety analysis

**File**: `src/field_planning/backstop_analyzer.py`

For each point in HuntingSector:
1. Compute bearing from post to point
2. Extend bearing past point by `max_bullet_range_m` (where energy < 10J or ground hit)
3. Sample elevation profile along extended line (every 50m)
4. Find first terrain intersection with bullet trajectory arc
5. If no ground hit within 8km: query OSM for buildings along line
6. If building within line-of-sight: verdict = "unsafe"
7. If energy at ground > 100J: verdict = "caution"
8. Else: verdict = "safe"

---

## Bullet Journey Widget (`src/ui/bullet_journey_widget.py`)

Three synchronized panels using `pyqtgraph` (already a dependency):

### Panel 1: Side view (elevation cross-section)
- X axis: distance (m)
- Y axis: height (m above sea level)
- Drawn elements:
  - Terrain profile (brown fill)
  - Bullet trajectory arc (colored by phase: green/yellow/red)
  - Atmospheric layer boundaries (dashed horizontal lines)
  - Max ordinate marker
  - Zero crossing marker
  - Transonic boundary marker (vertical dashed line)
  - Subsonic boundary marker (vertical dashed line)
  - Monte Carlo CEP band (semi-transparent vertical bars every 100m)

### Panel 2: Top view (horizontal drift)
- X axis: distance (m)
- Y axis: lateral deviation (cm)
- Drawn elements:
  - Wind drift line
  - Spin drift line
  - Coriolis drift line
  - Combined drift (total, thick line)
  - MOA grid overlay

### Panel 3: Data graphs (synchronized cursor)
Four sub-graphs stacked vertically, all sharing X axis (distance):
1. **Velocity**: fps + Mach number, with Mach 1.0 line highlighted
2. **Energy**: joules + ft-lbs, with game-specific ethical threshold line
3. **Stability Sg**: with warning band below 1.4, danger band below 1.0
4. **Drag coefficient**: if CDM available, show actual Cd vs Mach

**Cursor**: click anywhere on side view → vertical cursor line appears on all panels
with popup showing all values at that distance.

---

## Weather History (`src/field_planning/weather_history.py`)

### Sources (priority order):
1. **Own session history** (best — your weapon, your conditions):
   - Query `chronograph_sessions` WHERE temperature within range, grouped by month
   - Shows: "You have shot here under similar conditions 4 times. Avg MV: 832 m/s"
2. **Frost API** (met.no historical climate, free Norwegian API):
   - Endpoint: `https://frost.met.no/observations/v0.jsonld`
   - Data: monthly normals for nearest station (temp, pressure, wind)
   - Cache locally, refresh monthly
3. **Yr.no forecast** (already implemented): live + 48h

### Weather history panel shows:
- Monthly temperature/pressure/wind chart for selected location
- "Conditions today vs historical average"
- Highlight if today is anomalous (inversion risk, unusually warm/cold)

---

## Map Technology Stack

### Tile layers (switchable in UI):
| Layer | Source | Purpose |
|-------|--------|---------|
| Topo (default) | Kartverket WMS `https://wms.kartverket.no/...` | Terrain, elevation lines |
| Satellite | ESRI ArcGIS World Imagery (free) | Visual identification |
| Street/OSM | OpenStreetMap | Buildings, roads, habitation |

### Elevation data:
- **Kartverket høydemodell** (primary, Norway): 1m resolution DTM
  - API: `https://ws.geonorge.no/hoydedata/v1/punkt`
- **OpenTopo SRTM** (fallback, global): already partially used

### Habitation/buildings:
- **Overpass API** (OSM): query `building=*` within radius of shot line
- Cache results locally (buildings don't move)

### Offline support:
- Use existing `tools/offline_map_cache.py`
- Pre-download tiles + elevation + building data for selected area
- "Download for offline use" button in map header

---

## UI Layout Detail

### Main window structure:
```
┌──────────────────────────────────────────────────────────────────┐
│ [Velg våpen ▼]  [Velg ammo/batch ▼]  [Zero-korreksjon: +2.3 klikk ↑]│
├─────────────────────────┬────────────────────────────────────────┤
│ DOPE-KORT               │  FELT-KART                             │
│                         │  [Skytebane] [Jakt]                    │
│ Avstand | Klikk | MOA   │                                        │
│ 100m    |  0    | 0.0   │  [Kart widget — Folium/Leaflet]        │
│ 200m    | +2.1  | +2.1  │                                        │
│ 300m    | +5.8  | +5.8  │  Verktøylinje: [📍Standplass]         │
│ 500m    | +14.2 | +14.2 │              [🎯 Mål] [📐 Sektor]     │
│ 800m    | +31.7 | +31.7 │              [⬇️ Last ned offline]     │
│ 1000m   | +46.2 | +46.2 │                                        │
│         │               │  Analysepanel (under kart):            │
│ [📄 PDF]│               │  [Terreng] [Atmosfære] [Bakstop]       │
├─────────────────────────┴────────────────────────────────────────┤
│ KULENS REISE                                                      │
│ [Side-visning]══════════════════════════════════════════════════ │
│ [Topp-visning]══════════════════════════════════════════════════ │
│ [Hastighet / Energi / Sg]                                        │
└──────────────────────────────────────────────────────────────────┘
```

### Hunting tab additions:
- Draw polygon tool for kill sector
- Per-point backstop overlay (green/orange/red dots)
- Game type selector (Elg, Hjort, Rådyr, etc.) → sets min energy threshold
- "Sikkerhetsrapport" button → PDF with full backstop analysis per sector point
- "Nærmeste bebyggelse: 847m NØ" info box

### Warning system (shown as banners above map):
```
⚠️  Temperaturinversjon sannsynlig (klar natt, vindstille, dal -90m lavere)
    → Subsonic-terskel ~140m nærmere enn standard. Ikke skyt >1180m.

⚠️  Termikk-risiko HØYT (sol, granitt >400m i skuddlinje, kl. 13:00)
    → Forventet vertikal spredning +18–28 cm ved 1200m.
    → Beste skytetid: 06:00–09:00 eller overskyet.

ℹ️  Luftfuktighet 72% (myr 280–620m i skuddlinje)
    → Lufttetthet 1.8% lavere enn standard. Kompensert i beregningen.

✅  Coriolis: -0.4 MOA venstre (skuddretning 127°, breddegrad 61.2°N)
✅  Spindrift: +7.2 cm høyre ved 1000m (HH, 1:8 twist)
```

---

## Dataflyt — komplett

```
Rifleprofil (DB)
├── twist_rate, sight_height, zero_distance
└── barrel_configuration_id

Ammo-profil (DB) + batch-læring
├── Kalibrert BC (fra drop-målinger) ──────────────────────┐
├── Gjennomsnittlig MV + faktisk SD (fra chrono-sesjoner)  │
├── MV(T)-kurve (lært fra sesjoner ved ulike temp)         │
└── Cold bore offset (lært)                                │
                                                           ▼
Kartposisjon (klikk på kart / GPS)              BallisticInput
├── GeoShot (standplass + mål)                  (kalibrert, ikke fabrikkdata)
├── GeoSolution (slant range, helning, bearing)            │
└── Terreng-profil (Kartverket høydemodell)                │
                                                           ▼
LayeredAtmosphere                              AdvancedBallisticsEngine
├── Surface: Yr.no live                        (per segment med riktig layer)
├── Aloft: Radiosonde (met.no) / lapse rate                │
├── Terrengklassifisering (OSM AR5)                        ▼
└── Historisk: Frost API                       EnrichedTrajectoryPoint[]
                                                           │
                                               ┌───────────┼───────────┐
                                               ▼           ▼           ▼
                                          MonteCarloResult  BulletJourney  BackstopAnalysis
                                          (CEP per avstand) (visualisering) (sikkerhetsfarger)
                                               │                           │
                                               ▼                           ▼
                                          DOPE-kort                   Kart-overlay
                                          (klikk + CEP)               (grønn/gul/rød)
```

---

## Byggerekkefølge (8 blokker)

### Blokk 1: Datafundament
- `ballistics_profile_bridge.py` — hent lært BC/MV fra profil
- `field_planning/models.py` — alle dataklasser

### Blokk 2: Basis feltløsning
- Enkel `build_field_solution()` med én atmosfærelag
- DOPE-kort fra profil med kalibrerte data
- Zero-korreksjon panel

### Blokk 3: Kulens reise — visualisering
- `bullet_journey_widget.py` — side + topp + grafer
- Mach/fase-farging, Sg-kurve, energi-kurve

### Blokk 4: Atmosfærelag + terrenganalyse
- `atmosphere.py` — multi-lag, lapse rate estimat
- `terrain_classifier.py` — OSM-oppslag, overflate-klassifisering
- Varselmotor (inversjon, termikk, fuktighet)

### Blokk 5: Monte Carlo
- `monte_carlo.py` — 10 000 iterasjoner
- CEP-band i visualisering
- "Din ammo gir X cm ved Y m" tekst

### Blokk 6: Skytebane-kart
- `range_tab.py` — kart med standplass + mål-markering
- Klikk-tabell per mål med slant-korreksjon
- Atmosfære + terrenganalyse-panel

### Blokk 7: Jakt-modul
- `hunting_tab.py` — post + sektorpolygon
- `backstop_analyzer.py` — sikkerhetskalkulator
- Farge-overlay på kart, sikkerhetsrapport PDF

### Blokk 8: Vær og historikk
- `weather_history.py` — Frost API + session-historikk
- Radiosonde-integrasjon (met.no)
- CDM-kalibrering fra multi-range data

---

## Avhengigheter (nye)

```
requests          — allerede tilgjengelig
folium            — allerede tilgjengelig
pyqtgraph         — allerede tilgjengelig (brukes i ballistics_simulator)
numpy             — allerede tilgjengelig
scipy             — for Monte Carlo + CDM fitting (legg til requirements)
```

Ingen nye tunge avhengigheter. Appen forblir offline-kapabel.

---

## Presisjonsnivå vs. konkurrentene

| Funksjon | Hornady 4DOF | Applied Ballistics | Denne |
|---------|-------------|-------------------|-------|
| Drag-modell | G1/G7/4DOF | CDM (målt) | CDM kalibrert mot ditt våpen |
| MV-kilde | Manuell input | Manuell input | Lært fra dine chrono-sesjoner |
| BC-kilde | Fabrikkdata | Radarmålt (for kjente kuler) | Back-kalkulert fra dine drop-målinger |
| Atmosfære | Enkelt-lag | Enkelt-lag | Multi-lag (radiosonde) |
| Terreng | Ingen | Ingen | Overflate-termikk + dal-inversjon |
| Dispersjon | Punkt-estimat | Punkt-estimat | Monte Carlo CEP med ditt faktiske SD |
| Vær-historikk | Ingen | Ingen | Frost API + egne sesjoner |
| Jakt-sikkerhet | Ingen | Ingen | Backstop + bebyggelsesanalyse |
| Visualisering | Tabell | Tabell | 3-panel kulereise med alle fysiske parametre |

---

## Neste steg

Klar til å starte på Blokk 1.
Se `docs/load_module_finish_todo.md` for modell på hvordan vi tracker framdrift.
