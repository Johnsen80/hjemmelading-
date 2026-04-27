# Plattform- og produktvalg (beslutninger)

## Status
- Oppdatert: 2026-03-26
- Gjelder: MVP og 1.0 plan

## Plattform og rekkefolge
Beslutning: Windows desktop for MVP. Rekkefolge: Windows -> Web/cloud portal -> Mobilapp.

Begrunnelse: Windows er dominerende i hjemmelading, gir best arbeidsflyt for bilder, kronografdata, store grafer og filimport/eksport, og brukes ogsa i fabrikk/lab.

Konsekvens: Mobil brukes senere til feltdata (registrere skyting, ta bilde av skive, sync), men er ikke hovedplattform.

## Offline-first og cloud
Beslutning: Offline-first med optional cloud sync.

Begrunnelse: Skytebaner har ofte daarlig dekning, og profesjonelle brukere vil ha lokal kontroll over data.

Konsekvens: Lokal database er standard, cloud er tillegg for backup, deling og synk.

## Enheter og dataformat i MVP
Beslutning: Chronograph import via CSV/TXT (LabRadar, Garmin Xero C1 Pro, MagnetoSpeed). Target analyse fra JPG/PNG.

Begrunnelse: Dette er de mest brukte formatene og gir raskest vei til nytte.

Konsekvens: Definer CSV mapping og stott lokale desimaler/units ved import.

## Intern data og eksport
Beslutning: SQLite lokal database med JSON/CSV eksport (PDF senere).

Begrunnelse: Robust, enkel backup og enkel integrasjon.

Konsekvens: Enhetsnormalisering og tydelige skjema for eksport/import.

## Simulering og modell
Beslutning: Start med fysikkbasert modell. ML kommer senere.

Begrunnelse: Transparent, forklarbar, mer troverdig, og fungerer uten store datamengder.

Konsekvens: Dokumenter antakelser, gyldighetsomraade og sikkerhetsgrenser.

Tillegg 2026-03-27:
- neste retning er en `Scientific Accuracy Core` som samler felles ballistikkmotor, miljodata, kalibrering og evidensvurdering under eksisterende moduler
- `Auto / G1 / G7` er etablert som arbeidsstandard, men skal videreutvikles til felles dragdatamodell med senere `segmented BC` og `custom drag curve`
- internballistikksporet skal ogsa omfatte fyllrate, komprimert ladning og modellert `burn completeness` som del av samme scientific core
- terrengsporet skal starte som `terrengrisiko`, ikke som falsk eksakt mikroklima-solver

## Forste kundegruppe
Beslutning: Hobby-reloaders og konkurranseskyttere.

Begrunnelse: Tidlige brukere tester nye verktoy, gir rask feedback og er lettere aa naa.

Konsekvens: MVP prioriterer ladetest, kronografanalyse, skiveanalyse og statistikk.

## MVP ma gi umiddelbar nytte
- Skiveanalyse som gir repeterbare gruppemaal
- Chronograph import og statistikk (avg, ES, SD)
- Strukturert ladetest og historikk per rifle/ammo
- Enkel eksport av data for videre analyse

## Harmoni mellom moduler
- Felles datamodell og enhetssystem paa tvers av UI, import og analyse.
- Felles i18n-lag slik at alle tekster kommer fra samme kilde.
- Felles validering og feilformat for import, skjema og beregninger.
- Felles import/eksport-skjema med versjonering.
- Felles logging og audit-spor for kritiske endringer.

