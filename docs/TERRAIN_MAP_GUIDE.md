# 🗺️ Terrain Map - Brukerveiledning

## Oversikt
Terrain Map er et revolusjonerende verktøy som integrerer 3D-terrenganalyse direkte i ditt reloading-workflow. Dette er **world-first teknologi** - ingen konkurrenter (QuickLOAD, Applied Ballistics, Strelok Pro) har tilsvarende funksjonalitet.

## Hvorfor er dette viktig?

### Problem med tradisjonell ballistikk
De fleste ballistikk-kalkulatorer antar flat mark:
- Du legger inn "450 meters distanse"
- Kalkulatoren gir deg drop for 450m flat skyting
- **MEN**: I virkeligheten skyter du 150m nedover i fjellet!
- Kulen påvirkes mindre av gravity når du skyter i vinkel
- Resultat: Du holder for høyt → bommer

### Løsningen: Terrain-Aware Ballistics
Med Terrain Map:
1. Kartet henter automatisk elevation for både deg og målet
2. Beregner skytvinkel (oppover/nedover)
3. Anvender **Rifleman's Rule**: Bruk horisontal distanse, ikke line-of-sight
4. Gir korrekte holdover-verdier

## Komme i gang

### Åpne Terrain Map
1. Start programmet
2. Gå til **Analyse**-tab
3. Klikk på **🗺️ Terrengkart**

### Grensesnitt-oversikt
```
┌─────────────────────────────────────────────────────────┐
│ 🗺️ Terrain Map - Geospatial Shooting Analysis          │
│ 3D terrengvisualisering med høydekurver og ballistikk   │
├──────────────────────────────────┬──────────────────────┤
│                                  │ ⚙️ Innstillinger     │
│  KART (OpenTopoMap)              │                      │
│  • Click-to-place markører       │ Ammunisjon:          │
│  • 3D høydekurver                │ [Dropdown]           │
│  • Zoom/Pan kontroller           │                      │
│  • Layer control (OSM/Topo/Sat)  │ 📍 Koordinater:      │
│                                  │ Lat/Lon input        │
│  [Rød markør] = Skyteposisjon    │                      │
│  [Grønn markør] = Mål            │ 🌦️ Vær:             │
│  [Stiplet linje] = Kulebane      │ [Hent værdata]       │
│                                  │                      │
├──────────────────────────────────┴──────────────────────┤
│ 📊 Analyse-resultater                                   │
│ Distanse | Elevation | Vinkel | Drop | Korreksjon      │
└─────────────────────────────────────────────────────────┘
```

## Metode 1: Klikk på kartet

### Steg 1: Sett skyteposisjon
1. Klikk på kartet der DU står
2. En **rød markør** 🔴 plasseres
3. Popup viser lat/lon koordinater

### Steg 2: Sett mål
1. Klikk igjen på kartet der MÅLET er
2. En **grønn markør** 🟢 plasseres
3. En **rød stiplet linje** tegnes mellom posisjonene
4. Popup viser automatisk distanse

### Steg 3: Analyser
1. Velg ammunisjon fra dropdown-menyen
2. Klikk **"🎯 Analyser Skyting"**
3. Få komplett terreng- og ballistikkanalyse!

## Metode 2: Manuell koordinat-input

### Når bruker du dette?
- Du har GPS-koordinater fra jakt-app (OnX, HuntStand, etc.)
- Du planlegger skyting på forhånd
- Du vil teste spesifikke lokasjoner

### Prosedyre
1. **Skytter Lat/Lon**: Fyll inn din posisjon
   - Eksempel: `59.9139` / `10.7522` (Oslo)
2. **Mål Lat/Lon**: Fyll inn målets posisjon
   - Eksempel: `59.9200` / `10.7600`
3. Klikk **"✓ Bruk koordinater"**
4. Kartet oppdateres automatisk med markører
5. Klikk **"🎯 Analyser Skyting"**

## Hente værdata

### Hvorfor er vær viktig?
- **Temperatur**: Påvirker kruttforbrenning og hastighet
- **Lufttrykk**: Lavere trykk = mindre luftmotstand
- **Density Altitude**: Kombinert effekt av temp/trykk/elevation
- **Vind**: Må kompenseres for lateral drift

### Slik gjør du det
1. Sett skyteposisjon (rød markør)
2. Klikk **"☁️ Hent vær for skyteposisjon"**
3. Få live data fra Yr.no:
   - Temperatur (°C)
   - Lufttrykk (hPa)
   - Luftfuktighet (%)
   - Vind (m/s og retning)
   - **Density Altitude** (automatisk beregnet!)

