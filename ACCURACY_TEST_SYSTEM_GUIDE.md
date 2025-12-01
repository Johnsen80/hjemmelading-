# 📊 Rifle Accuracy Test System - Brukerveiledning

## Oversikt

**Accuracy Test System** lar deg systematisk teste og dokumentere rifle-accuracy over hele pipe-levetiden. Perfekt for:
- Baseline testing (initial accuracy)
- 500-skudd kontroller (tracking utvikling)
- Load development (finne optimal ladning)
- Verifikasjon av loads
- Dokumentasjon med bilder

---

## 🎯 Hvordan Bruke Systemet

### **1. Åpne Accuracy Test Manager**

**Fra Rifle Database:**
1. Gå til **Rifles & Optikk** → **Våpen Database**
2. Velg rifle i tabellen
3. Klikk **📊 Accuracy Test**

---

### **2. Opprett Ny Test**

Klikk **➕ Ny Accuracy Test**

#### **Tab 1: 📋 Test Info**

**Grunndata:**
- **Test Dato:** Når testen ble gjennomført
- **Skudd ved Test:** Hvor mange skudd har rifle fyrt totalt? (0, 500, 1000, etc)
- **Test Type:** 
  - `baseline` - Initial baseline test
  - `500_round_check` - Standard 500-skudd kontroll
  - `load_development` - Load development test
  - `verification` - Verifisering av ladning
  - `cold_bore` - Cold bore accuracy
  - `group_test` - Generell gruppetest
  - `ladder_test` - Ladder test
- **Distanse:** 100m, 200m, etc
- **Antall Grupper:** Hvor mange grupper skal fyres? (anbefalt: 3-5)
- **Skudd per Gruppe:** 3, 5, eller 10 skudd

**Forhold:**
- **Temperatur:** °C
- **Vind:** none, light, moderate, strong
- **Forhold:** Fritekst (lysforhold, mirage, etc)

---

#### **Tab 2: 🔫 Ladning**

**KOMPLETT ladningsdata for denne testen:**

**Hylse:**
- Velg hylse fra dropdown
- Ganger fyrt (1, 2, 3...)
- Hylse lengde (mm)

**Krutt:**
- Velg krutt type
- **Krutt mengde** (grains) - KRITISK DATA!

**Kule:**
- Velg kule
- **COAL** (mm)
- **CBTO** (mm)
- **Jump/Seating Depth** (mm) - Avstand til lands

**Tennhette:**
- Velg tennhette type

> 💡 **Hvorfor dokumentere ladningen?**
> 
> Når du tester ved 0 skudd, 500 skudd, 1000 skudd med **SAMME ladning**, kan du se hvordan accuracy endres over tid. Hvis accuracy degraderer, vet du det er pipen, ikke ladningen!

---

#### **Tab 3: 🎯 Grupper**

**Mål hver gruppe:**
- Legg inn gruppestørrelse i **mm** (målt c-c - center til center)
- Alternativt: Legg inn i **MOA**

**Programmet beregner automatisk:**
- ✅ Gjennomsnittlig gruppe
- ✅ Gjennomsnittlig MOA
- ✅ Beste gruppe
- ✅ Verste gruppe

**Eksempel:**
```
Gruppe 1: 18.5 mm  (0.637 MOA @ 100m)
Gruppe 2: 21.2 mm  (0.730 MOA @ 100m)
Gruppe 3: 19.8 mm  (0.682 MOA @ 100m)

Gjennomsnitt: 19.8 mm (0.683 MOA)
Beste: 18.5 mm (0.637 MOA)
Verste: 21.2 mm (0.730 MOA)
```

---

#### **Tab 4: ⚡ Hastighet**

**Legg inn hastigheter fra chronograph:**

```
2750
2755
2748
2752
2750
2753
2749
2754
2751
2750
```

**Programmet beregner automatisk:**
- ✅ Gjennomsnitt (fps)
- ✅ **ES** (Extreme Spread) - Maks - Min
- ✅ **SD** (Standard Deviation) - Konsistens
- ✅ Min hastighet
- ✅ Max hastighet

**Målsetting for presisjonsskyting:**
- **ES < 15 fps** - Bra
- **ES < 10 fps** - Meget bra
- **ES < 5 fps** - Utmerket
- **SD < 10 fps** - Konkurransekvalitet
- **SD < 5 fps** - Benchrest-kvalitet

---

#### **Tab 5: 📷 Bilder**

**Dokumentasjon:**
- **📷 Last opp Målskive** - Bilde av grupper
- **📷 Last opp Setup** - Bilde av rifle, miljø, utstyr

**Notater:**
- Observasjoner
- Problemer
- Kommentarer

> 💡 **Tips:** Ta alltid bilde av målskivene! Kan være nyttig senere for å sammenligne.

