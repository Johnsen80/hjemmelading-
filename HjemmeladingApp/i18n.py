from __future__ import annotations

import logging

from .utils.qt_compat import QSettings

log = logging.getLogger(__name__)

_LANG_MAP = {
    "no": {
        "Settings": "Innstillinger",
        "Theme": "Tema",
        "Units": "Enheter",
        "Metric": "Metrisk",
        "Imperial": "Imperial",
        "Save": "Lagre",
        "Cancel": "Avbryt",
        "Preview": "Forhandsvisning",
        "Background": "Bakgrunn",
        "Button Style": "Knappestil",
        "Color Adjustment": "Fargejustering",
        "Global System": "Globalt system",
        "Language": "Sprak",
        "English": "Engelsk",
        "Norwegian": "Norsk",
        "Choose Image": "Velg bilde...",
        "Clear": "Fjern",
        "Theme Light": "Lys",
        "Theme Dark": "Mørk",
        "Theme High Contrast": "Høy kontrast",
        "Button Style Filled": "Fylt",
        "Button Style Outlined": "Omriss",
        "Button Style Flat": "Flat",
        "Background Mode Fill": "Fyll",
        "Background Mode Fit": "Tilpass",
        "Background Mode Center": "Sentrer",
        "Background Mode Stretch": "Strekk",
        "I18n Status": "i18n-status",
        "Example": "Eksempel",
        "Settings Save Error": "Kunne ikke lagre innstillinger. Se debug-logg for detaljer.",
        "No Registered Missing Keys For": "Ingen registrerte manglende nøkler for",
        "Missing Keys For": "Manglende nøkler for",
        "And More": "til",
        "Could Not Read I18n Status": "Kunne ikke lese i18n-status.",
        "Profile Settings": "Brukerprofil og innstillinger",
        "Username": "Brukernavn:",
        "Choose Background Image": "Velg bakgrunnsbilde",
        "Background Image": "Bakgrunnsbilde",
        "Save Settings": "Lagre innstillinger",
        "Export Profile": "Eksporter profil",
        "Import Profile": "Importer profil",
        "Profile Editor Unavailable": "Profilredigering er midlertidig utilgjengelig.",
        "Close": "Lukk",
        "Images Filter": "Bilder (*.png *.jpg *.jpeg *.bmp)",
        "Images Filter Extended": "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)",
        "Customize Appearance": "Tilpass utseende",
        "Upload Image": "Last opp bilde",
        "Choose Background Color": "Velg bakgrunnsfarge",
        "Choose Color": "Velg farge",
        "Customizer Unavailable": "Customizer er midlertidig utilgjengelig.",
        "Saved": "Lagret",
        "Settings Saved": "Innstillinger lagret!",
        "Error": "Feil",
        "Could Not Save Settings": "Kunne ikke lagre innstillinger.",
        "Exported": "Eksportert",
        "Profile Exported": "Profil eksportert!",
        "Export Failed": "Eksport feilet!",
        "Imported": "Importert",
        "Profile Imported": "Profil importert!",
        "Import Failed": "Import feilet",
        "Profile Import Failed": "Import av profil feilet.",
        "See Details": "Se detaljer for mer informasjon.",
    },
    "en": {
        "Settings": "Settings",
        "Theme": "Theme",
        "Units": "Units",
        "Metric": "Metric",
        "Imperial": "Imperial",
        "Save": "Save",
        "Cancel": "Cancel",
        "Preview": "Preview",
        "Background": "Background",
        "Button Style": "Button Style",
        "Color Adjustment": "Color Adjustment",
        "Global System": "Global System",
        "Language": "Language",
        "English": "English",
        "Norwegian": "Norwegian",
        "Choose Image": "Choose image...",
        "Clear": "Clear",
        "Theme Light": "Light",
        "Theme Dark": "Dark",
        "Theme High Contrast": "High contrast",
        "Button Style Filled": "Filled",
        "Button Style Outlined": "Outlined",
        "Button Style Flat": "Flat",
        "Background Mode Fill": "Fill",
        "Background Mode Fit": "Fit",
        "Background Mode Center": "Center",
        "Background Mode Stretch": "Stretch",
        "I18n Status": "i18n status",
        "Example": "Example",
        "Settings Save Error": "Could not save settings. See debug log for details.",
        "No Registered Missing Keys For": "No registered missing keys for",
        "Missing Keys For": "Missing keys for",
        "And More": "more",
        "Could Not Read I18n Status": "Could not read i18n status.",
        "Profile Settings": "Profile Settings",
        "Username": "Username:",
        "Choose Background Image": "Choose Background Image",
        "Background Image": "Background Image",
        "Save Settings": "Save Settings",
        "Export Profile": "Export Profile",
        "Import Profile": "Import Profile",
        "Profile Editor Unavailable": "Profile editor is temporarily unavailable.",
        "Close": "Close",
        "Images Filter": "Images (*.png *.jpg *.jpeg *.bmp)",
        "Images Filter Extended": "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        "Customize Appearance": "Customize Appearance",
        "Upload Image": "Upload Image",
        "Choose Background Color": "Choose Background Color",
        "Choose Color": "Choose Color",
        "Customizer Unavailable": "Customizer is temporarily unavailable.",
        "Saved": "Saved",
        "Settings Saved": "Settings saved!",
        "Error": "Error",
        "Could Not Save Settings": "Could not save settings.",
        "Exported": "Exported",
        "Profile Exported": "Profile exported!",
        "Export Failed": "Export failed!",
        "Imported": "Imported",
        "Profile Imported": "Profile imported!",
        "Import Failed": "Import failed",
        "Profile Import Failed": "Profile import failed.",
        "See Details": "See details for more information.",
    },
}

_current_lang = "no"


def translate(text: str) -> str:
    return _LANG_MAP.get(_current_lang, {}).get(text, text)


def get_language() -> str:
    return _current_lang


def set_language(lang_code: str) -> None:
    global _current_lang

    normalized = lang_code if lang_code in _LANG_MAP else "en"
    _current_lang = normalized
    if QSettings is not None:
        try:
            qs = QSettings("ReloadingWorkshop", "ReloadingManager")
            qs.setValue("language", normalized)
        except Exception as exc:
            log.debug("Failed to persist language preference: %s", exc)


__all__ = ["get_language", "set_language", "translate"]
