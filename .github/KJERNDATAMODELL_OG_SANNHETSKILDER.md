# Kjernedatamodell og sannhetskilder

## Formål

Dette dokumentet fryser den praktiske kjernedatamodellen for Hjemmelading slik den skal forstås videre i produktet.

Målet er å unngå:

- flere parallelle sannheter
- uklar eierskap til data
- at UI og tjenester tolker de samme dataene forskjellig
- at gammel ingest-tenkning fortsetter å lekke inn i sluttproduktet

## Hovedregel

Programmet skal tenke slik:

- våpenprofil + aktiv pipe + brass-baseline + komponentlotter + ladning + målinger + simulering/referanse = beslutningsgrunnlag

## Kjerneobjekter

### 1. Våpenprofil

Rolle:

- toppnivå for våpenets identitet og faste kontekst

Sannhetskilde:

- `rifles`
- utvidet profilinnhold i våpenprofil-/detaljlag

Skal eie:

- våpenidentitet
- kaliberkontekst
- produsent/modell
- overordnet notat- og historikkontekst

Skal ikke eie:

- pipe-spesifikke målinger
- lotter
- konkrete ladningsmålinger

### 2. Pipeprofil

Rolle:

- operativ enhet for analyse, simulering og læring

Sannhetskilde:

- pipe-/barrel-data under våpenprofil
- aktiv pipevalg

Skal eie:

- pipelengde
- twist
- rifleretning
- pipeprofil/kontur
- innfestning
- fri flukt
- demper/brems/kompensator
- harmonikkrelevante felt
- brass-baseline for akkurat denne pipa
- testhistorikk for akkurat denne pipa

### 3. Brass-baseline

Rolle:

- pipe-spesifikk fysisk baseline for skutte hylser

Sannhetskilde:

- `case_measurements` under pipeprofil / barrel
- senere eventuelle egne tabeller for mer moden lagring

Skal eie:

- H2O / case capacity
- H2O-serie og spredning
- trimlengde
- neck-diameter
- shoulder bump
- base-to-datum
- notat om hva som formet baseline

Skal være tydelig skilt fra:

- generell case-/hylsekatalog
- konkrete testobservasjoner etter enkeltskyting

### 4. Komponentmasterdata

Rolle:

- produktets eget masterbibliotek for kuler, krutt, tennhetter og hylser

Sannhetskilde:

- database-tabeller for komponenter
- egne eksporterte og berikede masterfiler under `.github/data/exports`

Deles i:

- kulemaster
- kruttmaster
- tennhettemaster
- hylsemaster

Hovedregel:

- dette er våre masterdata i produktet
- opprinnelig ingest-kilde er ikke produktets domene

### 5. Komponentlotter

Rolle:

- brukerens virkelige, målbare komponentvirkelighet

Sannhetskilde:

- `component_lots`
- lot-statistikk og lot-læringsprofiler

Skal eie:

- lotnummer
- beholdning
- måleserier
- læringsprofil
- risiko/trykktegn/konfidens

Hovedregel:

- lot-data skal kunne overstyre masterdata når brukerens målte data er bedre

### 6. Ladning

Rolle:

- kjernen i arbeidsflyten

Sannhetskilde:

- `ammo_profiles`

Skal eie:

- valgt våpenprofil
- valgt pipe
- valgt kule / krutt / tennhette / hylse
- valgte lotter
- charge
- COAL / CBTO / seating
- brukerens intensjon og oppsett

Skal ikke alene tolkes som hele sannheten.

En ladning må alltid leses sammen med:

- pipe
- brass
- lotter
- målinger

### 7. Målinger

Rolle:

- faktisk evidens

Sannhetskilde:

- chrono-tabeller
- presisjonstester
- trykktegn
- pipehistorikk / testhistorikk
- samlingsbilder

Deles i:

- kronograf
- presisjon
- trykkobservasjoner
- miljø/temperatur
- bildebevis

### 8. Referanse og simulering

Rolle:

- modellert og/eller importert støtte, ikke absolutt fasit

Sannhetskilde:

- samlet analysemotor i `src/ballistics/services.py`
- referansedata lagret i egne rader/tabeller der det er relevant

Hovedregel:

- simulert og referansebasert data skal alltid være tydelig skilt fra målt data

### 9. Evidens, helse og tillit

Rolle:

- oppsummert lesbarhet og risikovurdering for brukeren

Sannhetskilde:

- felles service-lag i `src/modules/load_data_service.py`
- underliggende oppsummering i dagens implementasjon

Skal eie:

- evidensoppsummering
- helseoppsummering
- tillitskart
- lottnivå
- brassnivå
- historikknivå

## Prioritet mellom datalag

Når flere datakilder finnes for samme verdi, skal systemet prioritere slik:

1. Brukerens målte data for valgt lot / valgt pipe / valgt ladning
2. Brukerens lagrede lot-data og pipe-baseline
3. Våre transformerte og berikede masterdata
4. Våre avledede/heuristiske verdier
5. Antatte standardverdier

## Hva som ikke skal være egen sannhetskilde

Dette skal ikke være endelig produktdomene:

- gammel ingest-bro
- gamle kompatibilitetsnavn
- gammel kildeidentitet som lekker inn i UI
- rå importer uten normalisering

Disse finnes bare for overgang, migrasjon eller revisjon.

## Tjenestelag som skal regnes som hovedinnganger

Videre arkitektur skal primært bygges rundt:

- `src/ballistics/services.py`
- `src/modules/load_data_service.py`
- `src/modules/profile_insights_service.py`

Disse skal være de tydelige hovedinngangene for:

- analyse
- ladningskort
- evidens
- helse
- tillit
- referanseoppsummering

## Praktisk konsekvens for videre arbeid

Før nye store funksjoner bygges skal vi sjekke:

- skriver funksjonen til riktig sannhetskilde?
- leser den data via riktig tjenestelag?
- blander den målt, simulert og antatt data feil?
- skaper den ny parallell logikk som burde ligge i felleslag?

Hvis svaret er ja på siste punkt, skal den ryddes før vi bygger videre.
