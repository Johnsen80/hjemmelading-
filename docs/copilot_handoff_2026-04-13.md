# Copilot Handoff 2026-04-13

Denne filen er lagret for å kunne fortsette arbeidet uten å være avhengig av at selve chat-tråden åpner identisk.

## Nåværende status

- Lastmodulen kjøres etter en låst ferdigplan i `docs/load_module_finish_todo.md`.
- Todo-status akkurat nå:
  - `Lock canonical truth path`: ferdig
  - `Complete engine input context`: ferdig
  - `Finish evidence weighting core`: aktiv
  - resterende blokker står fortsatt etter denne

## Siste ferdigstilte arbeid

- Kanonisk workflow/runtime-truth-path ble sentralisert rundt `src/tools/load_session_runtime_service.py`.
- Smart engine input ble fullført i `src/modules/smart_ammo_engine.py` for:
  - active component context
  - active lot context
  - environment context
  - measured evidence context
- Smart-engine TODO ble oppdatert i `docs/local_smart_ammo_engine_todo.md` slik at disse Phase 1-punktene er markert som ferdige.

## Siste validering

- Kommando som sist ble kjørt grønt:

```powershell
C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/.tool-venv/Scripts/python.exe -m pytest tests/test_smart_ammo_engine.py
```

- Resultat: `8 passed`

## Aktiv neste blokk

Neste arbeid skal fortsette på `Finish evidence weighting core`.

Første konkrete sted å gå videre:

- `src/modules/smart_ammo_engine.py`
- `src/tools/load_session_runtime_service.py`
- `docs/local_smart_ammo_engine_todo.md`

Målet i neste blokk er å:

- gjenbruke eksisterende evidensmodell der det er mulig
- normalisere matched vs unmatched evidence scoring
- sørge for at motoren foretrekker `insufficient evidence` fremfor å tvinge en konklusjon
- legge til fokuserte tester for mixed signals

## Viktig miljøinfo

- Stabil test-Python for repoet er `.github/.tool-venv` med Python 3.11.
- Den lokale `.venv/.venv`-tolken finnes, men er ikke den verifiserte testveien for denne repoen.

## VS Code / Pylance

- Pylance-feilen `Client Pylance: connection to server is erroring. Channel closed` ble forsøkt dempet ved å legge lokale `.vscode/settings.json`-filer i tunge workspace-røtter som `node_modules`, `build`, `dist`, cache-mapper og `.venv`, slik at de ikke analyseres som kodeprosjekter.
- Hvis problemet kommer tilbake: kjør `Reload Window`, deretter `Pylance: Restart Language Server`.

## Arbeidsregel videre

- Fortsett autonomt på load-modulen.
- Ta så mye som mulig i hvert pass.
- Unngå sidespor utenfor plan og intensjon.