## Modulkoblinger (TODO)
- App shell og nav: [src/ui/main_window.py](src/ui/main_window.py) -> prioriter arbeidsflyter for chronograph, skiveanalyse, ladetest.
- Settings og sprak: [HjemmeladingApp/ui/settings_dialog.py](HjemmeladingApp/ui/settings_dialog.py) + [HjemmeladingApp/i18n.py](HjemmeladingApp/i18n.py) -> lag språkvalg, persistens og fallback.
- Chronograph import: [src/modules/chronograph_importer.py](src/modules/chronograph_importer.py) + [src/utils/chronograph_import.py](src/utils/chronograph_import.py) -> stabil CSV/TXT mapping og locale-decimaler.
- Target analyse: [src/modules/target_analyzer.py](src/modules/target_analyzer.py) + [src/modules/image_analysis.py](src/modules/image_analysis.py) + [src/ui/image_calibration_dialog.py](src/ui/image_calibration_dialog.py) -> skala/perspektiv og robust gruppemaal.
- CSV komponentimport: [src/database/import_csv.py](src/database/import_csv.py) -> feltmapping, validering og klare feil.
- GRT import: [src/modules/grt_importer.py](src/modules/grt_importer.py) + [src/database/import_grtload.py](src/database/import_grtload.py) -> sikre mapping og feilhaandtering.
- Lokal lagring: [src/database/database.py](src/database/database.py) -> SQLite schema, backup/restore og migrering.
- Statistikk: [src/utils/analysis.py](src/utils/analysis.py) + [src/modules/historical_analysis.py](src/modules/historical_analysis.py) -> enhetlige ES/SD/regresjoner.

## App shell status
- Toppnivå i appen er nå strukturert som:
  `Ladeutvikling`, `Prosjekter`, `Ballistikk`, `Lager og batcher`, `Våpenprofiler`, `Lab og testing`, `Innstillinger`.
- Hovedområdene har egne startsider som forklarer rolle, hurtigvalg og anbefalt arbeidsretning.
- Startsider viser nå også enkel status for aktivt prosjekt, profiler, lager, batcher og noen grunnleggende oppmerksomhetspunkter.
- Gjenstående arbeid er å finpusse stegstyring, innholdsprioritering og koblinger mellom workflows.
- Prosjektkontekst flyter nå også videre inn i batcher, loggbok og historikkvisning.
- Workflow-kontekst flyter na også videre mellom `Ladeutvikling`, `Batch Workspace`, `Chronograph Import` og `Target Analyzer`.
- `Ladeutvikling` viser na egne pressure/spike-advarsler i testplan og arbeidssteg, ikke bare i builder-visningen.
- `Ladeutvikling` har na eksplisitt `Bruksprofil` i workflow-wizarden, slik at presisjon, trening og jaktbruk kan styre testplan og neste steg.
- Første versjon av `Impact Window` er na sydd inn i `Ladeutvikling`, startsider og `Modern Load Builder` for jaktstyrte workflows.
- `Impact Window` viser na ikke bare punktestimat, men ogsa enkel `confidence` og `uncertainty` basert pa chrono- og kuledata.
- Lotverifisering viser na ogsa `confidence` og enkel `uncertainty`, ikke bare status og kontrollrad.
- Workflow-readiness, `best next test` og komponentrobusthet har na egne confidence-/uncertainty-lag.
- `Evidenskvalitet` brukes na som et samlet signal over readiness, robusthet, lotverifisering, neste test og impact-vurdering.
- Startsidene og workflow-detaljene viser na ogsa korte evidens-checks som forklarer hva som trekker kvalitetsnivaet opp eller ned.
- Hovedlanding, `Ladeutvikling` og `Prosjekter` viser na aktiv workflow-status og anbefalt neste handling, inkludert direkte apning av siste prosjektbatch nar konteksten er kjent.
- De tre workflow-utfallene `stop`, `trenger data` og `ready` leder na videre til henholdsvis `Target Analyzer`, `Chronograph Import` og `Batch Workspace` med tydelig fokus i hvert verktøy.

