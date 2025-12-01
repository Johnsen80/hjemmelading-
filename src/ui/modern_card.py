"""
Modern Viking Card Widget for PyQt6
- Dark theme, gradient, rounded corners, shadow
- SVG icon support
- Responsive layout
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

class ModernCard(QWidget):
    def __init__(self, title, subtitle, icon_path=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 #23242b, stop:1 #18181c);
            border-radius: 16px;
            border: 2px solid #bfa14a;
            padding: 18px;
        """)
        self.setMinimumWidth(320)
        self.setMaximumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        # Icon
        if icon_path:
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(icon_label)
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffd700;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label)
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont('Segoe UI', 12))
        subtitle_label.setStyleSheet("color: #e0e0e0;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(subtitle_label)
        layout.addStretch()
