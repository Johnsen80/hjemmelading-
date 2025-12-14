from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class BarrelEditorDialog(QDialog):
    """Simple dialog to edit a barrel dict.

    The dialog expects a barrel-like dict and returns the updated dict via
    `gather()` if accepted. For now measurement points can be edited as JSON
    in a textarea (simple and robust for first iteration).
    """

    def __init__(self, barrel: Optional[Dict[str, Any]] = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Barrel Editor")
        self.resize(520, 360)
        # allow stylesheet targeting and apply central stylesheet safely
        try:
            from src.ui.reloading_theme import ReloadingTheme

            self.setObjectName("barrelEditorDialog")
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception:
            pass
        self._barrel = barrel.copy() if barrel else {}
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(self._barrel.get("name", ""))
        form.addRow("Name:", self.name_edit)

        self.length_edit = QLineEdit(str(self._barrel.get("length_mm", "")))
        form.addRow("Length (mm):", self.length_edit)

        self.material_edit = QLineEdit(self._barrel.get("material", ""))
        form.addRow("Material:", self.material_edit)

        self.mount_edit = QLineEdit(self._barrel.get("mount_type", ""))
        form.addRow("Mount Type:", self.mount_edit)

        # Muzzle device fields
        self.muzzle_type_edit = QLineEdit(self._barrel.get("muzzle_device_type", ""))
        form.addRow("Muzzle device type:", self.muzzle_type_edit)

        self.muzzle_weight_edit = QLineEdit(
            str(self._barrel.get("muzzle_device_weight_g", ""))
        )
        form.addRow("Muzzle device weight (g):", self.muzzle_weight_edit)

        self.muzzle_length_edit = QLineEdit(
            str(self._barrel.get("muzzle_device_length_mm", ""))
        )
        form.addRow("Muzzle device length (mm):", self.muzzle_length_edit)

        self.measurements_text = QTextEdit()
        mp = self._barrel.get("measurement_points", [])
        try:
            import json

            self.measurements_text.setPlainText(
                json.dumps(mp, indent=2, ensure_ascii=False)
            )
        except Exception:
            self.measurements_text.setPlainText(str(mp))
        form.addRow(QLabel("Measurement points (JSON array):"), self.measurements_text)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("OK")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def gather(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data["id"] = self._barrel.get("id", "")
        data["name"] = self.name_edit.text().strip()
        try:
            data["length_mm"] = (
                float(self.length_edit.text())
                if self.length_edit.text().strip()
                else None
            )
        except ValueError:
            data["length_mm"] = None
        data["material"] = self.material_edit.text().strip()
        data["mount_type"] = self.mount_edit.text().strip()
        # muzzle device
        try:
            data["muzzle_device_weight_g"] = (
                float(self.muzzle_weight_edit.text())
                if self.muzzle_weight_edit.text().strip()
                else None
            )
        except ValueError:
            data["muzzle_device_weight_g"] = None
        try:
            data["muzzle_device_length_mm"] = (
                float(self.muzzle_length_edit.text())
                if self.muzzle_length_edit.text().strip()
                else None
            )
        except ValueError:
            data["muzzle_device_length_mm"] = None
        data["muzzle_device_type"] = self.muzzle_type_edit.text().strip()
        # parse measurement points JSON
        try:
            import json

            mp = json.loads(self.measurements_text.toPlainText())
            if isinstance(mp, list):
                data["measurement_points"] = mp
            else:
                data["measurement_points"] = []
        except Exception:
            QMessageBox.warning(
                self,
                "Invalid JSON",
                "Measurement points JSON could not be parsed. Using empty list.",
            )
            data["measurement_points"] = []
        return data
