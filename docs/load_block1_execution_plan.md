# Blokk 1 Execution Plan

## Samlet sannhetsmodell for ladekjernen

## Status
- Oppdatert: 2026-04-10
- Gjelder: første operative utviklingsblokk i ladedelen

## Formål

Blokk 1 skal fjerne tvil om hvor aktiv ladetilstand, aktiv pipekontekst og aktiv evidens egentlig bor.

Dette er ikke en ny featureblokk.

Dette er en konsolideringsblokk som skal gjøre resten av produktet mer pålitelig å bygge videre på.

## Hva problemet er i dag

Prosjektet har allerede sterke byggesteiner, men aktiv ladeutvikling er fortsatt spredt mellom flere flater:

- `smart_loading_wizard.py`
- `modern_load_builder.py`
- `load_development_workflow.py`
- `batch_workspace.py`
- workflow-kontekst i `QSettings`
- eldre / legacy lastesession-spor

Resultatet er at:

- brukeren ikke alltid ser hva som er den egentlige sannhetskilden
- samme aktive kontekst flyter via flere baner
- noen moduler leser direkte fra runtime/session, andre fra workflow context, andre fra lokale snapshots

## Låst beslutning

For denne blokken gjelder følgende som hard regel:

`load_development_sessions` + et felles runtime-lag skal være eneste kanoniske sannhetskilde for aktiv ladeutvikling.

Det betyr:

- nye flater skal ikke lage egne parallelle runtime-modeller
- `QSettings`-kontekst skal være arbeidskontekst, ikke domenesannhet
- `load_development_workflows` skal eie planlegging og metodikk, ikke live session truth
- `batch_workspace` skal være oppfølgingsflate, ikke alternativ eier av aktiv session

## Primære sannhetskilder

### 1. Aktiv runtime/session

Kanonisk:
- `load_development_sessions`

Denne skal eie:
- valgt rifle
- valgt pipe
- valgt pipekonfigurasjon
- valgt bruksprofil
- aktive komponenter
- aktive lotter
- recommendation state
- evidence summary
- learning state
- confidence/safety state
- next action

Tjenestelag:
- [load_development_session_service.py](C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/src/tools/load_development_session_service.py)
- [load_session_runtime_service.py](C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/src/tools/load_session_runtime_service.py)

### 2. Plan og metodikk

Kanonisk:
- `load_development_workflows`

Denne skal eie:
- protokollvalg
- testmetodikk
- exit criteria
- usage profile
- planleggingslogikk

Skal ikke eie:
- endelig live komponenttilstand for aktiv session

### 3. Målt evidens

Kanoniske tabeller:
- `chronograph_sessions`
- `chronograph_readings`
- `rifle_accuracy_tests`
- batch-relaterte evidensrader
- trykk-/primer-/observasjonsspor som peker tilbake til `load_session_id`

Viktig prinsipp:
Ny målt evidens skal så langt det er praktisk knyttes tilbake til `load_session_id` og riktig pipekonfigurasjon.

### 4. Arbeidskontekst i UI

Midlertidig kontekst:
- `QSettings` under `workflow_context/*`

Denne skal brukes til:
- navigasjon
- fokus
- gjenåpning av riktig verktøy
- huske hva brukeren jobbet med

Denne skal ikke brukes som eneste sannhetskilde når en modul kan lese fra `load_development_sessions`.

## Hvilke moduler som skal justeres først

### A. Smart Loading Wizard

Fil:
- [smart_loading_wizard.py](C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/src/modules/smart_loading_wizard.py)

Rolle etter blokk 1:
- guided intake
- opprette / oppdatere `load_development_session`
- skrive navigasjonskontekst til `QSettings`
- sende brukeren videre til riktig arbeidsflate

Skal ikke:
- være separat eier av aktiv runtime

### B. Modern Load Builder

Fil:
- [modern_load_builder.py](C:/Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\src\modules\modern_load_builder.py)

Rolle etter blokk 1:
- primær ekspertflate
- lese aktiv runtime fra felles runtime service
- vise og oppdatere samme session state

Skal ikke:
- bygge opp en konkurrerende, skjult sessionmodell som bare lever inne i widgeten

### C. Load Development Workflow

Fil:
- [load_development_workflow.py](C:/Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\src\modules\load_development_workflow.py)

Rolle etter blokk 1:
- protokoll
- plan
- metodikk
- usage profile
- readiness og next-step-logikk

Skal ikke:
- bli alternativ live-eier av komponenttilstand og aktiv session

### D. Batch Workspace

Fil:
- [batch_workspace.py](C:/Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\src\modules\batch_workspace.py)

Rolle etter blokk 1:
- oppfølging av batch og verifisering
- lese aktiv load context fra runtime/session ved behov
- skrive målt evidens tilbake til samme læringssløyfe

Skal ikke:
- bli isolert øy for egen sannhet om oppsettet

### E. Chronograph Import / Target Analyzer / Safety Dashboard