### Eksempel output
```
🌦️ Værdata (Yr.no)
Posisjon: 60.1234, 11.4567

Temperatur: 12°C
Lufttrykk: 1013 hPa
Luftfuktighet: 65%
Vind: 3.5 m/s fra 270°

Density Altitude: 850 ft (259 m)

Data fra Meteorologisk Institutt (Yr.no)
```

## Forstå analyse-resultater

### Eksempel-scenario
```
🎯 Shooting Analysis

📍 Posisjon
Skytter:    60.4720, 8.4689
Elevation:  1050.2 m

Mål:        60.4680, 8.4750
Elevation:  890.5 m

📏 Distanse & Terreng
Horisontal distanse:  520.8 m
Line-of-sight:        548.2 m
Høydeforskjell:       -159.7 m
Skytvinkel:           ↘ -17.2° NEDOVER
Bearing:              135°

🎯 Ballistikk
Ammunisjon:    .308 Win 175gr Sierra (7.62x51mm)
Hastighet:     2600 fps
BC (G1):       0.505
Drop (flat):   -89.3 cm | 34.8 MOA | 10.1 MRAD
Effektiv dist: 497.2 m (for holdover)

⚠️ Terrengkorreksjon
Rifleman's Rule:
Hold LAVERE enn flat-range drop (kulen påvirkes mindre av gravity)

Tips: Bruk horisontal distanse (521m) for å beregne drop, ikke LOS (548m).
```

### Hva betyr dette?

#### Horisontal distanse vs Line-of-Sight
- **Horisontal**: 520.8m (flat mark-ekvivalent)
- **Line-of-Sight**: 548.2m (faktisk avstand kulen flyr)
- **Bruk horisontal** for drop-beregning!

#### Hvorfor?
Når du skyter i vinkel (opp eller ned):
- Gravitasjonskraften virker **vinkelrett på horisontplanet**
- Kulen er "i luften" samme tid som ved horisontal skyting
- Men den horisontale komponenten er kortere
- Derfor: Mindre drop enn forventet ved flat range

#### Skytvinkel
- **Positiv** (↗): Skyter oppover → hold lavere
- **Negativ** (↘): Skyter nedover → hold lavere
- **Null** (→): Flat → ingen korreksjon

#### Bearing
Kompassretning fra deg til målet (0-360°):
- 0° = Nord
- 90° = Øst
- 180° = Sør
- 270° = Vest

## Kart-kontroller

### Zoom
- **Scroll-hjul**: Zoom inn/ut
- **+ / -** knapper: Steg-for-steg zoom
- **Dobbeltklikk**: Zoom til punkt

### Pan (flytt kart)
- **Dra med mus**: Flytt kartet rundt
- **Pil-taster**: Keyboardnavigasjon

### Layer Control
Bytt mellom ulike kart-visninger:

1. **Standard** (OpenStreetMap)
   - Veinett, byer, landemerker
   - God oversikt over sivilisasjon

2. **Topografisk (Høydekurver)** - OpenTopoMap
   - **Tydelige høydekurver** med elevation-tall
   - Fargekodet etter høyde (grønn = lavt, brun = høyt)
   - Beste for å forstå terreng
   - **ANBEFALT for skyting-analyse!**

3. **Satellitt** (Esri World Imagery)
   - Flybilder
   - Se faktisk terrengtype (skog, åpent, vann)
   - God for å vurdere line-of-sight

4. **Topo Map (3D-effekt)** - Esri World Topo
   - Kombinerer høydekurver med relieff-skyggelegging
   - "3D-effekt" som gjør det lett å se fjellkanter
   - Perfekt for å identifiere bratte skråninger

### Måle-verktøy
Klikk **ruler-ikonet** for å måle distanser:
- Klikk flere punkter for å tegne en linje
- Får automatisk distanse i meter
- Nyttig for å sjekke alternative skutt-posisjoner

### Fullskjerm
Klikk **fullscreen-ikonet** for å maksimere kartet.

### MousePosition
Nederst til høyre ser du:
```
Pos: Lat: 60.47205 | Lon: 8.46893
```
Dette oppdateres når du beveger musen over kartet.

## Rifleman's Rule - Matematikk

### Hva er det?
En forenklet metode for å korrigere for skytvinkel.

