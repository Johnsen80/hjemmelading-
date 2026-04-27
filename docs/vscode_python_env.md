# VS Code Python-miljo

For a unnga import-feil for Qt-bibliotekene i prosjektet:

1. Apne kommandopalletten (`Ctrl+Shift+P`)
2. Sok etter `Python: Select Interpreter`
3. Velg:
   `C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/.tool-venv/Scripts/python.exe`

Dette sikrer at VS Code bruker riktig miljo for linting, kjoring og testing.

Merk:

- Miljoet skal bygges med Python 3.11.
- Miljoet inneholder Qt-avhengighetene som trengs for import-oppslag i VS Code.
- `main.py` starter applikasjonen med `PyQt6`.
- `.github/.tool-venv` behandles som et repo-styrt verktøymiljo, ikke et tilfeldig lokalt side-miljo.

Hvis miljoet virker skadet eller importene begynner a drive, bygg det opp igjen med:

```powershell
powershell -ExecutionPolicy Bypass -File tools/rebuild_tool_venv.ps1
```

Hvis du fortsatt far import-feil, kjør:

```powershell
C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/.tool-venv/Scripts/python.exe main.py
```

Hvis denne kommandoen starter appen uten import-feil, er Python-interpreteren riktig satt opp.

---
Se `docs/pyside_qt_checklist.md` for flere feilsokingstips.
