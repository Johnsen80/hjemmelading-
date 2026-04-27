"""Brass/Case Manager with comprehensive lifecycle tracking."""

from PyQt6.QtCore import QDate, Qt
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
from ..utils.i18n import tr


class BrassManager(QWidget):
    """Main brass/case management widget"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()

        # Header
        header = QLabel(tr("brass_title"), self)
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        info = QLabel(
            tr("brass_subtitle"),
            self,
        )
        info.setWordWrap(True)
        info.setProperty("variant", "cardSubtitle")
        layout.addWidget(info)

        # Toolbar
        toolbar = QHBoxLayout()

        btn_add = QPushButton(tr("brass_new_lot"), self)
        btn_add.setProperty("variant", "primary")
        btn_add.clicked.connect(self.add_case_lot)
        toolbar.addWidget(btn_add)

        btn_fire = QPushButton(tr("brass_log_firing"), self)
        btn_fire.setProperty("variant", "secondary")
        btn_fire.clicked.connect(self.log_firing)
        toolbar.addWidget(btn_fire)

        btn_anneal = QPushButton(tr("brass_log_annealing"), self)
        btn_anneal.setProperty("variant", "secondary")
        btn_anneal.clicked.connect(self.log_annealing)
        toolbar.addWidget(btn_anneal)

        btn_prep = QPushButton(tr("brass_log_prep"), self)
        btn_prep.setProperty("variant", "secondary")
        btn_prep.clicked.connect(self.log_prep)
        toolbar.addWidget(btn_prep)

        btn_measure = QPushButton(tr("brass_add_measurement"), self)
        btn_measure.setProperty("variant", "ghost")
        btn_measure.clicked.connect(self.add_measurement)
        toolbar.addWidget(btn_measure)

        btn_retire = QPushButton(tr("brass_retire_cases"), self)
        btn_retire.setProperty("variant", "ghost")
        btn_retire.clicked.connect(self.retire_cases)
        toolbar.addWidget(btn_retire)

        toolbar.addStretch()

        btn_refresh = QPushButton(tr("bw_refresh"), self)
        btn_refresh.setProperty("variant", "ghost")
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Main table
        self.table = QTableWidget(self)
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                tr("brass_col_lot_name"),
                tr("brass_col_manufacturer"),
                tr("brass_col_caliber"),
                tr("brass_col_quantity"),
                tr("brass_col_times_fired"),
                tr("brass_col_last_annealed"),
                tr("brass_col_anneal_due"),
                tr("brass_col_avg_weight"),
                tr("brass_col_capacity"),
                tr("brass_col_retired"),
                tr("brass_col_status"),
            ]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.view_details)
        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel(tr("status_ready"), self)
        self.status_label.setProperty("role", "muted")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def load_data(self):
        """Load brass lots from database"""
        cases = self.db.execute_query(
            """
            SELECT id, name, manufacturer, caliber, quantity, times_fired,
                   last_annealed, needs_annealing, avg_weight_gr,
                   case_capacity_gr_h2o, retired_quantity, lot_number
            FROM cases
            ORDER BY caliber, manufacturer, name
        """
        )

        self.table.setRowCount(len(cases))

        for i, case in enumerate(cases):
            (
                case_id,
                name,
                manufacturer,
                caliber,
                qty,
                fired,
                annealed,
                needs_anneal,
                weight,
                capacity,
                retired,
                lot,
            ) = case

            # ID (hidden, for selection)
            item_id = QTableWidgetItem(str(case_id))
            item_id.setData(Qt.ItemDataRole.UserRole, case_id)
            self.table.setItem(i, 0, item_id)

            # Lot/Name
            lot_name = f"{lot} - {name}" if lot else name
            self.table.setItem(i, 1, QTableWidgetItem(lot_name))

            # Manufacturer
            self.table.setItem(i, 2, QTableWidgetItem(manufacturer or "-"))

            # Caliber
            self.table.setItem(i, 3, QTableWidgetItem(caliber))

            # Quantity
            self.table.setItem(i, 4, QTableWidgetItem(str(qty)))

            # Times Fired (color-coded)
            fired_item = QTableWidgetItem(str(fired))
            if fired >= 10:
                fired_item.setBackground(QColor("#e74c3c"))  # Red - consider retirement
                fired_item.setForeground(QColor("white"))
            elif fired >= 5:
                fired_item.setBackground(QColor("#f39c12"))  # Orange - watch closely
            elif fired >= 3:
                fired_item.setBackground(QColor("#f9e79f"))  # Yellow - anneal soon
            else:
                fired_item.setBackground(QColor("#d5f4e6"))  # Green - fresh
            self.table.setItem(i, 5, fired_item)

            # Last Annealed
            self.table.setItem(i, 6, QTableWidgetItem(annealed or "Never"))

            # Anneal Due?
            anneal_item = QTableWidgetItem("YES" if needs_anneal else "OK")
            if needs_anneal:
                anneal_item.setBackground(QColor("#f39c12"))
                anneal_item.setForeground(QColor("white"))
            self.table.setItem(i, 7, anneal_item)

            # Avg Weight
            weight_str = f"{weight:.1f}gr" if weight else "-"
            self.table.setItem(i, 8, QTableWidgetItem(weight_str))

            # Capacity
            cap_str = f"{capacity:.1f}gr H2O" if capacity else "-"
            self.table.setItem(i, 9, QTableWidgetItem(cap_str))

            # Retired
            self.table.setItem(i, 10, QTableWidgetItem(str(retired)))

            # Status
            if qty == 0:
                status = "Empty"
            elif fired >= 10:
                status = "Consider Retiring"
            elif needs_anneal:
                status = "Needs Annealing"
            elif fired >= 5:
                status = "Moderate Use"
            else:
                status = "Good"
            self.table.setItem(i, 11, QTableWidgetItem(status))

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 200)  # Lot/Name wider

        # Update status
        total_cases = sum(case[4] for case in cases)  # Sum quantities
        need_anneal = sum(1 for case in cases if case[7])
        self.status_label.setText(
            tr(
                "brass_status_summary",
                lots=len(cases),
                cases=total_cases,
                anneal_due=need_anneal,
            )
        )

    def _ensure_case_exists(self, case_id):
        rows = self.db.execute_query("SELECT id FROM cases WHERE id = ?", (case_id,))
        if rows:
            return True
        QMessageBox.warning(
            self,
            tr("brass_missing_lot_title"),
            tr("brass_missing_lot_message"),
        )
        self.load_data()
        return False

    def add_case_lot(self):
        """Add new case lot"""
        dialog = CaseLotDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            case_id = self.db.insert(
                "cases",
                {
                    "name": data["name"],
                    "manufacturer": data["manufacturer"],
                    "caliber": data["caliber"],
                    "quantity": data["quantity"],
                    "lot_number": data["lot_number"],
                    "purchase_date": data["purchase_date"],
                    "case_capacity_gr_h2o": data["case_capacity"],
                    "avg_weight_gr": data["avg_weight"],
                    "wall_thickness": data["wall_thickness"],
                    "material": data["material"],
                    "notes": data["notes"],
                },
            )
            self.db.refresh_case_learning_profile(case_id)
            self.load_data()
            QMessageBox.information(
                self, tr("msg_success"), tr("brass_lot_added", name=data["name"])
            )

    def log_firing(self):
        """Log firing session (increment times_fired)"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("brass_select_lot_first")
            )
            return

        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        if not self._ensure_case_exists(case_id):
            return

        dialog = FiringLogDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()

            # Update times_fired
            current_rows = self.db.execute_query(
                "SELECT times_fired FROM cases WHERE id = ?", (case_id,)
            )
            if not current_rows:
                QMessageBox.warning(
                    self,
                    tr("brass_missing_lot_title"),
                    tr("brass_missing_lot_message"),
                )
                self.load_data()
                return
            current = current_rows[0][0]

            new_fired = current + 1

            # Check if annealing due (every 3 firings for match brass)
            needs_anneal = new_fired % 3 == 0 and new_fired > 0

            self.db.execute_query(
                """
                UPDATE cases SET
                    times_fired = ?,
                    needs_annealing = ?
                WHERE id = ?
            """,
                (new_fired, needs_anneal, case_id),
            )

            # Log firing event
            self.db.execute_query(
                """
                INSERT INTO case_firing_log (
                    case_id, firing_date, rounds_fired, rifle_id,
                    ammo_profile_id, pressure_level, case_head_expansion_inch,
                    primer_condition, annealing_due, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    data["date"],
                    data["rounds_fired"],
                    data["rifle_id"],
                    data["ammo_id"],
                    data["pressure_level"],
                    data["case_head_expansion"],
                    data["primer_condition"],
                    needs_anneal,
                    data["notes"],
                ),
            )

            self.db.commit()
            self.db.refresh_case_learning_profile(case_id)
            self.load_data()

            msg = f"Skyting logget! Times fired: {new_fired}"
            if needs_anneal:
                msg += "\n\nANNEALING DUE! (hver 3. gang)"
            QMessageBox.information(self, tr("brass_logged_title"), msg)

    def log_annealing(self):
        """Log annealing session"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("brass_select_lot_first")
            )
            return

        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        if not self._ensure_case_exists(case_id):
            return

        dialog = AnnealingLogDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()

            # Update last_annealed and reset needs_annealing
            self.db.execute_query(
                """
                UPDATE cases SET
                    last_annealed = ?,
                    needs_annealing = 0
                WHERE id = ?
            """,
                (data["date"], case_id),
            )

            # Log annealing event
            self.db.execute_query(
                """
                INSERT INTO case_annealing_log (
                    case_id, annealing_date, method, temperature_f,
                    time_seconds, templaq_verified, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    data["date"],
                    data["method"],
                    data["temperature"],
                    data["time_seconds"],
                    data["templaq_verified"],
                    data["notes"],
                ),
            )

            self.db.commit()
            self.db.refresh_case_learning_profile(case_id)
            self.load_data()
            QMessageBox.information(
                self, tr("brass_logged_title"), tr("brass_annealing_logged")
            )

    def log_prep(self):
        """Log case prep (trimming, uniforming, etc.)"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("brass_select_lot_first")
            )
            return

        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        if not self._ensure_case_exists(case_id):
            return

        dialog = PrepLogDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()

            # Update case prep flags
            if data["trimmed"]:
                self.db.execute_query(
                    """
                    UPDATE cases SET
                        last_trimmed_date = ?,
                        trim_length_mm = ?
                    WHERE id = ?
                """,
                    (data["date"], data["trim_length"], case_id),
                )

            if data["primer_pocket_uniformed"]:
                self.db.execute_query(
                    "UPDATE cases SET primer_pocket_uniformed = 1 WHERE id = ?",
                    (case_id,),
                )

            # Log prep event
            self.db.execute_query(
                """
                INSERT INTO case_prep_log (
                    case_id, prep_date, trimmed, trim_length_mm,
                    chamfered, deburred, primer_pocket_uniformed,
                    flash_hole_deburred, neck_turned, neck_thickness_final_mm,
                    weight_sorted, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    data["date"],
                    data["trimmed"],
                    data["trim_length"],
                    data["chamfered"],
                    data["deburred"],
                    data["primer_pocket_uniformed"],
                    data["flash_hole_deburred"],
                    data["neck_turned"],
                    data["neck_thickness"],
                    data["weight_sorted"],
                    data["notes"],
                ),
            )

            self.db.commit()
            self.db.refresh_case_learning_profile(case_id)
            self.load_data()
            QMessageBox.information(
                self, tr("brass_logged_title"), tr("brass_prep_logged")
            )

    def add_measurement(self):
        """Add case measurements"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("brass_select_lot_first")
            )
            return

        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        if not self._ensure_case_exists(case_id):
            return

        dialog = MeasurementDialog(self, case_id)
        if dialog.exec():
            data = dialog.get_data()

            # Insert measurement
            self.db.execute_query(
                """
                INSERT INTO case_measurements (
                    case_id, measurement_date, case_length_mm,
                    neck_diameter_mm, neck_thickness_mm, base_diameter_mm,
                    shoulder_diameter_mm, case_weight_gr,
                    concentricity_tir_mm, measurement_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    data["date"],
                    data["case_length"],
                    data["neck_diameter"],
                    data["neck_thickness"],
                    data["base_diameter"],
                    data["shoulder_diameter"],
                    data["case_weight"],
                    data["concentricity"],
                    data["measurement_type"],
                    data["notes"],
                ),
            )

            # Update avg_weight if provided
            if data["case_weight"] and data["case_weight"] > 0:
                self.db.execute_query(
                    "UPDATE cases SET avg_weight_gr = ? WHERE id = ?",
                    (data["case_weight"], case_id),
                )

            self.db.commit()
            self.db.refresh_case_learning_profile(case_id)
            QMessageBox.information(
                self, tr("msg_success"), tr("brass_measurement_saved")
            )

    def retire_cases(self):
        """Retire cases (splits, cracks, etc.)"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("brass_select_lot_first")
            )
            return

        case_id = selected[0].data(Qt.ItemDataRole.UserRole)
        if not self._ensure_case_exists(case_id):
            return

        # Get current quantities
        case_rows = self.db.execute_query(
            "SELECT name, quantity, retired_quantity FROM cases WHERE id = ?",
            (case_id,),
        )
        if not case_rows:
            QMessageBox.warning(
                self,
                tr("brass_missing_lot_title"),
                tr("brass_missing_lot_message"),
            )
            self.load_data()
            return
        case = case_rows[0]

        name, qty, retired = case

        # Ask how many to retire
        from PyQt6.QtWidgets import QInputDialog

        retire_qty, ok = QInputDialog.getInt(
            self,
            tr("brass_retire_cases"),
            tr("brass_retire_prompt", name=name, quantity=qty),
            1,
            1,
            qty,
        )

        if ok:
            new_qty = qty - retire_qty
            new_retired = retired + retire_qty

            self.db.execute_query(
                """
                UPDATE cases SET
                    quantity = ?,
                    retired_quantity = ?
                WHERE id = ?
            """,
                (new_qty, new_retired, case_id),
            )

            self.db.commit()
            self.db.refresh_case_learning_profile(case_id)
            self.load_data()
            QMessageBox.information(
                self,
                tr("brass_retired_title"),
                tr("brass_retired_message", retired=retire_qty, remaining=new_qty),
            )

    def view_details(self, index):
        """View detailed history for selected case lot"""
        case_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)

        dialog = CaseDetailsDialog(self, case_id)
        dialog.exec()