## Teststatus
- Standard verifisering er nå `python -m pytest -q -m core`.
- `core` er dokumentert lokalt, har enkle startskript og kjøres i CI.
- `ruff check src tests` er nå også grønn etter opprydding i aktive `src/modules`.
- Aktiv importopprydding i levende `src/modules` er ferdigstilt; videre kvalitetspass bør fokusere på reelle bugs, validering og UX.
- En egen bugjakt-passasje har nå også luket ut flere konkrete runtime-feil i arbeidsflyter med guard-tester rundt.
- Bugjakt-passasjen dekker nå også flere stale-selection og missing-row feil i workflow-resume, component database, measurement wizard, environmental compare, barrel-flyt og andre små UI-baner.
- Hele den moderne testsuiten under `tests/` er nå også grønn (`111 passed`), så statusen er ikke lenger bare lokal `core`-stabilitet, men bred regresjonsdekning i aktiv testmasse.
- Fokus videre bør være å promotere flere moderne arbeidsflyt-tester inn i `core`, ikke å bygge mer parallell testinfrastruktur.
- Importsporet har na ogsa flyttet seg frem: `import_csv.py` og `import_grtload.py` har mer tolerant mapping og tydeligere importrapport, og `component_database.py` har faktisk JSON/CSV-import og eksport for bullets og powders.
- Det finnes na ogsa runde-trip-testgrunnmur for eksport -> import av komponentdata og ORM-basert CSV for krutt og kuledata.
- Historikkeksport og komponentdatabase-eksport har na ogsa enkel schema-versjonering og eksplisitt eksportmetadata, slik at dataflyten blir tryggere a videreutvikle.
- ORM-basert CSV-eksport for krutt og kuler har na ogsa eksplisitt schema-kolonne, slik at baade database- og ORM-sporet bruker samme retning.
- Enhetssystemet har na faktisk grunnmur i `HjemmeladingApp/utils/units.py`, og konverteringene brukes allerede i `drop_chart_generator.py`, `weapon_profile_dialog.py`, `chronograph_importer.py`, `target_analyzer.py`, `batch_workspace.py` og `historical_analysis.py`.
- I18n-sporet har na ogsa faktisk grunnmur med fallback, manglende-nokkel rapportering og synlig status i settings, og felles i18n-tekst brukes i settings, startsider, `Batch Workspace`, `Ladeutvikling`, `Modern Load Builder` (inkludert sentrale dialoger og safety/status), `Chronograph Import`, `Target Analyzer`, `Historikk` og `Component Database`.

## Modul-sjekkliste (MVP)
- [~] (P0) App shell og nav: [src/ui/main_window.py](src/ui/main_window.py)
- [~] (P0) Chronograph import: [src/modules/chronograph_importer.py](src/modules/chronograph_importer.py), [src/utils/chronograph_import.py](src/utils/chronograph_import.py)
- [~] (P0) Target analyse: [src/modules/target_analyzer.py](src/modules/target_analyzer.py), [src/modules/image_analysis.py](src/modules/image_analysis.py), [src/ui/image_calibration_dialog.py](src/ui/image_calibration_dialog.py)
- [~] (P0) Ladetest og historikk: [src/modules/load_development_workflow.py](src/modules/load_development_workflow.py), [src/modules/ladder_test_lab.py](src/modules/ladder_test_lab.py), [src/modules/temperature_ladder_test.py](src/modules/temperature_ladder_test.py), [src/modules/historical_analysis.py](src/modules/historical_analysis.py)
- [~] (P0) Import/eksport: [src/database/import_csv.py](src/database/import_csv.py), [src/database/import_grtload.py](src/database/import_grtload.py), [src/modules/component_database.py](src/modules/component_database.py)
- [ ] (P1) Settings og sprak: [HjemmeladingApp/ui/settings_dialog.py](HjemmeladingApp/ui/settings_dialog.py), [HjemmeladingApp/i18n.py](HjemmeladingApp/i18n.py), [src/utils/i18n.py](src/utils/i18n.py)
- [~] (P1) Enhetssystem: [HjemmeladingApp/utils/units.py](HjemmeladingApp/utils/units.py)
- [ ] (P1) Rapport-MVP: spesifiser modul og format
- [ ] (P2) Cloud-sync: design og konflikthandtering

## TODO (avtalt)
- [ ] Definer Windows MVP krav (installer, oppdatering, maskinvarekrav)
- [ ] Fastsett offline-first lagring og sync-modell (lokal DB + optional cloud)
- [ ] CSV standard og feltmapping for LabRadar, Garmin Xero, MagnetoSpeed
- [ ] Target-kalibrering (maalestokk, perspektiv, referansepunkt)
- [~] Enhetssystem og locale-format (mm/in, fps/mps, desimaler)
- [ ] I18n implementasjon i hele UI, inkl. norsk (se [docs/i18n_requirements.md](docs/i18n_requirements.md))
- [ ] Felles validering/feilformat paa tvers av import, skjema og beregning
- [ ] Felles import/eksport-skjema med versjonering
- [ ] Rapport-MVP format og maler (CSV/JSON, PDF senere)
- [ ] Golden-data testsett og regresjonstester for chronograph og target analyse

