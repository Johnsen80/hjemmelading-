"""
Precision Tracker - Statistisk analyse av presisjon over tid
Finner sammenhenger mellom væ, ammunisjon, og presisjon
"""

from datetime import datetime

from PyQt6.QtCore import QDate, QSettings, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
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

from ..database.database import get_database
from ..ui.reloading_theme import ReloadingTheme
from ..utils.optional_deps import Figure as Figure
from ..utils.optional_deps import FigureCanvas as FigureCanvas
from ..utils.unit_preferences import format_temperature_c as format_temperature_c_pref


def _format_group_mm(value: object) -> str:
    try:
        group_mm = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "N/A"
    if _get_global_unit_system() == "imperial":
        return f"{group_mm / 25.4:.2f} in ({group_mm:.1f} mm)"
    return f"{group_mm:.1f} mm"


def _format_temperature_c(value: object) -> str:
    return format_temperature_c_pref(value)


def _get_global_unit_system() -> str:
    settings = QSettings("ReloadingWorkshop", "ReloadingManager")
    return str(settings.value("units/global", "metric") or "metric").strip().lower()


def _format_wind_mps(value: object) -> str:
    try:
        wind_mps = float(value)
    except Exception:
        return str(value) if value not in (None, "") else "N/A"
    if _get_global_unit_system() == "imperial":
        return f"{wind_mps * 2.23694:.1f} mph ({wind_mps:.1f} m/s)"
    return f"{wind_mps:.1f} m/s"


def _group_unit_label() -> str:
    return "in" if _get_global_unit_system() == "imperial" else "mm"


def _temperature_axis_label() -> str:
    return (
        "Temperature (°F)"
        if _get_global_unit_system() == "imperial"
        else "Temperature (°C)"
    )


def _wind_axis_label() -> str:
    return "Wind (mph)" if _get_global_unit_system() == "imperial" else "Wind (m/s)"


