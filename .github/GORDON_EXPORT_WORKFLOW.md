# Gordon Export Workflow

Dette er den praktiske veien videre når vi vil kopiere Gordon-data over i vårt eget system uten å være avhengig av Gordon etterpå.

## Status

- Den interne `GordonsReloadingTool.db` ser ut til å være en kryptert SQL-/SQLite-variant.
- Vi har ikke nøkkelen ennå.
- Derfor er den tryggeste veien nå å bruke Gordon sine XML-eksporter og lese dem inn i vårt eget system.

## Verktøy vi har klare

- Forensics-rapport:
  - `.github/data/component_knowledge_base/gordon_installation_forensics_report.md`
- XML/GRT extractor:
  - `.github/tools/extract_gordon_data.py`
- Samle inn brukerfiler fra `%APPDATA%`:
  - `.github/tools/collect_gordon_user_files.py`
- Kombinert intake for installasjon + AppData:
  - `.github/tools/collect_and_ingest_gordon_sources.py`
- Snapshot-import til vår egen DB:
  - `src/tools/gordon_reference_snapshot_service.py`
- End-to-end intake-script:
  - `.github/tools/ingest_gordon_export_folder.py`

## Hva Gordon tydelig støtter

- Projectile Database:
  - eksport av valgt kule til XML i GRT-format
- Propellant Database:
  - eksport av valgt krutt til XML i GRT-format
- Caliber Database:
  - eksport av valgt kaliber til XML i GRT-format
- User files:
  - egne endringer lagres som vanlig XML i `%APPDATA%\GordonsReloadingTool\`
- Native filendelser:
  - `*.projectile`
  - `*.propellant`
  - `*.caliber`

## Åpne formater vi nå støtter direkte

- `projectilefile`
- `propellantfile`
- `caliberfile`
- flere poster i samme XML-fil
- native Gordon-filendelser over

Dette er dokumentert i Gordon sin egen `doku/en/doku/file_projectile.txt`, `file_propellant.txt` og `file_caliber.txt`.

## Anbefalt arbeidsflyt

1. Eksporter kuler fra Gordon til en egen mappe.
2. Eksporter krutt fra Gordon til en egen mappe.
3. Kopier eventuelle bruker-XML-filer fra `%APPDATA%\GordonsReloadingTool\`.
4. Kjør intake-scriptet mot denne mappa.

## Raskeste samlekommando

Hvis du vil ta med både installasjonsmappe og brukerfiler i ett løp:

```powershell
& "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\python.exe" `
  "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\tools\collect_and_ingest_gordon_sources.py" `
  --install-root "C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY" `
  --appdata-root "C:\Users\bjjoh\AppData\Roaming\GordonsReloadingTool" `
  --output-root "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\tmp\gordon_known_sources_ingest" `
  --component-db "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\test_tmp\gordon_known_sources_components.json" `
  --snapshot-db "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\test_tmp\gordon_known_sources_snapshots.db"
```

## Kommando

```powershell
& "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\.tool-venv\Scripts\python.exe" `
  "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\tools\ingest_gordon_export_folder.py" `
  --source-root "C:\sti\til\gordon-eksporter" `
  --output-root "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\tmp\gordon_full_ingest" `
  --component-db "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\test_tmp\gordon_ingest_components.json" `
  --snapshot-db "c:\Users\bjjoh\OneDrive\Dokumenter\Programering\Hjemmelading\.github\test_tmp\gordon_ingest_snapshots.db"
```

## Output

Scriptet skriver blant annet:

- `gordon_extracted_projectiles_raw.csv`
- `gordon_extracted_propellants_raw.csv`
- `gordon_extracted_calibers_raw.csv`
- `gordon_projectile_reference.csv`
- `gordon_propellant_reference.csv`
- `gordon_caliber_reference_full.csv`
- `gordon_bullets_for_hjemmelading.csv`
- `gordon_powders_for_hjemmelading.csv`
- `gordon_calibers_reference.csv`
- `gordon_ingest_summary.json`

## Hva de nye referansefilene gir oss

- `gordon_projectile_reference.csv`
  - rik kuleprofil med produsent, navn, lot, diameter, lengde, masse, G1/G7, UBCS og halegeometri
- `gordon_propellant_reference.csv`
  - rik kruttprofil med Gordon-modellfelt som `Br`, `Bp`, `Brp`, `Ba`, `Qex`, `k`, `eta`, `a0`, `a1`, `z1`, `z2`, `pc`, `pcd`, `pt`, `tcc`, `tch`
- `gordon_caliber_reference_full.csv`
  - rik kaliberprofil med standard, CIP-felt, dimensjoner, trykk og datasheet-lenke når den finnes

Dette er ment som vårt eget interne referanselag, mens `...for_hjemmelading.csv` er den tynnere app-tilpassede varianten.

## Viktig om duplikater

- Når vi kjører kombinert installasjon + AppData-ingest, bruker vi nå den kopierte `user_files`-mappa som kilde og unngår å lese original AppData dobbelt i samme løp.
- Det gjør snapshot- og referansefilene renere.

## Viktig om kaliber / SAAMI

- Denne Gordon-builden viser sterke CIP-spor i schema og binærtekst.
- Vi har foreløpig ikke funnet tilsvarende klare SAAMI-spor i Gordon.
- Derfor bør SAAMI behandles som eget offisielt ingest-spor i vårt system.

## Neste steg

- Fortsette nøkkel-/DB-forensics for å se om full intern DB kan åpnes direkte.
- Bygge eget SAAMI/CIP-lag fra offisielle kilder parallelt.
- Koble Gordon-export intake videre inn i app-UI når eksportvolumet blir større.