## TODO (detaljert per modul)
### App shell og nav
- [x] Definer MVP arbeidsflyter i shell (chronograph, skiveanalyse, ladetest) (se [src/ui/main_window.py](src/ui/main_window.py))
- [~] Lag tomme stater og hjelpetekster for tomme datasett (se [src/ui/main_window.py](src/ui/main_window.py))
- [~] Samme terminologi i nav, titler og menyvalg (se [src/ui/main_window.py](src/ui/main_window.py))
- [~] Gjør startsider mer datadrevne med faktiske varsler og siste brukte objekter (se [src/ui/main_window.py](src/ui/main_window.py))
- [~] Koble Prosjekter, Batch Workspace og historikk tettere sammen med aktiv prosjektkontekst (se [src/ui/main_window.py](src/ui/main_window.py), [src/modules/session_logger.py](src/modules/session_logger.py), [src/modules/historical_analysis.py](src/modules/historical_analysis.py))

### Windows MVP
- [ ] Velg installer og update-strategi (MSI/Inno/auto-update) (se [installer/VALKYRIE_BALLISTICS_installer.iss](installer/VALKYRIE_BALLISTICS_installer.iss))
- [ ] Definer logg- og crash-rapporteringssti (se [scripts/build_windows.ps1](scripts/build_windows.ps1))
- [ ] Definer minimum maskinvarekrav for bildeanalyse

### Offline-first og lagring
- [ ] Fastsett lokal DB plassering og backup/restore flyt (se [src/database/database.py](src/database/database.py))
- [ ] Definer kryptering/tilgang for lokale data (se [src/database/database.py](src/database/database.py))
- [ ] Beskriv sync-konfliktregler (for senere cloud)

### Chronograph import
- [ ] CSV mapping per enhet (LabRadar, Garmin Xero, MagnetoSpeed) (se [src/modules/chronograph_importer.py](src/modules/chronograph_importer.py))
- [ ] Locale-decimaler og robust talltolkning (se [src/utils/chronograph_import.py](src/utils/chronograph_import.py))
- [ ] Klar feilmelding og validering ved import (se [src/modules/chronograph_importer.py](src/modules/chronograph_importer.py))
- [ ] Golden-data tester for import og statistikk (se [src/utils/chronograph_import.py](src/utils/chronograph_import.py))

### Target analyse
- [ ] Kalibrering: maalestokk og referansepunkt (se [src/ui/image_calibration_dialog.py](src/ui/image_calibration_dialog.py))
- [ ] Perspektiv/rotasjon og bildejustering (se [src/modules/image_analysis.py](src/modules/image_analysis.py))
- [ ] Robust hull-detektering med justerbar terskel (se [src/modules/target_analyzer.py](src/modules/target_analyzer.py))
- [ ] Validering mot testbilder (golden data)

### Ladetest og historikk
- [ ] Enhetlig datastruktur for ladder/temperature test (se [src/modules/ladder_test_lab.py](src/modules/ladder_test_lab.py), [src/modules/temperature_ladder_test.py](src/modules/temperature_ladder_test.py))
- [ ] Knytt resultater til rifle/ammo profil (se [src/modules/load_development_workflow.py](src/modules/load_development_workflow.py))
- [ ] Historikkvisning og sammenligning (se [src/modules/historical_analysis.py](src/modules/historical_analysis.py))

### Import/eksport
- [ ] Skjema-versjonering for CSV/JSON eksport (se [src/database/import_csv.py](src/database/import_csv.py))
- [ ] Re-import test (runde-trip) med samme resultat (se [src/database/import_csv.py](src/database/import_csv.py))
- [ ] Stabil feltnavn/units i eksport (se [src/database/import_csv.py](src/database/import_csv.py))

### Enhetssystem
- [~] Bruk ett internt normalformat og konverter i UI (se [HjemmeladingApp/utils/units.py](HjemmeladingApp/utils/units.py))
- [ ] Locale-format ved input, men stabilt format ved lagring (se [HjemmeladingApp/utils/units.py](HjemmeladingApp/utils/units.py))
- [x] Enhetstester for kritiske konverteringer (se [HjemmeladingApp/tests/test_units.py](HjemmeladingApp/tests/test_units.py))

