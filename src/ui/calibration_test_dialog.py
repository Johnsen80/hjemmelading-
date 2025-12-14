from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.modules.calibration_test import ChronoData
from src.modules.image_analysis import analyze_group_image
from src.ui.calibration_analysis_dialog import CalibrationAnalysisDialog
from src.ui.help_modal import HelpModal
from src.ui.image_calibration_dialog import ImageCalibrationDialog
from src.ui.reloading_theme import ReloadingTheme


class CalibrationTestDialog(QDialog):
    """Dialog to enter up to 3 calibration loads with chronograph and image paths.

    Optionally accepts a `profile` dict so the dialog can compute turret click
    recommendations when image calibration data is available.
    """

    def __init__(
        self,
        parent=None,
        existing: Optional[Dict[str, Any]] = None,
        profile: Optional[Dict[str, Any]] = None,
        persist_callback=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Calibration Test")
        self.resize(720, 480)
        # apply central stylesheet and objectName for selectors
        try:
            self.setObjectName("calibrationTestDialog")
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass
        self._data = existing.copy() if existing else {}
        self._profile = profile
        self._persist_callback = persist_callback
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.load_sections: List[Dict[str, Any]] = []
        for i in range(3):
            sec: Dict[str, Any] = {}
            form = QFormLayout()
            sec["bullet"] = QLineEdit(self._data.get("bullet", ""))
            form.addRow(f"Load {i+1} Bullet:", sec["bullet"])
            sec["powder"] = QLineEdit(self._data.get("powder", ""))
            form.addRow("Powder:", sec["powder"])
            sec["seating"] = QLineEdit(str(self._data.get("seating_depth_col_mm", "")))
            form.addRow("Seating depth (mm):", sec["seating"])
            velocities_widget = QTextEdit(self._data.get("velocities", ""))
            velocities_widget.setPlaceholderText(
                "Enter velocities (m/s) separated by commas or newlines, or import CSV"
            )
            form.addRow("Velocities (comma/newline separated):", velocities_widget)
            # parsed summary label and parse button
            sec["vel_summary"] = QLabel("")
            parse_btn = QPushButton("Parse velocities")

            def _parse_and_show():
                text = velocities_widget.toPlainText().strip()
                vals = []
                for token in text.replace(";", ",").replace("\n", ",").split(","):
                    t = token.strip()
                    if not t:
                        continue
                    try:
                        vals.append(float(t))
                    except Exception:
                        pass
                chrono = ChronoData(vals)
                stats = chrono.stats()
                if stats.get("n", 0) > 0:
                    sec["vel_summary"].setText(
                        f"N={stats['n']} mean={stats['mean']:.1f} ES={stats['es']:.1f} SD={stats['sd']:.2f}"
                    )
                else:
                    sec["vel_summary"].setText("No velocities parsed")

            parse_btn.clicked.connect(_parse_and_show)
            form.addRow(parse_btn, sec["vel_summary"])

            btn_row = QHBoxLayout()
            import_btn = QPushButton("Import chrono CSV")
            import_btn.clicked.connect(self._make_import_handler(velocities_widget))
            btn_row.addWidget(import_btn)
            img_btn = QPushButton("Upload group image")
            img_btn.clicked.connect(self._make_image_handler(sec))
            btn_row.addWidget(img_btn)
            calib_btn = QPushButton("Calibrate image (DPI)")
            calib_btn.clicked.connect(self._make_calibrate_handler(sec))
            btn_row.addWidget(calib_btn)
            # image preview
            sec["img_label"] = QLabel()
            sec["img_label"].setFixedSize(160, 120)
            # objectName used to apply themed image preview style
            sec["img_label"].setObjectName("imagePreview")
            form.addRow("Preview:", sec["img_label"])
            form.addRow(btn_row)

            sec["velocities"] = velocities_widget

            layout.addLayout(form)
            self.load_sections.append(sec)

        self.notes = QTextEdit(self._data.get("notes", ""))
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self.notes)

        action_row = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self._on_analyze)
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(
            lambda: HelpModal(self, title="Calibration Help").exec()
        )
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        action_row.addStretch()
        action_row.addWidget(self.analyze_btn)
        action_row.addWidget(help_btn)
        action_row.addWidget(self.cancel_btn)
        layout.addLayout(action_row)

    def _make_import_handler(self, velocities_widget: QTextEdit):
        def handler() -> None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Open chrono CSV", "", "CSV Files (*.csv);;All Files (*)"
            )
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                velocities_widget.setPlainText(text)
            except Exception as e:
                QMessageBox.warning(self, "Import failed", str(e))

        return handler

    def _make_image_handler(self, sec: Dict[str, Any]):
        def handler() -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open group image",
                "",
                "Images (*.png *.jpg *.jpeg);;All Files (*)",
            )
            if not path:
                return
            sec["group_image_path"] = path
            # attempt to load and auto-orient image using Pillow if available
            try:
                from PIL import ExifTags
                from PIL import Image as PILImage

                img = PILImage.open(path)
                try:
                    orientation = None
                    for k, v in ExifTags.TAGS.items():
                        if v == "Orientation":
                            orientation = k
                            break
                    exif = getattr(img, "_getexif", lambda: None)()
                    final_img: Any = img
                    if exif is not None and orientation is not None:
                        orient = exif.get(orientation)
                        if orient == 3:
                            final_img = img.rotate(180, expand=True)
                        elif orient == 6:
                            final_img = img.rotate(270, expand=True)
                        elif orient == 8:
                            final_img = img.rotate(90, expand=True)
                    else:
                        final_img = img
                except Exception:
                    pass
                # convert to QPixmap via bytes
                from io import BytesIO

                buf = BytesIO()
                final_img.save(buf, format="PNG")
                buf.seek(0)
                pix = QPixmap()
                pix.loadFromData(buf.read())
            except Exception:
                # fallback to QPixmap load
                pix = QPixmap(path)
            lbl = sec["img_label"]
            sec["img_label"].setPixmap(
                pix.scaled(
                    lbl.width(), lbl.height(), Qt.AspectRatioMode.KeepAspectRatio
                )
            )
            QMessageBox.information(self, "Image selected", Path(path).name)

        return handler

    def _make_calibrate_handler(self, sec: Dict[str, Any]):
        def handler() -> None:
            img = sec.get("group_image_path")
            if not img:
                QMessageBox.information(self, "No image", "Upload an image first.")
                return
            dlg = ImageCalibrationDialog(img, parent=self)
            if dlg.exec():
                mm_per_px = dlg.get_mm_per_pixel()
                if mm_per_px:
                    sec["mm_per_pixel"] = mm_per_px
                    QMessageBox.information(
                        self, "Calibrated", f"Scale set: {mm_per_px:.6f} mm/pixel"
                    )

        return handler

    def gather(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"loads": []}
        for sec in self.load_sections:
            velocities_text = sec["velocities"].toPlainText().strip()
            vals = []
            for token in (
                velocities_text.replace(";", ",").replace("\n", ",").split(",")
            ):
                t = token.strip()
                if not t:
                    continue
                try:
                    vals.append(float(t))
                except Exception:
                    pass
            load = {
                "bullet": sec["bullet"].text().strip(),
                "powder": sec["powder"].text().strip(),
                "seating_depth_col_mm": (
                    float(sec["seating"].text())
                    if sec["seating"].text().strip()
                    else None
                ),
                "velocities": vals,
                "group_image_path": sec.get("group_image_path"),
            }
            # only include loads that have some data
            if load["bullet"] or load["powder"] or vals or load["group_image_path"]:
                result["loads"].append(load)
        result["notes"] = self.notes.toPlainText().strip()
        return result

    def _on_analyze(self) -> None:
        """Gather input, run chrono and image analysis, open results dialog.

        If the user chooses to Save in the analysis dialog, accept() so the
        caller can persist the gathered data.
        """
        data = self.gather()
        results: List[Dict[str, Any]] = []
        for load in data.get("loads", []):
            velocities = load.get("velocities", [])
            chrono = ChronoData(velocities)
            chrono_stats = chrono.stats()
            img_path = load.get("group_image_path")
            img_res = None
            if img_path:
                try:
                    img_res = analyze_group_image(img_path)
                except Exception as exc:  # pragma: no cover - defensive
                    img_res = {"error": str(exc)}
            results.append({"chrono_stats": chrono_stats, "image_analysis": img_res})

        dlg = CalibrationAnalysisDialog(
            results=results,
            parent=self,
            profile=self._profile,
            persist_callback=self._persist_callback,
        )
        # If we have profile and at least one image with mm_per_pixel, attempt to
        # compute turret clicks suggestion and attach to the results for display.
        try:
            if self._profile:
                optics = self._profile.get("optics", [])
                active_optic = optics[0] if optics else None
            else:
                active_optic = None
            # augment results with click suggestions where possible
            for i, res in enumerate(results):
                img_analysis = res.get("image_analysis") or {}
                # find corresponding sec to get mm_per_pixel and image path
                sec = self.load_sections[i]
                mm_per_px = sec.get("mm_per_pixel")
                img_path = sec.get("group_image_path")
                if (
                    img_analysis
                    and img_analysis.get("center")
                    and mm_per_px
                    and img_path
                    and active_optic
                ):
                    try:
                        from PyQt6.QtGui import QPixmap

                        pix = QPixmap(img_path)
                        img_w = pix.width()
                        img_h = pix.height()
                        center = img_analysis.get("center")
                        if not center or not (
                            hasattr(center, "__iter__") and len(center) >= 2
                        ):
                            continue
                        cx, cy = center[0], center[1]
                        # compute pixel offset from image center (positive y means down)
                        dx_px = cx - (img_w / 2.0)
                        dy_px = cy - (img_h / 2.0)
                        # convert to meters (mm_per_px -> mm -> m)
                        dx_m = (dx_px * mm_per_px) / 1000.0
                        dy_m = (dy_px * mm_per_px) / 1000.0
                        # choose vertical offset for elevation correction (negative dy_m -> target above center)
                        # compute using optic settings
                        from src.utils.optics import compute_clicks_for_offset

                        zero_distance = None
                        try:
                            zero_distance = (
                                float(active_optic.get("zero_distance_m"))
                                if active_optic.get("zero_distance_m")
                                else None
                            )
                        except Exception:
                            zero_distance = None
                        use_range = zero_distance if zero_distance else 100.0
                        # vertical correction: negate dy_m because pixel y grows downward
                        v_res = compute_clicks_for_offset(
                            -dy_m,
                            use_range,
                            unit=active_optic.get("turret_units", "mil"),
                            click_value=float(active_optic.get("click_value") or 0.1),
                            clicks_per_rev=int(active_optic.get("clicks_per_rev") or 0),
                        )
                        # horizontal correction using dx_m
                        h_res = compute_clicks_for_offset(
                            dx_m,
                            use_range,
                            unit=active_optic.get("turret_units", "mil"),
                            click_value=float(active_optic.get("click_value") or 0.1),
                            clicks_per_rev=int(active_optic.get("clicks_per_rev") or 0),
                        )
                        res["optics_suggestion"] = {
                            "vertical": v_res,
                            "horizontal": h_res,
                        }
                    except Exception:
                        pass
        except Exception:
            pass

        if dlg.exec() and getattr(dlg, "saved", False):
            # user elected to save the test
            self.accept()
