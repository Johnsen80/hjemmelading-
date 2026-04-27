# Scientific Accuracy TODO

Dette dokumentet samler neste forbedringsrunde for a gjore Hjemmelading mer nøyaktig,
mer konsistent og mer vitenskapelig troverdig pa tvers av ladeutvikling, ballistikk,
rapporter og kart.

## Maalbilde

- En felles ballistikkmotor som brukes av alle relevante moduler.
- Et tydelig skille mellom:
  - `measured inputs`
  - `ballistics engine`
  - `calibration layer`
  - `advisory layer`
- Et tydelig skille mellom:
  - `målt`
  - `modellert`
  - `utledet`
  - `anbefalt`
- Mer konsistent bruk av miljodata, dragmodell og kalibrering.
- Felles tverrmodul-verifisering slik at samme input gir samme svar overalt.
- En lokal, larende motor som forbedrer seg gjennom malte data uten ekstern AI.

## Last retning for vitenskapelig motor

- Motoren skal vaere lokal og fullt brukbar offline.
- Motoren skal ikke bruke OpenAI eller annen ekstern generativ AI for kjerneanalyser eller anbefalinger.
- Laringssporet skal bygges fra kalibrering, historikk, lotrespons, våpenprofil og eksplisitt evidens.
- Alle sentrale råd skal kunne spores tilbake til fysikk, datagrunnlag, confidence og uncertainty.
- Ingen modell skal late som den er mer eksakt enn datagrunnlaget tillater.

## Lokal læringsmotor som del av Scientific Core

- [ ] Definere ett felles laringsobjekt per våpen og pipe med bias, confidence, uncertainty og robustness.
- [ ] Definere hvordan lot-laring for kule, krutt, tennhette og hylse mates inn i samme motor.
- [ ] La laringsmotoren oppdatere anbefalt neste steg og anbefalingsstyrke automatisk nar nye målinger lagres.
- [ ] Skille eksplisitt mellom referansedata, målt brukerdata og kalibrerte modellparametre i all motorlogikk.
- [ ] Gi alle sentrale resultater en modellstatus som minst viser `rå modell`, `delvis kalibrert` eller `godt kalibrert`.
- [ ] Kreve at rådgivningslaget forklarer hvilke målinger som raskest vil redusere usikkerheten videre.

## Vitenskapelig korrekthet: obligatoriske kvalitetsspor

- [ ] Kreve at sentrale prediksjoner får eksplisitt uncertainty-band der datagrunnlaget er godt nok.
- [ ] Kreve at alle kritiske råd viser svakeste antakelse og viktigste verifiseringsbehov.
- [ ] Bygge et referansedatasett for regression og holdout-testing av fart, drop, impact og arbeidsvindu.
- [ ] Teste systematisk at samme input gir samme resultat i workflow, builder, ballistikkvisning og rapporter.
- [ ] Lage en egen verifikasjonsrunde for temperaturrespons, lotrespons, cold-bore drift og case-capacity-variant.

## Arkitektur: Scientific Core

### Felles ballistikkmotor

- [ ] Samle drop, drift, velocity at distance, energi og impact-vurdering i ett felles motorlag.
- [ ] Fjerne modulspesifikke småberegninger der samme logikk allerede finnes et annet sted.
- [ ] La disse modulene hente resultater fra samme beregningslag:
  - `Drop Chart`
  - `Zero Shift`
  - `Modern Load Builder`
  - `Ladeutvikling`
  - `Ammo Test Lab`
  - rapport-/PDF-sporet
- [ ] Definere ett felles resultatobjekt for ballistiske løsninger som kan brukes i tabeller, grafer og rapporter.

### Lagdeling

- [ ] Lage et eksplisitt `core measured inputs`-lag for:
  - chrono
  - target
  - miljodata
  - våpen/pipe
  - lotkontekst
- [ ] Lage et felles `ballistics engine`-lag for:
  - dragmodell
  - miljokorreksjon
  - hastighet
  - drop
  - drift
  - energi
- [ ] Lage et felles `calibration layer` for:
  - muzzle velocity offset
  - temperaturrespons
  - cold-bore drift
  - pipe/løp-offset
  - lotrespons
- [ ] Lage et felles `advisory layer` for:
  - confidence
  - uncertainty
  - evidence quality
  - anbefalt neste steg

## Miljødata som first-class input

- [ ] Gjore temperatur, trykk, høyde og luftfuktighet til standard input i ekstern ballistikk.
- [ ] Beregne og lagre `density altitude` som avledet standardverdi.
- [ ] Vise tydelig om miljodata er:
  - `målt`
  - `importert`
  - `antatt`
  - `standard`
