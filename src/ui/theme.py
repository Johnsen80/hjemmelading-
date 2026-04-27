"""
Modern, professional Qt style/theme for Hjemmelading
- Flat design, mørk bakgrunn, blå aksent, tydelig typografi
- Brukes av alle hovedvinduer og dialoger
"""

DARK_BG = "#23272e"
MID_BG = "#2c313a"
LIGHT_BG = "#353b45"
ACCENT = "#2980b9"
ACCENT2 = "#27ae60"
WARNING = "#e67e22"
ERROR = "#e74c3c"
TEXT = "#e0e6ed"
SUBTLE = "#b0b6be"
BORDER = "#3c4250"
FONT_FAMILY = "Segoe UI, Arial, sans-serif"

STYLE_SHEET = f"""
QWidget {{
    background: {DARK_BG};
    color: {TEXT};
    font-family: {FONT_FAMILY};
    font-size: 11.5pt;
}}
QMainWindow {{
    background: {DARK_BG};
}}
QMenuBar, QMenu {{
    background: {MID_BG};
    color: {TEXT};
    border: none;
}}
QMenu::item:selected {{
    background: {ACCENT};
    color: white;
}}
QToolBar {{
    background: {MID_BG};
    border-bottom: 1px solid {BORDER};
}}
QStatusBar {{
    background: {MID_BG};
    color: {SUBTLE};
    border-top: 1px solid {BORDER};
}}
QPushButton {{
    background: {ACCENT};
    color: white;
    border-radius: 5px;
    padding: 6px 16px;
    font-weight: 600;
    border: none;
}}
QPushButton:disabled {{
    background: {BORDER};
    color: {SUBTLE};
}}
QPushButton:hover {{
    background: {ACCENT2};
}}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {LIGHT_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    background: {MID_BG};
}}
QTabBar::tab {{
    background: {MID_BG};
    color: {TEXT};
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: white;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    background: {MID_BG};
    font-weight: 600;
}}
QGroupBox:title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {ACCENT};
    font-size: 12pt;
}}
QLabel[variant="cardTitle"] {{
    font-size: 16pt;
    font-weight: bold;
    color: {ACCENT};
    margin-bottom: 8px;
}}
QLabel[variant="sectionHeader"] {{
    font-size: 13pt;
    font-weight: 600;
    color: {ACCENT2};
    margin-top: 12px;
    margin-bottom: 6px;
}}
QTableWidget, QHeaderView::section {{
    background: {LIGHT_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QScrollBar:vertical, QScrollBar:horizontal {{
    background: {MID_BG};
    border: none;
    width: 12px;
    margin: 0px;
}}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: {ACCENT};
    border-radius: 6px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    background: none;
    border: none;
}}
QMessageBox {{
    background: {MID_BG};
    color: {TEXT};
    border-radius: 8px;
}}
QProgressBar {{
    background: {LIGHT_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {ACCENT2};
    border-radius: 6px;
}}

/* ── Top bar ────────────────────────────── */
QWidget#topBar {{
    background: {MID_BG};
    border-bottom: 1px solid {BORDER};
}}
QLabel#appTitle {{
    font-size: 14pt;
    font-weight: 700;
    color: {ACCENT};
    letter-spacing: 1px;
}}

/* ── Nav panel ──────────────────────────── */
QWidget#navPanel {{
    background: {MID_BG};
    border-right: 1px solid {BORDER};
}}
QPushButton[class="navButton"] {{
    background: transparent;
    color: {TEXT};
    text-align: left;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 11pt;
    border: none;
}}
QPushButton[class="navButton"]:hover {{
    background: {LIGHT_BG};
    color: white;
}}
QPushButton[class="navButton"][active="true"] {{
    background: {ACCENT};
    color: white;
    font-weight: 600;
}}

/* ── Module tile cards ──────────────────── */
QFrame#moduleCard {{
    background: {MID_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    min-height: 140px;
}}
QFrame#moduleCard:hover {{
    border: 1px solid {ACCENT};
    background: {LIGHT_BG};
}}
QLabel#landingHeader {{
    font-size: 22pt;
    font-weight: 700;
    color: {TEXT};
}}
QLabel#cardTitle {{
    font-size: 13pt;
    font-weight: 700;
    color: {ACCENT};
}}
QLabel#cardSubtitle {{
    font-size: 10pt;
    color: {SUBTLE};
}}
QPushButton[class="tileOpenBtn"] {{
    background: transparent;
    color: {ACCENT};
    border: 1px solid {ACCENT};
    border-radius: 5px;
    padding: 5px 14px;
    font-weight: 600;
}}
QPushButton[class="tileOpenBtn"]:hover {{
    background: {ACCENT};
    color: white;
}}
"""


def apply_modern_theme(app_or_widget):
    """Apply the modern stylesheet to QApplication or QWidget."""
    app_or_widget.setStyleSheet(STYLE_SHEET)
