"""
Ammunisjonsprofil Manager
Håndterer opprettelse og administrasjon av ammunisjonsprofiler
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.database.database import get_database


class AmmoProfileManager(QWidget):
    """Widget for ammunisjonsprofil-administrasjon"""

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
        title = QLabel("🔫 Ammunisjonsprofiler")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel("Administrer og sammenlign ammunisjonsprofiler")
        layout.addWidget(desc)

        # Knapper
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Ny Profil")
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.add_profile)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Rediger")
        edit_btn.setMinimumHeight(40)
        edit_btn.clicked.connect(self.edit_profile)
        btn_layout.addWidget(edit_btn)

        copy_btn = QPushButton("📋 Kopier")
        copy_btn.setMinimumHeight(40)
        copy_btn.clicked.connect(self.copy_profile)
        btn_layout.addWidget(copy_btn)

        delete_btn = QPushButton("🗑️ Slett")
        delete_btn.setMinimumHeight(40)
        delete_btn.clicked.connect(self.delete_profile)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Navn",
                "Rifle",
                "Kaliber",
                "Kule (gr)",
                "Krutt",
                "Ladning (gr)",
                "Hastighet (fps)",
                "BC",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.edit_profile)
        layout.addWidget(self.table)

        # Info-tekst
        info = QLabel(
            """
        <b>Tips:</b> Dobbeltklikk på en profil for å redigere.
        Bruk 'Kopier' for å lage varianter av eksisterende profiler.
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

    def load_data(self):
        """Laster ammunisjonsprofiler fra database"""
        profiles = self.db.get_all("ammo_profiles", "caliber, name")
        self.table.setRowCount(len(profiles))

        for i, profile in enumerate(profiles):
            self.table.setItem(i, 0, QTableWidgetItem(profile["name"]))

            # Rifle navn
            rifle_name = "-"
            if profile["rifle_id"]:
                rifle = self.db.get_by_id("rifles", profile["rifle_id"])
                if rifle:
                    rifle_name = rifle["name"]
            self.table.setItem(i, 1, QTableWidgetItem(rifle_name))

            self.table.setItem(i, 2, QTableWidgetItem(profile["caliber"]))
            self.table.setItem(i, 3, QTableWidgetItem(f"{profile['bullet_weight']}"))

            # Krutt navn
            powder_name = "-"
            if profile["powder_id"]:
                powder = self.db.get_by_id("powder", profile["powder_id"])
                if powder:
                    powder_name = powder["name"]
            self.table.setItem(i, 4, QTableWidgetItem(powder_name))

            self.table.setItem(i, 5, QTableWidgetItem(f"{profile['powder_charge']}"))

            vel = f"{profile['velocity_fps']}" if profile["velocity_fps"] else "-"
            self.table.setItem(i, 6, QTableWidgetItem(vel))

            bc = f"{profile['bc_g1']:.3f}" if profile["bc_g1"] else "-"
            self.table.setItem(i, 7, QTableWidgetItem(bc))

            # Lagre ID
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, profile["id"])

    def add_profile(self):
        """Legger til ny ammunisjonsprofil"""
        rifles = self.db.get_all("rifles")
        powders = self.db.get_all("powder")
        bullets = self.db.get_all("bullets")
        primers = self.db.get_all("primers")
        cases = self.db.get_all("cases")

        dialog = AmmoProfileDialog(
            self,
            rifles=rifles,
            powders=powders,
            bullets=bullets,
            primers=primers,
            cases=cases,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.insert("ammo_profiles", data)
            self.load_data()
            QMessageBox.information(self, "Suksess", "Ammunisjonsprofil lagt til!")

    def edit_profile(self):
        """Redigerer valgt profil"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en profil først!")
            return

        profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        profile = self.db.get_by_id("ammo_profiles", profile_id)

        rifles = self.db.get_all("rifles")
        powders = self.db.get_all("powder")
        bullets = self.db.get_all("bullets")
        primers = self.db.get_all("primers")
        cases = self.db.get_all("cases")

        dialog = AmmoProfileDialog(
            self, profile, rifles, powders, bullets, primers, cases
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.db.update("ammo_profiles", data, "id = ?", (profile_id,))
            self.load_data()
            QMessageBox.information(self, "Suksess", "Ammunisjonsprofil oppdatert!")

    def copy_profile(self):
        """Kopierer valgt profil"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en profil først!")
            return

        profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
        profile = self.db.get_by_id("ammo_profiles", profile_id)

        # Fjern ID og endre navn
        profile = dict(profile)
        if "id" in profile:
            del profile["id"]
        if "created_date" in profile:
            del profile["created_date"]
        profile["name"] = profile["name"] + " (kopi)"

        self.db.insert("ammo_profiles", profile)
        self.load_data()
        QMessageBox.information(self, "Suksess", "Profil kopiert!")

    def delete_profile(self):
        """Sletter valgt profil"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ingen valgt", "Velg en profil først!")
            return

        reply = QMessageBox.question(
            self,
            "Bekreft sletting",
            "Er du sikker på at du vil slette denne profilen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            profile_id = self.table.item(selected, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete("ammo_profiles", "id = ?", (profile_id,))
            self.load_data()
            QMessageBox.information(self, "Suksess", "Profil slettet!")


class AmmoProfileDialog(QDialog):
    """Dialog for ammunisjonsprofil"""

    def __init__(
        self,
        parent=None,
        profile=None,
        rifles=None,
        powders=None,
        bullets=None,
        primers=None,
        cases=None,
    ):
        super().__init__(parent)
        self.profile = profile
        self.rifles = rifles or []
        self.powders = powders or []
        self.bullets = bullets or []
        self.primers = primers or []
        self.cases = cases or []
        self.init_ui()
        if profile:
            self.load_data()

    def init_ui(self):
        """Initialiserer dialog"""
        self.setWindowTitle("Ammunisjonsprofil")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Grunnleggende info
        basic_group = QGroupBox("Grunnleggende Informasjon")
        basic_layout = QFormLayout()
        basic_group.setLayout(basic_layout)

        self.name = QLineEdit()
        basic_layout.addRow("Profilnavn:", self.name)

        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("-- Ingen rifle --", None)
        for rifle in self.rifles:
            self.rifle_combo.addItem(
                f"{rifle['name']} ({rifle['caliber']})", rifle["id"]
            )
        basic_layout.addRow("Rifle:", self.rifle_combo)

        self.caliber = QLineEdit()
        basic_layout.addRow("Kaliber:", self.caliber)

        layout.addWidget(basic_group)

        # Komponenter
        comp_group = QGroupBox("Komponenter")
        comp_layout = QFormLayout()
        comp_group.setLayout(comp_layout)

        # Kuler
        bullet_layout = QHBoxLayout()
        self.bullet_combo = QComboBox()
        self.bullet_combo.addItem("-- Velg kule --", None)
        for bullet in self.bullets:
            self.bullet_combo.addItem(
                f"{bullet['name']} - {bullet['weight_grains']}gr ({bullet['caliber']})",
                bullet["id"],
            )
        self.bullet_combo.currentIndexChanged.connect(self.on_bullet_selected)
        bullet_layout.addWidget(self.bullet_combo)
        comp_layout.addRow("Kule:", bullet_layout)

        self.bullet_weight = QDoubleSpinBox()
        self.bullet_weight.setRange(20, 500)
        self.bullet_weight.setSuffix(" gr")
        comp_layout.addRow("Kulevekt:", self.bullet_weight)

        # Krutt
        powder_layout = QHBoxLayout()
        self.powder_combo = QComboBox()
        self.powder_combo.addItem("-- Velg krutt --", None)
        for powder in self.powders:
            self.powder_combo.addItem(
                f"{powder['name']} ({powder['manufacturer'] if powder['manufacturer'] else 'Ukjent'})",
                powder["id"],
            )
        powder_layout.addWidget(self.powder_combo)
        comp_layout.addRow("Krutt:", powder_layout)

        self.powder_charge = QDoubleSpinBox()
        self.powder_charge.setRange(5, 100)
        self.powder_charge.setDecimals(1)
        self.powder_charge.setSingleStep(0.1)
        self.powder_charge.setSuffix(" gr")
        comp_layout.addRow("Kruttvekt:", self.powder_charge)

        # Tennhetter
        self.primer_combo = QComboBox()
        self.primer_combo.addItem("-- Velg tennhette --", None)
        for primer in self.primers:
            self.primer_combo.addItem(
                f"{primer['name']} ({primer['type'] if primer['type'] else 'Ukjent'})",
                primer["id"],
            )
        comp_layout.addRow("Tennhette:", self.primer_combo)

        # Hylser
        self.case_combo = QComboBox()
        self.case_combo.addItem("-- Velg hylse --", None)
        for case in self.cases:
            self.case_combo.addItem(f"{case['name']} - {case['caliber']}", case["id"])
        comp_layout.addRow("Hylse:", self.case_combo)

        layout.addWidget(comp_group)

        # Settedybde og ballistikk
        bal_group = QGroupBox("Settedybde og Ballistikk")
        bal_layout = QFormLayout()
        bal_group.setLayout(bal_layout)

        self.coal = QDoubleSpinBox()
        self.coal.setRange(1.0, 5.0)
        self.coal.setDecimals(3)
        self.coal.setSingleStep(0.001)
        self.coal.setSuffix(' "')
        bal_layout.addRow("COAL:", self.coal)

        self.cbto = QDoubleSpinBox()
        self.cbto.setRange(1.0, 5.0)
        self.cbto.setDecimals(3)
        self.cbto.setSingleStep(0.001)
        self.cbto.setSuffix(' "')
        bal_layout.addRow("CBTO:", self.cbto)

        self.velocity = QSpinBox()
        self.velocity.setRange(500, 4500)
        self.velocity.setSuffix(" fps")
        bal_layout.addRow("Hastighet:", self.velocity)

        self.bc_g1 = QDoubleSpinBox()
        self.bc_g1.setRange(0.1, 1.0)
        self.bc_g1.setDecimals(3)
        self.bc_g1.setSingleStep(0.001)
        bal_layout.addRow("BC (G1):", self.bc_g1)

        self.bc_g7 = QDoubleSpinBox()
        self.bc_g7.setRange(0.1, 1.0)
        self.bc_g7.setDecimals(3)
        self.bc_g7.setSingleStep(0.001)
        bal_layout.addRow("BC (G7):", self.bc_g7)

        layout.addWidget(bal_group)

        # Notater
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText("Notater om denne profilen...")
        layout.addWidget(QLabel("Notater:"))
        layout.addWidget(self.notes)

        # Knapper
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Lagre")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def on_bullet_selected(self, index):
        """Når kule velges, fyll inn vekt og BC automatisk"""
        bullet_id = self.bullet_combo.currentData()
        if bullet_id:
            bullet = self.db.get_by_id("bullets", bullet_id)
            if bullet:
                self.bullet_weight.setValue(bullet["weight_grains"])
                if bullet["bc_g1"]:
                    self.bc_g1.setValue(bullet["bc_g1"])
                if bullet["bc_g7"]:
                    self.bc_g7.setValue(bullet["bc_g7"])

    def load_data(self):
        """Laster profil-data"""
        self.name.setText(self.profile["name"])

        # Rifle
        if self.profile["rifle_id"]:
            for i in range(self.rifle_combo.count()):
                if self.rifle_combo.itemData(i) == self.profile["rifle_id"]:
                    self.rifle_combo.setCurrentIndex(i)
                    break

        self.caliber.setText(self.profile["caliber"])

        # Bullet
        if self.profile["bullet_id"]:
            for i in range(self.bullet_combo.count()):
                if self.bullet_combo.itemData(i) == self.profile["bullet_id"]:
                    self.bullet_combo.setCurrentIndex(i)
                    break

        self.bullet_weight.setValue(self.profile["bullet_weight"])

        # Powder
        if self.profile["powder_id"]:
            for i in range(self.powder_combo.count()):
                if self.powder_combo.itemData(i) == self.profile["powder_id"]:
                    self.powder_combo.setCurrentIndex(i)
                    break

        self.powder_charge.setValue(self.profile["powder_charge"])

        # Primer
        if self.profile["primer_id"]:
            for i in range(self.primer_combo.count()):
                if self.primer_combo.itemData(i) == self.profile["primer_id"]:
                    self.primer_combo.setCurrentIndex(i)
                    break

        # Case
        if self.profile["case_id"]:
            for i in range(self.case_combo.count()):
                if self.case_combo.itemData(i) == self.profile["case_id"]:
                    self.case_combo.setCurrentIndex(i)
                    break

        # Ballistikk
        if self.profile["coal"]:
            self.coal.setValue(self.profile["coal"])
        if self.profile["cbto"]:
            self.cbto.setValue(self.profile["cbto"])
        if self.profile["velocity_fps"]:
            self.velocity.setValue(self.profile["velocity_fps"])
        if self.profile["bc_g1"]:
            self.bc_g1.setValue(self.profile["bc_g1"])
        if self.profile["bc_g7"]:
            self.bc_g7.setValue(self.profile["bc_g7"])
        if self.profile["notes"]:
            self.notes.setText(self.profile["notes"])

    def get_data(self):
        """Returnerer profil-data"""
        return {
            "name": self.name.text(),
            "rifle_id": self.rifle_combo.currentData(),
            "caliber": self.caliber.text(),
            "bullet_id": self.bullet_combo.currentData(),
            "bullet_weight": self.bullet_weight.value(),
            "powder_id": self.powder_combo.currentData(),
            "powder_charge": self.powder_charge.value(),
            "primer_id": self.primer_combo.currentData(),
            "case_id": self.case_combo.currentData(),
            "coal": self.coal.value() if self.coal.value() > 0 else None,
            "cbto": self.cbto.value() if self.cbto.value() > 0 else None,
            "velocity_fps": (
                self.velocity.value() if self.velocity.value() > 0 else None
            ),
            "bc_g1": self.bc_g1.value() if self.bc_g1.value() > 0 else None,
            "bc_g7": self.bc_g7.value() if self.bc_g7.value() > 0 else None,
            "notes": self.notes.toPlainText(),
        }