class PrecisionTracker(QWidget):
    """Widget for presisjonssporing og analyse"""

    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tittel
        title = QLabel("Precision Tracker - Historical Analysis")
        title.setProperty("role", "title")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel(
            "Analyze relationships between weather, ammunition, and precision over time"
        )
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Filterkontroller
        filter_layout = self.create_filters()
        layout.addLayout(filter_layout)

        # Tabs for forskjellige analyser
        tabs = QTabWidget()
        layout.addWidget(tabs)

        tabs.addTab(self.create_overview_tab(), "Overview")
        tabs.addTab(self.create_weather_impact_tab(), "Weather Impact")
        tabs.addTab(self.create_trends_tab(), "Trends")
        tabs.addTab(self.create_alerts_tab(), "Alerts and POI Shift")

    def create_filters(self):
        """Create filter controls."""
        layout = QHBoxLayout()

        # Rifle-filter
        layout.addWidget(QLabel("Rifle:"))
        self.rifle_filter = QComboBox()
        self.rifle_filter.addItem("All Rifles", None)
        self.load_rifles()
        self.rifle_filter.currentIndexChanged.connect(self.refresh_data)
        layout.addWidget(self.rifle_filter)

        # Ammunisjon-filter
        layout.addWidget(QLabel("Ammunition:"))
        self.ammo_filter = QComboBox()
        self.ammo_filter.addItem("All Ammunition", None)
        self.load_ammo_profiles()
        self.ammo_filter.currentIndexChanged.connect(self.refresh_data)
        layout.addWidget(self.ammo_filter)

        # Datofilter
        layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-6))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.refresh_data)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.refresh_data)
        layout.addWidget(self.date_to)

        # Oppdater-knapp
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setProperty("variant", "secondary")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        return layout

    def create_overview_tab(self):
        """Create the overview tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Statistikk-kort
        cards_layout = QHBoxLayout()
        layout.addLayout(cards_layout)

        self.avg_group_label = self.create_stat_card(
            "Average Group", "-- mm", ReloadingTheme.ACCENT
        )
        cards_layout.addWidget(self.avg_group_label)

        self.best_group_label = self.create_stat_card(
            "Best Group", "-- mm", ReloadingTheme.SUCCESS
        )
        cards_layout.addWidget(self.best_group_label)

        self.worst_group_label = self.create_stat_card(
            "Worst Group", "-- mm", ReloadingTheme.WARNING
        )
        cards_layout.addWidget(self.worst_group_label)

        self.session_count_label = self.create_stat_card(
            "Shooting Sessions", "--", ReloadingTheme.INFO
        )
        cards_layout.addWidget(self.session_count_label)

        # Graf: Gruppestørrelse over tid
        graph_group = QGroupBox("Group Size Over Time")
        graph_group.setProperty("variant", "panel")
        graph_layout = QVBoxLayout()
        graph_group.setLayout(graph_layout)

        self.overview_canvas = FigureCanvas(Figure(figsize=(10, 4)))
        graph_layout.addWidget(self.overview_canvas)

        layout.addWidget(graph_group)

        # Detaljert tabell
        table_group = QGroupBox("Detailed Data")
        table_group.setProperty("variant", "panel")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Rifle",
                "Ammunition",
                f"Group ({_group_unit_label()})",
                "MOA",
                _temperature_axis_label(),
                _wind_axis_label(),
            ]
        )
        table_layout.addWidget(self.detail_table)

        layout.addWidget(table_group)

        return widget

    def create_weather_impact_tab(self):
        """Create the weather impact tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Insight-kort
        insight_group = QGroupBox("Weather Analysis")
        insight_group.setProperty("variant", "panel")
        insight_layout = QVBoxLayout()
        insight_group.setLayout(insight_layout)

        self.weather_insights = QLabel("Load data to see weather impact...")
        self.weather_insights.setWordWrap(True)
        self.weather_insights.setProperty("role", "muted")
        insight_layout.addWidget(self.weather_insights)

        layout.addWidget(insight_group)

        # Grafer
        graphs_layout = QHBoxLayout()
        layout.addLayout(graphs_layout)

        # Temperatur vs presisjon
        temp_group = QGroupBox("Temperature vs Group Size")
        temp_group.setProperty("variant", "panel")
        temp_layout = QVBoxLayout()
        temp_group.setLayout(temp_layout)

        self.temp_canvas = FigureCanvas(Figure(figsize=(5, 4)))
        temp_layout.addWidget(self.temp_canvas)

        graphs_layout.addWidget(temp_group)

        # Vind vs presisjon
        wind_group = QGroupBox("Wind vs Group Size")
        wind_group.setProperty("variant", "panel")
        wind_layout = QVBoxLayout()
        wind_group.setLayout(wind_layout)

        self.wind_canvas = FigureCanvas(Figure(figsize=(5, 4)))
        wind_layout.addWidget(self.wind_canvas)

        graphs_layout.addWidget(wind_group)

        return widget

    def create_trends_tab(self):
        """Create the trends tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Trend-insights
        trend_group = QGroupBox("Trend Analysis")
        trend_group.setProperty("variant", "panel")
        trend_layout = QVBoxLayout()
        trend_group.setLayout(trend_layout)

        self.trend_insights = QLabel("Load data to see trends...")
        self.trend_insights.setWordWrap(True)
        self.trend_insights.setProperty("role", "muted")
        trend_layout.addWidget(self.trend_insights)

        layout.addWidget(trend_group)

        # Trendgraf
        graph_group = QGroupBox("Precision Trend (Moving Average)")
        graph_group.setProperty("variant", "panel")
        graph_layout = QVBoxLayout()
        graph_group.setLayout(graph_layout)

        self.trend_canvas = FigureCanvas(Figure(figsize=(10, 5)))
        graph_layout.addWidget(self.trend_canvas)

        layout.addWidget(graph_group)

        return widget

    def create_alerts_tab(self):
        """Create the alerts tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Info
        info = QLabel(
            """
        <h3>POI Shift Detection</h3>
        <p>The system automatically warns if it detects:</p>
        <ul>
            <li><b>Sudden degradation</b>: Group size increases by >30% from the previous session</li>
            <li><b>Gradual trend</b>: Precision worsens over 5+ sessions</li>
            <li><b>Weather anomalies</b>: Unusual behavior under specific weather conditions</li>
        </ul>
        """
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Varsler-tabell
        alerts_group = QGroupBox("Active Alerts")
        alerts_group.setProperty("variant", "panel")
        alerts_layout = QVBoxLayout()
        alerts_group.setLayout(alerts_layout)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels(
            ["Severity", "Type", "Rifle/Ammo", "Description"]
        )
        alerts_layout.addWidget(self.alerts_table)

        layout.addWidget(alerts_group)

        layout.addStretch()

        return widget

    def create_stat_card(self, title, value, accent: str | None = None):
        """Create a statistics card."""
        card = QFrame()
        card.setMinimumHeight(80)
        card.setProperty("variant", "statCard")

        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)
        card.setLayout(card_layout)

        accent_color = accent or ReloadingTheme.ACCENT
        accent_bar = QFrame(card)
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(
            f"background-color: {accent_color}; border: none; border-radius: 2px;"
        )
        card_layout.addWidget(accent_bar)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(4)
        card_layout.addLayout(content, 1)

        value_label = QLabel(value)
        value_label.setProperty("variant", "statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setProperty("variant", "statTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content.addWidget(title_label)

        # Store reference to value_label for updates
        card.value_label = value_label

        return card

    def load_rifles(self):
        """Load rifles into the filter."""
        rifles = self.db.execute_query("SELECT id, name FROM rifles ORDER BY name")
        for rifle_id, name in rifles:
            self.rifle_filter.addItem(name, rifle_id)

    def load_ammo_profiles(self):
        """Load ammunition profiles into the filter."""
        ammos = self.db.execute_query(
            "SELECT id, name FROM ammo_profiles ORDER BY name"
        )
        for ammo_id, name in ammos:
            self.ammo_filter.addItem(name, ammo_id)

    def refresh_data(self):
        """Refresh all data and charts."""
        # Get filtered data
        data = self.get_shooting_data()

        if len(data) == 0:
            return

        # Update statistics cards
        self.update_stats_cards(data)

        # Update overview chart
        self.update_overview_graph(data)

        # Update detailed table
        self.update_detail_table(data)

        # Update weather analysis
        self.update_weather_analysis(data)

        # Update trend analysis
        self.update_trend_analysis(data)

        # Update alerts
        self.update_alerts(data)

    def get_shooting_data(self):
        """Fetch shooting data based on filters."""
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

            self.avg_group_label.value_label.setText(_format_group_mm(avg_group))
            self.best_group_label.value_label.setText(_format_group_mm(best_group))
            self.worst_group_label.value_label.setText(_format_group_mm(worst_group))

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
        ax.set_xlabel("Date")
        ax.set_ylabel(f"Group Size ({_group_unit_label()})")
        ax.set_title("Precision Over Time")
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
                i, 3, QTableWidgetItem(_format_group_mm(best_group))
            )
            self.detail_table.setItem(i, 4, QTableWidgetItem(moa))
            self.detail_table.setItem(
                i, 5, QTableWidgetItem(_format_temperature_c(temp))
            )
            self.detail_table.setItem(i, 6, QTableWidgetItem(_format_wind_mps(wind)))

    def update_weather_analysis(self, data):
        """Update weather analysis."""
        # Filter data that includes temperature and wind
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
            # Find the best temperature range
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
<h3>Temperature Analysis</h3>
<p><b>Your rifle shoots best at:</b> {best_range}<br>
Average group: {_format_group_mm(best_avg)}</p>
            """

            # Draw temperature chart
            temps = [t for t, g in temp_data]
            groups = [g for t, g in temp_data]

            fig = self.temp_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            ax.scatter(temps, groups)
            ax.set_xlabel(_temperature_axis_label())
            ax.set_ylabel(f"Group ({_group_unit_label()})")
            ax.set_title("Temperature vs Precision")
            ax.grid(True, alpha=0.3)
            self.temp_canvas.draw()

            self.weather_insights.setHtml(insight_text)

        if wind_data:
            # Draw wind chart
            winds = [w for w, g in wind_data]
            groups = [g for w, g in wind_data]

            fig = self.wind_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)
            ax.scatter(winds, groups)
            ax.set_xlabel(_wind_axis_label())
            ax.set_ylabel(f"Group ({_group_unit_label()})")
            ax.set_title("Wind vs Precision")
            ax.grid(True, alpha=0.3)
            self.wind_canvas.draw()

    def update_trend_analysis(self, data):
        """Update trend analysis."""
        if len(data) < 3:
            return

        groups = [row[3] for row in data if row[3] is not None]

        if len(groups) < 3:
            return

        # Calculate moving average
        window = min(5, len(groups))
        moving_avg = []
        for i in range(len(groups) - window + 1):
            avg = sum(groups[i : i + window]) / window
            moving_avg.append(avg)

        # Calculate trend (improvement or deterioration)
        if len(moving_avg) >= 2:
            start_avg = (
                sum(moving_avg[:3]) / 3 if len(moving_avg) >= 3 else moving_avg[0]
            )
            end_avg = (
                sum(moving_avg[-3:]) / 3 if len(moving_avg) >= 3 else moving_avg[-1]
            )

            change_pct = ((end_avg - start_avg) / start_avg) * 100

            if change_pct < -10:
                trend_text = f"<span style='color: green;'>Precision is improving! ({abs(change_pct):.1f}% better)</span>"
            elif change_pct > 10:
                trend_text = f"<span style='color: red;'>Precision is worsening ({change_pct:.1f}% worse)</span>"
            else:
                trend_text = "<span style='color: blue;'>Stable precision</span>"

            insight = f"""
