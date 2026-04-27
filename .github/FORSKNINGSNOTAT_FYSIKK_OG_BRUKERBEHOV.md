# Forskningsnotat: fysikk, modeller og brukerbehov i ladeutvikling

## Status 2026-04-03

Dette notatet samler hvilke fysikkmodeller, matematiske spor og brukerbehov som bor prioriteres videre i plattformen.

Målet er ikke a lage en tilfeldig samling lenker, men a gi et praktisk grunnlag for hva som bor inn i motoren for:

- ladeutvikling
- harmonikk
- stabilitet
- ytre ballistikk
- terminal vurdering
- datakvalitet
- anbefalinger og laering

## Hovedkonklusjon

Programmet kan bli bedre enn Gordon og QuickLOAD hvis det bygger pa fire lag samtidig:

1. standardmotor
2. fysikkmotor
3. evidensmotor
4. beslutningsmotor

Dette betyr:

- standarder setter grenser og kompatibilitet
- fysikk gir prediksjon
- malt data gir kalibrering og sannhet
- beslutningslaget gir anbefaling og neste steg

## 1. Standardmotor: det som bor regnes som fasit

### SAAMI og CIP

Disse ma vaere ryggraden for:

- makstrykk
- proof / sikkerhetsmargin
- patron- og kammergeometri
- hylsemal og kompatibilitet
- referansemal for trim, neck og kammer

Dette bor ikke bare vaere en egen sjekkside. Det bor vaere et internt regelverk som brukes overalt:

- i builderen
- i harmonikkvurderingen
- i internballistikken
- i terminalvurderingen
- i varsler og anbefalinger

### Praktisk regel

Hvis standarddata finnes, skal systemet alltid vite:

- hva som er nominell referanse
- hva som er maalt i brukerens pipe
- hva som er antatt fordi data mangler

## 2. Fysikkmotor: hva som bor brukes videre

### 2.1 Internballistikk

Retningen dere allerede har er riktig:

- Noble-Abel-lignende gassmodell
- Vieille / burn-rate-logikk
- case volume / H2O
- fyllgrad og kompresjon
- temperaturfoelsomhet

Dette bor prioriteres videre:

- maalt H2O fra fireformed brass som aktiv input
- starttrykk / ignition pressure som eksplisitt faktor
- lotpaavirkning som korreksjonsledd
- skille mellom nominell case capacity og maalt case capacity

### 2.2 Stabilitet

Gyroskopisk stabilitet bor bygge pa Miller-regelen eller tilsvarende praktisk modell.

Dette bor brukes i systemet:

- twist
- kulelengde
- diameter
- vekt
- hastighet
- lufttetthet / miljo

Viktig prinsipp:

- stabilitetsresultatet skal presenteres med confidence
- manglende kulelengde eller geometri skal trekke confidence ned
- subsonisk modus skal bruke strengere terskler enn vanlig supersonisk bruk

### 2.3 Harmonikk og barrel time

Harmonikk er viktig, men ma brukes som beslutningsstotte, ikke som absolutt fasit.

Det som bor brukes:

- pipeprofil
- pipelengde
- innfestning
- fri flukt
- demper / brems / munningsutstyr
- brass-baseline
- barrel time
- seating depth
- charge

Det som bor vaere tydelig i UI:

- node-fit
- barrel time
- charge sensitivity
- seating sensitivity
- confidence

### 2.4 Ytre ballistikk

Ytre ballistikk bor bruke:

- G1 / G7 med tydelig resolved drag model
- transsonisk oppforsel
- vindavdrift
- spindrift
- Coriolis og Eotvos i avansert/labmodus

Dette bor styres av bruksmal:

- jakt
- langhold
- presisjon
- subsonisk

### 2.5 Terminal vurdering

Terminal vurdering bor ikke vaere en enkel energiutskrift.

Det bor bygges rundt:

- impact velocity
- impact energy
- kulefamilie og type
- oppgitt arbeidsvindu hvis kjent
- bruksmal

Dette betyr:

- jaktvurdering skal handle om arbeidsvindu og anslagshastighet
- langhold skal ogsa vurdere om kula fortsatt virker i terminalt vindu pa aktuell avstand

## 3. Evidensmotor: hva som gjor systemet smartere enn en ren kalkulator

Dette er det sterkeste konkurransefortrinnet.

Systemet bor bruke:

- kronografserier
- samlingsbilder
- gruppestorrelse
- mean radius der data tillater det
- trykktegn
- brassmalinger
- pipehistorikk
- lotmaalinger
- miljo / temperatur

### Viktig statistisk retning

Systemet bor etter hvert vurdere:

- antall skudd i gruppe
- usikkerhet ved sma serier
- mean radius vs extreme spread
- pooled variance over flere serier
- trend over tid
- forskjell mellom enkeltbra serie og repeterbar node

## 4. Beslutningsmotor: hva brukeren faktisk trenger

Brukeren trenger ikke bare flere tall.

Brukeren trenger:

- trygg startladning
- anbefalt charge-vindu
- anbefalt seating-vindu
- vurdering av risiko
- vurdering av confidence
- forslag til neste test

Systemet bor kunne si:

