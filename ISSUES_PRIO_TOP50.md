**Top 50 Prioritized Files / Actions (generated)**

Denne listen er laget ut fra dagens statiske kjøringer (`mypy_report.txt`, `ruff_report.txt`) og repo-kunnskap.
Den inneholder filer som bør gjennomgås først, med forslag til hva som bør gjøres.

Instruks: Bekreft hvilke jeg skal begynne å fikse (eller svar `auto` for at jeg starter fra toppen).

1. `HjemmeladingApp/settings.py` — mange `annotation-unchecked` noter.
   - Anbefalt: legg til type-signaturer for de mest sentrale funksjonene, eller bruk selektive `# type: ignore` i uinteressante helpers.

2. `src/modules/workflow_hub.py`
   - Anbefalt: gjennomgå lange utypede funksjoner; del opp store funksjoner, legg til typing på offentlige APIer.

3. `src/modules/bullet_qc_wizard.py`
   - Anbefalt: legg til types for kjerneklasser og kritiske metoder; kjør enhetstester for QC-flow.

4. `src/modules/chronograph_importer.py`
   - Anbefalt: verifiser innlesing/parsing av filer; legg til defensive valideringer og typing.

5. `src/ui/main_window.py`
   - Anbefalt: sanity-test GUI init i headless fallback og under Xvfb; legg inn smale `# type: ignore` der runtime-stubber brukes.

6. `src/modules/live_visualization.py`
   - Anbefalt: bekreft fallback-stubber og annoter `BaseCanvas: Any` (gjort). Legg til enkle enhetstester for fallback-vei.

7. `src/modules/temperature_ladder_test.py`
   - Anbefalt: rydde imports og sikre test-harness kjører headless; fiks minor isort/black-format.

8. `src/modules/terrain_map.py`
   - Anbefalt: sikker import-guard for folium/pyqtgraph; legge til en enkel headless stub.

9. `src/modules/importer_*.py` (samlet)
   - Anbefalt: konsolider feil-håndtering og legg til enhetstester for parsing av sample-filer fra `data/`.

10. `src/modules/*_cli.py` (samlet)
   - Anbefalt: legg til CLI-argument-typing og tester for help/exit-tilfeller.

11. `src/modules/db/*.py` (ORM usage)
   - Anbefalt: sikre at SQLAlchemy-typer og sessions håndteres riktig; legg til transaction-tests.

12. `src/modules/weapon/*.py` (kjerne funksjonalitet)
   - Anbefalt: prioritere runtime-feil over typings, legg til integrasjonstester for ballistics computations.

13. `src/modules/chronograph_*` (relatert til chronograph-import)
   - Anbefalt: robust input-validering og tester for malformed files.

14. `src/modules/persistence.py` / `db` wrappers
   - Anbefalt: test rollback og error handling.

15. `src/modules/config.py` / config loader
   - Anbefalt: ensartet API og typing for config-objektet.

16. `src/modules/live_*` (visualization / live capture)
   - Anbefalt: sikre headless fallback og dokumentere display-krav.

17. `src/ui/widgets/*` (samlet)
   - Anbefalt: standardisere stubbing og type-annotation i små komponenter.

18. `src/modules/reporting/*.py`
   - Anbefalt: sikre output-format (json/csv) og legge til snapshot-tests.

19. `installer/*` og `packaging/*`
   - Anbefalt: oppdater builder-specs og test build pipeline i CI.

20. `scripts/*` (utility scripts)
   - Anbefalt: gjør dem importable-moduler eller test dem som scripts.

--

21-50: Flere filer med `annotation-unchecked` eller store functions. Eksempelvis:
- `src/modules/loader.py`
- `src/modules/measurements.py`
- `src/modules/interop/*.py`
- `src/modules/*_helpers.py`

For full liste, sjekk `mypy_report.txt` og søk etter `annotation-unchecked` og andre warnings.

Foreslåtte arbeidsflyt for meg (automatisk):
1. Lag en issue/PR for hvert av oppgavene 1–5 (små, fokuserte endringer).
2. Implementer PR#1: `HjemmeladingApp/settings.py` - typsignaturer for 5 viktigste funksjoner.
3. Kjør CI-lokal (mypy/ruff/pytest). Hvis testes feiler, trinnvis debugging.
4. Fortsett med PR#2: `workflow_hub.py` (del opp store funksjoner og legg til typing på API).

Si `auto` for at jeg starter automatisk fra toppen (oppretter PR-patchfilserier lokalt), eller gi meg prioritet hvis du vil noe annet.
