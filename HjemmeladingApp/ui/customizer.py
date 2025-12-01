from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QColorDialog,
    QFileDialog,
)
from PyQt6.QtGui import QPalette, QColor
import logging
from HjemmeladingApp.utils.backgrounds import get_background_preview
from HjemmeladingApp.utils.safe_logger import append_exception

logger = logging.getLogger(__name__)
try:
    from PyQt6.QtGui import QPixmap

    _HAS_QPIXMAP = True
except Exception:
    QPixmap = None
    _HAS_QPIXMAP = False


class AppearanceCustomizer(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        # Build UI defensively so failures in optional image backends don't crash the app
        try:
            self.setWindowTitle("Tilpass utseende")
            self.setMinimumSize(400, 300)
            layout = QVBoxLayout()
            self.bg_label = QLabel("Velg bakgrunnsbilde:")
            self.bg_btn = QPushButton("Last opp bilde")
            self.bg_btn.clicked.connect(self.choose_bg)
            self.color_label = QLabel("Velg bakgrunnsfarge:")
            self.color_btn = QPushButton("Velg farge")
            self.color_btn.clicked.connect(self.choose_color)
            layout.addWidget(self.bg_label)
            layout.addWidget(self.bg_btn)
            layout.addWidget(self.color_label)
            layout.addWidget(self.color_btn)
            self.setLayout(layout)
        except Exception as _init_err:
            try:
                append_exception(
                    f"AppearanceCustomizer init failed: {_init_err}", _init_err
                )
            except Exception:
                pass
            logger.exception("AppearanceCustomizer init failed")
            # Fallback minimal UI
            fallback = QVBoxLayout()
            fallback.addWidget(QLabel("Customizer unavailable."))
            close_btn = QPushButton("Lukk")
            close_btn.clicked.connect(self.close)
            fallback.addWidget(close_btn)
            self.setLayout(fallback)

    def choose_bg(self):
        try:
            file, _ = QFileDialog.getOpenFileName(
                self, "Velg bilde", "", "Bilder (*.png *.jpg *.jpeg *.bmp)"
            )
            if not file:
                return
            # Try to get a safe preview pixmap (may return None)
            pixmap = None
            try:
                pixmap = get_background_preview(file)
            except Exception as _gerr:
                try:
                    append_exception(f"get_background_preview failed: {_gerr}", _gerr)
                except Exception:
                    pass
            if pixmap is None and _HAS_QPIXMAP:
                try:
                    pixmap = QPixmap(file)
                except Exception:
                    pixmap = None

            try:
                palette = self.main_window.palette()
                if pixmap is not None and _HAS_QPIXMAP:
                    palette.setBrush(QPalette.ColorRole.Window, pixmap)
                else:
                    # Fallback: set a neutral background color if image fails
                    palette.setColor(QPalette.ColorRole.Window, QColor("#f0f0f0"))
                self.main_window.setPalette(palette)
                self.main_window.setAutoFillBackground(True)
            except Exception as _pal_err:
                try:
                    append_exception(
                        f"Applying background failed: {_pal_err}", _pal_err
                    )
                except Exception:
                    pass
                logger.exception("Applying background failed")
        except Exception as _err:
            try:
                append_exception(f"choose_bg exception: {_err}", _err)
            except Exception:
                pass
            logger.exception("choose_bg exception")

    def choose_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                try:
                    palette = self.main_window.palette()
                    palette.setColor(QPalette.ColorRole.Window, color)
                    self.main_window.setPalette(palette)
                    self.main_window.setAutoFillBackground(True)
                except Exception as _pal_err:
                    try:
                        append_exception(f"Applying color failed: {_pal_err}", _pal_err)
                    except Exception:
                        pass
                    logger.exception("Applying color failed")
        except Exception as _err:
            try:
                append_exception(f"choose_color exception: {_err}", _err)
            except Exception:
                pass
            logger.exception("choose_color exception")