### Formelen
```
Effektiv distanse = Horisontal distanse × cos(vinkel)
```

Men i praksis er dette **nesten lik horisontal distanse** for moderate vinkler (<30°).

### Eksempel
- Skytvinkel: 20° nedover
- Line-of-sight: 500m
- Horisontal distanse: 470m
- cos(20°) = 0.940

**Bruk 470m for drop-beregning**, ikke 500m!

### Praktisk regel
- **0-15°**: Minimal forskjell, men viktig på lange hold
- **15-30°**: Betydelig forskjell, MÅ korrigere
- **>30°**: Ekstrem korreksjon nødvendig (sjeldent i jakt)

## Density Altitude

### Hva er det?
En "korrigert høyde" som tar hensyn til:
- Faktisk elevation
- Temperatur
- Lufttrykk

### Hvorfor viktig?
Høyere DA = tynnere luft = mindre luftmotstand = kulen flyr raskere og dropper mindre.

### Eksempel
```
Scenario 1: Sommer i fjellet
- Elevation: 1000m
- Temp: 25°C (varmt!)
- Lufttrykk: 900 hPa (lavt)
- DA: 2500m (!!!)

Scenario 2: Vinter ved havet
- Elevation: 50m
- Temp: -5°C (kaldt)
- Lufttrykk: 1025 hPa (høyt)
- DA: -500m (negativ!)
```

### Effekt på ballistikk
- **Høy DA**: Kulen flyr lenger → hold litt lavere
- **Lav DA**: Kulen flyr kortere → hold litt høyere

Terrain Map beregner DA automatisk når du henter værdata!

## Bruksscenarier

### 1. Jakt i fjellet
**Situasjon**: Du ser en hjort 400m unna, 100m lavere i høyden.

**Workflow**:
1. Åpne Terrain Map
2. Klikk din posisjon → rød markør
3. Klikk hjortens posisjon → grønn markør
4. Velg din jakt-ammunisjon
5. Klikk "Analyser"
6. Se: "Bruk 385m drop, ikke 412m (LOS)"
7. Juster sikte tilsvarende
8. Skyt med konfidanse!

### 2. Long-range konkurranse - Reconnaissance
**Situasjon**: Du skal skyte konkurranse på ny bane neste uke.

**Workflow**:
1. Få GPS-koordinater for skyteposisjon og targets
2. Fyll inn manuelt i Terrain Map
3. Få terrain analysis for alle distanser
4. Hent værdata (historisk gjennom uken)
5. Lag DOPE-kort med terrengkorreksjon
6. Ankomme konkurranse forberedt!

### 3. Ladeutvikling for spesifikk jakt-lokasjon
**Situasjon**: Du jakter på samme sted hvert år. Vil optimalisere ladning.

**Workflow**:
1. Logg lokasjonen i Terrain Map
2. Hent værdata (temperatur-område gjennom sesongen)
3. Se Density Altitude-variasjon
4. Utvikle ladning som er **robust** for disse forholdene
5. Test på skytebanen med simulert DA
6. Vær sikker på at ladningen fungerer på jakt!

### 4. Undervisning / Team-planlegging
**Situasjon**: Du er instruktør for et skytte-lag.

**Workflow**:
1. Vis Terrain Map på projektor
2. La studenter se hvordan terreng påvirker ballistikk
3. Demonstrer forskjellen mellom LOS og horisontal distanse
4. Kjør "what-if" scenarios
5. Studenter lærer terrengforståelse visuelt!

## Tips & Triks

### 1. Zoom ut for oversikt
Før du plasserer markører, zoom ut for å se hele området. Dette hjelper deg å identifisere større fjell/daler.

### 2. Bytt til Topo Map
For beste terrengforståelse, bruk **Topo Map (3D-effekt)** eller **Topografisk (Høydekurver)**. Standard OSM viser ikke høyder!

### 3. Sjekk flere skutt-posisjoner
Prøv å flytte skytter-posisjon litt til høyre/venstre. Kanskje du finner en posisjon med bedre vinkel?

### 4. Lagre favoritter (kommer snart)
Når database-integrasjonen er ferdig, kan du lagre lokasjoner og gjenbruke dem.

### 5. Print terrain analysis
Kopier resultatene til et DOPE-kort eller export (PDF-funksjon kommer).

### 6. Kombiner med Precision Tracker
Etter en jakt-tur:
1. Logg skuddet i Session Logger
2. Noter ned terreng-data fra Terrain Map
3. Precision Tracker vil lære hvordan DIN rifle presterer i terreng!

