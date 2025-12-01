from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QTextEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt
from src.logging_config import get_logger, configure_logging
from src.database.database import get_database

configure_logging()
logger = get_logger(__name__)


class WeaponProfileDialog(QDialog):
    """Dialog for creating/editing/deleting a weapon profile (rifle)."""

    def __init__(self, db=None, rifle_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db or get_database()
        self.rifle_id = rifle_id
        self.setWindowTitle("Våpenprofil")
        self.resize(520, 380)
        self.init_ui()
        if self.rifle_id:
            self.load_rifle()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        form.addRow("Navn:", self.name_edit)

        self.manufacturer_edit = QLineEdit()
        form.addRow("Produsent:", self.manufacturer_edit)

        self.model_edit = QLineEdit()
        form.addRow("Modell:", self.model_edit)

        self.caliber_edit = QLineEdit()
        form.addRow("Kaliber:", self.caliber_edit)

        self.action_type = QComboBox()
        self.action_type.addItems(["bolt", "semi-auto", "lever", "single-shot", "other"])
        form.addRow("Våpentype:", self.action_type)

        self.serial_edit = QLineEdit()
        form.addRow("Serienummer:", self.serial_edit)

        self.notes_edit = QTextEdit()
        form.addRow("Notater:", self.notes_edit)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Lagre")
        self.save_btn.clicked.connect(self.on_save)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Avbryt")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.delete_btn = QPushButton("Slett profil")
        self.delete_btn.clicked.connect(self.on_delete)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        # If creating new, hide delete button
        if not self.rifle_id:
            self.delete_btn.setVisible(False)

    def load_rifle(self):
        row = self.db.get_by_id('rifles', self.rifle_id)
        if not row:
            QMessageBox.warning(self, "Feil", "Kunne ikke finne våpenprofilen i databasen.")
            return
        self.name_edit.setText(row.get('name', ''))
        self.manufacturer_edit.setText(row.get('manufacturer', ''))
        self.model_edit.setText(row.get('model', ''))
        self.caliber_edit.setText(row.get('caliber', ''))
        action = row.get('action_type', '')
        try:
            idx = self.action_type.findText(action)
            if idx >= 0:
                self.action_type.setCurrentIndex(idx)
        except Exception:
            pass
        self.serial_edit.setText(row.get('serial_number', '') or '')
        self.notes_edit.setPlainText(row.get('notes', '') or '')

    def on_save(self):
        data = {
            'name': self.name_edit.text().strip(),
            'manufacturer': self.manufacturer_edit.text().strip(),
            'model': self.model_edit.text().strip(),
            'caliber': self.caliber_edit.text().strip(),
            'action_type': self.action_type.currentText(),
            'serial_number': self.serial_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }

        # Remove empty keys not present in schema will be ignored by DB layer
        if self.rifle_id:
            try:
                self.db.update('rifles', data, 'id = ?', (self.rifle_id,))
                logger.info('Updated rifle id %s', self.rifle_id)
                self.accept()
            except Exception as e:
                logger.exception('Failed to update rifle: %s', e)
                QMessageBox.critical(self, "Feil", f"Kunne ikke oppdatere våpen: {e}")
        else:
            try:
                new_id = self.db.insert('rifles', data)
                logger.info('Inserted new rifle id %s', new_id)
                self.rifle_id = new_id
                self.accept()
            except Exception as e:
                logger.exception('Failed to insert rifle: %s', e)
                QMessageBox.critical(self, "Feil", f"Kunne ikke opprette våpen: {e}")

    def on_delete(self):
        if not self.rifle_id:
            return
        ok = QMessageBox.question(self, "Bekreft sletting", "Er du sikker på at du vil slette denne våpenprofilen? Dette kan ikke angres.")
        if ok == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete('rifles', 'id = ?', (self.rifle_id,))
                logger.info('Deleted rifle id %s', self.rifle_id)
                self.accept()
            except Exception as e:
                logger.exception('Failed to delete rifle: %s', e)
                QMessageBox.critical(self, "Feil", f"Kunne ikke slette våpen: {e}")
