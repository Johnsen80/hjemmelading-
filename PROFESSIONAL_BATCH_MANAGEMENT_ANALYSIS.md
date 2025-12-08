# 🎯 Professional Batch & Brass Management - Analyse

## Hva Gjør Profesjonelle Ladere?

### 1. **Benchrest & F-Class Shooters (0.1-0.3 MOA)**

#### **Brass Management:**

**Innkjøp:**
- Kjøper 200-300 cases fra **SAMME LOT** (Lapua, Norma, Peterson)
- Lot number er KRITISK (samme brass thickness, capacity)
- Aldri bland lot numbers!

**Initial Prep (ny brass):**
1. **Weight sorting** ±0.5gr (eller ±0.2gr for benchrest)
   - Veier ALLE 200 cases
   - Sorterer i grupper: 168.0-168.5gr, 168.5-169.0gr, etc
   - Bruker kun toppgruppen (50-100 cases)
   - Resten blir "practice ammo"

2. **Length measurement**
   - Måler alle cases: 2.005", 2.007", 2.006"
   - Sorterer ±0.002" (0.05mm)
   - Trimmer til eksakt lengde

3. **Neck thickness uniforming**
   - Måler neck thickness med ball micrometer
   - Sorterer ±0.001" (0.025mm)
   - Eller: Neck turning (skjærer uniformt)

4. **Flash hole deburring & uniforming**
   - Alle flash holes må være identiske
   - Påvirker tennhette tenning uniformt

5. **Primer pocket uniforming**
   - Ensartet dybde = konsistent tennhette seating

**Resultat:**
- 50-100 "match grade" cases
- Identiske: vekt ±0.2gr, lengde ±0.002", neck ±0.001"
- Cost: ~$150-200 for brass + 4-6 timer arbeid

---

#### **Batch Loading System:**

**Batch størrelse:**
- **Benchrest:** 20-50 rounds per batch
- **F-Class:** 50-100 rounds
- **PRS:** 100-200 rounds

**Hvorfor små batches?**
- Hvis en batch ikke skyter bra, har du ikke ødelagt 500 rounds
- Lettere QC (Quality Control)
- Kan teste små justeringer

**Batch Tracking:**
```
Batch ID: 2024-11-24-001
Rifle: Tikka T3x 6.5CM
Lot: Lapua 6.5CM brass, Lot #2023-08-15
Cases: 50 pcs, 2x fired, last annealed 2024-11-20
Bullet: Berger 140gr Hybrid, Lot #7654321, avg weight 140.2gr
Powder: H4350, Lot #MB-2024-042, 41.5gr ±0.02gr
Primer: CCI BR-2, Lot #5432
COAL: 71.12mm ±0.02mm
CBTO: 54.86mm ±0.01mm
Neck Tension: 0.002" (not annealed before sizing)
Loaded Date: 2024-11-24
QC Pass Rate: 48/50 (96%)
Notes: 2 rounds rejected for CBTO >0.02mm variance
```

---

### 2. **Dies & Sizing (KRITISK for Konsistens)**

#### **Full Length vs Neck Sizing:**

**Benchrest/F-Class (single rifle, match brass):**
- **Neck sizing only** (eller minimal shoulder bump)
- Hvorfor? Brass fire-forms til chamber = perfect fit
- Bump shoulder kun 0.001-0.002" (25-50 microns)
- Preserverer brass-levetid

**PRS/Competition (multiple rifles, field conditions):**
- **Full length sizing** (for pålitelighet)
- Bump shoulder 0.002-0.003"
- Sikrer at ammo chambers i alle forhold (dirt, carbon)

**Critical measurements per batch:**
```
Pre-sizing measurement:
- Case length: 2.005"
- Shoulder datum: 1.630"
- Case head to shoulder: 1.630"

Post-sizing target:
- Shoulder bump: 0.002" (1.628")
- Case length maintained
- Neck OD: 0.289" (for 0.002" tension with 0.264" bullet)
```

---

#### **Die Setup (Per Rifle, Per Brass):**

**Proffene dokumenterer:**

**Sizing Die Settings (per rifle):**
```
Rifle: Tikka T3x 6.5CM #1
Brass: Lapua 6.5CM Lot #2023-08-15
Die: Redding Type-S Bushing FL Die

Settings:
- Die depth: Shell holder contact + 1/4 turn (1.630" shoulder)
- Bushing size: 0.287" (for 0.002" neck tension)
- Decapping pin: Removed (separate operation)
- Expander: Not used (bushing only)
- Lube: Imperial Dry Neck Lube

Verification:
- Shoulder bump: 0.0015" measured
- Neck tension: 0.002" interference
- Chamber fit: 0.001" headspace on GO gauge
- Case run-out: <0.002" TIR
```

