"""Component lot tracking system."""

from typing import Dict

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.i18n import tr


class AddLotDialog(QDialog):
    """Dialog for adding a new lot."""

    def __init__(
        self, component_type: str, component_id: int, component_name: str, parent=None
    ):
        super().__init__(parent)
        self.component_type = component_type
        self.component_id = component_id
        self.component_name = component_name

        self.setWindowTitle(f"Add Lot: {component_name}")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Lot number
        lot_layout = QHBoxLayout()
        lot_layout.addWidget(QLabel("Lot #:"))
        self.edit_lot = QLineEdit()
        self.edit_lot.setPlaceholderText("F-230815-42")
        lot_layout.addWidget(self.edit_lot)
        layout.addLayout(lot_layout)

        # Purchase date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Purchase Date:"))
        self.date_purchase = QDateEdit()
        self.date_purchase.setDate(QDate.currentDate())
        self.date_purchase.setCalendarPopup(True)
        date_layout.addWidget(self.date_purchase)
        layout.addLayout(date_layout)

        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(0, 100000)
        self.spin_quantity.setDecimals(1)

        if self.component_type == "powder":
            self.spin_quantity.setSuffix(" g")
        else:
            self.spin_quantity.setSuffix(" pcs")

        qty_layout.addWidget(self.spin_quantity)
        layout.addLayout(qty_layout)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(100)
        self.edit_notes.setPlaceholderText("Supplier, cost, observations...")
        layout.addWidget(self.edit_notes)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self) -> Dict:
        """Get dialog input data."""
        return {
            "lot_number": self.edit_lot.text(),
            "purchase_date": self.date_purchase.date().toString("yyyy-MM-dd"),
            "quantity": self.spin_quantity.value(),
            "notes": self.edit_notes.toPlainText(),
        }


