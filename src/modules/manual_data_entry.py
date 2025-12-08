from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from src.database.database import BulletData, PowderData


class ManualDataEntryWidget(QWidget):
    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel("Legg inn kruttdata manuelt:"))
        self.powder_name = QLineEdit()
        self.powder_manufacturer = QLineEdit()
        self.powder_type = QLineEdit()
        self.powder_burn_rate = QDoubleSpinBox()
        self.powder_energy_density = QDoubleSpinBox()
        self.powder_charge_min = QDoubleSpinBox()
        self.powder_charge_max = QDoubleSpinBox()
        self.powder_reference = QLineEdit()
        layout.addWidget(QLabel("Navn:"))
        layout.addWidget(self.powder_name)
        layout.addWidget(QLabel("Produsent:"))
        layout.addWidget(self.powder_manufacturer)
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(self.powder_type)
        layout.addWidget(QLabel("Brennhastighet:"))
        layout.addWidget(self.powder_burn_rate)
        layout.addWidget(QLabel("Energitetthet:"))
        layout.addWidget(self.powder_energy_density)
        layout.addWidget(QLabel("Anbefalt ladning min:"))
        layout.addWidget(self.powder_charge_min)
        layout.addWidget(QLabel("Anbefalt ladning maks:"))
        layout.addWidget(self.powder_charge_max)
        layout.addWidget(QLabel("Referanse:"))
        layout.addWidget(self.powder_reference)
        self.save_powder_btn = QPushButton("Lagre kruttdata")
        self.save_powder_btn.clicked.connect(self.save_powder)
        layout.addWidget(self.save_powder_btn)
        layout.addWidget(QLabel("Legg inn kuledata manuelt:"))
        self.bullet_name = QLineEdit()
        self.bullet_manufacturer = QLineEdit()
        self.bullet_diameter = QDoubleSpinBox()
        self.bullet_weight = QDoubleSpinBox()
        self.bullet_bc = QDoubleSpinBox()
        self.bullet_type = QLineEdit()
        self.bullet_length = QDoubleSpinBox()
        self.bullet_twist = QDoubleSpinBox()
        self.bullet_reference = QLineEdit()
        layout.addWidget(QLabel("Navn:"))
        layout.addWidget(self.bullet_name)
        layout.addWidget(QLabel("Produsent:"))
        layout.addWidget(self.bullet_manufacturer)
        layout.addWidget(QLabel("Diameter:"))
        layout.addWidget(self.bullet_diameter)
        layout.addWidget(QLabel("Vekt:"))
        layout.addWidget(self.bullet_weight)
        layout.addWidget(QLabel("BC:"))
        layout.addWidget(self.bullet_bc)
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(self.bullet_type)
        layout.addWidget(QLabel("Lengde:"))
        layout.addWidget(self.bullet_length)
        layout.addWidget(QLabel("Anbefalt twist:"))
        layout.addWidget(self.bullet_twist)
        layout.addWidget(QLabel("Referanse:"))
        layout.addWidget(self.bullet_reference)
        self.save_bullet_btn = QPushButton("Lagre kuledata")
        self.save_bullet_btn.clicked.connect(self.save_bullet)
        layout.addWidget(self.save_bullet_btn)
        layout.addWidget(QLabel("Antall kontrollmålinger for kule:"))
        self.bullet_measure_count = QSpinBox()
        self.bullet_measure_count.setRange(10, 50)
        self.bullet_measure_count.setSingleStep(10)
        self.bullet_measure_count.setValue(10)
        layout.addWidget(self.bullet_measure_count)
        self.bullet_measurements: list[float] = []
        self.add_bullet_measure_btn = QPushButton("Legg til måling")
        self.add_bullet_measure_btn.clicked.connect(self.add_bullet_measurement)
        layout.addWidget(self.add_bullet_measure_btn)
        self.bullet_measure_list = QLabel()
        layout.addWidget(self.bullet_measure_list)
        self.calc_bullet_stats_btn = QPushButton("Beregn snitt og avvik")
        self.calc_bullet_stats_btn.clicked.connect(self.calc_bullet_stats)
        layout.addWidget(self.calc_bullet_stats_btn)
        self.bullet_stats_label = QLabel()
        layout.addWidget(self.bullet_stats_label)
        layout.addWidget(QLabel("Velg måleenhet for vekt:"))
        self.weight_unit_select = QComboBox()
        self.weight_unit_select.addItems(["grain", "gram"])
        self.weight_unit_select.setCurrentText("grain")
        layout.addWidget(self.weight_unit_select)
        layout.addWidget(QLabel("Registrer kruttbeholdning:"))
        self.powder_stock_amount = QDoubleSpinBox()
        self.powder_stock_amount.setRange(0, 100)
        self.powder_stock_amount.setDecimals(3)
        layout.addWidget(self.powder_stock_amount)
        self.powder_stock_unit = QComboBox()
        self.powder_stock_unit.addItems(["kg", "gram", "pund", "grain"])
        self.powder_stock_unit.setCurrentText("kg")
        layout.addWidget(self.powder_stock_unit)
        self.save_powder_stock_btn = QPushButton("Lagre kruttbeholdning")
        self.save_powder_stock_btn.clicked.connect(self.save_powder_stock)
        layout.addWidget(self.save_powder_stock_btn)

    def save_powder(self):
        unit = self.weight_unit_select.currentText()
        charge_min = self.powder_charge_min.value()
        charge_max = self.powder_charge_max.value()
        if unit == "gram":
            charge_min = charge_min * 15.4324
            charge_max = charge_max * 15.4324
        powder = PowderData(
            name=self.powder_name.text(),
            manufacturer=self.powder_manufacturer.text(),
            type=self.powder_type.text(),
            burn_rate=self.powder_burn_rate.value(),
            energy_density=self.powder_energy_density.value(),
            recommended_charge_min=charge_min,
            recommended_charge_max=charge_max,
            reference=self.powder_reference.text(),
        )
        self.db_session.add(powder)
        self.db_session.commit()
        QMessageBox.information(self, "Lagring", "Kruttdata lagret!")

    def save_bullet(self):
        unit = self.weight_unit_select.currentText()
        weight = self.bullet_weight.value()
        if unit == "gram":
            weight = weight * 15.4324
        bullet = BulletData(
            name=self.bullet_name.text(),
            manufacturer=self.bullet_manufacturer.text(),
            diameter=self.bullet_diameter.value(),
            weight=weight,
            bc=self.bullet_bc.value(),
            type=self.bullet_type.text(),
            length=self.bullet_length.value(),
            recommended_twist=self.bullet_twist.value(),
            reference=self.bullet_reference.text(),
        )
        self.db_session.add(bullet)
        self.db_session.commit()
        QMessageBox.information(self, "Lagring", "Kuledata lagret!")

    def add_bullet_measurement(self):
        if len(self.bullet_measurements) < self.bullet_measure_count.value():
            value, ok = QInputDialog.getDouble(
                self, "Kulemåling", "Skriv inn måling (mm eller grain):", 0, 0, 1000, 2
            )
            if ok:
                self.bullet_measurements.append(value)
                self.bullet_measure_list.setText(
                    f"Målinger: {self.bullet_measurements}"
                )
        else:
            QMessageBox.warning(
                self, "Maks målinger", "Du har nådd valgt antall målinger."
            )

    def calc_bullet_stats(self):
        if len(self.bullet_measurements) < 10:
            QMessageBox.warning(self, "For få målinger", "Minimum 10 målinger kreves.")
            return
        avg = sum(self.bullet_measurements) / len(self.bullet_measurements)
        std = (
            sum((x - avg) ** 2 for x in self.bullet_measurements)
            / len(self.bullet_measurements)
        ) ** 0.5
        self.bullet_stats_label.setText(f"Snitt: {avg:.3f}, Std.avvik: {std:.3f}")

    def save_powder_stock(self):
        amount = self.powder_stock_amount.value()
        unit = self.powder_stock_unit.currentText()
        # Konverter til grain
        if unit == "kg":
            amount_grain = amount * 15432.4
        elif unit == "gram":
            amount_grain = amount * 15.4324
        elif unit == "pund":
            amount_grain = amount * 7000
        else:
            amount_grain = amount
        # Her kan du lagre amount_grain i lagerbeholdningstabellen
        QMessageBox.information(
            self,
            "Lagring",
            f"Kruttbeholdning lagret: {amount} {unit} ({amount_grain:.0f} grain)",
        )
