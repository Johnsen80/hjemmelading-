from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout

from src.ui.reloading_theme import ReloadingTheme
from src.utils.i18n import tr


class HelpModal(QDialog):
    """Simple help / quick guide modal used across dialogs."""

    def __init__(self, parent=None, title: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title or tr("help_modal_title"))
        # Give the dialog an objectName so theme selectors can target it
        self.setObjectName("helpDialog")
        try:
            # Apply the central app stylesheet snippet so widgets inside
            # get consistent look without inline styles.
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass
        self.resize(700, 520)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.text = QTextEdit(self)
        self.text.setReadOnly(True)
        # Short guide: user-facing, non-actionable instructions
        guide = tr("help_modal_guide_html")
        self.text.setHtml(guide)
        layout.addWidget(self.text)

        btn_row = QHBoxLayout()
        self.close_btn = QPushButton(tr("calib_analysis_close"))
        self.close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)