class ComponentLotTracker(QWidget):
    """Track component lots and compare performance across lots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Component Lot Tracker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        desc = QLabel(
            "Track lot numbers for powder, bullets, and primers.\n"
            "Factory ammunition is tested by lot, and your reloads should be too. Lot changes can shift an optimal charge by about ±0.3 gr."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Tabs for each component type
        self.tabs = QTabWidget()

        self.tabs.addTab(self.create_component_tab("powder", "Powder"), "Powder")
        self.tabs.addTab(self.create_component_tab("bullets", "Bullets"), "Bullets")
        self.tabs.addTab(self.create_component_tab("primers", "Primers"), "Primers")

        layout.addWidget(self.tabs)

        # Lot comparison section
        comparison_group = QGroupBox("Lot Comparison & Warnings")
        comparison_layout = QVBoxLayout()

        self.text_comparison = QTextEdit()
        self.text_comparison.setReadOnly(True)
        self.text_comparison.setMaximumHeight(200)
        self.text_comparison.setHtml(
            """
            <p style='color: #7f8c8d;'>
            Select a component and add lots to compare them.<br><br>
            <b>Tip:</b> Lot variation is real.
            <ul>
                <li>Powder burn rate can vary by about ±2% between lots</li>
                <li>That can equal roughly ±0.3 to 0.5 gr of charge difference</li>
                <li>Bullets can vary by about ±0.0001" in diameter</li>
                <li>Always re-test when changing lots</li>
            </ul>
            </p>
        """
        )
        comparison_layout.addWidget(self.text_comparison)

        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group)

        self.setLayout(layout)

    def create_component_tab(self, table_name: str, display_name: str) -> QWidget:
        """Create a tab for one component type."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Component selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(f"{display_name}:"))

        combo = QComboBox()
        combo.setObjectName(f"combo_{table_name}")
        self.load_components(combo, table_name)
        combo.currentIndexChanged.connect(lambda: self.on_component_changed(table_name))
        selector_layout.addWidget(combo)

        btn_add_lot = QPushButton("Add Lot")
        btn_add_lot.clicked.connect(lambda: self.add_lot(table_name))
        selector_layout.addWidget(btn_add_lot)

        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Lots table
        table = QTableWidget()
        table.setObjectName(f"table_{table_name}")
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            [
                "Lot #",
                "Quantity",
                "Purchase Date",
                "Status",
                "Performance",
                "Notes",
                "Action",
            ]
        )
        hdr = table.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        widget.setLayout(layout)
        return widget

    def load_components(self, combo: QComboBox, table_name: str):
        """Load components into the selector."""
        components = self.db.get_all(table_name, "name")
        combo.clear()
        for comp in components:
            combo.addItem(comp["name"], comp["id"])

    def on_component_changed(self, table_name: str):
        """Handle component selection changes."""
        combo = self.findChild(QComboBox, f"combo_{table_name}")
        table = self.findChild(QTableWidget, f"table_{table_name}")

        if not combo or not table:
            return

        component_id = combo.currentData()
        if not component_id:
            return

        # Load lots for this component
        self.load_lots(table, table_name, component_id)

        # Update comparison
        self.update_comparison(table_name, component_id)

    def load_lots(self, table: QTableWidget, table_name: str, component_id: int):
        """Load lots for the selected component."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM component_lots
            WHERE component_type = ? AND component_id = ?
            ORDER BY purchase_date DESC
        """,
            (table_name, component_id),
        )

        lots = cursor.fetchall()
        table.setRowCount(len(lots))

        for i, lot in enumerate(lots):
            # Lot number
            table.setItem(i, 0, QTableWidgetItem(lot["lot_number"]))

            # Quantity
            qty = lot["quantity_remaining"]
            if table_name == "powder":
                qty_str = f"{qty:.1f} g"
            else:
                qty_str = f"{int(qty)} pcs"

            item_qty = QTableWidgetItem(qty_str)
            if qty < 100:  # Low stock
                item_qty.setBackground(QColor(255, 200, 200))
            table.setItem(i, 1, item_qty)

            # Purchase date
            table.setItem(i, 2, QTableWidgetItem(lot["purchase_date"]))

            # Status
            status = "Active" if lot["is_active"] else "Inactive"
            table.setItem(i, 3, QTableWidgetItem(status))

            # Performance rating
            rating = lot.get("performance_rating", "N/A")
            table.setItem(i, 4, QTableWidgetItem(str(rating)))

            # Notes
            notes = lot.get("notes", "")[:50]
            table.setItem(i, 5, QTableWidgetItem(notes))

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)

            btn_deactivate = QPushButton("Deactivate")
            btn_deactivate.setToolTip("Deactivate lot")
            btn_deactivate.clicked.connect(
                lambda _, lid=lot["id"]: self.deactivate_lot(
                    lid, table_name, component_id
                )
            )
            btn_layout.addWidget(btn_deactivate)

            btn_widget.setLayout(btn_layout)
            table.setCellWidget(i, 6, btn_widget)

    def _build_powder_learning_summary(self, lot: Dict) -> str:
        profile = self.db.refresh_powder_lot_learning_profile(int(lot["id"]))
        if not profile:
            return "No learning data yet"

        parts = [
            f"Status: {profile.get('status', 'unknown')}",
            f"Confidence: {profile.get('confidence_label', 'no data yet')}",
        ]
        batch_samples = int(profile.get("batch_samples") or 0)
        if batch_samples:
            parts.append(f"Batches: {batch_samples}")
        avg_velocity = profile.get("avg_velocity_fps")
        if isinstance(avg_velocity, (int, float)):
            parts.append(f"Avg V0: {avg_velocity:.1f} fps")
        offset = profile.get("velocity_offset_fps")
        if isinstance(offset, (int, float)):
            parts.append(f"Offset: {offset:+.1f} fps")
        typical_es = profile.get("typical_es_fps")
        if isinstance(typical_es, (int, float)):
            parts.append(f"Typical ES: {typical_es:.1f}")
        temp_sensitivity = profile.get("temp_sensitivity_fps_per_c")
        if isinstance(temp_sensitivity, (int, float)):
            parts.append(f"Temp: {temp_sensitivity:+.2f} fps/C")
        drift_flag = str(profile.get("drift_flag") or "").strip()
        if drift_flag:
            parts.append(f"Flag: {drift_flag}")
        return " | ".join(parts)

    def _build_powder_comparison_summary(self, component_id: int, lot: Dict) -> str:
        comparison = self.db.compare_powder_lots(int(component_id), int(lot["id"]))
        if not comparison:
            return ""
        title = str(comparison.get("title") or "").strip()
        message = str(comparison.get("message") or "").strip()
        recommended_action = str(comparison.get("recommended_action") or "").strip()
        verification_plan = comparison.get("verification_plan") or {}
        if not title and not message:
            return ""
        parts = [f"<b>{title}</b>"]
        if message:
            parts.append(message)
        if recommended_action:
            parts.append(f"Action: {recommended_action}")
        if isinstance(verification_plan, dict):
            focus = str(verification_plan.get("focus") or "").strip()
            shots = verification_plan.get("shots")
            delta = verification_plan.get("start_delta_grains")
            plan_bits = []
            if isinstance(shots, int) and shots > 0:
                plan_bits.append(f"{shots} verification shots")
            if isinstance(delta, (int, float)) and float(delta) != 0.0:
                plan_bits.append(f"start {float(delta):+.1f} gr")
            if focus:
                plan_bits.append(focus)
            if plan_bits:
                parts.append("Verification Plan: " + " | ".join(plan_bits))
        severity = str(comparison.get("severity") or "info")
        color = "#1f618d"
        if severity == "ok":
            color = "#1e8449"
        elif severity == "watch":
            color = "#b9770e"
        elif severity == "high":
            color = "#b03a2e"
        return (
            "<div style='margin-top:4px; padding:6px; border-radius:4px; "
            f"background-color:#f8f9fa; color:{color};'>"
            + "<br>".join(parts)
            + "</div>"
        )

    def _build_primer_learning_summary(self, lot: Dict) -> str:
        profile = self.db.refresh_primer_lot_learning_profile(int(lot["id"]))
        if not profile:
            return "No learning data yet"

        parts = [
            f"Status: {profile.get('status', 'unknown')}",
            f"Confidence: {profile.get('confidence_label', 'no data yet')}",
        ]
        batch_samples = int(profile.get("batch_samples") or 0)
        if batch_samples:
            parts.append(f"Batches: {batch_samples}")
        avg_velocity = profile.get("avg_velocity_fps")
        if isinstance(avg_velocity, (int, float)):
            parts.append(f"Avg V0: {avg_velocity:.1f} fps")
        typical_es = profile.get("typical_es_fps")
        if isinstance(typical_es, (int, float)):
            parts.append(f"Typical ES: {typical_es:.1f}")
        typical_sd = profile.get("profile_data", {}).get("typical_sd_fps")
        if isinstance(typical_sd, (int, float)):
            parts.append(f"Typical SD: {typical_sd:.1f}")
        best_moa = profile.get("best_recorded_moa")
        if isinstance(best_moa, (int, float)):
            parts.append(f"Best MOA: {best_moa:.3f}")
        drift_flag = str(profile.get("drift_flag") or "").strip()
        if drift_flag:
            parts.append(f"Flag: {drift_flag}")
        return " | ".join(parts)

    def _build_primer_comparison_summary(self, component_id: int, lot: Dict) -> str:
        comparison = self.db.compare_primer_lots(int(component_id), int(lot["id"]))
        if not comparison:
            return ""
        title = str(comparison.get("title") or "").strip()
        message = str(comparison.get("message") or "").strip()
        recommended_action = str(comparison.get("recommended_action") or "").strip()
        verification_plan = comparison.get("verification_plan") or {}
        if not title and not message:
            return ""
        parts = [f"<b>{title}</b>"]
        if message:
            parts.append(message)
        if recommended_action:
            parts.append(f"Action: {recommended_action}")
        if isinstance(verification_plan, dict):
            focus = str(verification_plan.get("focus") or "").strip()
            shots = verification_plan.get("shots")
            plan_bits = []
            if isinstance(shots, int) and shots > 0:
                plan_bits.append(f"{shots} verification shots")
            if focus:
                plan_bits.append(focus)
            if plan_bits:
                parts.append("Verification Plan: " + " | ".join(plan_bits))
        severity = str(comparison.get("severity") or "info")
        color = "#1f618d"
        if severity == "ok":
            color = "#1e8449"
        elif severity == "watch":
            color = "#b9770e"
        elif severity == "high":
            color = "#b03a2e"
        return (
            "<div style='margin-top:4px; padding:6px; border-radius:4px; "
            f"background-color:#f8f9fa; color:{color};'>"
            + "<br>".join(parts)
            + "</div>"
        )

    def add_lot(self, table_name: str):
        """Add a new lot."""
        combo = self.findChild(QComboBox, f"combo_{table_name}")
        if not combo:
            return

        component_id = combo.currentData()
        component_name = combo.currentText()

        if not component_id:
            QMessageBox.warning(
                self,
                tr("msg_no_selection"),
                tr("lot_tracker_select_component_first", component=table_name),
            )
            return

        dialog = AddLotDialog(table_name, component_id, component_name, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            # Save to database
            lot_id = self.db.insert(
                "component_lots",
                {
                    "component_type": table_name,
                    "component_id": component_id,
                    "lot_number": data["lot_number"],
                    "purchase_date": data["purchase_date"],
                    "quantity_initial": data["quantity"],
                    "quantity_remaining": data["quantity"],
                    "is_active": 1,
                    "notes": data["notes"],
                },
            )
            if table_name == "powder":
                self.db.refresh_powder_lot_learning_profile(lot_id)
            elif table_name == "primers":
                self.db.refresh_primer_lot_learning_profile(lot_id)

            # Reload table
            table = self.findChild(QTableWidget, f"table_{table_name}")
            self.load_lots(table, table_name, component_id)

            QMessageBox.information(
                self, "Lot Added", f"Lot {data['lot_number']} was added."
            )

    def deactivate_lot(self, lot_id: int, table_name: str, component_id: int):
        """Deactivate a lot that is used up or retired."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            UPDATE component_lots
            SET is_active = 0
            WHERE id = ?
        """,
            (lot_id,),
        )
        self.db.conn.commit()
        if table_name == "powder":
            self.db.refresh_powder_lot_learning_profile(lot_id)
        elif table_name == "primers":
            self.db.refresh_primer_lot_learning_profile(lot_id)

        # Reload table
        table = self.findChild(QTableWidget, f"table_{table_name}")
        self.load_lots(table, table_name, component_id)

    def update_comparison(self, table_name: str, component_id: int):
        """Update the comparison view for recent lots."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            """
            SELECT id, lot_number, performance_rating, notes
            FROM component_lots
            WHERE component_type = ? AND component_id = ?
            ORDER BY purchase_date DESC
            LIMIT 5
        """,
            (table_name, component_id),
        )

        lots = cursor.fetchall()

        if not lots:
            self.text_comparison.setHtml(
                """
                <p style='color: #7f8c8d;'>
                No lots have been registered yet. Add a lot to start tracking.
                </p>
            """
            )
            return

        html = """
        <h3 style='color: #2c3e50;'>Lot Comparison</h3>
        <table border='1' style='border-collapse: collapse; width: 100%;'>
            <tr style='background-color: #ecf0f1;'>
                <th>Lot #</th>
                <th>Performance</th>
                <th>Notes</th>
            </tr>
        """

        for lot in lots:
            rating = (
                lot["performance_rating"] if lot["performance_rating"] else "Not Tested"
            )
            notes = lot["notes"][:50] if lot["notes"] else "-"
            learning = (
                self._build_powder_learning_summary(lot)
                if table_name == "powder"
                else (
                    self._build_primer_learning_summary(lot)
                    if table_name == "primers"
                    else "Learning data will appear when this component type is linked to measurements."
                )
            )
            comparison = (
                self._build_powder_comparison_summary(component_id, lot)
                if table_name == "powder"
                else (
                    self._build_primer_comparison_summary(component_id, lot)
                    if table_name == "primers"
                    else ""
                )
            )

            html += f"""
            <tr>
                <td><b>{lot['lot_number']}</b></td>
                <td>{rating}</td>
                <td>{notes}</td>
            </tr>
            <tr>
                <td colspan='3' style='font-size: 11px; color: #34495e; background-color: #f8f9fa;'>
                    {learning}
                    {comparison}
                </td>
            </tr>
            """

        html += """
        </table>

        <h3 style='color: #e67e22; margin-top: 15px;'>Important When Changing Lots:</h3>
        <ul>
            <li><b>Re-test.</b> Lot variation can change the optimal load.</li>
            <li><b>Start conservatively:</b> 0.3 to 0.5 gr below the previous optimum.</li>
            <li><b>Check pressure signs:</b> A new lot can raise pressure.</li>
            <li><b>Verify velocity:</b> Compare against the previous lot.</li>
        </ul>
        """

        self.text_comparison.setHtml(html)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ComponentLotTracker()
    window.show()
    sys.exit(app.exec())