- [ ] Definere konservative fallback-verdier nar data mangler.
- [ ] La confidence/uncertainty falle nar miljodata er antatt i stedet for målt.
- [ ] Bruke samme miljologikk i:
  - `Drop Chart`
  - `Zero Shift`
  - `Impact Window`
  - `Ammo Test Lab`
  - rapporter

## Dragmodell og aerodynamikk

### Felles dragdatamodell

- [~] Stotte `Auto / G1 / G7` som felles arbeidsstandard i appen.
- [ ] Vise aktiv dragmodell konsekvent i alle relevante analyser og rapporter.
- [ ] Lagre originaldata separat fra valgt arbeidsmodell.
- [ ] Legge inn støtte for `segmented BC`.
- [ ] Planlegge `custom drag curve` som senere avansert tilleggsfunksjon.

### Nøyaktighetsløft

- [ ] Vurdere transonic-risiko som egen uncertainty-driver.
- [ ] Vurdere om solveren skal støtte Mach-basert Cd-tabell nar den finnes.
- [ ] Gjore det tydelig i UI at enkel BC er et gjennomsnitt, ikke en full dragkurve.
- [ ] Vurdere `spin drift`, `Coriolis` og `aerodynamic jump` som felles motoropsjoner, ikke modulspesifikke særtilfeller.

## Kalibrering som samlet lag

- [ ] Definere én samlet kalibreringsprofil per:
  - våpen
  - pipe/løp
  - kule eller ammomodell
  - lot
  - miljøvindu
- [ ] Bruke pipe-læring, lot-læring og chrono/target-resultater i samme kalibreringsprofil.
- [ ] La kalibreringslaget levere:
  - velocity offset
  - temp sensitivity
  - drag/impact confidence
  - node robustness
  - cold-bore drift
- [ ] Skille mellom:
  - fabrikk- / produsentdata
  - målt brukerdata
  - kalibrerte modellparametre
- [ ] Lage en tydelig modellstatus:
  - `rå modell`
  - `delvis kalibrert`
  - `godt kalibrert`

## Input-kvalitet og evidens

- [ ] Lage en felles kvalitetsvurdering før kritiske beregninger kjøres.
- [ ] Sjekke eksplisitt:
  - har vi nok chrono?
  - er BC kjent?
  - er miljodata målt eller antatt?
  - matcher kule faktisk kaliber?
  - er lotdata gyldige?
  - er dataene ferske nok?
- [ ] Senke anbefalingsstyrke nar input-kvaliteten er lav.
- [ ] Tydelig markere nar dårlig input gir bred uncertainty.
- [ ] Knytte kvalitetsnivået til `evidence quality`.

## Kart og terreng

### Fase 1: Terrengrisiko

- [ ] Lage `terrengrisiko` i kartmodulen i stedet for a late som vi har full CFD / mikroklima-solver.
- [ ] Vurdere skuddlinjen mot:
  - vann
  - myr
  - åpent berg
  - dal / renne
  - rygg / sadel
  - stor høydeforskjell
- [ ] Lage praktiske risikoflagg som:
  - mulig termikk
  - mulig kanalvind
  - mulig leeside-turbulens
  - mulig mirage-risiko
- [ ] Vise lav / middels / høy terrengpåvirkning med forklaring i UI.

### Fase 2: Segmentert miljømodell

- [ ] Segmentere skuddlinjen i delstrekninger.
- [ ] Knytte høyde, terrengtype og eventuell vind til hver delstrekning.
- [ ] Bruke dette som risikoscore eller korreksjonsstotte, ikke falsk eksakt sannhet.

## Små detaljer som kan gi reell nøyaktighetsgevinst

### Indre ballistikk

- [ ] Vektlegge faktisk case capacity sterkere i modell og validering.
- [ ] Beregne fyllrate / `load density` fra case capacity og kruttets bulk density.
- [ ] Markere når ladningen er lavt fylt, normalt fylt, hoy fyllrate eller komprimert.
- [ ] Estimere `burn completeness` / forbrent andel ved gitt pipelengde som modellert verdi, ikke malt sannhet.
- [ ] Bruke fyllrate og burn completeness som del av QA, temperaturtolkning og trykk/usikkerhetsvurdering.
- [ ] Vurdere netto settedybde / jump som volumdriver, ikke bare COAL.
- [ ] Fange opp risiko ved repeated rechambering / set-back.
- [ ] Spore ammo-temperatur separat fra lufttemperatur der det er relevant.
- [ ] Vurdere neck tension / neck-tykkelse / annealing-status som konsistenssignal.
- [ ] La primerlot inngå tydeligere i ignition-/SD-vurdering.
- [ ] Vurdere kruttlot som egen temp-/pressure-driver, ikke bare speed-offset.
- [ ] Behandle `Optimal Barrel Time` som en heuristisk nodeindikator, ikke som absolutt sannhet.
- [ ] Skille tydelig mellom:
  - `OBT-estimat`
  - målt node / gruppenode
  - målt velocity-plateau
