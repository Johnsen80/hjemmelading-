
"""
22LR Rimfire Analyzer
Modul for langholdsskyting med 22LR: ammo-database, kammerprofil, batch-logging, ammo-fit, ballistikk, rapporter og AI-tips.
Fokus på fabrikkammo og rifle/ammo-match.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
                            QGroupBox, QComboBox, QTableWidget, QTableWidgetItem, QTextEdit, QLineEdit, QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt

class RimfireAnalyzer(QWidget):
    """
    22LR Rimfire Analyzer modul
    """
    def save_user_profile(self):
        import json
        from PyQt6.QtWidgets import QFileDialog
        profile = {
            "ammo_db": self.ammo_db,
            "lot_entries": getattr(self, 'lot_entries', []),
            "weather_entries": getattr(self, 'weather_entries', []),
            "export_fields": getattr(self, 'export_fields', {}),
        }
        fname, _ = QFileDialog.getSaveFileName(self, "Lagre brukeroppsett", "", "JSON-filer (*.json)")
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)

    def load_user_profile(self):
        import json
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getOpenFileName(self, "Last brukeroppsett", "", "JSON-filer (*.json)")
        if fname:
            with open(fname, "r", encoding="utf-8") as f:
                profile = json.load(f)
            self.ammo_db = profile.get("ammo_db", [])
            self.lot_entries = profile.get("lot_entries", [])
            self.weather_entries = profile.get("weather_entries", [])
            self.export_fields = profile.get("export_fields", self.export_fields)
            self.update_ammo_table()
            self.update_lot_table()
            self.update_weather_table()
            for k in self.export_fields:
                    if k in self.field_checkboxes:
                        self.field_checkboxes[k].setChecked(self.export_fields[k])
    """
    22LR Rimfire Analyzer modul
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("22LR Rimfire Analyzer")
        self.setMinimumSize(900, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("🔬 22LR Rimfire Analyzer")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Ammo-database
        tabs.addTab(self.create_ammo_tab(), "Ammo-database")
        # Tab 2: Kammerprofil
        tabs.addTab(self.create_chamber_tab(), "Kammerprofil")
        # Tab 3: Batch-logging
        tabs.addTab(self.create_batch_tab(), "Batch-logging")
        # Tab 4: Ammo-fit
        tabs.addTab(self.create_fit_tab(), "Ammo-fit")
        # Tab 5: Ballistisk simulering
        tabs.addTab(self.create_simulation_tab(), "Simulering")

    def create_simulation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Interaktiv ballistisk simulering for 22LR. Juster avstand, vind, temperatur og se grafisk kulebane og vindavdrift."))

        self.sim_ammo_combo = QComboBox()
        self.sim_ammo_combo.addItem("Velg ammomodell...")
        for ammo in getattr(self, 'ammo_db', []):
            self.sim_ammo_combo.addItem(ammo["merke"])
        self.sim_distance = QLineEdit(); self.sim_distance.setPlaceholderText("Avstand (m)")
        self.sim_wind = QLineEdit(); self.sim_wind.setPlaceholderText("Vind (m/s)")
        self.sim_temp = QLineEdit(); self.sim_temp.setPlaceholderText("Temperatur (°C)")
        self.sim_angle = QLineEdit(); self.sim_angle.setPlaceholderText("Skytvinkel (°)")
        sim_btn = QPushButton("Simuler kulebane")
        sim_btn.clicked.connect(self.run_simulation)
        layout.addWidget(self.sim_ammo_combo)
        layout.addWidget(self.sim_distance)
        layout.addWidget(self.sim_wind)
        layout.addWidget(self.sim_temp)
        layout.addWidget(self.sim_angle)
        layout.addWidget(sim_btn)

        self.sim_result = QTextEdit(); self.sim_result.setReadOnly(True)
        layout.addWidget(self.sim_result)
        self.sim_img = QLabel()
        layout.addWidget(self.sim_img)

        return widget

    def run_simulation(self):
        import matplotlib.pyplot as plt
        import io, base64
        ammo_name = self.sim_ammo_combo.currentText()
        if ammo_name == "Velg ammomodell...":
            self.sim_result.setText("Velg ammomodell!"); return
        ammo = next((a for a in getattr(self, 'ammo_db', []) if a["merke"] == ammo_name), None)
        if not ammo:
            self.sim_result.setText("Fant ikke ammo-data!"); return
        try:
            distance = float(self.sim_distance.text().strip())
        except Exception:
            distance = 100
        try:
            wind = float(self.sim_wind.text().strip())
        except Exception:
            wind = 0
        try:
            temp = float(self.sim_temp.text().strip())
        except Exception:
            temp = 15
        try:
            angle = float(self.sim_angle.text().strip())
        except Exception:
            angle = 0
        v0 = ammo["hastighet"]
        bc = ammo["bc"]
        # Simuler kulebane med enkel modell
        xs = list(range(0, int(distance)+1, 5))
        drops = [self.simple_drop(v0, bc, x, temp, angle) for x in xs]
        winddrift = [self.simple_wind_drift(v0, bc, x, wind) for x in xs]
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(xs, drops, label="Kulebane (cm)", color="navy")
        ax.plot(xs, winddrift, label="Vindavdrift (cm)", color="orange")
        ax.set_xlabel("Avstand (m)")
        ax.set_ylabel("Drop / Vinddrift (cm)")
        ax.set_title(f"Simulering: {ammo_name}")
        ax.grid(True)
        ax.legend()
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        self.sim_img.setText(f'<img src="data:image/png;base64,{img_b64}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px #888;" />')
        self.sim_result.setText(f"Avstand: {distance} m\nVind: {wind} m/s\nTemp: {temp} °C\nVinkel: {angle}°\nAmmo: {ammo_name}\nStart-hastighet: {v0} fps\nBC: {bc}")

    def simple_drop(self, v0, bc, x, temp, angle):
        # Enkel ballistisk drop-modell (for demo)
        g = 9.81
        v = v0 * (1 + 0.003*(temp-15))
        t = x / (v*0.3048) if v > 0 else 0
        drop = 0.5 * g * t**2 * 100
        drop *= (1 - 0.01*bc)
        drop *= (1 - 0.01*angle)
        return drop

    def simple_wind_drift(self, v0, bc, x, wind):
        # Enkel vinddrift-modell (for demo)
        v = v0
        t = x / (v*0.3048) if v > 0 else 0
        drift = wind * t * 10 * (1 - 0.01*bc)
        return drift

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("🔬 22LR Rimfire Analyzer")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(header)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Ammo-database
        tabs.addTab(self.create_ammo_tab(), "Ammo-database")
        # Tab 2: Kammerprofil
        tabs.addTab(self.create_chamber_tab(), "Kammerprofil")
        # Tab 3: Batch-logging
        tabs.addTab(self.create_batch_tab(), "Batch-logging")
        # Tab 4: Ammo-fit
        tabs.addTab(self.create_fit_tab(), "Ammo-fit")
        # Tab 5: Ballistisk simulering
        tabs.addTab(self.create_simulation_tab(), "Simulering")
        # Tab 6: Vær-logging
        tabs.addTab(self.create_weather_tab(), "Vær-logging")
        # Tab 7: Rapporter
        tabs.addTab(self.create_report_tab(), "Rapporter")
        # Tab 8: AI-tips
        tabs.addTab(self.create_ai_tab(), "AI-tips")

        # Lagring/lasting brukeroppsett
        save_btn = QPushButton("Lagre brukeroppsett")
        save_btn.clicked.connect(self.save_user_profile)
        layout.addWidget(save_btn)
        load_btn = QPushButton("Last brukeroppsett")
        load_btn.clicked.connect(self.load_user_profile)
        layout.addWidget(load_btn)
    def create_weather_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Logg værdata under test: temperatur, vind, trykk, fuktighet, skydekke."))

        self.weather_temp = QLineEdit(); self.weather_temp.setPlaceholderText("Temperatur (°C)")
        self.weather_wind = QLineEdit(); self.weather_wind.setPlaceholderText("Vind (m/s)")
        self.weather_dir = QLineEdit(); self.weather_dir.setPlaceholderText("Vindretning (°)")
        self.weather_pressure = QLineEdit(); self.weather_pressure.setPlaceholderText("Trykk (hPa)")
        self.weather_humidity = QLineEdit(); self.weather_humidity.setPlaceholderText("Fuktighet (%)")
        self.weather_cloud = QLineEdit(); self.weather_cloud.setPlaceholderText("Skydekke (%)")
        add_btn = QPushButton("Logg værdata")
        add_btn.clicked.connect(self.add_weather_entry)
        layout.addWidget(self.weather_temp)
        layout.addWidget(self.weather_wind)
        layout.addWidget(self.weather_dir)
        layout.addWidget(self.weather_pressure)
        layout.addWidget(self.weather_humidity)
        layout.addWidget(self.weather_cloud)
        layout.addWidget(add_btn)

        self.weather_table = QTableWidget()
        self.weather_table.setColumnCount(6)
        self.weather_table.setHorizontalHeaderLabels(["Temp", "Vind", "Retning", "Trykk", "Fuktighet", "Skydekke"])
        self.weather_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.weather_table)
        self.weather_entries = []

        export_btn = QPushButton("Eksporter værdata til Excel")
        export_btn.clicked.connect(self.export_weather_excel)
        layout.addWidget(export_btn)

        return widget

    def add_weather_entry(self):
        temp = self.weather_temp.text().strip()
        wind = self.weather_wind.text().strip()
        dir = self.weather_dir.text().strip()
        pressure = self.weather_pressure.text().strip()
        humidity = self.weather_humidity.text().strip()
        cloud = self.weather_cloud.text().strip()
        self.weather_entries.append({
            "Temp": temp, "Vind": wind, "Retning": dir, "Trykk": pressure, "Fuktighet": humidity, "Skydekke": cloud
        })
        self.update_weather_table()
        self.weather_temp.clear(); self.weather_wind.clear(); self.weather_dir.clear()
        self.weather_pressure.clear(); self.weather_humidity.clear(); self.weather_cloud.clear()

    def update_weather_table(self):
        self.weather_table.setRowCount(len(self.weather_entries))
        for i, entry in enumerate(self.weather_entries):
            self.weather_table.setItem(i, 0, QTableWidgetItem(entry["Temp"]))
            self.weather_table.setItem(i, 1, QTableWidgetItem(entry["Vind"]))
            self.weather_table.setItem(i, 2, QTableWidgetItem(entry["Retning"]))
            self.weather_table.setItem(i, 3, QTableWidgetItem(entry["Trykk"]))
            self.weather_table.setItem(i, 4, QTableWidgetItem(entry["Fuktighet"]))
            self.weather_table.setItem(i, 5, QTableWidgetItem(entry["Skydekke"]))

    def export_weather_excel(self):
        import pandas as pd
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getSaveFileName(self, "Lagre værdata som Excel", "", "Excel-filer (*.xlsx)")
        if fname:
            df = pd.DataFrame(self.weather_entries)
            df.to_excel(fname, index=False)

    def create_ammo_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Oversikt over 22LR fabrikkammo og egenskaper. Søk, filtrer og legg til ny ammo."))

        # Forhåndsutfylt 22LR-liste
        self.ammo_db = [
            {"merke": "CCI Standard", "hastighet": 1070, "bc": 0.120, "land": "USA"},
            {"merke": "Federal Gold Medal", "hastighet": 1080, "bc": 0.120, "land": "USA"},
            {"merke": "SK Rifle Match", "hastighet": 1070, "bc": 0.120, "land": "Tyskland"},
            {"merke": "Lapua Center-X", "hastighet": 1073, "bc": 0.120, "land": "Finland"},
            {"merke": "RWA Target", "hastighet": 1060, "bc": 0.120, "land": "Tyskland"},
            {"merke": "Eley Tenex", "hastighet": 1085, "bc": 0.120, "land": "UK"},
            {"merke": "Norma Match", "hastighet": 1100, "bc": 0.120, "land": "Sverige"},
            {"merke": "RWS Rifle Match", "hastighet": 1082, "bc": 0.120, "land": "Tyskland"},
            {"merke": "Winchester T22", "hastighet": 1150, "bc": 0.120, "land": "USA"},
            {"merke": "Aguila Super Extra", "hastighet": 1130, "bc": 0.120, "land": "Mexico"},
            {"merke": "Fiocchi Exacta", "hastighet": 1070, "bc": 0.120, "land": "Italia"},
        ]

        # Søkefelt
        self.ammo_search = QLineEdit()
        self.ammo_search.setPlaceholderText("Søk etter merke eller modell...")
        self.ammo_search.textChanged.connect(self.update_ammo_table)
        layout.addWidget(self.ammo_search)

        # Ammo-tabell
        self.ammo_table = QTableWidget()
        self.ammo_table.setColumnCount(4)
        self.ammo_table.setHorizontalHeaderLabels(["Merke/Modell", "Hastighet (fps)", "BC", "Land"])
        self.ammo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.ammo_table)
        self.update_ammo_table()

        # Legg til ny ammo
        add_group = QGroupBox("Legg til ny ammomodell")
        add_layout = QHBoxLayout()
        add_group.setLayout(add_layout)
        self.new_ammo_name = QLineEdit(); self.new_ammo_name.setPlaceholderText("Merke/modell")
        self.new_ammo_vel = QLineEdit(); self.new_ammo_vel.setPlaceholderText("Hastighet (fps)")
        self.new_ammo_bc = QLineEdit(); self.new_ammo_bc.setPlaceholderText("BC")
        self.new_ammo_land = QLineEdit(); self.new_ammo_land.setPlaceholderText("Land")
        add_btn = QPushButton("Legg til")
        add_btn.clicked.connect(self.add_new_ammo)
        add_layout.addWidget(self.new_ammo_name)
        add_layout.addWidget(self.new_ammo_vel)
        add_layout.addWidget(self.new_ammo_bc)
        add_layout.addWidget(self.new_ammo_land)
        add_layout.addWidget(add_btn)
        layout.addWidget(add_group)

        return widget

    def update_ammo_table(self):
        query = self.ammo_search.text().lower() if hasattr(self, 'ammo_search') else ""
        filtered = [a for a in self.ammo_db if query in a["merke"].lower() or query in a["land"].lower()]
        self.ammo_table.setRowCount(len(filtered))
        for i, ammo in enumerate(filtered):
            self.ammo_table.setItem(i, 0, QTableWidgetItem(ammo["merke"]))
            self.ammo_table.setItem(i, 1, QTableWidgetItem(str(ammo["hastighet"])))
            self.ammo_table.setItem(i, 2, QTableWidgetItem(str(ammo["bc"])))
            self.ammo_table.setItem(i, 3, QTableWidgetItem(ammo["land"]))

    def add_new_ammo(self):
        name = self.new_ammo_name.text().strip()
        vel = self.new_ammo_vel.text().strip()
        bc = self.new_ammo_bc.text().strip()
        land = self.new_ammo_land.text().strip()
        if not name or not vel or not bc or not land:
            return
        try:
            vel = int(vel)
            bc = float(bc)
        except Exception:
            return
        self.ammo_db.append({"merke": name, "hastighet": vel, "bc": bc, "land": land})
        self.update_ammo_table()

    def create_chamber_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Registrer og analyser kammerprofil for rifle."))
        # TODO: Implementer kammerprofil input og analyse
        return widget

    def create_batch_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Logg og analyser batcher/lots av 22LR ammo. Legg inn fabrikkdata, testverdier og bilde av samling. Få vitenskapelig analyse og grafer."))

        # Input for lot/batch
        form_group = QGroupBox("Registrer ny lot/batch")
        form_layout = QVBoxLayout()
        form_group.setLayout(form_layout)

        # Våpentype (rifle/pistol)
        self.lot_weapon_type = QComboBox()
        self.lot_weapon_type.addItems(["Rifle", "Pistol"])
        form_layout.addWidget(self.lot_weapon_type)

        self.lot_ammo_combo = QComboBox()
        self.lot_ammo_combo.addItem("Velg ammomodell...")
        for ammo in getattr(self, 'ammo_db', []):
            self.lot_ammo_combo.addItem(ammo["merke"])
        self.lot_lotnr = QLineEdit(); self.lot_lotnr.setPlaceholderText("Lot/batch-nummer")
        self.lot_factory_vel = QLineEdit(); self.lot_factory_vel.setPlaceholderText("Fabrikkhastighet (fps)")
        self.lot_factory_bc = QLineEdit(); self.lot_factory_bc.setPlaceholderText("Fabrikk BC")
        self.lot_test_vel = QLineEdit(); self.lot_test_vel.setPlaceholderText("Testet hastighet (fps)")
        self.lot_group_size = QLineEdit(); self.lot_group_size.setPlaceholderText("Samling (mm)")
        self.lot_notes = QLineEdit(); self.lot_notes.setPlaceholderText("Notater")
        self.lot_img_btn = QPushButton("Last opp bilde av samling/skive")
        self.lot_img_btn.clicked.connect(self.upload_lot_image)
        self.lot_img_path = QLabel("")

        # Pistolspesifikke felter
        self.lot_pistol_fields = {}
        self.lot_pistol_fields["skive_type"] = QLineEdit(); self.lot_pistol_fields["skive_type"].setPlaceholderText("F.eks: ISSF, NSF")
        self.lot_pistol_fields["avtrekk"] = QLineEdit(); self.lot_pistol_fields["avtrekk"].setPlaceholderText("F.eks: 1000g, justerbar")
        self.lot_pistol_fields["magasin"] = QSpinBox(); self.lot_pistol_fields["magasin"].setRange(1, 20)
        self.lot_pistol_fields["score"] = QLineEdit(); self.lot_pistol_fields["score"].setPlaceholderText("Treffprosent eller poengsum")
        self.lot_pistol_fields["img"] = QPushButton("Last opp bilde av skive")
        self.lot_pistol_img_path = QLabel("")
        def upload_pistol_img():
            from PyQt6.QtWidgets import QFileDialog
            fname, _ = QFileDialog.getOpenFileName(self, "Velg bilde av skive", "", "Bilder (*.png *.jpg *.jpeg)")
            if fname:
                self.lot_pistol_img_path.setText(fname)
        self.lot_pistol_fields["img"].clicked.connect(upload_pistol_img)
        for label, widget in self.lot_pistol_fields.items():
            if label == "img":
                form_layout.addWidget(widget)
                form_layout.addWidget(self.lot_pistol_img_path)
            else:
                form_layout.addWidget(widget)
            widget.hide()
        self.lot_pistol_img_path.hide()

        def on_lot_weapon_type_changed(value):
            is_pistol = value == "Pistol"
            for label, widget in self.lot_pistol_fields.items():
                widget.setVisible(is_pistol)
                if label == "img":
                    self.lot_pistol_img_path.setVisible(is_pistol)
            self.lot_group_size.setVisible(not is_pistol)  # Skive for pistol, samling for rifle
        self.lot_weapon_type.currentTextChanged.connect(on_lot_weapon_type_changed)

        form_layout.addWidget(self.lot_ammo_combo)
        form_layout.addWidget(self.lot_lotnr)
        form_layout.addWidget(self.lot_factory_vel)
        form_layout.addWidget(self.lot_factory_bc)
        form_layout.addWidget(self.lot_test_vel)
        form_layout.addWidget(self.lot_group_size)
        form_layout.addWidget(self.lot_notes)
        form_layout.addWidget(self.lot_img_btn)
        form_layout.addWidget(self.lot_img_path)
        add_btn = QPushButton("Registrer lot")
        add_btn.clicked.connect(self.add_lot_entry)
        form_layout.addWidget(add_btn)
        layout.addWidget(form_group)

        # Tabell for lot-logging
        self.lot_table = QTableWidget()
        self.lot_table.setColumnCount(8)
        self.lot_table.setHorizontalHeaderLabels(["Ammo", "Lot", "Fabrikk V", "Fabrikk BC", "Test V", "Samling", "Notater", "Bilde"])
        self.lot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.lot_table)
        self.lot_entries = []

        # Statistikk og grafer
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        self.stats_img = QLabel()
        layout.addWidget(self.stats_img)

        stats_btn = QPushButton("Analyser statistikk og vis grafer")
        stats_btn.clicked.connect(self.analyze_lot_stats)
        layout.addWidget(stats_btn)

        return widget

    def analyze_lot_stats(self):
        import numpy as np
        import matplotlib.pyplot as plt
        import io, base64
        # Hent testverdier
        test_vels = [float(e["tvel"]) for e in self.lot_entries if e["tvel"]]
        group_sizes = [float(e["group"]) for e in self.lot_entries if e["group"]]
        factory_vels = [float(e["fvel"]) for e in self.lot_entries if e["fvel"]]
        # Statistikk
        stats = []
        if test_vels:
            stats.append(f"Gjennomsnitt testet hastighet: {np.mean(test_vels):.1f} fps")
            stats.append(f"Standardavvik: {np.std(test_vels):.2f} fps")
            stats.append(f"Median: {np.median(test_vels):.1f} fps")
        if group_sizes:
            stats.append(f"Gjennomsnitt samling: {np.mean(group_sizes):.1f} mm")
            stats.append(f"Standardavvik: {np.std(group_sizes):.2f} mm")
            stats.append(f"Median: {np.median(group_sizes):.1f} mm")
        # Avvik mot fabrikkdata
        if test_vels and factory_vels:
            avvik = np.mean(test_vels) - np.mean(factory_vels)
            stats.append(f"Avvik fra fabrikkhastighet: {avvik:+.1f} fps ({100*avvik/np.mean(factory_vels):+.1f}%)")
        self.stats_text.setText("\n".join(stats))
        # Grafer
        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        if test_vels:
            axs[0].hist(test_vels, bins=8, color='navy', alpha=0.7)
            axs[0].set_title("Testet hastighet (fps)")
        if group_sizes:
            axs[1].boxplot(group_sizes, vert=False)
            axs[1].set_title("Samling (mm)")
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        self.stats_img.setText(f'<img src="data:image/png;base64,{img_b64}" style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px #888;" />')

    def add_lot_entry(self):
        ammo = self.lot_ammo_combo.currentText()
        lotnr = self.lot_lotnr.text().strip()
        fvel = self.lot_factory_vel.text().strip()
        fbc = self.lot_factory_bc.text().strip()
        tvel = self.lot_test_vel.text().strip()
        group = self.lot_group_size.text().strip()
        notes = self.lot_notes.text().strip()
        img = self.lot_img_path.text()
        weapon_type = self.lot_weapon_type.currentText()
        entry = {
            "ammo": ammo, "lot": lotnr, "fvel": fvel, "fbc": fbc,
            "tvel": tvel, "group": group, "notes": notes, "img": img,
            "weapon_type": weapon_type
        }
        if weapon_type == "Pistol":
            entry["skive_type"] = self.lot_pistol_fields["skive_type"].text().strip()
            entry["avtrekk"] = self.lot_pistol_fields["avtrekk"].text().strip()
            entry["magasin"] = self.lot_pistol_fields["magasin"].value()
            entry["score"] = self.lot_pistol_fields["score"].text().strip()
            entry["img"] = self.lot_pistol_img_path.text()
        if not ammo or ammo == "Velg ammomodell..." or not lotnr:
            return
        self.lot_entries.append(entry)
        self.update_lot_table()
        self.lot_lotnr.clear(); self.lot_factory_vel.clear(); self.lot_factory_bc.clear()
        self.lot_test_vel.clear(); self.lot_group_size.clear(); self.lot_notes.clear(); self.lot_img_path.setText("")
        for widget in self.lot_pistol_fields.values():
            if hasattr(widget, 'clear'):
                widget.clear()

    def update_lot_table(self):
        self.lot_table.setRowCount(len(self.lot_entries))
        for i, entry in enumerate(self.lot_entries):
            self.lot_table.setItem(i, 0, QTableWidgetItem(entry["ammo"]))
            self.lot_table.setItem(i, 1, QTableWidgetItem(entry["lot"]))
            self.lot_table.setItem(i, 2, QTableWidgetItem(entry["fvel"]))
            self.lot_table.setItem(i, 3, QTableWidgetItem(entry["fbc"]))
            self.lot_table.setItem(i, 4, QTableWidgetItem(entry["tvel"]))
            self.lot_table.setItem(i, 5, QTableWidgetItem(entry["group"]))
            self.lot_table.setItem(i, 6, QTableWidgetItem(entry["notes"]))
            self.lot_table.setItem(i, 7, QTableWidgetItem("Bilde" if entry["img"] else ""))

    def upload_lot_image(self):
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getOpenFileName(self, "Velg bilde av samling/skive", "", "Bilder (*.png *.jpg *.jpeg)")
        if fname:
            self.lot_img_path.setText(fname)

    def create_fit_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Analyser ammo-fit og match mellom rifle og ammunisjon."))
        # TODO: Implementer ammo-fit analyse
        return widget

    def create_ballistics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Ballistisk kalkyle for 22LR langhold."))
        # TODO: Integrer BallisticsCalculator for 22LR
        return widget

    def create_report_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Generer rapport for alle tester, statistikk og bilder. Eksporter til HTML. Velg selv hvilke datafelter du vil ha med."))

        # Feltvalg for eksport
        self.export_fields = {
            "Ammo": True,
            "Lot": True,
            "Fabrikk V": True,
            "Fabrikk BC": True,
            "Test V": True,
            "Samling": True,
            "Notater": True,
            "Bilde": True,
            "Våpentype": True,
            "Skive": True,
            "Avtrekk": True,
            "Magasin": True,
            "Score": True
        }
        field_group = QGroupBox("Velg datafelter for eksport")
        field_layout = QHBoxLayout()
        field_group.setLayout(field_layout)
        self.field_checkboxes = {}
        for key in self.export_fields:
            cb = QCheckBox(key)
            cb.setChecked(True)
            cb.stateChanged.connect(lambda _, k=key: self.toggle_export_field(k))
            self.field_checkboxes[key] = cb
            field_layout.addWidget(cb)
        layout.addWidget(field_group)

        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)
        gen_btn = QPushButton("Generer rapport")
        gen_btn.clicked.connect(self.generate_report)
        layout.addWidget(gen_btn)
        export_html_btn = QPushButton("Eksporter til HTML-fil")
        export_html_btn.clicked.connect(self.export_report)
        layout.addWidget(export_html_btn)

        export_pdf_btn = QPushButton("Eksporter til PDF")
        export_pdf_btn.clicked.connect(self.export_report_pdf)
        layout.addWidget(export_pdf_btn)

        export_excel_btn = QPushButton("Eksporter til Excel")
        export_excel_btn.clicked.connect(self.export_report_excel)
        layout.addWidget(export_excel_btn)
        return widget

    def toggle_export_field(self, key):
        self.export_fields[key] = self.field_checkboxes[key].isChecked()
    def export_report_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtWidgets import QFileDialog
        printer = QPrinter()
        fname, _ = QFileDialog.getSaveFileName(self, "Lagre rapport som PDF", "", "PDF-filer (*.pdf)")
        if fname:
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(fname)
            # Generer rapport med valgte felter før eksport
            self.generate_report()
            self.report_text.document().print(printer)

    def export_report_excel(self):
        import pandas as pd
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getSaveFileName(self, "Lagre rapport som Excel", "", "Excel-filer (*.xlsx)")
        if fname:
            lots = getattr(self, 'lot_entries', [])
            fields = [k for k, v in self.export_fields.items() if v]
            excel_map = {
                "Ammo": "ammo", "Lot": "lot", "Fabrikk V": "fvel", "Fabrikk BC": "fbc",
                "Test V": "tvel", "Samling": "group", "Notater": "notes", "Bilde": "img",
                "Våpentype": "weapon_type", "Skive": "skive_type", "Avtrekk": "avtrekk", "Magasin": "magasin", "Score": "score"
            }
            df = pd.DataFrame([{excel_map[f]: e.get(excel_map[f], "") for f in fields} for e in lots])
            df.to_excel(fname, index=False)

    def generate_report(self):
        lots = getattr(self, 'lot_entries', [])
        fields = [k for k, v in self.export_fields.items() if v]
        html = ["<h2>22LR Testrapport</h2>"]
        html.append("<h3>Batcher/Lots</h3><table border='1' cellpadding='4' style='border-collapse:collapse;'>")
        html.append("<tr>" + ''.join([f"<th>{f}</th>" for f in fields]) + "</tr>")
        for e in lots:
            row = []
            for f in fields:
                if f == "Ammo": row.append(f"<td>{e.get('ammo','')}</td>")
                elif f == "Lot": row.append(f"<td>{e.get('lot','')}</td>")
                elif f == "Fabrikk V": row.append(f"<td>{e.get('fvel','')}</td>")
                elif f == "Fabrikk BC": row.append(f"<td>{e.get('fbc','')}</td>")
                elif f == "Test V": row.append(f"<td>{e.get('tvel','')}</td>")
                elif f == "Samling": row.append(f"<td>{e.get('group','')}</td>")
                elif f == "Notater": row.append(f"<td>{e.get('notes','')}</td>")
                elif f == "Våpentype": row.append(f"<td>{e.get('weapon_type','')}</td>")
                elif f == "Skive": row.append(f"<td>{e.get('skive_type','')}</td>")
                elif f == "Avtrekk": row.append(f"<td>{e.get('avtrekk','')}</td>")
                elif f == "Magasin": row.append(f"<td>{e.get('magasin','')}</td>")
                elif f == "Score": row.append(f"<td>{e.get('score','')}</td>")
                elif f == "Bilde":
                    img_html = f'<img src="file://{e.get("img","")}" width="80" />' if e.get("img","") else ""
                    row.append(f"<td>{img_html}</td>")
            html.append("<tr>" + ''.join(row) + "</tr>")
        html.append("</table>")
        html.append("<h3>Statistikk</h3>")
        html.append(self.stats_text.toPlainText().replace('\n', '<br>'))
        html.append("<h3>Grafer</h3>")
        html.append(self.stats_img.text())
        self.report_text.setHtml(''.join(html))

    def export_report(self):
        from PyQt6.QtWidgets import QFileDialog
        fname, _ = QFileDialog.getSaveFileName(self, "Lagre rapport som HTML", "", "HTML-filer (*.html)")
        if fname:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(self.report_text.toHtml())

    def create_ai_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Få AI-tips om ammo-valg, batch-testing og ballistikk for 22LR. Personlig anbefaling basert på dine data."))
        self.ai_input = QLineEdit(); self.ai_input.setPlaceholderText("Spør AI-coach om ammo, test, ballistikk...")
        layout.addWidget(self.ai_input)
        ai_btn = QPushButton("Få AI-tips")
        ai_btn.clicked.connect(self.get_ai_tip)
        layout.addWidget(ai_btn)
        self.ai_output = QTextEdit(); self.ai_output.setReadOnly(True)
        layout.addWidget(self.ai_output)
        return widget

    def get_ai_tip(self):
        # Demo: Generer AI-tips basert på brukerdata og input
        question = self.ai_input.text().strip()
        lots = getattr(self, 'lot_entries', [])
        ammo_db = getattr(self, 'ammo_db', [])
        if not question:
            self.ai_output.setText("Skriv inn et spørsmål eller ønsket analyse!"); return
        # Enkel heuristikk/demo
        if "presisjon" in question.lower():
            best = sorted(lots, key=lambda e: float(e.get("group", 9999)))[:1]
            if best:
                self.ai_output.setText(f"Beste presisjon: {best[0]['ammo']} lot {best[0]['lot']} med samling {best[0]['group']} mm.")
            else:
                self.ai_output.setText("Ingen testdata for presisjon.")
        elif "hastighet" in question.lower():
            fastest = sorted(lots, key=lambda e: float(e.get("tvel", 0)), reverse=True)[:1]
            if fastest:
                self.ai_output.setText(f"Høyeste målt hastighet: {fastest[0]['ammo']} lot {fastest[0]['lot']} med {fastest[0]['tvel']} fps.")
            else:
                self.ai_output.setText("Ingen testdata for hastighet.")
        elif "anbefal" in question.lower() or "match" in question.lower():
            # Demo: anbefal ammo med lavt avvik og god presisjon
            best = sorted(lots, key=lambda e: (abs(float(e.get("tvel",0))-float(e.get("fvel",0))), float(e.get("group",9999))))[:1]
            if best:
                self.ai_output.setText(f"Anbefalt ammo: {best[0]['ammo']} lot {best[0]['lot']} (samling {best[0]['group']} mm, avvik {float(best[0]['tvel'])-float(best[0]['fvel']):+.1f} fps)")
            else:
                self.ai_output.setText("Ingen testdata for anbefaling.")
        else:
            self.ai_output.setText("AI-coach: Spør om presisjon, hastighet, anbefaling eller match!")
