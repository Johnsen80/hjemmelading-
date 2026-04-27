# Internationalization Requirements (i18n)

## Scope
- Windows desktop UI (MVP) and generated reports.
- Offline-first operation with no dependency on cloud translation services.

## Language support (1.0)
- English (default and fallback).
- Norwegian (Bokmal).

## Functional requirements
- User can select UI language in Settings; preference is persisted per user.
- Language change is safe and communicated clearly (restart allowed if needed).
- All UI strings are externalized with stable keys; no hard-coded text in UI code.
- Pluralization and gender-neutral phrasing are supported where needed.
- Date, time, and number formatting are locale-aware.
- Data entry accepts locale decimal separators and normalizes on save.
- Data exports (CSV/JSON) use locale-invariant formats for reliability.
- Human-facing reports can be localized.

## Technical requirements
- Translation files are versioned in the repo and loaded locally.
- Missing keys fall back to English with a visible development warning.
- Validation checks detect missing/unused keys and invalid placeholders.
- UI labels avoid concatenation; use full sentences with placeholders.

## Module checklist (TODO)
- Settings: language selector UI, persistence, and restart messaging if required.
- App shell: main menu, navigation, tooltips, status bar, and empty states.
- Forms and validation: field labels, helper text, and error messages.
- Charts and tables: axes, legends, tooltips, and locale-aware numeric display.
- Reports: localized headings, summaries, and templates while keeping data fields stable.
- Import/export: CSV delimiter/decimal handling on import; locale-invariant formats on export.
- Dialogs and warnings: confirmations, safety notices, and error dialogs.

## Codebase touchpoints (current)
- HjemmeladingApp/main.py: language menu and fallback window labels.
- HjemmeladingApp/ui/settings_dialog.py: settings UI labels and option text.
- HjemmeladingApp/i18n.py: language preference setter (QSettings).
- src/i18n.py: compatibility shim for set_language.
- src/utils/i18n.py: translation dictionary (Norwegian/English) to wire into UI.
- src/ui/main_window.py: app shell labels, nav buttons, tooltips, status text.
- src/database/import_csv.py: CSV import validation and error messages.
- src/database/import_grtload.py: GRT XML import validation text.
- src/utils/chronograph_import.py: chronograph CSV parsing and error strings.
- src/modules/chronograph_importer.py: chronograph import UI labels.
- src/modules/grt_importer.py: GRT import UI labels and errors.

## UI and layout constraints
- Allow text expansion of at least 30% without clipping.
- Avoid fixed-width labels; prefer flexible layouts and wrapping.
- Fonts must include the characters needed for supported languages.

## Acceptance checks
- Switching language changes all visible UI labels.
- Locale formatting is consistent across charts, tables, and reports.
- No missing-key placeholders in production builds.
- Exported data can be re-imported without locale ambiguity.
