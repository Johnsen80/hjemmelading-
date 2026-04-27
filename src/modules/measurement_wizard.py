from __future__ import annotations

import csv
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.analysis import compute_stats, detect_outliers


class MeasurementSessionDialog(QDialog):
    """Wizard dialog for entering QC measurement sessions."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Measurement Session")
        self.db = get_database()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        # Lot selection
        lot_row = QHBoxLayout()
        lot_row.addWidget(QLabel("Inventory lot:"))
        self.lot_combo = QComboBox()
        lot_row.addWidget(self.lot_combo)
        self.refresh_lots_btn = QPushButton("Refresh lots")
        self.refresh_lots_btn.clicked.connect(self.load_lots)
        lot_row.addWidget(self.refresh_lots_btn)
        layout.addLayout(lot_row)

        # Table for measurements
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Index",
                "Weight (gr)",
                "Length (mm)",
                "Neck (mm)",
                "Case Weight (gr)",
                "Passed",
                "Notes",
            ]
        )
        layout.addWidget(self.table)

        # Buttons for table operations
        tbl_ops = QHBoxLayout()
        self.add_row_btn = QPushButton("Add row")
        self.add_row_btn.clicked.connect(self.add_row)
        tbl_ops.addWidget(self.add_row_btn)
        self.remove_row_btn = QPushButton("Remove row")
        self.remove_row_btn.clicked.connect(self.remove_selected_row)
        tbl_ops.addWidget(self.remove_row_btn)
        self.import_csv_btn = QPushButton("Import CSV")
        self.import_csv_btn.clicked.connect(self.import_csv)
        tbl_ops.addWidget(self.import_csv_btn)
        layout.addLayout(tbl_ops)

        # Stats display
        stats_row = QHBoxLayout()
        self.stats_label = QLabel("Stats: n=0")
        stats_row.addWidget(self.stats_label)
        self.compute_stats_btn = QPushButton("Compute stats")
        self.compute_stats_btn.clicked.connect(self.compute_stats_action)
        stats_row.addWidget(self.compute_stats_btn)
        layout.addLayout(stats_row)

        # Save/Cancel
        bottom = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_session)
        bottom.addWidget(self.save_btn)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(self.cancel_btn)
        layout.addLayout(bottom)

        self.setLayout(layout)
        self.load_lots()

    def load_lots(self):
        self.lot_combo.clear()
        lots = self.db.get_all("inventory_lots", order_by="id DESC")
        for lot in lots:
            display = f"{lot.get('lot_number') or 'lot-'+str(lot.get('id'))} ({lot.get('component_type')}) qty={lot.get('quantity_remaining')}"
            self.lot_combo.addItem(display, lot.get("id"))

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        # default index
        self.table.setItem(r, 0, QTableWidgetItem(str(r + 1)))

    def remove_selected_row(self):
        sel = self.table.currentRow()
        if sel >= 0:
            self.table.removeRow(sel)

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    # Fill fields defensively
                    self.table.setItem(
                        row, 0, QTableWidgetItem(r.get("item_index", str(row + 1)))
                    )
                    self.table.setItem(
                        row, 1, QTableWidgetItem(str(r.get("weight_grains") or ""))
                    )
                    self.table.setItem(
                        row, 2, QTableWidgetItem(str(r.get("length_mm") or ""))
                    )
                    self.table.setItem(
                        row, 3, QTableWidgetItem(str(r.get("neck_thickness_mm") or ""))
                    )
                    self.table.setItem(
                        row, 4, QTableWidgetItem(str(r.get("case_weight_gr") or ""))
                    )
                    self.table.setItem(
                        row, 5, QTableWidgetItem(r.get("passed_qc") or "")
                    )
                    self.table.setItem(row, 6, QTableWidgetItem(r.get("notes") or ""))
        except Exception as e:
            QMessageBox.warning(self, "Import error", f"Failed to import CSV: {e}")

    def compute_stats_action(self):
        weights = []
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 1)
            if it and it.text().strip():
                try:
                    weights.append(float(it.text()))
                except Exception:
                    pass
        if not weights:
            QMessageBox.information(
                self, "No data", "No weight data present to compute stats"
            )
            return
        stats = compute_stats(weights)
        outliers = detect_outliers(weights, method="mad")
        self.stats_label.setText(
            f"Stats: n={stats['n']} mean={stats['mean']:.3f} sd={stats['sd']:.3f} CI95=({stats['ci95'][0]:.3f},{stats['ci95'][1]:.3f}) outliers={outliers}"
        )

    def save_session(self):
        if self.lot_combo.count() == 0:
            QMessageBox.warning(
                self,
                "No lot",
                "No inventory lot selected. Create or import a lot first.",
            )
            return
        lot_id = self.lot_combo.currentData()
        if not lot_id:
            QMessageBox.warning(self, "Invalid lot", "Selected lot invalid")
            return
        lot = self.db.get_by_id("inventory_lots", lot_id)
        if not lot:
            QMessageBox.warning(
                self,
                "Missing lot",
                "The selected inventory lot no longer exists.",
            )
            self.load_lots()
            return

        session_id = self.db.create_measurement_session(
            lot_id,
            measured_by="ui",
            sample_size=self.table.rowCount(),
            measured_all=0,
            notes="Saved from UI",
        )
        for r in range(self.table.rowCount()):
            try:
                idx_item = self.table.item(r, 0)
                idx = (
                    int(idx_item.text())
                    if idx_item and idx_item.text().strip()
                    else r + 1
                )
                weight = self._parse_cell_float(r, 1)
                length = self._parse_cell_float(r, 2)
                neck = self._parse_cell_float(r, 3)
                case_w = self._parse_cell_float(r, 4)
                passed = None
                passed_it = self.table.item(r, 5)
                if passed_it and passed_it.text().strip().lower() in (
                    "1",
                    "true",
                    "y",
                    "yes",
                ):
                    passed = 1
                notes_it = self.table.item(r, 6)
                notes = notes_it.text() if notes_it else None
                self.db.add_measurement_value(
                    session_id, idx, weight, length, neck, case_w, passed, notes
                )
            except Exception:
                # skip problematic rows
                continue

        QMessageBox.information(self, "Saved", f"Session {session_id} saved")
        self.accept()

    def _parse_cell_float(self, row: int, col: int) -> Optional[float]:
        it = self.table.item(row, col)
        if not it:
            return None
        txt = it.text().strip()
        if not txt:
            return None
        try:
            return float(txt)
        except Exception:
            return None


def show_measurement_wizard():
    _ = QApplication.instance() or QApplication([])
    dlg = MeasurementSessionDialog()
    dlg.exec()


if __name__ == "__main__":
    show_measurement_wizard()
