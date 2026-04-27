# Gordon Extract Side Tool

Dette er et midlertidig sideverktøy for å hente ut data fra Gordon Reloading Tool uten å bygge Gordon-spesifikk logikk inn i hovedappen.

Mål:
- hente ut mest mulig av Gordon sine `kuler`, `krutt` og `kaliber`
- prioritere åpne og dokumenterte spor før DB-forensics
- eksportere til vårt eget format, slik at Hjemmelading eier dataene videre

## Strategi

Verktøyet jobber i denne rekkefølgen:
1. lesbare Gordon-filer og eksportmapper
2. plugin/API-spor
3. UI-automatisering
4. DB-forensics som siste utvei

## Innhold

- `analyze_extraction_options.py`
  Lager en konkret analyse- og anbefalingsrapport basert på lokal Gordon-installasjon og våre eksisterende rapporter.
- `build_plugin_probe.py`
  Genererer en liten Gordon-plugin-probe som kan kopieres inn i Gordon sin `plugins`-mappe for å teste IPC/plugin-sporet.
- `build_plugin_probe_attempt_report.py`
  Oppsummerer hva som faktisk skjedde i plugin-forsøket.
- `build_ui_export_scaffold.py`
  Lager et PowerShell-basert fallback-skjelett for UI-/eksportsporet.

## Typisk bruk

Analyse:

```powershell
& ".github\.tool-venv\Scripts\python.exe" `
  ".github\tools\gordon_extract\analyze_extraction_options.py"
```

Bygg plugin-probe:

```powershell
& ".github\.tool-venv\Scripts\python.exe" `
  ".github\tools\gordon_extract\build_plugin_probe.py"
```

Plugin-proben blir skrevet til:

- `.github\tmp\gordon_plugin_probe\`

Den kan senere kopieres til Gordon sin plugin-mappe når vi er klare til å teste IPC-sporet.
