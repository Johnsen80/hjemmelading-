# 🌐 Flerspråk-støtte / Language Support

## Oversikt / Overview

Reloading Workshop Manager støtter både norsk og engelsk brukergrensesnitt.
The Reloading Workshop Manager supports both Norwegian and English user interfaces.

## Bytte språk / Change Language

### I programmet / In the application:
1. Åpne **Innstillinger** / Open **Settings** tab
2. Finn **🌐 Språk / Language** øverst i enheter-seksjonen / Find at top of units section
3. Velg **Norsk** eller **English**
4. Klikk **💾 Lagre innstillinger** / Click **💾 Save Settings**
5. **Start programmet på nytt** / **Restart the program**

### Første gang / First time:
- Standardspråket er **Norsk** / Default language is **Norwegian**
- Innstillingen lagres automatisk / Setting is saved automatically
- Huskes mellom kjøringer / Remembered between sessions

## Hva oversettes / What is translated

### ✅ Oversatt / Translated:
- Alle meny-titler / All menu titles
- Tab-navn / Tab names
- Knapper (Ny, Lagre, Slett, etc.) / Buttons (New, Save, Delete, etc.)
- Dashboard-tekster / Dashboard texts
- Dialoger og meldinger / Dialogs and messages
- Felt-etiketter / Field labels
- Status-meldinger / Status messages

### 🚧 Ennå ikke oversatt / Not yet translated:
- Noen dialogbokser / Some dialog boxes
- Enkelte hjelpetekster / Some help texts
- Tips-tekster i Dashboard / Tips in Dashboard
- Feilmeldinger fra database / Database error messages

## For utviklere / For Developers

### Oversettelsessystem / Translation System

Programmet bruker et enkelt dictionary-basert oversettelsessystem:
The program uses a simple dictionary-based translation system:

```python
from src.utils.i18n import tr, set_language

# Bruk tr() for oversettelser / Use tr() for translations
label = QLabel(tr('dashboard_title'))

# Bytt språk / Change language
set_language('en')  # eller / or 'no'
```

### Legge til nye oversettelser / Adding New Translations

1. Åpne `src/utils/i18n.py`
2. Legg til nøkkel i både `_norwegian()` og `_english()` / Add key to both functions
3. Bruk `tr('din_nokkel')` i koden / Use `tr('your_key')` in code

Eksempel / Example:
```python
def _norwegian(self):
    return {
        'my_new_text': 'Min nye tekst',
        ...
    }

def _english(self):
    return {
        'my_new_text': 'My new text',
        ...
    }
```

### Formatering / Formatting

For dynamisk tekst / For dynamic text:
```python
# Med variabler / With variables
tr('msg_items_count', count=5)  # "5 items" / "5 elementer"

# I oversettelser / In translations
'msg_items_count': '{count} elementer'  # NO
'msg_items_count': '{count} items'      # EN
```

## Planlagte forbedringer / Planned Improvements

- [ ] Fullstendig oversettelse av alle moduler / Complete translation of all modules
- [ ] Flere språk (svensk, dansk, tysk) / More languages (Swedish, Danish, German)
- [ ] Automatisk språkdeteksjon fra OS / Auto-detect language from OS
- [ ] Eksport/import av oversettelser / Export/import of translations
- [ ] Crowdsourcing av oversettelser / Crowdsourced translations

## Teknisk implementasjon / Technical Implementation

### Arkitektur / Architecture:
```
src/utils/i18n.py          # Oversettelsessystem / Translation system
  ↓
src/ui/main_window.py      # Laster språk ved oppstart / Loads language at startup
  ↓
src/modules/*.py           # Bruker tr() funksjon / Uses tr() function
  ↓
QSettings                  # Lagrer valg / Saves choice
```

### Språk-koder / Language Codes:
- `no` = Norsk / Norwegian
- `en` = English

### Lagring / Storage:
Språkvalget lagres i QSettings under nøkkelen `"language"`.
Language choice is stored in QSettings under the key `"language"`.

## Kjente problemer / Known Issues

1. **Ikke alle moduler er oversatt ennå** / **Not all modules are translated yet**
   - Løsning: Jobber med fullstendig oversettelse
   - Solution: Working on complete translation

2. **Krever restart av program** / **Requires program restart**
   - Grunn: GUI-komponenter lages ved oppstart
   - Reason: GUI components are created at startup
   - Fremtidig: Dynamisk oppdatering uten restart
   - Future: Dynamic update without restart

3. **Tips i Dashboard kun på norsk** / **Dashboard tips only in Norwegian**
   - Jobbes med / Working on it

## Bidrag / Contributing

Ønsker du å bidra med oversettelser?
Want to contribute translations?

1. Fork repositoriet / Fork the repository
2. Legg til oversettelser i `src/utils/i18n.py`
3. Test grundig / Test thoroughly
4. Send pull request

## Kontakt / Contact

Har du spørsmål om oversettelser?
Questions about translations?

- Opprett et issue på GitHub
- Create an issue on GitHub
