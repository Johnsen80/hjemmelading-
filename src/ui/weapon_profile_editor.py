import json
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QFileDialog,
)


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

        self.data_path = Path(data_path) if data_path else DEFAULT_DATA
        self._data = []
        self._load_data()

        self.layout = QVBoxLayout(self)

        self.selector_layout = QHBoxLayout()
        self.profile_select = QComboBox()
        self.profile_select.currentIndexChanged.connect(self._on_select)
        self.selector_layout.addWidget(self.profile_select)

        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._on_new)
        self.selector_layout.addWidget(self.new_btn)

        self.layout.addLayout(self.selector_layout)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.caliber_edit = QLineEdit()
        self.barrel_length_edit = QLineEdit()
        self.twist_edit = QLineEdit()
        self.muzzle_velocity_edit = QLineEdit()
        self.notes_edit = QTextEdit()

        form.addRow("Name:", self.name_edit)
        form.addRow("Caliber:", self.caliber_edit)
        form.addRow("Barrel length (mm):", self.barrel_length_edit)
        form.addRow("Twist:", self.twist_edit)
        form.addRow("Muzzle velocity (m/s):", self.muzzle_velocity_edit)
        form.addRow("Notes:", self.notes_edit)

        self.layout.addLayout(form)

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

        self.layout.addLayout(btn_row)

        self._refresh_selector()

    def _load_data(self):
        try:
            if self.data_path.exists():
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = []
        except Exception:
            self._data = []

    def _save_data(self, path: Optional[Path] = None):
        target = Path(path) if path else self.data_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def _refresh_selector(self):
        self.profile_select.blockSignals(True)
        self.profile_select.clear()
        for p in self._data:
            self.profile_select.addItem(p.get("name", p.get("id", "Unnamed")))
        self.profile_select.blockSignals(False)
        if self._data:
            self.profile_select.setCurrentIndex(0)
            self._populate_fields(self._data[0])

    def _populate_fields(self, profile: dict):
        self.name_edit.setText(profile.get("name", ""))
        self.caliber_edit.setText(profile.get("caliber", ""))
        self.barrel_length_edit.setText(str(profile.get("barrel_length_mm", "")))
        self.twist_edit.setText(profile.get("twist", ""))
        self.muzzle_velocity_edit.setText(str(profile.get("muzzle_velocity_mps", "")))
        self.notes_edit.setPlainText(profile.get("notes", ""))

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

    def _gather_current(self) -> dict:
        idx = self.profile_select.currentIndex()
        profile = self._data[idx] if 0 <= idx < len(self._data) else {}
        profile["name"] = self.name_edit.text().strip()
        profile["caliber"] = self.caliber_edit.text().strip()
        try:
            profile["barrel_length_mm"] = int(self.barrel_length_edit.text()) if self.barrel_length_edit.text().strip() else None
        except ValueError:
            profile["barrel_length_mm"] = None
        profile["twist"] = self.twist_edit.text().strip()
        try:
            profile["muzzle_velocity_mps"] = float(self.muzzle_velocity_edit.text()) if self.muzzle_velocity_edit.text().strip() else None
        except ValueError:
            profile["muzzle_velocity_mps"] = None
        profile["notes"] = self.notes_edit.toPlainText().strip()
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
                QMessageBox.information(self, "Saved", f"Profiles saved to {self.data_path}")
                self._refresh_selector()
            except Exception as e:
                QMessageBox.critical(self, "Error saving", str(e))

    def _on_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save profiles as...", str(self.data_path), "JSON Files (*.json)")
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
            if QMessageBox.question(self, "Delete", "Delete selected profile?") == QMessageBox.StandardButton.Yes:
                del self._data[idx]
                self._refresh_selector()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dlg = WeaponProfileEditor()
    dlg.show()
    sys.exit(app.exec())
