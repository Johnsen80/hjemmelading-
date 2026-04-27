# Qt-miljo – sjekkliste

## Status
- Visual C++ er installert
- Python 3.11.9 (virtuelt miljø) er aktivert
- PyQt6 og relaterte Qt-pakker er installert i `.github/.tool-venv`
- PySide6 er valgfritt og trengs ikke for standard verktøyflyt

## Neste steg
1. Test at PyQt6 og Qt fungerer:
   - Kjør et enkelt testscript for å verifisere import og GUI.
2. Sjekk at Visual C++ er tilgjengelig for kompilering (for utvidelser eller pyinstaller).
3. Hvis verktøymiljøet er skadet, bygg det opp igjen med `tools/rebuild_tool_venv.ps1`.
4. Oppdater dokumentasjon med krav og instruksjoner.

## Testscript
```python
from PyQt6.QtWidgets import QApplication, QLabel
app = QApplication([])
label = QLabel('PyQt6 virker!')
label.show()
app.exec()
```

Kjør dette med:
```
C:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/.tool-venv/Scripts/python.exe -c "from PyQt6.QtWidgets import QApplication, QLabel; app = QApplication([]); label = QLabel('PyQt6 virker!'); label.show(); app.exec()"
```

## Feilsøking
- Hvis du får "DLL load failed" eller lignende, sjekk at Visual C++ redistributable er installert.
- Sjekk at PATH inkluderer Qt-bibliotekene.

## Dokumentasjon
- Oppdater README.md med avsnitt om Visual C++ og Qt/PySide-krav.

---
Denne sjekklisten hjelper deg å verifisere at alt er klart for PySide/Qt-konvertering og videre utvikling.
