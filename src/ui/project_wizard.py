from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..qt_compat import QSettings, QtWidgets
from ..utils.i18n import tr
from .reloading_theme import ReloadingTheme

# pyright: reportOptionalCall=false


QCheckBox = QtWidgets.QCheckBox
QDialog = QtWidgets.QDialog
QFileDialog = QtWidgets.QFileDialog
QFormLayout = QtWidgets.QFormLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QLabel = QtWidgets.QLabel
QLineEdit = QtWidgets.QLineEdit
QMessageBox = QtWidgets.QMessageBox
QPushButton = QtWidgets.QPushButton
QVBoxLayout = QtWidgets.QVBoxLayout


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("project_wizard_title"))
        self.setMinimumSize(520, 360)
        self.setObjectName("newProjectDialog")
        try:
            self.setStyleSheet(ReloadingTheme.get_stylesheet())
        except Exception as e:
            import logging

            logging.getLogger("HjemmeladingApp").warning(
                f"Kunne ikke sette stilark: {e}"
            )
            try:
                QMessageBox.warning(
                    self,
                    tr("project_wizard_stylesheet_title"),
                    tr("project_wizard_stylesheet_error", error=e),
                )
            except Exception:
                pass

        self.project_path: str = ""
        self.pin_project: bool = False

        layout = QVBoxLayout(self)

        title = QLabel(tr("project_wizard_heading"))
        layout.addWidget(title)

        subtitle = QLabel(tr("project_wizard_subtitle"))
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        form = QFormLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText(tr("project_wizard_name_placeholder"))
        form.addRow(tr("project_wizard_name"), self.name_input)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText(tr("project_wizard_base_folder_placeholder"))
        browse_btn = QPushButton(tr("btn_browse"), self)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(browse_btn)
        form.addRow(tr("project_wizard_location"), path_row)

        self.create_data_check = QCheckBox(
            tr("project_wizard_create_data_folder"), self
        )
        self.create_data_check.setChecked(True)
        form.addRow("", self.create_data_check)

        self.copy_demo_check = QCheckBox(tr("project_wizard_copy_demo_data"), self)
        form.addRow("", self.copy_demo_check)

        self.pin_check = QCheckBox(tr("project_wizard_pin_recent"), self)
        self.pin_check.setChecked(True)
        form.addRow("", self.pin_check)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(tr("btn_cancel"), self)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        create_btn = QPushButton(tr("project_wizard_create"), self)
        create_btn.clicked.connect(self._create_project)
        btn_row.addWidget(create_btn)
        layout.addLayout(btn_row)

        self._load_defaults()

    def _load_defaults(self) -> None:
        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            base = settings.value("workspace/last_project_base", "")
        except Exception:
            base = ""
        if not base:
            base = str(Path.home())
        self.path_input.setText(base)

    def _browse(self) -> None:
        try:
            base = QFileDialog.getExistingDirectory(
                self, tr("project_wizard_select_base")
            )
        except Exception:
            base = ""
        if base:
            self.path_input.setText(base)

    def _sanitize_name(self, name: str) -> str:
        invalid = '<>:/\\|?*"'
        cleaned = "".join("_" if ch in invalid else ch for ch in name).strip()
        return cleaned

    def _create_project(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                tr("project_wizard_missing_name"),
                tr("project_wizard_missing_name_body"),
            )
            return

        base = self.path_input.text().strip()
        if not base:
            base = str(Path.home())

        safe_name = self._sanitize_name(name)
        if not safe_name:
            QMessageBox.warning(
                self,
                tr("project_wizard_invalid_name"),
                tr("project_wizard_invalid_name_body"),
            )
            return

        project_dir = Path(base).expanduser() / safe_name

        if project_dir.exists():
            try:
                has_files = any(project_dir.iterdir())
            except Exception:
                has_files = True
            if has_files:
                reply = QMessageBox.question(
                    self,
                    tr("project_wizard_folder_exists"),
                    tr("project_wizard_folder_exists_body"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
        else:
            try:
                project_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    tr("project_wizard_create_failed"),
                    tr("project_wizard_create_failed_body", error=exc),
                )
                return

        data_dir: Optional[Path] = None
        if self.create_data_check.isChecked():
            data_dir = project_dir / "data"
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                data_dir = None

        if self.copy_demo_check.isChecked() and data_dir is not None:
            demo_src = (
                Path(__file__).resolve().parents[2] / "data" / "demo_weapons.json"
            )
            if demo_src.exists():
                try:
                    target = data_dir / "demo_weapons.json"
                    target.write_text(
                        demo_src.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                except Exception as e:
                    import logging

                    logging.getLogger("HjemmeladingApp").warning(
                        f"Kunne ikke kopiere demo-data: {e}"
                    )
                    try:
                        QMessageBox.warning(
                            self,
                            tr("project_wizard_demo_data"),
                            tr("project_wizard_demo_data_error", error=e),
                        )
                    except Exception:
                        pass

        meta = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "version": 1,
        }
        try:
            meta_path = project_dir / "hjemmelading_project.json"
            with meta_path.open("w", encoding="utf-8") as fh:
                json.dump(meta, fh, indent=2, ensure_ascii=True)
        except Exception as e:
            import logging

            logging.getLogger("HjemmeladingApp").warning(
                f"Kunne ikke skrive prosjekt-metadata: {e}"
            )
            try:
                QMessageBox.warning(
                    self,
                    tr("project_wizard_metadata_title"),
                    tr("project_wizard_metadata_error", error=e),
                )
            except Exception:
                pass

        try:
            settings = QSettings("ReloadingWorkshop", "ReloadingManager")
            settings.setValue("workspace/last_project_base", str(project_dir.parent))
        except Exception as e:
            import logging

            logging.getLogger("HjemmeladingApp").warning(
                f"Kunne ikke lagre siste prosjektbase: {e}"
            )
            try:
                QMessageBox.warning(
                    self,
                    tr("settings_title"),
                    tr("project_wizard_last_base_error", error=e),
                )
            except Exception:
                pass

        self.project_path = str(project_dir)
        self.pin_project = self.pin_check.isChecked()
        self.accept()