---

### **3. Lagre Test**

Klikk **💾 Lagre Test**

Data lagres i databasen og vises i:
- Accuracy Test Manager (oversiktstabell)
- Rifle Details → Accuracy Tests tab
- Kan brukes til å generere utviklingskurver

---

## 📈 Tracking Accuracy Utvikling

### **Scenario: Baseline → 500 skudd → 1000 skudd**

**Baseline Test (0 skudd):**
```
Dato: 2025-01-15
Skudd: 0
Avg MOA: 0.683
ES: 12 fps
SD: 4.2 fps
```

**500-skudd Test:**
```
Dato: 2025-06-20
Skudd: 500
Avg MOA: 0.695
ES: 14 fps
SD: 4.8 fps
Trend: 📉 Litt dårligere (+1.8%)
```

**1000-skudd Test:**
```
Dato: 2025-12-10
Skudd: 1000
Avg MOA: 0.741
ES: 18 fps
SD: 6.1 fps
Trend: 📉 Dårligere (+8.5% fra baseline)
```

**Konklusjon:**
- Accuracy degraderer over tid (normal)
- Ved 1000 skudd: ~8.5% dårligere enn baseline
- Vurder re-barreling ved fortsatt degradering

---

## 🖨️ Print Test Ark (Kommer snart)

Systemet vil generere et print-vennlig ark med:

**Test Ark inneholder:**
- Ladningsdata (krutt, kule, COAL, CBTO, jump)
- Nummererte skudd (1, 2, 3, 4, 5...)
- Plass for å notere:
  - Velocity per skudd
  - Gruppe-nummer
  - Observasjoner
- QR-kode for rask data-entry senere

**Arbeidsflyt:**
1. **Print ark** før shooting session
2. **Fyr skuddene i riktig rekkefølge** (1→2→3...)
3. **Noter velocity** fra chronograph
4. **Mål grupper** med caliper
5. **Ta bilde** av målskiver
6. **Scan QR-kode** → Auto-åpner test i programmet
7. **Legg inn data** fra arket
8. **Last opp bilder**
9. **Lagre!**

---

## 📊 Analyse og Rapporter

### **Accuracy Development Chart**

**Klikk:** 📈 Utviklingskurve

**Viser:**
- X-akse: Skudd fyrt
- Y-akse: MOA
- Trendlinje over alle tester

**Eksempel plot:**
```
MOA
0.8 |           ●
    |       ●       ●
0.7 |   ●               
    | ●
0.6 |_________________
    0   500  1000 1500  Skudd
```

**Konklusjon:**
- Accuracy starter på ~0.65 MOA
- Holder seg stabilt til 500 skudd
- Begynner å degradere etter 1000 skudd
- Ved 1500 skudd: ~0.8 MOA (kanskje tid for ny pipe)

---

## 🎯 Best Practices

### **1. Konsistente Tester**

**Bruk SAMME:**
- ✅ Ladning (krutt mengde, COAL, jump)
- ✅ Hylser (samme lot, samme ganger fyrt)
- ✅ Kuler (samme lot, batch)
- ✅ Distanse (100m anbefalt for repeatability)
- ✅ Skudd per gruppe (5 skudd anbefalt)
- ✅ Antall grupper (3-5 grupper)

**Dette gir:**
- Valid sammenligning over tid
- Kan isolere pipe-degradering fra andre faktorer

---

### **2. Testing Intervaller**

**Anbefalt schedule:**
- **0 skudd** - Baseline (KRITISK!)
- **500 skudd** - Første kontroll
- **1000 skudd** - Andre kontroll
- **1500 skudd** - Tredje kontroll
- **2000+ skudd** - Hver 500 skudd

**Hvorfor hver 500 skudd?**
- Passer med case measurement intervall
- Fanger opp gradvis degradering
- Data for å predikere barrel life

---

### **3. Dokumentasjon**

**Alltid dokumenter:**
- ✅ Værforhold (temperatur, vind)
- ✅ Lysforhold (kan påvirke sight picture)
- ✅ Rifle condition (nettopp rengjort? Kald? Varm?)
- ✅ Kronograf posisjon (konsistent plassering)
- ✅ Bilder av grupper (kan ikke stole på hukommelsen!)

---

### **4. Flere Grupper > Færre Skudd**

**Bedre:**
- 5 grupper × 3 skudd = 15 skudd
- Gjennomsnitt av 5 målinger

**Enn:**
- 1 gruppe × 15 skudd = 15 skudd
- Kun én måling (kan være fluke)

**Hvorfor?**
- Reduserer random variation
- Mer statistisk valid
- Ser om rifle "grupperer konsistent"

---

### **5. Cold Bore Testing**

