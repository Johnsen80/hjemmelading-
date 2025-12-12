from pathlib import Path
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QLabel,
)
from src.modules.weapon_profile import load_profiles, save_profiles
from src.ui.barrel_editor import BarrelEditorDialog
from src.ui.calibration_test_dialog import CalibrationTestDialog

DEFAULT_DATA = Path("data") / "demo_weapons.json"


class WeaponProfileEditor(QDialog):
    """Minimal weapon profile editor dialog.

    Loads and saves a JSON file containing a list of weapon profiles.
    Each profile is a dict containing at least an `id` and `name`.
    """

    def __init__(self, data_path: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weapon Profile Editor — Valkyrie Ballistics")
        self.resize(640, 360)
        # Apply central stylesheet and objectName for theming
        try:
            from src.ui.reloading_theme import ReloadingTheme

            self.setObjectName("weaponProfileEditor")
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass

        self.data_path = Path(data_path) if data_path else DEFAULT_DATA
        # load via model helper
        self._profiles = load_profiles(self.data_path)
        # convert to legacy list-of-dicts shape for UI code reuse
        self._data: list[dict[str, Any]] = [p.to_dict() for p in self._profiles]

        self.main_layout = QVBoxLayout(self)

        self.selector_layout = QHBoxLayout()
        self.profile_select = QComboBox()
        self.profile_select.currentIndexChanged.connect(self._on_select)
        self.selector_layout.addWidget(self.profile_select)

        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._on_new)
        self.selector_layout.addWidget(self.new_btn)

        self.main_layout.addLayout(self.selector_layout)

        # Barrels selector and actions
        self.barrel_selector_layout = QHBoxLayout()
        self.barrel_select = QComboBox()
        self.barrel_select.currentIndexChanged.connect(self._on_barrel_select)
        self.barrel_selector_layout.addWidget(QLabel("Barrels:"))
        self.barrel_selector_layout.addWidget(self.barrel_select)

        self.add_barrel_btn = QPushButton("Add Barrel")
        self.add_barrel_btn.clicked.connect(self._on_new_barrel)
        self.barrel_selector_layout.addWidget(self.add_barrel_btn)

        self.edit_barrel_btn = QPushButton("Edit Barrel")
        self.edit_barrel_btn.clicked.connect(self._on_edit_barrel)
        self.barrel_selector_layout.addWidget(self.edit_barrel_btn)

        self.remove_barrel_btn = QPushButton("Remove Barrel")
        self.remove_barrel_btn.clicked.connect(self._on_remove_barrel)
        self.barrel_selector_layout.addWidget(self.remove_barrel_btn)

        self.add_calib_btn = QPushButton("Add Calibration Test")
        self.add_calib_btn.clicked.connect(self._on_add_calibration_test)
        self.barrel_selector_layout.addWidget(self.add_calib_btn)
        self.view_calib_btn = QPushButton("View Tests")
        self.view_calib_btn.clicked.connect(self._on_view_calibration_tests)
        self.barrel_selector_layout.addWidget(self.view_calib_btn)

        self.main_layout.addLayout(self.barrel_selector_layout)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.caliber_edit = QLineEdit()
        self.barrel_length_edit = QLineEdit()
        self.twist_edit = QLineEdit()
        self.muzzle_velocity_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        # Optics fields (simple single-active-optic UI)
        self.optic_name_edit = QLineEdit()
        self.optic_manufacturer_edit = QLineEdit()
        self.optic_zero_distance_edit = QLineEdit()
        self.optic_unit_combo = QComboBox()
        self.optic_unit_combo.addItems(["mil", "moa"])
        self.optic_click_value_edit = QLineEdit()
        self.optic_clicks_per_rev_edit = QLineEdit()

        form.addRow("Name:", self.name_edit)
        form.addRow("Caliber:", self.caliber_edit)
        form.addRow("Barrel length (mm):", self.barrel_length_edit)
        form.addRow("Twist:", self.twist_edit)
        form.addRow("Muzzle velocity (m/s):", self.muzzle_velocity_edit)
        form.addRow("Notes:", self.notes_edit)
        # Optics section
        form.addRow("Optic name:", self.optic_name_edit)
        form.addRow("Manufacturer:", self.optic_manufacturer_edit)
        form.addRow("Zero distance (m):", self.optic_zero_distance_edit)
        form.addRow("Turret units:", self.optic_unit_combo)
        form.addRow("Click value (unit):", self.optic_click_value_edit)
        form.addRow("Clicks per rev:", self.optic_clicks_per_rev_edit)
        # Optics history / management
        self.view_optics_history_btn = QPushButton("View Optics History")
        self.view_optics_history_btn.clicked.connect(self._on_view_optics_history)
        form.addRow(self.view_optics_history_btn)

        self.main_layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._on_save)
        self.save_as_btn = QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self._on_save_as)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.save_as_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.close_btn)

        self.main_layout.addLayout(btn_row)

        self._refresh_selector()

    def _load_data(self):
        # deprecated: now using model loader in __init__
        pass

    def _save_data(self, path: Optional[Path] = None):
        # persist via model save helper
        target = Path(path) if path else self.data_path
        profiles = [
            __import__("src.modules.weapon_profile", fromlist=["WeaponProfile"]).WeaponProfile.from_dict(p)
            for p in self._data
        ]
        save_profiles(target, profiles)

    def _refresh_selector(self):
        self.profile_select.blockSignals(True)
        self.profile_select.clear()
        for p in self._data:
            self.profile_select.addItem(p.get("name", p.get("id", "Unnamed")))
        self.profile_select.blockSignals(False)
        if self._data:
            self.profile_select.setCurrentIndex(0)
            self._populate_fields(self._data[0])

    def _refresh_barrel_selector(self, profile: dict | None):
        self.barrel_select.blockSignals(True)
        self.barrel_select.clear()
        if not profile:
            self.barrel_select.blockSignals(False)
            return
        for b in profile.get("barrels", []):
            self.barrel_select.addItem(b.get("name", b.get("id", "Barrel")))
        self.barrel_select.blockSignals(False)
        if profile.get("barrels"):
            self.barrel_select.setCurrentIndex(0)

    def _populate_fields(self, profile: dict):
        self.name_edit.setText(profile.get("name", ""))
        self.caliber_edit.setText(profile.get("caliber", ""))
        self.barrel_length_edit.setText(str(profile.get("barrel_length_mm", "")))
        self.twist_edit.setText(profile.get("twist", ""))
        self.muzzle_velocity_edit.setText(str(profile.get("muzzle_velocity_mps", "")))
        self.notes_edit.setPlainText(profile.get("notes", ""))
        # Populate optics (use first optic as active)
        optics = profile.get("optics", [])
        if optics and len(optics) > 0:
            o = optics[0]
            self.optic_name_edit.setText(o.get("name", ""))
            self.optic_manufacturer_edit.setText(o.get("manufacturer", ""))
            self.optic_zero_distance_edit.setText(str(o.get("zero_distance_m", "")))
            unit = o.get("turret_units", "mil")
            idx = self.optic_unit_combo.findText(unit)
            if idx >= 0:
                self.optic_unit_combo.setCurrentIndex(idx)
            self.optic_click_value_edit.setText(str(o.get("click_value", "")))
            self.optic_clicks_per_rev_edit.setText(str(o.get("clicks_per_rev", "")))
        else:
            self.optic_name_edit.setText("")
            self.optic_manufacturer_edit.setText("")
            self.optic_zero_distance_edit.setText("")
            self.optic_unit_combo.setCurrentIndex(0)
            self.optic_click_value_edit.setText("")
            self.optic_clicks_per_rev_edit.setText("")
        self._refresh_barrel_selector(profile)

    def _on_select(self, index: int):
        if 0 <= index < len(self._data):
            self._populate_fields(self._data[index])

    def _on_new(self):
        new_profile = {
            "id": f"new-{len(self._data)+1}",
            "name": "New Weapon",
            "caliber": "",
            "barrel_length_mm": None,
            "twist": "",
            "muzzle_velocity_mps": None,
            "notes": "",
        }
        self._data.append(new_profile)
        self._refresh_selector()
        self.profile_select.setCurrentIndex(len(self._data) - 1)

    def _on_barrel_select(self, index: int):
        # nothing to populate inline; barrels are edited in a dialog
        return

    def _on_new_barrel(self):
        idx = self.profile_select.currentIndex()
        if not (0 <= idx < len(self._data)):
            QMessageBox.information(self, "No profile", "Select a profile first.")
            return
        profile = self._data[idx]
        new_barrel = {
            "id": f"barrel-{len(profile.get('barrels', [])) + 1}",
            "name": "New Barrel",
            "length_mm": None,
            "material": "",
            "mount_type": "",
            "measurement_points": [],
        }
        profile.setdefault("barrels", []).append(new_barrel)
        self._refresh_barrel_selector(profile)
        self.barrel_select.setCurrentIndex(len(profile["barrels"]) - 1)

    def _on_edit_barrel(self):
        idx = self.profile_select.currentIndex()
        if not (0 <= idx < len(self._data)):
            QMessageBox.information(self, "No profile", "Select a profile first.")
            return
        profile = self._data[idx]
        bidx = self.barrel_select.currentIndex()
        if not (0 <= bidx < len(profile.get("barrels", []))):
            QMessageBox.information(self, "No barrel", "Select a barrel first.")
            return
        barrel = profile["barrels"][bidx]
        dlg = BarrelEditorDialog(barrel, parent=self)
        if dlg.exec():
            updated = dlg.gather()
            profile["barrels"][bidx] = updated
            self._refresh_barrel_selector(profile)

    def _on_add_calibration_test(self):
        idx = self.profile_select.currentIndex()
        if not (0 <= idx < len(self._data)):
            QMessageBox.information(self, "No profile", "Select a profile first.")
            return
        profile = self._data[idx]
        bidx = self.barrel_select.currentIndex()
        if not (0 <= bidx < len(profile.get("barrels", []))):
            QMessageBox.information(self, "No barrel", "Select a barrel first.")
            return
        barrel = profile["barrels"][bidx]
        dlg = CalibrationTestDialog(parent=self, profile=profile, persist_callback=self._save_data)
        if dlg.exec():
            data = dlg.gather()
            # convert into storage: add to barrel['calibration_tests']
            barrel.setdefault("calibration_tests", [])
            # create a simple id
            nid = f"ct-{len(barrel['calibration_tests'])+1}"
            data_obj = {"id": nid, "barrel_id": barrel.get("id"), "loads": data.get("loads", []), "notes": data.get("notes", "")}
            barrel["calibration_tests"].append(data_obj)
            QMessageBox.information(self, "Saved", "Calibration test saved to profile.")

    def _on_view_calibration_tests(self):
        idx = self.profile_select.currentIndex()
        if not (0 <= idx < len(self._data)):
            QMessageBox.information(self, "No profile", "Select a profile first.")
            return
        profile = self._data[idx]
        bidx = self.barrel_select.currentIndex()
        if not (0 <= bidx < len(profile.get("barrels", []))):
            QMessageBox.information(self, "No barrel", "Select a barrel first.")
            return
        barrel = profile["barrels"][bidx]
        from src.ui.calibration_tests_viewer import CalibrationTestsViewer

        dlg = CalibrationTestsViewer(barrel, parent=self)
        dlg.exec()

    def _on_remove_barrel(self):
        idx = self.profile_select.currentIndex()
        if not (0 <= idx < len(self._data)):
            return
        profile = self._data[idx]
        bidx = self.barrel_select.currentIndex()
        if not (0 <= bidx < len(profile.get("barrels", []))):
            return
        if (
            QMessageBox.question(self, "Remove Barrel", "Remove selected barrel?")
            == QMessageBox.StandardButton.Yes
        ):
            del profile["barrels"][bidx]
            self._refresh_barrel_selector(profile)

    def _on_view_optics_history(self):
        idx = self.profile_select.currentIndex()
        if not (0 <= idx < len(self._data)):
            QMessageBox.information(self, "No profile", "Select a profile first.")
            return
        profile = self._data[idx]
        dlg = OpticsHistoryDialog(profile, persist_callback=self._save_data, parent=self)
        dlg.exec()

    def _gather_current(self) -> dict:
        idx = self.profile_select.currentIndex()
        profile = self._data[idx] if 0 <= idx < len(self._data) else {}
        profile["name"] = self.name_edit.text().strip()
        profile["caliber"] = self.caliber_edit.text().strip()
        try:
            profile["barrel_length_mm"] = (
                int(self.barrel_length_edit.text())
                if self.barrel_length_edit.text().strip()
                else None
            )
        except ValueError:
            profile["barrel_length_mm"] = None
        profile["twist"] = self.twist_edit.text().strip()
        try:
            profile["muzzle_velocity_mps"] = (
                float(self.muzzle_velocity_edit.text())
                if self.muzzle_velocity_edit.text().strip()
                else None
            )
        except ValueError:
            profile["muzzle_velocity_mps"] = None
        profile["notes"] = self.notes_edit.toPlainText().strip()
        # gather optics (store as single-entry list if provided)
        optic_name = self.optic_name_edit.text().strip()
        if optic_name:
            try:
                zero_d = (
                    float(self.optic_zero_distance_edit.text())
                    if self.optic_zero_distance_edit.text().strip()
                    else None
                )
            except ValueError:
                zero_d = None
            try:
                click_val = (
                    float(self.optic_click_value_edit.text())
                    if self.optic_click_value_edit.text().strip()
                    else None
                )
            except ValueError:
                click_val = None
            try:
                clicks_rev = (
                    int(self.optic_clicks_per_rev_edit.text())
                    if self.optic_clicks_per_rev_edit.text().strip()
                    else None
                )
            except ValueError:
                clicks_rev = None
            optic = {
                "id": "optic-1",
                "name": optic_name,
                "manufacturer": self.optic_manufacturer_edit.text().strip(),
                "type": "telescopic",
                "zero_distance_m": zero_d,
                "turret_units": self.optic_unit_combo.currentText(),
                "click_value": click_val,
                "clicks_per_rev": clicks_rev,
                "notes": "",
            }
            profile["optics"] = [optic]
        else:
            # keep existing optics if no optic set in UI
            profile.setdefault("optics", profile.get("optics", []))
        return profile

    def _on_save(self):
        if not self._data:
            QMessageBox.information(self, "Nothing to save", "No profiles to save.")
            return
        idx = self.profile_select.currentIndex()
        if 0 <= idx < len(self._data):
            self._data[idx] = self._gather_current()
            try:
                self._save_data()
                QMessageBox.information(
                    self, "Saved", f"Profiles saved to {self.data_path}"
                )
                self._refresh_selector()
            except Exception as e:
                QMessageBox.critical(self, "Error saving", str(e))

    def _on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save profiles as...", str(self.data_path), "JSON Files (*.json)"
        )
        if path:
            try:
                # ensure current data is updated
                idx = self.profile_select.currentIndex()
                if 0 <= idx < len(self._data):
                    self._data[idx] = self._gather_current()
                self._save_data(Path(path))
                QMessageBox.information(self, "Saved", f"Profiles saved to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error saving", str(e))

    def _on_delete(self):
        idx = self.profile_select.currentIndex()
        if 0 <= idx < len(self._data):
            if (
                QMessageBox.question(self, "Delete", "Delete selected profile?")
                == QMessageBox.StandardButton.Yes
            ):
                del self._data[idx]
                self._refresh_selector()


