"""
Modern Dashboard for Reloading Workshop Manager
- Cards for alle hovedfunksjoner
- Live status, grafisk oversikt, snarveier
- Inspirert av GRT/QuickLOAD, men mer elegant og informasjonsrikt
"""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ModernDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏠 Modern Dashboard - Reloading Workshop Manager")
        self.setStyleSheet("background: #23272a; color: #eaeaea;")
        self.resize(1600, 900)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Header
        header = QLabel("Reloading Workshop Manager")
        header.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #e67e22; padding: 20px;")
        main_layout.addWidget(header)

        # Cards for hovedfunksjoner
        card_layout = QGridLayout()
        card_layout.setSpacing(30)
        cards = [
            (
                "⚡ Lade-modul",
                "Start lading, se grafer og AI-anbefalinger",
                self.open_loading_workspace,
            ),
            (
                "🔬 Ballistikk-simulator",
                "Avansert simulering av trykk og velocity",
                self.open_ballistics_simulator,
            ),
            ("📦 Batch QC", "Batch management og analyse", self.open_batch_qc),
            ("🤖 AI Chat", "Få AI-hjelp og forklaringer", self.open_ai_chat),
            (
                "📊 Historikk & Rapporter",
                "Se og eksporter testresultater",
                self.open_history_reports,
            ),
            ("⚙️ Innstillinger", "Tilpass programmet", self.open_settings),
        ]
        for i, (title, desc, func) in enumerate(cards):
            card = QFrame()
            card.setStyleSheet(
                "background: #2c2f33; border-radius: 12px; padding: 30px; border: 2px solid #e67e22;"
            )
            vbox = QVBoxLayout()
            label = QLabel(title)
            label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            label.setStyleSheet("color: #e67e22;")
            vbox.addWidget(label)
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #eaeaea; font-size: 12pt;")
            vbox.addWidget(desc_label)
            btn = QPushButton("Åpne")
            btn.setStyleSheet(
                "background: #e67e22; color: #23272a; font-weight: bold; padding: 10px 30px; border-radius: 8px;"
            )
            btn.clicked.connect(func)
            vbox.addWidget(btn)
            card.setLayout(vbox)
            card_layout.addWidget(card, i // 3, i % 3)
        main_layout.addLayout(card_layout)

        # Live status/grafisk oversikt
        status_box = QFrame()
        status_box.setStyleSheet(
            "background: #2c2f33; border-radius: 12px; padding: 20px; margin-top: 40px;"
        )
        status_layout = QHBoxLayout()
        status_box.setLayout(status_layout)
        # Siste testresultater
        graph = pg.PlotWidget()
        graph.setBackground("#23272a")
        graph.setTitle("Siste Velocity & Trykk", color="#eaeaea", size="14pt")
        x = np.linspace(1, 10, 10)
        velocity = 2600 + np.random.randn(10) * 20
        pressure = 55000 + np.random.randn(10) * 500
        graph.plot(x, velocity, pen=pg.mkPen("#3498db", width=3), name="Velocity")
        graph.plot(x, pressure, pen=pg.mkPen("#e67e22", width=3), name="Trykk")
        status_layout.addWidget(graph, 2)
        # Siste AI-anbefaling
        ai_box = QTextEdit()
        ai_box.setReadOnly(True)
        ai_box.setStyleSheet("background: #23272a; color: #eaeaea; font-size: 12pt;")
        ai_box.setText(
            "AI: Test 42.3gr H4350, seating 70.8mm. Unngå trykk over 59k PSI. Group size: 0.65 MOA."
        )
        status_layout.addWidget(ai_box, 1)
        main_layout.addWidget(status_box)

    def open_loading_workspace(self):
        from src.modules.modern_reloading_workspace import ModernReloadingWorkspace

        self._open_module(ModernReloadingWorkspace, "⚡ Lade-modul")

    def open_ballistics_simulator(self):
        from src.modules.ballistics_simulator import BallisticsSimulator

        self._open_module(BallisticsSimulator, "🔬 Ballistikk-simulator")

    def open_batch_qc(self):
        # Placeholder
        pass

    def open_ai_chat(self):
        # Placeholder
        pass

    def open_history_reports(self):
        # Placeholder
        pass

    def open_settings(self):
        # Placeholder
        pass

    def _open_module(self, module_class, title):
        win = module_class()
        win.setWindowTitle(title)
        win.resize(1400, 900)
        win.show()
