# Dokumentasjon

## Start Her

- Se [programbeskrivelse.md](programbeskrivelse.md) for oppdatert programbeskrivelse og funksjonsoversikt.
- Se [load_product_roadmap.md](load_product_roadmap.md) for låst videre retning og roadmap for ladedelen.
- Se [load_block1_execution_plan.md](load_block1_execution_plan.md) for operativ gjennomføringsplan for første utviklingsblokk i ladekjernen.
- Se [load_block1_technical_backlog.md](load_block1_technical_backlog.md) for teknisk restliste og fil-for-fil rekkefølge for Blokk 1.
- Se [weapon_learning_domain_model.md](weapon_learning_domain_model.md) for domenemodellen bak våpenplattform, pipe, batch, testsløyfe og selvlæring.
- Se [weapon_learning_schema_plan.md](weapon_learning_schema_plan.md) for konkret schema-, migrasjons- og kompatibilitetsplan.

## Installasjon

1. Klon repoet fra GitHub
2. Installer nødvendige avhengigheter (se requirements.txt og dev-requirements.txt)
3. Opprett og aktiver virtuelt miljø
4. Kjør programmet med hovedfilen (main.py)

## Bruk

- Start programmet og følg instruksjoner i UI
- Importer data via CSV, bilder eller sensorer
- Bruk hovedområdene i appen:
  `Ladeutvikling`, `Prosjekter`, `Ballistikk`, `Lager og batcher`, `Våpenprofiler`, `Lab og testing`, `Innstillinger`
- Start vanligvis i `Ladeutvikling` eller `Våpenprofiler` når du skal begynne nytt arbeid
- Startsider viser nå også enkel status for prosjekt, profiler, batcher og lager slik at du ser hvor du bør fortsette
- `Ladeutvikling` binder nå sammen testplan, batch, chronograph og target-analyse med delt workflow-kontekst
- `Ladeutvikling` har nå også `Bruksprofil`, slik at workflowen kan styre testplan forskjellig for presisjon, trening og jakt
- Trykk- og spike-risiko vises nå både i builder og i workflowens testplan-/arbeidssteg
- Jaktstyrte workflows har nå også første versjon av `Impact Window`, med enkel `confidence` og `uncertainty` rundt anslagshastighet og kulevindu
- Lotverifisering, readiness, `best next test` og komponentrobusthet har nå også egne confidence-/uncertainty-lag
- Startsidene og workflow-detaljene viser nå samlet `Evidenskvalitet`, med korte checks som forklarer hva som trekker vurderingen opp eller ned
- Hovedlandingen og startsidene viser nå også aktiv workflow-status og anbefalt neste handling
- Anbefalt neste handling åpner nå også riktig verktøy med riktig fokus for `stop`, `trenger data` og `ready`
- Importsporet er også strammet inn med mer tolerant CSV/GRT-mapping og fungerende JSON/CSV-import/eksport i `component_database` for bullets og powders
- Import/eksport har nå også runde-trip-testgrunnmur for sentrale dataflyter
- Historikk- og komponenteksport har nå også enkel schema-versjonering og eksportmetadata i JSON/CSV
- ORM-basert CSV-eksport for krutt og kuler har nå også egen schema-kolonne
- Enhetssystemet har nå fått faktisk grunnmur for mm/in, grains/gram, fps/mps, yards/meters og psi/bar, og brukes allerede i `Drop Chart`, `Våpenprofil`, `Chronograph`, `Target Analyzer`, `Batch Workspace` og `Historikk`
- I18n-sporet har nå faktisk grunnmur med fallback, manglende-nøkkel-rapportering og synlig språkstatus i settings
- Felles i18n-tekst brukes nå også i settings, startsider, `Batch Workspace`, `Ladeutvikling`, `Modern Load Builder` (inkludert sentrale dialoger og safety/status), `Chronograph Import`, `Target Analyzer`, `Historikk` og `Component Database`
- Neste store produktretning er å sy sammen en mer vitenskapelig `Scientific Core` med tydelig skille mellom målte data, modellerte data, confidence og anbefalinger
- Jaktspor og kuleoppførsel skal bygges inn i `Ladeutvikling`, med `Bruksprofil`, `Impact Window` og mer forsiktig terminal vurdering
- En sentral videre retning er også å gjøre systemet selvlærende per våpen og pipe/løp, som en digital tvilling bygget på chrono, target, H2O, temperatur og historikk
- Den samme selvlæringen utvides nå også til komponentnivå: hylselotter har egen læringsprofil, og kruttlotter har fått første læringsgrunnmur med velocity-/driftoppsummering i `Component Lot Tracker`
- BC-/dragsporet har nå global `Auto / G1 / G7`-arbeidsstandard og brukes i `Drop Chart`, ammo-profiler, wizard, builder, `Zero Shift` og `Ladeutvikling`
- Neste vitenskapelige hovedretning er en felles `Scientific Accuracy Core` for ballistikkmotor, miljodata, kalibrering, input-kvalitet og terrengrisiko
- Internballistikksporet utvides også med fyllrate, kompresjonsgrad og modellert `burn completeness` i builder, QA og senere patronvisning
- `All Tools`/klassiske faner regnes nå som legacy-verktøybibliotek, mens startsidene og workflow-flytene er de anbefalte 1.0-inngangene

