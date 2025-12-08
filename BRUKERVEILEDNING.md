# 🎯 HVORDAN BRUKE PROGRAMMET

## Starte Programmet

### Windows PowerShell:
```powershell
cd "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading"
.\.venv\Scripts\python.exe main.py
```

---

## 🚀 DEMO: Zero Shift Calculator

### Hva gjør den?
Beregner hvor mange klikk du må justere optikken når du bytter ammunisjon.

### Eksempel Scenario:

**Situasjon:**
- Du har skutt inn rifla med 140gr ammunition på 100 meter
- Skal konkurrere på 300 meter med 147gr ammunition
- Trenger å vite optikk-justering

### Steg-for-steg:

#### 1. Åpne Zero Shift Calculator
- Klikk på menyen: **Verktøy → Zero Shift Kalkulator**
- Eller finn den i tabben som dukker opp

#### 2. Fyll inn Ammunisjon 1 (Det du har skutt inn med)
```
Hastighet: 2700 fps
BC (G1): 0.450
Vekt: 140 grains
Zero avstand: 100 m
```

#### 3. Fyll inn Ammunisjon 2 (Det du skal bytte til)
```
Hastighet: 2620 fps
BC (G1): 0.497
Vekt: 147 grains
Zero avstand: 100 m
```

#### 4. Konfigurer Optikk
```
Klikk-verdi: 0.25 (typisk for 1/4 MOA)
Enhet: MOA (eller MRAD hvis din optikk bruker det)
Skyteavstand: 300 m
```

#### 5. Klikk "🎯 Beregn Justering"

### Resultat du får:

**Hovedresultat:**
```
9 klikk NED ⬇
-2.3 MOA ved 300m
```

**Detaljert Info:**
- Drop for begge ammunisjoner
- Forskjell i cm, MOA og MRAD
- Energi og hastighet

**Tabell for flere avstander:**
| Avstand | Klikk   |
|---------|---------|
| 100m    | 0       |
| 200m    | 3 NED   |
| 300m    | 9 NED   |
| 400m    | 18 NED  |
| 500m    | 29 NED  |

---

## 🎓 TIPS & TRIKS

### Zero Shift Calculator

#### Tips 1: Noter Original Zero
Før du justerer, skriv ned:
- Nåværende zero-innstilling
- Ammunitionen brukt
- Dato

#### Tips 2: Test på Kort Hold
Etter justering:
1. Skyt 1 skudd på 100m først
2. Bekreft treffpunkt
3. Juster videre hvis nødvendig

#### Tips 3: Værforhold
Husk at:
- Temperatur påvirker hastighet (ca 2fps per grad)
- Vind påvirker sidejustering
- Luftfuktighet har minimal effekt på korte avstander

#### Tips 4: Lagre Profiler (kommer snart)
Når ammunition-modulen er klar:
- Lagre ofte brukte ammunisjoner som profiler
- Last raskt inn for sammenligning
- Hold historikk over tester

---

## 🔧 ANDRE FUNKSJONER (Under utvikling)

### Kommer snart:

#### 🧪 Test Lab
- Planlegg ladder tests
- Logg resultater
- Analyser presisjonsdata
- Finn optimal ladning

#### 📦 Lagermodul
- Spor krutt, kuler, tennhetter
- Få varsler når lavt på lager
- Kostnadssporing
- Bestillingshistorikk

#### 🔫 Rifles & Optikk
- Legg til dine rifles
- Konfigurer optikk
- Koble optikk til rifle
- Spor løpslevetid

#### 📊 Analyse
- Grafer over presisjon
- Hastighet scatter plots
- Kostnad per skudd
- Sammenlign ladninger

#### 📝 Loggføring
- Dokumenter alle ladeøkter
- Spor skyteøkter
- Historikk og trendanalyse
- Notater og observasjoner

---

## ⚠️ VIKTIG SIKKERHET

### LES DETTE FØR BRUK!

#### Dette programmet KAN:
✅ Hjelpe med beregninger
✅ Organisere data
✅ Analysere resultater
✅ Spare tid

#### Dette programmet KAN IKKE:
❌ Erstatte lastmanualer
❌ Garantere sikkerhet
❌ Erstatte erfaring
❌ Sjekke fysiske tegn på høyt trykk

### Alltid følg disse reglene:

1. **Start lavt, gå sakte**
   - Begynn under max anbefalt ladning
   - Øk i små steg (0.2-0.3 grains)

2. **Bruk lastmanualer**
   - Konsulter flere kilder
   - Følg anbefalte max-verdier
   - Aldri overskrid maks

3. **Sjekk for trykkegn**
   - Flate/krusede primers
   - Tunge løftspor
   - Stramme hylser
   - Kratering rundt slag

4. **Eget skjønn**
   - Stol på erfaring
   - Stopp ved mistenkelige tegn
   - Spør eksperter ved tvil

---

## 🐛 FEILSØKING

### Programmet starter ikke
1. Sjekk at Python er installert
2. Kontroller at du er i riktig mappe
3. Sjekk at virtual environment er aktivert

### Beregninger gir rare verdier
1. Sjekk input-verdier (realistische?)
2. Kontroller enheter (fps vs m/s)
3. Verifiser BC-verdier (fra produsent)

### Database-feil
- Slett `data/reloading.db` og start på nytt
- Programmet vil gjenopprette tabellene

---

## 📞 HJELP & STØTTE

### Spørsmål?
- Les PROSJEKTOVERSIKT.md for tekniske detaljer
- Les README.md for generell info

### Funnet en bug?
- Noter nøyaktig hva du gjorde
- Hva var resultatet?
- Hva forventet du?

### Feature-forslag?
- Beskriv funksjonen
- Hvorfor er den nyttig?
- Eksempel på bruk

---

## 🎉 NESTE STEG

1. **Utforsk Programmet**
   - Klikk rundt i alle tabs
   - Test Zero Shift Calculator
   - Kjenn deg frem

2. **Kom med innspill**
   - Hva liker du?
   - Hva mangler?
   - Hva kan forbedres?

3. **Vente på oppdateringer**
   - Rifles Manager kommer snart
   - Lagermodul under utvikling
   - Test Lab planlagt

---

**Lykke til med hjemmeladingen! 🎯**

*Husk: Start lavt, gå sakte, vær trygg!*