- [ ] La OBT-rådet bygges på faktisk eller simulert `barrel time`, men krev bekreftelse med chrono og target før status løftes.

### Ytre ballistikk

- [ ] Bruke sight height, zero offset og shot angle konsekvent i samme motor.
- [ ] Vurdere `density altitude` eksplisitt i UI, ikke bare skjult i korreksjonene.
- [ ] Vurdere gyroskopisk stabilitet som confidence-signal i solveren.
- [ ] Vurdere vindgradient / flere vindsoner senere i stedet for kun én global vindverdi.
- [ ] Vurdere transonic uncertainty og modellovergang som egen kilde til økt usikkerhet.
- [ ] Unngå å late som OBT alene forklarer ytre treffpunkt; koble alltid OBT mot faktisk muzzle state, velocity-spread og miljødata.

### Terminal ballistikk

- [ ] Fortsette med konservativ `Impact Window`, ikke "stopping power".
- [ ] Knytte terminalvurdering til:
  - anslagshastighet
  - energi
  - momentum
  - kulekonstruksjon
- [ ] Stotte kule-spesifikke minimums- og optimum-vinduer der produsentdata finnes.
- [ ] Vise tydelig nar terminalvurdering bygger pa produsentkrav kontra målt/utledet data.

## Datamodell: kule, hylse, krutt og tennhette

### Kuledata

- [ ] Beholde:
  - vekt
  - diameter
  - lengde
  - type
  - BC G1/G7
- [ ] Utvide med:
  - drag model source
  - segmented BC
  - custom drag curve reference
  - minimum impact velocity
  - recommended impact velocity band
  - expansion / fragmentation notes
  - meplat / form factor nar data finnes

### Hylsedata

- [ ] Beholde:
  - case capacity
  - vekt
  - neck thickness
  - prep- og firinghistorikk
- [ ] Utvide med:
  - capacity sample count
  - case capacity variance
  - brukbart netto hylsevolum for fyllrateberegning
  - primer pocket condition trend
  - neck tension target / measured
  - lot-level consistency score

### Krutdata

- [ ] Beholde:
  - type
  - burn-rate-relatert data
  - lot-læring
- [ ] Utvide med:
  - bulk density / load-density-grunnlag
  - temperature response model
  - lot-to-lot drift summary
  - modellert burn completeness / uforbrent-krutt-risiko
  - conditioning / storage notes
  - supersonic/transonic confidence hvis solveren bygger pa publiserte dragdata

### Tennhettedata

- [ ] Beholde:
  - primer type
  - lot-læring
- [ ] Utvide med:
  - ignition consistency score
  - misfire / weak ignition logikk
  - temperatur- eller kuldefølsomhet nar data finnes

## Tverrmodul-verifisering

- [ ] Lage faste referansecaser for ekstern ballistikk.
- [ ] Verifisere at samme input gir samme:
  - drop
  - drift
  - velocity at distance
  - impact estimate
  - zero shift
  i alle moduler.
- [ ] Lage egne kontrollcaser for:
  - G1 vs G7
  - density altitude
  - kalibrert vs ukalibrert motor
  - målt vs antatt miljø
- [ ] Lage regresjonstester for gamle profiler slik at ny motor ikke bryter eksisterende arbeidsflyt.

## Foreslått rekkefølge

### 1.0+

- [ ] Felles drag-/ballistikk-helper
- [ ] Felles miljøobjekt med density altitude
- [ ] Felles kalibreringsprofil
- [ ] Input-quality / evidence-gating
- [ ] Terrengrisiko fase 1
- [ ] Tverrmodul-referansetester

### 1.1

- [ ] Segmented BC
- [ ] Mer samlet solver-kalibrering fra faktisk skyting
- [ ] Bedre terminalvindu per kulemodell
- [ ] Segmentert miljømodell langs skuddlinjen

### 2.0

- [ ] Custom drag curve
- [ ] Mer avansert terreng-/vindsegmentering
- [ ] Dypere personalisert drag-/kalibreringsmodell per våpen og pipe
