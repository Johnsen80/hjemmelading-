from __future__ import annotations

from typing import Any, Dict, List

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from src.modules.calibration_test import ChronoData
from src.modules.image_analysis import analyze_group_image
from src.ui.calibration_analysis_dialog import CalibrationAnalysisDialog


class CalibrationTestsViewer(QDialog):
    """Viewer for saved calibration tests attached to a barrel dict."""

    def __init__(self, barrel: Dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibration Tests")
        self.resize(600, 400)
        self.barrel = barrel
        self._tests: List[Dict[str, Any]] = barrel.get("calibration_tests", [])
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.listw = QListWidget()
        for t in self._tests:
            self.listw.addItem(t.get("id", "Unnamed"))
        layout.addWidget(self.listw)

        row = QHBoxLayout()
        self.view_btn = QPushButton("View")
        self.view_btn.clicked.connect(self._on_view)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        row.addWidget(self.view_btn)
        row.addWidget(self.delete_btn)
        row.addStretch()
        row.addWidget(self.close_btn)
        layout.addLayout(row)

    def _selected_test(self) -> Dict[str, Any] | None:
        idx = self.listw.currentRow()
        if 0 <= idx < len(self._tests):
            return self._tests[idx]
        return None

    def _on_view(self) -> None:
        t = self._selected_test()
        if not t:
            QMessageBox.information(self, "No selection", "Select a test first.")
            return
        # build results list for analysis dialog
        results = []
        for load in t.get("loads", []):
            velocities = load.get("velocities", [])
            chrono = ChronoData(velocities)
            chrono_stats = chrono.stats()
            img_path = load.get("group_image_path")
            img_res = None
            if img_path:
                img_res = analyze_group_image(img_path, dpi=load.get("mm_per_pixel") and (1.0 / load.get("mm_per_pixel")))
            results.append({"chrono_stats": chrono_stats, "image_analysis": img_res, "image_path": img_path})
        dlg = CalibrationAnalysisDialog(results=results, parent=self)
        dlg.exec()

    def _on_delete(self) -> None:
        idx = self.listw.currentRow()
        if not (0 <= idx < len(self._tests)):
            return
        if QMessageBox.question(self, "Delete", "Delete selected test?") == QMessageBox.StandardButton.Yes:
            del self._tests[idx]
            self.listw.takeItem(idx)
            # update barrel storage
            self.barrel["calibration_tests"] = self._tests
