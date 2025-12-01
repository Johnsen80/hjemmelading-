"""
Hjemmelading - Professional Logo with Skull Theme
Tough, masculine design for serious reloaders
"""

import logging

# Guard Qt imports so this module can be imported in environments
# without a GUI (headless CI, tests, etc.). Methods that require
# Qt will only run when `_HAS_QT` is True.
try:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QLinearGradient
    from PyQt6.QtSvg import QSvgRenderer
    _HAS_QT = True
except Exception:
    # Minimal placeholders to allow importing this module in headless tests.
    QWidget = object
    QLabel = object
    QVBoxLayout = object
    QHBoxLayout = object
    Qt = type("_NoQt", (), {})()
    QPixmap = None
    _HAS_QT = False

class SkullLogo(QWidget):
    """
    Professional skull-themed logo for Hjemmelading
    Represents precision, danger awareness, and serious craftsmanship
    """
    
    def __init__(self, size=128, show_text=True):
        super().__init__()
        self.logo_size = size
        self.show_text = show_text
        self.setFixedSize(size if not show_text else size * 3, size)
        
    def paintEvent(self, event):
        """Draw the skull logo"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center point
        center_x = self.logo_size // 2
        center_y = self.logo_size // 2
        
        # Draw skull with bullet cartridge design
        self.draw_skull_cartridge(painter, center_x, center_y)
        
        # Draw text if enabled
        if self.show_text:
            self.draw_logo_text(painter)
    
    def draw_skull_cartridge(self, painter, cx, cy):
        """
        Badass tactical skull - realistic, menacing, professional
        """
        scale = self.logo_size / 128.0
        
        # Bullet cartridge silhouette (background)
        brass_gradient = QLinearGradient(cx, cy - 50*scale, cx, cy + 50*scale)
        brass_gradient.setColorAt(0, QColor(60, 50, 30))
        brass_gradient.setColorAt(0.3, QColor(139, 101, 8))
        brass_gradient.setColorAt(0.7, QColor(184, 134, 11))
        brass_gradient.setColorAt(1, QColor(100, 80, 20))
        
        painter.setBrush(QBrush(brass_gradient))
        painter.setPen(QPen(QColor(80, 60, 20), 2*scale))
        
        # Cartridge shape (vertical)
        from PyQt6.QtCore import QPointF, QRectF
        from PyQt6.QtGui import QPolygonF
        cartridge_points = [
            (cx - 18*scale, cy + 50*scale),  # Bottom left
            (cx - 18*scale, cy - 30*scale),  # Top left
            (cx - 15*scale, cy - 40*scale),  # Shoulder left
            (cx - 8*scale, cy - 50*scale),   # Neck left
            (cx, cy - 55*scale),              # Bullet tip
            (cx + 8*scale, cy - 50*scale),   # Neck right
            (cx + 15*scale, cy - 40*scale),  # Shoulder right
            (cx + 18*scale, cy - 30*scale),  # Top right
            (cx + 18*scale, cy + 50*scale),  # Bottom right
        ]
        cartridge_polygon = QPolygonF([QPointF(x, y) for x, y in cartridge_points])
        painter.drawPolygon(cartridge_polygon)
        
        # Primer pocket (bottom detail)
        painter.setBrush(QBrush(QColor(40, 30, 20)))
        painter.drawEllipse(int(cx - 8*scale), int(cy + 45*scale), int(16*scale), int(10*scale))
        
        # SKULL - Realistic and menacing
        skull_gradient = QLinearGradient(cx, cy - 30*scale, cx, cy + 30*scale)
        skull_gradient.setColorAt(0, QColor(180, 180, 180))  # Light bone
        skull_gradient.setColorAt(0.3, QColor(140, 140, 140))  # Medium bone
        skull_gradient.setColorAt(0.7, QColor(100, 100, 100))  # Shadow
        skull_gradient.setColorAt(1, QColor(60, 60, 60))  # Dark shadow
        
        # Cranium (realistic shape)
        painter.setBrush(QBrush(skull_gradient))
        painter.setPen(QPen(QColor(40, 40, 40), 2*scale))
        
        # Main skull shape (more angular, realistic)
        skull_rect = QRectF(cx - 30*scale, cy - 35*scale, 60*scale, 55*scale)
        painter.drawEllipse(skull_rect)
        
        # Jaw (lower part)
        jaw_gradient = QLinearGradient(cx, cy + 10*scale, cx, cy + 35*scale)
        jaw_gradient.setColorAt(0, QColor(120, 120, 120))
        jaw_gradient.setColorAt(1, QColor(80, 80, 80))
        painter.setBrush(QBrush(jaw_gradient))
        
        jaw_points = [
            (cx - 22*scale, cy + 12*scale),
            (cx - 18*scale, cy + 30*scale),
            (cx - 10*scale, cy + 35*scale),
            (cx, cy + 38*scale),
            (cx + 10*scale, cy + 35*scale),
            (cx + 18*scale, cy + 30*scale),
            (cx + 22*scale, cy + 12*scale),
        ]
        jaw_polygon = QPolygonF([QPointF(x, y) for x, y in jaw_points])
        painter.drawPolygon(jaw_polygon)
        
        # EYE SOCKETS - Deep, realistic, menacing
        eye_gradient = QLinearGradient(0, cy - 15*scale, 0, cy - 5*scale)
        eye_gradient.setColorAt(0, QColor(10, 10, 10))  # Pure black
        eye_gradient.setColorAt(0.5, QColor(30, 30, 30))
        eye_gradient.setColorAt(1, QColor(50, 50, 50))
        
        painter.setBrush(QBrush(eye_gradient))
        painter.setPen(QPen(QColor(30, 30, 30), 2*scale))
        
        # Left eye - angular, scary
        left_eye_points = [
            (cx - 24*scale, cy - 15*scale),
            (cx - 14*scale, cy - 18*scale),
            (cx - 10*scale, cy - 12*scale),
            (cx - 12*scale, cy - 5*scale),
            (cx - 20*scale, cy - 8*scale),
        ]
        left_eye = QPolygonF([QPointF(x, y) for x, y in left_eye_points])
        painter.drawPolygon(left_eye)
        
        # Right eye
        right_eye_points = [
            (cx + 24*scale, cy - 15*scale),
            (cx + 14*scale, cy - 18*scale),
            (cx + 10*scale, cy - 12*scale),
            (cx + 12*scale, cy - 5*scale),
            (cx + 20*scale, cy - 8*scale),
        ]
        right_eye = QPolygonF([QPointF(x, y) for x, y in right_eye_points])
        painter.drawPolygon(right_eye)
        
        # Red glow in eyes (evil/danger)
        glow_gradient = QLinearGradient(0, cy - 15*scale, 0, cy - 8*scale)
        glow_gradient.setColorAt(0, QColor(255, 0, 0, 100))
        glow_gradient.setColorAt(1, QColor(200, 0, 0, 50))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 18*scale), int(cy - 13*scale), int(8*scale), int(6*scale))
        painter.drawEllipse(int(cx + 10*scale), int(cy - 13*scale), int(8*scale), int(6*scale))
        
        # NOSE CAVITY - Triangular, deep
        painter.setBrush(QBrush(QColor(10, 10, 10)))
        painter.setPen(QPen(QColor(30, 30, 30), 1.5*scale))
        nose_points = [
            (cx, cy - 8*scale),
            (cx - 7*scale, cy + 5*scale),
            (cx + 7*scale, cy + 5*scale),
        ]
        nose_polygon = QPolygonF([QPointF(x, y) for x, y in nose_points])
        painter.drawPolygon(nose_polygon)
        
        # TEETH - Realistic, separated, menacing
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(QPen(QColor(60, 60, 60), 1*scale))
        
        # Upper teeth (visible in jaw gap)
        teeth_y = cy + 15*scale
        tooth_width = 4 * scale
        tooth_height = 8 * scale
        
        for i in range(6):
            tooth_x = cx - 15*scale + i * 6*scale
            # Individual teeth with rounded tops
            painter.drawRoundedRect(int(tooth_x), int(teeth_y), 
                                  int(tooth_width), int(tooth_height),
                                  2*scale, 2*scale)
        
        # Lower teeth
        teeth_y_lower = cy + 24*scale
        for i in range(6):
            tooth_x = cx - 15*scale + i * 6*scale
            painter.drawRoundedRect(int(tooth_x), int(teeth_y_lower), 
                                  int(tooth_width), int(tooth_height - 2*scale),
                                  2*scale, 2*scale)
        
        # CRACKS in skull (battle-worn, realistic)
        painter.setPen(QPen(QColor(40, 40, 40), 1.5*scale))
        painter.drawLine(int(cx - 15*scale), int(cy - 28*scale), 
                        int(cx - 8*scale), int(cy - 18*scale))
        painter.drawLine(int(cx + 15*scale), int(cy - 28*scale), 
                        int(cx + 8*scale), int(cy - 18*scale))
        
        # CROSSHAIR - Tactical overlay (subtle)
        painter.setPen(QPen(QColor(255, 0, 0, 80), 1*scale, Qt.PenStyle.DotLine))
        painter.drawLine(int(cx - 40*scale), int(cy), int(cx + 40*scale), int(cy))
        painter.drawLine(int(cx), int(cy - 40*scale), int(cx), int(cy + 40*scale))
        
        # Corner brackets (mil-spec targeting)
        bracket_size = 8 * scale
        bracket_offset = 45 * scale
        painter.setPen(QPen(QColor(255, 0, 0, 150), 2*scale))
        
        for x_dir, y_dir in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            x_pos = cx + x_dir * bracket_offset
            y_pos = cy + y_dir * bracket_offset
            painter.drawLine(int(x_pos), int(y_pos), 
                           int(x_pos - x_dir * bracket_size), int(y_pos))
            painter.drawLine(int(x_pos), int(y_pos), 
                           int(x_pos), int(y_pos - y_dir * bracket_size))
    
    def draw_logo_text(self, painter):
        """Draw hardcore military-style text"""
        # Main title - aggressive, bold
        font = QFont("Arial Black", int(self.logo_size / 5.5))
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        painter.setFont(font)
        
        # Deep shadow for 3D effect
        painter.setPen(QPen(QColor(0, 0, 0, 200), 3))
        painter.drawText(self.logo_size + 13, self.logo_size // 2 + 3, "HJEMMELADING")
        
        # Brass outline
        painter.setPen(QPen(QColor(139, 101, 8), 2))
        painter.drawText(self.logo_size + 11, self.logo_size // 2 + 1, "HJEMMELADING")
        
        # Main text (bright brass/gold)
        painter.setPen(QPen(QColor(218, 165, 32), 1))
        painter.drawText(self.logo_size + 10, self.logo_size // 2, "HJEMMELADING")
        
        # Subtitle - tactical/military style
        subtitle_font = QFont("Arial", int(self.logo_size / 11))
        subtitle_font.setBold(True)
        subtitle_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(200, 200, 210))
        painter.drawText(self.logo_size + 10, self.logo_size // 2 + int(self.logo_size / 5), 
                        "TACTICAL RELOADING SYSTEM")
        
        # Warning stripe (danger indicator)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        painter.drawRect(self.logo_size + 10, self.logo_size // 2 + int(self.logo_size / 4.5),
                        int(self.logo_size * 2.3), 2)


class CompactSkullIcon(QWidget):
    """Compact skull icon for toolbar/buttons"""
    
    def __init__(self, size=32):
        super().__init__()
        self.icon_size = size
        self.setFixedSize(size, size)
        
    def paintEvent(self, event):
        """Draw compact badass skull icon"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.icon_size // 2
        cy = self.icon_size // 2
        scale = self.icon_size / 32.0
        
        # Skull silhouette (realistic bone color)
        gradient = QLinearGradient(cx, cy - 14*scale, cx, cy + 14*scale)
        gradient.setColorAt(0, QColor(180, 180, 180))
        gradient.setColorAt(0.5, QColor(120, 120, 120))
        gradient.setColorAt(1, QColor(80, 80, 80))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(40, 40, 40), 1.5*scale))
        painter.drawEllipse(int(cx - 11*scale), int(cy - 13*scale), 
                           int(22*scale), int(26*scale))
        
        # Jaw
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPolygonF
        jaw_points = [
            (cx - 9*scale, cy + 6*scale),
            (cx - 6*scale, cy + 12*scale),
            (cx, cy + 14*scale),
            (cx + 6*scale, cy + 12*scale),
            (cx + 9*scale, cy + 6*scale),
        ]
        jaw_polygon = QPolygonF([QPointF(x, y) for x, y in jaw_points])
        painter.drawPolygon(jaw_polygon)
        
        # Eye sockets (deep black)
        painter.setBrush(QBrush(QColor(10, 10, 10)))
        painter.setPen(QPen(QColor(30, 30, 30), 1*scale))
        
        # Left eye (angular)
        left_eye_points = [
            (cx - 9*scale, cy - 6*scale),
            (cx - 5*scale, cy - 8*scale),
            (cx - 4*scale, cy - 4*scale),
            (cx - 7*scale, cy - 2*scale),
        ]
        left_eye = QPolygonF([QPointF(x, y) for x, y in left_eye_points])
        painter.drawPolygon(left_eye)
        
        # Right eye
        right_eye_points = [
            (cx + 9*scale, cy - 6*scale),
            (cx + 5*scale, cy - 8*scale),
            (cx + 4*scale, cy - 4*scale),
            (cx + 7*scale, cy - 2*scale),
        ]
        right_eye = QPolygonF([QPointF(x, y) for x, y in right_eye_points])
        painter.drawPolygon(right_eye)
        
        # Red glow
        painter.setBrush(QBrush(QColor(255, 0, 0, 120)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 7*scale), int(cy - 6*scale), int(3*scale), int(3*scale))
        painter.drawEllipse(int(cx + 4*scale), int(cy - 6*scale), int(3*scale), int(3*scale))
        
        # Nose
        painter.setBrush(QBrush(QColor(10, 10, 10)))
        painter.setPen(QPen(QColor(30, 30, 30), 1*scale))
        nose_points = [
            (cx, cy - 2*scale),
            (cx - 3*scale, cy + 3*scale),
            (cx + 3*scale, cy + 3*scale)
        ]
        nose_polygon = QPolygonF([QPointF(x, y) for x, y in nose_points])
        painter.drawPolygon(nose_polygon)
        
        # Teeth (individual, realistic)
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.setPen(QPen(QColor(60, 60, 60), 0.5*scale))
        teeth_y = cy + 7*scale
        for i in range(4):
            x = cx - 6*scale + i * 4*scale
            painter.drawRoundedRect(int(x), int(teeth_y), 
                                  int(2*scale), int(4*scale), 1, 1)