### I18n
- [~] Flytt UI-tekster til felles i18n-lag (se [src/utils/i18n.py](src/utils/i18n.py))
- [~] Implementer fallback og manglende-nokkel rapportering (se [HjemmeladingApp/i18n.py](HjemmeladingApp/i18n.py))
- [ ] Test norsk og engelsk i kjerneflyter (se [docs/i18n_requirements.md](docs/i18n_requirements.md))

### Rapport-MVP
- [ ] Definer minimumsinnhold for rapport (konfig + data + stats)
- [ ] CSV/JSON eksport for MVP, PDF senere

## Faseplan (forslag)
- Phase 1 (MVP): rifleprofiler, ladedata, chronograph, skiveanalyse, statistikk. Plattform: Windows desktop, offline DB.
- Phase 2 (Simulator): intern ballistikk, nodeanalyse, ekstern ballistikk.
- Phase 3 (Cloud): sync, backup, community data.
- Phase 4 (Professional): batchsystem, QA analyse, labmodus.

## Mangler og avklaringer
- Installer og oppdateringsstrategi for Windows
- Synkmodell og konfliktlosning for cloud
- CSV standard og feltmapping per enhet
- Target-kalibrering (maalestokk, perspektiv, referansepunkt)
- Enhetssystem og lokalformat for tall/dato
- Teststrategi med golden data for regresjon

## Smarte tillegg
- Proveniens og audit-logg for alle kritiske data
- Plugin/adapter-lag for nye chronograph-formater
- Sikkerhets-guardrails med tydelige advarsler
- Kontrollkart/SPC for batch og drift over tid
- Rapport-MVP med standard maler og metadata
- Verifisering av bildeanalyse med kalibrerte testsett
- Scientific Core som samler `measured`, `modeled`, `derived`, `confidence` og `uncertainty`
- Felles `Load Evidence Record` for rifle, pipe, batch, chrono, target og jaktvurdering
- Hunting/impact-vurdering som en del av `Ladeutvikling`, ikke en los side-modul
- Felles ballistikkmotor med lik oppførsel i `Drop Chart`, `Zero Shift`, `Modern Load Builder`, `Ladeutvikling`, `Ammo Test Lab` og rapporter
- Felles miljomodell med temperatur, trykk, høyde, luftfuktighet og `density altitude`
- Terrengrisiko i kartmodulen som kan flagge vann, myr, dal, rygg, åpent berg og stor høydeforskjell

## Strategisk differensiering
- Ikke bare bygge en solver eller en chrono-app, men en sammenhengende ladeutviklingsplattform.
- Prioritere lukket arbeidsflyt:
  `Vapenprofil -> Batch -> Chronograph -> Target -> Analyse -> Neste steg`.
- Bygge `digital twin` for pipe eller lop med H2O, temperaturrespons, historikk, harmonikk og kalibrert modell.
- Vise `confidence` og `uncertainty` eksplisitt i stedet for a late som alle tall er like sikre.
- Samle de viktigste signalene i et eget `evidenskvalitet`-lag, slik at brukeren ser helhetskvalitet og ikke bare mange enkeltbokser.
- Knytte jaktvurdering til kuleprofil, anslagshastighet og impact-vindu pa en faglig forsiktig mate.
- Lage tydelig skill e mellom `malt`, `modellert` og `anbefalt`, slik at produktet fremstar mer vitenskapelig og mer troverdig.
- Gjore systemet selvlærende per pipe eller lop, slik at anbefalingene blir mer personlige, mer presise og vanskeligere a erstatte med generiske verktøy.
- Utvide selvlæringen til komponentnivå med egne profiler for hylselotter, kruttlotter og kuleytelse i valgt pipe eller lop.
- Forste byggesteiner er startet: hylselotter har egne laeringsprofiler, og kruttlotter har na egen laeringsprofil med velocity offset, temp-spor og driftstatus i lot-trackeren.

## Testplan
Se [docs/mvp_test_plan.md](docs/mvp_test_plan.md) for MVP-regresjon og golden-data tester.
