# 📊 REALISTISKE MÅLBARE DATA FOR HJEMMELADERE
## Grundig Analyse av Data-Innsamling og Fysikk

---

## 🎯 MÅLSETTING
Definere hvilke data en hjemmelader **realistisk kan måle** med vanlig tilgjengelig utstyr, og hvordan disse dataene brukes for å estimere **indre ballistikk** (trykk, forbrenning) og **ytre ballistikk** (trajectory, BC, drift).

---

## 📐 1. MÅLBARE DATA MED STANDARD UTSTYR

### 🔴 TIER 1: GRUNNLEGGENDE (Alle kan måle)

#### **A. Skyvelære / Digital Caliper**
**Hva kan måles:**
- ✅ **COAL (Cartridge Overall Length)**: 0.01mm presisjon
- ✅ **CBTO (Cartridge Base to Ogive)**: Med bullet comparator, 0.01mm presisjon
- ✅ **Case Length**: Hylselengde, kritisk for safety (0.01mm)
- ✅ **Neck Diameter (loaded)**: Indikerer neck tension (0.01mm)
- ✅ **Case Base Diameter**: FØR og ETTER skyting for trykk-indikasjon (0.001mm nødvendig!)
- ✅ **Case Shoulder Diameter**: Før/etter sizing (0.01mm)
- ✅ **Bullet Diameter**: QC check av kuler (0.001mm med micrometer)
- ✅ **Primer Seating Depth**: Med depth gauge (0.01mm)

**Fysikk-relevans:**
- Case measurements → Chamber clearance → **ES/SD estimering**
- Neck diameter → Neck tension → **Start trykk + burning consistency**
- CBTO → Freebore jump → **Peak pressure timing + accuracy**

**Anbefalt utstyr:**
- Mitutoyo/Starrett digital caliper (±0.01mm)
- Hornady bullet comparator kit
- Sinclair expander mandrels (known neck tension)

---

#### **B. Vekt / Powder Scale**
**Hva kan måles:**
- ✅ **Powder charge weight**: 0.01gr presisjon (kritisk!)
- ✅ **Bullet weight**: Sort bullets by weight (0.1gr variance = BC variance)
- ✅ **Brass weight**: Indikerer case capacity variance (±1gr = ±0.2gr H2O)
- ✅ **Loaded ammo weight**: QC check (should be consistent within 0.5gr)

**Fysikk-relevans:**
- Powder charge → **Direkte trykk + hastighet**
- Bullet weight variance → **BC variance + SD**
- Brass weight → Case capacity → **Load density + pressure**

**Anbefalt utstyr:**
- RCBS Chargemaster (±0.1gr auto-dispense)
- A&D FX-120i (±0.02gr laboratorium precision)
- GemPro 250 (±0.04gr budget option)

---

#### **C. Hornady OAL Gauge / Split Case Method**
**Hva kan måles:**
- ✅ **Ogive to lands (jam length)**: 0.01mm presisjon
- ✅ **Freebore per bullet type**: Different ogives = different jump!
- ✅ **Throat erosion tracking**: Re-measure every 500 rounds

