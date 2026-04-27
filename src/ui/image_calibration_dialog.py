from __future__ import annotations

from typing import Optional

from src.qt_compat import QMouseEvent, QPixmap, QPoint, Qt, QtWidgets
from src.utils.i18n import tr

QDialog = QtWidgets.QDialog
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QMessageBox = QtWidgets.QMessageBox
QPushButton = QtWidgets.QPushButton
QVBoxLayout = QtWidgets.QVBoxLayout

from src.ui.reloading_theme import ReloadingTheme


class ClickableImageLabel(QLabel):
    def __init__(self, pixmap=None, parent=None):
        super().__init__(parent)
        if pixmap:
            self.setPixmap(pixmap)
        self.points: list[QPoint] = []

    def mousePressEvent(self, ev: QMouseEvent) -> None:  # type: ignore[override]
        if ev.button() == Qt.MouseButton.LeftButton:
            pos = ev.pos()
            self.points.append(pos)
            # draw small marker by updating
            self.update()


class ImageCalibrationDialog(QDialog):
    """Dialog to let user click two points on image and enter the real-world distance.

    Returns mm_per_pixel via `result()` when accepted.
    """

    def __init__(self, image_path: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("image_calib_title"))
        self.setObjectName("imageCalibDialog")
        try:
            from .theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            try:
                self.setStyleSheet(ReloadingTheme.get_stylesheet())
            except Exception:
                pass
        self.resize(800, 600)
        self.image_path = image_path
        self.mm_per_pixel: Optional[float] = None
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Instruksjonstekst
        instructions = QLabel(tr("image_calib_instructions"))
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #2a5d8f; font-size: 11pt;")
        layout.addWidget(instructions)

        pix = QPixmap(self.image_path)
        self.img_label = ClickableImageLabel(pix)
        self.img_label.setScaledContents(True)
        layout.addWidget(self.img_label)

        row = QHBoxLayout()
        self.ok_btn = QPushButton(tr("image_calib_set_distance"))
        self.ok_btn.setObjectName("imageCalibSetBtn")
        self.ok_btn.clicked.connect(self._on_set_distance)
        self.cancel_btn = QPushButton(tr("rifle_optics_cancel"))
        self.cancel_btn.setObjectName("imageCalibCancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        row.addStretch()
        row.addWidget(self.ok_btn)
        row.addWidget(self.cancel_btn)
        layout.addLayout(row)

    def _on_set_distance(self) -> None:
        pts = self.img_label.points
        if len(pts) < 2:
            QMessageBox.warning(
                self,
                tr("image_calib_need_two_points_title"),
                tr("image_calib_need_two_points_message"),
            )
            return
        p1 = pts[-2]
        p2 = pts[-1]
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        pixel_dist = (dx * dx + dy * dy) ** 0.5
        if pixel_dist <= 0:
            QMessageBox.warning(
                self,
                tr("image_calib_invalid_points_title"),
                tr("image_calib_invalid_points_message"),
            )
            return
        # ask user for real-world mm via input dialog
        QInputDialog = QtWidgets.QInputDialog

        txt, ok = QInputDialog.getText(
            self,
            tr("image_calib_distance_mm_title"),
            tr("image_calib_distance_mm_message"),
        )
        if not ok:
            return
        try:
            mm = float(txt)
        except Exception:
            QMessageBox.warning(
                self,
                tr("image_calib_invalid_value_title"),
                tr("image_calib_invalid_value_message"),
            )
            return
        self.mm_per_pixel = mm / pixel_dist
        self.accept()

    def get_mm_per_pixel(self) -> Optional[float]:
        return self.mm_per_pixel
