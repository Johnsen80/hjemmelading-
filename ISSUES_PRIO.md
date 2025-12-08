**Project Backlog & Priorities**

Kortfattet prioritering og første steg for å rydde opp i statiske feil, tester og runtime-problemer.

**Status (kort)**
- `mypy`: Success: no issues found in 90 source files. Flere "note:"-linjer indikerer funksjoner uten type-sjekk (`annotation-unchecked`).
- `ruff`: All checks passed.
- `pytest`: Ingen feilede headless-tester i dagens run.
- Branch `refactor/long-lines` er ikke pushet til remote pga. fjernkontroll / credentials / SSH-host-key.

**Høy-nivå anbefaling**
1. Løse blokkere: få branchen opp på remote (push) eller levere bundle for PR. Uten dette blir review/CI vanskelig.
2. Stabiliser CI for headless: kjør testene i CI (Xvfb) slik at GUI-avhengigheter ikke blokkerer.
3. Automatiser feilsamling: kjør mypy/ruff/pytest regelmessig og eksporter rapporter (allerede gjort — `mypy_report.txt`, `ruff_report.txt`, `pytest_report.txt`).
4. Triager og prioriter feil basert på impact: Blockers -> Runtime bugs -> High-impact typing issues -> Lint/style.
5. Del opp arbeidet i små PRer (<200 changed lines) med ett fokusområde per PR.

**Blockers (må løses først)**
- Push/PR: fiks repo-tilgang (SSH host-key eller HTTPS med PAT) eller bruk bundle `refactor-long-lines.bundle` som ble opprettet.
- Reproducerbare GUI-krasjer: kjør GUI-tester i Xvfb CI eller container for trygg debugging.

**High-impact filer funnet i dagens skanning**
(disse bør prioriteres for gjennomgang — finn detaljer i `mypy_report.txt`)
- `HjemmeladingApp/settings.py`  — mange `annotation-unchecked` noter (mypy body-check off for many functions).
- `src/modules/workflow_hub.py`  — `annotation-unchecked` noter; potensielt komplekse runtime flows.
- `src/modules/bullet_qc_wizard.py` — `annotation-unchecked` noter i store funksjoner.
- `src/modules/chronograph_importer.py` — `annotation-unchecked` noter.
- `src/modules/live_visualization.py` — nylig fikset en mypy-feil; fortsatt bør gjennomgås for headless stubs.
- `src/ui/main_window.py` — nylig refaktorert for TYPE_CHECKING; verifiser GUI-runtime oppførsel.

Hvis du ønsker at jeg lager konkrete issues i repoen, kan jeg automatisk lage en issue per fil/feil med forslag til PR-innhold.

**Forslag til 10 første PR‑oppgaver (fokusert, kjapp gevinst)**
1. Push + CI: få `refactor/long-lines` publisert og aktiver CI (Xvfb for GUI jobber).
2. Fix/verify `src/ui/main_window.py` runtime i en kontrollert miljø (headless og GUI), små endringer.
3. Gjennomgå `HjemmeladingApp/settings.py` og legg til typing i de viktigste funksjonene eller bruk `# type: ignore` lokalt.
4. Auditer `src/modules/live_visualization.py` og `temperature_ladder_test.py` for fallback-stubber, legg til klare `Any`-annotasjoner der passende.
5. Add CI job som kjører `mypy` og `ruff` med rapport-utdata (artifact) for hver PR.
6. Create a lightweight functional test harness for a core workflow (e.g. import/parse a demo JSON) to catch runtime regressions.
7. Tidy packaging spec files (installer/spec) — separate PR.
8. Address top 5 `annotation-unchecked` files by adding signatures or `# type: ignore[annotation-unchecked]` in narrow scopes.
9. Add a CONTRIBUTING.md explaining how to run tests locally and how to use the bundle if push fails.
10. Add flakiness detection for GUI tests (retry once) and mark tests requiring a display.

**Quick commands for reviewers / maintainers**
- Open the stat reports:
  - `type mypy_report.txt`
  - `type ruff_report.txt`
  - `type pytest_report.txt`
- If you want to apply the offline bundle on another machine:
```powershell
git bundle verify C:\Users\bjjoh\OneDrive\Dokumenter\Programering\refactor-long-lines.bundle
git fetch C:\Users\bjjoh\OneDrive\Dokumenter\Programering\refactor-long-lines.bundle refactor/long-lines:refs/heads/refactor/long-lines
git checkout refactor/long-lines
git push origin refactor/long-lines
```

**Estimater**
- Quick triage + backlog (create issues + 1 PR): ~1–2 timer.
- Clear blockers + CI green: ~1–2 dager.
- Clean up all typing/lint warnings repo-wide: flere dager til uker.

---
Hvis du vil at jeg skal: 
- generere konkrete GitHub-issues/PR-templates fra rapportene — svar `issues`.
- lage `ISSUES_PRIO_TOP50.md` med en fil-for-fil liste (top 50) — svar `top50`.
- forsøke å pushe branchen igjen (jeg trenger at du godkjenner SSH-host-key eller oppgir en PAT) — svar `push`.

Jeg kan starte med å generere en `top50`-liste nå hvis du ønsker det.
