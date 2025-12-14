from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.ui.icon_registry import get_icon
from src.ui.reloading_theme import ReloadingTheme


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Hjemmelading")
        self.setMinimumSize(520, 320)
        # allow stylesheet targeting and apply central stylesheet safely
        self.setObjectName("onboardingDialog")
        try:
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass
        layout = QVBoxLayout()

        title = QLabel("Welcome — Quick Tour")
        title.setFont(QFont("Segoe UI", 16))
        title.setObjectName("onboardingTitle")
        # optional icon at the top if available
        try:
            ic = get_icon("welcome")
            if ic:
                title.setPixmap(ic.pixmap(24, 24))
        except Exception:
            pass
        layout.addWidget(title)

        body = QLabel(
            "This brief tour highlights key workflows:\n\n"
            "• Measurement Wizard — record QC sessions\n"
            "• Ladder Test Lab — run ladder tests and analyze velocity\n"
            "• Batch QC — run production-style quality control\n\n"
            "You can revisit this later from Settings."
        )
        body.setWordWrap(True)
        layout.addWidget(body)

        btn_layout = QHBoxLayout()
        btn_close = QPushButton("Got it — don't show again")
        btn_close.clicked.connect(self._dismiss_and_save)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _dismiss_and_save(self):
        try:
            settings = QSettings("VALKYRIE", "Hjemmelading")
            settings.setValue("onboarding_seen", True)
        except Exception:
            pass
        self.accept()