class CaseLotDialog(QDialog):
    """Dialog for adding new case lot"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("brass_new_lot"))
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()

        # Basic info
        self.name = QLineEdit()
        self.name.setPlaceholderText("E.g. Lapua 6.5 CM Batch 2024-01")
        form.addRow("Lot Name:", self.name)

        self.lot_number = QLineEdit()
        self.lot_number.setPlaceholderText("Manufacturer lot number")
        form.addRow("Lot #:", self.lot_number)

        self.manufacturer = QComboBox()
        self.manufacturer.setEditable(True)
        self.manufacturer.addItems(
            [
                "Lapua",
                "Peterson",
                "Alpha Munitions",
                "ADG",
                "Norma",
                "Hornady",
                "Federal",
                "Winchester",
                "Starline",
            ]
        )
        form.addRow("Manufacturer:", self.manufacturer)

        self.caliber = QComboBox()
        self.caliber.setEditable(True)
        self.caliber.addItems(
            [
                "6.5 Creedmoor",
                ".308 Winchester",
                ".223 Remington",
                "6.5x55 Swedish",
                ".30-06 Springfield",
                "6mm Creedmoor",
            ]
        )
        form.addRow("Caliber:", self.caliber)

        self.material = QComboBox()
        self.material.addItems(["Brass", "Nickel Brass", "Steel"])
        form.addRow("Material:", self.material)

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000)
        self.quantity.setValue(100)
        form.addRow("Quantity:", self.quantity)

        self.purchase_date = QDateEdit()
        self.purchase_date.setDate(QDate.currentDate())
        self.purchase_date.setCalendarPopup(True)
        form.addRow("Purchase Date:", self.purchase_date)

        # Technical specs
        self.case_capacity = QDoubleSpinBox()
        self.case_capacity.setRange(0, 100)
        self.case_capacity.setSuffix(" gr H2O")
        self.case_capacity.setDecimals(1)
        self.case_capacity.setSpecialValueText("Unknown")
        form.addRow("Case Capacity:", self.case_capacity)

        self.avg_weight = QDoubleSpinBox()
        self.avg_weight.setRange(0, 300)
        self.avg_weight.setSuffix(" gr")
        self.avg_weight.setDecimals(1)
        self.avg_weight.setSpecialValueText("Unknown")
        form.addRow("Avg Weight:", self.avg_weight)

        self.wall_thickness = QComboBox()
        self.wall_thickness.addItems(["-", "Thin", "Medium", "Thick", "Extra Thick"])
        form.addRow("Wall Thickness:", self.wall_thickness)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notes about this brass lot...")
        form.addRow("Notes:", self.notes)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(tr("btn_save"))
        btn_save.setProperty("variant", "primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(tr("btn_cancel"))
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name.text(),
            "lot_number": self.lot_number.text(),
            "manufacturer": self.manufacturer.currentText(),
            "caliber": self.caliber.currentText(),
            "material": self.material.currentText(),
            "quantity": self.quantity.value(),
            "purchase_date": self.purchase_date.date().toString("yyyy-MM-dd"),
            "case_capacity": (
                self.case_capacity.value() if self.case_capacity.value() > 0 else None
            ),
            "avg_weight": (
                self.avg_weight.value() if self.avg_weight.value() > 0 else None
            ),
            "wall_thickness": (
                self.wall_thickness.currentText()
                if self.wall_thickness.currentIndex() > 0
                else None
            ),
            "notes": self.notes.toPlainText(),
        }


class FiringLogDialog(QDialog):
    """Dialog for logging firing session"""

    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.db = get_database()
        self.setWindowTitle(tr("brass_log_firing"))
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow("Date:", self.date)

        self.rounds_fired = QSpinBox()
        self.rounds_fired.setRange(1, 100)
        self.rounds_fired.setValue(5)
        layout.addRow("Rounds Fired:", self.rounds_fired)

        # Rifle selection
        self.rifle_combo = QComboBox()
        rifles = self.db.execute_query("SELECT id, name FROM rifles ORDER BY name")
        self.rifle_combo.addItem("-", None)
        for rifle_id, name in rifles:
            self.rifle_combo.addItem(name, rifle_id)
        layout.addRow("Rifle:", self.rifle_combo)

        # Ammo profile
        self.ammo_combo = QComboBox()
        ammos = self.db.execute_query(
            "SELECT id, name FROM ammo_profiles ORDER BY name"
        )
        self.ammo_combo.addItem("-", None)
        for ammo_id, name in ammos:
            self.ammo_combo.addItem(name, ammo_id)
        layout.addRow("Ammunition:", self.ammo_combo)

        self.pressure_level = QComboBox()
        self.pressure_level.addItems(["-", "Low", "Medium", "High", "Max"])
        layout.addRow("Pressure Level:", self.pressure_level)

        self.case_head_expansion = QDoubleSpinBox()
        self.case_head_expansion.setRange(0, 0.001)
        self.case_head_expansion.setSuffix(' "')
        self.case_head_expansion.setDecimals(5)
        self.case_head_expansion.setSpecialValueText("Not Measured")
        layout.addRow("Case Head Expansion:", self.case_head_expansion)

        self.primer_condition = QComboBox()
        self.primer_condition.addItems(["Good", "Flattened", "Cratered", "Pierced"])
        layout.addRow("Primer Condition:", self.primer_condition)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        layout.addRow("Notes:", self.notes)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(tr("brass_log_button"))
        btn_save.setProperty("variant", "primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(tr("btn_cancel"))
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "rounds_fired": self.rounds_fired.value(),
            "rifle_id": self.rifle_combo.currentData(),
            "ammo_id": self.ammo_combo.currentData(),
            "pressure_level": (
                self.pressure_level.currentText()
                if self.pressure_level.currentIndex() > 0
                else None
            ),
            "case_head_expansion": (
                self.case_head_expansion.value()
                if self.case_head_expansion.value() > 0
                else None
            ),
            "primer_condition": self.primer_condition.currentText(),
            "notes": self.notes.toPlainText(),
        }


class AnnealingLogDialog(QDialog):
    """Dialog for logging annealing"""

    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.setWindowTitle(tr("brass_log_annealing"))
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow("Date:", self.date)

        self.method = QComboBox()
        self.method.addItems(["Flame (torch)", "Induction (Annie/EP)", "AMP Annealer"])
        layout.addRow("Method:", self.method)

        self.temperature = QSpinBox()
        self.temperature.setRange(0, 900)
        self.temperature.setSuffix(" °F")
        self.temperature.setValue(750)
        self.temperature.setSpecialValueText("Unknown")
        layout.addRow("Temperature:", self.temperature)

        self.time_seconds = QDoubleSpinBox()
        self.time_seconds.setRange(0, 60)
        self.time_seconds.setSuffix(" sec")
        self.time_seconds.setDecimals(1)
        self.time_seconds.setValue(3.0)
        self.time_seconds.setSpecialValueText("Auto")
        layout.addRow("Tid:", self.time_seconds)

        self.templaq_verified = QCheckBox("Templaq paint verified")
        layout.addRow("", self.templaq_verified)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        layout.addRow("Notes:", self.notes)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(tr("brass_log_button"))
        btn_save.setProperty("variant", "primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(tr("btn_cancel"))
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "method": self.method.currentText(),
            "temperature": (
                self.temperature.value() if self.temperature.value() > 0 else None
            ),
            "time_seconds": (
                self.time_seconds.value() if self.time_seconds.value() > 0 else None
            ),
            "templaq_verified": self.templaq_verified.isChecked(),
            "notes": self.notes.toPlainText(),
        }


class PrepLogDialog(QDialog):
    """Dialog for logging case prep"""

    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.setWindowTitle(tr("brass_log_case_prep"))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Date
        date_layout = QFormLayout()
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        date_layout.addRow("Date:", self.date)
        layout.addLayout(date_layout)

        # Checkboxes for prep steps
        prep_group = QGroupBox(tr("brass_prep_steps"))
        prep_group.setProperty("variant", "panel")
        prep_layout = QVBoxLayout()

        self.trimmed = QCheckBox("Trimmed")
        self.trimmed.toggled.connect(self.toggle_trim_length)
        prep_layout.addWidget(self.trimmed)

        trim_layout = QFormLayout()
        self.trim_length = QDoubleSpinBox()
        self.trim_length.setRange(0, 100)
        self.trim_length.setSuffix(" mm")
        self.trim_length.setDecimals(2)
        self.trim_length.setEnabled(False)
        trim_layout.addRow("  Trim Length:", self.trim_length)
        prep_layout.addLayout(trim_layout)

        self.chamfered = QCheckBox("Chamfered (inside/outside)")
        prep_layout.addWidget(self.chamfered)

        self.deburred = QCheckBox("Deburred (flash hole)")
        prep_layout.addWidget(self.deburred)

        self.primer_pocket_uniformed = QCheckBox("Primer pocket uniformed")
        prep_layout.addWidget(self.primer_pocket_uniformed)

        self.flash_hole_deburred = QCheckBox("Flash hole deburred")
        prep_layout.addWidget(self.flash_hole_deburred)

        self.neck_turned = QCheckBox("Neck turned")
        self.neck_turned.toggled.connect(self.toggle_neck_thickness)
        prep_layout.addWidget(self.neck_turned)

        neck_layout = QFormLayout()
        self.neck_thickness = QDoubleSpinBox()
        self.neck_thickness.setRange(0, 5)
        self.neck_thickness.setSuffix(" mm")
        self.neck_thickness.setDecimals(3)
        self.neck_thickness.setEnabled(False)
        neck_layout.addRow("  Final Neck Thickness:", self.neck_thickness)
        prep_layout.addLayout(neck_layout)

        self.weight_sorted = QCheckBox("Weight sorted")
        prep_layout.addWidget(self.weight_sorted)

        prep_group.setLayout(prep_layout)
        layout.addWidget(prep_group)

        # Notes
        notes_layout = QFormLayout()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        notes_layout.addRow("Notes:", self.notes)
        layout.addLayout(notes_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(tr("brass_log_button"))
        btn_save.setProperty("variant", "primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(tr("btn_cancel"))
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_trim_length(self, checked):
        self.trim_length.setEnabled(checked)

    def toggle_neck_thickness(self, checked):
        self.neck_thickness.setEnabled(checked)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "trimmed": self.trimmed.isChecked(),
            "trim_length": (
                self.trim_length.value() if self.trimmed.isChecked() else None
            ),
            "chamfered": self.chamfered.isChecked(),
            "deburred": self.deburred.isChecked(),
            "primer_pocket_uniformed": self.primer_pocket_uniformed.isChecked(),
            "flash_hole_deburred": self.flash_hole_deburred.isChecked(),
            "neck_turned": self.neck_turned.isChecked(),
            "neck_thickness": (
                self.neck_thickness.value() if self.neck_turned.isChecked() else None
            ),
            "weight_sorted": self.weight_sorted.isChecked(),
            "notes": self.notes.toPlainText(),
        }


class MeasurementDialog(QDialog):
    """Dialog for adding case measurements"""

    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.setWindowTitle(tr("brass_measurements_title"))
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addRow("Date:", self.date)

        self.measurement_type = QComboBox()
        self.measurement_type.addItems(["new", "fired", "sized", "after_trim"])
        layout.addRow("Measurement Type:", self.measurement_type)

        # Measurements
        self.case_length = QDoubleSpinBox()
        self.case_length.setRange(0, 100)
        self.case_length.setSuffix(" mm")
        self.case_length.setDecimals(2)
        self.case_length.setSpecialValueText("Not Measured")
        layout.addRow("Case Length:", self.case_length)

        self.neck_diameter = QDoubleSpinBox()
        self.neck_diameter.setRange(0, 20)
        self.neck_diameter.setSuffix(" mm")
        self.neck_diameter.setDecimals(3)
        self.neck_diameter.setSpecialValueText("Not Measured")
        layout.addRow("Neck Diameter:", self.neck_diameter)

        self.neck_thickness = QDoubleSpinBox()
        self.neck_thickness.setRange(0, 5)
        self.neck_thickness.setSuffix(" mm")
        self.neck_thickness.setDecimals(3)
        self.neck_thickness.setSpecialValueText("Not Measured")
        layout.addRow("Neck Thickness:", self.neck_thickness)

        self.base_diameter = QDoubleSpinBox()
        self.base_diameter.setRange(0, 20)
        self.base_diameter.setSuffix(" mm")
        self.base_diameter.setDecimals(3)
        self.base_diameter.setSpecialValueText("Not Measured")
        layout.addRow("Base Diameter:", self.base_diameter)

        self.shoulder_diameter = QDoubleSpinBox()
        self.shoulder_diameter.setRange(0, 20)
        self.shoulder_diameter.setSuffix(" mm")
        self.shoulder_diameter.setDecimals(3)
        self.shoulder_diameter.setSpecialValueText("Not Measured")
        layout.addRow("Shoulder Diameter:", self.shoulder_diameter)

        self.case_weight = QDoubleSpinBox()
        self.case_weight.setRange(0, 300)
        self.case_weight.setSuffix(" gr")
        self.case_weight.setDecimals(1)
        self.case_weight.setSpecialValueText("Not Measured")
        layout.addRow("Case Weight:", self.case_weight)

        self.concentricity = QDoubleSpinBox()
        self.concentricity.setRange(0, 1)
        self.concentricity.setSuffix(" mm TIR")
        self.concentricity.setDecimals(3)
        self.concentricity.setSpecialValueText("Not Measured")
        layout.addRow("Concentricity:", self.concentricity)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(60)
        layout.addRow("Notes:", self.notes)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(tr("btn_save"))
        btn_save.setProperty("variant", "primary")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(tr("btn_cancel"))
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "measurement_type": self.measurement_type.currentText(),
            "case_length": (
                self.case_length.value() if self.case_length.value() > 0 else None
            ),
            "neck_diameter": (
                self.neck_diameter.value() if self.neck_diameter.value() > 0 else None
            ),
            "neck_thickness": (
                self.neck_thickness.value() if self.neck_thickness.value() > 0 else None
            ),
            "base_diameter": (
                self.base_diameter.value() if self.base_diameter.value() > 0 else None
            ),
            "shoulder_diameter": (
                self.shoulder_diameter.value()
                if self.shoulder_diameter.value() > 0
                else None
            ),
            "case_weight": (
                self.case_weight.value() if self.case_weight.value() > 0 else None
            ),
            "concentricity": (
                self.concentricity.value() if self.concentricity.value() > 0 else None
            ),
            "notes": self.notes.toPlainText(),
        }


class CaseDetailsDialog(QDialog):
    """Dialog showing detailed history for a case lot"""

    def __init__(self, parent, case_id):
        super().__init__(parent)
        self.case_id = case_id
        self.db = get_database()
        self.setWindowTitle(tr("brass_details_title"))
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Case info header
        case = self.db.execute_query(
            "SELECT name, manufacturer, caliber, quantity, times_fired FROM cases WHERE id = ?",
            (self.case_id,),
        )[0]

        header = QLabel(str(case[0]))
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        info = QLabel(
            f"<b>Manufacturer:</b> {case[1]} | "
            f"<b>Caliber:</b> {case[2]} | "
            f"<b>Quantity:</b> {case[3]} | "
            f"<b>Times Fired:</b> {case[4]}"
        )
        info.setProperty("variant", "cardSubtitle")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabs for different history types
        tabs = QTabWidget()

        tabs.addTab(self.create_firing_history_tab(), tr("brass_firing_history"))
        tabs.addTab(self.create_annealing_history_tab(), tr("brass_annealing_history"))
        tabs.addTab(self.create_prep_history_tab(), tr("brass_prep_history"))
        tabs.addTab(self.create_measurements_tab(), tr("brass_measurements_tab"))
        tabs.addTab(self.create_learning_tab(), tr("brass_learning_tab"))

        layout.addWidget(tabs)

        # Close button
        btn_close = QPushButton(tr("btn_close"))
        btn_close.setProperty("variant", "ghost")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def create_firing_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        firings = self.db.execute_query(
            """
            SELECT firing_date, rounds_fired, pressure_level,
                   case_head_expansion_inch, primer_condition, notes
            FROM case_firing_log
            WHERE case_id = ?
            ORDER BY firing_date DESC
        """,
            (self.case_id,),
        )

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Date", "Shots", "Pressure", "Case Head Exp", "Primer", "Notes"]
        )
        table.setRowCount(len(firings))

        for i, firing in enumerate(firings):
            for j, value in enumerate(firing):
                table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))

        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def create_annealing_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        annealings = self.db.execute_query(
            """
            SELECT annealing_date, method, temperature_f, time_seconds,
                   templaq_verified, notes
            FROM case_annealing_log
            WHERE case_id = ?
            ORDER BY annealing_date DESC
        """,
            (self.case_id,),
        )

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Date", "Method", "Temp (°F)", "Time (s)", "Templaq", "Notes"]
        )
        table.setRowCount(len(annealings))

        for i, annealing in enumerate(annealings):
            for j, value in enumerate(annealing):
                if j == 4:  # Templaq boolean
                    table.setItem(i, j, QTableWidgetItem("Yes" if value else "No"))
                else:
                    table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))

        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def create_prep_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        preps = self.db.execute_query(
            """
            SELECT prep_date, trimmed, trim_length_mm, chamfered,
                   primer_pocket_uniformed, neck_turned, notes
            FROM case_prep_log
            WHERE case_id = ?
            ORDER BY prep_date DESC
        """,
            (self.case_id,),
        )

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            [
                "Date",
                "Trimmed",
                "Length",
                "Chamfered",
                "Pocket",
                "Neck Turned",
                "Notes",
            ]
        )
        table.setRowCount(len(preps))

        for i, prep in enumerate(preps):
            for j, value in enumerate(prep):
                if j in [1, 3, 4, 5]:  # Boolean fields
                    table.setItem(i, j, QTableWidgetItem("Yes" if value else "No"))
                else:
                    table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))

        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def create_measurements_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        measurements = self.db.execute_query(
            """
            SELECT measurement_date, measurement_type, case_length_mm,
                   neck_diameter_mm, base_diameter_mm, case_weight_gr
            FROM case_measurements
            WHERE case_id = ?
            ORDER BY measurement_date DESC
        """,
            (self.case_id,),
        )

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Date", "Type", "Length (mm)", "Neck (mm)", "Base (mm)", "Weight (gr)"]
        )
        table.setRowCount(len(measurements))

        for i, measurement in enumerate(measurements):
            for j, value in enumerate(measurement):
                table.setItem(i, j, QTableWidgetItem(str(value) if value else "-"))

        table.resizeColumnsToContents()
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget

    def create_learning_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        learning = self.db.refresh_case_learning_profile(self.case_id)

        summary = QLabel(
            f"<b>Status:</b> {learning.get('status', 'insufficient_data')}<br>"
            f"<b>Confidence:</b> {learning.get('confidence_label', 'no data yet')}<br>"
            f"<b>Data Points:</b> {learning.get('data_points', 0)}<br>"
            f"<b>H2O Samples:</b> {learning.get('h2o_samples', 0)}<br>"
            f"<b>Firing Events:</b> {learning.get('firing_events', 0)}<br>"
            f"<b>Prep:</b> {learning.get('prep_events', 0)}<br>"
            f"<b>Annealing:</b> {learning.get('anneal_events', 0)}"
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)

        details = []
        if learning.get("avg_case_capacity_h2o") is not None:
            details.append(
                f"Average case capacity: {float(learning['avg_case_capacity_h2o']):.2f} gr H2O"
            )
        if learning.get("capacity_spread_h2o") is not None:
            details.append(
                f"H2O spread: {float(learning['capacity_spread_h2o']):.2f} gr"
            )
        if learning.get("avg_case_weight_gr") is not None:
            details.append(
                f"Average case weight: {float(learning['avg_case_weight_gr']):.1f} gr"
            )
        if learning.get("typical_times_fired") is not None:
            details.append(
                f"Typical reload cycles: {float(learning['typical_times_fired']):.1f}"
            )
        if learning.get("estimated_remaining_cycles") is not None:
            details.append(
                f"Estimated remaining cycles: {float(learning['estimated_remaining_cycles']):.1f}"
            )
        if learning.get("drift_flag"):
            details.append(f"Drift Flag: {learning['drift_flag']}")

        details_label = QLabel(
            "<br>".join(details) if details else tr("brass_no_learning_data")
        )
        details_label.setWordWrap(True)
        layout.addWidget(details_label)

        widget.setLayout(layout)
        return widget
