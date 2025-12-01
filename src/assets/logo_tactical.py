"""
HJEMMELADING - Minimalist Tactical Logo
Clean, professional, masculine design
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QLinearGradient, QRadialGradient
from PyQt6.QtSvg import QSvgRenderer


class TacticalLogo(QWidget):
    """
    Minimalist tactical crosshair + cartridge design
    Professional, clean, masculine
    """
    
    def __init__(self, size=128, show_text=True):
        super().__init__()
        self.logo_size = size
        self.show_text = show_text
        from PyQt6.QtWidgets import QSizePolicy
        self.setMinimumSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def paintEvent(self, event):
        """Draw minimalist tactical logo"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.logo_size // 2
        cy = self.logo_size // 2
        
        # Draw the tactical crosshair with cartridge
        self.draw_tactical_design(painter, cx, cy)
        
        # Draw text if enabled
        if self.show_text:
            self.draw_logo_text(painter)
    
    def draw_tactical_design(self, painter, cx, cy):
        """
        Minimalist tactical design:
        - Crosshair (precision)
        - Bullet cartridge silhouette
        - Range finder markers
        """
        scale = self.logo_size / 128.0
        
        # Background circle (subtle)
        radial = QRadialGradient(cx, cy, 60*scale)
        radial.setColorAt(0, QColor(40, 40, 45, 100))
        radial.setColorAt(1, QColor(20, 20, 25, 0))
        painter.setBrush(QBrush(radial))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 60*scale), int(cy - 60*scale), 
                           int(120*scale), int(120*scale))
        
        # Outer tactical circle
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(100, 100, 105), 2*scale))
        painter.drawEllipse(int(cx - 55*scale), int(cy - 55*scale), 
                           int(110*scale), int(110*scale))
        
        # Inner precision circle
        painter.setPen(QPen(QColor(218, 165, 32), 2*scale))
        painter.drawEllipse(int(cx - 50*scale), int(cy - 50*scale), 
                           int(100*scale), int(100*scale))
        
        # BULLET CARTRIDGE (center, vertical)
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPolygonF
        
        # Cartridge gradient (brass)
        brass_gradient = QLinearGradient(cx, cy - 45*scale, cx, cy + 45*scale)
        brass_gradient.setColorAt(0, QColor(100, 80, 30))
        brass_gradient.setColorAt(0.2, QColor(184, 134, 11))
        brass_gradient.setColorAt(0.5, QColor(218, 165, 32))
        brass_gradient.setColorAt(0.8, QColor(184, 134, 11))
        brass_gradient.setColorAt(1, QColor(120, 90, 35))
        
        painter.setBrush(QBrush(brass_gradient))
        painter.setPen(QPen(QColor(80, 60, 20), 2*scale))
        
        # Cartridge silhouette (clean, professional)
        cartridge = [
            (cx - 12*scale, cy + 40*scale),   # Base left
            (cx - 12*scale, cy - 25*scale),   # Body left
            (cx - 10*scale, cy - 35*scale),   # Shoulder left
            (cx - 6*scale, cy - 42*scale),    # Neck left
            (cx - 4*scale, cy - 48*scale),    # Bullet left
            (cx, cy - 50*scale),               # Tip
            (cx + 4*scale, cy - 48*scale),    # Bullet right
            (cx + 6*scale, cy - 42*scale),    # Neck right
            (cx + 10*scale, cy - 35*scale),   # Shoulder right
            (cx + 12*scale, cy - 25*scale),   # Body right
            (cx + 12*scale, cy + 40*scale),   # Base right
        ]
        cartridge_poly = QPolygonF([QPointF(x, y) for x, y in cartridge])
        painter.drawPolygon(cartridge_poly)
        
        # Primer (bottom detail)
        painter.setBrush(QBrush(QColor(60, 50, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 6*scale), int(cy + 35*scale), 
                           int(12*scale), int(8*scale))
        
        # Bullet tip highlight
        tip_gradient = QLinearGradient(cx, cy - 50*scale, cx, cy - 40*scale)
        tip_gradient.setColorAt(0, QColor(140, 140, 145))
        tip_gradient.setColorAt(1, QColor(80, 80, 85))
        painter.setBrush(QBrush(tip_gradient))
        
        bullet_tip = [
            (cx - 4*scale, cy - 42*scale),
            (cx, cy - 50*scale),
            (cx + 4*scale, cy - 42*scale),
        ]
        bullet_poly = QPolygonF([QPointF(x, y) for x, y in bullet_tip])
        painter.drawPolygon(bullet_poly)
        
        # CROSSHAIR - Tactical, precise
        painter.setPen(QPen(QColor(255, 255, 255, 180), 2*scale))
        
        # Horizontal line
        painter.drawLine(int(cx - 55*scale), int(cy), int(cx - 18*scale), int(cy))
        painter.drawLine(int(cx + 18*scale), int(cy), int(cx + 55*scale), int(cy))
        
        # Vertical line
        painter.drawLine(int(cx), int(cy - 55*scale), int(cx), int(cy - 18*scale))
        painter.drawLine(int(cx), int(cy + 18*scale), int(cx), int(cy + 55*scale))
        
        # Center dot
        painter.setBrush(QBrush(QColor(255, 0, 0, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 2*scale), int(cy - 2*scale), 
                           int(4*scale), int(4*scale))
        
        # RANGE FINDER MARKS
        painter.setPen(QPen(QColor(218, 165, 32, 180), 1.5*scale))
        
        # Cardinal marks (N, E, S, W)
        for angle in [0, 90, 180, 270]:
            import math
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * 50 * scale
            y1 = cy + math.sin(rad) * 50 * scale
            x2 = cx + math.cos(rad) * 45 * scale
            y2 = cy + math.sin(rad) * 45 * scale
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Secondary marks
        for angle in [45, 135, 225, 315]:
            import math
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * 50 * scale
            y1 = cy + math.sin(rad) * 50 * scale
            x2 = cx + math.cos(rad) * 47 * scale
            y2 = cy + math.sin(rad) * 47 * scale
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Corner brackets (mil-spec)
        bracket_size = 10 * scale
        bracket_offset = 52 * scale
        painter.setPen(QPen(QColor(218, 165, 32), 2*scale))
        
        for x_dir, y_dir in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            x_pos = cx + x_dir * bracket_offset
            y_pos = cy + y_dir * bracket_offset
            painter.drawLine(int(x_pos), int(y_pos), 
                           int(x_pos - x_dir * bracket_size), int(y_pos))
            painter.drawLine(int(x_pos), int(y_pos), 
                           int(x_pos), int(y_pos - y_dir * bracket_size))
    
    def draw_logo_text(self, painter):
        """Draw professional text"""
        # Main title
        font = QFont("Arial Black", int(self.logo_size / 5.5))
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        
        # Shadow
        painter.setPen(QPen(QColor(0, 0, 0, 200), 2))
        painter.drawText(self.logo_size + 12, self.logo_size // 2 + 2, "HJEMMELADING")
        
        # Main text
        painter.setPen(QPen(QColor(218, 165, 32)))
        painter.drawText(self.logo_size + 10, self.logo_size // 2, "HJEMMELADING")
        
        # Subtitle
        subtitle_font = QFont("Arial", int(self.logo_size / 11))
        subtitle_font.setBold(True)
        subtitle_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(180, 180, 190))
        painter.drawText(self.logo_size + 10, self.logo_size // 2 + int(self.logo_size / 5), 
                        "PRECISION RELOADING")


class CompactTacticalIcon(QWidget):
    """Compact tactical icon for toolbar"""
    
    def __init__(self, size=32):
        super().__init__()
        self.icon_size = size
        self.setFixedSize(size, size)
        
    def paintEvent(self, event):
        """Draw compact tactical icon"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.icon_size // 2
        cy = self.icon_size // 2
        scale = self.icon_size / 32.0
        
        # Outer circle
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(100, 100, 105), 2*scale))
        painter.drawEllipse(int(cx - 14*scale), int(cy - 14*scale), 
                           int(28*scale), int(28*scale))
        
        # Inner circle (gold)
        painter.setPen(QPen(QColor(218, 165, 32), 1.5*scale))
        painter.drawEllipse(int(cx - 12*scale), int(cy - 12*scale), 
                           int(24*scale), int(24*scale))
        
        # Bullet cartridge (simplified)
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPolygonF
        
        brass_gradient = QLinearGradient(cx, cy - 12*scale, cx, cy + 12*scale)
        brass_gradient.setColorAt(0, QColor(184, 134, 11))
        brass_gradient.setColorAt(0.5, QColor(218, 165, 32))
        brass_gradient.setColorAt(1, QColor(150, 110, 30))
        
        painter.setBrush(QBrush(brass_gradient))
        painter.setPen(QPen(QColor(80, 60, 20), 1*scale))
        
        cartridge = [
            (cx - 4*scale, cy + 12*scale),
            (cx - 4*scale, cy - 8*scale),
            (cx - 3*scale, cy - 11*scale),
            (cx, cy - 13*scale),
            (cx + 3*scale, cy - 11*scale),
            (cx + 4*scale, cy - 8*scale),
            (cx + 4*scale, cy + 12*scale),
        ]
        cartridge_poly = QPolygonF([QPointF(x, y) for x, y in cartridge])
        painter.drawPolygon(cartridge_poly)
        
        # Crosshair
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5*scale))
        painter.drawLine(int(cx - 14*scale), int(cy), int(cx - 6*scale), int(cy))
        painter.drawLine(int(cx + 6*scale), int(cy), int(cx + 14*scale), int(cy))
        painter.drawLine(int(cx), int(cy - 14*scale), int(cx), int(cy - 6*scale))
        painter.drawLine(int(cx), int(cy + 6*scale), int(cx), int(cy + 14*scale))
        
        # Center dot
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 1*scale), int(cy - 1*scale), 
                           int(2*scale), int(2*scale))


def get_window_icon_pixmap(size=64):
    """Get tactical logo as QPixmap for window icon"""
    widget = CompactTacticalIcon(size)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    widget.render(pixmap)
    return pixmap


try:
    from src.ui.reloading_theme import ReloadingTheme
except Exception:
    # Fallback minimal theme if canonical import fails
    class ReloadingTheme:
        @staticmethod
        def get_stylesheet():
            return """
            QWidget { background-color: #23242b; color: #e0e0e0; }
            """


if __name__ == '__main__':
    """Test the tactical logo"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("HJEMMELADING - Tactical Logo")
    window.resize(800, 400)
    window.setStyleSheet(ReloadingTheme.get_stylesheet())
    
    layout = QVBoxLayout()
    
    # Large logo with text
    large_logo = TacticalLogo(size=128, show_text=True)
    layout.addWidget(large_logo)
    
    # Icons row
    icons_layout = QHBoxLayout()
    for size in [64, 48, 32, 24, 16]:
        icon = CompactTacticalIcon(size)
        icons_layout.addWidget(icon)
    layout.addLayout(icons_layout)
    
    info = QLabel("Tactical crosshair + cartridge design - minimalist & professional")
    info.setStyleSheet(f"color: {ReloadingTheme.TEXT_SECONDARY}; padding: 20px;")
    layout.addWidget(info)
    
    window.setLayout(layout)
    window.show()
    
    sys.exit(app.exec())
