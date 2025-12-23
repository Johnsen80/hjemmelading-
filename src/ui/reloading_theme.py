class ReloadingTheme:
    # Public theme constants used by various UI modules. Keep these simple
    # and import-safe so other modules can access them without creating
    # a QApplication or triggering side-effects.
    BACKGROUND = "#0f1315"
    TEXT_PRIMARY = "#d8e1e6"
    TEXT_SECONDARY = "#b8c6cc"
    ACCENT = "#ff6b35"

    @staticmethod
    def get_palette():
        """Return a small palette dict that callers can use programmatically."""
        return {
            "background": ReloadingTheme.BACKGROUND,
            "text_primary": ReloadingTheme.TEXT_PRIMARY,
            "text_secondary": ReloadingTheme.TEXT_SECONDARY,
            "accent": ReloadingTheme.ACCENT,
        }

    @staticmethod
    def get_stylesheet():
        # Return a comprehensive stylesheet for the application. Keep this
        # method pure and free of external dependencies to avoid import-time
        # failures.
        return """
        /* Industrial Dark Theme - gunmetal, tactical accents, technical fonts */
        QWidget {
            background-color: #0f1315; /* deep charcoal */
            color: #d8e1e6; /* soft white */
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QMainWindow { background-color: #0f1315; }

        /* Panel / Card */
        QGroupBox, QFrame {
            background-color: #111418; /* panel */
            border: 1px solid #21262a; /* subtle metal border */
            border-radius: 4px;
            padding: 8px;
        }

        /* Labels */
        QLabel {
            color: #d8e1e6;
        }

        /* Primary buttons: gunmetal, square, robust */
        QPushButton {
            background-color: #232a2f; /* gunmetal */
            color: #e6eef3;
            border: 1px solid #2f363b;
            border-radius: 4px;
            padding: 10px 18px;
            font-weight: 700;
            font-size: 14px;
            min-height: 36px;
        }
        /* Hover gives a thin accent edge (glow substitute) */
        QPushButton:hover {
            border: 1px solid #ff6b35; /* accent orange edge */
            background-color: #2b3136;
        }
        QPushButton:pressed {
            background-color: #1b2023;
            border: 1px solid #1f2427;
        }

        /* Secondary buttons: outline tactical */
        QPushButton[variant="secondary"] {
            background: transparent;
            color: #d8e1e6;
            border: 1px solid #3a4044;
        }
        QPushButton[variant="secondary"]:hover {
            border: 1px solid #5a6b2e; /* olive hint */
        }

        /* Numeric displays should use monospaced font for precision */
        .numeric, QLineEdit.numeric, QLabel.numeric {
            font-family: 'JetBrains Mono', 'Roboto Mono', 'monospace';
            letter-spacing: 0.5px;
            color: #dbe9ef;
        }

        QLineEdit, QTextEdit {
            background-color: #0d1112;
            color: #d8e1e6;
            border: 1px solid #202428;
            border-radius: 4px;
            padding: 6px;
        }

        QTabWidget::pane { border: none; }
        QTabBar::tab {
            background: transparent;
            color: #b8c6cc;
            padding: 8px 12px;
            margin-right: 6px;
            border-radius: 3px;
        }
        QTabBar::tab:selected {
            background: #161a1c;
            color: #e6eef3;
            border: 1px solid #2a3134;
        }

        QTableView, QListView, QTreeView {
            background-color: #0d1112;
            color: #d8e1e6;
            gridline-color: #15181a;
        }

        /* Landing page big buttons */
        QPushButton.landingBig {
            background: rgba(35, 38, 42, 0.86);
            color: #fbfbfb;
            border: 1px solid rgba(255,107,53,0.10);
            border-radius: 10px;
            padding: 14px 22px;
            font-size: 15px;
            font-weight: 800;
            min-width: 260px;
            min-height: 64px;
            /* backdrop-filter is unsupported in many Qt style engines; remove it */
            /* fallback: slightly translucent background already provides visual depth */
        }
        QPushButton.landingBig:hover {
            border: 1px solid rgba(255,107,53,0.45);
            background: rgba(40,48,52,0.92);
        }
        QPushButton.landingBig:pressed {
            background: #16181a;
            color: #e8eef2;
        }

        /* Make prominent headings light and slightly luminous */
        QLabel#landingHeader {
            color: #f5f8fa;
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 1px;
        }

        /* Image preview styling for small thumbnails */
        QLabel#imagePreview {
            border: 1px solid #888;
            background-color: #0b0d0e;
            padding: 2px;
        }

        /* Status / warnings */
        .warning { color: #ff6b35; }
        .danger { color: #d9534f; }

        /* Small accent helpers */
        .accent-olive { color: #7b8a3a; }
        .accent-blue { color: #0b3a66; }

        """

    @staticmethod
    def get_card_style():
        """Return a small stylesheet snippet for modern card widgets.
        Callers can apply this via `widget.setObjectName('modernCard')`
        and then apply `ReloadingTheme.get_card_style()` at widget-level.
        """
        return """
        QWidget#modernCard {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #23242b, stop:1 #18181c);
            border-radius: 12px;
            border: 2px solid #bfa14a;
            padding: 14px;
        }
        QWidget#modernCard QLabel#cardTitle {
            color: #ff6b35;
            font-size: 18px;
            font-weight: 700;
        }
        QWidget#modernCard QLabel#cardSubtitle {
            color: #d8e1e6;
            font-size: 12px;
        }
        """

    @staticmethod
    def get_banner_style():
        """Return a compact banner style used for disabled-feature notices."""
        return """
        QWidget#banner {
            background-color: #241f2a;
            border: 1px solid #3a2f37;
            color: #f3e9e6;
            padding: 10px;
            border-radius: 6px;
        }
        """

    @staticmethod
    def get_button_stylesheet() -> str:
        """Return a stylesheet snippet for global button styling (used by MainWindow)."""
        return """
        /* Centralized button styling snippet */
        QPushButton { min-height: 36px; padding: 8px 12px; border-radius: 6px; }
        QPushButton#homeButton { font-weight: 800; }
        QPushButton#measurementWizardButton { padding-left: 10px; }
        QPushButton[variant="secondary"] { border-style: solid; }
        """

    @staticmethod
    def get_navbar_style() -> str:
        """Return a small stylesheet snippet for navigation bar widgets."""
        return """
        QWidget { background-color: transparent; }
        QWidget > QPushButton { background-color: transparent; }
        QLabel#currentWorkflowLabel { color: #b8c6cc; font-weight: 600; }
        """