**Seating Die Settings:**
```
Die: Redding Competition Seating Die

Settings:
- Seating depth: CBTO 54.86mm (2.160")
- Micrometer: 0.285" from datum
- Neck bushing alignment: Floating sleeve
- Bullet alignment: VLD chamfer in die

Verification per round:
- CBTO: 54.86mm ±0.01mm
- Run-out: <0.001" TIR
- Seating force: Consistent (if not = reject round)
```

---

### 3. **Annealing (Levetid & Konsistens)**

#### **Timing:**

**Professional schedule:**
- **Benchrest:** Anneal HVER gang (1x fired = 1x anneal)
- **F-Class:** Anneal hver 2-3 firings
- **PRS:** Anneal hver 3-5 firings
- **Hunting:** Anneal hver 5-10 firings (eller aldri)

**Hvorfor?**
- Work hardening → inkonsistent neck tension
- Neck tension = konsistent bullet release = konsistent velocity
- ES/SD øker dramatisk uten annealing

**Data fra testing:**
```
Same load, same brass (Lapua 6.5CM):

Without annealing (5x fired):
ES: 28 fps
SD: 9.2 fps
Avg velocity: 2750 fps

With annealing after every firing:
ES: 8 fps
SD: 2.8 fps
Avg velocity: 2751 fps
```

**Annealing Methods:**

1. **AMP Annealer ($1500-2000)**
   - Aztec Mode (analyze brass)
   - Auto-program per brass/lot
   - Perfekt anneal hver gang
   - Used by 90% of benchrest shooters

2. **Annie Induction Annealer ($500-800)**
   - Time-based, må tune
   - Good consistency hvis riktig setup

3. **Flame annealing (Bench-Source, etc)**
   - $200-400
   - Mindre consistent
   - Krever Templaq for verifikasjon

**Dokumentasjon:**
```
Annealing Log:
Date: 2024-11-20
Brass: Lapua 6.5CM Lot #2023-08-15
Cases: 50 pcs (2x fired before annealing)
Method: AMP Annealer
Program: #0457 (Lapua 6.5CM)
Aztec reading: 114 (within spec 110-120)
Verification: Templaq 750°F (did not melt = good)
Notes: All cases within ±2 units
```

---

### 4. **Batch QC (Quality Control)**

#### **Per Round QC (100% inspection):**

**Proffene sjekker HVER patroner:**

1. **Powder charge:**
   - AutoTrickler V4: ±0.02gr (best)
   - ChargeMaster: ±0.1gr (ok)
   - Manual measure: ±0.3gr (ikke bra nok)
   - **Reject hvis >0.1gr variance**

