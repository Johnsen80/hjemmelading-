# Valkyrie Ballistics Logo Integration
# This file provides a widget for displaying the Valkyrie Ballistics logo on the landing page and other places in the app.

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

class ValkyrieLogo(QWidget):
    def __init__(self, size=180, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        logo_path = os.path.join(os.path.dirname(__file__), "valkyrie_logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        else:
            label = QLabel("VALKYRIE BALLISTICS")
            label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffd700;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