def get_window_icon_pixmap(size=64):
    """Get skull logo as QPixmap for window icon"""
    if not _HAS_QT:
        return None
    widget = CompactSkullIcon(size)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    widget.render(pixmap)
    return pixmap


# Professional color scheme for the application
try:
    from src.ui.reloading_theme import ReloadingTheme
except Exception:
    # Fallback minimal theme if canonical import fails (keeps app usable)
    class ReloadingTheme:
        @staticmethod
        def get_stylesheet():
            return """
            QWidget { background-color: #23242b; color: #e0e0e0; }
            """


if __name__ == '__main__':
    """Test the logo (only runs if Qt is available)"""
    if not _HAS_QT:
        logging.warning("Qt not available — skipping logo demo")
    else:
        import sys
        from PyQt6.QtWidgets import QApplication, QVBoxLayout

        app = QApplication(sys.argv)

        # Create test window
        window = QWidget()
        window.setWindowTitle("Hjemmelading Logo Test")
        window.resize(800, 400)
        try:
            window.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            logging.exception("Failed to apply ReloadingTheme stylesheet")

        layout = QVBoxLayout()

        # Large logo with text
        large_logo = SkullLogo(size=128, show_text=True)
        layout.addWidget(large_logo)

        # Icons row
        icons_layout = QHBoxLayout()
        for size in [64, 48, 32, 24, 16]:
            icon = CompactSkullIcon(size)
            icons_layout.addWidget(icon)
        layout.addLayout(icons_layout)

        # Info label
        info = QLabel("Professional skull-themed logo for serious reloaders")
        try:
            info.setStyleSheet(f"color: {ReloadingTheme.TEXT_SECONDARY}; padding: 20px;")
        except Exception:
            pass
        layout.addWidget(info)

        window.setLayout(layout)
        window.show()

        sys.exit(app.exec())