<h3>Trend Analysis</h3>
<p>{trend_text}</p>
<p>Early sessions: {_format_group_mm(start_avg)} average<br>
Latest sessions: {_format_group_mm(end_avg)} average</p>
            """

            self.trend_insights.setHtml(insight)

        # Draw trend chart
        dates = [
            datetime.strptime(row[0], "%Y-%m-%d") for row in data if row[3] is not None
        ]

        fig = self.trend_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        ax.plot(dates, groups, "o", alpha=0.5, label="Actual")

        if len(moving_avg) > 0:
            ma_dates = dates[window - 1 :]
            ax.plot(
                ma_dates,
                moving_avg,
                "r-",
                linewidth=2,
                label=f"{window}-session moving average",
            )

        ax.set_xlabel("Date")
        ax.set_ylabel(f"Group ({_group_unit_label()})")
        ax.set_title("Precision Trend")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        self.trend_canvas.draw()

    def update_alerts(self, data):
        """Update alerts."""
        if len(data) < 2:
            return

        alerts = []

        # Check for sudden deterioration
        recent_groups = [row[3] for row in data[-3:] if row[3] is not None]
        previous_groups = [row[3] for row in data[-6:-3] if row[3] is not None]

        if recent_groups and previous_groups:
            recent_avg = sum(recent_groups) / len(recent_groups)
            previous_avg = sum(previous_groups) / len(previous_groups)

            change_pct = ((recent_avg - previous_avg) / previous_avg) * 100

            if change_pct > 30:
                alerts.append(
                    (
                        "🔴 HIGH",
                        "Sudden Deterioration",
                        data[-1][1] or "N/A",
                        f"Group size increased {change_pct:.0f}% over the last 3 sessions. Check rifle/optic!",
                    )
                )

        # Update table
        self.alerts_table.setRowCount(len(alerts))

        for i, (severity, alert_type, rifle_ammo, description) in enumerate(alerts):
            self.alerts_table.setItem(i, 0, QTableWidgetItem(severity))
            self.alerts_table.setItem(i, 1, QTableWidgetItem(alert_type))
            self.alerts_table.setItem(i, 2, QTableWidgetItem(rifle_ammo))
            self.alerts_table.setItem(i, 3, QTableWidgetItem(description))

            # Color severity
            color = (
                QColor(255, 200, 200) if "HIGH" in severity else QColor(255, 255, 200)
            )
            for col in range(4):
                self.alerts_table.item(i, col).setBackground(color)
