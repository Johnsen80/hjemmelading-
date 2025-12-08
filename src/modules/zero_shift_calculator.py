"""
Zero Shift Calculator - Widget
Beregner optikk-justeringer ved ammunisjonsbytte
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.database.database import get_database
from src.utils.ballistics import BallisticData, BallisticsCalculator


class ZeroShiftCalculator(QWidget):
    """Widget for Zero Shift beregning"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.calc = BallisticsCalculator()
        self.init_ui()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("🎯 Zero Shift Calculator")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel("Beregn optikk-justeringer når du bytter ammunisjon")
        layout.addWidget(desc)

        # Hovedinnhold i horisontal layout
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)

        # Venstre side - Input
        left_widget = self.create_input_section()
        main_layout.addWidget(left_widget, 1)

        # Høyre side - Resultat
        right_widget = self.create_result_section()
        main_layout.addWidget(right_widget, 1)

    def create_input_section(self):
        """Oppretter input-seksjon"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Ammunisjon 1 (Innskutt med)
        ammo1_group = QGroupBox("Ammunisjon 1 (Innskutt med)")
        ammo1_layout = QVBoxLayout()
        ammo1_group.setLayout(ammo1_layout)

        # Profil dropdown
        ammo1_layout.addWidget(QLabel("Velg profil:"))
        self.ammo1_combo = QComboBox()
        self.ammo1_combo.addItem("-- Manuell input --")
        ammo1_layout.addWidget(self.ammo1_combo)

        # Manuelle felter
        ammo1_layout.addWidget(QLabel("Hastighet (fps):"))
        self.ammo1_velocity = QSpinBox()
        self.ammo1_velocity.setRange(1000, 4000)
        self.ammo1_velocity.setValue(2700)
        self.ammo1_velocity.setSuffix(" fps")
        ammo1_layout.addWidget(self.ammo1_velocity)

        ammo1_layout.addWidget(QLabel("BC (G1):"))
        self.ammo1_bc = QDoubleSpinBox()
        self.ammo1_bc.setRange(0.1, 1.0)
        self.ammo1_bc.setValue(0.450)
        self.ammo1_bc.setDecimals(3)
        self.ammo1_bc.setSingleStep(0.001)
        ammo1_layout.addWidget(self.ammo1_bc)

        ammo1_layout.addWidget(QLabel("Vekt (grains):"))
        self.ammo1_weight = QSpinBox()
        self.ammo1_weight.setRange(40, 300)
        self.ammo1_weight.setValue(140)
        self.ammo1_weight.setSuffix(" gr")
        ammo1_layout.addWidget(self.ammo1_weight)

        ammo1_layout.addWidget(QLabel("Zero avstand (m):"))
        self.ammo1_zero = QSpinBox()
        self.ammo1_zero.setRange(25, 500)
        self.ammo1_zero.setValue(100)
        self.ammo1_zero.setSuffix(" m")
        ammo1_layout.addWidget(self.ammo1_zero)

        layout.addWidget(ammo1_group)

        # Ammunisjon 2 (Bytte til)
        ammo2_group = QGroupBox("Ammunisjon 2 (Bytte til)")
        ammo2_layout = QVBoxLayout()
        ammo2_group.setLayout(ammo2_layout)

        ammo2_layout.addWidget(QLabel("Velg profil:"))
        self.ammo2_combo = QComboBox()
        self.ammo2_combo.addItem("-- Manuell input --")
        ammo2_layout.addWidget(self.ammo2_combo)

        ammo2_layout.addWidget(QLabel("Hastighet (fps):"))
        self.ammo2_velocity = QSpinBox()
        self.ammo2_velocity.setRange(1000, 4000)
        self.ammo2_velocity.setValue(2620)
        self.ammo2_velocity.setSuffix(" fps")
        ammo2_layout.addWidget(self.ammo2_velocity)

        ammo2_layout.addWidget(QLabel("BC (G1):"))
        self.ammo2_bc = QDoubleSpinBox()
        self.ammo2_bc.setRange(0.1, 1.0)
        self.ammo2_bc.setValue(0.497)
        self.ammo2_bc.setDecimals(3)
        self.ammo2_bc.setSingleStep(0.001)
        ammo2_layout.addWidget(self.ammo2_bc)

        ammo2_layout.addWidget(QLabel("Vekt (grains):"))
        self.ammo2_weight = QSpinBox()
        self.ammo2_weight.setRange(40, 300)
        self.ammo2_weight.setValue(147)
        self.ammo2_weight.setSuffix(" gr")
        ammo2_layout.addWidget(self.ammo2_weight)

        ammo2_layout.addWidget(QLabel("Zero avstand (m):"))
        self.ammo2_zero = QSpinBox()
        self.ammo2_zero.setRange(25, 500)
        self.ammo2_zero.setValue(100)
        self.ammo2_zero.setSuffix(" m")
        ammo2_layout.addWidget(self.ammo2_zero)

        layout.addWidget(ammo2_group)

        # Optikk-innstillinger
        optic_group = QGroupBox("Optikk-innstillinger")
        optic_layout = QVBoxLayout()
        optic_group.setLayout(optic_layout)

        optic_layout.addWidget(QLabel("Velg optikk:"))
        self.optic_combo = QComboBox()
        self.optic_combo.addItem("-- Manuell input --")
        self.optic_combo.currentTextChanged.connect(self.on_optic_selected)
        optic_layout.addWidget(self.optic_combo)

        optic_layout.addWidget(QLabel("Klikk-verdi:"))
        h_layout = QHBoxLayout()
        self.click_value = QDoubleSpinBox()
        self.click_value.setRange(0.01, 1.0)
        self.click_value.setValue(0.25)
        self.click_value.setDecimals(2)
        self.click_value.setSingleStep(0.01)
        h_layout.addWidget(self.click_value)

        self.click_unit = QComboBox()
        self.click_unit.addItems(["MOA", "MRAD"])
        h_layout.addWidget(self.click_unit)
        optic_layout.addLayout(h_layout)

        optic_layout.addWidget(QLabel("Skyteavstand (m):"))
        self.shooting_distance = QSpinBox()
        self.shooting_distance.setRange(50, 1000)
        self.shooting_distance.setValue(300)
        self.shooting_distance.setSuffix(" m")
        optic_layout.addWidget(self.shooting_distance)

        layout.addWidget(optic_group)

        # Beregn-knapp
        calculate_btn = QPushButton("🎯 Beregn Justering")
        calculate_btn.setMinimumHeight(50)
        calculate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        calculate_btn.clicked.connect(self.calculate_adjustment)
        layout.addWidget(calculate_btn)

        layout.addStretch()

        return widget

    def create_result_section(self):
        """Oppretter resultat-seksjon"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Hovedresultat
        result_group = QGroupBox("📊 Justering Påkrevd")
        result_layout = QVBoxLayout()
        result_group.setLayout(result_layout)

        self.result_label = QLabel()
        self.result_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            """
            QLabel {
                padding: 20px;
                background-color: #E3F2FD;
                border-radius: 5px;
                border: 2px solid #2196F3;
            }
        """
        )
        self.result_label.setText("Klikk 'Beregn Justering' for å se resultat")
        result_layout.addWidget(self.result_label)

        layout.addWidget(result_group)

        # Detaljer
        details_group = QGroupBox("📋 Detaljert Informasjon")
        details_layout = QVBoxLayout()
        details_group.setLayout(details_layout)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)

        layout.addWidget(details_group)

        # Tabell med flere avstander
        table_group = QGroupBox("📐 Justeringer ved Ulike Avstander")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.distance_table = QTableWidget()
        self.distance_table.setColumnCount(4)
        self.distance_table.setHorizontalHeaderLabels(
            ["Avstand (m)", "Forskjell (cm)", "Justering", "Klikk"]
        )
        self.distance_table.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self.distance_table)

        layout.addWidget(table_group)

        return widget

    def on_optic_selected(self, text):
        """Håndterer valg av optikk"""
        # TODO: Last inn optikk-data fra database
        pass

    def calculate_adjustment(self):
        """Beregner nødvendig justering"""
        # Hent data fra inputs
        ammo1 = BallisticData(
            velocity=self.ammo1_velocity.value(),
            bc=self.ammo1_bc.value(),
            weight=self.ammo1_weight.value(),
            zero_distance=self.ammo1_zero.value(),
            bc_type="G1",
        )

        ammo2 = BallisticData(
            velocity=self.ammo2_velocity.value(),
            bc=self.ammo2_bc.value(),
            weight=self.ammo2_weight.value(),
            zero_distance=self.ammo2_zero.value(),
            bc_type="G1",
        )

        distance = self.shooting_distance.value()
        click_value = self.click_value.value()
        click_unit = self.click_unit.currentText()

        # Beregn zero shift
        shift = self.calc.calculate_zero_shift(ammo1, ammo2, distance)

        # Finn riktig justering basert på enhet
        if click_unit == "MOA":
            adjustment_value = shift["difference_moa"]
        else:
            adjustment_value = shift["difference_mrad"]

        # Beregn klikk
        clicks = self.calc.calculate_clicks(adjustment_value, click_value, click_unit)

        # Retning
        if clicks > 0:
            direction = "OPP ⬆"
            color = "#4CAF50"
        elif clicks < 0:
            direction = "NED ⬇"
            color = "#F44336"
            clicks = abs(clicks)
        else:
            direction = "INGEN JUSTERING"
            color = "#2196F3"

        # Vis hovedresultat
        result_text = f"""
        <div style='text-align: center;'>
            <h2 style='color: {color}; margin: 5px;'>{clicks} klikk {direction}</h2>
            <p style='font-size: 12px; margin: 5px;'>
                {adjustment_value:.2f} {click_unit} ved {distance}m
            </p>
        </div>
        """
        self.result_label.setText(result_text)

        # Vis detaljer
        details = f"""
<b>📊 Detaljert Analyse:</b>

<b>Ammunisjon 1:</b>
  • Hastighet: {ammo1.velocity} fps
  • BC (G1): {ammo1.bc}
  • Vekt: {ammo1.weight} grains
  • Drop ved {distance}m: {shift['drop_ammo1_cm']:.1f} cm

<b>Ammunisjon 2:</b>
  • Hastighet: {ammo2.velocity} fps
  • BC (G1): {ammo2.bc}
  • Vekt: {ammo2.weight} grains
  • Drop ved {distance}m: {shift['drop_ammo2_cm']:.1f} cm

<b>Forskjell:</b>
  • {shift['difference_cm']:.1f} cm
  • {shift['difference_moa']:.2f} MOA
  • {shift['difference_mrad']:.3f} MRAD

<b>Anbefaling:</b>
  Noter din original zero før justering!
  Test på kort hold først for å bekrefte.
        """
        self.details_text.setText(details)

        # Generer tabell for flere avstander
        distances = [100, 200, 300, 400, 500]
        table_data = self.calc.generate_adjustment_table(
            ammo1, ammo2, distances, click_value, click_unit
        )

        self.distance_table.setRowCount(len(table_data))
        for i, row in enumerate(table_data):
            self.distance_table.setItem(
                i, 0, QTableWidgetItem(f"{row['distance_m']} m")
            )
            self.distance_table.setItem(
                i, 1, QTableWidgetItem(f"{row['difference_cm']:.1f} cm")
            )
            self.distance_table.setItem(
                i, 2, QTableWidgetItem(f"{row['adjustment_value']:.2f} {click_unit}")
            )

            clicks_str = f"{abs(row['clicks'])} {row['direction']}"
            self.distance_table.setItem(i, 3, QTableWidgetItem(clicks_str))
