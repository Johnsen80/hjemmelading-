from __future__ import annotations

from typing import Any, Dict, List

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QTextEdit,
)
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QPixmap, QPainter, QPen
from PyQt6.QtCore import Qt

# pathlib.Path not required here


class CalibrationAnalysisDialog(QDialog):
    """Show analysis results for a calibration test.

    Expects `results` to be a list of dicts for each load containing chrono
    stats and optional image-analysis results. If a `profile` dict is
    provided the dialog can apply suggested optic adjustments into
    `profile['optics_history']`.
    """

    def __init__(self, results: List[Dict[str, Any]], parent=None, profile: dict | None = None, persist_callback=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibration Analysis")
        self.resize(720, 480)
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
            lines: List[str] = [f"Load {i} analysis:"]
            chrono = res.get("chrono_stats")
            if chrono:
                lines.append(f"  Mean velocity: {chrono.get('mean')}")
                lines.append(f"  ES: {chrono.get('es')}")
                lines.append(f"  SD: {chrono.get('sd')}")
                lines.append(f"  N: {chrono.get('n')}")
            img = res.get("image_analysis")
            if img:
                if img.get("error"):
                    lines.append(f"  Image analysis: error={img.get('error')}")
                else:
                    lines.append(f"  Pixel diameter: {img.get('pixel_diameter')}")
                    lines.append(f"  Mm diameter: {img.get('mm_diameter')}")
                    lines.append(f"  Detected shots: {img.get('n_shots')}")
            # optics suggestion (if present)
            optics_sugg = res.get("optics_suggestion")
            if optics_sugg:
                v = optics_sugg.get("vertical")
                h = optics_sugg.get("horizontal")
                if v:
                    lines.append("")
                    lines.append("  Optics suggestion (vertical):")
                    lines.append(f"    Angle ({v.get('unit')}): {v.get('angle_unit'):.3f}")
                    lines.append(f"    Clicks: {v.get('clicks')} (revs={v.get('revolutions')}, rem={v.get('remainder_clicks')})")
                if h:
                    lines.append("")
                    lines.append("  Optics suggestion (horizontal):")
                    lines.append(f"    Angle ({h.get('unit')}): {h.get('angle_unit'):.3f}")
                    lines.append(f"    Clicks: {h.get('clicks')} (revs={h.get('revolutions')}, rem={h.get('remainder_clicks')})")
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
                if img_analysis and isinstance(img_analysis, dict) and img_analysis.get("pixel_diameter") and img_analysis.get("center"):
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
                        painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
                        painter.end()
                        img_label.setPixmap(p)
                    except Exception:
                        img_label.setPixmap(pix)
                else:
                    img_label.setPixmap(pix)
                layout.addWidget(img_label)
            layout.addWidget(txt)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save Test")
        self.save_btn.clicked.connect(self._on_save)
        # Apply optics suggestion button (only enabled if profile is present)
        self.apply_btn = QPushButton("Apply Optic Suggestions")
        self.apply_btn.setToolTip("Apply computed optic click suggestions to the active profile history")
        self.apply_btn.clicked.connect(self._on_apply_suggestions)
        self.apply_btn.setEnabled(self._profile is not None)
        self.close_btn = QPushButton("Close")
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
            QMessageBox.warning(self, "No profile", "No profile available to apply suggestions to.")
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
                QMessageBox.warning(self, "Persist failed", "Applied suggestions but failed to persist to storage.")

            QMessageBox.information(self, "Applied", f"Applied {applied} optic suggestion(s) to profile history.")
        else:
            QMessageBox.information(self, "No suggestions", "No optic suggestions were present to apply.")
