"""
Target Analyzer - automatic group measurement with computer vision
Uses OpenCV to measure group size from target images
"""

import os

import numpy as np
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from HjemmeladingApp.utils import units

from ..database.database import get_database
from ..tools.load_session_runtime_service import (
    build_active_workflow_context_from_settings,
    refresh_load_session_measurement_summary,
)
from ..utils.i18n import tr
from ..utils.optional_deps import HAS_CV2, cv2
from .batch_workspace import recompute_batch_analysis_from_db


def _get_active_workflow_context() -> dict[str, object]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    try:
        database = get_database()
    except Exception:
        database = None
    return build_active_workflow_context_from_settings(settings, database)


def _get_active_analysis_focus() -> dict[str, str]:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    focus = str(settings.value("workflow_context/analysis_focus", "") or "").strip()
    reason = str(
        settings.value("workflow_context/analysis_focus_reason", "") or ""
    ).strip()
    if not focus and not reason:
        return {}
    return {"focus": focus, "reason": reason}


def _get_global_unit_system() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return str(settings.value("units/global", "metric") or "metric").strip().lower()


def _format_group_size_mm(value_mm: float) -> str:
    if _get_global_unit_system() == "imperial":
        return f"{units.mm_to_inches(value_mm):.2f} in ({value_mm:.1f} mm)"
    return f"{value_mm:.1f} mm"


def _format_distance_m(distance_m: float) -> str:
    if _get_global_unit_system() == "imperial":
        return f"{units.meters_to_yards(distance_m):.0f} yd ({distance_m:.0f} m)"
    return f"{distance_m:.0f} meter"


def _format_offset_mm(value_mm: float) -> str:
    if _get_global_unit_system() == "imperial":
        return f"{units.mm_to_inches(value_mm):.2f} in ({value_mm:.1f} mm)"
    return f"{value_mm:.1f} mm"


def _shot_axis_unit_label() -> str:
    return "in" if _get_global_unit_system() == "imperial" else "mm"


def build_target_analysis_summary(
    results: dict, workflow_context: dict[str, object] | None = None
) -> str:
    summary = (
        f"Target Analyzer | {tr('target_summary_prefix')}: "
        f"{results['max_spread_mm']:.1f} mm ({results['moa']:.2f} MOA), "
        + tr("target_summary_shots", count=results["shot_count"])
    )
    context = workflow_context or {}
    if context.get("workflow_id"):
        workflow_name = (
            context.get("workflow_name") or f"Workflow {context['workflow_id']}"
        )
        summary += f" [workflow:{context['workflow_id']}] " f"{workflow_name}"
    return summary


def build_target_quality_summary(results: dict) -> dict[str, str]:
    shot_count = int(results.get("shot_count", 0) or 0)
    group_mm = float(results.get("max_spread_mm", 0.0) or 0.0)
    moa = float(results.get("moa", 0.0) or 0.0)

    if shot_count < 3:
        return {
            "level": "needs_more_data",
            "title": tr("target_quality_needs_more_title"),
            "message": tr("target_quality_needs_more_message"),
        }
    if moa <= 0.75:
        return {
            "level": "ready",
            "title": tr("target_quality_ready_title"),
            "message": tr("target_quality_ready_message"),
        }
    if moa >= 1.5 or group_mm >= 45:
        return {
            "level": "watch",
            "title": tr("target_quality_watch_title"),
            "message": tr("target_quality_watch_message"),
        }
    return {
        "level": "usable",
        "title": tr("target_quality_usable_title"),
        "message": tr("target_quality_usable_message"),
    }


def build_target_evidence_basis(results: dict) -> dict[str, str]:
    shot_count = int(results.get("shot_count", 0) or 0)
    measured_parts = [
        tr("target_evidence_measured_shots", count=shot_count),
        tr("target_evidence_measured_group"),
    ]
    modeled_parts = [
        tr("target_evidence_modeled"),
    ]
    recommended_parts = [
        tr("target_evidence_recommended_quality"),
    ]
    if shot_count < 3:
        recommended_parts.append(tr("target_evidence_recommended_more"))
    else:
        recommended_parts.append(tr("target_evidence_recommended_compare"))

    return {
        "title": tr("target_evidence_title"),
        "message": (
            f"{tr('evidence_measured')}: {', '.join(measured_parts)}. "
            f"{tr('evidence_modeled')}: {', '.join(modeled_parts)}. "
            f"{tr('evidence_recommended')}: {', '.join(recommended_parts)}."
        ),
    }


