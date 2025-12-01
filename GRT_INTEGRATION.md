# Gordon Reloading Tool (GRT) - Integrasjonsveiledning

## Hva er Gordon Reloading Tool?

Gordon Reloading Tool er et **gratis, avansert intern ballistikk-program** som simulerer hva som skjer inne i hylsen og løpet når skuddet går av.

**Last ned her:** https://www.grtools.de/

### Hva GRT beregner:
- **Trykk**: Estimert maks-trykk i PSI/bar
- **Hastighet**: Predikert utgangshastighet
- **Fyllingsprosent**: Hvor full hylsen er (optimalt 90-105%)
- **Trykk-kurve**: Detaljer om trykk-oppbygging
- **Brennhastighet**: Hvor godt krutt-typen matcher din konfigurasjon

## Hvorfor bruke GRT sammen med dette programmet?

### 1. Trygg ladeutvikling
- Se estimert trykk **før** du lader
- Identifiser farlige kombinasjoner på forhånd
- Start med trygg ladning basert på GRT-simulering

### 2. Bedre forståelse
- Lær hvordan ulike krutt oppfører seg
- Se effekten av COAL på trykk
- Forstå fyllingsprosent og density

### 3. Datavalidering
- Sammenlign GRT-prediksjoner med dine faktiske resultater
- Kalibrerer du får du bedre forståelse av ditt våpens egenskaper
- Identifiser avvik (f.eks. treg løp → lavere hastighet enn GRT)

## Slik bruker du integrasjonen

### Steg 1: Kjør simuleringer i GRT

1. **Last ned og installer GRT** (gratis)
2. **Opprett prosjekt** for din kaliber (f.eks. 6.5 Creedmoor)
3. **Velg komponenter**:
   - Kule (bullet)
   - Krutt (powder)
   - Tennhette (primer)
   - Hylse (case)
4. **Angi parametere**:
   - COAL (Cartridge Overall Length)
   - Løpslengde
   - Kruttvekt
5. **Kjør simulering** → GRT beregner hastighet og trykk
6. **Eksporter resultat** som JSON

### Steg 2: Importer til Reloading Workshop Manager

1. Åpne **Analyse → GRT Integrasjon** tab
2. Klikk **📥 Importer fra GRT**
3. Velg JSON-filen du eksporterte fra GRT
4. Programmet matcher automatisk mot dine ammunisjonsprofiler
5. Se resultat i tabellen

### Steg 3: Analyser

**Hastighets-sammenligning:**
- Grønn = GRT stemmer godt (<30 fps avvik)
- Gul = Moderat avvik (30-60 fps)
- Rød = Stort avvik (>60 fps)

**Trykk-analyse:**
- 🟢 Under 58000 PSI = Trygt område
- 🟡 58000-62000 PSI = Høyt, sjekk trykkegn nøye
- 🔴 Over 62000 PSI = Over SAAMI, reduser ladning!

**Fyllingsprosent:**
- Under 85%: Mye luftrom, kan gi ustabil forbrenning
- 90-105%: Optimalt område
- Over 105%: Komprimert ladning (OK for mange krutt)
- Over 110%: Farlig høyt trykk!

### Steg 4: Bruk innsikten

**Scenario 1: Ny ladning**
```
1. Simuler i GRT først
2. Ser du 59000 PSI? → Trygt å teste
3. Ser du 65000 PSI? → IKKE TEST, reduser kruttvekt
4. Når GRT viser trygt trykk → lag patroner
5. Skyt test → legg inn faktisk hastighet
6. Sammenlign med GRT-prediksjon
```

**Scenario 2: Eksisterende ladning**
```
1. Legg inn dine faktiske data (hastighet fra kronometer)
2. Simuler samme ladning i GRT
3. Importer GRT-data
4. Sammenlign:
   - Hvis GRT predikerte 2700 fps, du fikk 2650 fps
   - Ditt løp er litt tregere enn "standard"
   - Juster forventninger til andre ladninger
```

**Scenario 3: Krutt-valg**
```
1. Test 3-4 ulike krutt i GRT for samme kule
2. Se hvilke gir:
   - Trygt trykk
   - God fyllingsprosent (90-100%)
   - Høy hastighet
3. Velg beste krutt basert på GRT
4. Test i virkeligheten
```

## JSON Format (for import)

GRT kan eksportere JSON. Forventet format:

```json
[
  {
    "name": "6.5 CM ELD-M 140gr",
    "caliber": "6.5 Creedmoor",
    "bullet": {
      "name": "Hornady ELD-M",
      "weight_grains": 140
    },
    "powder": {
      "name": "Vihtavuori N555",
      "charge_grains": 42.5
    },
    "velocity_fps": 2750,
    "max_pressure_psi": 58200,
    "case_fill_percent": 98.5
  }
]
```

Alternativt kan du eksportere CSV (kommer snart).

## Viktige advarsler

### ⚠️ GRT er et estimat
- GRT-trykk er teoretiske beregninger
- **Alltid** sjekk for faktiske trykkegn ved skyting
- Bruk GRT som veiledning, ikke fasit

### ⚠️ Trykkegn å se etter
Uansett hva GRT sier, stopp hvis du ser:
- Tunge åpninger på tennhette
- Flate tennhetter (primers)
- Ejector marks på hylsebunn
- Tung lukkemekanisme
- Sprukne hylser

### ⚠️ Variasjon mellom våpen
To identiske rifles kan gi ulik hastighet:
- Løpsroughness
- Chamber dimensjoner
- Freebore lengde
- Løpstemperatur

Derfor: Kalibrer GRT-forventninger mot dine faktiske resultater.

## Tips & Tricks

### 1. Kalibrer GRT for ditt våpen
Etter 5-10 ladninger med faktiske hastigheter, se mønsteret:
- Ligger du konsekvent 50 fps under GRT? → Tregere løp
- Ligger du 30 fps over? → Raskere løp
- Bruk dette til å justere forventninger

### 2. Bruk GRT for krutt-sammenligning
Test 10 ulike krutt i GRT på 2 minutter → spar tid og penger på å teste kun de beste.

### 3. Sjekk fyllingsprosent
Ladninger med 95-100% fylling gir ofte best konsistens (lav ES/SD).

### 4. Kombiner med Harmonic Wizard
- Bruk GRT til å finne trygg kruttvekt
- Bruk Harmonic Wizard til å finne beste COAL
- Perfekt kombinasjon!

## FAQ

**Q: Må jeg ha GRT for å bruke programmet?**  
A: Nei, GRT-integrasjon er valgfri. Alle andre funksjoner fungerer uten GRT.

**Q: Koster GRT penger?**  
A: Nei, GRT er gratis!

**Q: Kan jeg importere direkte fra GRT?**  
A: Du må eksportere fra GRT først (JSON), deretter importere her.

**Q: Hva om GRT gir feil hastighet?**  
A: Helt normalt! Bruk differansen til å lære om ditt våpen. GRT er et estimat.

**Q: Er GRT-trykk nøyaktig?**  
A: Rimelig nøyaktig, men ikke absolutt. Alltid sjekk faktiske trykkegn.

**Q: Hvilke kalibere støtter GRT?**  
A: De fleste populære kalibere. Sjekk GRT-dokumentasjon.

## Videre lesing

- **GRT Hjemmeside**: https://www.grtools.de/
- **GRT Forum**: https://forum.accurateshooter.com/ (søk "GRT")
- **QuickLOAD**: Alternativ til GRT (ikke gratis)

---

**Sist oppdatert**: November 2025  
**Versjon**: 1.0
