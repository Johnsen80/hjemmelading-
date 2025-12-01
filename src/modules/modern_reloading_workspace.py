"""
Modern Reloading Workspace - Next Level Ballistics

- Alt skjer i ett rom: velg våpen/hylse, juster krutt/kule/seating, se live grafer og AI-anbefalinger.
- Inspirert av Gordon/QuickLOAD, men med moderne, maskulin og informasjonsrik design.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider,
    QTextEdit, QGroupBox, QFrame, QSplitter, QScrollArea, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg
import numpy as np

class ModernReloadingWorkspace(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Modern Reloading Workspace")
        self.setStyleSheet("background: #23272a; color: #eaeaea;")
        self.resize(1600, 1000)
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Venstre panel: Våpenprofil og hylse
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("🔫 Våpenprofil"))
        self.rifle_combo = QComboBox()
        self.rifle_combo.addItem("Tikka T3x 6.5CM")
        self.rifle_combo.addItem("Remington 700 .308")
        left_panel.addWidget(self.rifle_combo)
        left_panel.addWidget(QLabel("🧃 Hylsebatch"))
        self.brass_combo = QComboBox()
        self.brass_combo.addItem("Lapua Batch #1")
        self.brass_combo.addItem("Norma Batch #2")
        left_panel.addWidget(self.brass_combo)
        left_panel.addStretch()

        # Midtseksjon: Krutt, kule, sliders
        center_panel = QVBoxLayout()
        center_panel.addWidget(QLabel("💥 Kruttvalg"))
        self.powder_combo = QComboBox()
        self.powder_combo.addItem("Vihtavuori N150")
        self.powder_combo.addItem("Hodgdon H4350")
        center_panel.addWidget(self.powder_combo)
        center_panel.addWidget(QLabel("🔘 Kulevalg"))
        self.bullet_combo = QComboBox()
        self.bullet_combo.addItem("Hornady 140gr ELD-M")
        self.bullet_combo.addItem("Berger 185gr Hybrid")
        center_panel.addWidget(self.bullet_combo)
        center_panel.addWidget(QLabel("💣 Kruttmengde (grains)"))
        self.powder_slider = QSlider(Qt.Orientation.Horizontal)
        self.powder_slider.setMinimum(35)
        self.powder_slider.setMaximum(50)
        self.powder_slider.setValue(42)
        center_panel.addWidget(self.powder_slider)
        center_panel.addWidget(QLabel("📏 Seating Depth (mm)"))
        self.seating_slider = QSlider(Qt.Orientation.Horizontal)
        self.seating_slider.setMinimum(65)
        self.seating_slider.setMaximum(80)
        self.seating_slider.setValue(70)
        center_panel.addWidget(self.seating_slider)
        center_panel.addStretch()

        # Høyre panel: Grafer, AI-anbefalinger og ES/samling
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("📈 Live Grafer"))
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#23272a')
        self.graph_widget.setTitle("Trykk & Velocity", color='#eaeaea', size="16pt")
        self.graph_widget.setLabel('left', 'PSI / FPS', color='#eaeaea')
        self.graph_widget.setLabel('bottom', 'Kruttmengde (gr)', color='#eaeaea')
        right_panel.addWidget(self.graph_widget)

        # ES og samlingssimulator
        right_panel.addWidget(QLabel("🎯 ES & Samlingssimulator"))
        self.es_group_graph = pg.PlotWidget()
        self.es_group_graph.setBackground('#23272a')
        self.es_group_graph.setTitle("Predikert ES & Group Size", color='#eaeaea', size="14pt")
        self.es_group_graph.setLabel('left', 'ES (fps) / MOA', color='#eaeaea')
        self.es_group_graph.setLabel('bottom', 'Kruttmengde (gr)', color='#eaeaea')
        right_panel.addWidget(self.es_group_graph)
        self.es_group_label = QLabel()
        self.es_group_label.setStyleSheet("color: #eaeaea; font-size: 13pt; margin: 8px 0;")
        right_panel.addWidget(self.es_group_label)

        right_panel.addWidget(QLabel("🎯 AI Anbefalinger"))
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setStyleSheet("background: #2c2f33; color: #eaeaea; font-size: 12pt;")
        self.ai_text.setText("Optimal presisjon: 42.3gr H4350, 70.8mm seating.\nUnngå trykk over 59k PSI.\nTest denne ladningen!")
        right_panel.addWidget(self.ai_text)

        right_panel.addWidget(QLabel("🔬 Vibrasjon & Kulde Dybde"))
        self.vibration_graph = pg.PlotWidget()
        self.vibration_graph.setBackground('#23272a')
        self.vibration_graph.setTitle("Harmonisk Vibrasjon", color='#eaeaea', size="14pt")
        right_panel.addWidget(self.vibration_graph)
        right_panel.addStretch()

        # Layout: sidepaneler og workspace
        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(center_panel, 3)
        main_layout.addLayout(right_panel, 5)

        # Live oppdatering av grafer
        self.powder_slider.valueChanged.connect(self.update_graphs)
        self.seating_slider.valueChanged.connect(self.update_graphs)
        self.update_graphs()

    def update_graphs(self):
        powder = self.powder_slider.value()
        seating = self.seating_slider.value()
        # Simuler trykk og velocity
        x = np.linspace(35, 50, 100)
        pressure = 50000 + (x-42)*1200 - (seating-70)*100
        velocity = 2600 + (x-42)*30 - (seating-70)*5
        self.graph_widget.clear()
        self.graph_widget.plot(x, pressure, pen=pg.mkPen('#e67e22', width=3), name="Trykk")
        self.graph_widget.plot(x, velocity, pen=pg.mkPen('#3498db', width=3), name="Velocity")

        # Simuler ES og group size
        es = 12 + (powder-42)*0.8 + abs(seating-70)*0.5
        group = 0.65 + (powder-42)*0.03 + abs(seating-70)*0.02
        es_curve = 12 + (x-42)*0.8 + abs(seating-70)*0.5
        group_curve = 0.65 + (x-42)*0.03 + abs(seating-70)*0.02
        self.es_group_graph.clear()
        self.es_group_graph.plot(x, es_curve, pen=pg.mkPen('#e74c3c', width=2), name="ES (fps)")
        self.es_group_graph.plot(x, group_curve, pen=pg.mkPen('#27ae60', width=2), name="Group Size (MOA)")
        self.es_group_label.setText(f"Predikert ES: {es:.1f} fps   |   Group Size: {group:.2f} MOA")

        # Simuler vibrasjon
        vib_x = np.linspace(35, 50, 100)
        vib_y = np.sin((vib_x-42)/2) * (seating-70)/10 + 1
        self.vibration_graph.clear()
        self.vibration_graph.plot(vib_x, vib_y, pen=pg.mkPen('#f1c40f', width=2), name="Vibrasjon")

        # Oppdater AI-anbefalinger
        self.ai_text.setText(f"Optimal presisjon: {powder:.1f}gr {self.powder_combo.currentText()}, {seating:.1f}mm seating.\nUnngå trykk over 59k PSI.\nTest denne ladningen!\nPredikert ES: {es:.1f} fps   |   Group Size: {group:.2f} MOA")
