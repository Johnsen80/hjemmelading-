"""
Gordon Reloading Tool (GRT) Integration
Importerer og analyserer data fra GRT for bedre trykkanalyse og ballistikk
"""

import json
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.database.database import get_database


class GRTIntegration(QWidget):
    """Widget for GRT-integrasjon"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()
        self.load_grt_profiles()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("🔗 Gordon Reloading Tool Integrasjon")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Info om GRT
        info = QLabel(
            """
        <b>Hva er dette?</b><br>
        Gordon Reloading Tool (GRT) er et avansert intern ballistikk-program som beregner:
        <ul>
            <li><b>Trykk</b>: Estimert max trykk i PSI/bar</li>
            <li><b>Hastighet</b>: Predikert utgangshastighet basert på krutt/kule/hylse</li>
            <li><b>Fyllingsprosent</b>: Hvor full hylsen er</li>
            <li><b>Trykkurve</b>: Detaljer om trykk-oppbygning</li>
        </ul>

        <b>Hvordan bruke integrasjonen:</b><br>
        1. Eksporter profiler fra GRT som JSON/CSV<br>
        2. Importer dem her<br>
        3. Programmet kobler GRT-data med dine faktiske skyte-resultater<br>
        4. Få kraftig analyse: Predikert vs faktisk hastighet, trykkevarsler, osv.
        """
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            """
            background-color: #e7f3ff;
            border: 2px solid #2196F3;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0px;
        """
        )
        layout.addWidget(info)

        # Knapper
        btn_layout = QHBoxLayout()

        import_btn = QPushButton("📥 Importer fra GRT")
        import_btn.setMinimumHeight(40)
        import_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold;"
        )
        import_btn.clicked.connect(self.import_from_grt)
        btn_layout.addWidget(import_btn)

        export_btn = QPushButton("📤 Eksporter til GRT")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.export_to_grt)
        btn_layout.addWidget(export_btn)

        analyze_btn = QPushButton("📊 Analyser vs Faktiske Data")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.analyze_grt_vs_actual)
        btn_layout.addWidget(analyze_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Tabell med GRT-profiler
        self.grt_table = QTableWidget()
        self.grt_table.setColumnCount(8)
        self.grt_table.setHorizontalHeaderLabels(
            [
                "Ammunisjonsprofil",
                "GRT Hastighet",
                "Faktisk Hastighet",
                "Diff",
                "Max Trykk (PSI)",
                "Fylling %",
                "Status",
                "Importert",
            ]
        )
        self.grt_table.horizontalHeader().setStretchLastSection(True)
        self.grt_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.grt_table)

        # Tips
        tips = QLabel(
            """
        <b>💡 Tips:</b>
        <ul>
            <li>GRT gir deg <b>predikert trykk</b> - sammenlign med trykkegn fra faktisk skyting</li>
            <li>Stor forskjell mellom GRT hastighet og faktisk? Sjekk kronometerdata og løpslengde</li>
            <li>Bruk GRT for å finne <b>sikre start-ladninger</b> før du begynner testing</li>
            <li>GRT kan forutsi hvilke krutt som gir <b>best fyllingsprosent</b> for din kaliber</li>
        </ul>
        """
        )
        tips.setWordWrap(True)
        layout.addWidget(tips)

    def load_grt_profiles(self):
        """Laster GRT-profiler fra database"""
        profiles = self.db.execute_query(
            """
            SELECT
                ap.*,
                grt.predicted_velocity,
                grt.max_pressure_psi,
                grt.case_fill_percent,
                grt.grt_data,
                grt.import_date
            FROM ammo_profiles ap
            LEFT JOIN grt_data grt ON ap.id = grt.ammo_profile_id
            ORDER BY ap.name
        """
        )

        if not profiles:
            profiles = []

        self.grt_table.setRowCount(len(profiles))

        for i, profile in enumerate(profiles):
            # Navn
            self.grt_table.setItem(i, 0, QTableWidgetItem(profile["name"]))

            # GRT hastighet
            grt_vel = (
                f"{profile['predicted_velocity']:.0f}"
                if profile["predicted_velocity"]
                else "-"
            )
            self.grt_table.setItem(i, 1, QTableWidgetItem(grt_vel))

            # Faktisk hastighet
            actual_vel = (
                f"{profile['velocity_fps']:.0f}" if profile["velocity_fps"] else "-"
            )
            self.grt_table.setItem(i, 2, QTableWidgetItem(actual_vel))

            # Diff
            if profile["predicted_velocity"] and profile["velocity_fps"]:
                diff = profile["velocity_fps"] - profile["predicted_velocity"]
                diff_item = QTableWidgetItem(f"{diff:+.0f} fps")
                if abs(diff) < 30:
                    diff_item.setForeground(QColor("green"))
                elif abs(diff) < 60:
                    diff_item.setForeground(QColor("orange"))
                else:
                    diff_item.setForeground(QColor("red"))
                self.grt_table.setItem(i, 3, diff_item)
            else:
                self.grt_table.setItem(i, 3, QTableWidgetItem("-"))

            # Max trykk
            pressure = (
                f"{profile['max_pressure_psi']:.0f}"
                if profile["max_pressure_psi"]
                else "-"
            )
            pressure_item = QTableWidgetItem(pressure)
            if profile["max_pressure_psi"]:
                # SAAMI grenser (eks: .308 Win = 62000 PSI)
                if profile["max_pressure_psi"] > 60000:
                    pressure_item.setBackground(QColor(255, 200, 200))  # Rød
                elif profile["max_pressure_psi"] > 55000:
                    pressure_item.setBackground(QColor(255, 255, 200))  # Gul
                else:
                    pressure_item.setBackground(QColor(200, 255, 200))  # Grønn
            self.grt_table.setItem(i, 4, pressure_item)

            # Fylling %
            fill = (
                f"{profile['case_fill_percent']:.1f}%"
                if profile["case_fill_percent"]
                else "-"
            )
            self.grt_table.setItem(i, 5, QTableWidgetItem(fill))

            # Status
            if profile["predicted_velocity"]:
                if profile["velocity_fps"]:
                    status = "✅ Verifisert"
                    status_color = QColor("green")
                else:
                    status = "⏳ GRT importert, test utstår"
                    status_color = QColor("orange")
            else:
                status = "⚪ Ingen GRT data"
                status_color = QColor("gray")

            status_item = QTableWidgetItem(status)
            status_item.setForeground(status_color)
            self.grt_table.setItem(i, 6, status_item)

            # Importert dato
            import_date = profile["import_date"] if profile["import_date"] else "-"
            self.grt_table.setItem(i, 7, QTableWidgetItem(import_date))

            self.grt_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, profile["id"])

    def import_from_grt(self):
        """Importerer data fra GRT"""
        dialog = GRTImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_grt_profiles()

    def export_to_grt(self):
        """Eksporterer til GRT-format"""
        # Hent alle ammunisjonsprofiler
        profiles = self.db.get_all("ammo_profiles")

        if not profiles:
            QMessageBox.warning(
                self, "Ingen profiler", "Du har ingen ammunisjonsprofiler å eksportere!"
            )
            return

        # Velg lagringsplass
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Eksporter til GRT-format",
            f"grt_export_{datetime.now().strftime('%Y%m%d')}.json",
            "JSON filer (*.json);;CSV filer (*.csv)",
        )

        if not file_path:
            return

        # Bygg GRT-kompatibel struktur
        grt_export = []

        for profile in profiles:
            # Hent komponenter
            bullet = (
                self.db.get_by_id("bullets", profile["bullet_id"])
                if profile["bullet_id"]
                else None
            )
            powder = (
                self.db.get_by_id("powder", profile["powder_id"])
                if profile["powder_id"]
                else None
            )
            primer = (
                self.db.get_by_id("primers", profile["primer_id"])
                if profile["primer_id"]
                else None
            )
            case_data = (
                self.db.get_by_id("cases", profile["case_id"])
                if profile["case_id"]
                else None
            )

            grt_item = {
                "profile_name": profile["name"],
                "caliber": profile["caliber"],
                "bullet": {
                    "name": bullet["name"] if bullet else "",
                    "weight_grains": profile["bullet_weight"],
                    "diameter": None,  # GRT trenger dette
                    "length": None,
                },
                "powder": {
                    "name": powder["name"] if powder else "",
                    "charge_grains": profile["powder_charge"],
                    "type": powder["type"] if powder else None,
                },
                "primer": {
                    "name": primer["name"] if primer else "",
                    "type": primer["type"] if primer else "",
                },
                "case": {
                    "name": case_data["name"] if case_data else "",
                    "capacity": None,  # GRT trenger dette
                    "length": None,
                },
                "coal": profile["coal"],
                "actual_velocity": profile["velocity_fps"],
                "notes": profile["notes"],
            }

            grt_export.append(grt_item)

        # Lagre fil
        try:
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(grt_export, f, indent=2, ensure_ascii=False)
            else:  # CSV
                import csv

                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    if grt_export:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=[
                                "profile_name",
                                "caliber",
                                "bullet_weight",
                                "powder_name",
                                "powder_charge",
                                "coal",
                                "actual_velocity",
                            ],
                        )
                        writer.writeheader()
                        for item in grt_export:
                            writer.writerow(
                                {
                                    "profile_name": item["profile_name"],
                                    "caliber": item["caliber"],
                                    "bullet_weight": item["bullet"]["weight_grains"],
                                    "powder_name": item["powder"]["name"],
                                    "powder_charge": item["powder"]["charge_grains"],
                                    "coal": item["coal"],
                                    "actual_velocity": item["actual_velocity"],
                                }
                            )

            QMessageBox.information(
                self,
                "Eksport vellykket",
                f"Eksportert {len(grt_export)} profiler til:\n{file_path}\n\n"
                f"Du kan nå åpne denne filen i GRT for å kjøre simuleringer.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke eksportere:\n{str(e)}")

    def analyze_grt_vs_actual(self):
        """Analyserer GRT-prediksjoner vs faktiske resultater"""
        # Hent profiler med både GRT og faktiske data
        profiles = self.db.execute_query(
            """
            SELECT
                ap.*,
                grt.predicted_velocity,
                grt.max_pressure_psi,
                grt.case_fill_percent,
                grt.predicted_accuracy_potential
            FROM ammo_profiles ap
            INNER JOIN grt_data grt ON ap.id = grt.ammo_profile_id
            WHERE ap.velocity_fps IS NOT NULL
        """
        )

        if not profiles:
            QMessageBox.information(
                self,
                "Ingen data",
                "Fant ingen profiler med både GRT-data og faktiske skyte-resultater.\n\n"
                "Importer GRT-data først, og legg deretter inn faktiske hastigheter.",
            )
            return

        # Åpne analyse-vindu
        dialog = GRTAnalysisDialog(self, profiles)
        dialog.exec()


class GRTImportDialog(QDialog):
    """Dialog for import av GRT-data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.setWindowTitle("Importer fra Gordon Reloading Tool")
        self.setMinimumSize(700, 500)
        self.init_ui()

    def init_ui(self):
        """Initialiserer dialog"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Forklaring
        info = QLabel(
            """
        <h3>Slik importerer du fra GRT:</h3>
        <ol>
            <li>Åpne Gordon Reloading Tool</li>
            <li>Kjør simuleringer for dine ladninger</li>
            <li>Eksporter resultatene (JSON anbefalt)</li>
            <li>Velg filen nedenfor</li>
        </ol>

        <b>Forventet format:</b> JSON eller CSV med felt for kule, krutt, hastighet, trykk.
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Filvalg
        file_group = QGroupBox("1. Velg GRT-fil")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)

        file_btn_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Ingen fil valgt...")
        self.file_path.setReadOnly(True)
        file_btn_layout.addWidget(self.file_path)

        browse_btn = QPushButton("📁 Bla...")
        browse_btn.clicked.connect(self.browse_file)
        file_btn_layout.addWidget(browse_btn)

        file_layout.addLayout(file_btn_layout)
        layout.addWidget(file_group)

        # Matching-strategi
        match_group = QGroupBox("2. Kobling til eksisterende profiler")
        match_layout = QVBoxLayout()
        match_group.setLayout(match_layout)

        self.match_strategy = QComboBox()
        self.match_strategy.addItems(
            [
                "Match på navn (eksakt)",
                "Match på navn (fuzzy)",
                "Match på kaliber + kulevekt + kruttvekt",
                "Opprett nye profiler automatisk",
            ]
        )
        match_layout.addWidget(QLabel("Matchingsstrategi:"))
        match_layout.addWidget(self.match_strategy)

        layout.addWidget(match_group)

        # Forhåndsvisning
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(
            ["GRT Profil", "Hastighet", "Trykk (PSI)", "Fylling %", "Match med"]
        )
        layout.addWidget(QLabel("3. Forhåndsvisning:"))
        layout.addWidget(self.preview_table)

        # Knapper
        btn_layout = QHBoxLayout()
        import_btn = QPushButton("✅ Importer")
        import_btn.clicked.connect(self.do_import)
        cancel_btn = QPushButton("❌ Avbryt")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def browse_file(self):
        """Velg GRT-fil"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Velg GRT-fil",
            "",
            "JSON filer (*.json);;CSV filer (*.csv);;Alle filer (*.*)",
        )

        if file_path:
            self.file_path.setText(file_path)
            self.parse_and_preview(file_path)

    def parse_and_preview(self, file_path):
        """Parser og viser forhåndsvisning"""
        try:
            if file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                QMessageBox.warning(
                    self,
                    "Format ikke støttet",
                    "Kun JSON støttes foreløpig. CSV kommer snart.",
                )
                return

            # Forventet format (eksempel):
            # [
            #   {
            #     "name": "6.5 CM ELD-M 140gr",
            #     "velocity_fps": 2750,
            #     "max_pressure_psi": 58000,
            #     "case_fill_percent": 98.5,
            #     ...
            #   }
            # ]

            if not isinstance(data, list):
                QMessageBox.warning(
                    self, "Ugyldig format", "Forventet en liste med profiler."
                )
                return

            self.grt_data = data
            self.preview_table.setRowCount(len(data))

            for i, item in enumerate(data):
                # GRT Profil navn
                name = item.get("name", item.get("profile_name", f"Profil {i+1}"))
                self.preview_table.setItem(i, 0, QTableWidgetItem(name))

                # Hastighet
                vel = item.get("velocity_fps", item.get("predicted_velocity", 0))
                self.preview_table.setItem(i, 1, QTableWidgetItem(f"{vel:.0f}"))

                # Trykk
                pressure = item.get("max_pressure_psi", item.get("pressure", 0))
                self.preview_table.setItem(i, 2, QTableWidgetItem(f"{pressure:.0f}"))

                # Fylling
                fill = item.get("case_fill_percent", item.get("fill_ratio", 0))
                self.preview_table.setItem(i, 3, QTableWidgetItem(f"{fill:.1f}%"))

                # Finn match
                match = self.find_matching_profile(item)
                match_text = match["name"] if match else "❌ Ingen match"
                match_item = QTableWidgetItem(match_text)
                if match:
                    match_item.setForeground(QColor("green"))
                else:
                    match_item.setForeground(QColor("red"))
                self.preview_table.setItem(i, 4, match_item)

            self.preview_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(
                self, "Parse-feil", f"Kunne ikke lese filen:\n{str(e)}"
            )

    def find_matching_profile(self, grt_item):
        """Finner matchende ammunisjonsprofil"""
        strategy = self.match_strategy.currentText()

        profiles = self.db.get_all("ammo_profiles")

        grt_name = grt_item.get("name", grt_item.get("profile_name", ""))

        if "eksakt" in strategy:
            # Eksakt navn-match
            for profile in profiles:
                if profile["name"].lower() == grt_name.lower():
                    return profile

        elif "kaliber" in strategy:
            # Match på specs
            grt_caliber = grt_item.get("caliber", "")
            grt_bullet_weight = grt_item.get("bullet", {}).get("weight_grains", 0)
            grt_powder_charge = grt_item.get("powder", {}).get("charge_grains", 0)

            for profile in profiles:
                if (
                    profile["caliber"] == grt_caliber
                    and abs(profile["bullet_weight"] - grt_bullet_weight) < 1
                    and abs(profile["powder_charge"] - grt_powder_charge) < 0.5
                ):
                    return profile

        return None

    def do_import(self):
        """Utfører import"""
        if not hasattr(self, "grt_data"):
            QMessageBox.warning(self, "Ingen data", "Velg en fil først!")
            return

        imported = 0
        skipped = 0

        for item in self.grt_data:
            match = self.find_matching_profile(item)

            if match:
                # Oppdater eksisterende profil med GRT-data
                grt_record = {
                    "ammo_profile_id": match["id"],
                    "predicted_velocity": item.get(
                        "velocity_fps", item.get("predicted_velocity")
                    ),
                    "max_pressure_psi": item.get(
                        "max_pressure_psi", item.get("pressure")
                    ),
                    "case_fill_percent": item.get(
                        "case_fill_percent", item.get("fill_ratio")
                    ),
                    "predicted_accuracy_potential": item.get("accuracy_potential"),
                    "grt_data": json.dumps(item),
                    "import_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Sjekk om GRT-data allerede eksisterer
                existing = self.db.execute_query(
                    "SELECT id FROM grt_data WHERE ammo_profile_id = ?", (match["id"],)
                )

                if existing:
                    self.db.update("grt_data", existing[0]["id"], grt_record)
                else:
                    self.db.insert("grt_data", grt_record)

                imported += 1
            else:
                skipped += 1

        QMessageBox.information(
            self,
            "Import fullført",
            f"✅ Importert: {imported} profiler\n"
            f"⏭️ Hoppet over (ingen match): {skipped} profiler\n\n"
            f"GRT-data er nå koblet til dine ammunisjonsprofiler!",
        )

        self.accept()


class GRTAnalysisDialog(QDialog):
    """Dialog for analyse av GRT vs faktiske data"""

    def __init__(self, parent=None, profiles=None):
        super().__init__(parent)
        self.profiles = profiles or []
        self.setWindowTitle("GRT Analyse: Predikert vs Faktisk")
        self.setMinimumSize(1000, 700)
        self.init_ui()

    def init_ui(self):
        """Initialiserer analyse-vindu"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("<h2>📊 GRT Prediksjon vs Faktiske Resultater</h2>")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Hastighets-sammenligning
        tabs.addTab(self.create_velocity_tab(), "🎯 Hastighet")

        # Tab 2: Trykk-analyse
        tabs.addTab(self.create_pressure_tab(), "⚠️ Trykk")

        # Tab 3: Nøyaktighet
        tabs.addTab(self.create_accuracy_tab(), "📈 Nøyaktighet")

        # Lukk
        close_btn = QPushButton("Lukk")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def create_velocity_tab(self):
        """Hastighets-analyse tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <b>Hastighets-sammenligning:</b> Hvor godt stemmer GRT-prediksjoner med faktiske målinger?
        """
        )
        layout.addWidget(info)

        # Tabell
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Profil", "GRT Hastighet", "Faktisk Hastighet", "Differanse", "Avvik %"]
        )
        table.setRowCount(len(self.profiles))

        total_diff = 0

        for i, profile in enumerate(self.profiles):
            table.setItem(i, 0, QTableWidgetItem(profile["name"]))
            table.setItem(
                i, 1, QTableWidgetItem(f"{profile['predicted_velocity']:.0f} fps")
            )
            table.setItem(i, 2, QTableWidgetItem(f"{profile['velocity_fps']:.0f} fps"))

            diff = profile["velocity_fps"] - profile["predicted_velocity"]
            diff_item = QTableWidgetItem(f"{diff:+.0f} fps")

            if abs(diff) < 30:
                diff_item.setBackground(QColor(200, 255, 200))
            elif abs(diff) < 60:
                diff_item.setBackground(QColor(255, 255, 200))
            else:
                diff_item.setBackground(QColor(255, 200, 200))

            table.setItem(i, 3, diff_item)

            pct = (diff / profile["predicted_velocity"]) * 100
            table.setItem(i, 4, QTableWidgetItem(f"{pct:+.1f}%"))

            total_diff += abs(diff)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Statistikk
        avg_diff = total_diff / len(self.profiles) if self.profiles else 0
        stats = QLabel(
            f"""
        <b>Statistikk:</b><br>
        Gjennomsnittlig avvik: {avg_diff:.0f} fps<br>
        Antall profiler: {len(self.profiles)}
        """
        )
        layout.addWidget(stats)

        return widget

    def create_pressure_tab(self):
        """Trykk-analyse tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <b>Trykk-analyse:</b> GRT beregner estimert maks-trykk. Sammenlign med trykkegn fra skyting.
        """
        )
        layout.addWidget(info)

        # Tabell
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(
            ["Profil", "GRT Maks Trykk", "Fylling %", "Status"]
        )
        table.setRowCount(len(self.profiles))

        for i, profile in enumerate(self.profiles):
            table.setItem(i, 0, QTableWidgetItem(profile["name"]))

            pressure = profile["max_pressure_psi"]
            pressure_item = QTableWidgetItem(f"{pressure:.0f} PSI")

            # Fargemarkering (typisk .308 Win max = 62000 PSI)
            if pressure > 62000:
                pressure_item.setBackground(QColor(255, 150, 150))
                status = "🔴 OVER SAAMI"
            elif pressure > 58000:
                pressure_item.setBackground(QColor(255, 220, 150))
                status = "🟡 Høyt (sjekk tegn)"
            else:
                pressure_item.setBackground(QColor(200, 255, 200))
                status = "🟢 Trygt område"

            table.setItem(i, 1, pressure_item)
            table.setItem(
                i, 2, QTableWidgetItem(f"{profile['case_fill_percent']:.1f}%")
            )
            table.setItem(i, 3, QTableWidgetItem(status))

        table.resizeColumnsToContents()
        layout.addWidget(table)

        warning = QLabel(
            """
        <b>⚠️ Viktig:</b> GRT-trykk er estimater. Sjekk alltid for faktiske trykkegn:
        <ul>
            <li>Tunge åpninger på tennhette</li>
            <li>Flate tennhetter</li>
            <li>Ejector marks</li>
            <li>Tunge lukkemekanisme</li>
        </ul>
        """
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "background-color: #fff3cd; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(warning)

        return widget

    def create_accuracy_tab(self):
        """Nøyaktighets-analyse tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        info = QLabel(
            """
        <b>Nøyaktighets-potensial:</b> Noen GRT-versjoner estimerer også nøyaktighet.
        Her ser du hvordan det stemmer med faktiske grupper.
        """
        )
        layout.addWidget(info)

        note = QLabel(
            """
        <i>Merk: Nøyaktighetsprediksjon er vanskelig. GRT kan gi hint, men faktisk skyting er nødvendig.</i>
        """
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()

        return widget