## Utvikling

- Kjør tester med pytest
- Standard kjernesuite kjøres med:
  `./run_core_tests.ps1`
- Alternativt direkte med:
  `.github/.tool-venv/Scripts/python.exe -m pytest -q -m core`
- `core` dekker den stabile moderne regresjonspakken for imports, app-shell, ballistikk, chronograph, harmonikk, research og analyse
- `core` er også koblet til CI og er standardkommandoen for rask verifisering av prosjektet
- Katalogsikkerhet kan også kjøres eksplisitt med:
  `.github/.tool-venv/Scripts/python.exe -m src.tools.catalog_engine_regression_check --report-json .github/data/exports/catalog_engine_regression_check.audit.json --report-md .github/data/exports/catalog_engine_regression_check.audit.md`
- Denne sjekken sammenligner rå og rensede katalogimporter end-to-end og verifiserer at motorrelevante felter i bullets, powder og powder_database er identiske
- Den moderne testsuiten holdes grønn som del av den løpende 1.0-verifiseringen
- Kodekvalitet kan nå også sjekkes med:
  `.github/.tool-venv/Scripts/python.exe -m ruff check src tests`
- Verktøymiljøet kan bygges rent opp igjen med:
  `powershell -ExecutionPolicy Bypass -File tools/rebuild_tool_venv.ps1`
- Aktive moduler i `src/modules` er ryddet for gamle `src.*`-/`HjemmeladingApp.*`-importmønstre, så videre feiljakt bør i større grad handle om faktiske bugs og flytproblemer
- Bruk pre-commit hooks for kodekvalitet
- Følg roadmap og todo-liste for videre utvikling
- Se [project_todo.md](project_todo.md) for aktiv arbeidsliste for struktur, arbeidsflyt og kalibrering
- Se [load_product_roadmap.md](load_product_roadmap.md) for produktprioritering og faseplan for ladekjernen
- Se [scientific_accuracy_todo.md](scientific_accuracy_todo.md) for neste fase rundt nøyaktighet, ballistikkmotor, miljodata og terrengsporet
- Se [release_checklist_1_0.md](release_checklist_1_0.md) for konkret sluttløp mot 1.0

## Feilhåndtering

- Feilmeldinger logges i logs/-mappen
- Sjekk loggene ved problemer

## Kontakt

- For spørsmål eller forslag, kontakt prosjektansvarlig

## Visual C++ og Qt/PySide

For å bygge og kjøre GUI-applikasjonen må du ha:
- Visual C++ redistributable installert
- Python 3.11 for `.github/.tool-venv`
- PyQt6 installert i verktøymiljøet
- PySide6 bare hvis du eksplisitt trenger dobbel binding-støtte lokalt

Se docs/pyside_qt_checklist.md for sjekkliste og feilsøking.

### Test
Kjør en enkel Qt-importtest for å verifisere verktøymiljøet:

  C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/.tool-venv/Scripts/python.exe -c "import PyQt6.QtCore; print('PyQt6 ok')"

---

Oppdater denne filen etter hvert som funksjoner og behov endres.
