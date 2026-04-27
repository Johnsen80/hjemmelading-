"""
Cold Bore Shot Logger & Barrel Condition Tracker
Tracks the first shot from a cold rifle and barrel condition over time
"""

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..database.database import get_database


class RiflePerformanceTracker(QWidget):
    """Widget for cold-bore logging and barrel tracking."""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QLabel("Rifle Performance Tracker")
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        subtitle = QLabel("Cold Bore Shot Logger & Barrel Condition Tracker")
        subtitle.setProperty("variant", "cardSubtitle")
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Cold Bore Logger
        tabs.addTab(self.create_cold_bore_tab(), "Cold Bore")

        # Tab 2: Barrel Tracker
        tabs.addTab(self.create_barrel_tracker_tab(), "Barrel Tracker")

        # Tab 3: Analysis
        tabs.addTab(self.create_analysis_tab(), "Analysis")

    def create_cold_bore_tab(self):
        """Create the cold-bore logging tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(
            "Cold Bore Shot Logger:\n"
            "The first shot from a cold rifle often lands differently than follow-up shots.\n"
            "Log cold-bore POI systematically to understand the rifle's behavior."
        )
        info.setWordWrap(True)
        info.setProperty("role", "muted")
        layout.addWidget(info)

        # Input section
        input_group = QGroupBox("New Cold-Bore Entry")
        input_group.setProperty("variant", "panel")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        # Rifle
        self.cb_rifle = QComboBox()
        self.cb_rifle.addItem("Select firearm...", None)
        self.load_rifles(self.cb_rifle)
        input_layout.addRow("Rifle:", self.cb_rifle)

        # Ammunition
        self.cb_ammo = QComboBox()
        self.cb_ammo.addItem("Select ammunition...", None)
        self.load_ammo_profiles(self.cb_ammo)
        input_layout.addRow("Ammunition:", self.cb_ammo)

        # Distance
        self.cb_distance = QSpinBox()
        self.cb_distance.setRange(50, 1000)
        self.cb_distance.setValue(100)
        self.cb_distance.setSuffix(" m")
        input_layout.addRow("Distance:", self.cb_distance)

        # Temperature
        self.cb_temp = QDoubleSpinBox()
        self.cb_temp.setRange(-30, 50)
        self.cb_temp.setValue(15)
        self.cb_temp.setSuffix(" °C")
        input_layout.addRow("Temperature:", self.cb_temp)

        # Time since the last shot
        self.cb_time_since = QSpinBox()
        self.cb_time_since.setRange(1, 24)
        self.cb_time_since.setValue(12)
        self.cb_time_since.setSuffix(" hours")
        input_layout.addRow("Time Since Last Shot:", self.cb_time_since)

        # POI shift (Point of Impact)
        poi_group = QGroupBox("Cold Bore POI Shift")
        poi_group.setProperty("variant", "panel")
        poi_layout = QFormLayout()
        poi_group.setLayout(poi_layout)

        self.cb_poi_h = QDoubleSpinBox()
        self.cb_poi_h.setRange(-50, 50)
        self.cb_poi_h.setValue(0)
        self.cb_poi_h.setSuffix(" cm")
        self.cb_poi_h.setDecimals(1)
        poi_layout.addRow("Horizontal shift (+ = right):", self.cb_poi_h)

        self.cb_poi_v = QDoubleSpinBox()
        self.cb_poi_v.setRange(-50, 50)
        self.cb_poi_v.setValue(0)
        self.cb_poi_v.setSuffix(" cm")
        self.cb_poi_v.setDecimals(1)
        poi_layout.addRow("Vertical shift (+ = up):", self.cb_poi_v)

        # Quick buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick:"))

        for label, h, v in [
            ("On Zero", 0, 0),
            ("1 cm right", 1, 0),
            ("2 cm up", 0, 2),
            ("1 cm diag", 1, 1),
        ]:
            btn = QPushButton(label)
            btn.setProperty("variant", "ghost")
            btn.clicked.connect(
                lambda checked, x=h, y=v: (
                    self.cb_poi_h.setValue(x),
                    self.cb_poi_v.setValue(y),
                )
            )
            quick_layout.addWidget(btn)

        quick_layout.addStretch()
        poi_layout.addRow(quick_layout)

        input_layout.addRow(poi_group)

        # Notes
        self.cb_notes = QTextEdit()
        self.cb_notes.setMaximumHeight(80)
        self.cb_notes.setPlaceholderText(
            "e.g. Oiled barrel, cold weather, the rifle was left outside overnight..."
        )
        input_layout.addRow("Notes:", self.cb_notes)

        layout.addWidget(input_group)

        # Save button
        save_cb_btn = QPushButton("Save Cold Bore Shot")
        save_cb_btn.setProperty("variant", "primary")
        save_cb_btn.setProperty("size", "lg")
        save_cb_btn.clicked.connect(self.save_cold_bore)
        layout.addWidget(save_cb_btn)

        # History
        history_label = QLabel("Cold-Bore History")
        history_label.setProperty("variant", "cardTitle")
        layout.addWidget(history_label)

        self.cb_history_table = QTableWidget()
        self.cb_history_table.setColumnCount(8)
        self.cb_history_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Rifle",
                "Ammo",
                "Distance",
                "Temp",
                "POI H (cm)",
                "POI V (cm)",
                "Notes",
            ]
        )
        layout.addWidget(self.cb_history_table)

        # Refresh button
        refresh_cb_btn = QPushButton("Refresh History")
        refresh_cb_btn.setProperty("variant", "ghost")
        refresh_cb_btn.clicked.connect(self.load_cold_bore_history)
        layout.addWidget(refresh_cb_btn)

        # Load initial data
        self.load_cold_bore_history()

        return widget

    def create_barrel_tracker_tab(self):
        """Create the barrel tracker tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(
            "Barrel Condition Tracker:\n"
            "Track how many shots have gone through the barrel and how precision changes over time.\n"
            "Identify when it is time for cleaning or a new barrel."
        )
        info.setWordWrap(True)
        info.setProperty("role", "muted")
        layout.addWidget(info)

        # Rifle selector
        rifle_layout = QHBoxLayout()
        rifle_layout.addWidget(QLabel("Rifle:"))

        self.bt_rifle = QComboBox()
        self.bt_rifle.addItem("Select firearm...", None)
        self.load_rifles(self.bt_rifle)
        self.bt_rifle.currentIndexChanged.connect(self.load_barrel_status)
        rifle_layout.addWidget(self.bt_rifle, 1)

        layout.addLayout(rifle_layout)

        # Status cards
        status_layout = QHBoxLayout()

        self.bt_total_rounds = self.create_info_card("Total Shots", "0")
        status_layout.addWidget(self.bt_total_rounds)

        self.bt_last_cleaning = self.create_info_card("Since Last Cleaning", "0")
        status_layout.addWidget(self.bt_last_cleaning)

        self.bt_avg_group = self.create_info_card("Average Group Size", "N/A")
        status_layout.addWidget(self.bt_avg_group)

        self.bt_condition = self.create_info_card("Barrel Condition", "Unknown")
        status_layout.addWidget(self.bt_condition)

        layout.addLayout(status_layout)

        # Add rounds
        add_group = QGroupBox("Add Shots")
        add_group.setProperty("variant", "panel")
        add_layout = QFormLayout()
        add_group.setLayout(add_layout)

        self.bt_add_rounds = QSpinBox()
        self.bt_add_rounds.setRange(1, 500)
        self.bt_add_rounds.setValue(20)
        self.bt_add_rounds.setSuffix(" shots")
        add_layout.addRow("Count:", self.bt_add_rounds)

        self.bt_group_size = QDoubleSpinBox()
        self.bt_group_size.setRange(0, 10)
        self.bt_group_size.setValue(0.5)
        self.bt_group_size.setSuffix(" MOA")
        self.bt_group_size.setDecimals(2)
        add_layout.addRow("Group size (optional):", self.bt_group_size)

        add_btn_layout = QHBoxLayout()

        add_rounds_btn = QPushButton("Add shots")
        add_rounds_btn.setProperty("variant", "primary")
        add_rounds_btn.clicked.connect(self.add_barrel_rounds)
        add_btn_layout.addWidget(add_rounds_btn)

        cleaning_btn = QPushButton("Cleaning completed")
        cleaning_btn.setProperty("variant", "secondary")
        cleaning_btn.clicked.connect(self.mark_barrel_cleaning)
        add_btn_layout.addWidget(cleaning_btn)

        add_layout.addRow(add_btn_layout)

        layout.addWidget(add_group)

        # Graf placeholder
        self.bt_chart_label = QLabel("Select a firearm to view precision vs shot count")
        self.bt_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bt_chart_label.setProperty("role", "muted")
        self.bt_chart_label.setProperty("emphasis", "placeholder")
        layout.addWidget(self.bt_chart_label)

        # Matplotlib canvas (opprettes når data er tilgjengelig)
        self.bt_canvas = None

        return widget

    def create_analysis_tab(self):
        """Oppretter analyse-tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        title = QLabel("Rifle Performance Analysis")
        title.setProperty("variant", "cardTitle")
        layout.addWidget(title)

        info = QLabel(
            "Compare cold-bore shift and barrel condition to optimize maintenance."
        )
        info.setWordWrap(True)
        info.setProperty("variant", "cardSubtitle")
        layout.addWidget(info)

        # Rifle selector
        rifle_layout = QHBoxLayout()
        rifle_layout.addWidget(QLabel("Rifle:"))

        self.an_rifle = QComboBox()
        self.an_rifle.addItem("Select firearm...", None)
        self.load_rifles(self.an_rifle)
        rifle_layout.addWidget(self.an_rifle, 1)

        analyze_btn = QPushButton("Run Analysis")
        analyze_btn.setProperty("variant", "primary")
        analyze_btn.clicked.connect(self.run_analysis)
        rifle_layout.addWidget(analyze_btn)

        layout.addLayout(rifle_layout)

        # Resultat
        self.an_result = QTextEdit()
        self.an_result.setReadOnly(True)
        layout.addWidget(self.an_result)

        return widget

    def create_info_card(self, title, value):
        """Oppretter info-kort"""
        card = QFrame()
        card.setProperty("variant", "statCard")
        card.setMinimumHeight(100)

        layout = QVBoxLayout()
        card.setLayout(layout)

        value_label = QLabel(value)
        value_label.setProperty("variant", "statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setProperty("variant", "statTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        return card

    def load_rifles(self, combo_widget):
        """Laster rifles"""
        rifles = self.db.execute_query(
            "SELECT id, name, caliber FROM rifles ORDER BY name"
        )

        for row in rifles:
            rifle_id, name, caliber = row
            combo_widget.addItem(f"{name} ({caliber})", rifle_id)

    def load_ammo_profiles(self, combo_widget):
        """Laster ammunisjonsprofiler"""
        ammos = self.db.execute_query(
            "SELECT id, name, caliber FROM ammo_profiles ORDER BY name"
        )

        for row in ammos:
            ammo_id, name, caliber = row
            combo_widget.addItem(f"{name} ({caliber})", ammo_id)

    def save_cold_bore(self):
        """Lagrer cold bore shot"""
        rifle_id = self.cb_rifle.currentData()
        ammo_id = self.cb_ammo.currentData()

        if not rifle_id or not ammo_id:
            QMessageBox.warning(
                self, "Missing Data", "Select a firearm and ammunition!"
            )
            return

        try:
            self.db.execute_query(
                """
                INSERT INTO cold_bore_shots
                (rifle_id, ammo_profile_id, distance_m, temperature_c,
                 time_since_last_shot_hrs, poi_horizontal_cm, poi_vertical_cm, notes, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    rifle_id,
                    ammo_id,
                    self.cb_distance.value(),
                    self.cb_temp.value(),
                    self.cb_time_since.value(),
                    self.cb_poi_h.value(),
                    self.cb_poi_v.value(),
                    self.cb_notes.toPlainText(),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            QMessageBox.information(
                self,
                "Saved!",
                f"Cold-bore shot saved!\n\nPOI shift: {self.cb_poi_h.value():.1f} cm H, {self.cb_poi_v.value():.1f} cm V",
            )

            # Reset
            self.cb_poi_h.setValue(0)
            self.cb_poi_v.setValue(0)
            self.cb_notes.clear()

            # Refresh history
            self.load_cold_bore_history()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def load_cold_bore_history(self):
        """Laster cold bore historikk"""
        try:
            data = self.db.execute_query(
                """
                SELECT cb.date, r.name, ap.name, cb.distance_m, cb.temperature_c,
                       cb.poi_horizontal_cm, cb.poi_vertical_cm, cb.notes
                FROM cold_bore_shots cb
                LEFT JOIN rifles r ON cb.rifle_id = r.id
                LEFT JOIN ammo_profiles ap ON cb.ammo_profile_id = ap.id
                ORDER BY cb.date DESC
                LIMIT 50
            """
            )

            self.cb_history_table.setRowCount(len(data))

            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.cb_history_table.setItem(row_idx, col_idx, item)

            self.cb_history_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error loading cold bore history: {e}")

    def load_barrel_status(self):
        """Laster barrel status"""
        rifle_id = self.bt_rifle.currentData()

        if not rifle_id:
            return

        try:
            # Get total rounds
            total = self.db.execute_query(
                """
                SELECT COALESCE(SUM(rounds_fired), 0)
                FROM barrel_log
                WHERE rifle_id = ?
            """,
                (rifle_id,),
            )

            total_rounds = total[0][0] if total and len(total) > 0 else 0

            # Get rounds since last cleaning
            last_clean = self.db.execute_query(
                """
                SELECT COALESCE(SUM(rounds_fired), 0)
                FROM barrel_log
                WHERE rifle_id = ? AND date > (
                    SELECT COALESCE(MAX(date), '1900-01-01')
                    FROM barrel_log
                    WHERE rifle_id = ? AND event_type = 'CLEANING'
                )
            """,
                (rifle_id, rifle_id),
            )

            since_cleaning = (
                last_clean[0][0] if last_clean and len(last_clean) > 0 else total_rounds
            )

            # Get average group size
            avg_group = self.db.execute_query(
                """
                SELECT AVG(group_size_moa)
                FROM barrel_log
                WHERE rifle_id = ? AND group_size_moa IS NOT NULL
            """,
                (rifle_id,),
            )

            avg = (
                avg_group[0][0]
                if avg_group and len(avg_group) > 0 and avg_group[0][0]
                else None
            )

            # Update cards
            self.bt_total_rounds.findChild(QLabel, "value").setText(str(total_rounds))
            self.bt_last_cleaning.findChild(QLabel, "value").setText(
                str(since_cleaning)
            )

            if avg:
                self.bt_avg_group.findChild(QLabel, "value").setText(f"{avg:.2f} MOA")
            else:
                self.bt_avg_group.findChild(QLabel, "value").setText("N/A")

            # Determine condition
            if total_rounds < 200:
                condition = "New"
            elif total_rounds < 1000:
                condition = "Good"
            elif total_rounds < 2500:
                condition = "OK"
            elif total_rounds < 5000:
                condition = "Worn"
            else:
                condition = "Critical"

            self.bt_condition.findChild(QLabel, "value").setText(condition)

        except Exception as e:
            print(f"Error loading barrel status: {e}")

    def add_barrel_rounds(self):
        """Legger til skudd i barrel log"""
        rifle_id = self.bt_rifle.currentData()

        if not rifle_id:
            QMessageBox.warning(self, "No Firearm", "Select a firearm first!")
            return

        rounds = self.bt_add_rounds.value()
        group_size = (
            self.bt_group_size.value() if self.bt_group_size.value() > 0 else None
        )

        try:
            self.db.execute_query(
                """
                INSERT INTO barrel_log
                (rifle_id, rounds_fired, group_size_moa, event_type, date)
                VALUES (?, ?, ?, 'SHOOTING', ?)
            """,
                (
                    rifle_id,
                    rounds,
                    group_size,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            QMessageBox.information(
                self, "Saved!", f"{rounds} shots added to the barrel log!"
            )

            # Refresh status
            self.load_barrel_status()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def mark_barrel_cleaning(self):
        """Markerer barrel cleaning"""
        rifle_id = self.bt_rifle.currentData()

        if not rifle_id:
            QMessageBox.warning(self, "No Firearm", "Select a firearm first!")
            return

        try:
            self.db.execute_query(
                """
                INSERT INTO barrel_log
                (rifle_id, rounds_fired, event_type, date)
                VALUES (?, 0, 'CLEANING', ?)
            """,
                (rifle_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )

            QMessageBox.information(
                self,
                "Saved!",
                "Barrel cleaning registered!\n\nRound counter since the last cleaning has been reset.",
            )

            # Refresh status
            self.load_barrel_status()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def run_analysis(self):
        """Kjører analyse"""
        rifle_id = self.an_rifle.currentData()

        if not rifle_id:
            QMessageBox.warning(self, "No Firearm", "Select a firearm first!")
            return

        try:
            # Get rifle name
            rifle_data = self.db.execute_query(
                "SELECT name, caliber FROM rifles WHERE id = ?", (rifle_id,)
            )

            if not rifle_data:
                return

            rifle_name, caliber = rifle_data[0]

            # Cold bore analysis
            cb_data = self.db.execute_query(
                """
                SELECT AVG(poi_horizontal_cm), AVG(poi_vertical_cm),
                       AVG(temperature_c), COUNT(*)
                FROM cold_bore_shots
                WHERE rifle_id = ?
            """,
                (rifle_id,),
            )

            if cb_data and cb_data[0][3] > 0:
                avg_h, avg_v, avg_temp, count = cb_data[0]
                cb_text = f"""
<h3>Cold Bore Analysis</h3>
<p><b>{count} cold-bore shots logged</b></p>
<ul>
<li>Average POI shift: <b>{avg_h:.1f} cm right, {avg_v:.1f} cm up</b></li>
<li>Average temperature: <b>{avg_temp:.1f}°C</b></li>
</ul>

<p><b>Recommendation:</b></p>
"""
                if abs(avg_h) < 1 and abs(avg_v) < 1:
                    cb_text += "<p>Meget god cold bore performance. Minimal shift.</p>"
                elif abs(avg_h) < 2 and abs(avg_v) < 2:
                    cb_text += "<p>Moderate cold-bore shift. Hold {:.1f} cm left and {:.1f} cm low for the first shot.</p>".format(
                        -avg_h, -avg_v
                    )
                else:
                    cb_text += "<p>Significant cold-bore shift. Consider firing a fouler before hunting.</p>"
            else:
                cb_text = "<p><i>No cold-bore data for this firearm</i></p>"

            # Barrel condition analysis
            barrel_data = self.db.execute_query(
                """
                SELECT SUM(rounds_fired), AVG(group_size_moa)
                FROM barrel_log
                WHERE rifle_id = ? AND event_type = 'SHOOTING'
            """,
                (rifle_id,),
            )

            if barrel_data and barrel_data[0][0]:
                total_rounds, avg_group = barrel_data[0]

                barrel_text = f"""
<h3>Barrel Condition</h3>
<p><b>Total shots: {total_rounds}</b></p>
"""
                if avg_group:
                    barrel_text += (
                        f"<p>Average group size: <b>{avg_group:.2f} MOA</b></p>"
                    )

                barrel_text += "<p><b>Status:</b></p>"

                if total_rounds < 200:
                    barrel_text += (
                        "<p>The barrel is still new. Keep up regular cleaning.</p>"
                    )
                elif total_rounds < 1000:
                    barrel_text += "<p>The barrel is in good condition. Clean every 100-200 shots.</p>"
                elif total_rounds < 2500:
                    barrel_text += "<p>The barrel is starting to wear. Monitor precision closely.</p>"
                elif total_rounds < 5000:
                    barrel_text += "<p>The barrel is significantly worn. Consider a new barrel soon.</p>"
                else:
                    barrel_text += "<p>The barrel is past its service life. A new barrel is strongly recommended.</p>"
            else:
                barrel_text = "<p><i>No barrel-log data for this firearm</i></p>"

            # Combine results
            result_html = f"""
<h2>Rifle Performance Report</h2>
<h3>{rifle_name} ({caliber})</h3>
<p><i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i></p>
<hr>

{cb_text}

<hr>

{barrel_text}

<hr>

<h3>General Recommendations</h3>
<ul>
<li>Log cold-bore shots before each hunting season</li>
<li>Clean the barrel every 100-200 shots for best precision</li>
<li>Track group size to identify precision degradation early</li>
<li>Consider a new barrel at >3000-5000 shots, depending on caliber</li>
</ul>
            """

            self.an_result.setHtml(result_html)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
