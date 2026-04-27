from __future__ import annotations

from typing import Any, Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.utils.i18n import tr

# pathlib.Path not required here


class CalibrationAnalysisDialog(QDialog):
    """Show analysis results for a calibration test.

    Expects `results` to be a list of dicts for each load containing chrono
    stats and optional image-analysis results. If a `profile` dict is
    provided the dialog can apply suggested optic adjustments into
    `profile['optics_history']`.
    """

    def __init__(
        self,
        results: List[Dict[str, Any]],
        parent=None,
        profile: dict | None = None,
        persist_callback=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("calib_analysis_title"))
        self.resize(720, 480)
        try:
            from .theme import apply_modern_theme

            apply_modern_theme(self)
        except Exception:
            pass
        self.results = results
        self._profile = profile
        self._persist_callback = persist_callback
        self.saved = False
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        for i, res in enumerate(self.results, start=1):
            txt = QTextEdit()
            txt.setReadOnly(True)
            lines: List[str] = [tr("calib_analysis_load", index=i)]
            load_meta = res.get("load_data") or {}
            if load_meta:
                meta_parts: List[str] = []
                if load_meta.get("bullet"):
                    bullet = str(load_meta.get("bullet"))
                    if load_meta.get("bullet_weight_gr") is not None:
                        bullet += f" {float(load_meta.get('bullet_weight_gr')):.1f} gr"
                    meta_parts.append(tr("calib_analysis_bullet", value=bullet))
                if load_meta.get("powder"):
                    powder = str(load_meta.get("powder"))
                    if load_meta.get("powder_manufacturer"):
                        powder = f"{load_meta.get('powder_manufacturer')} {powder}"
                    if load_meta.get("charge_weight_gr") is not None:
                        powder += f" {float(load_meta.get('charge_weight_gr')):.2f} gr"
                    meta_parts.append(tr("calib_analysis_powder", value=powder))
                powder_traits: List[str] = []
                if load_meta.get("powder_type"):
                    powder_traits.append(str(load_meta.get("powder_type")))
                if load_meta.get("powder_burn_rate_label"):
                    powder_traits.append(
                        f"burn rate: {load_meta.get('powder_burn_rate_label')}"
                    )
                if load_meta.get("powder_burn_rate_position") is not None:
                    powder_traits.append(
                        f"position: {int(load_meta.get('powder_burn_rate_position'))}"
                    )
                if load_meta.get("powder_relative_burn_rate") is not None:
                    powder_traits.append(
                        f"Ba: {float(load_meta.get('powder_relative_burn_rate')):.4f}"
                    )
                if load_meta.get("powder_density_gcc") is not None:
                    powder_traits.append(
                        f"density: {float(load_meta.get('powder_density_gcc')):.3f} g/cc"
                    )
                if powder_traits:
                    meta_parts.append(
                        tr(
                            "calib_analysis_powder_model",
                            value=" | ".join(powder_traits),
                        )
                    )
                if load_meta.get("cbto_mm") is not None:
                    meta_parts.append(
                        tr("calib_analysis_cbto", value=float(load_meta.get("cbto_mm")))
                    )
                if load_meta.get("coal_mm") is not None:
                    meta_parts.append(
                        tr("calib_analysis_coal", value=float(load_meta.get("coal_mm")))
                    )
                if load_meta.get("neck_tension_mm") is not None:
                    meta_parts.append(
                        tr(
                            "calib_analysis_neck_tension",
                            value=float(load_meta.get("neck_tension_mm")),
                        )
                    )
                if load_meta.get("group_size_mm") is not None:
                    meta_parts.append(
                        tr(
                            "calib_analysis_group",
                            value=float(load_meta.get("group_size_mm")),
                        )
                    )
                if load_meta.get("distance_m") is not None:
                    meta_parts.append(
                        tr(
                            "calib_analysis_distance",
                            value=float(load_meta.get("distance_m")),
                        )
                    )
                if load_meta.get("temperature_c") is not None:
                    meta_parts.append(
                        tr(
                            "calib_analysis_temperature",
                            value=float(load_meta.get("temperature_c")),
                        )
                    )
                lines.extend(f"  {part}" for part in meta_parts)
                if meta_parts:
                    lines.append("")
            chrono = res.get("chrono_stats")
            if chrono:
                lines.append(
                    tr("calib_analysis_mean_velocity", value=chrono.get("mean"))
                )
                lines.append(tr("calib_analysis_es", value=chrono.get("es")))
                lines.append(tr("calib_analysis_sd", value=chrono.get("sd")))
                lines.append(tr("calib_analysis_n", value=chrono.get("n")))
            img = res.get("image_analysis")
            if img:
                if img.get("error"):
                    lines.append(
                        tr("calib_analysis_image_error", error=img.get("error"))
                    )
                else:
                    lines.append(
                        tr(
                            "calib_analysis_pixel_diameter",
                            value=img.get("pixel_diameter"),
                        )
                    )
                    lines.append(
                        tr("calib_analysis_mm_diameter", value=img.get("mm_diameter"))
                    )
                    lines.append(
                        tr("calib_analysis_detected_shots", value=img.get("n_shots"))
                    )
            # optics suggestion (if present)
            optics_sugg = res.get("optics_suggestion")
            if optics_sugg:
                v = optics_sugg.get("vertical")
                h = optics_sugg.get("horizontal")
                if v:
                    lines.append("")
                    lines.append(tr("calib_analysis_optics_vertical"))
                    lines.append(
                        tr(
                            "calib_analysis_angle",
                            unit=v.get("unit"),
                            value=v.get("angle_unit"),
                        )
                    )
                    lines.append(
                        tr(
                            "calib_analysis_clicks",
                            clicks=v.get("clicks"),
                            revs=v.get("revolutions"),
                            rem=v.get("remainder_clicks"),
                        )
                    )
                if h:
                    lines.append("")
                    lines.append(tr("calib_analysis_optics_horizontal"))
                    lines.append(
                        tr(
                            "calib_analysis_angle",
                            unit=h.get("unit"),
                            value=h.get("angle_unit"),
                        )
                    )
                    lines.append(
                        tr(
                            "calib_analysis_clicks",
                            clicks=h.get("clicks"),
                            revs=h.get("revolutions"),
                            rem=h.get("remainder_clicks"),
                        )
                    )
            lines.append("")
            txt.setPlainText("\n".join(lines))
            # if there is an image, display it with overlay if center + pixel_diameter present
            img_path = None
            if isinstance(res, dict) and res.get("image_path"):
                img_path = res.get("image_path")
            # backwards compatibility: image_analysis may have come from CalibrationTestDialog
            img_analysis = res.get("image_analysis")
            if img_path:
                img_label = QLabel()
                pix = QPixmap(img_path)
                # draw overlay if we have analysis center and pixel_diameter
                if (
                    img_analysis
                    and isinstance(img_analysis, dict)
                    and img_analysis.get("pixel_diameter")
                    and img_analysis.get("center")
                ):
                    center = img_analysis.get("center")
                    px_d = img_analysis.get("pixel_diameter")
                    try:
                        p = QPixmap(img_path)
                        painter = QPainter(p)
                        pen = QPen(Qt.GlobalColor.green)
                        pen.setWidth(3)
                        painter.setPen(pen)
                        cx, cy = center
                        r = px_d / 2.0
                        painter.drawEllipse(
                            int(cx - r), int(cy - r), int(r * 2), int(r * 2)
                        )
                        painter.end()
                        img_label.setPixmap(p)
                    except Exception:
                        img_label.setPixmap(pix)
                else:
                    img_label.setPixmap(pix)
                layout.addWidget(img_label)
            layout.addWidget(txt)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton(tr("calib_analysis_save_test"))
        self.save_btn.clicked.connect(self._on_save)
        # Apply optics suggestion button (only enabled if profile is present)
        self.apply_btn = QPushButton(tr("calib_analysis_apply_optics"))
        self.apply_btn.setToolTip(tr("calib_analysis_apply_optics_tooltip"))
        self.apply_btn.clicked.connect(self._on_apply_suggestions)
        self.apply_btn.setEnabled(self._profile is not None)
        self.close_btn = QPushButton(tr("calib_analysis_close"))
        self.close_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        self.saved = True
        self.accept()

    def _on_apply_suggestions(self) -> None:
        """Apply any optics_suggestion entries from results into the profile.

        Appends entries to `profile['optics_history']` with timestamp and details.
        """
        if not self._profile:
            QMessageBox.warning(
                self,
                tr("calib_analysis_no_profile_title"),
                tr("calib_analysis_no_profile_message"),
            )
            return

        applied = 0
        from datetime import datetime

        hist = self._profile.setdefault("optics_history", [])
        for idx, res in enumerate(self.results):
            sugg = res.get("optics_suggestion")
            if not sugg:
                continue
            entry = {
                "timestamp": datetime.now().isoformat(),
                "load_index": idx,
                "vertical": sugg.get("vertical"),
                "horizontal": sugg.get("horizontal"),
                "meta": {"source": "calibration_analysis_dialog"},
            }
            hist.append(entry)
            applied += 1

        if applied:
            # attempt auto-persist if callback provided
            try:
                if callable(getattr(self, "_persist_callback", None)):
                    self._persist_callback()
            except Exception:
                # ignore persistence failures but inform user
                QMessageBox.warning(
                    self,
                    tr("calib_analysis_persist_failed_title"),
                    tr("calib_analysis_persist_failed_message"),
                )

            QMessageBox.information(
                self,
                tr("calib_analysis_applied_title"),
                tr("calib_analysis_applied_message", count=applied),
            )
        else:
            QMessageBox.information(
                self,
                tr("calib_analysis_no_suggestions_title"),
                tr("calib_analysis_no_suggestions_message"),
            )