class OpticsHistoryDialog(QDialog):
    """Dialog to view and manage optics_history entries on a profile."""

    def __init__(self, profile: dict, persist_callback=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optics History")
        self.resize(800, 400)
        self.profile = profile
        self._persist = persist_callback
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Timestamp",
            "Load Index",
            "V Angle",
            "V Clicks",
            "H Angle",
            "H Clicks",
            "Meta",
        ])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._on_remove_selected)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self._load_entries()

    def _load_entries(self) -> None:
        self.table.setRowCount(0)
        entries = self.profile.get("optics_history", [])
        for i, e in enumerate(entries):
            row = self.table.rowCount()
            self.table.insertRow(row)
            ts = e.get("timestamp", "")
            li = str(e.get("load_index", ""))
            v = e.get("vertical") or {}
            h = e.get("horizontal") or {}
            v_angle = f"{v.get('angle_unit'):.3f}" if v and v.get("angle_unit") is not None else ""
            v_clicks = str(v.get("clicks", "")) if v else ""
            h_angle = f"{h.get('angle_unit'):.3f}" if h and h.get("angle_unit") is not None else ""
            h_clicks = str(h.get("clicks", "")) if h else ""
            meta = str(e.get("meta", {}))

            self.table.setItem(row, 0, QTableWidgetItem(ts))
            self.table.setItem(row, 1, QTableWidgetItem(li))
            self.table.setItem(row, 2, QTableWidgetItem(v_angle))
            self.table.setItem(row, 3, QTableWidgetItem(v_clicks))
            self.table.setItem(row, 4, QTableWidgetItem(h_angle))
            self.table.setItem(row, 5, QTableWidgetItem(h_clicks))
            self.table.setItem(row, 6, QTableWidgetItem(meta))

    def _on_remove_selected(self) -> None:
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.information(self, "No selection", "Select a row to remove.")
            return
        # selectedItems returns all cells; get unique rows
        rows = sorted({item.row() for item in sel}, reverse=True)
        entries = self.profile.get("optics_history", [])
        for r in rows:
            if 0 <= r < len(entries):
                del entries[r]
        # persist if callback provided
        try:
            if callable(self._persist):
                self._persist()
        except Exception:
            QMessageBox.warning(self, "Persist failed", "Failed to persist optics history after removal.")
        self.profile["optics_history"] = entries
        self._load_entries()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dlg = WeaponProfileEditor()
    dlg.show()
    sys.exit(app.exec())
