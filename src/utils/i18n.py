"""
Internationalization (i18n) system
Handles translations between Norwegian and English
"""

# ruff: noqa: F811  # Temporary: duplicate `tr` definitions exist; needs manual consolidation


class Translations:
    """Translation management"""

    def __init__(self):
        self.current_language = "no"  # Default Norwegian
        self.translations = {"no": self._norwegian(), "en": self._english()}

    def set_language(self, lang_code):
        """Set current language"""
        if lang_code in self.translations:
            self.current_language = lang_code

    def get(self, key, **kwargs):
        """Get translated text"""
        text = self.translations[self.current_language].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def _norwegian(self):
        """Norwegian translations"""
        return {
            # Menu
            "menu_file": "&Fil",
            "menu_new": "&Ny",
            "menu_open": "&Åpne",
            "menu_save": "&Lagre",
            "menu_export": "&Eksporter",
            "menu_exit": "&Avslutt",
            "menu_tools": "&Verktøy",
            "menu_help": "&Hjelp",
            "menu_about": "&Om programmet",
            "menu_user_guide": "&Brukerveiledning",
            "menu_language": "&Språk",
            # Tabs
            "tab_dashboard": "📊 Dashboard",
            "tab_test_lab": "🧪 Test Lab",
            "tab_ammunition": "🎯 Ammunisjon",
            "tab_rifles": "🔫 Rifles & Optikk",
            "tab_inventory": "📦 Lager",
            "tab_log": "📝 Logg",
            "tab_analysis": "📈 Analyse",
            "tab_settings": "⚙️ Innstillinger",
            # Common buttons
            "btn_new": "➕ Ny",
            "btn_add": "➕ Legg til",
            "btn_edit": "✏️ Rediger",
            "btn_delete": "🗑️ Slett",
            "btn_save": "💾 Lagre",
            "btn_cancel": "❌ Avbryt",
            "btn_close": "Lukk",
            "btn_ok": "OK",
            "btn_yes": "Ja",
            "btn_no": "Nei",
            "btn_browse": "📁 Bla...",
            "btn_import": "📥 Importer",
            "btn_export": "📤 Eksporter",
            "btn_analyze": "📊 Analyser",
            "btn_copy": "📋 Kopier",
            # Dashboard
            "dashboard_title": "📊 Dashboard",
            "dashboard_welcome": "Velkommen til Reloading Workshop Manager!",
            "dashboard_rifles": "Rifles",
            "dashboard_ammo_profiles": "Ammunisjonsprofiler",
            "dashboard_ladder_tests": "Ladder Tests",
            "dashboard_loading_sessions": "Ladeøkter",
            "dashboard_inventory_status": "📦 Lagerstatus",
            "dashboard_recent_activity": "🕐 Nylige aktiviteter (siste 7 dager)",
            "dashboard_quick_tips": "💡 Nyttige tips",
            "dashboard_all_ok": "✅ Alt ser bra ut! Alle komponenter har god beholdning.",
            "dashboard_no_activity": "Ingen aktivitet siste 7 dager",
            # Rifles & Optics
            "rifles_title": "🔫 Rifles & Optikk Manager",
            "rifles_subtitle": "Administrer dine rifles og optikk",
            "rifles_tab": "Rifles",
            "optics_tab": "Optikk",
            "rifles_name": "Navn",
            "rifles_caliber": "Kaliber",
            "rifles_barrel_length": "Løpslengde",
            "rifles_twist_rate": "Twist Rate",
            "rifles_action_type": "Aksjon",
            "rifles_manufacturer": "Produsent",
            "rifles_notes": "Notater",
            "optics_click_value": "Klikk-verdi",
            "optics_click_unit": "Enhet",
            "optics_zero_distance": "Zero-avstand",
            # Inventory
            "inventory_title": "📦 Lager",
            "inventory_powder": "💥 Krutt",
            "inventory_bullets": "🎯 Kuler",
            "inventory_primers": "💨 Tennhetter",
            "inventory_cases": "🔩 Hylser",
            "inventory_quantity": "Beholdning",
            "inventory_status": "Status",
            "inventory_cost": "Kostnad",
            "inventory_very_low": "⚠️ Svært lavt",
            "inventory_low": "⚠️ Lavt",
            "inventory_ok": "✓ OK",
            "inventory_good": "✓ God",
            # Ammunition Profiles
            "ammo_title": "🎯 Ammunisjonsprofiler",
            "ammo_new_profile": "➕ Ny Ammunisjonsprofil",
            "ammo_name": "Navn",
            "ammo_rifle": "Rifle",
            "ammo_caliber": "Kaliber",
            "ammo_bullet": "Kule",
            "ammo_powder": "Krutt",
            "ammo_primer": "Tennhette",
            "ammo_case": "Hylse",
            "ammo_velocity": "Hastighet",
            "ammo_basic_info": "Grunnleggende",
            "ammo_components": "Komponenter",
            "ammo_ballistics": "Ballistikk",
            # Ladder Test
            "ladder_title": "🧪 Ladder Test Lab",
            "ladder_subtitle": "Planlegg og analyser systematiske ladder tests",
            "ladder_new_test": "➕ Ny Ladder Test",
            "ladder_view": "📊 Vis/Analyser",
            "ladder_test_name": "Testnavn",
            "ladder_date": "Dato",
            "ladder_distance": "Avstand",
            "ladder_charge_range": "Ladning",
            "ladder_results": "Resultater",
            "ladder_test_info": "Test-informasjon",
            "ladder_components": "Komponenter",
            "ladder_parameters": "Ladder Test Parametere",
            "ladder_start_charge": "Start ladning",
            "ladder_end_charge": "Slutt ladning",
            "ladder_step_size": "Steg størrelse",
            "ladder_steps": "steg",
            # Harmonic Wizard
            "harmonic_title": "🎯 Harmonic Wizard - Settedybde Assistent",
            "harmonic_new_test": "🆕 Ny Settedybde-test",
            "harmonic_disclaimer": '<b style="color: #d9534f;">⚠️ VIKTIG:</b> Dette verktøyet analyserer <i>dine faktiske testresultater</i> og foreslår settedybder som har høy sannsynlighet for god presisjon. Det beregner IKKE teoretisk harmonikk - det lærer av dine skudd.<br><b>Du har alltid ansvar for sikker lading innenfor ladebokens grenser.</b>',
            "harmonic_how_it_works": "Hvordan det fungerer:",
            "harmonic_barrel_profile": "Steg 1: Løpsprofil og konfigurasjon",
            "harmonic_components": "Steg 2: Ammunisjonskomponenter",
            "harmonic_test_setup": "Steg 3: Definer testområde",
            "harmonic_summary": "Steg 4: Oppsummering",
            # Session Logger
            "logger_title": "📝 Loggbok",
            "logger_loading_sessions": "🔧 Ladeøkter",
            "logger_shooting_sessions": "🎯 Skyteøkter",
            "logger_new_loading": "➕ Ny Ladeøkt",
            "logger_new_shooting": "➕ Ny Skyteøkt",
            "logger_quantity": "Antall",
            "logger_time": "Tid",
            "logger_rounds_fired": "Skudd avfyrt",
            "logger_weather": "Vær",
            # GRT Integration
            "grt_title": "🔗 Gordon Reloading Tool Integrasjon",
            "grt_import": "📥 Importer fra GRT",
            "grt_export": "📤 Eksporter til GRT",
            "grt_analyze": "📊 Analyser vs Faktiske Data",
            "grt_predicted_velocity": "GRT Hastighet",
            "grt_actual_velocity": "Faktisk Hastighet",
            "grt_difference": "Differanse",
            "grt_max_pressure": "Max Trykk (PSI)",
            "grt_case_fill": "Fylling %",
            "grt_status": "Status",
            "grt_imported": "Importert",
            # Settings
            "settings_title": "⚙️ Innstillinger",
            "settings_units": "📏 Enheter",
            "settings_defaults": "🎯 Standardverdier",
            "settings_safety": "⚠️ Sikkerhetsinnstillinger",
            "settings_database": "💾 Database og Backup",
            "settings_language": "🌐 Språk",
            "settings_save": "💾 Lagre innstillinger",
            "settings_reset": "🔄 Tilbakestill til standard",
            "settings_backup": "📦 Lag backup",
            "settings_restore": "♻️ Gjenopprett backup",
            # Zero Shift Calculator
            "zero_shift_title": "🎯 Zero Shift Calculator",
            "zero_shift_subtitle": "Beregn optikk-justeringer ved ammunisjonsbytte",
            "zero_shift_ammo1": "Ammunisjon 1 (Din zero)",
            "zero_shift_ammo2": "Ammunisjon 2 (Ny ladning)",
            "zero_shift_optic": "Optikk",
            "zero_shift_calculate": "🎯 Beregn justering",
            "zero_shift_result": "Resultat",
            "zero_shift_adjustment": "Justering",
            # Messages
            "msg_confirm_delete": "Bekreft sletting",
            "msg_are_you_sure": "Er du sikker?",
            "msg_success": "Suksess",
            "msg_error": "Feil",
            "msg_warning": "Advarsel",
            "msg_info": "Informasjon",
            "msg_saved": "Lagret!",
            "msg_deleted": "Slettet!",
            "msg_no_selection": "Ingen valgt",
            "msg_select_first": "Velg en rad først!",
            "msg_confirm_exit": "Bekreft avslutning",
            "msg_exit_question": "Er du sikker på at du vil avslutte?",
            # Units
            "unit_mm": "mm",
            "unit_cm": "cm",
            "unit_m": "m",
            "unit_fps": "fps",
            "unit_gr": "gr",
            "unit_psi": "PSI",
            "unit_celsius": "°C",
            "unit_percent": "%",
            "unit_pieces": "stk",
            "unit_grams": "g",
            "unit_minutes": "min",
        }

    def _english(self):
        """English translations"""
        return {
            # Menu
            "menu_file": "&File",
            "menu_new": "&New",
            "menu_open": "&Open",
            "menu_save": "&Save",
            "menu_export": "&Export",
            "menu_exit": "&Exit",
            "menu_tools": "&Tools",
            "menu_help": "&Help",
            "menu_about": "&About",
            "menu_user_guide": "&User Guide",
            "menu_language": "&Language",
            # Tabs
            "tab_dashboard": "📊 Dashboard",
            "tab_test_lab": "🧪 Test Lab",
            "tab_ammunition": "🎯 Ammunition",
            "tab_rifles": "🔫 Rifles & Optics",
            "tab_inventory": "📦 Inventory",
            "tab_log": "📝 Log",
            "tab_analysis": "📈 Analysis",
            "tab_settings": "⚙️ Settings",
            # Common buttons
            "btn_new": "➕ New",
            "btn_add": "➕ Add",
            "btn_edit": "✏️ Edit",
            "btn_delete": "🗑️ Delete",
            "btn_save": "💾 Save",
            "btn_cancel": "❌ Cancel",
            "btn_close": "Close",
            "btn_ok": "OK",
            "btn_yes": "Yes",
            "btn_no": "No",
            "btn_browse": "📁 Browse...",
            "btn_import": "📥 Import",
            "btn_export": "📤 Export",
            "btn_analyze": "📊 Analyze",
            "btn_copy": "📋 Copy",
            # Dashboard
            "dashboard_title": "📊 Dashboard",
            "dashboard_welcome": "Welcome to Reloading Workshop Manager!",
            "dashboard_rifles": "Rifles",
            "dashboard_ammo_profiles": "Ammunition Profiles",
            "dashboard_ladder_tests": "Ladder Tests",
            "dashboard_loading_sessions": "Loading Sessions",
            "dashboard_inventory_status": "📦 Inventory Status",
            "dashboard_recent_activity": "🕐 Recent Activity (last 7 days)",
            "dashboard_quick_tips": "💡 Quick Tips",
            "dashboard_all_ok": "✅ All good! All components have sufficient stock.",
            "dashboard_no_activity": "No activity in the last 7 days",
            # Rifles & Optics
            "rifles_title": "🔫 Rifles & Optics Manager",
            "rifles_subtitle": "Manage your rifles and optics",
            "rifles_tab": "Rifles",
            "optics_tab": "Optics",
            "rifles_name": "Name",
            "rifles_caliber": "Caliber",
            "rifles_barrel_length": "Barrel Length",
            "rifles_twist_rate": "Twist Rate",
            "rifles_action_type": "Action",
            "rifles_manufacturer": "Manufacturer",
            "rifles_notes": "Notes",
            "optics_click_value": "Click Value",
            "optics_click_unit": "Unit",
            "optics_zero_distance": "Zero Distance",
            # Inventory
            "inventory_title": "📦 Inventory",
            "inventory_powder": "💥 Powder",
            "inventory_bullets": "🎯 Bullets",
            "inventory_primers": "💨 Primers",
            "inventory_cases": "🔩 Cases",
            "inventory_quantity": "Quantity",
            "inventory_status": "Status",
            "inventory_cost": "Cost",
            "inventory_very_low": "⚠️ Very Low",
            "inventory_low": "⚠️ Low",
            "inventory_ok": "✓ OK",
            "inventory_good": "✓ Good",
            # Ammunition Profiles
            "ammo_title": "🎯 Ammunition Profiles",
            "ammo_new_profile": "➕ New Ammunition Profile",
            "ammo_name": "Name",
            "ammo_rifle": "Rifle",
            "ammo_caliber": "Caliber",
            "ammo_bullet": "Bullet",
            "ammo_powder": "Powder",
            "ammo_primer": "Primer",
            "ammo_case": "Case",
            "ammo_velocity": "Velocity",
            "ammo_basic_info": "Basic Information",
            "ammo_components": "Components",
            "ammo_ballistics": "Ballistics",
            # Ladder Test
            "ladder_title": "🧪 Ladder Test Lab",
            "ladder_subtitle": "Plan and analyze systematic ladder tests",
            "ladder_new_test": "➕ New Ladder Test",
            "ladder_view": "📊 View/Analyze",
            "ladder_test_name": "Test Name",
            "ladder_date": "Date",
            "ladder_distance": "Distance",
            "ladder_charge_range": "Charge",
            "ladder_results": "Results",
            "ladder_test_info": "Test Information",
            "ladder_components": "Components",
            "ladder_parameters": "Ladder Test Parameters",
            "ladder_start_charge": "Start Charge",
            "ladder_end_charge": "End Charge",
            "ladder_step_size": "Step Size",
            "ladder_steps": "steps",
            # Harmonic Wizard
            "harmonic_title": "🎯 Harmonic Wizard - Seating Depth Assistant",
            "harmonic_new_test": "🆕 New Seating Depth Test",
            "harmonic_disclaimer": '<b style="color: #d9534f;">⚠️ IMPORTANT:</b> This tool analyzes <i>your actual test results</i> and suggests seating depths with high probability of good accuracy. It does NOT calculate theoretical harmonics - it learns from your shots.<br><b>You are always responsible for safe loading within published data limits.</b>',
            "harmonic_how_it_works": "How it works:",
            "harmonic_barrel_profile": "Step 1: Barrel Profile and Configuration",
            "harmonic_components": "Step 2: Ammunition Components",
            "harmonic_test_setup": "Step 3: Define Test Range",
            "harmonic_summary": "Step 4: Summary",
            # Session Logger
            "logger_title": "📝 Logbook",
            "logger_loading_sessions": "🔧 Loading Sessions",
            "logger_shooting_sessions": "🎯 Shooting Sessions",
            "logger_new_loading": "➕ New Loading Session",
            "logger_new_shooting": "➕ New Shooting Session",
            "logger_quantity": "Quantity",
            "logger_time": "Time",
            "logger_rounds_fired": "Rounds Fired",
            "logger_weather": "Weather",
            # GRT Integration
            "grt_title": "🔗 Gordon Reloading Tool Integration",
            "grt_import": "📥 Import from GRT",
            "grt_export": "📤 Export to GRT",
            "grt_analyze": "📊 Analyze vs Actual Data",
            "grt_predicted_velocity": "GRT Velocity",
            "grt_actual_velocity": "Actual Velocity",
            "grt_difference": "Difference",
            "grt_max_pressure": "Max Pressure (PSI)",
            "grt_case_fill": "Fill %",
            "grt_status": "Status",
            "grt_imported": "Imported",
            # Settings
            "settings_title": "⚙️ Settings",
            "settings_units": "📏 Units",
            "settings_defaults": "🎯 Default Values",
            "settings_safety": "⚠️ Safety Settings",
            "settings_database": "💾 Database and Backup",
            "settings_language": "🌐 Language",
            "settings_save": "💾 Save Settings",
            "settings_reset": "🔄 Reset to Default",
            "settings_backup": "📦 Create Backup",
            "settings_restore": "♻️ Restore Backup",
            # Zero Shift Calculator
            "zero_shift_title": "🎯 Zero Shift Calculator",
            "zero_shift_subtitle": "Calculate scope adjustments when changing ammunition",
            "zero_shift_ammo1": "Ammunition 1 (Your zero)",
            "zero_shift_ammo2": "Ammunition 2 (New load)",
            "zero_shift_optic": "Optic",
            "zero_shift_calculate": "🎯 Calculate Adjustment",
            "zero_shift_result": "Result",
            "zero_shift_adjustment": "Adjustment",
            # Messages
            "msg_confirm_delete": "Confirm Deletion",
            "msg_are_you_sure": "Are you sure?",
            "msg_success": "Success",
            "msg_error": "Error",
            "msg_warning": "Warning",
            "msg_info": "Information",
            "msg_saved": "Saved!",
            "msg_deleted": "Deleted!",
            "msg_no_selection": "No Selection",
            "msg_select_first": "Please select a row first!",
            "msg_confirm_exit": "Confirm Exit",
            "msg_exit_question": "Are you sure you want to exit?",
            # Units
            "unit_mm": "mm",
            "unit_cm": "cm",
            "unit_m": "m",
            "unit_fps": "fps",
            "unit_gr": "gr",
            "unit_psi": "PSI",
            "unit_celsius": "°C",
            "unit_percent": "%",
            "unit_pieces": "pcs",
            "unit_grams": "g",
            "unit_minutes": "min",
        }


# Global translator instance
_translator = Translations()


def tr(key: str, *, lang: str | None = None, **kwargs: object) -> str:
    """Shorthand for translation.

    If `lang` is provided, attempt a temporary translation lookup for that
    language; otherwise use the global translator instance.
    """
    if lang is not None:
        try:
            tmp = Translations()
            tmp.set_language(lang)
            return tmp.get(key)
        except Exception:
            pass
    return _translator.get(key, **kwargs)


def set_language(lang_code):
    """Set application language"""
    _translator.set_language(lang_code)


def get_current_language():
    """Get current language code"""
    return _translator.current_language


# Legg til globale språkvalg og funksjon for enkel oversettelse
LANGUAGES = ["no", "en"]


# (previous alternate tr removed; unified implementation above)
