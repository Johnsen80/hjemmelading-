"""
Hjemmelading - Viking Logo
Eksklusivt, nordisk design med vikinghjelm og runer
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt

class VikingLogo(QWidget):
    """
    Viking-inspired logo for Hjemmelading
    Features stylized viking helmet and runes
    """
    def __init__(self, size=128, show_text=True):
        super().__init__()
        self.logo_size = size
        self.show_text = show_text
        self.setFixedSize(size if not show_text else size * 3, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.logo_size // 2
        cy = self.logo_size // 2
        # Draw viking helmet
        helmet_color = QColor(60, 60, 60)
        horn_color = QColor(220, 200, 120)
        painter.setBrush(helmet_color)
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.drawEllipse(cx-32, cy-32, 64, 48)  # helmet dome
        painter.setBrush(horn_color)
        painter.drawArc(cx-48, cy-40, 32, 32, 30*16, 120*16)  # left horn
        painter.drawArc(cx+16, cy-40, 32, 32, 120*16, 120*16) # right horn
        # Draw runes below helmet
        if self.show_text:
            painter.setFont(QFont("Times", 18, QFont.Weight.Bold))
            painter.setPen(QColor(200, 180, 80))
            painter.drawText(cx-60, cy+40, 120, 32, Qt.AlignmentFlag.AlignCenter, "ᚼᛁᛁᛘᛘᛁᛚᚨᛞᛁᛝ")
            painter.setFont(QFont("Times", 14))
            painter.setPen(QColor(220, 220, 220))
            painter.drawText(cx-60, cy+70, 120, 32, Qt.AlignmentFlag.AlignCenter, "HJEMMELADING")
