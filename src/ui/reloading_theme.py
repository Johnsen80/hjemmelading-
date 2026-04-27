from __future__ import annotations


class ReloadingTheme:
    BACKGROUND = "#f6f4f0"
    PANEL = "#ffffff"
    PANEL_ALT = "#efeae3"
    TEXT_PRIMARY = "#0b1320"
    TEXT_SECONDARY = "#4b5563"
    ACCENT = "#0d7c8c"
    ACCENT_CYAN = "#00a6a6"
    ACCENT_BRASS = "#c9a16e"
    SUCCESS = "#1f8a70"
    WARNING = "#b45309"
    DANGER = "#b91c1c"
    INFO = "#2563eb"
    BORDER = "#d6d2cb"

    @staticmethod
    def get_stylesheet() -> str:
        return f"""
QWidget {{
    background-color: {ReloadingTheme.BACKGROUND};
    color: {ReloadingTheme.TEXT_PRIMARY};
}}
QWidget#navPanel, QWidget#inspectorPanel {{
    background-color: {ReloadingTheme.PANEL};
}}
QFrame, QGroupBox, QTabWidget::pane, QMenu, QDialog {{
    background-color: {ReloadingTheme.PANEL};
    border: 1px solid {ReloadingTheme.BORDER};
    border-radius: 8px;
}}
QPushButton {{
    background-color: {ReloadingTheme.ACCENT};
    color: white;
    border: 1px solid {ReloadingTheme.ACCENT};
    border-radius: 6px;
    padding: 6px 10px;
}}
QPushButton:hover {{
    background-color: {ReloadingTheme.ACCENT_CYAN};
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: {ReloadingTheme.PANEL_ALT};
    color: {ReloadingTheme.TEXT_PRIMARY};
    border: 1px solid {ReloadingTheme.BORDER};
    border-radius: 6px;
    padding: 6px;
}}
QLabel#currentWorkflowLabel {{
    color: {ReloadingTheme.TEXT_SECONDARY};
    font-weight: 600;
}}
QWidget#topBar {{
    background-color: {ReloadingTheme.PANEL};
    border-bottom: 1px solid {ReloadingTheme.BORDER};
}}
QLabel#syncStatus {{
    color: {ReloadingTheme.TEXT_SECONDARY};
    padding: 4px 8px;
}}
QLabel#appTitle {{
    color: {ReloadingTheme.TEXT_PRIMARY};
    font-weight: 700;
}}
QFrame#inspectorCard {{
    background-color: {ReloadingTheme.PANEL_ALT};
    border: 1px solid {ReloadingTheme.BORDER};
    border-radius: 12px;
}}
"""

    @staticmethod
    def get_safe_stylesheet() -> str:
        return ReloadingTheme.get_stylesheet()

    @staticmethod
    def get_button_stylesheet() -> str:
        return f"""
QPushButton {{ min-height: 36px; padding: 8px 12px; border-radius: 6px; }}
QPushButton#homeButton {{ font-weight: 800; }}
QPushButton#topHomeButton {{ font-weight: 800; letter-spacing: 0.5px; }}
QPushButton#measurementWizardButton {{ padding-left: 10px; }}
QPushButton[class="navButton"] {{
    min-height: 40px;
    text-align: left;
    padding: 10px 12px;
    background-color: {ReloadingTheme.PANEL};
    color: {ReloadingTheme.TEXT_PRIMARY};
    border: 1px solid {ReloadingTheme.BORDER};
    border-radius: 10px;
}}
QPushButton[class="navButton"]:hover {{
    background-color: {ReloadingTheme.PANEL_ALT};
    border: 1px solid {ReloadingTheme.ACCENT_BRASS};
}}
QPushButton[active="true"] {{
    background-color: {ReloadingTheme.ACCENT};
    color: white;
    border: 1px solid {ReloadingTheme.ACCENT};
}}
QPushButton[class="landingBig"] {{
    min-height: 44px;
    padding: 10px 14px;
    border-radius: 10px;
    font-weight: 600;
}}
QPushButton[variant="secondary"] {{
    background-color: {ReloadingTheme.PANEL};
    color: {ReloadingTheme.TEXT_PRIMARY};
    border: 1px solid {ReloadingTheme.BORDER};
}}
QPushButton[variant="secondary"]:hover {{
    background-color: {ReloadingTheme.PANEL_ALT};
    border: 1px solid {ReloadingTheme.ACCENT_BRASS};
}}
"""

    @staticmethod
    def get_navbar_style() -> str:
        return """
QWidget { background-color: transparent; }
QWidget > QPushButton { background-color: transparent; }
QLabel#currentWorkflowLabel { color: #4b5563; font-weight: 600; }
"""

    @staticmethod
    def get_card_style() -> str:
        return f"""
QWidget#modernCard {{
    background-color: {ReloadingTheme.PANEL};
    border: 1px solid {ReloadingTheme.BORDER};
    border-radius: 14px;
    padding: 12px;
}}
QLabel#cardTitle {{
    color: {ReloadingTheme.TEXT_PRIMARY};
    font-weight: 700;
}}
QLabel#cardSubtitle {{
    color: {ReloadingTheme.TEXT_SECONDARY};
}}
"""

    @staticmethod
    def get_banner_style() -> str:
        return f"""
QWidget#banner {{
    background-color: #fff8e8;
    border: 1px solid {ReloadingTheme.ACCENT_BRASS};
    border-radius: 10px;
    padding: 10px;
}}
QWidget#banner QLabel {{
    color: {ReloadingTheme.TEXT_PRIMARY};
}}
QPushButton#bannerAction {{
    background-color: {ReloadingTheme.ACCENT_BRASS};
    color: {ReloadingTheme.TEXT_PRIMARY};
    border: 1px solid {ReloadingTheme.ACCENT_BRASS};
    border-radius: 6px;
    padding: 6px 12px;
}}
"""

    @staticmethod
    def get_palette() -> dict[str, str]:
        return {
            "background": ReloadingTheme.BACKGROUND,
            "panel": ReloadingTheme.PANEL,
            "panel_alt": ReloadingTheme.PANEL_ALT,
            "text_primary": ReloadingTheme.TEXT_PRIMARY,
            "text_secondary": ReloadingTheme.TEXT_SECONDARY,
            "accent": ReloadingTheme.ACCENT,
            "accent_cyan": ReloadingTheme.ACCENT_CYAN,
            "accent_brass": ReloadingTheme.ACCENT_BRASS,
            "success": ReloadingTheme.SUCCESS,
            "warning": ReloadingTheme.WARNING,
            "danger": ReloadingTheme.DANGER,
            "info": ReloadingTheme.INFO,
            "border": ReloadingTheme.BORDER,
        }
