"""
Precision Tracker - Statistisk analyse av presisjon over tid
Finner sammenhenger mellom væ, ammunisjon, og presisjon
"""

from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.database.database import get_database


class PrecisionTracker(QWidget):
    """Widget for presisjonssporing og analyse"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()

    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("📊 Presisjonstracker - Historisk Analyse")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(
            "Analyser sammenhenger mellom vær, ammunisjon og presisjon over tid"
        )
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Filterkontroller
        filter_layout = self.create_filters()
        layout.addLayout(filter_layout)

        # Tabs for forskjellige analyser
        tabs = QTabWidget()
        layout.addWidget(tabs)

        tabs.addTab(self.create_overview_tab(), "📈 Oversikt")
        tabs.addTab(self.create_weather_impact_tab(), "🌦️ Værpåvirkning")
        tabs.addTab(self.create_trends_tab(), "📉 Trender")
        tabs.addTab(self.create_alerts_tab(), "⚠️ Varsler & POI Shift")

    def create_filters(self):
        """Oppretter filterkontroller"""
        layout = QHBoxLayout()

        # Rifle-filter
        layout.addWidget(QLabel("Rifle:"))
        self.rifle_filter = QComboBox()
        self.rifle_filter.addItem("Alle rifles", None)
        self.load_rifles()
        self.rifle_filter.currentIndexChanged.connect(self.refresh_data)
        layout.addWidget(self.rifle_filter)

        # Ammunisjon-filter
        layout.addWidget(QLabel("Ammunisjon:"))
        self.ammo_filter = QComboBox()
        self.ammo_filter.addItem("Alle ammunisjoner", None)
        self.load_ammo_profiles()
        self.ammo_filter.currentIndexChanged.connect(self.refresh_data)
        layout.addWidget(self.ammo_filter)

        # Datofilter
        layout.addWidget(QLabel("Fra:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-6))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.refresh_data)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("Til:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.refresh_data)
        layout.addWidget(self.date_to)

        # Oppdater-knapp
        refresh_btn = QPushButton("🔄 Oppdater")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        return layout

    def create_overview_tab(self):
        """Oppretter oversikserfane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Statistikk-kort
        cards_layout = QHBoxLayout()
        layout.addLayout(cards_layout)

        self.avg_group_label = self.create_stat_card("Gj.snitt gruppe", "-- mm")
        cards_layout.addWidget(self.avg_group_label)

        self.best_group_label = self.create_stat_card("Beste gruppe", "-- mm")
        cards_layout.addWidget(self.best_group_label)

        self.worst_group_label = self.create_stat_card("Dårligste gruppe", "-- mm")
        cards_layout.addWidget(self.worst_group_label)

        self.session_count_label = self.create_stat_card("Skyteøkter", "--")
        cards_layout.addWidget(self.session_count_label)

        # Graf: Gruppestørrelse over tid
        graph_group = QGroupBox("Gruppestørrelse over tid")
        graph_layout = QVBoxLayout()
        graph_group.setLayout(graph_layout)

        self.overview_canvas = FigureCanvasQTAgg(Figure(figsize=(10, 4)))
        graph_layout.addWidget(self.overview_canvas)

        layout.addWidget(graph_group)

        # Detaljert tabell
        table_group = QGroupBox("Detaljerte data")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels(
            ["Dato", "Rifle", "Ammunisjon", "Gruppe (mm)", "MOA", "Temp °C", "Vind m/s"]
        )
        table_layout.addWidget(self.detail_table)

        layout.addWidget(table_group)

        return widget

    def create_weather_impact_tab(self):
        """Oppretter værpåvirkningsfane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Insight-kort
        insight_group = QGroupBox("🔍 Væranalyse")
        insight_layout = QVBoxLayout()
        insight_group.setLayout(insight_layout)

        self.weather_insights = QLabel("Last data for å se værets påvirkning...")
        self.weather_insights.setWordWrap(True)
        self.weather_insights.setStyleSheet("font-size: 11pt; padding: 10px;")
        insight_layout.addWidget(self.weather_insights)

        layout.addWidget(insight_group)

        # Grafer
        graphs_layout = QHBoxLayout()
        layout.addLayout(graphs_layout)

        # Temperatur vs presisjon
        temp_group = QGroupBox("Temperatur vs Gruppestørrelse")
        temp_layout = QVBoxLayout()
        temp_group.setLayout(temp_layout)

        self.temp_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 4)))
        temp_layout.addWidget(self.temp_canvas)

        graphs_layout.addWidget(temp_group)

        # Vind vs presisjon
        wind_group = QGroupBox("Vind vs Gruppestørrelse")
        wind_layout = QVBoxLayout()
        wind_group.setLayout(wind_layout)

        self.wind_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 4)))
        wind_layout.addWidget(self.wind_canvas)

        graphs_layout.addWidget(wind_group)

        return widget

    def create_trends_tab(self):
        """Oppretter trendfane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Trend-insights
        trend_group = QGroupBox("📈 Trend-analyse")
        trend_layout = QVBoxLayout()
        trend_group.setLayout(trend_layout)

        self.trend_insights = QLabel("Last data for å se trender...")
        self.trend_insights.setWordWrap(True)
        self.trend_insights.setStyleSheet("font-size: 11pt; padding: 10px;")
        trend_layout.addWidget(self.trend_insights)

        layout.addWidget(trend_group)

        # Trendgraf
        graph_group = QGroupBox("Presisjon-trend (glidende gjennomsnitt)")
        graph_layout = QVBoxLayout()
        graph_group.setLayout(graph_layout)

        self.trend_canvas = FigureCanvasQTAgg(Figure(figsize=(10, 5)))
        graph_layout.addWidget(self.trend_canvas)

        layout.addWidget(graph_group)

        return widget

    def create_alerts_tab(self):
        """Oppretter varsler-fane"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(
            """
        <h3>POI Shift Detection</h3>
        <p>Systemet varsler automatisk hvis det detekteres:</p>
        <ul>
            <li><b>Plutselig forverring</b>: Gruppestørrelse øker med >30% fra forrige økt</li>
            <li><b>Gradvis trend</b>: Presisjon forverres over 5+ økter</li>
            <li><b>Væranomalier</b>: Uvanlig oppførsel ved spesifikke værforhold</li>
        </ul>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Varsler-tabell
        alerts_group = QGroupBox("🚨 Aktive varsler")
        alerts_layout = QVBoxLayout()
        alerts_group.setLayout(alerts_layout)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels(
            ["Alvorlighet", "Type", "Rifle/Ammo", "Beskrivelse"]
        )
        alerts_layout.addWidget(self.alerts_table)

        layout.addWidget(alerts_group)

        layout.addStretch()

        return widget

    def create_stat_card(self, title, value):
        """Oppretter statistikk-kort"""
        card = QGroupBox()
        card.setMinimumHeight(80)
        card.setStyleSheet(
            """
            QGroupBox {
                background-color: #f0f0f0;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )

        card_layout = QVBoxLayout()
        card.setLayout(card_layout)

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)

        # Lagre referanse til value_label for oppdatering
        card.value_label = value_label

        return card

    def load_rifles(self):
        """Laster rifles til filter"""
        rifles = self.db.execute_query("SELECT id, name FROM rifles ORDER BY name")
        for rifle_id, name in rifles:
            self.rifle_filter.addItem(name, rifle_id)

    def load_ammo_profiles(self):
        """Laster ammunisjonsprofiler til filter"""
        ammos = self.db.execute_query(
            "SELECT id, name FROM ammo_profiles ORDER BY name"
        )
        for ammo_id, name in ammos:
            self.ammo_filter.addItem(name, ammo_id)

    def refresh_data(self):
        """Oppdaterer alle data og grafer"""
        # Hent filtrerte data
        data = self.get_shooting_data()

        if len(data) == 0:
            return

        # Oppdater statistikk-kort
        self.update_stats_cards(data)

        # Oppdater oversikts-graf
        self.update_overview_graph(data)

        # Oppdater detaljert tabell
        self.update_detail_table(data)

        # Oppdater væranalyse
        self.update_weather_analysis(data)

        # Oppdater trend-analyse
        self.update_trend_analysis(data)

        # Oppdater varsler
        self.update_alerts(data)

    def get_shooting_data(self):
        """Henter skytedata basert på filtre"""
        rifle_id = self.rifle_filter.currentData()
        ammo_id = self.ammo_filter.currentData()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        query = """
            SELECT
                ss.date,
                r.name as rifle_name,
                ap.name as ammo_name,
                ss.best_group_mm,
                ss.avg_group_mm,
                ss.temperature,
                ss.wind_speed,
                ss.humidity,
                ss.distance_meters
            FROM shooting_sessions ss
            LEFT JOIN rifles r ON ss.rifle_id = r.id
            LEFT JOIN ammo_profiles ap ON ss.ammo_profile_id = ap.id
            WHERE ss.date BETWEEN ? AND ?
        """

        params = [date_from, date_to]

        if rifle_id is not None:
            query += " AND ss.rifle_id = ?"
            params.append(rifle_id)

        if ammo_id is not None:
            query += " AND ss.ammo_profile_id = ?"
            params.append(ammo_id)

        query += " ORDER BY ss.date"

        return self.db.execute_query(query, tuple(params))

    def update_stats_cards(self, data):
        """Oppdaterer statistikk-kort"""
        if not data:
            return

        # Ekstraher gruppestørrelser (bruker best_group_mm)
        groups = [row[3] for row in data if row[3] is not None]

        if groups:
            avg_group = sum(groups) / len(groups)
            best_group = min(groups)
            worst_group = max(groups)

            self.avg_group_label.value_label.setText(f"{avg_group:.1f} mm")
            self.best_group_label.value_label.setText(f"{best_group:.1f} mm")
            self.worst_group_label.value_label.setText(f"{worst_group:.1f} mm")

        self.session_count_label.value_label.setText(str(len(data)))

    def update_overview_graph(self, data):
        """Oppdaterer oversiktsgraf"""
        if not data:
            return

        dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in data]
        groups = [row[3] if row[3] is not None else 0 for row in data]

        fig = self.overview_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        ax.plot(dates, groups, "o-", linewidth=2, markersize=6)
        ax.set_xlabel("Dato")
        ax.set_ylabel("Gruppestørrelse (mm)")
        ax.set_title("Presisjon over tid")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        self.overview_canvas.draw()

    def update_detail_table(self, data):
        """Oppdaterer detaljert tabell"""
        self.detail_table.setRowCount(len(data))

        for i, row in enumerate(data):
            date, rifle, ammo, best_group, avg_group, temp, wind, humidity, distance = (
                row
            )

            # Beregn MOA
            moa = "N/A"
            if best_group and distance:
                moa_val = (best_group / 10) / (distance / 100) / 2.908
                moa = f"{moa_val:.2f}"

            self.detail_table.setItem(i, 0, QTableWidgetItem(date))
            self.detail_table.setItem(i, 1, QTableWidgetItem(rifle or "N/A"))
            self.detail_table.setItem(i, 2, QTableWidgetItem(ammo or "N/A"))
            self.detail_table.setItem(
                i, 3, QTableWidgetItem(f"{best_group:.1f}" if best_group else "N/A")
            )
            self.detail_table.setItem(i, 4, QTableWidgetItem(moa))
            self.detail_table.setItem(
                i, 5, QTableWidgetItem(f"{temp:.0f}" if temp else "N/A")
            )
            self.detail_table.setItem(
                i, 6, QTableWidgetItem(f"{wind:.1f}" if wind else "N/A")
            )

    def update_weather_analysis(self, data):
        """Oppdaterer væranalyse"""
        # Filtrer ut data med temperatur og vind
        temp_data = [
            (row[5], row[3])
            for row in data
            if row[5] is not None and row[3] is not None
        ]
        wind_data = [
            (row[6], row[3])
            for row in data
            if row[6] is not None and row[3] is not None
        ]

        if temp_data:
            # Finn beste temperaturområde
            temp_ranges = [
                ((-10, 0), "Under 0°C"),
                ((0, 10), "0-10°C"),
                ((10, 20), "10-20°C"),
                ((20, 30), "Over 20°C"),
            ]

            best_range = None
            best_avg = float("inf")

            for (min_t, max_t), label in temp_ranges:
                groups_in_range = [g for t, g in temp_data if min_t <= t < max_t]
                if groups_in_range:
                    avg = sum(groups_in_range) / len(groups_in_range)
                    if avg < best_avg:
                        best_avg = avg
                        best_range = label

            insight_text = f"""
<h3>🌡️ Temperatur-analyse</h3>
<p><b>Din rifle skyter best ved:</b> {best_range}<br>
Gjennomsnittlig gruppe: {best_avg:.1f} mm</p>
            """

            # Tegn temperatur-graf
            temps = [t for t, g in temp_data]
            groups = [g for t, g in temp_data]

            fig = self.temp_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            ax.scatter(temps, groups)
            ax.set_xlabel("Temperatur (°C)")
            ax.set_ylabel("Gruppe (mm)")
            ax.set_title("Temperatur vs Presisjon")
            ax.grid(True, alpha=0.3)
            self.temp_canvas.draw()

            self.weather_insights.setHtml(insight_text)

        if wind_data:
            # Tegn vind-graf
            winds = [w for w, g in wind_data]
            groups = [g for w, g in wind_data]

            fig = self.wind_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            ax.scatter(winds, groups)
            ax.set_xlabel("Vind (m/s)")
            ax.set_ylabel("Gruppe (mm)")
            ax.set_title("Vind vs Presisjon")
            ax.grid(True, alpha=0.3)
            self.wind_canvas.draw()

    def update_trend_analysis(self, data):
        """Oppdaterer trend-analyse"""
        if len(data) < 3:
            return

        groups = [row[3] for row in data if row[3] is not None]

        if len(groups) < 3:
            return

        # Beregn glidende gjennomsnitt
        window = min(5, len(groups))
        moving_avg = []
        for i in range(len(groups) - window + 1):
            avg = sum(groups[i : i + window]) / window
            moving_avg.append(avg)

        # Beregn trend (forbedring eller forverring)
        if len(moving_avg) >= 2:
            start_avg = (
                sum(moving_avg[:3]) / 3 if len(moving_avg) >= 3 else moving_avg[0]
            )
            end_avg = (
                sum(moving_avg[-3:]) / 3 if len(moving_avg) >= 3 else moving_avg[-1]
            )

            change_pct = ((end_avg - start_avg) / start_avg) * 100

            if change_pct < -10:
                trend_text = f"<span style='color: green;'>✅ Presisjon forbedres! ({abs(change_pct):.1f}% bedre)</span>"
            elif change_pct > 10:
                trend_text = f"<span style='color: red;'>⚠️ Presisjon forverres ({change_pct:.1f}% dårligere)</span>"
            else:
                trend_text = "<span style='color: blue;'>➡️ Stabil presisjon</span>"

            insight = f"""
<h3>📈 Trend-analyse</h3>
<p>{trend_text}</p>
<p>Første økter: {start_avg:.1f} mm gjennomsnitt<br>
Siste økter: {end_avg:.1f} mm gjennomsnitt</p>
            """

            self.trend_insights.setHtml(insight)

        # Tegn trend-graf
        dates = [
            datetime.strptime(row[0], "%Y-%m-%d") for row in data if row[3] is not None
        ]

        fig = self.trend_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        ax.plot(dates, groups, "o", alpha=0.5, label="Faktisk")

        if len(moving_avg) > 0:
            ma_dates = dates[window - 1 :]
            ax.plot(
                ma_dates,
                moving_avg,
                "r-",
                linewidth=2,
                label=f"{window}-økters gj.snitt",
            )

        ax.set_xlabel("Dato")
        ax.set_ylabel("Gruppe (mm)")
        ax.set_title("Presisjon-trend")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        self.trend_canvas.draw()

    def update_alerts(self, data):
        """Oppdaterer varsler"""
        if len(data) < 2:
            return

        alerts = []

        # Sjekk for plutselig forverring
        recent_groups = [row[3] for row in data[-3:] if row[3] is not None]
        previous_groups = [row[3] for row in data[-6:-3] if row[3] is not None]

        if recent_groups and previous_groups:
            recent_avg = sum(recent_groups) / len(recent_groups)
            previous_avg = sum(previous_groups) / len(previous_groups)

            change_pct = ((recent_avg - previous_avg) / previous_avg) * 100

            if change_pct > 30:
                alerts.append(
                    (
                        "🔴 HØY",
                        "Plutselig forverring",
                        data[-1][1] or "N/A",
                        f"Gruppe økt {change_pct:.0f}% siste 3 økter. Sjekk rifle/optikk!",
                    )
                )

        # Oppdater tabell
        self.alerts_table.setRowCount(len(alerts))

        for i, (severity, alert_type, rifle_ammo, description) in enumerate(alerts):
            self.alerts_table.setItem(i, 0, QTableWidgetItem(severity))
            self.alerts_table.setItem(i, 1, QTableWidgetItem(alert_type))
            self.alerts_table.setItem(i, 2, QTableWidgetItem(rifle_ammo))
            self.alerts_table.setItem(i, 3, QTableWidgetItem(description))

            # Fargelegg alvorlighet
            color = (
                QColor(255, 200, 200) if "HØY" in severity else QColor(255, 255, 200)
            )
            for col in range(4):
                self.alerts_table.item(i, col).setBackground(color)
