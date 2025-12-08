"""
VikingSkullLogo - Minimalistisk viking-skalle for Hjemmelading
Stilren, maskulin, norrøn design
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class VikingSkullLogo(QWidget):
    def __init__(self, size=128, show_text=True):
        super().__init__()
        self.logo_size = size
        self.show_text = show_text
        from PyQt6.QtWidgets import QSizePolicy

        self.setMinimumSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.logo_size // 2
        cy = self.logo_size // 2
        scale = self.logo_size / 128.0

        # Skalle (hode)
        painter.setBrush(QBrush(QColor(230, 230, 230)))
        painter.setPen(QPen(QColor(80, 80, 80), 3 * scale))
        painter.drawEllipse(
            int(cx - 38 * scale), int(cy - 32 * scale), int(76 * scale), int(80 * scale)
        )

        # Øyne
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(cx - 16 * scale), int(cy - 8 * scale), int(14 * scale), int(12 * scale)
        )
        painter.drawEllipse(
            int(cx + 2 * scale), int(cy - 8 * scale), int(14 * scale), int(12 * scale)
        )

        # Nese
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawEllipse(
            int(cx - 6 * scale), int(cy + 8 * scale), int(12 * scale), int(10 * scale)
        )

        # Skjegg
        painter.setBrush(QBrush(QColor(120, 90, 40)))
        painter.setPen(QPen(QColor(80, 60, 30), 2 * scale))
        painter.drawEllipse(
            int(cx - 22 * scale), int(cy + 32 * scale), int(44 * scale), int(28 * scale)
        )

        # Hjelm
        painter.setBrush(QBrush(QColor(120, 120, 130)))
        painter.setPen(QPen(QColor(60, 60, 70), 3 * scale))
        painter.drawEllipse(
            int(cx - 38 * scale), int(cy - 38 * scale), int(76 * scale), int(32 * scale)
        )
        # Hjelm stripe
        painter.setBrush(QBrush(QColor(218, 165, 32)))
        painter.setPen(QPen(QColor(218, 165, 32), 4 * scale))
        painter.drawRect(
            int(cx - 8 * scale), int(cy - 38 * scale), int(16 * scale), int(32 * scale)
        )

        # Horn
        painter.setBrush(QBrush(QColor(230, 230, 230)))
        painter.setPen(QPen(QColor(80, 80, 80), 3 * scale))
        painter.drawArc(
            int(cx - 38 * scale),
            int(cy - 48 * scale),
            int(32 * scale),
            int(32 * scale),
            30 * 16,
            120 * 16,
        )
        painter.drawArc(
            int(cx + 6 * scale),
            int(cy - 48 * scale),
            int(32 * scale),
            int(32 * scale),
            120 * 16,
            120 * 16,
        )

        # Korshår bak skallen
        painter.setPen(QPen(QColor(218, 165, 32), 3 * scale))
        painter.drawLine(int(cx - 55 * scale), int(cy), int(cx + 55 * scale), int(cy))
        painter.drawLine(int(cx), int(cy - 55 * scale), int(cx), int(cy + 55 * scale))

        # Ingen tekst i logo-widgeten, kun grafikk
