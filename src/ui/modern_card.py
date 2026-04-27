"""Modern Viking Card widget."""

from src.qt_compat import QFont, QPixmap, Qt, QtWidgets

QLabel = QtWidgets.QLabel
QVBoxLayout = QtWidgets.QVBoxLayout
QWidget = QtWidgets.QWidget

from src.ui.reloading_theme import ReloadingTheme


class ModernCard(QWidget):
    def __init__(self, title, subtitle, icon_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName("modernCard")
        try:
            from src.ui.theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            try:
                self.setStyleSheet(ReloadingTheme.get_card_style())
            except Exception:
                self.setStyleSheet(
                    "background-color:#23242b; border-radius:12px; padding:12px;"
                )
        self.setMinimumWidth(320)
        self.setMaximumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        # Icon
        if icon_path:
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(
                pixmap.scaled(
                    48,
                    48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(icon_label)
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label)
        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("cardSubtitle")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(subtitle_label)
        layout.addStretch()
