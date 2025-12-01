class ReloadingTheme:
    # Public theme constants used by various UI modules. Keep these simple
    # and import-safe so other modules can access them without creating
    # a QApplication or triggering side-effects.
    BACKGROUND = '#0f1315'
    TEXT_PRIMARY = '#d8e1e6'
    TEXT_SECONDARY = '#b8c6cc'
    ACCENT = '#ff6b35'

    @staticmethod
    def get_palette():
        """Return a small palette dict that callers can use programmatically."""
        return {
            'background': ReloadingTheme.BACKGROUND,
            'text_primary': ReloadingTheme.TEXT_PRIMARY,
            'text_secondary': ReloadingTheme.TEXT_SECONDARY,
            'accent': ReloadingTheme.ACCENT,
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

        /* Status / warnings */
        .warning { color: #ff6b35; }
        .danger { color: #d9534f; }

        /* Small accent helpers */
        .accent-olive { color: #7b8a3a; }
        .accent-blue { color: #0b3a66; }

        """
