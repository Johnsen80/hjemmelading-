from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.ui.reloading_theme import ReloadingTheme


class DisabledFeatureCard(QWidget):
    """A small, reusable card widget that explains why a feature is disabled
    and provides an action to learn how to enable it.
    """

    def __init__(self, missing: list[str], parent=None):
        super().__init__(parent)
        # Use the banner style from the central theme and set an objectName
        # so stylesheet selectors can target this widget.
        self.setObjectName("banner")
        try:
            self.setStyleSheet(ReloadingTheme.get_banner_style())
        except Exception:
            pass
        layout = QHBoxLayout()
        self.setLayout(layout)
        txt = ", ".join(missing)
        lbl = QLabel(f"Optional packages missing: {txt}. Some features are disabled.")
        lbl.setWordWrap(True)
        btn = QPushButton("How to install")
        btn.setObjectName("bannerAction")
        # Try to add an info icon if available
        try:
            from src.ui.icon_registry import get_icon

            ic = get_icon("info")
            if ic:
                btn.setIcon(ic)
        except Exception:
            pass

        def _open_instructions():
            try:
                import os

                from PyQt6.QtCore import QUrl
                from PyQt6.QtGui import QDesktopServices

                root = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..")
                )
                md = os.path.join(root, "OPTIONAL_DEPENDENCIES.md")
                QDesktopServices.openUrl(QUrl.fromLocalFile(md))
            except Exception:
                try:
                    from PyQt6.QtWidgets import QMessageBox

                    QMessageBox.information(
                        self, "Info", "See OPTIONAL_DEPENDENCIES.md in project root."
                    )
                except Exception:
                    pass

        btn.clicked.connect(_open_instructions)
        layout.addWidget(lbl)
        layout.addWidget(btn)
        layout.setStretch(0, 3)
        layout.setStretch(1, 1)
