"""
Komplett Rifle Database Manager
Håndterer alle rifle data inkl. harmonikk, skuddteller, bullet jump, vedlikehold
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.cartridge_standard_support import compare_chamber_to_cartridge_standard
from ..utils.rifle_harmonics import build_harmonics_html


def build_chamber_comparison_html(db, rifle: dict, profile_details: dict) -> str:
    caliber = str(rifle.get("caliber") or "").strip()
    if not caliber:
        return "<h3>Standard vs Measured</h3><p>Caliber is missing for comparison.</p>"

    measured = {
        "freebore_mm": rifle.get("freebore_mm"),
        "throat_angle_deg": rifle.get("throat_angle_deg"),
        "throat_erosion_mm": rifle.get("throat_erosion_mm"),
        "case_neck_diameter_mm": profile_details.get("chamber_neck_diameter_mm"),
        "trim_length_mm": None,
    }
    comparison = compare_chamber_to_cartridge_standard(db, caliber, measured)
    notes = comparison.get("notes") or []
    status = comparison.get("status") or "missing_standard"
    status_label = {
        "ok": "OK",
        "watch": "Watch",
        "missing_standard": "Missing standard",
    }.get(status, str(status))
    notes_html = (
        "".join(f"<li>{note}</li>" for note in notes)
        or "<li>No comparison is available yet.</li>"
    )
    return f"""
    <h3>Standard vs Measured</h3>
    <p><b>Status:</b> {status_label}</p>
    <ul>{notes_html}</ul>
    """


def describe_jump_measurement_barrel(measurement: dict) -> str:
    barrel_name = str(measurement.get("barrel_name") or "").strip()
    if barrel_name:
        return barrel_name

    barrel_id = str(measurement.get("barrel_id") or "").strip()
    if barrel_id:
        return f"Barrel {barrel_id}"

    return "Legacy rifle-level"


class RifleDatabaseManager(QWidget):
    """
    Hovedvindu for rifle database management
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.init_ui()
        self.load_rifles()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel("Firearm Database")
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        desc = QLabel(
            "Complete database of your firearms with barrel data, harmonics, round count, "
            "bullet jump measurements, and maintenance."
        )
        desc.setWordWrap(True)
        desc.setProperty("variant", "cardSubtitle")
        layout.addWidget(desc)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("New Firearm")
        self.btn_add.clicked.connect(self.add_rifle)
        self.btn_add.setProperty("variant", "primary")

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.edit_rifle)
        self.btn_edit.setProperty("variant", "secondary")

        self.btn_view_details = QPushButton("Details")
        self.btn_view_details.clicked.connect(self.view_rifle_details)
        self.btn_view_details.setProperty("variant", "ghost")

        self.btn_add_rounds = QPushButton("Add Shots")
        self.btn_add_rounds.clicked.connect(self.add_rounds_fired)
        self.btn_add_rounds.setProperty("variant", "secondary")

        self.btn_maintenance = QPushButton("Maintenance")
        self.btn_maintenance.clicked.connect(self.log_maintenance)
        self.btn_maintenance.setProperty("variant", "secondary")

        self.btn_accuracy_test = QPushButton("Accuracy Test")
        self.btn_accuracy_test.clicked.connect(self.manage_accuracy_tests)
        self.btn_accuracy_test.setProperty("variant", "secondary")

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.delete_rifle)
        self.btn_delete.setProperty("variant", "ghost")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_view_details)
        btn_layout.addWidget(self.btn_add_rounds)
        btn_layout.addWidget(self.btn_maintenance)
        btn_layout.addWidget(self.btn_accuracy_test)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(btn_layout)

        # Rifles table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "Manufacturer",
                "Model",
                "Caliber",
                "Barrel Length",
                "Shots Fired",
                "Status",
                "Last Maintenance",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(  # type: ignore[union-attr]
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.view_rifle_details)

        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel("Klar.")
        self.status_label.setProperty("role", "muted")
        self.status_label.setProperty("emphasis", "placeholder")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def load_rifles(self):
        """Load all rifles from database"""
        rifles = self.db.get_all("rifles", "name")

        self.table.setRowCount(len(rifles))

        for row, rifle in enumerate(rifles):
            self.table.setItem(row, 0, QTableWidgetItem(str(rifle.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(rifle.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(rifle.get("manufacturer", "")))
            self.table.setItem(row, 3, QTableWidgetItem(rifle.get("model", "")))
            self.table.setItem(row, 4, QTableWidgetItem(rifle.get("caliber", "")))

            # Barrel length
            barrel_length = rifle.get(
                "barrel_length_inches", rifle.get("barrel_length_mm")
            )
            if barrel_length:
                length_str = f'{barrel_length:.1f}"'
            else:
                length_str = "-"
            self.table.setItem(row, 5, QTableWidgetItem(length_str))

            # Round count
            round_count = rifle.get("round_count", 0) or 0
            round_item = QTableWidgetItem(str(round_count))

            # Check if case measurement warning should be triggered
            accuracy_life = rifle.get("accuracy_life_estimate", 2000)
            if (
                round_count >= 500 and round_count % 500 < 100
            ):  # Near 500 round intervals
                round_item.setBackground(QColor(255, 200, 0, 100))  # Yellow warning
                round_item.setToolTip("Time for case measurement!")
            elif round_count > accuracy_life * 0.8:  # 80% of barrel life
                round_item.setBackground(QColor(255, 100, 100, 100))  # Red warning
                round_item.setToolTip(
                    "The barrel is nearing the end of its service life!"
                )

            self.table.setItem(row, 6, round_item)

            # Status
            bore_condition = rifle.get("bore_condition", "unknown")
            status_colors = {
                "excellent": ("#27ae60", "Excellent"),
                "good": ("#3498db", "Good"),
                "fair": ("#f39c12", "OK"),
                "worn": ("#e74c3c", "Worn"),
                "unknown": ("#95a5a6", "Unknown"),
            }
            color, text = status_colors.get(bore_condition, status_colors["unknown"])
            status_item = QTableWidgetItem(text)
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 7, status_item)

            # Last maintenance
            last_maint = rifle.get("last_maintenance_date", "-")
            self.table.setItem(
                row, 8, QTableWidgetItem(last_maint if last_maint else "-")
            )

        self.status_label.setText(f"Loaded {len(rifles)} firearms.")

    def add_rifle(self):
        """Add new rifle"""
        dialog = RifleEditorDialog(self, rifle_id=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()

    def edit_rifle(self):
        """Edit selected rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Select a firearm to edit.")
            return

        rifle_id = int(self.table.item(selected, 0).text())
        dialog = RifleEditorDialog(self, rifle_id=rifle_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()

    def view_rifle_details(self):
        """View detailed rifle information"""
        selected = self.table.currentRow()
        if selected < 0:
            return

        rifle_id = int(self.table.item(selected, 0).text())
        dialog = RifleDetailsDialog(self, rifle_id=rifle_id)
        dialog.exec()

    def add_rounds_fired(self):
        """Add rounds fired to rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Select a firearm.")
            return

        rifle_id = int(self.table.item(selected, 0).text())
        rifle = self.db.get_by_id("rifles", rifle_id)
        if not rifle:
            QMessageBox.warning(
                self,
                "Firearm Missing",
                "The selected firearm no longer exists in the database.",
            )
            self.load_rifles()
            return

        dialog = AddRoundsFiredDialog(self, rifle)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()

    def log_maintenance(self):
        """Log maintenance for rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Select a firearm.")
            return

        rifle_id = int(self.table.item(selected, 0).text())
        rifle = self.db.get_by_id("rifles", rifle_id)
        if not rifle:
            QMessageBox.warning(
                self,
                "Firearm Missing",
                "The selected firearm no longer exists in the database.",
            )
            self.load_rifles()
            return

        dialog = MaintenanceLogDialog(self, rifle)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_rifles()

    def manage_accuracy_tests(self):
        """Open accuracy test manager for selected rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Select a firearm.")
            return

        rifle_id = int(self.table.item(selected, 0).text())
        rifle = self.db.get_by_id("rifles", rifle_id)
        if not rifle:
            QMessageBox.warning(
                self,
                "Firearm Missing",
                "The selected firearm no longer exists in the database.",
            )
            self.load_rifles()
            return

        from .rifle_accuracy_test_system import RifleAccuracyTestManager

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Accuracy Tests - {rifle.get('name', '')}")
        dialog.setMinimumSize(1000, 600)

        layout = QVBoxLayout()
        test_manager = RifleAccuracyTestManager(dialog, rifle_id=rifle_id)
        layout.addWidget(test_manager)

        btn_close = QPushButton("Close")
        btn_close.setProperty("variant", "ghost")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.setLayout(layout)
        dialog.exec()

    def delete_rifle(self):
        """Delete selected rifle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Select a firearm to delete.")
            return

        rifle_name = self.table.item(selected, 1).text()
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{rifle_name}'?\n\nThis will also delete all related data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            rifle_id = int(self.table.item(selected, 0).text())
            self.db.delete("rifles", "id = ?", (rifle_id,))
            self.load_rifles()
            self.status_label.setText(f"Deleted '{rifle_name}'.")


class RifleEditorDialog(QDialog):
    """
    Comprehensive rifle editor dialog with ALL database fields
    """

    def __init__(self, parent=None, rifle_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id
        self.rifle_data: Dict[str, Any] = {}

        self.setWindowTitle("Rifle Editor" if rifle_id is None else "Edit Firearm")
        self.setMinimumSize(900, 700)

        self.init_ui()

        if rifle_id:
            self.load_rifle_data()

    def init_ui(self):
        """Initialize UI with tabs"""
        layout = QVBoxLayout()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_basic_tab(), "Basic")
        self.tabs.addTab(self.create_barrel_tab(), "Barrel")
        self.tabs.addTab(self.create_chamber_tab(), "Chamber & Twist")
        self.tabs.addTab(self.create_precision_tab(), "Precision")
        self.tabs.addTab(self.create_status_tab(), "Status & Condition")

        layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.save_rifle)
        self.btn_save.setProperty("variant", "primary")

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setProperty("variant", "ghost")

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def create_basic_tab(self):
        """Create basic information tab"""
        widget = QWidget()
        layout = QFormLayout()

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. 'My 6.5 Creedmoor'")
        layout.addRow("Name:", self.input_name)

        self.input_manufacturer = QLineEdit()
        self.input_manufacturer.setPlaceholderText("e.g. 'Tikka', 'Remington', 'Sauer'")
        layout.addRow("Manufacturer:", self.input_manufacturer)

        self.input_model = QLineEdit()
        self.input_model.setPlaceholderText("e.g. 'T3x', '700', '100'")
        layout.addRow("Model:", self.input_model)

        self.input_caliber = QComboBox()
        self.input_caliber.setEditable(True)
        calibers = [
            ".223 Rem",
            "5.56 NATO",
            ".22-250",
            ".243 Win",
            "6mm Creedmoor",
            "6mm BR",
            "6.5 Creedmoor",
            "6.5x55 Swedish",
            ".260 Rem",
            "6.5 PRC",
            ".270 Win",
            "7mm-08",
            "7mm Rem Mag",
            ".308 Win",
            ".30-06",
            ".300 Win Mag",
            ".338 Lapua Mag",
        ]
        self.input_caliber.addItems(calibers)
        layout.addRow("Caliber:", self.input_caliber)

        self.input_action = QComboBox()
        self.input_action.addItems(
            ["bolt", "semi-auto", "lever", "single-shot", "pump"]
        )
        layout.addRow("Action Type:", self.input_action)

        self.input_serial = QLineEdit()
        self.input_serial.setPlaceholderText("Serial number")
        layout.addRow("Serial Number:", self.input_serial)

        self.input_purchase_date = QDateEdit()
        self.input_purchase_date.setDate(QDate.currentDate())
        self.input_purchase_date.setCalendarPopup(True)
        layout.addRow("Purchase Date:", self.input_purchase_date)

        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(100)
        self.input_notes.setPlaceholderText("Notes...")
        layout.addRow("Notes:", self.input_notes)

        widget.setLayout(layout)
        return widget

    def create_barrel_tab(self):
        """Create barrel specifications tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Barrel Profile Selection
        profile_group = QGroupBox("Barrel Profile")
        profile_group.setProperty("variant", "panel")
        profile_layout = QFormLayout()

        self.input_barrel_profile = QComboBox()
        profiles = self.db.execute_query(
            "SELECT id, name, category, stiffness_rating FROM barrel_profiles ORDER BY name"
        )
        self.input_barrel_profile.addItem("-- Select Profile --", None)
        for profile in profiles:
            display_text = f"{profile['name']} ({profile['category']}, {profile['stiffness_rating']})"
            self.input_barrel_profile.addItem(display_text, profile["id"])
        self.input_barrel_profile.currentIndexChanged.connect(self.on_profile_selected)
        profile_layout.addRow("Profile:", self.input_barrel_profile)

        self.input_barrel_contour = QComboBox()
        self.input_barrel_contour.setEditable(True)
        contours = [
            "light",
            "medium",
            "heavy",
            "varmint",
            "bull",
            "sendero",
            "palma",
            "custom",
        ]
        self.input_barrel_contour.addItems(contours)
        profile_layout.addRow("Contour:", self.input_barrel_contour)

        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        # Dimensions
        dim_group = QGroupBox("Dimensjoner")
        dim_group.setProperty("variant", "panel")
        dim_layout = QFormLayout()

        self.input_barrel_length = QDoubleSpinBox()
        self.input_barrel_length.setRange(10, 50)
        self.input_barrel_length.setValue(24)
        self.input_barrel_length.setSuffix(' "')
        self.input_barrel_length.setDecimals(1)
        dim_layout.addRow("Barrel Length:", self.input_barrel_length)

        self.input_muzzle_diameter = QDoubleSpinBox()
        self.input_muzzle_diameter.setRange(0.5, 2.0)
        self.input_muzzle_diameter.setValue(0.75)
        self.input_muzzle_diameter.setSuffix(' "')
        self.input_muzzle_diameter.setDecimals(3)
        dim_layout.addRow("Muzzle Diameter:", self.input_muzzle_diameter)

        self.input_breech_diameter = QDoubleSpinBox()
        self.input_breech_diameter.setRange(0.8, 2.0)
        self.input_breech_diameter.setValue(1.2)
        self.input_breech_diameter.setSuffix(' "')
        self.input_breech_diameter.setDecimals(3)
        dim_layout.addRow("Breech Diameter:", self.input_breech_diameter)

        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)

        # Material & Finish
        mat_group = QGroupBox("Material & Finish")
        mat_group.setProperty("variant", "panel")
        mat_layout = QFormLayout()

        self.input_barrel_material = QComboBox()
        self.input_barrel_material.addItems(
            ["chrome-moly", "stainless", "carbon-fiber"]
        )
        mat_layout.addRow("Material:", self.input_barrel_material)

        self.input_barrel_finish = QComboBox()
        self.input_barrel_finish.setEditable(True)
        self.input_barrel_finish.addItems(
            ["blued", "stainless", "cerakote", "nitride", "parkerized"]
        )
        mat_layout.addRow("Finish:", self.input_barrel_finish)

        self.input_barrel_manufacturer = QLineEdit()
        self.input_barrel_manufacturer.setPlaceholderText(
            "e.g. 'Bartlein', 'Krieger', 'Proof'"
        )
        mat_layout.addRow("Barrel Manufacturer:", self.input_barrel_manufacturer)

        mat_group.setLayout(mat_layout)
        layout.addWidget(mat_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_chamber_tab(self):
        """Create chamber & twist specifications tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Twist Rate
        twist_group = QGroupBox("Twist Rate & Rifling")
        twist_group.setProperty("variant", "panel")
        twist_layout = QFormLayout()

        self.input_twist_rate = QComboBox()
        self.input_twist_rate.setEditable(True)
        twist_rates = [
            "1:7",
            "1:7.5",
            "1:8",
            "1:8.5",
            "1:9",
            "1:9.5",
            "1:10",
            "1:11",
            "1:12",
            "1:14",
        ]
        self.input_twist_rate.addItems(twist_rates)
        twist_layout.addRow("Twist Rate:", self.input_twist_rate)

        self.input_twist_direction = QComboBox()
        self.input_twist_direction.addItems(["right", "left"])
        twist_layout.addRow("Twist Direction:", self.input_twist_direction)

        self.input_rifling_type = QComboBox()
        self.input_rifling_type.setEditable(True)
        self.input_rifling_type.addItems(
            ["conventional", "polygonal", "5R", "button", "cut", "broach"]
        )
        twist_layout.addRow("Rifling Type:", self.input_rifling_type)

        twist_group.setLayout(twist_layout)
        layout.addWidget(twist_group)

        # Chamber
        chamber_group = QGroupBox("Chamber Details")
        chamber_group.setProperty("variant", "panel")
        chamber_layout = QFormLayout()

        self.input_chamber_spec = QComboBox()
        self.input_chamber_spec.addItems(["SAAMI", "CIP", "match", "custom", "minimum"])
        chamber_layout.addRow("Chamber Spec:", self.input_chamber_spec)

        self.input_freebore = QDoubleSpinBox()
        self.input_freebore.setRange(0, 10)
        self.input_freebore.setValue(0)
        self.input_freebore.setSuffix(" mm")
        self.input_freebore.setDecimals(2)
        chamber_layout.addRow("Freebore:", self.input_freebore)

        self.input_throat_angle = QDoubleSpinBox()
        self.input_throat_angle.setRange(0, 5)
        self.input_throat_angle.setValue(1.5)
        self.input_throat_angle.setSuffix(" °")
        self.input_throat_angle.setDecimals(1)
        chamber_layout.addRow("Throat Angle:", self.input_throat_angle)

        self.input_max_coal = QDoubleSpinBox()
        self.input_max_coal.setRange(40, 100)
        self.input_max_coal.setValue(70)
        self.input_max_coal.setSuffix(" mm")
        self.input_max_coal.setDecimals(2)
        chamber_layout.addRow("Max COAL (Magazine):", self.input_max_coal)

        chamber_group.setLayout(chamber_layout)
        layout.addWidget(chamber_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_precision_tab(self):
        """Create precision profile tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        hint = QLabel(
            "Advanced profile fields provide better precision and safety calculations."
        )
        hint.setProperty("role", "muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        limits_group = QGroupBox("Safety Limits")
        limits_group.setProperty("variant", "panel")
        limits_layout = QFormLayout()

        self.input_pressure_limit = QDoubleSpinBox()
        self.input_pressure_limit.setRange(0, 100000)
        self.input_pressure_limit.setDecimals(0)
        self.input_pressure_limit.setSuffix(" PSI")
        limits_layout.addRow("Max pressure override:", self.input_pressure_limit)

        self.input_magazine_length = QDoubleSpinBox()
        self.input_magazine_length.setRange(40, 120)
        self.input_magazine_length.setDecimals(2)
        self.input_magazine_length.setSuffix(" mm")
        limits_layout.addRow("Magazine length:", self.input_magazine_length)

        self.input_scope_height = QDoubleSpinBox()
        self.input_scope_height.setRange(0, 120)
        self.input_scope_height.setDecimals(1)
        self.input_scope_height.setSuffix(" mm")
        limits_layout.addRow("Scope height:", self.input_scope_height)

        self.input_zero_distance = QSpinBox()
        self.input_zero_distance.setRange(25, 1000)
        self.input_zero_distance.setSuffix(" m")
        self.input_zero_distance.setValue(100)
        limits_layout.addRow("Zero distance:", self.input_zero_distance)

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        # ── Optics / Click presets ──────────────────────────────────────────────
        optics_group = QGroupBox("Optikk-presets (klikk)")
        optics_group.setProperty("variant", "panel")
        optics_layout = QFormLayout()

        # Click value row with presets
        click_row = QHBoxLayout()
        self.input_click_value = QDoubleSpinBox()
        self.input_click_value.setRange(0.01, 5.0)
        self.input_click_value.setDecimals(4)
        self.input_click_value.setValue(0.25)
        self.input_click_value.setSuffix(" MOA")
        self.input_click_value.setToolTip("Verdi per klikk på høyde/side (MOA)")
        click_row.addWidget(self.input_click_value, 1)
        for label, val in [
            ("¼ MOA", 0.25),
            ("⅛ MOA", 0.125),
            ("0.1 mil", 0.3438),
            ("1 MOA", 1.0),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setProperty("variant", "ghost")
            btn.clicked.connect(lambda _, v=val: self.input_click_value.setValue(v))
            click_row.addWidget(btn)
        optics_layout.addRow("Klikk-verdi:", click_row)

        # Clicks per revolution row with presets
        cpr_row = QHBoxLayout()
        self.input_clicks_per_revolution = QSpinBox()
        self.input_clicks_per_revolution.setRange(1, 500)
        self.input_clicks_per_revolution.setValue(40)
        self.input_clicks_per_revolution.setToolTip(
            "Antall klikk per omdreing på turret"
        )
        cpr_row.addWidget(self.input_clicks_per_revolution, 1)
        for label, val in [
            ("10", 10),
            ("15", 15),
            ("20", 20),
            ("40", 40),
            ("100", 100),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setProperty("variant", "ghost")
            btn.clicked.connect(
                lambda _, v=val: self.input_clicks_per_revolution.setValue(v)
            )
            cpr_row.addWidget(btn)
        optics_layout.addRow("Klikk/omdr.:", cpr_row)

        optics_group.setLayout(optics_layout)
        layout.addWidget(optics_group)

        geometry_group = QGroupBox("Chamber Geometry")
        geometry_group.setProperty("variant", "panel")
        geometry_layout = QFormLayout()

        self.input_land_diameter = QDoubleSpinBox()
        self.input_land_diameter.setRange(0, 20)
        self.input_land_diameter.setDecimals(3)
        self.input_land_diameter.setSuffix(" mm")
        geometry_layout.addRow("Land diameter:", self.input_land_diameter)

        self.input_groove_diameter = QDoubleSpinBox()
        self.input_groove_diameter.setRange(0, 20)
        self.input_groove_diameter.setDecimals(3)
        self.input_groove_diameter.setSuffix(" mm")
        geometry_layout.addRow("Groove diameter:", self.input_groove_diameter)

        self.input_chamber_neck_diameter = QDoubleSpinBox()
        self.input_chamber_neck_diameter.setRange(0, 20)
        self.input_chamber_neck_diameter.setDecimals(3)
        self.input_chamber_neck_diameter.setSuffix(" mm")
        geometry_layout.addRow("Chamber neck:", self.input_chamber_neck_diameter)

        self.input_headspace_go = QDoubleSpinBox()
        self.input_headspace_go.setRange(0, 100)
        self.input_headspace_go.setDecimals(3)
        self.input_headspace_go.setSuffix(" mm")
        geometry_layout.addRow("Headspace GO:", self.input_headspace_go)

        self.input_headspace_no_go = QDoubleSpinBox()
        self.input_headspace_no_go.setRange(0, 100)
        self.input_headspace_no_go.setDecimals(3)
        self.input_headspace_no_go.setSuffix(" mm")
        geometry_layout.addRow("Headspace NO-GO:", self.input_headspace_no_go)

        geometry_group.setLayout(geometry_layout)
        layout.addWidget(geometry_group)

        self.input_profile_notes = QTextEdit()
        self.input_profile_notes.setMaximumHeight(80)
        self.input_profile_notes.setPlaceholderText("Profile notes...")
        layout.addWidget(self.input_profile_notes)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_status_tab(self):
        """Create status & condition tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Round Count
        count_group = QGroupBox("Round Count")
        count_group.setProperty("variant", "panel")
        count_layout = QFormLayout()

        self.input_round_count = QSpinBox()
        self.input_round_count.setRange(0, 50000)
        self.input_round_count.setValue(0)
        self.input_round_count.setSuffix(" shots")
        count_layout.addRow("Total Shots Fired:", self.input_round_count)

        self.input_accuracy_life = QSpinBox()
        self.input_accuracy_life.setRange(500, 10000)
        self.input_accuracy_life.setValue(2000)
        self.input_accuracy_life.setSuffix(" shots")
        count_layout.addRow("Estimated Barrel Life:", self.input_accuracy_life)

        count_group.setLayout(count_layout)
        layout.addWidget(count_group)

        # Condition
        cond_group = QGroupBox("Tilstand")
        cond_group.setProperty("variant", "panel")
        cond_layout = QFormLayout()

        self.input_bore_condition = QComboBox()
        self.input_bore_condition.addItems(["excellent", "good", "fair", "worn"])
        cond_layout.addRow("Bore Condition:", self.input_bore_condition)

        self.input_throat_erosion = QDoubleSpinBox()
        self.input_throat_erosion.setRange(0, 5)
        self.input_throat_erosion.setValue(0)
        self.input_throat_erosion.setSuffix(" mm")
        self.input_throat_erosion.setDecimals(2)
        cond_layout.addRow("Throat Erosion:", self.input_throat_erosion)

        self.input_accuracy_baseline = QDoubleSpinBox()
        self.input_accuracy_baseline.setRange(0.1, 5)
        self.input_accuracy_baseline.setValue(1.0)
        self.input_accuracy_baseline.setSuffix(" MOA")
        self.input_accuracy_baseline.setDecimals(2)
        cond_layout.addRow("Baseline Accuracy:", self.input_accuracy_baseline)

        cond_group.setLayout(cond_layout)
        layout.addWidget(cond_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_profile_selected(self, index):
        """When barrel profile is selected, populate fields"""
        profile_id = self.input_barrel_profile.currentData()
        if profile_id is None:
            return

        profile = self.db.get_by_id("barrel_profiles", profile_id)
        if profile:
            self.input_muzzle_diameter.setValue(
                profile.get("muzzle_diameter_inches", 0.75)
            )
            self.input_breech_diameter.setValue(
                profile.get("breech_diameter_inches", 1.2)
            )

            # Set contour based on profile name
            contour = profile.get("name", "").lower()
            if "sporter" in contour:
                self.input_barrel_contour.setCurrentText("medium")
            elif "varmint" in contour:
                self.input_barrel_contour.setCurrentText("varmint")
            elif "bull" in contour:
                self.input_barrel_contour.setCurrentText("bull")
            elif "palma" in contour:
                self.input_barrel_contour.setCurrentText("palma")

    def load_rifle_data(self):
        """Load existing rifle data"""
        rifle = self.db.get_by_id("rifles", self.rifle_id)
        if not rifle:
            return

        # Basic tab
        self.input_name.setText(rifle.get("name", ""))
        self.input_manufacturer.setText(rifle.get("manufacturer", ""))
        self.input_model.setText(rifle.get("model", ""))
        self.input_caliber.setCurrentText(rifle.get("caliber", ""))
        self.input_action.setCurrentText(rifle.get("action_type", "bolt"))
        self.input_serial.setText(rifle.get("serial_number", ""))

        if rifle.get("purchase_date"):
            date = QDate.fromString(rifle["purchase_date"], "yyyy-MM-dd")
            self.input_purchase_date.setDate(date)

        self.input_notes.setPlainText(rifle.get("notes", ""))

        # Barrel tab
        if rifle.get("barrel_profile_id"):
            for i in range(self.input_barrel_profile.count()):
                if self.input_barrel_profile.itemData(i) == rifle["barrel_profile_id"]:
                    self.input_barrel_profile.setCurrentIndex(i)
                    break

        self.input_barrel_contour.setCurrentText(rifle.get("barrel_contour", "medium"))
        self.input_barrel_length.setValue(rifle.get("barrel_length_inches", 24.0))
        self.input_muzzle_diameter.setValue(
            rifle.get("muzzle_diameter_mm", 19.05) / 25.4
        )
        self.input_breech_diameter.setValue(
            rifle.get("breech_diameter_mm", 30.48) / 25.4
        )
        self.input_barrel_material.setCurrentText(
            rifle.get("barrel_material", "stainless")
        )
        self.input_barrel_finish.setCurrentText(rifle.get("barrel_finish", "stainless"))
        self.input_barrel_manufacturer.setText(rifle.get("barrel_manufacturer", ""))

        # Chamber tab
        self.input_twist_rate.setCurrentText(rifle.get("twist_rate", "1:8"))
        self.input_twist_direction.setCurrentText(rifle.get("twist_direction", "right"))
        self.input_rifling_type.setCurrentText(
            rifle.get("rifling_type", "conventional")
        )
        self.input_chamber_spec.setCurrentText(rifle.get("chamber_spec", "SAAMI"))
        self.input_freebore.setValue(rifle.get("freebore_mm", 0))
        self.input_throat_angle.setValue(rifle.get("throat_angle_deg", 1.5))
        self.input_max_coal.setValue(rifle.get("max_coal_magazine_mm", 70))

        # Status tab
        self.input_round_count.setValue(rifle.get("round_count", 0) or 0)
        self.input_accuracy_life.setValue(
            rifle.get("accuracy_life_estimate", 2000) or 2000
        )
        self.input_bore_condition.setCurrentText(
            rifle.get("bore_condition", "excellent")
        )
        self.input_throat_erosion.setValue(rifle.get("throat_erosion_mm", 0) or 0)
        self.input_accuracy_baseline.setValue(
            rifle.get("accuracy_baseline_moa", 1.0) or 1.0
        )

        self.load_precision_profile()

    def _read_precision_profile(self) -> Dict[str, Any]:
        details: Dict[str, Any] = {}
        if not self.rifle_id:
            return details
        try:
            rows = self.db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (self.rifle_id,),
            )
            if rows and rows[0].get("profile_json"):
                details = json.loads(rows[0]["profile_json"])
        except Exception:
            details = {}
        return details

    def load_precision_profile(self) -> None:
        details = self._read_precision_profile()
        try:
            self.input_pressure_limit.setValue(
                float(details.get("pressure_limit_psi") or 0)
            )
            self.input_magazine_length.setValue(
                float(details.get("magazine_length_mm") or 0)
            )
            self.input_scope_height.setValue(float(details.get("scope_height_mm") or 0))
            self.input_zero_distance.setValue(
                int(details.get("zero_distance_m") or 100)
            )
            self.input_click_value.setValue(
                float(details.get("click_value_moa") or 0.25)
            )
            self.input_clicks_per_revolution.setValue(
                int(details.get("clicks_per_revolution") or 40)
            )
            self.input_land_diameter.setValue(
                float(details.get("land_diameter_mm") or 0)
            )
            self.input_groove_diameter.setValue(
                float(details.get("groove_diameter_mm") or 0)
            )
            self.input_chamber_neck_diameter.setValue(
                float(details.get("chamber_neck_diameter_mm") or 0)
            )
            self.input_headspace_go.setValue(float(details.get("headspace_go_mm") or 0))
            self.input_headspace_no_go.setValue(
                float(details.get("headspace_no_go_mm") or 0)
            )
            self.input_profile_notes.setPlainText(details.get("notes") or "")
        except Exception:
            pass

    def _save_precision_profile(self, rifle_id: int) -> None:
        def _float_or_none(value: float) -> Optional[float]:
            try:
                fval = float(value)
            except Exception:
                return None
            return None if abs(fval) < 1e-6 else fval

        def _int_or_none(value: int) -> Optional[int]:
            try:
                ival = int(value)
            except Exception:
                return None
            return None if ival == 0 else ival

        profile = {
            "pressure_limit_psi": _float_or_none(self.input_pressure_limit.value()),
            "magazine_length_mm": _float_or_none(self.input_magazine_length.value()),
            "scope_height_mm": _float_or_none(self.input_scope_height.value()),
            "zero_distance_m": _int_or_none(self.input_zero_distance.value()),
            "click_value_moa": _float_or_none(self.input_click_value.value()),
            "clicks_per_revolution": _int_or_none(
                self.input_clicks_per_revolution.value()
            ),
            "land_diameter_mm": _float_or_none(self.input_land_diameter.value()),
            "groove_diameter_mm": _float_or_none(self.input_groove_diameter.value()),
            "chamber_neck_diameter_mm": _float_or_none(
                self.input_chamber_neck_diameter.value()
            ),
            "headspace_go_mm": _float_or_none(self.input_headspace_go.value()),
            "headspace_no_go_mm": _float_or_none(self.input_headspace_no_go.value()),
            "notes": (self.input_profile_notes.toPlainText() or "").strip() or None,
        }

        clean = {k: v for k, v in profile.items() if v is not None}
        try:
            payload = json.dumps(clean)
        except Exception:
            payload = "{}"

        try:
            cur = self.db.cursor
            cur.execute(
                """
                INSERT INTO rifle_profile_details (rifle_id, profile_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(rifle_id) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (rifle_id, payload),
            )
            self.db.conn.commit()
        except Exception:
            pass

    def save_rifle(self):
        """Save rifle to database"""
        data = {
            "name": self.input_name.text(),
            "manufacturer": self.input_manufacturer.text(),
            "model": self.input_model.text(),
            "caliber": self.input_caliber.currentText(),
            "action_type": self.input_action.currentText(),
            "serial_number": self.input_serial.text(),
            "purchase_date": self.input_purchase_date.date().toString("yyyy-MM-dd"),
            "notes": self.input_notes.toPlainText(),
            # Barrel
            "barrel_profile_id": self.input_barrel_profile.currentData(),
            "barrel_contour": self.input_barrel_contour.currentText(),
            "barrel_length_inches": self.input_barrel_length.value(),
            "barrel_length_mm": self.input_barrel_length.value() * 25.4,
            "muzzle_diameter_mm": self.input_muzzle_diameter.value() * 25.4,
            "breech_diameter_mm": self.input_breech_diameter.value() * 25.4,
            "barrel_material": self.input_barrel_material.currentText(),
            "barrel_finish": self.input_barrel_finish.currentText(),
            "barrel_manufacturer": self.input_barrel_manufacturer.text(),
            # Chamber & Twist
            "twist_rate": self.input_twist_rate.currentText(),
            "twist_direction": self.input_twist_direction.currentText(),
            "rifling_type": self.input_rifling_type.currentText(),
            "chamber_spec": self.input_chamber_spec.currentText(),
            "freebore_mm": self.input_freebore.value(),
            "throat_angle_deg": self.input_throat_angle.value(),
            "max_coal_magazine_mm": self.input_max_coal.value(),
            # Status
            "round_count": self.input_round_count.value(),
            "accuracy_life_estimate": self.input_accuracy_life.value(),
            "bore_condition": self.input_bore_condition.currentText(),
            "throat_erosion_mm": self.input_throat_erosion.value(),
            "accuracy_baseline_moa": self.input_accuracy_baseline.value(),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Validation
        if not data["name"]:
            QMessageBox.warning(self, "Missing Name", "Please enter a name.")
            return

        if not data["caliber"]:
            QMessageBox.warning(self, "Missing Caliber", "Please select a caliber.")
            return

        if self.rifle_id:
            self.db.update("rifles", data, "id = ?", (self.rifle_id,))
            self._save_precision_profile(self.rifle_id)
            QMessageBox.information(
                self, "Lagret", f"Våpen '{data['name']}' oppdatert!"
            )
            self.accept()
        else:
            data["created_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = self.db.insert("rifles", data)
            if new_id is None:
                QMessageBox.critical(
                    self, "Feil", "Kunne ikke lagre våpenet. Sjekk loggen for detaljer."
                )
                return
            self._save_precision_profile(new_id)
            self.rifle_id = new_id
            QMessageBox.information(self, "Lagret", f"Våpen '{data['name']}' lagret!")
            self.accept()


class RifleDetailsDialog(QDialog):
    """
    View comprehensive rifle details
    """

    def __init__(self, parent=None, rifle_id: Optional[int] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle_id = rifle_id

        self.setWindowTitle("Firearm Details")
        self.setMinimumSize(800, 600)

        self.init_ui()
        self.load_details()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_info_tab(), "Info")
        self.tabs.addTab(self.create_harmonics_tab(), "Harmonics")
        self.tabs.addTab(self.create_bullet_jump_tab(), "Bullet Jump")
        self.tabs.addTab(self.create_accuracy_tests_tab(), "Accuracy Tests")
        self.tabs.addTab(self.create_maintenance_tab(), "Maintenance")

        layout.addWidget(self.tabs)

        btn_close = QPushButton("Close")
        btn_close.setProperty("variant", "ghost")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def create_info_tab(self):
        """Create info display tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        layout.addWidget(self.info_display)

        widget.setLayout(layout)
        return widget

    def create_harmonics_tab(self):
        """Create harmonics analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Harmonic Analysis")
        label.setProperty("variant", "cardTitle")
        layout.addWidget(label)

        self.harmonics_display = QTextEdit()
        self.harmonics_display.setReadOnly(True)
        layout.addWidget(self.harmonics_display)

        widget.setLayout(layout)
        return widget

    def create_bullet_jump_tab(self):
        """Create bullet jump measurements tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Bullet Jump Measurements")
        label.setProperty("variant", "cardTitle")
        layout.addWidget(label)

        self.bullet_jump_table = QTableWidget()
        self.bullet_jump_table.setColumnCount(7)
        self.bullet_jump_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Bullet",
                "Barrel",
                "Jam COAL",
                "Jam CBTO",
                "Method",
                "Shots at Measurement",
            ]
        )
        layout.addWidget(self.bullet_jump_table)

        widget.setLayout(layout)
        return widget

    def create_accuracy_tests_tab(self):
        """Create accuracy tests tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Accuracy Tests")
        label.setProperty("variant", "cardTitle")
        layout.addWidget(label)

        self.accuracy_table = QTableWidget()
        self.accuracy_table.setColumnCount(6)
        self.accuracy_table.setHorizontalHeaderLabels(
            ["Date", "Shots in Test", "Avg MOA", "ES fps", "SD fps", "Groups"]
        )
        layout.addWidget(self.accuracy_table)

        widget.setLayout(layout)
        return widget

    def create_maintenance_tab(self):
        """Create maintenance log tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Maintenance Log")
        label.setProperty("variant", "cardTitle")
        layout.addWidget(label)

        self.maintenance_table = QTableWidget()
        self.maintenance_table.setColumnCount(5)
        self.maintenance_table.setHorizontalHeaderLabels(
            ["Date", "Type", "Shots", "Bore Condition", "Notes"]
        )
        layout.addWidget(self.maintenance_table)

        widget.setLayout(layout)
        return widget

    def load_details(self):
        """Load rifle details"""
        rifle = self.db.get_by_id("rifles", self.rifle_id)
        if not rifle:
            return

        profile_details = {}
        try:
            rows = self.db.execute_query(
                "SELECT profile_json FROM rifle_profile_details WHERE rifle_id = ?",
                (self.rifle_id,),
            )
            if rows and rows[0].get("profile_json"):
                profile_details = json.loads(rows[0]["profile_json"])
        except Exception:
            profile_details = {}

        def _fmt(value, suffix=""):
            return f"{value}{suffix}" if value is not None else "-"

        if profile_details:
            precision_html = f"""
            <h3>Precision Profile</h3>
            <ul>
                <li><b>Max pressure override:</b> {_fmt(profile_details.get('pressure_limit_psi'), ' PSI')}</li>
                <li><b>Magazine length:</b> {_fmt(profile_details.get('magazine_length_mm'), ' mm')}</li>
                <li><b>Scope height:</b> {_fmt(profile_details.get('scope_height_mm'), ' mm')}</li>
                <li><b>Zero distance:</b> {_fmt(profile_details.get('zero_distance_m'), ' m')}</li>
                <li><b>Land diameter:</b> {_fmt(profile_details.get('land_diameter_mm'), ' mm')}</li>
                <li><b>Groove diameter:</b> {_fmt(profile_details.get('groove_diameter_mm'), ' mm')}</li>
                <li><b>Chamber neck:</b> {_fmt(profile_details.get('chamber_neck_diameter_mm'), ' mm')}</li>
                <li><b>Headspace GO:</b> {_fmt(profile_details.get('headspace_go_mm'), ' mm')}</li>
                <li><b>Headspace NO-GO:</b> {_fmt(profile_details.get('headspace_no_go_mm'), ' mm')}</li>
            </ul>
            """
        else:
            precision_html = (
                "<h3>Precision Profile</h3><p>No precision profile is registered.</p>"
            )

        chamber_comparison_html = build_chamber_comparison_html(
            self.db, rifle, profile_details
        )

        # Info tab
        info_html = f"""
        <h2>{rifle.get('name', 'N/A')}</h2>
        <h3>Basic Info</h3>
        <ul>
            <li><b>Manufacturer:</b> {rifle.get('manufacturer', '-')}</li>
            <li><b>Model:</b> {rifle.get('model', '-')}</li>
            <li><b>Caliber:</b> {rifle.get('caliber', '-')}</li>
            <li><b>Action:</b> {rifle.get('action_type', '-')}</li>
            <li><b>Serial Number:</b> {rifle.get('serial_number', '-')}</li>
        </ul>

        <h3>Barrel Details</h3>
        <ul>
            <li><b>Length:</b> {rifle.get('barrel_length_inches', 0):.1f}" / {rifle.get('barrel_length_mm', 0):.1f} mm</li>
            <li><b>Contour:</b> {rifle.get('barrel_contour', '-')}</li>
            <li><b>Material:</b> {rifle.get('barrel_material', '-')}</li>
            <li><b>Finish:</b> {rifle.get('barrel_finish', '-')}</li>
            <li><b>Twist Rate:</b> {rifle.get('twist_rate', '-')} ({rifle.get('twist_direction', 'right')})</li>
            <li><b>Rifling:</b> {rifle.get('rifling_type', '-')}</li>
        </ul>

        <h3>Status</h3>
        <ul>
            <li><b>Shots Fired:</b> {rifle.get('round_count', 0)} / {rifle.get('accuracy_life_estimate', 0)} estimated</li>
            <li><b>Bore Condition:</b> {rifle.get('bore_condition', '-')}</li>
            <li><b>Throat Erosion:</b> {rifle.get('throat_erosion_mm', 0):.2f} mm</li>
            <li><b>Baseline Accuracy:</b> {rifle.get('accuracy_baseline_moa', 0):.2f} MOA</li>
        </ul>
        {precision_html}
        {chamber_comparison_html}
        """

        self.info_display.setHtml(info_html)

        # Harmonics tab
        harmonics_html = build_harmonics_html(rifle, profile_details)

        self.harmonics_display.setHtml(harmonics_html)

        # Bullet Jump tab
        jump_measurements = self.db.execute_query(
            """SELECT * FROM rifle_bullet_jump_measurements
               WHERE rifle_id = ?
               ORDER BY CASE WHEN barrel_id IS NULL OR barrel_id = '' THEN 1 ELSE 0 END,
                        measurement_date DESC""",
            (self.rifle_id,),
        )

        self.bullet_jump_table.setRowCount(len(jump_measurements))
        for row, meas in enumerate(jump_measurements):
            self.bullet_jump_table.setItem(
                row, 0, QTableWidgetItem(meas.get("measurement_date", "-"))
            )

            # Get bullet name
            bullet = self.db.get_by_id("bullets", meas.get("bullet_id"))
            bullet_name = (
                f"{bullet['name']}" if bullet else f"ID: {meas.get('bullet_id')}"
            )
            self.bullet_jump_table.setItem(row, 1, QTableWidgetItem(bullet_name))
            self.bullet_jump_table.setItem(
                row,
                2,
                QTableWidgetItem(describe_jump_measurement_barrel(meas)),
            )

            self.bullet_jump_table.setItem(
                row, 3, QTableWidgetItem(f"{meas.get('jam_coal_mm', 0):.2f} mm")
            )
            self.bullet_jump_table.setItem(
                row, 4, QTableWidgetItem(f"{meas.get('jam_cbto_mm', 0):.2f} mm")
            )
            self.bullet_jump_table.setItem(
                row, 5, QTableWidgetItem(meas.get("measurement_method", "-"))
            )
            self.bullet_jump_table.setItem(
                row,
                6,
                QTableWidgetItem(str(meas.get("rounds_fired_at_measurement", 0))),
            )

        # Accuracy Tests tab
        accuracy_tests = self.db.execute_query(
            "SELECT * FROM rifle_accuracy_tests WHERE rifle_id = ? ORDER BY test_date DESC LIMIT 10",
            (self.rifle_id,),
        )

        self.accuracy_table.setRowCount(len(accuracy_tests))
        for row, test in enumerate(accuracy_tests):
            self.accuracy_table.setItem(
                row, 0, QTableWidgetItem(test.get("test_date", "-"))
            )
            self.accuracy_table.setItem(
                row, 1, QTableWidgetItem(str(test.get("round_count_at_test", 0)))
            )

            avg_moa = test.get("average_moa", 0)
            moa_item = QTableWidgetItem(f"{avg_moa:.3f}" if avg_moa else "-")
            if avg_moa:
                if avg_moa < 0.5:
                    moa_item.setForeground(QColor("#27ae60"))
                elif avg_moa < 1.0:
                    moa_item.setForeground(QColor("#3498db"))
                elif avg_moa < 1.5:
                    moa_item.setForeground(QColor("#f39c12"))
            self.accuracy_table.setItem(row, 2, moa_item)

            self.accuracy_table.setItem(
                row, 3, QTableWidgetItem(str(test.get("extreme_spread_fps", 0) or "-"))
            )
            self.accuracy_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    f"{test.get('standard_deviation_fps', 0):.1f}"
                    if test.get("standard_deviation_fps")
                    else "-"
                ),
            )
            self.accuracy_table.setItem(
                row, 5, QTableWidgetItem(str(test.get("groups_fired", 0)))
            )

        # Maintenance tab
        maintenance_logs = self.db.execute_query(
            "SELECT * FROM rifle_maintenance_log WHERE rifle_id = ? ORDER BY maintenance_date DESC LIMIT 20",
            (self.rifle_id,),
        )

        self.maintenance_table.setRowCount(len(maintenance_logs))
        for row, log in enumerate(maintenance_logs):
            self.maintenance_table.setItem(
                row, 0, QTableWidgetItem(log.get("maintenance_date", "-"))
            )
            self.maintenance_table.setItem(
                row, 1, QTableWidgetItem(log.get("maintenance_type", "-"))
            )
            self.maintenance_table.setItem(
                row, 2, QTableWidgetItem(str(log.get("rounds_fired_before", 0)))
            )
            self.maintenance_table.setItem(
                row, 3, QTableWidgetItem(log.get("throat_condition", "-"))
            )
            self.maintenance_table.setItem(
                row, 4, QTableWidgetItem(log.get("notes", "-")[:50])
            )


class AddRoundsFiredDialog(QDialog):
    """Dialog for adding rounds fired"""

    def __init__(self, parent=None, rifle: Optional[Dict] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle = rifle or {}

        self.setWindowTitle(f"Add Shots - {self.rifle.get('name', '')}")
        self.setMinimumWidth(400)

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        form = QFormLayout()

        current_count = self.rifle.get("round_count", 0) or 0
        label = QLabel(f"Current round count: <b>{current_count}</b>")
        layout.addWidget(label)

        self.input_rounds = QSpinBox()
        self.input_rounds.setRange(1, 1000)
        self.input_rounds.setValue(20)
        self.input_rounds.setSuffix(" shots")
        form.addRow("Add shots:", self.input_rounds)

        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(80)
        self.input_notes.setPlaceholderText("Notes about the session...")
        form.addRow("Notes:", self.input_notes)

        layout.addLayout(form)

        # Warning check
        accuracy_life = self.rifle.get("accuracy_life_estimate", 2000)
        new_count = current_count + self.input_rounds.value()

        if new_count >= 500 and (new_count // 500) > (current_count // 500):
            warning = QLabel(
                "You are passing 500 shots. Remember to measure cases for wear."
            )
            warning.setProperty("variant", "callout")
            warning.setWordWrap(True)
            layout.addWidget(warning)

        if new_count > accuracy_life * 0.8:
            warning2 = QLabel(
                f"The barrel is nearing its estimated service life ({accuracy_life} shots)."
            )
            warning2.setProperty("variant", "callout")
            warning2.setWordWrap(True)
            layout.addWidget(warning2)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_rounds)
        btn_save.setProperty("variant", "primary")

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setProperty("variant", "ghost")

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_rounds(self):
        """Save rounds fired"""
        rounds_to_add = self.input_rounds.value()
        current_count = self.rifle.get("round_count", 0) or 0
        new_count = current_count + rounds_to_add

        # Update rifle
        self.db.update(
            "rifles", {"round_count": new_count}, "id = ?", (self.rifle["id"],)
        )

        # Log maintenance entry
        log_data = {
            "rifle_id": self.rifle["id"],
            "maintenance_date": datetime.now().strftime("%Y-%m-%d"),
            "maintenance_type": "shooting_session",
            "rounds_fired_before": current_count,
            "rounds_fired_after": new_count,
            "notes": self.input_notes.toPlainText(),
        }
        self.db.insert("rifle_maintenance_log", log_data)

        QMessageBox.information(
            self, "Saved", f"Round count updated: {current_count} -> {new_count}"
        )

        self.accept()


class MaintenanceLogDialog(QDialog):
    """Dialog for logging maintenance"""

    def __init__(self, parent=None, rifle: Optional[Dict] = None):
        super().__init__(parent)
        self.db = get_database()
        self.rifle = rifle or {}

        self.setWindowTitle(f"Maintenance - {self.rifle.get('name', '')}")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        form = QFormLayout()

        self.input_date = QDateEdit()
        self.input_date.setDate(QDate.currentDate())
        self.input_date.setCalendarPopup(True)
        form.addRow("Date:", self.input_date)

        self.input_type = QComboBox()
        self.input_type.addItems(
            [
                "cleaning",
                "deep_clean",
                "inspection",
                "repair",
                "accuracy_test",
                "barrel_break_in",
            ]
        )
        form.addRow("Type:", self.input_type)

        self.input_bore_cleaned = QCheckBox()
        form.addRow("Barrel cleaned:", self.input_bore_cleaned)

        self.input_carbon_removed = QCheckBox()
        form.addRow("Carbon removed:", self.input_carbon_removed)

        self.input_copper_removed = QCheckBox()
        form.addRow("Copper removed:", self.input_copper_removed)

        self.input_bore_condition = QComboBox()
        self.input_bore_condition.addItems(["excellent", "good", "fair", "worn"])
        self.input_bore_condition.setCurrentText(
            self.rifle.get("bore_condition", "good")
        )
        form.addRow("Bore Condition:", self.input_bore_condition)

        self.input_accuracy = QDoubleSpinBox()
        self.input_accuracy.setRange(0.1, 10)
        self.input_accuracy.setValue(1.0)
        self.input_accuracy.setSuffix(" MOA")
        self.input_accuracy.setDecimals(2)
        form.addRow("Accuracy Test:", self.input_accuracy)

        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(100)
        form.addRow("Notes:", self.input_notes)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_maintenance)
        btn_save.setProperty("variant", "primary")

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setProperty("variant", "ghost")

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_maintenance(self):
        """Save maintenance log"""
        log_data = {
            "rifle_id": self.rifle["id"],
            "maintenance_date": self.input_date.date().toString("yyyy-MM-dd"),
            "maintenance_type": self.input_type.currentText(),
            "rounds_fired_before": self.rifle.get("round_count", 0),
            "bore_cleaned": 1 if self.input_bore_cleaned.isChecked() else 0,
            "carbon_removed": 1 if self.input_carbon_removed.isChecked() else 0,
            "copper_removed": 1 if self.input_copper_removed.isChecked() else 0,
            "bore_condition_rating": ["worn", "fair", "good", "excellent"].index(
                self.input_bore_condition.currentText()
            )
            + 1,
            "throat_condition": self.input_bore_condition.currentText(),
            "accuracy_test_performed": 1,
            "accuracy_result_moa": self.input_accuracy.value(),
            "notes": self.input_notes.toPlainText(),
        }

        self.db.insert("rifle_maintenance_log", log_data)

        # Update rifle
        update_data = {
            "last_maintenance_date": log_data["maintenance_date"],
            "bore_condition": self.input_bore_condition.currentText(),
            "current_accuracy_moa": self.input_accuracy.value(),
        }

        if self.input_bore_cleaned.isChecked():
            update_data["last_cleaning_date"] = log_data["maintenance_date"]
            update_data["last_cleaned_round_count"] = self.rifle.get("round_count", 0)

        self.db.update("rifles", update_data, "id = ?", (self.rifle["id"],))

        QMessageBox.information(self, "Saved", "Maintenance logged!")

        self.accept()
