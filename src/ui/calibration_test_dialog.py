from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.modules.calibration_test import ChronoData
from src.modules.image_analysis import analyze_group_image
from src.ui.calibration_analysis_dialog import CalibrationAnalysisDialog
from src.ui.help_modal import HelpModal
from src.ui.image_calibration_dialog import ImageCalibrationDialog
from src.ui.reloading_theme import ReloadingTheme
from src.utils.i18n import tr

from ..database.database import get_database
from ..qt_compat import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPixmap,
    QPushButton,
    Qt,
    QTextEdit,
    QVBoxLayout,
)


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
        self.setWindowTitle(tr("calib_test_title"))
        self.resize(720, 480)
        # apply central stylesheet and objectName for selectors
        try:
            from .theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            try:
                self.setObjectName("calibrationTestDialog")
                self.setStyleSheet(ReloadingTheme.get_stylesheet())
            except Exception:
                pass
        self._data = existing.copy() if existing else {}
        self._profile = profile
        self._persist_callback = persist_callback
        self._powders_db: list = []
        self._bullets_db: list = []
        try:
            _db = getattr(parent, "db", None) or get_database()
            self._powders_db = _db.execute_query(
                "SELECT id, name, manufacturer FROM powder ORDER BY manufacturer, name"
            )
            self._bullets_db = _db.execute_query(
                "SELECT id, name, manufacturer, weight_grains, caliber"
                " FROM bullets ORDER BY manufacturer, weight_grains, name"
            )
        except Exception:
            pass
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        intro = QLabel(tr("calib_test_intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        session_form = QFormLayout()
        self.distance_edit = QLineEdit(str(self._data.get("distance_m", "")))
        self.distance_edit.setPlaceholderText(tr("calib_test_example_100"))
        session_form.addRow(tr("calib_test_distance_m"), self.distance_edit)
        self.temperature_edit = QLineEdit(str(self._data.get("temperature_c", "")))
        self.temperature_edit.setPlaceholderText(tr("calib_test_example_12"))
        session_form.addRow(tr("calib_test_temperature_c"), self.temperature_edit)
        layout.addLayout(session_form)

        self.load_sections: List[Dict[str, Any]] = []
        for i in range(3):
            sec: Dict[str, Any] = {}
            form = QFormLayout()
            defaults = self._get_load_defaults(i)
            bullet_combo = QComboBox()
            bullet_combo.setEditable(True)
            bullet_combo.addItem("— velg kule —", None)
            for _b in self._bullets_db:
                _lbl = _b["name"]
                if _b.get("weight_grains"):
                    _lbl += f" {float(_b['weight_grains']):.0f}gr"
                if _b.get("caliber"):
                    _lbl += f" ({_b['caliber']})"
                bullet_combo.addItem(_lbl, _b["id"])
            _exist_bullet = defaults.get("bullet", "")
            if _exist_bullet:
                bullet_combo.setCurrentText(_exist_bullet)
            sec["bullet"] = bullet_combo
            form.addRow(tr("calib_test_load_bullet", index=i + 1), bullet_combo)

            sec["bullet_weight"] = QLineEdit(str(defaults.get("bullet_weight_gr", "")))
            sec["bullet_weight"].setPlaceholderText(tr("calib_test_example_140"))
            form.addRow(tr("calib_test_bullet_weight"), sec["bullet_weight"])

            def _make_bullet_handler(bcombo, bweight_edit, bullets):
                def _on_bullet_changed(idx):
                    bid = bcombo.itemData(idx)
                    if bid is None:
                        return
                    for _b in bullets:
                        if _b["id"] == bid and _b.get("weight_grains"):
                            bweight_edit.setText(str(float(_b["weight_grains"])))
                            break

                return _on_bullet_changed

            bullet_combo.currentIndexChanged.connect(
                _make_bullet_handler(
                    bullet_combo, sec["bullet_weight"], self._bullets_db
                )
            )

            powder_combo = QComboBox()
            powder_combo.setEditable(True)
            powder_combo.addItem("— velg krutt —", None)
            for _p in self._powders_db:
                _lbl = _p["name"]
                if _p.get("manufacturer"):
                    _lbl += f" ({_p['manufacturer']})"
                powder_combo.addItem(_lbl, _p["id"])
            _exist_powder = defaults.get("powder", "")
            if _exist_powder:
                powder_combo.setCurrentText(_exist_powder)
            sec["powder"] = powder_combo
            form.addRow(tr("calib_test_powder"), powder_combo)
            sec["charge"] = QLineEdit(str(defaults.get("charge_weight_gr", "")))
            sec["charge"].setPlaceholderText(tr("calib_test_example_42_3"))
            form.addRow(tr("calib_test_charge_weight"), sec["charge"])
            sec["seating"] = QLineEdit(str(defaults.get("seating_depth_col_mm", "")))
            form.addRow(tr("calib_test_seating_depth"), sec["seating"])
            sec["cbto"] = QLineEdit(str(defaults.get("cbto_mm", "")))
            sec["cbto"].setPlaceholderText(tr("calib_test_example_56_20"))
            form.addRow(tr("calib_test_cbto"), sec["cbto"])
            sec["coal"] = QLineEdit(str(defaults.get("coal_mm", "")))
            sec["coal"].setPlaceholderText(tr("calib_test_example_71_10"))
            form.addRow(tr("calib_test_coal"), sec["coal"])
            sec["neck_tension"] = QLineEdit(str(defaults.get("neck_tension_mm", "")))
            sec["neck_tension"].setPlaceholderText(tr("calib_test_example_0_05"))
            form.addRow(tr("calib_test_neck_tension"), sec["neck_tension"])
            sec["group_size"] = QLineEdit(str(defaults.get("group_size_mm", "")))
            sec["group_size"].setPlaceholderText(tr("calib_test_example_18_5"))
            form.addRow(tr("calib_test_group_size"), sec["group_size"])
            velocities_widget = QTextEdit(
                self._format_velocities(defaults.get("velocities", ""))
            )
            velocities_widget.setPlaceholderText(
                tr("calib_test_velocities_placeholder")
            )
            form.addRow(tr("calib_test_velocities"), velocities_widget)
            # parsed summary label and parse button
            sec["vel_summary"] = QLabel("")
            parse_btn = QPushButton(tr("calib_test_parse_velocities"))

            def _parse_and_show():
                vals = self._parse_velocities(velocities_widget.toPlainText().strip())
                chrono = ChronoData(vals)
                stats = chrono.stats()
                if stats.get("n", 0) > 0:
                    sec["vel_summary"].setText(
                        tr(
                            "calib_test_velocity_summary",
                            n=stats["n"],
                            mean=f"{stats['mean']:.1f}",
                            es=f"{stats['es']:.1f}",
                            sd=f"{stats['sd']:.2f}",
                        )
                    )
                else:
                    sec["vel_summary"].setText(tr("calib_test_no_velocities_parsed"))

            parse_btn.clicked.connect(_parse_and_show)
            form.addRow(parse_btn, sec["vel_summary"])

            btn_row = QHBoxLayout()
            import_btn = QPushButton(tr("calib_test_import_chrono_csv"))
            import_btn.clicked.connect(self._make_import_handler(velocities_widget))
            btn_row.addWidget(import_btn)
            img_btn = QPushButton(tr("calib_test_upload_group_image"))
            img_btn.clicked.connect(self._make_image_handler(sec))
            btn_row.addWidget(img_btn)
            calib_btn = QPushButton(tr("calib_test_calibrate_image"))
            calib_btn.clicked.connect(self._make_calibrate_handler(sec))
            btn_row.addWidget(calib_btn)
            # image preview
            sec["img_label"] = QLabel()
            sec["img_label"].setFixedSize(160, 120)
            # objectName used to apply themed image preview style
            sec["img_label"].setObjectName("imagePreview")
            form.addRow(tr("calib_test_preview"), sec["img_label"])
            form.addRow(btn_row)

            sec["velocities"] = velocities_widget

            layout.addLayout(form)
            self.load_sections.append(sec)

        self.notes = QTextEdit(self._data.get("notes", ""))
        layout.addWidget(QLabel(tr("ammo_profiles_notes")))
        layout.addWidget(self.notes)

        action_row = QHBoxLayout()
        self.analyze_btn = QPushButton(tr("calib_test_analyze"))
        self.analyze_btn.clicked.connect(self._on_analyze)
        help_btn = QPushButton(tr("calib_test_help"))
        help_btn.clicked.connect(
            lambda: HelpModal(self, title=tr("calib_test_help_title")).exec()
        )
        self.cancel_btn = QPushButton(tr("rifle_optics_cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        action_row.addStretch()
        action_row.addWidget(self.analyze_btn)
        action_row.addWidget(help_btn)
        action_row.addWidget(self.cancel_btn)
        layout.addLayout(action_row)

    def _make_import_handler(self, velocities_widget: QTextEdit):
        def handler() -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("calib_test_open_chrono_csv"),
                "",
                tr("calib_test_csv_file_filter"),
            )
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
                velocities_widget.setPlainText(text)
            except Exception as e:
                QMessageBox.warning(self, tr("chrono_import_failed"), str(e))

        return handler

    def _make_image_handler(self, sec: Dict[str, Any]):
        def handler() -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("target_upload_button"),
                "",
                tr("calib_test_image_file_filter"),
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
            QMessageBox.information(
                self, tr("calib_test_image_selected"), Path(path).name
            )

        return handler

    def _make_calibrate_handler(self, sec: Dict[str, Any]):
        def handler() -> None:
            img = sec.get("group_image_path")
            if not img:
                QMessageBox.information(
                    self, tr("target_no_image_title"), tr("target_no_image_message")
                )
                return
            dlg = ImageCalibrationDialog(img, parent=self)
            if dlg.exec():
                mm_per_px = dlg.get_mm_per_pixel()
                if mm_per_px:
                    sec["mm_per_pixel"] = mm_per_px
                    QMessageBox.information(
                        self,
                        tr("calib_test_calibrated"),
                        tr("calib_test_scale_set", value=mm_per_px),
                    )

        return handler

    def gather(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"loads": []}
        result["distance_m"] = self._parse_float(self.distance_edit.text())
        result["temperature_c"] = self._parse_float(self.temperature_edit.text())
        for sec in self.load_sections:
            vals = self._parse_velocities(sec["velocities"].toPlainText().strip())
            chrono = ChronoData(vals)
            chrono_stats = chrono.stats()
            load = {
                "bullet": sec["bullet"].currentText().strip(),
                "bullet_id": sec["bullet"].currentData(),
                "bullet_weight_gr": self._parse_float(sec["bullet_weight"].text()),
                "powder": sec["powder"].currentText().strip(),
                "powder_id": sec["powder"].currentData(),
                "charge_weight_gr": self._parse_float(sec["charge"].text()),
                "seating_depth_col_mm": (self._parse_float(sec["seating"].text())),
                "cbto_mm": self._parse_float(sec["cbto"].text()),
                "coal_mm": self._parse_float(sec["coal"].text()),
                "neck_tension_mm": self._parse_float(sec["neck_tension"].text()),
                "group_size_mm": self._parse_float(sec["group_size"].text()),
                "velocities": vals,
                "velocity_avg": chrono_stats.get("mean"),
                "velocity_es": chrono_stats.get("es"),
                "velocity_sd": chrono_stats.get("sd"),
                "velocity_count": chrono_stats.get("n"),
                "group_image_path": sec.get("group_image_path"),
            }
            # only include loads that have some data
            if (
                (load["bullet"] and load["bullet"] != "— velg kule —")
                or (load["powder"] and load["powder"] != "— velg krutt —")
                or load["charge_weight_gr"] is not None
                or load["cbto_mm"] is not None
                or load["coal_mm"] is not None
                or load["group_size_mm"] is not None
                or vals
                or load["group_image_path"]
            ):
                result["loads"].append(load)
        result["notes"] = self.notes.toPlainText().strip()
        return result

    def _get_load_defaults(self, index: int) -> Dict[str, Any]:
        loads = self._data.get("loads")
        if (
            isinstance(loads, list)
            and 0 <= index < len(loads)
            and isinstance(loads[index], dict)
        ):
            return loads[index]
        return self._data

    def _parse_float(self, value: str) -> Optional[float]:
        text = str(value).strip()
        if not text:
            return None
        try:
            return float(text.replace(",", "."))
        except Exception:
            return None

    def _parse_velocities(self, text: str) -> List[float]:
        vals: List[float] = []
        for token in text.replace(";", ",").replace("\n", ",").split(","):
            t = token.strip()
            if not t:
                continue
            try:
                vals.append(float(t))
            except Exception:
                pass
        return vals

    def _format_velocities(self, value: Any) -> str:
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value or "")

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
            try:
                sec = self.load_sections[len(results)]
                mm_per_px = sec.get("mm_per_pixel")
                if (
                    img_res
                    and isinstance(img_res, dict)
                    and img_res.get("pixel_diameter") is not None
                    and mm_per_px
                ):
                    img_res["mm_diameter"] = float(img_res["pixel_diameter"]) * float(
                        mm_per_px
                    )
                    if not load.get("group_size_mm"):
                        load["group_size_mm"] = img_res["mm_diameter"]
                        sec["group_size"].setText(f"{img_res['mm_diameter']:.2f}")
            except Exception:
                pass
            load_meta = dict(load)
            load_meta["distance_m"] = data.get("distance_m")
            load_meta["temperature_c"] = data.get("temperature_c")
            results.append(
                {
                    "chrono_stats": chrono_stats,
                    "image_analysis": img_res,
                    "image_path": img_path,
                    "load_data": load_meta,
                }
            )

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
