"""
Rifles & Optikk Manager Widget
Håndterer administrasjon av rifles og optikk
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database
from ..utils.i18n import tr


class RifleOpticManager(QWidget):
    """Widget for å administrere rifles og optikk"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel(tr("rifle_optics_title"))
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel(tr("rifle_optics_subtitle"))
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        # Hovedinnhold
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)

        # Venstre side - Rifles
        rifles_widget = self.create_rifles_section()
        content_layout.addWidget(rifles_widget, 1)

        # Høyre side - Optikk
        optics_widget = self.create_optics_section()
        content_layout.addWidget(optics_widget, 1)

    def create_rifles_section(self):
        """Oppretter rifles-seksjon"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Header
        header = QLabel(tr("rifle_optics_rifles"))
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        # Knapper
        btn_layout = QHBoxLayout()
        add_rifle_btn = QPushButton(tr("rifle_optics_new_rifle"))
        add_rifle_btn.setProperty("variant", "primary")
        add_rifle_btn.clicked.connect(self.add_rifle)
        btn_layout.addWidget(add_rifle_btn)

        edit_rifle_btn = QPushButton(tr("rifle_optics_edit"))
        edit_rifle_btn.setProperty("variant", "secondary")
        edit_rifle_btn.clicked.connect(self.edit_rifle)
        btn_layout.addWidget(edit_rifle_btn)

        delete_rifle_btn = QPushButton(tr("rifle_optics_delete"))
        delete_rifle_btn.setProperty("variant", "ghost")
        delete_rifle_btn.clicked.connect(self.delete_rifle)
        btn_layout.addWidget(delete_rifle_btn)

        layout.addLayout(btn_layout)

        # Tabell
        self.rifles_table = QTableWidget()
        self.rifles_table.setColumnCount(4)
        self.rifles_table.setHorizontalHeaderLabels(
            [
                tr("rifle_optics_col_name"),
                tr("rifle_optics_col_caliber"),
                tr("rifle_optics_col_barrel"),
                tr("rifle_optics_col_manufacturer"),
            ]
        )
        self.rifles_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.rifles_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.rifles_table)

        return widget

    def create_optics_section(self):
        """Oppretter optikk-seksjon"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Header
        header = QLabel(tr("rifle_optics_optics"))
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        # Knapper
        btn_layout = QHBoxLayout()
        add_optic_btn = QPushButton(tr("rifle_optics_new_optic"))
        add_optic_btn.setProperty("variant", "primary")
        add_optic_btn.clicked.connect(self.add_optic)
        btn_layout.addWidget(add_optic_btn)

        edit_optic_btn = QPushButton(tr("rifle_optics_edit"))
        edit_optic_btn.setProperty("variant", "secondary")
        edit_optic_btn.clicked.connect(self.edit_optic)
        btn_layout.addWidget(edit_optic_btn)

        delete_optic_btn = QPushButton(tr("rifle_optics_delete"))
        delete_optic_btn.setProperty("variant", "ghost")
        delete_optic_btn.clicked.connect(self.delete_optic)
        btn_layout.addWidget(delete_optic_btn)

        layout.addLayout(btn_layout)

        # Tabell
        self.optics_table = QTableWidget()
        self.optics_table.setColumnCount(5)
        self.optics_table.setHorizontalHeaderLabels(
            [
                tr("rifle_optics_col_name"),
                tr("rifle_optics_col_click"),
                tr("rifle_optics_col_unit"),
                tr("rifle_optics_col_zero"),
                tr("rifle_optics_col_rifle"),
            ]
        )
        self.optics_table.horizontalHeader().setStretchLastSection(True)  # type: ignore[union-attr]
        self.optics_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.optics_table)

        return widget

    def load_data(self):
        """Laster data fra database"""
        self.load_rifles()
        self.load_optics()

    def load_rifles(self):
        """Laster rifles fra database"""
        rifles = self.db.get_all("rifles", "name")
        self.rifles_table.setRowCount(len(rifles))

        for i, rifle in enumerate(rifles):
            self.rifles_table.setItem(i, 0, QTableWidgetItem(rifle["name"]))
            self.rifles_table.setItem(i, 1, QTableWidgetItem(rifle["caliber"]))
            barrel = f"{rifle['barrel_length']}" if rifle["barrel_length"] else "-"
            self.rifles_table.setItem(i, 2, QTableWidgetItem(barrel))
            mfg = rifle["manufacturer"] if rifle["manufacturer"] else "-"
            self.rifles_table.setItem(i, 3, QTableWidgetItem(mfg))
            # Lagre ID i første celle
            self.rifles_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, rifle["id"])

    def load_optics(self):
        """Laster optikk fra database"""
        optics = self.db.get_all("optics", "name")
        self.optics_table.setRowCount(len(optics))

        for i, optic in enumerate(optics):
            self.optics_table.setItem(i, 0, QTableWidgetItem(optic["name"]))
            click = f"{optic['click_value_elevation']}"
            self.optics_table.setItem(i, 1, QTableWidgetItem(click))
            self.optics_table.setItem(i, 2, QTableWidgetItem(optic["click_unit"]))
            zero = f"{optic['zero_distance']}" if optic["zero_distance"] else "100"
            self.optics_table.setItem(i, 3, QTableWidgetItem(zero))

            # Finn rifle-navn
            rifle_name = "-"
            if optic["rifle_id"]:
                rifle = self.db.get_by_id("rifles", optic["rifle_id"])
                if rifle:
                    rifle_name = rifle["name"]
            self.optics_table.setItem(i, 4, QTableWidgetItem(rifle_name))

            # Lagre ID
            self.optics_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, optic["id"])

    def add_rifle(self):
        """Åpner dialog for å legge til rifle"""
        dialog = RifleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("rifles", data)
            self.load_rifles()
            QMessageBox.information(
                self, tr("msg_success"), tr("rifle_optics_rifle_added")
            )

    def edit_rifle(self):
        """Redigerer valgt rifle"""
        selected = self.rifles_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("rifle_optics_select_rifle_first")
            )
            return

        rifle_id = self.rifles_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        rifle = self.db.get_by_id("rifles", rifle_id)
        if not rifle:
            QMessageBox.warning(
                self,
                tr("rifle_optics_rifle_missing_title"),
                tr("rifle_optics_rifle_missing_message"),
            )
            self.load_rifles()
            return

        dialog = RifleDialog(self, rifle)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("rifles", data, "id = ?", (rifle_id,))
            self.load_rifles()
            QMessageBox.information(
                self, tr("msg_success"), tr("rifle_optics_rifle_updated")
            )

    def delete_rifle(self):
        """Sletter valgt rifle"""
        selected = self.rifles_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("rifle_optics_select_rifle_first")
            )
            return

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_delete"),
            tr("rifle_optics_confirm_delete_rifle"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            rifle_id = self.rifles_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("rifles", "id = ?", (rifle_id,))
            self.load_rifles()
            QMessageBox.information(
                self, tr("msg_success"), tr("rifle_optics_rifle_deleted")
            )

    def add_optic(self):
        """Åpner dialog for å legge til optikk"""
        rifles = self.db.get_all("rifles")
        dialog = OpticDialog(self, rifles=rifles)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("optics", data)
            self.load_optics()
            QMessageBox.information(
                self, tr("msg_success"), tr("rifle_optics_optic_added")
            )

    def edit_optic(self):
        """Redigerer valgt optikk"""
        selected = self.optics_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("rifle_optics_select_optic_first")
            )
            return

        optic_id = self.optics_table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        optic = self.db.get_by_id("optics", optic_id)
        rifles = self.db.get_all("rifles")
        if not optic:
            QMessageBox.warning(
                self,
                tr("rifle_optics_optic_missing_title"),
                tr("rifle_optics_optic_missing_message"),
            )
            self.load_optics()
            return

        dialog = OpticDialog(self, optic, rifles)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("optics", data, "id = ?", (optic_id,))
            self.load_optics()
            QMessageBox.information(
                self, tr("msg_success"), tr("rifle_optics_optic_updated")
            )

    def delete_optic(self):
        """Sletter valgt optikk"""
        selected = self.optics_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self, tr("msg_no_selection"), tr("rifle_optics_select_optic_first")
            )
            return

        reply = QMessageBox.question(
            self,
            tr("msg_confirm_delete"),
            tr("rifle_optics_confirm_delete_optic"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            optic_id = self.optics_table.item(selected, 0).data(
                Qt.ItemDataRole.UserRole
            )
            self.db.delete("optics", "id = ?", (optic_id,))
            self.load_optics()
            QMessageBox.information(
                self, tr("msg_success"), tr("rifle_optics_optic_deleted")
            )


class RifleDialog(QDialog):
    """Dialog for å legge til/redigere rifle"""

    def __init__(self, parent=None, rifle=None):
        super().__init__(parent)
        self.rifle = rifle
        self.init_ui()
        if rifle:
            self.load_rifle_data()

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle(
            tr("rifle_optics_rifle_dialog_edit")
            if self.rifle
            else tr("rifle_optics_rifle_dialog_new")
        )
        self.setMinimumWidth(500)

        layout = QFormLayout()
        self.setLayout(layout)

        # Spec lookup section
        ai_layout = QHBoxLayout()
        ai_info = QLabel(tr("rifle_optics_ai_info"))
        ai_info.setWordWrap(True)
        ai_info.setProperty("role", "muted")
        ai_layout.addWidget(ai_info)

        self.ai_lookup_btn = QPushButton(tr("rifle_optics_ai_lookup"))
        self.ai_lookup_btn.setProperty("variant", "secondary")
        self.ai_lookup_btn.clicked.connect(self.run_ai_lookup)
        ai_layout.addWidget(self.ai_lookup_btn)

        layout.addRow(ai_layout)

        # Separator
        separator = QLabel(" ")
        layout.addRow(separator)

        # Felter
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr("rifle_optics_name_placeholder"))
        layout.addRow(tr("rifle_optics_name"), self.name_input)

        self.manufacturer = QLineEdit()
        self.manufacturer.setPlaceholderText(
            tr("rifle_optics_manufacturer_placeholder")
        )
        layout.addRow(tr("rifle_optics_manufacturer"), self.manufacturer)

        self.caliber_input = QLineEdit()
        self.caliber_input.setPlaceholderText(tr("rifle_optics_caliber_placeholder"))
        layout.addRow(tr("rifle_optics_caliber"), self.caliber_input)

        # Unit selection for barrel length
        unit_layout = QHBoxLayout()
        self.radio_metric = QRadioButton("mm")
        self.radio_imperial = QRadioButton(tr("rifle_optics_inches"))
        self.radio_metric.setChecked(True)
        self.radio_metric.toggled.connect(self.on_unit_changed)
        unit_layout.addWidget(self.radio_metric)
        unit_layout.addWidget(self.radio_imperial)
        unit_layout.addStretch()
        layout.addRow(tr("rifle_optics_measure_unit"), unit_layout)

        self.barrel_length = QDoubleSpinBox()
        self.barrel_length.setRange(400, 800)  # Start with metric (mm)
        self.barrel_length.setValue(610)  # ~24 inches
        self.barrel_length.setSuffix(" mm")
        self.barrel_length.setDecimals(0)
        layout.addRow(tr("rifle_optics_barrel_length"), self.barrel_length)

        self.twist_rate = QLineEdit()
        self.twist_rate.setPlaceholderText(tr("rifle_optics_twist_placeholder"))
        layout.addRow(tr("rifle_optics_twist_rate"), self.twist_rate)

        self.action_type = QComboBox()
        self.action_type.addItems(
            [
                tr("rifle_optics_bolt_action"),
                tr("rifle_optics_semi_auto"),
                tr("rifle_optics_lever_action"),
                tr("rifle_optics_single_shot"),
                tr("rifle_optics_other"),
            ]
        )
        layout.addRow(tr("rifle_optics_action_type"), self.action_type)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText(tr("rifle_optics_notes_placeholder"))
        layout.addRow(tr("rifle_optics_notes"), self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("rifle_optics_save"))
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("rifle_optics_cancel"))
        cancel_btn.setProperty("variant", "ghost")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def on_unit_changed(self, checked):
        """Handle unit system toggle between metric and imperial"""
        if not checked:
            return

        if self.radio_metric.isChecked():
            # Metric mode
            if self.barrel_length.suffix() != " mm":
                current_val = self.barrel_length.value()
                self.barrel_length.setRange(400, 800)
                self.barrel_length.setValue(current_val * 25.4)
                self.barrel_length.setSuffix(" mm")
                self.barrel_length.setDecimals(0)
        else:
            # Imperial mode
            if self.barrel_length.suffix() != ' "':
                current_val = self.barrel_length.value()
                self.barrel_length.setRange(10, 50)
                self.barrel_length.setValue(current_val / 25.4)
                self.barrel_length.setSuffix(' "')
                self.barrel_length.setDecimals(1)

    def run_ai_lookup(self):
        """Kjører spesifikasjonsoppslag og fyller ut feltene (kan redigeres etterpå)."""
        rifle_name = self.name_input.text().strip()

        if not rifle_name:
            QMessageBox.warning(
                self,
                tr("rifle_optics_missing_name_title"),
                tr("rifle_optics_missing_name_message"),
            )
            return

        # Vis loading
        self.ai_lookup_btn.setEnabled(False)
        self.ai_lookup_btn.setText(tr("rifle_optics_searching"))

        try:
            from ..utils.rifle_ai_lookup import get_rifle_lookup_service

            ai_service = get_rifle_lookup_service()
            manufacturer = self.manufacturer.text().strip() or None

            # Kjør lookup
            result = ai_service.lookup_rifle(rifle_name, manufacturer)

            # Fyll ut feltene (brukeren kan endre alt)
            if result["manufacturer"]:
                self.manufacturer.setText(result["manufacturer"])

            if result["caliber"]:
                self.caliber_input.setText(result["caliber"])

            if result["barrel_length"]:
                # Lookup returns inches; convert if metric is selected.
                barrel_inches = result["barrel_length"]
                if self.radio_metric.isChecked():
                    self.barrel_length.setValue(barrel_inches * 25.4)  # Convert to mm
                else:
                    self.barrel_length.setValue(barrel_inches)

            if result["twist_rate"]:
                self.twist_rate.setText(result["twist_rate"])

            if result["action_type"]:
                index = self.action_type.findText(result["action_type"])
                if index >= 0:
                    self.action_type.setCurrentIndex(index)

            # Legg til oppslagsinfo i notater
            ai_note = f"\n\nSpec Lookup ({result['confidence']} confidence)"
            if result["sources"]:
                ai_note += f"\nKilder: {', '.join(result['sources'][:2])}"

            current_notes = self.notes.toPlainText()
            if result["notes"]:
                ai_note += f"\n{result['notes']}"

            self.notes.setText(current_notes + ai_note)

            # Vis resultat
            QMessageBox.information(
                self,
                tr("rifle_optics_ai_lookup_done_title"),
                tr(
                    "rifle_optics_ai_lookup_done_message",
                    confidence=result["confidence"],
                    manufacturer=result["manufacturer"] or tr("rifle_optics_unknown"),
                    caliber=result["caliber"] or tr("rifle_optics_no_caliber"),
                    barrel_length=result["barrel_length"] or tr("rifle_optics_unknown"),
                ),
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                tr("rifle_optics_ai_lookup_failed_title"),
                tr("rifle_optics_ai_lookup_failed_message", error=str(e)),
            )

        finally:
            self.ai_lookup_btn.setEnabled(True)
            self.ai_lookup_btn.setText(tr("rifle_optics_ai_lookup"))

    def load_rifle_data(self):
        """Laster rifle-data inn i felter"""
        self.name_input.setText(self.rifle["name"])
        if self.rifle["manufacturer"]:
            self.manufacturer.setText(self.rifle["manufacturer"])
        self.caliber_input.setText(self.rifle["caliber"])
        if self.rifle["barrel_length"]:
            self.barrel_length.setValue(self.rifle["barrel_length"])
        if self.rifle["twist_rate"]:
            self.twist_rate.setText(self.rifle["twist_rate"])
        if self.rifle["action_type"]:
            index = self.action_type.findText(self.rifle["action_type"])
            if index >= 0:
                self.action_type.setCurrentIndex(index)
        if self.rifle["notes"]:
            self.notes.setText(self.rifle["notes"])

    def get_data(self):
        """Returnerer data fra dialog"""
        return {
            "name": self.name_input.text(),
            "caliber": self.caliber_input.text(),
            "barrel_length": self.barrel_length.value(),
            "twist_rate": self.twist_rate.text(),
            "action_type": self.action_type.currentText(),
            "manufacturer": self.manufacturer.text(),
            "notes": self.notes.toPlainText(),
        }