class TargetAnalyzer(QWidget):
    """Widget for automatic target analysis."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_image = None
        self.detected_shots = []
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel(tr("target_analyzer_title"))
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(tr("target_analyzer_subtitle"))
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)

        analysis_focus = _get_active_analysis_focus()
        if analysis_focus.get("focus") == "pressure_review":
            focus_text = analysis_focus.get("reason") or (
                tr("target_pressure_review_reason")
            )
            self.focus_label = QLabel(f"{tr('target_pressure_review')}: {focus_text}")
            self.focus_label.setWordWrap(True)
            self.focus_label.setStyleSheet(
                "background-color: #fff3cd; color: #856404; border: 1px solid #ffe69c; "
                "border-radius: 6px; padding: 8px; font-size: 10.5pt;"
            )
            layout.addWidget(self.focus_label)

        # Hovedlayout med bilde og resultater side-ved-side
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)

        # Venstre side - Bildeopplasting og visning
        left_widget = self.create_image_section()
        main_layout.addWidget(left_widget, 3)

        # Høyre side - Resultater og analyse
        right_widget = self.create_results_section()
        main_layout.addWidget(right_widget, 2)

        # Kontroller nederst
        controls_layout = self.create_controls()
        layout.addLayout(controls_layout)

    def create_image_section(self):
        """Oppretter bildeseksjon"""
        group = QGroupBox(tr("target_image_group"))
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Bildedisplay
        self.image_label = QLabel()
        self.image_label.setMinimumSize(600, 600)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            """
            QLabel {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
        """
        )
        self.image_label.setText(tr("target_upload_prompt"))
        layout.addWidget(self.image_label)

        # Last opp knapp
        upload_btn = QPushButton(tr("target_upload_button"))
        upload_btn.setMinimumHeight(40)
        upload_btn.clicked.connect(self.upload_image)
        layout.addWidget(upload_btn)

        return group

    def create_results_section(self):
        """Oppretter resultatseksjon"""
        group = QGroupBox(tr("target_results_group"))
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)

        # Resultatvisning
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(300)
        self.results_text.setStyleSheet("font-size: 11pt;")
        self.results_text.setText(tr("target_results_intro"))
        layout.addWidget(self.results_text)

        # Skuddtabell
        group_shots = QGroupBox(tr("target_detected_shots"))
        shots_layout = QVBoxLayout()
        group_shots.setLayout(shots_layout)

        self.shots_table = QTableWidget()
        self.shots_table.setColumnCount(3)
        axis_unit = _shot_axis_unit_label()
        self.shots_table.setHorizontalHeaderLabels(
            ["Shot #", f"X ({axis_unit})", f"Y ({axis_unit})"]
        )
        self.shots_table.setMaximumHeight(200)
        shots_layout.addWidget(self.shots_table)

        layout.addWidget(group_shots)

        return group

    def create_controls(self):
        """Oppretter kontroller"""
        layout = QHBoxLayout()

        # Parametre for analyse
        params_group = QGroupBox(tr("target_analysis_parameters"))
        params_layout = QHBoxLayout()
        params_group.setLayout(params_layout)

        params_layout.addWidget(QLabel(tr("target_distance")))
        self.distance = QSpinBox()
        self.distance.setRange(10, 1000)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        params_layout.addWidget(self.distance)

        params_layout.addWidget(QLabel(tr("target_target_size")))
        self.target_size = QDoubleSpinBox()
        self.target_size.setRange(10, 100)
        self.target_size.setValue(20.0)
        self.target_size.setSuffix(" cm")
        self.target_size.setDecimals(1)
        params_layout.addWidget(self.target_size)

        params_layout.addWidget(QLabel(tr("target_sensitivity")))
        self.sensitivity = QSpinBox()
        self.sensitivity.setRange(1, 10)
        self.sensitivity.setValue(5)
        params_layout.addWidget(self.sensitivity)

        layout.addWidget(params_group)

        # Handlingsknapper
        analyze_btn = QPushButton(tr("target_analyze_image"))
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.analyze_image)
        layout.addWidget(analyze_btn)

        save_btn = QPushButton(tr("target_save_results"))
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_results)
        layout.addWidget(save_btn)

        layout.addStretch()

        return layout

    def upload_image(self):
        """Last opp bilde"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("target_upload_button"),
            "",
            tr("target_image_filter"),
        )

        if file_path:
            if not HAS_CV2 or cv2 is None:
                QMessageBox.critical(
                    self,
                    tr("target_missing_dependency_title"),
                    tr("target_missing_dependency_load"),
                )
                return

            # Last inn med OpenCV
            self.current_image = cv2.imread(file_path)

            if self.current_image is not None:
                # Vis bilde
                self.display_image(self.current_image)
                self.results_text.setText(
                    tr("target_image_loaded", filename=os.path.basename(file_path))
                )
            else:
                QMessageBox.critical(
                    self,
                    tr("target_load_failed_title"),
                    tr("target_load_failed_message"),
                )

    def display_image(self, image, shots=None):
        """Viser bilde i GUI"""
        # Lag en kopi for visning
        display_img = image.copy()

        # Tegn detekterte skudd hvis tilgjengelig
        if shots is not None and len(shots) > 0:
            for i, shot in enumerate(shots):
                x, y = shot
                # Tegn sirkel rundt skudd
                if HAS_CV2 and cv2 is not None:
                    cv2.circle(display_img, (int(x), int(y)), 10, (0, 255, 0), 2)
                # Nummerer skudd
                if HAS_CV2 and cv2 is not None:
                    cv2.putText(
                        display_img,
                        str(i + 1),
                        (int(x) + 15, int(y) + 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

        # Konverter BGR til RGB
        if HAS_CV2 and cv2 is not None:
            rgb_image = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        else:
            # Fallback: assume image is already RGB-like numpy array
            rgb_image = display_img

        # Skaler ned hvis for stort
        height, width = rgb_image.shape[:2]
        max_size = 600
        if height > max_size or width > max_size:
            scale = min(max_size / height, max_size / width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            rgb_image = cv2.resize(rgb_image, (new_width, new_height))

        # Konverter til QPixmap
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(
            rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qt_image)

        self.image_label.setPixmap(pixmap)

    def analyze_image(self):
        """Analyserer bildet for å finne skudd"""
        if self.current_image is None:
            QMessageBox.warning(
                self, tr("target_no_image_title"), tr("target_no_image_message")
            )
            return

        try:
            # Kjør deteksjon
            if not HAS_CV2 or cv2 is None:
                QMessageBox.critical(
                    self,
                    tr("target_missing_dependency_title"),
                    tr("target_missing_dependency_analyze"),
                )
                return

            shots = self.detect_shots(self.current_image, self.sensitivity.value())

            if len(shots) == 0:
                QMessageBox.warning(
                    self,
                    tr("target_no_shots_title"),
                    tr("target_no_shots_message"),
                )
                return

            self.detected_shots = shots

            # Beregn statistikk
            results = self.calculate_group_stats(shots)

            # Vis resultater
            self.display_results(results)

            # Oppdater tabell
            self.update_shots_table(shots)

            # Vis bilde med markerte skudd
            self.display_image(self.current_image, shots)

        except Exception as e:
            QMessageBox.critical(
                self,
                tr("target_analysis_error_title"),
                tr("target_analysis_error_message", error=str(e)),
            )

    def detect_shots(self, image, sensitivity):
        """Detekterer skudd i bildet"""
        if not HAS_CV2 or cv2 is None:
            raise ImportError(
                "OpenCV (cv2) is required for detect_shots but is not installed."
            )

        # Konverter til gråskala
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Bruk Gaussian blur for å redusere støy
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Bruk Hough Circle detection for å finne skudd
        # Juster parametre basert på sensitivitet
        min_radius = max(5, 20 - sensitivity * 2)
        max_radius = min(50, 30 + sensitivity * 2)
        param1 = 50
        param2 = max(10, 30 - sensitivity * 2)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        shots = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for x, y, r in circles:
                shots.append((x, y))

        # Alternativ metode hvis Hough ikke finner noe: blob detection
        if len(shots) == 0:
            # Bruk SimpleBlobDetector
            params = cv2.SimpleBlobDetector_Params()
            params.filterByArea = True
            params.minArea = 50
            params.maxArea = 5000
            params.filterByCircularity = True
            params.minCircularity = 0.3
            params.filterByConvexity = True
            params.minConvexity = 0.5

            detector = cv2.SimpleBlobDetector_create(params)

            # Inverter bildet (skudd er ofte mørke hull)
            inverted = cv2.bitwise_not(gray)
            keypoints = detector.detect(inverted)

            for kp in keypoints:
                shots.append((int(kp.pt[0]), int(kp.pt[1])))

        return shots

    def calculate_group_stats(self, shots):
        """Beregner statistikk for gruppen"""
        if len(shots) < 2:
            return None

        # Konverter til numpy array
        points = np.array(shots, dtype=np.float32)

        # Finn centrum av gruppe
        center_x = np.mean(points[:, 0])
        center_y = np.mean(points[:, 1])

        # Beregn avstand fra hver shot til centrum
        distances = []
        for x, y in points:
            dist = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            distances.append(dist)

        # Finn ekstreme spread (lengste avstand mellom to skudd)
        max_spread_pixels = 0
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = np.sqrt(
                    (points[i][0] - points[j][0]) ** 2
                    + (points[i][1] - points[j][1]) ** 2
                )
                max_spread_pixels = max(max_spread_pixels, dist)

        # Konverter piksler til mm basert på kjent skive-størrelse
        # Anta at bildet viser hele skiven
        image_height = self.current_image.shape[0]
        target_size_mm = self.target_size.value() * 10  # cm til mm
        pixels_per_mm = image_height / target_size_mm

        max_spread_mm = max_spread_pixels / pixels_per_mm

        # Beregn gjennomsnittlig avstand fra centrum
        avg_distance_pixels = np.mean(distances)
        avg_distance_mm = avg_distance_pixels / pixels_per_mm

        # Beregn MOA ved gitt avstand
        distance_m = self.distance.value()
        moa = (
            (max_spread_mm / 10) / (distance_m / 100) / 2.908
        )  # 1 MOA = 2.908 cm ved 100m
        mrad = (max_spread_mm / 10) / (distance_m / 10)  # 1 MRAD = 10 cm ved 100m

        return {
            "shot_count": len(shots),
            "center": (center_x, center_y),
            "max_spread_mm": max_spread_mm,
            "avg_radius_mm": avg_distance_mm,
            "moa": moa,
            "mrad": mrad,
            "distance_m": distance_m,
        }

    def display_results(self, results):
        """Viser resultater i tekstfeltet"""
        if results is None:
            self.results_text.setText(tr("target_stats_failed"))
            return

        quality = build_target_quality_summary(results)
        evidence_basis = build_target_evidence_basis(results)

        text = f"""
<h3>{tr("target_analysis_done")}</h3>

<p><b>{quality['title']}</b><br>
{quality['message']}</p>

<p><b>{evidence_basis['title']}</b><br>
{evidence_basis['message']}</p>

<p><b>{tr("target_shot_count_label")}</b> {results['shot_count']}</p>

<p><b>{tr("target_group_size_label")}</b><br>
• {_format_group_size_mm(results['max_spread_mm'])}<br>
• {results['max_spread_mm']/10:.2f} cm<br>
• {results['moa']:.2f} MOA<br>
• {results['mrad']:.3f} MRAD</p>

<p><b>{tr("target_avg_radius_label")}</b><br>
• {_format_group_size_mm(results['avg_radius_mm'])} {tr("target_avg_radius_suffix")}</p>

<p><b>{tr("target_distance_label")}</b> {_format_distance_m(results['distance_m'])}</p>

<hr>

<p style="color: #555; font-size: 10pt;">
<b>{tr("target_tip_label")}</b> {tr("target_tip_body").replace(chr(10), "<br>")}
</p>
        """

        self.results_text.setHtml(text)

    def update_shots_table(self, shots):
        """Oppdaterer skuddtabellen"""
        self.shots_table.setRowCount(len(shots))
        axis_unit = _shot_axis_unit_label()
        self.shots_table.setHorizontalHeaderLabels(
            [tr("target_shot_col"), f"X ({axis_unit})", f"Y ({axis_unit})"]
        )

        # Beregn pixels per mm
        image_height = self.current_image.shape[0]
        target_size_mm = self.target_size.value() * 10
        pixels_per_mm = image_height / target_size_mm

        for i, (x, y) in enumerate(shots):
            # Konverter til mm relativt til centrum
            center_x = self.current_image.shape[1] / 2
            center_y = self.current_image.shape[0] / 2

            x_mm = (x - center_x) / pixels_per_mm
            y_mm = (center_y - y) / pixels_per_mm  # Y invertert

            self.shots_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.shots_table.setItem(i, 1, QTableWidgetItem(_format_offset_mm(x_mm)))
            self.shots_table.setItem(i, 2, QTableWidgetItem(_format_offset_mm(y_mm)))

    def save_results(self):
        """Lagrer resultater til database"""
        if len(self.detected_shots) == 0:
            QMessageBox.warning(
                self, tr("target_no_data_title"), tr("target_no_data_message")
            )
            return

        # Beregn statistikk på nytt
        results = self.calculate_group_stats(self.detected_shots)

        if results is None:
            return

        msg = tr(
            "target_save_confirm_body",
            group_mm=results["max_spread_mm"],
            moa=results["moa"],
            shot_count=results["shot_count"],
            distance_m=results["distance_m"],
        )

        reply = QMessageBox.question(
            self,
            tr("target_save_confirm_title"),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        from .session_logger import ShootingSessionDialog

        rifles = self.db.get_all("rifles")
        ammo_profiles = self.db.get_all("ammo_profiles")
        dialog = ShootingSessionDialog(self, rifles=rifles, ammo_profiles=ammo_profiles)

        dialog.rounds_fired.setValue(results["shot_count"])
        dialog.distance.setValue(int(round(results["distance_m"])))
        dialog.best_group.setValue(results["max_spread_mm"])
        dialog.avg_group.setValue(results["max_spread_mm"])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        workflow_context = _get_active_workflow_context()
        if data.get("load_session_id") in (None, ""):
            data["load_session_id"] = workflow_context.get("load_session_id")
        summary = build_target_analysis_summary(results, workflow_context)
        notes = (data.get("notes") or "").strip()
        data["notes"] = f"{notes}\n{summary}".strip()

        self.db.insert("shooting_sessions", data)
        rifle_id = data.get("rifle_id") or workflow_context.get("rifle_id")
        try:
            rifle_id_int = int(rifle_id) if rifle_id not in (None, "") else None
        except Exception:
            rifle_id_int = None
        if rifle_id_int:
            self.db.record_barrel_target_observation(
                rifle_id_int,
                workflow_context.get("barrel_id"),
                workflow_context.get("barrel_name"),
                {
                    "date": data.get("date"),
                    "distance_meters": data.get("distance_meters"),
                    "best_group_mm": data.get("best_group_mm"),
                },
                barrel_configuration_id=workflow_context.get("barrel_configuration_id"),
                barrel_configuration_name=workflow_context.get(
                    "barrel_configuration_name"
                ),
            )
        batch_id = QSettings("ReloadingWorkshop", "ReloadingManager").value(
            "batch_context/batch_id"
        )
        if batch_id not in (None, ""):
            try:
                recompute_batch_analysis_from_db(self.db, batch_id)
            except Exception:
                pass
        refresh_load_session_measurement_summary(
            self.db,
            data.get("load_session_id") or workflow_context.get("load_session_id"),
            source="target_analyzer.save_results",
        )
        QMessageBox.information(
            self, tr("target_saved_title"), tr("target_saved_message")
        )
