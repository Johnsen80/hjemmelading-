from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from src.ui.reloading_theme import ReloadingTheme


class HelpModal(QDialog):
    """Simple help / quick guide modal used across dialogs."""

    def __init__(self, parent=None, title: str = "Help") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
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
        guide = """
    <h2>Quick Guide: Barrel Measurements & Calibration</h2>
    <p>This guide explains how to collect good data for barrel calibration and analysis.</p>
    <h3>1) Measurement points</h3>
    <p>Record outer and inner diameters at several positions along the barrel (pos_mm). Use mm units; the UI will convert if needed.</p>
    <h3>2) Group photos</h3>
    <p>Take a clear, top-down photo of a single shot group on a contrasting background. Include a known-size object (ruler or coin) to calibrate scale, or use the calibrate button to indicate scale.</p>
    <h3>3) Chronograph data</h3>
    <p>Import CSV output from your chronograph or paste velocities. The app computes mean, ES and SD.</p>
    <h3>4) Layout & UX recommendations</h3>
    <p>Based on common user preferences and usability best practices:</p>
    <ul>
    <li>Use a clean left-to-right form flow: selector -> main fields -> auxiliary panels (barrels/tests) on the right or under a collapsible section.</li>
    <li>Show visual previews inline (thumbnail + overlay) so users can immediately verify image quality.</li>
    <li>Provide small contextual help (tooltips or ? buttons) near specialized fields rather than long pages of text.</li>
    <li>Offer an optional wizard for multi-step tasks (calibration) that guides users through shooting, importing, and analyzing.</li>
    <li>Prefer compact summary cards for results (badges, red/yellow/green indicators) and an expandable detailed view.</li>
    </ul>
    <h3>Safety</h3>
    <p>This tool provides analysis and advice only. It does not supply specific powder charges or load tables. Always consult official load manuals and follow safe reloading practices.</p>
    """
        self.text.setHtml(guide)
        layout.addWidget(self.text)

        btn_row = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)