class OpticDialog(QDialog):
    """Dialog for å legge til/redigere optikk"""

    def __init__(self, parent=None, optic=None, rifles=None):
        super().__init__(parent)
        self.optic = optic
        self.rifles = rifles or []
        self.init_ui()
        if optic:
            self.load_optic_data()

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle(
            tr("rifle_optics_optic_dialog_edit")
            if self.optic
            else tr("rifle_optics_optic_dialog_new")
        )
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        # Felter
        self.name_input = QLineEdit()
        layout.addRow(tr("rifle_optics_name"), self.name_input)

        self.manufacturer = QLineEdit()
        layout.addRow(tr("rifle_optics_manufacturer"), self.manufacturer)

        self.magnification = QLineEdit()
        self.magnification.setPlaceholderText(
            tr("rifle_optics_magnification_placeholder")
        )
        layout.addRow(tr("rifle_optics_magnification"), self.magnification)

        self.reticle = QLineEdit()
        layout.addRow(tr("rifle_optics_reticle"), self.reticle)

        # Klikk-verdier
        click_layout = QHBoxLayout()
        self.click_value = QDoubleSpinBox()
        self.click_value.setRange(0.01, 1.0)
        self.click_value.setValue(0.25)
        self.click_value.setDecimals(3)
        self.click_value.setSingleStep(0.01)
        click_layout.addWidget(self.click_value)

        self.click_unit = QComboBox()
        self.click_unit.addItems(["MOA", "MRAD"])
        click_layout.addWidget(self.click_unit)
        layout.addRow(tr("rifle_optics_click_value"), click_layout)

        self.zero_distance = QSpinBox()
        self.zero_distance.setRange(25, 500)
        self.zero_distance.setValue(100)
        self.zero_distance.setSuffix(" m")
        layout.addRow(tr("rifle_optics_zero_distance"), self.zero_distance)

        # Rifle dropdown
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem(tr("rifle_optics_no_rifle"), None)
        for rifle in self.rifles:
            self.rifle_combo.addItem(rifle["name"], rifle["id"])
        layout.addRow(tr("rifle_optics_mounted_on"), self.rifle_combo)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        layout.addRow(tr("rifle_optics_notes"), self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("rifle_optics_save"))
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("rifle_optics_cancel"))
        cancel_btn.setProperty("variant", "ghost")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def load_optic_data(self):
        """Laster optikk-data inn i felter"""
        self.name_input.setText(self.optic["name"])
        if self.optic["manufacturer"]:
            self.manufacturer.setText(self.optic["manufacturer"])
        if self.optic["magnification"]:
            self.magnification.setText(self.optic["magnification"])
        if self.optic["reticle"]:
            self.reticle.setText(self.optic["reticle"])
        self.click_value.setValue(self.optic["click_value_elevation"])

        unit_index = self.click_unit.findText(self.optic["click_unit"])
        if unit_index >= 0:
            self.click_unit.setCurrentIndex(unit_index)

        if self.optic["zero_distance"]:
            self.zero_distance.setValue(int(self.optic["zero_distance"]))

        if self.optic["rifle_id"]:
            for i in range(self.rifle_combo.count()):
                if self.rifle_combo.itemData(i) == self.optic["rifle_id"]:
                    self.rifle_combo.setCurrentIndex(i)
                    break

        if self.optic["notes"]:
            self.notes.setText(self.optic["notes"])

    def get_data(self):
        """Returnerer data fra dialog"""
        return {
            "name": self.name_input.text(),
            "manufacturer": self.manufacturer.text(),
            "magnification": self.magnification.text(),
            "reticle": self.reticle.text(),
            "click_value_elevation": self.click_value.value(),
            "click_value_windage": self.click_value.value(),  # Samme for begge
            "click_unit": self.click_unit.currentText(),
            "zero_distance": self.zero_distance.value(),
            "rifle_id": self.rifle_combo.currentData(),
            "notes": self.notes.toPlainText(),
        }