Filer:
- [chronograph_importer.py](C:/Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\src\modules\chronograph_importer.py)
- [target_analyzer.py](C:/Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\src\modules\target_analyzer.py)
- [safety_dashboard.py](C:/Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\src\modules\safety_dashboard.py)

Rolle etter blokk 1:
- bruke `workflow_context` som inngang for fokus
- validere og berike mot faktisk `load_development_session`
- skrive evidens tilbake med `load_session_id` og pipekonfigurasjon

## Konkrete leveranser

## Leveranse 1 - Canonical runtime payload

Lag eller styrk ett felles runtime-objekt som minst samler:

- session identity
- rifle identity
- barrel identity
- barrel configuration identity
- usage profile
- component selection
- component lots
- recommendation state
- evidence summary
- learning state
- confidence/safety summary
- linked batch context

Dette runtime-objektet skal kunne brukes av:

- builder
- workflow details
- batch workspace
- chrono import
- target analyzer
- safety dashboard

## Leveranse 2 - Klar rollefordeling mellom session, workflow og UI-context

Dette skal dokumenteres og håndheves i kode:

- `load_development_sessions` = live runtime truth
- `load_development_workflows` = plan/metodikk
- `workflow_context/*` = navigasjon og fokus

## Leveranse 3 - Felles lesebane for aktiv kontekst

Når en modul åpnes fra hovedflyten, bør den:

1. lese `workflow_context/load_session_id`
2. hente canonical session fra runtime/service
3. validere rifle/barrel/barrel_configuration
4. bruke `workflow_context` bare til fokus dersom noe mangler

## Leveranse 4 - Felles skrivebane for nye målinger

Når chrono, target eller sikkerhetsobservasjoner lagres, skal de så langt mulig få:

- `load_session_id`
- `rifle_id`
- `barrel_id`
- `barrel_name`
- `barrel_configuration_id`
- `barrel_configuration_name`

Målet er at senere læringsmotor ikke trenger å gjette hvilken kontekst målingen tilhører.

## Leveranse 5 - Legacy-rydding i kjerneflyten

Blokk 1 skal identifisere og redusere disse mønstrene:

- aktiv tilstand som bare finnes i widget-instans
- samme kontekst lagret forskjellig i flere moduler
- direkte avhengighet av legacy loading session når canonical session finnes

## Konkrete oppgaver

### Oppgavegruppe A - Kartlegg og lås runtime-kontrakten

- [ ] Dokumentere canonical runtime payload i kode eller docs
- [ ] Verifisere hvilke felter som alltid må finnes
- [ ] Bestemme hvilke felter som kan være fallback-basert

### Oppgavegruppe B - Gjør builder runtime-drevet

- [ ] La builder hente aktiv session via runtime service som hovedbane
- [ ] Redusere lokal duplisering av session state der det er mulig
- [ ] Sikre at oppdateringer skrives tilbake til canonical session

### Oppgavegruppe C - Stram inn workflow context

- [ ] Standardisere hvilke `workflow_context/*`-nøkler som faktisk brukes
- [ ] Sørge for at de peker til canonical session i stedet for å konkurrere med den
- [ ] Dokumentere at `QSettings` er navigasjonskontekst, ikke domenesannhet

### Oppgavegruppe D - Koble evidens tydeligere til session

- [ ] Chronograph import skal alltid forsøke å lagre med `load_session_id`
- [ ] Target analyzer skal alltid forsøke å lagre med `load_session_id`
- [ ] Batch-relatert oppfølging skal tydelig knyttes til session og pipekonfigurasjon

### Oppgavegruppe E - Test og verifisering

- [ ] E2E-test: wizard -> session -> builder
- [ ] E2E-test: builder -> batch -> chrono -> session update
- [ ] E2E-test: builder -> target -> session update
- [ ] E2E-test: riktig pipekonfigurasjon beholdes hele veien

## Definition of done

Blokk 1 er ferdig når:

- det er tydelig i kode og docs at `load_development_sessions` er canonical runtime
- builder, workflow, batch, chrono og target kan lese samme aktive kontekst uten å gjette
- målt evidens skriver tilbake med riktig `load_session_id` og pipekonfigurasjon
- `workflow_context` brukes som navigasjon og fokus, ikke som erstatning for session truth
- minst én ende-til-ende test viser at samme aktive ladning flyter riktig gjennom kjernebanen

Se også [load_block1_technical_backlog.md](load_block1_technical_backlog.md) for fil-for-fil restliste og foreslått kode-rekkefølge.

## Hva som ikke skal løses i denne blokken

Disse temaene er viktige, men de tilhører neste blokker:

- full confidence/uncertainty motor
- spredningslære
- robusthetsmotor
- neste-test-motor
- avansert terminalvurdering
- kart/feltballistikk
- ammo test & lot validation

Blokk 1 skal bare sikre at resten bygges på riktig fundament.