**Fysikk-relevans:**
- Jump to lands → **Peak pressure timing**
- Too little jump (<0.010") → **Pressure spike!**
- Too much jump (>0.060") → **Inconsistent ignition, high ES**
- Throat erosion → Freebore increases → Lower pressure over barrel life

**Anbefalt utstyr:**
- Hornady OAL gauge + modified case
- Sinclair bore gauge (for throat wear)

---

### 🟠 TIER 2: ENTHUSIAST (Investering 5000-15000 kr)

#### **D. Chronograph (Hastighetsmåling)**
**Hva kan måles:**
- ✅ **Muzzle velocity (fps/ms)**: ±2 fps presisjon med moderne units
- ✅ **ES (Extreme Spread)**: Max - Min velocity i serie
- ✅ **SD (Standard Deviation)**: Statistisk spredning
- ✅ **Shot-to-shot consistency**: Graf av velocity over time

**Fysikk-relevans:**
- Velocity → **Peak pressure estimate** (via QuickLOAD correlation)
- ES/SD → **Powder burning consistency + neck tension quality**
- Low SD (<10 fps) = tight ES, good brass prep, consistent powder
- High SD (>15 fps) = variance in ignition, neck tension, or charge weight

**Anbefalt utstyr:**
- **LabRadar**: Doppler, tracks velocity downrange, ±1 fps
- **MagnetoSpeed V3**: Barrel-mounted, ±0.5%, blocks POI
- **Garmin Xero C1 Pro**: Newest, accurate, expensive

**QuickLOAD Correlation (6.5 Creedmoor, 140gr, H4350):**
```
Charge Weight → Velocity → Estimated Pressure
40.0gr → 2550 fps → 52,000 PSI
41.0gr → 2620 fps → 56,000 PSI (SAAMI max)
42.0gr → 2690 fps → 60,000 PSI (⚠️ OVERPRESSURE!)
43.0gr → 2760 fps → 64,000 PSI (🔴 DANGEROUS!)
```

**Velocity-to-Pressure Rule of Thumb:**
- **+1% velocity = +15% pressure** (non-linear!)
- Example: 2700 fps → 2727 fps (+1%) = 56k PSI → 64k PSI (+15%)
- This is why pressure signs appear suddenly!

---

#### **E. Concentricity Gauge**
**Hva kan måles:**
- ✅ **Bullet runout**: TIR (Total Indicator Reading), ideelt <0.002"
- ✅ **Case neck runout**: Indikerer die alignment issues
- ✅ **Loaded round concentricity**: Affects accuracy drastically

**Fysikk-relevans:**
- Runout → **Bullet enters barrel off-axis → yaw → BC loss**
- >0.003" runout = 0.5-1.0 MOA accuracy penalty
- Affects yaw of repose → spin drift variance

**Anbefalt utstyr:**
- Sinclair concentricity gauge
- RCBS Case Master (cheaper)

---

#### **F. Case Neck Thickness Gauge**
**Hva kan måles:**
- ✅ **Neck wall thickness**: Check uniformity around circumference
- ✅ **Variance detection**: ±0.001" variance = neck turning needed
- ✅ **Neck tension consistency**: Thicker wall = more spring-back

**Fysikk-relevans:**
- Uneven neck thickness → **Asymmetric bullet release → yaw**
- Thick neck + tight chamber → **Pressure spike + accuracy loss**
- Neck turned brass → Lower ES/SD

**Anbefalt utstyr:**
- Sinclair neck thickness gauge (ball bearing type)
- 21st Century Shooting neck turning tool

---

### 🟢 TIER 3: ADVANCED (Investering 15000-50000 kr)

#### **G. Pressure Trace System (FAKTISK TRYKK!)**
**Hva kan måles:**
- ✅ **Peak pressure (PSI)**: Strain gauge på hylsen
- ✅ **Pressure curve shape**: Ser powder burning rate
- ✅ **Time to peak pressure**: Faster peak = sharper pressure spike
- ✅ **Pressure integral**: Total arbeid på kulen

**Fysikk-relevans:**
- **DETTE ER GULLSTANDARDEN** - faktisk trykkdata!
- Pressure Trace II kit (~$500 USD) gir PSI curves
- Ser forskjell på primer types, powder types, seating depth
- Validerer QuickLOAD estimater

**Eksempel data (6.5 CM, 41gr H4350, 140gr):**
```
Pressure Trace Output:
- Peak Pressure: 58,240 PSI @ 1.14ms
- Muzzle Pressure: 8,420 PSI @ 1.82ms
- Port Pressure: 4,210 PSI @ 2.15ms (for gas gun tuning)
- Barrel time: 1.82ms
```

**Anbefalt utstyr:**
- Pressure Trace II (~$500 USD)
- RSI Pressure Testing (send ammo, get data)

---

#### **H. Annealing Machine + Templaq**
**Hva kan måles:**
- ✅ **Neck hardness**: Vickers hardness test (requires lab)
- ✅ **Annealing temperature**: Templaq paint (450°F, 650°F, 750°F)
- ✅ **Annealing consistency**: Color change uniformity

**Fysikk-relevans:**
- Annealed brass → **Consistent neck tension → Lower ES/SD**
- Work-hardened brass → Brittle → Splits + inconsistent release
- AMP Annealer (~$1500) = perfect anneal every time

**Anbefalt utstyr:**
- AMP Annealer Mark II (~$1500)
- Annie Induction Annealer (~$400)
- Templaq paint sticks (temp verification)

---

#### **I. Barrel Borescope**
**Hva kan måles:**
- ✅ **Throat erosion**: Visual inspection
- ✅ **Carbon fouling**: Affects pressure + velocity
- ✅ **Copper fouling**: Check cleaning effectiveness
- ✅ **Heat cracks**: End-of-life indicator

**Fysikk-relevans:**
- Fouling → **Reduced bore diameter → Higher pressure**
- Throat erosion → **Longer freebore → Lower pressure over barrel life**
- Carbon ring @ 1-2" → Pressure spike if not cleaned

**Anbefalt utstyr:**
- Teslong borescope (~$100-300)
- Hawkeye digital borescope (~$500)

---

## 🔬 2. INDRE BALLISTIKK - HVA KAN ESTIMERES?

### **A. Trykk (PSI) - IKKE DIREKTE MÅLBART (uten Pressure Trace)**

#### **Metode 1: QuickLOAD Software**
**Input data:**
- Caliber, case capacity (H2O grains)
- Bullet weight, length, bearing surface
- Powder type, charge weight
- COAL/CBTO, case fill %
- Barrel length, twist rate

**Output:**
- Peak pressure (PSI)
- Muzzle velocity (fps)
- Muzzle pressure (PSI)
- Barrel time (ms)
- Powder burning % at bullet exit

**Nøyaktighet:**
- ±5% velocity if inputs correct
- ±10% pressure (conservative)
- **MUST true with chronograph data!**

**Eksempel (6.5 Creedmoor, Lapua brass, 140gr ELD-M, H4350):**
```
QuickLOAD Input:
- Case capacity: 52.5gr H2O (Lapua)
- Charge: 41.0gr H4350
- COAL: 70.6mm (0.020" jump)
- Barrel: 610mm (24")
- Primer: CCI 200

QuickLOAD Output:
- Peak Pressure: 56,120 PSI (SAAMI max = 62,000)
- Muzzle Velocity: 2,710 fps
- Barrel Time: 1.24ms
- Powder Burn %: 97.8% @ exit
```

**True velocity med chronograph:**
```
Actual Velocity: 2,695 fps
QuickLOAD estimated: 2,710 fps
Difference: -15 fps (-0.5%)
→ Adjust QuickLOAD case capacity: 52.5gr → 53.2gr
→ Re-run → 2,695 fps match!
→ Now pressure estimate is accurate
```

---

#### **Metode 2: Pressure Signs (Qualitative, ikke PSI)**
**Visual indicators:**
- ✅ **Flattened primers**: Soft indicator, can be false positive
- ✅ **Cratered primers**: Firing pin hole too big, not always pressure
- ✅ **Ejector mark**: **STRONG** pressure indicator (>65k PSI)
- ✅ **Extractor swipe**: Case rotating in chamber (pressure)
- ✅ **Sticky bolt lift**: Case stuck in chamber (high pressure + carbon)
- ✅ **Case head expansion**: **BEST NON-PRESSURE TRACE INDICATOR**

**Case Head Expansion - Kvantitativt!**
```
Measure case head (0.200" from base) before and after firing:

Before firing: 12.010mm
After firing:  12.015mm
Expansion:     0.005mm (0.0002")

Pressure estimate:
- 0.0001-0.0002" = 55-60k PSI (safe)
- 0.0003-0.0004" = 60-65k PSI (max)
- 0.0005"+ = >65k PSI (OVERPRESSURE!)
```

**Hvorfor case head expansion fungerer:**
- Brass yields @ ~40k PSI
- Higher pressure → More case stretching
- Case base is thickest part, so minimal stretch = high pressure
- Requires precision caliper (±0.001mm) or ball micrometer

---

#### **Metode 3: Velocity-to-Pressure Correlation**
**Using empirical data from reloading manuals:**

**6.5 Creedmoor (140gr, 24" barrel) - Hodgdon Data:**
```
H4350 Charge → Velocity → Estimated PSI
38.0gr (min)  → 2,488 fps → 47,500 PSI
40.0gr        → 2,621 fps → 54,000 PSI
41.5gr (max)  → 2,726 fps → 62,000 PSI (SAAMI)
```

**Interpolation for your load:**
```
Your chrono data: 2,680 fps with 41.0gr

Linear interpolation:
2,680 fps falls between 2,621 (54k) and 2,726 (62k)
→ (2,680 - 2,621) / (2,726 - 2,621) = 0.56
→ 54,000 + 0.56 * (62,000 - 54,000) = 58,480 PSI

Estimated pressure: ~58,500 PSI (safe, 93% of max)
```

**Caveats:**
- Assumes same components (brass, primer, bullet)
- Barrel length affects velocity (not pressure as much)
- Different lot of powder = different burn rate!

---

### **B. Powder Burning Efficiency**

#### **Load Density % (QuickLOAD)**
**Optimal load density: 85-105%**
- <85% = air space → inconsistent ignition → high ES
- 85-95% = excellent (compressed slightly)
- 95-105% = compressed (good, but watch COAL)
- >105% = dangerous compressed (case bulging)

**Example (6.5 CM, H4350, 140gr):**
```
Case capacity: 52.5gr H2O
Charge: 41.0gr H4350

Load density = (41.0 / 52.5) * (powder density factor) ≈ 95%
→ Excellent density, consistent ignition
```

#### **Muzzle Flash & Unburnt Powder**
**Visual inspection:**
- Large muzzle flash = unburnt powder exiting barrel
- Unburnt kernels near target = too slow powder
- Clean burn = optimal powder selection

---

### **C. Ignition Consistency (ES/SD Analysis)**

**Faktorer som påvirker ES/SD:**

#### **1. Neck Tension (biggest factor!)**
```
Loose neck (0.001" tension):
- ES: 25-40 fps (inconsistent bullet release)
- SD: 12-18 fps

Proper neck (0.002-0.003" tension):
- ES: 10-20 fps
- SD: 5-10 fps

Tight neck (0.004"+ tension):
- ES: 30-50 fps (inconsistent start pressure)
- SD: 15-25 fps
```

**Hvordan måle neck tension:**
```
1. Measure loaded round neck OD: 7.42mm
2. Measure bullet diameter: 6.71mm (0.264")
3. Neck tension = (7.42 - 6.71) / 2 = 0.355mm per side
4. Spring-back factor: brass springs back 0.001" typ
5. Effective tension = 0.001-0.002" (ideal)

Better method:
- Use Sinclair mandrels (known size)
- 0.262" mandrel for 0.264" bullet = 0.002" tension
```

#### **2. Powder Charge Consistency**
```
Hand-thrown charges (±0.2gr):
- ES: 20-35 fps
- SD: 10-15 fps

Auto-dispenser (±0.1gr):
- ES: 12-20 fps
- SD: 6-10 fps

Lab-grade (±0.02gr):
- ES: 8-15 fps
- SD: 3-6 fps
```

#### **3. Primer Seating Depth**
```
Proud primer (0.002" high):
- Crushed anvil → inconsistent ignition
- ES: +15-25 fps increase

Proper depth (0.002-0.004" below flush):
- Consistent ignition
- Baseline ES/SD

Too deep (0.006"+):
- Primer compound crushed → DANGER
- Possible slam-fire
```

---

### **D. Barrel Time & Harmonics (OBT Theory)**

#### **Chris Long's Optimal Barrel Time (OBT)**
**Formula:**
```
OBT = (Barrel Length / 10000) * sqrt(Barrel Weight / Stiffness)

For 6.5 CM with 24" MTU contour barrel:
- Length: 610mm
- Weight: 2400g (estimated with contour)
- Stiffness: depends on profile, material

OBT ≈ 1.20ms (calculated)
```

**Node Theory:**
```
Barrel vibrates in sine wave
Nodes occur at: 1.00ms, 1.20ms, 1.40ms, 1.60ms, etc.

If bullet exits at node → vertical dispersion minimized
If bullet exits between nodes → poor vertical

Target velocity for OBT:
Velocity = Barrel Length / OBT
= 610mm / 0.00120s
= 508,333 mm/s
= 1,668 fps (converted)

Wait, that's wrong for muzzle velocity calc...

Actually:
OBT timing affects which powder charge "tunes" best
Ladder test will show velocity nodes where groups shrink
```

**Realistic use:**
- Ladder test: 40.0gr → 42.0gr in 0.3gr increments
- Shoot 3-shot groups at each charge
- Plot group size vs velocity
- "Nodes" appear as velocity windows with small groups
- Example: 2,650-2,680 fps = 0.5 MOA, 2,710-2,730 fps = 1.2 MOA

---

## 🎯 3. YTRE BALLISTIKK - HVA KAN MÅLES/BEREGNES?

### **A. Ballistic Coefficient (BC) - CRITICAL!**

#### **Problem: Book BC vs Real BC**
```
Manufacturer claims: Berger 140gr Hybrid, G7 BC = 0.310

Your actual BC may be:
- 0.295-0.325 depending on:
  - Velocity (BC drops at lower velocity)
  - Altitude (air density affects drag)
  - Temperature
  - Bullet batch variation
  - Muzzle blast/yaw
```

#### **How to Calculate YOUR True BC:**

**Method 1: Velocity loss over distance (requires 2 chronographs)**
```
Setup:
- Chrono 1 @ muzzle: 2,710 fps
- Chrono 2 @ 100m: 2,520 fps
- Distance: 100m

Using G7 drag function:
- Input v0 = 2,710 fps, distance = 100m
- Vary BC until calculated v100m = 2,520 fps
- Result: G7 BC = 0.318 (higher than book!)

This is YOUR rifle's true BC for this load
```

**Method 2: Drop measurement (requires shooting)**
```
Setup:
- Zero @ 100m
- Shoot @ 600m
- Measure drop from 100m zero line

Example:
- Calculated drop (BC 0.310): -250cm @ 600m
- Actual drop measured: -265cm @ 600m
- Drop is 15cm more → BC is lower than 0.310

Adjust BC in ballistic solver until drop matches:
- True BC = 0.298 G7
```

**Method 3: Time of Flight (acoustic target)**
```
Using acoustic target or LabRadar:
- Time of flight @ 600m: 0.78 seconds
- Expected TOF (BC 0.310): 0.76 seconds
- Bullet is slower → BC is lower

Adjust BC: 0.298 G7 gives TOF = 0.78s → Match!
```

---

### **B. Wind Drift**

**Formula:**
```
Wind Drift (cm) = (Wind Speed * TOF * Drag Factor) / (Velocity * BC)

Example (6.5 CM, 140gr, G7 0.310):
- Distance: 600m
- Wind: 10 mph (4.47 m/s) crosswind
- TOF: 0.76 seconds
- Muzzle velocity: 2,710 fps (826 m/s)

Drift ≈ (4.47 * 0.76 * 1.5) / (826 * 0.310) ≈ 20cm

Full-value 10mph wind @ 600m = 20cm drift (0.8 MOA)
```

**Målebare data:**
- Wind speed (Kestrel meter): ±1 mph
- Wind direction (compass + feel)
- **Shot placement vs aim point** → back-calculate true wind effect

---

### **C. Spin Drift**

**Formula (Litz model):**
```
Spin Drift (MOA) = 1.25 * (Stability Factor^1.5) * (TOF^1.8) / 100

For 6.5 CM, 1:8" twist, 140gr @ 2,710 fps:
- Stability Factor (SG): 1.52 (calculated)
- TOF @ 600m: 0.76s

Spin Drift = 1.25 * (1.52^1.5) * (0.76^1.8) / 100
           ≈ 0.45 MOA @ 600m
           ≈ 8cm right drift (right-hand twist)
```

**Målebare data:**
- Shoot in zero wind (or known wind)
- Measure horizontal dispersion
- Subtract wind drift → remaining = spin drift
- Should match calculated value (±2cm)

---

### **D. Coriolis Effect (ELR only, >800m)**

**Formula:**
```
Coriolis Drift = 2 * Omega * TOF * sin(Latitude) * Distance

For Norge (60°N), 1000m shot:
- Omega = 0.00007292 rad/s (Earth rotation)
- TOF = 1.2s
- sin(60°) = 0.866

Coriolis = 2 * 0.00007292 * 1.2 * 0.866 * 1000
         ≈ 0.15m = 15cm right drift

At 1000m, Coriolis = ~0.5 MOA (not negligible!)
```

---

### **E. Gyroscopic Stability (SG)**

**Formula (Miller twist rule):**
```
SG = (Twist Rate / Caliber)^2 * (Velocity / Length)^(1/3) * (Temp / Pressure)^(1/3)

For 6.5 CM, 140gr Hybrid:
- Twist: 1:8" = 8
- Caliber: 0.264"
- Length: 1.430"
- Velocity: 2,710 fps
- Temp: 59°F
- Pressure: 29.92" Hg

SG ≈ 1.52

Interpretation:
- SG < 1.0: Unstable (tumbling)
- SG 1.0-1.5: Marginally stable (BC loss)
- SG 1.5-2.0: Stable (optimal)
- SG > 2.0: Overstabilized (may not tip on target)
```

**Measuring stability:**
- Shoot @ 100m: round holes = stable
- Shoot @ 100m: keyholing = unstable
- Measure BC: if BC < book value → insufficient stability

---

## 🗄️ 4. DATABASE INTEGRATION (QuickLOAD, GRT, Ballistic Solvers)

### **A. QuickLOAD / GRT - Pressure & Velocity Estimation**

**Data som trengs:**
```python
{
    "caliber": "6.5 Creedmoor",
    "case": {
        "manufacturer": "Lapua",
        "capacity_gr_h2o": 52.5,
        "length_mm": 48.8,
        "weight_gr": 171
    },
    "bullet": {
        "manufacturer": "Berger",
        "name": "140gr Hybrid Target",
        "weight_gr": 140,
        "diameter_inch": 0.264,
        "length_inch": 1.430,
        "bc_g7": 0.310
    },
    "powder": {
        "name": "H4350",
        "charge_gr": 41.0,
        "lot": "LOT2024-05"
    },
    "primer": {
        "type": "CCI 200 LR",
        "lot": "LOT2024-10"
    },
    "loading": {
        "coal_mm": 70.6,
        "cbto_mm": 56.2,
        "jump_inch": 0.020
    },
    "rifle": {
        "barrel_length_mm": 610,
        "twist_inch": 8,
        "groove_diameter_inch": 0.2640
    }
}
```

**QuickLOAD Output:**
```python
{
    "peak_pressure_psi": 56120,
    "muzzle_velocity_fps": 2710,
    "muzzle_pressure_psi": 8200,
    "barrel_time_ms": 1.24,
    "powder_burn_percent": 97.8,
    "case_fill_percent": 95.2
}
```

---

### **B. Applied Ballistics / Ballistic AE - Trajectory Solver**

**Input:**
```python
{
    "rifle": {
        "muzzle_velocity_fps": 2710,
        "zero_distance_m": 100,
        "sight_height_inch": 1.5,
        "scope_height_mm": 38
    },
    "bullet": {
        "bc_g7": 0.318,  # TRUED BC from your rifle!
        "weight_gr": 140,
        "caliber_inch": 0.264
    },
    "atmosphere": {
        "temperature_f": 59,
        "pressure_inhg": 29.92,
        "humidity_percent": 50,
        "altitude_ft": 0
    },
    "wind": {
        "speed_mph": 10,
        "direction_deg": 90  # 3 o'clock = full-value
    },
    "rifle_specifics": {
        "twist_rate_inch": 8,
        "twist_direction": "RIGHT",
        "latitude_deg": 60,  # Norge
        "azimuth_deg": 0  # Shooting north
    }
}
```

**Output Trajectory Table:**
```
Distance | Drop    | Drop  | Wind   | Spin  | Coriolis | Velocity | Energy  | TOF
(m)      | (cm)    | (MOA) | (cm)   | (cm)  | (cm)     | (fps)    | (ft-lb) | (s)
---------|---------|-------|--------|-------|----------|----------|---------|------
0        | 0.0     | 0.0   | 0.0    | 0.0   | 0.0      | 2710     | 2283    | 0.000
100      | 0.0     | 0.0   | 3.2    | 0.8   | 0.1      | 2520     | 1975    | 0.123
200      | -12.5   | -1.8  | 6.8    | 1.5   | 0.3      | 2340     | 1703    | 0.255
300      | -35.2   | -3.4  | 11.0   | 2.5   | 0.6      | 2170     | 1463    | 0.397
400      | -70.5   | -5.1  | 16.2   | 3.8   | 1.0      | 2010     | 1256    | 0.550
500      | -120.0  | -6.9  | 22.5   | 5.5   | 1.6      | 1860     | 1076    | 0.715
600      | -186.2  | -8.9  | 30.0   | 7.5   | 2.4      | 1720     | 920     | 0.893
700      | -271.0  | -11.1 | 39.2   | 10.2  | 3.5      | 1590     | 786     | 1.086
800      | -377.5  | -13.5 | 50.5   | 13.5  | 4.8      | 1470     | 672     | 1.295
900      | -509.2  | -16.2 | 64.0   | 17.5  | 6.5      | 1360     | 575     | 1.523
1000     | -670.0  | -19.2 | 80.2   | 22.5  | 8.6      | 1260     | 493     | 1.771
```

---

## 📊 5. DATA SOM ER UMULIG Å MÅLE (men kan estimeres)

### **❌ Direkte trykk (uten Pressure Trace)**
**Workaround:**
- QuickLOAD estimering
- Case head expansion
- Velocity correlation
- Pressure signs

### **❌ Eksakt BC (uten multi-chrono setup)**
**Workaround:**
- Book BC som start
- True BC fra drop data @ 600m
- Iterative tuning with dope card

### **❌ Powder burn rate (uten lab)**
**Workaround:**
- Manufacturer data
- QuickLOAD burn rate curves
- Muzzle flash observation

### **❌ Primer brisance (flame temp/pressure)**
**Workaround:**
- Manufacturer specs
- ES/SD comparison between primers
- QuickLOAD primer models

### **❌ Exact case capacity (varies per case)**
**Workaround:**
- Weigh water filled case (destructive)
- Use manufacturer nominal capacity
- Adjust QuickLOAD to match chrono velocity

---

## 🎓 6. ANBEFALTE MÅLINGER FOR AI/ML PREDIKSJONER

### **Minimum Dataset for Load Development Prediction:**
```python
{
    "components": {
        "brass_make": "Lapua",
        "brass_firings": 2,
        "powder_type": "H4350",
        "powder_charge_gr": 41.0,
        "bullet_weight_gr": 140,
        "bullet_bc_g7": 0.310,
        "primer_type": "CCI 200"
    },
    "rifle": {
        "caliber": "6.5 Creedmoor",
        "barrel_length_mm": 610,
        "twist_inch": 8,
        "round_count": 850,
        "rounds_since_clean": 40
    },
    "loading": {
        "coal_mm": 70.6,
        "cbto_mm": 56.2,
        "jump_inch": 0.020,
        "neck_tension_inch": 0.002
    },
    "results": {
        "velocity_avg_fps": 2710,
        "velocity_sd_fps": 8.5,
        "velocity_es_fps": 18,
        "group_size_mm": 15.2,
        "group_size_moa": 0.52
    },
    "environment": {
        "temperature_f": 59,
        "humidity_percent": 50,
        "altitude_ft": 100
    }
}
```

### **Optimal Dataset (med chamber specs):**
```python
{
    # ... all above, plus:
    "rifle_chamber": {
        "chamber_spec": "SAAMI",
        "case_base_fired_mm": 12.015,
        "case_base_sized_mm": 12.010,
        "case_clearance_microns": 50,  # Tight!
        "shoulder_bump_inch": 0.002,
        "freebore_cbto_mm": 56.4,  # Jam length
        "throat_erosion_mm": 0.2  # vs new
    },
    "brass_prep": {
        "full_length_sized": True,
        "annealed": True,
        "neck_turned": False,
        "primer_pocket_uniformed": True,
        "case_length_mm": 48.8
    },
    "advanced_results": {
        "case_head_expansion_inch": 0.0002,  # Pressure indicator!
        "primer_flattened": False,
        "ejector_mark": False,
        "velocity_shot_string": [2705, 2712, 2708, 2715, 2710]  # Individual shots
    }
}
```

---

## 🚀 7. IMPLEMENTASJON I PROGRAMMET

### **Data Collection Form - Prioritet:**

#### **TIER 1 (Alltid spør):**
- ✅ Powder type + charge
- ✅ Bullet weight + BC
- ✅ COAL/CBTO
- ✅ Velocity (avg, ES, SD)
- ✅ Group size
- ✅ Brass firings
- ✅ Primer type
- ✅ Barrel length + twist

#### **TIER 2 (Valgfritt, men sterkt anbefalt):**
- ✅ Case prep (FL sized, annealed, etc.)
- ✅ Neck tension (measured or mandrel size)
- ✅ Jump to lands
- ✅ Case head expansion (pressure!)
- ✅ Rifle round count
- ✅ Temperature + humidity

#### **TIER 3 (Advanced users):**
- ✅ Chamber measurements (fired vs sized brass)
- ✅ Pressure signs (visual checklist)
- ✅ Case capacity (H2O weight)
- ✅ Neck thickness (uniformity)
- ✅ Concentricity (runout)
- ✅ Throat erosion (measured)

---

## 📚 8. KILDER & VIDERE LESNING

### **Ballistikk-Teori:**
- Bryan Litz: *Applied Ballistics for Long Range Shooting*
- Robert McCoy: *Modern Exterior Ballistics*
- Chris Long: *Optimum Barrel Time Theory*

### **Indre Ballistikk:**
- QuickLOAD manual (indre ballistikk modeling)
- Gordon Reloading Tool (GRT) documentation
- Pressure Trace II manual

### **Målemeteknikker:**
- Sinclair Intl reloading manuals
- Berger Bullets Reloading Manual (precision techniques)
- AccurateShooter.com articles

### **Databaser:**
- Hodgdon Reloading Data Center
- Vihtavuori Reloading Guide
- Applied Ballistics bullet library
- JBM Ballistics calculators

---

## ✅ KONKLUSJON

**Realistisk målbare data med hjemmeutstyr:**

### **🟢 Lett å måle (0-1000 kr utstyr):**
- COAL, CBTO, case length, neck diameter (caliper)
- Powder charge weight (scale)
- Ogive to lands (OAL gauge)
- Visual pressure signs
- Group size (ruler + target)

### **🟡 Moderat investering (1000-5000 kr):**
- Velocity, ES, SD (chronograph)
- Case concentricity (gauge)
- Neck thickness (gauge)
- Case head expansion (precision caliper)

### **🔴 Avansert (5000-15000 kr):**
- Actual pressure (Pressure Trace)
- True BC (multi-chrono or 600m shooting)
- Barrel bore condition (borescope)
- Perfect annealing (AMP)

**Data som IKKE kan måles, men estimeres:**
- Trykk (via QuickLOAD + velocity)
- BC (via trajectory matching)
- Harmonics (via ladder testing)
- Optimal load (via AI learning from historical data)

**AI/ML kan lære:**
- QuickLOAD-style pressure estimation
- Optimal charge weight prediction
- ES/SD prediction from brass prep
- BC truing from limited drop data
- Node prediction from barrel specs

Dette er fundamentet for et intelligent reloading system! 🎯