2. **CBTO (Cartridge Base To Ogive):**
   - Måler med Hornady comparator
   - Spec: ±0.01mm (±0.0004")
   - **Reject hvis >0.02mm variance**

3. **COAL (Cartridge Overall Length):**
   - Mindre kritisk enn CBTO
   - Spec: ±0.02mm
   - Hovedsakelig for magazine fit

4. **Run-out (Concentricity):**
   - Måler med concentricity gauge
   - Spec: <0.002" TIR (Total Indicated Runout)
   - **Reject hvis >0.003" TIR**

5. **Visual inspection:**
   - Dented case mouth?
   - Bullet seated crooked?
   - Primer flush/cratered?

**QC Documentation:**
```
Batch: 2024-11-24-001 (50 rounds loaded)

Powder QC:
- Target: 41.5gr
- Actual range: 41.48-41.52gr
- Variance: ±0.02gr ✓
- Pass: 50/50 (100%)

CBTO QC:
- Target: 54.86mm
- Actual range: 54.85-54.87mm
- Variance: ±0.01mm ✓
- Pass: 48/50 (96%)
- Rejected: 2 rounds (54.89mm, 54.83mm)

Run-out QC:
- Spec: <0.002" TIR
- Actual range: 0.0005"-0.0018"
- Pass: 50/50 (100%)

Total QC: 48/50 passed (96%)
Rejected: 2 rounds (CBTO out of spec)
```

---

### 5. **Brass Lifecycle Management**

#### **Tracking per Case (Advanced):**

**Benchrest shooters (ekstrem):**
- Nummererer HVER case (1-100)
- Logger hver firing:
  ```
  Case #042:
  - Firing 1: 2024-06-15, 41.5gr, 2750fps, primer good
  - Annealed: 2024-06-16 (AMP #0457)
  - Firing 2: 2024-07-20, 41.5gr, 2748fps, primer good
  - Annealed: 2024-07-21 (AMP #0457)
  - Firing 3: 2024-09-10, 41.5gr, 2752fps, primer flattened
  - Annealed: 2024-09-11 (AMP #0457)
  - Firing 4: 2024-11-24, 41.5gr, ?, ?
  - Status: Active, 4x fired, excellent condition
  ```

**F-Class/PRS (pragmatisk):**
- Tracker i batches (50-100 cases)
- Logger collective:
  ```
  Batch: Lapua-2023-001 (100 cases)
  - Purchase: 2023-08-15
  - Weight sorted: 168.5-169.0gr (top 100 of 200)
  - Prep: FL sized, trimmed, flash hole deburred
  
  Firing log:
  1. 2023-09-01: 100 fired (41.5gr H4350)
  2. 2023-09-02: Annealed (AMP)
  3. 2023-10-15: 100 fired (41.5gr H4350)
  4. 2023-10-16: Annealed (AMP)
  5. 2024-01-20: 98 fired (2 lost in field)
  6. 2024-01-21: Annealed (AMP)
  7. 2024-05-10: 95 fired (3 rejected - loose primer pockets)
  8. 2024-05-11: Annealed (AMP)
  9. 2024-11-24: 95 fired
  
  Current status:
  - Cases remaining: 95
  - Times fired: 9
  - Times annealed: 8
  - Condition: Good (5 showing signs of wear)
  - Expected retirement: 12-15 firings
  ```

---

#### **Retirement Criteria:**

**When to retire brass:**

1. **Primer pocket loose** (most common)
   - Primer seats too easy (no resistance)
   - Primer falls out
   - Cause: High pressure, too many firings

2. **Case head separation** (dangerous!)
   - Incipient head separation (shiny ring inside)
   - Check with paper clip inside case
   - Retire IMMEDIATELY

3. **Neck splits**
   - Crack in case neck
   - Cause: Work hardening (no annealing)
   - Can sometimes be saved by trimming shorter

4. **Excessive length growth**
   - Case grows beyond max trim length
   - Trimming reduces neck thickness too much

5. **Donut formation**
   - Thickening inside case neck at shoulder junction
   - Causes inconsistent bullet seating
   - Can be reamed out (advanced)

**Typical Brass Lifespan:**
```
With proper annealing:
- Lapua: 15-20+ firings
- Norma: 12-18 firings
- Peterson: 15-20 firings
- Alpha: 12-15 firings
- Hornady: 8-12 firings
- Winchester: 5-8 firings (avoid for precision)

Without annealing:
- Cut lifespan by 50-70%
- Neck splits at 5-8 firings
- Inconsistent ES/SD after 3-4 firings
```

---

### 6. **Dies Dokumentasjon**

#### **Die Types & Usage:**

**Full Length Sizing Dies:**
```
Rifle: Tikka T3x 6.5CM
Chamber: SAAMI spec (factory)

Dies Used:
1. Redding Type-S Full Length Bushing Die
   - Bushing: 0.287" (0.002" neck tension)
   - Shoulder bump: 0.002"
   - Body size: Full (for reliable chambering)
   - Use: Every firing (ensures reliability)

2. Lee Collet Die (backup, neck only)
   - Mandrel: 0.262" (0.002" tension)
   - Use: If FL die oversizes too much
```

**Match Chamber (custom rifle):**
```
Rifle: Custom 6mm Dasher (Benchrest)
Chamber: Cut by Dave Tooley (tight neck, minimal headspace)

Dies Used:
1. Redding Competition Bushing Neck Die
   - Bushing: 0.269" (0.002" tension)
   - Shoulder: NOT touched (fire-formed perfect)
   - Use: Every firing (brass perfectly fits chamber)

2. Redding Body Die (emergency only)
   - Use: If brass needs body sizing (rare)
   - Bump shoulder only 0.001" if needed
```

**Settings per Brass Lot:**
```
Brass: Lapua 6.5CM Lot #2023-08-15

Die Settings (recorded):
- Press: Redding T-7 Turret
- Shell holder: #4 (RCBS)
- Lube: Imperial Sizing Wax (thin coat)

FL Sizing Die:
- Depth: Shell holder + 1/4 turn (1.630" shoulder)
- Bushing: 0.287"
- Measured shoulder bump: 0.0015-0.002"
- Measured neck OD: 0.287" (loaded: 0.289")

Seating Die:
- Depth: Micrometer 0.285"
- CBTO target: 54.86mm
- Measured CBTO: 54.85-54.87mm
- Run-out: 0.0005-0.0015" TIR

Notes:
- Cases last annealed: 2024-11-20
- Brass springs back 0.0005" after sizing (normal)
- If shoulder bump >0.003", reduce die depth 1/8 turn
```

---

### 7. **Bullet QC & Lot Tracking**

#### **What Pros Do When Buying Bullets:**

**Purchase:**
- Buy 500-1000+ bullets from SAME LOT
- Lot number printed on box (Berger, Sierra, Hornady)
- Different lots = different BC, weight, ogive length

**Bullet QC (match bullets):**

1. **Weight sorting:**
   ```
   Berger 140gr Hybrid Target (Lot #7654321)
   Box 1 (100 bullets):
   - Weight range: 139.8-140.3gr
   - Groups sorted:
     * 139.8-140.0gr: 8 bullets (practice)
     * 140.0-140.2gr: 72 bullets (MAIN GROUP) ✓
     * 140.2-140.3gr: 18 bullets (separate batch)
     * 140.3+gr: 2 bullets (discard or practice)
   
   Use 140.0-140.2gr group for match ammo
   ```

2. **Length measurement:**
   ```
   Measure base to ogive (BTO):
   - Target: 0.618" (typical for 140gr Hybrid)
   - Range: 0.616-0.620"
   - Sort ±0.002" (0.05mm)
   
   Why? 
   - BTO variance = CBTO variance
   - If bullet ogive varies, seating depth varies
   ```

3. **Visual inspection:**
   - Meplat (tip) uniformity
   - Jacket imperfections
   - Boat tail condition

**Documentation:**
```
Bullet Lot: Berger 140gr Hybrid Target
Lot #: 7654321
Purchase Date: 2024-10-15
Quantity: 500 bullets
Cost: $225 ($0.45 each)

QC Results (100 bullet sample):
- Avg weight: 140.1gr
- Weight range: 139.8-140.3gr (±0.25gr)
- Weight StdDev: 0.08gr
- Length (BTO): 0.618" ±0.002"
- Quality: Excellent (2% rejected)

Storage:
- Location: Dry cabinet, silica gel
- Temperature: 15-20°C
- Humidity: <40%

Usage Log:
- 2024-11-24: 50 bullets used (Batch #2024-11-24-001)
- Remaining: 450 bullets
```

---

### 8. **Advanced: Harmonics & Seating Depth**

**Pros test seating depth systematically:**

```
Test Setup:
Rifle: Tikka T3x 6.5CM
Bullet: Berger 140gr Hybrid
Powder: 41.5gr H4350 (pre-validated charge)
Brass: Lapua 50x, 2x fired, annealed

Jam Length (measured): 73.25mm COAL (54.86mm CBTO)

Seating Depth Test (5 shots per depth, 3 groups each):

Group 1: Jam (73.25mm COAL, 0.000 jump)
- Avg group: 0.85 MOA
- ES: 18 fps
- Note: Sticky chambering, not practical

Group 2: -0.010" jump (73.00mm COAL)
- Avg group: 0.92 MOA
- ES: 14 fps

Group 3: -0.020" jump (72.75mm COAL)
- Avg group: 0.58 MOA ✓✓✓ BEST
- ES: 9 fps
- Note: Excellent!

Group 4: -0.030" jump (72.49mm COAL)
- Avg group: 0.71 MOA
- ES: 12 fps

Group 5: -0.040" jump (72.24mm COAL)
- Avg group: 0.88 MOA
- ES: 16 fps

Conclusion:
Sweet spot: -0.020" jump (72.75mm COAL, 54.61mm CBTO)
Load 200 rounds at this depth for season.
```

---

## 🎯 System Requirements (Basert på Pro-Analyse)

### **Batch Management:**
1. Batch ID system (auto-generated)
2. Complete component tracking (lot numbers)
3. Die settings per rifle/brass
4. Annealing log
5. QC per round (powder, CBTO, run-out)
6. Pass/fail tracking
7. Rejection reasons

### **Bullet Inventory:**
1. Lot number tracking
2. QC on purchase (weight, length)
3. Storage conditions
4. Usage per batch
5. Remaining inventory

### **Brass Lifecycle:**
1. Lot tracking
2. Firing count per case/batch
3. Annealing log
4. Retirement tracking
5. Die settings documentation
6. Shoulder bump measurements
7. Neck tension verification

### **Die Settings Database:**
1. Per rifle settings
2. Per brass type/lot
3. Shoulder bump target/actual
4. Neck tension target/actual
5. Run-out verification
6. Notes & adjustments

### **QC System:**
1. Per-round inspection
2. Powder charge verification (±0.1gr)
3. CBTO verification (±0.02mm)
4. Run-out measurement (<0.003")
5. Rejection logging
6. Batch acceptance rate

---

## 📊 Anbefalt Implementasjon

### **Priority 1: Batch System**
- Batch ID generation
- Component linking (rifle, brass, bullet, powder, primer)
- Die settings per batch
- QC tracking per round
- Pass/fail statistics

### **Priority 2: Bullet Inventory**
- Lot tracking
- Weight/length QC on purchase
- Usage tracking per batch

### **Priority 3: Brass Lifecycle**
- Firing count
- Annealing log
- Retirement criteria
- Condition tracking

### **Priority 4: Die Settings Database**
- Per rifle/brass combinations
- Measured vs target comparisons
- Notes & adjustments

Dette er hva proffene gjør! 🎯