- denne ladningen ser trygg ut
- denne ligger naer node
- denne er foelsom for seating
- denne har lav confidence fordi brass-baseline mangler
- denne boer verifiseres med chrono
- denne er god for jakt, men ikke sterk nok for langhold

## 5. Hva brukere faktisk ser ut til a onske

Forum- og brukertrader peker ganske stabilt pa disse behovene:

- lokal lagring og offline-forst arbeid
- ett sted for ladning, chrono, targetbilde og notater
- lotnumre og sporbarhet
- enkel sammenligning mellom ladninger
- tydelig skille mellom eksperimentell og verifisert ladning
- lett eksport og dokumentasjon
- temperatur- og lotsporing
- kobling mellom vapen og ladning
- minst mulig Excel-kaos

Det betyr at systemet deres bor prioritere:

- struktur
- sporbarhet
- pipehistorikk
- laering over tid

fremfor a jage for tidlig etter flashy simulatorfunksjoner.

## 6. Hva som bor regnes som sikkert, heuristisk og empirisk

### Sikkert / standardstyrt

- SAAMI / CIP grenser
- patron- og kammerreferanser
- maalte egne data
- enkel fysikk som energi, drop, basic stability input

### Heuristisk

- harmonikk-score
- node-band fra pipeprofil alene
- barrel-time sweet spot uten faktisk kalibrering
- seating-vindu uten pipehistorikk

### Empirisk og meget verdifullt

- chrono-kalibrering
- targetbilder og gruppehistorikk
- fireformed H2O
- lotmaalinger
- retest etter lotbytte
- pipehistorikk med faktisk resultat

## 7. Anbefalt implementeringsprioritet

### Prioritet A

- SAAMI / CIP som aktivt regelverk
- samlet service-lag for anbefaling
- maalt H2O og brass-baseline i internballistikk
- stabilitet med confidence
- harmonikk inn i laddedelen

### Prioritet B

- pipehistorikk med chrono og targetbilder
- bedre statistikk for grupper og presisjon
- bruksmalstyrte anbefalinger
- terminal vurdering per kule og bruksmal

### Prioritet C

- mer avansert 3D
- mer avansert labvisualisering
- tyngre numerisk simulering i avansert modus

## 8. Konkrete forskningsspor som passer godt videre

1. Miller stability som praktisk modell i builderen
2. OBT / barrel-time som heuristisk stotte, aldri som fasit
3. mean radius og sma-serie-statistikk for presisjon
4. ignition pressure og startbetingelser som tydelig internballistisk faktor
5. confidence-modell som skiller mellom:
   - standarddata
   - antatt data
   - maalt data
   - kalibrert data

## 9. Kilder

Standarder og referanser:

- SAAMI standards:
  https://saami.org/technical-information/ansi-saami-standards/
- SAAMI centerfire rifle standard update, 2025-02-12:
  https://saami.org/saami-releases-update-of-centerfire-rifle-standard/
- CIP TDCC:
  https://www.cip-bobp.org/en/tdcc

Stabilitet og ballistikk:

- JBM stability calculator:
  https://www.jbmballistics.com/cgi-bin/jbmstab-5.1.cgi
- JBM drag / twist terms:
  https://jbmballistics.com/ballistics/calculators/help/drag/drag_exp.shtml
- Don Miller stability paper:
  https://www.jbmballistics.com/ballistics/bibliography/articles/miller_stability_1.pdf

Internballistikk og maaling:

- Ignition pressure paper:
  https://www.mdpi.com/1996-1073/15/16/5916
- Dynamic pressure measurement chain in ballistic tests:
  https://www.mdpi.com/1424-8220/23/19/8081
- Internal ballistics modelling:
  https://www.mdpi.com/2227-7390/9/21/2714

Harmonikk og barrel time:

- Chris Long OBT paper:
  https://www.the-long-family.com/OBT_paper.htm
- Varmint Al tuner / vibration analysis:
  https://www.varmintal.com/atune.htm
- Barrel harmonics optimization paper:
  https://www.researchgate.net/publication/370865360_Improving_the_Spreading_Pattern_of_Precision_Rifles_by_Modelling_and_Optimising_Barrel_Harmonics

Presisjonsstatistikk og brukerbehov:

- PrecisionRifleBlog on group statistics:
  https://precisionrifleblog.com/2020/12/12/measuring-group-size-statistics-for-shooters/
- PrecisionRifleBlog on chronograph accuracy:
  https://precisionrifleblog.com/2012/07/20/chronograph-accuracy-tips-15-practical-tips-to-increase-accuracy-reliability/
- Reddit thread about reloading app needs:
  https://www.reddit.com/r/reloading/comments/1qwwl56/reloading_app/
- Reddit thread about inventory and load-development app:
  https://www.reddit.com/r/reloading/comments/1pohtcv/built_an_inventory_load_development_app_for/

## Kort konklusjon

Den viktigste retningen videre er ikke a finne "den perfekte formelen".

Den viktigste retningen er a kombinere:

- standarder
- fysikk
- pipehistorikk
- statistikk
- bruksmalsstyrte anbefalinger

Hvis dette gjores riktig, kan programmet bli langt mer nyttig i praksis enn tradisjonelle reloader-kalkulatorer.