**For hunting rifles:**
- Test "cold bore" accuracy (første skudd)
- Relevant fordi første skudd er det som teller på jakt

**Metode:**
1. La rifle bli helt kald (30+ min)
2. Fyr ett skudd
3. Noter POI (Point of Impact)
4. Gjenta 5-10 ganger
5. Mål spredning av cold bore shots

**Skriv ned:**
- Avstand til POI fra warm barrel group
- Cold bore ES/SD
- Om første skudd er konsistent high/low/left/right

---

## 🔍 Analyse: Hva Betyr Dataene?

### **MOA Tolkning**

| MOA | Kvalitet | Anvendelse |
|-----|----------|------------|
| < 0.5 | Utmerket | Benchrest, F-Class |
| 0.5-1.0 | Meget bra | Competition, Long Range |
| 1.0-1.5 | God | Precision Hunting |
| 1.5-2.0 | OK | Hunting |
| > 2.0 | Dårlig | Undersøk rifle/load |

---

### **ES/SD Tolkning**

| ES fps | SD fps | Kvalitet | Anvendelse |
|--------|--------|----------|------------|
| < 10 | < 5 | Utmerket | Benchrest, ELR |
| 10-15 | 5-10 | Meget bra | Competition |
| 15-25 | 10-15 | God | Precision Hunting |
| 25-40 | 15-20 | OK | Hunting |
| > 40 | > 20 | Dårlig | Undersøk load |

**Hva påvirker ES/SD:**
- ❌ Inkonsistent krutt mengde
- ❌ Variabel neck tension
- ❌ Dårlig tennhetter (CCI BR-2 anbefalt)
- ❌ Temperatur-sensitive krutt
- ✅ Precision powder measure (Autotrickler, ChargeMaster)
- ✅ Annealed cases (konsistent neck tension)
- ✅ Weight-sorted brass

---

### **Accuracy Degradering**

**Normal degradering:**
- 0-500 skudd: Minimal (<2%)
- 500-1500 skudd: Gradvis (2-8%)
- 1500-2500 skudd: Merkbar (8-15%)
- 2500+ skudd: Betydelig (15%+)

**Varierer per kaliber:**
- **6mm BR:** ~1500 skudd (hot, overbore)
- **6.5 Creedmoor:** ~2500 skudd
- **.308 Win:** ~5000 skudd (cool, efficient)
- **.223 Rem:** ~3000 skudd
- **Magnums:** 1000-1500 skudd (very hot)

**Faktorer:**
- Kaliber (overbore = kortere liv)
- Krutt type (slow vs fast)
- Ladning (max loads = mer erosjon)
- Rengjøringsfrekvens
- Barrel quality (Bartlein, Krieger = lengre liv)

---

## 🚀 Avanserte Features (Kommer)

### **1. AI Load Recommendation**

Basert på alle dine tester, kan AI:
- Anbefale optimal krutt mengde
- Anbefale optimal seating depth
- Finne velocity nodes
- Predikere accuracy ved forskjellige loads

**Eksempel:**
```
📊 AI Analyse:

Dine tester viser:
• Beste accuracy ved 41.5-42.0gr H4350
• Sweet spot: 41.7gr (0.65 MOA, ES 8 fps)
• Node ved 2750-2770 fps
• Jump 0.020" gir beste konsistens

Anbefaling:
🎯 41.7gr H4350
🎯 COAL 71.10mm (0.020" jump)
🎯 Forventet: 0.65 MOA, ES <10 fps
```

---

### **2. OCW (Optimal Charge Weight) Integrasjon**

**Guided ladder test:**
1. System foreslår charge range (40.0-42.0gr i 0.3gr steps)
2. Generer nummerert test ark
3. Fyr round-robin (ikke stigende!)
4. System analyserer velocity nodes
5. Anbefaler optimal charge

---

### **3. Seating Depth Optimization**

**Guided test:**
1. System bruker dine jam-length målinger
2. Foreslår test: jam, -0.010", -0.020", -0.030", -0.040"
3. Fyr 3-5 grupper per depth
4. System analyserer hvilken depth gir best accuracy
5. Anbefaler optimal depth

---

### **4. Target Analyzer Integrasjon**

**Last opp bilde av målskive:**
1. AI detekterer skudd
2. Beregner automatisk gruppe størrelse
3. Fyller inn i test data
4. Ingen manuell måling nødvendig!

---

## ✅ Oppsummering

**Accuracy Test System gir:**
- ✅ Komplett dokumentasjon av rifle accuracy
- ✅ Tracking av utvikling over barrel life
- ✅ Data for optimal load development
- ✅ Bevis på når re-barreling er nødvendig
- ✅ Historikk for salg av rifle (dokumentert accuracy)

**Start med baseline test i dag!** 🎯