### 7. Vær konservativ
Hvis du er usikker på terrengkorreksjon, **hold litt lavere enn beregnet**. Det er bedre å treffe i nedkant enn å skyte over.

## Begrensninger

### Elevation-oppløsning
SRTM30m gir 30-meter oppløsning. Dette er **bra nok** for de fleste bruksområder, men:
- Små terrengvariasjoner (<30m) kan bli glatt ut
- I bratt terreng kan elevation være noen meter unøyaktig
- Bygninger/trær er ikke med (bare "ground elevation")

### Værdata
Yr.no gir værdata fra nærmeste målestasjon. Micro-klima kan variere:
- Vindforhold i dal vs. åstopp
- Temperatur-inversjoner
- Lokale værfenomener

### Kurvatur
For nå beregner vi **rett linje** mellom skytter og mål. I virkelighethen har kule-banen en kurve. Dette kommer i Fase 2.

### Line-of-sight blokkeringer
Kartet viser ikke om det er fjell/trær **i veien** mellom deg og målet. Bruk satellitt-visning for å sjekke!

## Feilsøking

### "Kunne ikke hente terrengdata"
**Problem**: API-kall til OpenTopoData feilet.

**Løsninger**:
1. Sjekk internett-tilkobling
2. OpenTopoData kan være nede (sjelden)
3. Prøv igjen etter noen minutter
4. Hvis det vedvarer, fyll inn elevation manuelt

### "Kunne ikke hente værdata"
**Problem**: Yr.no API feilet.

**Løsninger**:
1. Sjekk internett-tilkobling
2. Yr.no kan ha rate-limiting
3. Vent 10 sekunder og prøv igjen
4. Værdata er **ikke kritisk** for terrenganalyse - du kan fortsette uten

### Markører plasseres feil
**Problem**: Klikket litt ved siden av.

**Løsninger**:
1. Klikk **"🔄 Reset posisjoner"**
2. Zoom inn mer før du klikker
3. Bruk manuell koordinat-input for presisjon

### Kartet laster ikke
**Problem**: QWebEngineView initialisering feilet.

**Løsninger**:
1. Sjekk at `PyQt6-WebEngine` er installert:
   ```powershell
   pip install PyQt6-WebEngine
   ```
2. Restart programmet
3. Sjekk console output for feilmeldinger

## Fremtidige features (roadmap)

### Fase 2: Terrain Profile Cross-Section
- Graf som viser elevation langs hele kulebanen
- Identifiser terreng-hindringer
- Visualiser kulebane-kurve over terreng

### Fase 3: Vindkart
- Hent vind-forecast for området
- Vis vindretning med piler på kartet
- Beregn lateral drift

### Fase 4: Database-integrasjon
- Lagre favoritt-lokasjoner
- Historisk værdata per lokasjon
- Mission planning (pre-plan flere skutt-posisjoner)

### Fase 5: Multi-target planning
- Sett opp flere mål på én gang
- Beregn optimal skyteposisjon
- Export mission plan som PDF

### Fase 6: Drop Chart Export
- Generer drop-chart spesifikk for denne lokasjonen
- Inkluderer terrengkorreksjon
- Print og ta med på jakt!

## Konklusjoner

### Hvorfor Terrain Map er game-changing
1. **Ingen konkurrent har dette**: Du er foran 99% av skyttere
2. **Realistisk ballistikk**: Tar hensyn til virkeligheten (ikke flat mark)
3. **Lærer terrengforståelse**: Du blir en bedre skytter ved å forstå miljøet
4. **Gratis globale data**: Fungerer overalt, ikke bare Norge
5. **Integrert workflow**: Alt i ett program - ikke flere apper

### Når skal du bruke det?
- **Alltid** før en jakt-tur i fjellet
- Når du skal skyte **long-range** (>300m)
- Når terreng er **ujevnt** (ikke flat skytebane)
- For **mission planning** og reconnaissance
- Til **undervisning** og team-koordinering

### Når trenger du det IKKE?
- Flat skytebane (0° vinkel)
- Korte distanser (<200m) hvor terrengeffekten er minimal
- Når du allerede har nøyaktige DOPE-kort for lokasjonen

---

**Happy shooting, og husk: Terrain matters! 🗺️🎯**

*Laget med ❤️ av Reloading Workshop Manager*
*World-first technology in reloading software*
