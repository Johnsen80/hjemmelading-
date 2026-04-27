"""Field Planning Window — the central module for advanced field ballistic planning.

Combines:
  - Weapon/ammo selector with zero-shift display
  - Calibrated DOPE card from learned BC/MV
  - Shooting range tab with per-target click tables + slant correction
  - Hunting tab with backstop safety analysis
  - Bullet Journey visualization (3-panel pyqtgraph)
  - Atmosphere panel with warnings

Usage (standalone)::

    win = FieldPlanningWindow(db=database, parent=main_window)
    win.show()

Usage (from menu)::

    win = FieldPlanningWindow(db=database, parent=self)
    win.load_session_for_rifle(rifle_id)
    win.show()
"""

from __future__ import annotations

from ..field_planning.atmosphere import build_layered_atmosphere
from ..field_planning.models import (
    FieldSession,
    FieldTarget,
    GeoPoint,
    LayeredAtmosphere,
    RangeSession,
    WeaponBallisticProfile,
)
from ..field_planning.services import build_dope_card, build_field_solution
from ..qt_compat import (
    QComboBox,
    QDialog,
    QFont,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    Signal,
)
from .atmosphere_panel import AtmospherePanel
from .dope_card_panel import DopeCardPanel
from .field_map_panel import FieldMapPanel
from .hunting_tab import HuntingTab
from .range_tab import RangeTab


class FieldPlanningWindow(QDialog):
    """Main Field Planning window — weapon, DOPE, range, hunting, bullet journey."""

    session_changed = Signal(object)  # emits FieldSession on any change

    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self._db = db
        self._session: FieldSession | None = None
        self._available_profiles: list[WeaponBallisticProfile] = []
        self._shooter_point: GeoPoint | None = None
        self._map_target_count: int = 0

        self.setWindowTitle("Field Planning — DOPE / Range / Hunting")
        self.resize(1280, 800)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_session_for_rifle(self, rifle_id: int) -> None:
        """Load the best profile from DB for the given rifle and refresh."""
        if self._db is None:
            return
        try:
            from ..utils.ballistics_profile_bridge import build_weapon_ballistic_profile

            profile = build_weapon_ballistic_profile(self._db, rifle_id)
            self._set_profile(profile)
        except Exception as exc:
            self._status_bar.setText(f"Error loading profile: {exc}")

    def set_profile(self, profile: WeaponBallisticProfile) -> None:
        self._set_profile(profile)

    def set_atmosphere(self, atm: LayeredAtmosphere) -> None:
        if self._session is not None:
            self._session = FieldSession(
                profile=self._session.profile,
                atmosphere=atm,
                targets=self._session.targets,
                latitude_deg=self._session.latitude_deg,
                azimuth_deg=self._session.azimuth_deg,
                clicks_per_moa=self._session.clicks_per_moa,
                scope_unit=self._session.scope_unit,
            )
            self._refresh_all()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(6, 6, 6, 6)

        # ── Header bar ──────────────────────────────────────────────
        root.addWidget(self._build_header())

        # ── Conditions bar ──────────────────────────────────────────
        root.addWidget(self._build_conditions_bar())

        # ── Main area ───────────────────────────────────────────────
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: DOPE card
        self._dope_panel = DopeCardPanel()
        self._dope_panel.setMinimumWidth(280)
        self._dope_panel.setMaximumWidth(480)
        main_splitter.addWidget(self._dope_panel)

        # Right: tabbed content
        right_tabs = QTabWidget()
        right_tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._range_tab = RangeTab()
        right_tabs.addTab(self._range_tab, "🎯 Range")

        self._hunting_tab = HuntingTab()
        right_tabs.addTab(self._hunting_tab, "🦌 Hunting")

        self._atm_panel = AtmospherePanel()
        right_tabs.addTab(self._atm_panel, "🌤 Atmosphere")

        self._journey_tab = self._build_journey_tab()
        right_tabs.addTab(self._journey_tab, "💫 Kulens reise")

        self._map_panel = FieldMapPanel()
        self._map_panel.shooter_moved.connect(self._on_map_shooter_moved)
        self._map_panel.target_added.connect(self._on_map_target_added)
        right_tabs.addTab(self._map_panel, "🗺 Kart")

        main_splitter.addWidget(right_tabs)
        main_splitter.setSizes([320, 900])
        root.addWidget(main_splitter)

        # ── Status bar ──────────────────────────────────────────────
        self._status_bar = QLabel("No profile loaded.")
        self._status_bar.setStyleSheet(
            "color: #b0b6be; font-size: 9.5pt; padding: 2px 4px;"
            "border-top: 1px solid #3c4250;"
        )
        root.addWidget(self._status_bar)

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #2c313a; border-radius: 4px;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("FIELD PLANNING")
        f = QFont()
        f.setBold(True)
        f.setPointSize(13)
        title.setFont(f)
        title.setStyleSheet("color: #e0e6ed;")
        layout.addWidget(title)
        layout.addStretch()

        layout.addWidget(QLabel("Våpen:"))
        self._rifle_combo = QComboBox()
        self._rifle_combo.setMinimumWidth(180)
        self._rifle_combo.currentIndexChanged.connect(self._on_rifle_changed)
        layout.addWidget(self._rifle_combo)

        layout.addWidget(QLabel("Scope:"))
        self._scope_combo = QComboBox()
        self._scope_combo.addItems(
            [
                "1/4 MOA (4 kl/MOA)",
                "1/8 MOA (8 kl/MOA)",
                "0.1 MRAD (10 kl/MRAD)",
                "0.05 MRAD (20 kl/MRAD)",
            ]
        )
        self._scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        layout.addWidget(self._scope_combo)

        refresh_btn = QPushButton("↻ Oppdater")
        refresh_btn.clicked.connect(self._refresh_all)
        layout.addWidget(refresh_btn)

        return w

    def _build_conditions_bar(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(12)

        # Temperature
        layout.addWidget(QLabel("Temp °C:"))
        from ..qt_compat import QDoubleSpinBox

        self._temp_spin = QDoubleSpinBox()
        self._temp_spin.setRange(-40, 50)
        self._temp_spin.setValue(15.0)
        self._temp_spin.setSingleStep(1.0)
        self._temp_spin.setFixedWidth(70)
        layout.addWidget(self._temp_spin)

        layout.addWidget(QLabel("Pressure hPa:"))
        self._press_spin = QDoubleSpinBox()
        self._press_spin.setRange(850, 1080)
        self._press_spin.setValue(1013.25)
        self._press_spin.setSingleStep(1.0)
        self._press_spin.setDecimals(1)
        self._press_spin.setFixedWidth(80)
        layout.addWidget(self._press_spin)

        layout.addWidget(QLabel("RF%:"))
        self._hum_spin = QDoubleSpinBox()
        self._hum_spin.setRange(0, 100)
        self._hum_spin.setValue(50.0)
        self._hum_spin.setSingleStep(5.0)
        self._hum_spin.setFixedWidth(65)
        layout.addWidget(self._hum_spin)

        layout.addWidget(QLabel("Wind m/s:"))
        self._wind_spin = QDoubleSpinBox()
        self._wind_spin.setRange(0, 30)
        self._wind_spin.setValue(0.0)
        self._wind_spin.setSingleStep(0.5)
        self._wind_spin.setFixedWidth(65)
        layout.addWidget(self._wind_spin)

        layout.addWidget(QLabel("Vindretning °:"))
        self._winddir_spin = QDoubleSpinBox()
        self._winddir_spin.setRange(0, 359)
        self._winddir_spin.setValue(270.0)
        self._winddir_spin.setSingleStep(10.0)
        self._winddir_spin.setFixedWidth(65)
        layout.addWidget(self._winddir_spin)

        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(60)
        apply_btn.clicked.connect(self._apply_conditions)
        layout.addWidget(apply_btn)

        fetch_btn = QPushButton("☁ Hent vær")
        fetch_btn.setFixedWidth(90)
        fetch_btn.setToolTip(
            "Fetches current weather from met.no for the shooting post position"
        )
        fetch_btn.clicked.connect(self._fetch_weather)
        layout.addWidget(fetch_btn)

        layout.addStretch()

        self._da_badge = QLabel("")
        self._da_badge.setStyleSheet(
            "background: #1a3a5a; color: #80c0ff; padding: 2px 8px; "
            "border-radius: 4px; font-size: 10pt;"
        )
        layout.addWidget(self._da_badge)

        return w

    def _build_journey_tab(self) -> QWidget:
        try:
            from .bullet_journey_widget import BulletJourneyWidget

            w = BulletJourneyWidget()
            self._journey_widget = w
            return w
        except Exception:
            placeholder = QLabel(
                "Bullet journey visualization\n(requires pyqtgraph + computed trajectory)"
            )
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #888; font-size: 11pt;")
            self._journey_widget = None
            return placeholder

    # ------------------------------------------------------------------
    # Profile / session management
    # ------------------------------------------------------------------

    def _set_profile(self, profile: WeaponBallisticProfile) -> None:
        atm = self._build_atmosphere()
        self._session = FieldSession(
            profile=profile,
            atmosphere=atm,
            latitude_deg=60.0,
            clicks_per_moa=self._clicks_per_moa(),
            scope_unit=self._scope_unit(),
        )
        self._refresh_all()
        self._status_bar.setText(
            f"Lastet: {profile.rifle_name}  |  BC {profile.learned_bc:.4f} ({profile.bc_source})"
            f"  |  MV {profile.learned_mv_fps:.0f} fps ±{profile.learned_mv_sd_fps:.1f}"
        )

    def _build_atmosphere(self) -> LayeredAtmosphere:
        try:
            return build_layered_atmosphere(
                temperature_c=self._temp_spin.value(),
                pressure_hpa=self._press_spin.value(),
                humidity_pct=self._hum_spin.value(),
                wind_speed_mps=self._wind_spin.value(),
                wind_dir_deg=self._winddir_spin.value(),
            )
        except Exception:
            return build_layered_atmosphere(15.0, 1013.25, 50.0, 0.0, 270.0)

    def _clicks_per_moa(self) -> float:
        idx = self._scope_combo.currentIndex()
        return [4.0, 8.0, 10.0, 20.0][idx] if 0 <= idx < 4 else 4.0

    def _scope_unit(self) -> str:
        idx = self._scope_combo.currentIndex()
        return "mrad" if idx >= 2 else "moa"

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_rifle_changed(self) -> None:
        idx = self._rifle_combo.currentIndex()
        if 0 <= idx < len(self._available_profiles):
            self._set_profile(self._available_profiles[idx])

    def _on_scope_changed(self) -> None:
        if self._session is not None:
            self._session.clicks_per_moa = self._clicks_per_moa()
            self._session.scope_unit = self._scope_unit()
            self._refresh_all()

    def _apply_conditions(self) -> None:
        atm = self._build_atmosphere()
        if self._session is not None:
            self._session.atmosphere = atm
            self._refresh_all()
        else:
            self._atm_panel.set_atmosphere(atm)
            da = atm.surface_layer.density_altitude_m
            self._da_badge.setText(f"DA: {da:+.0f}m")

    def _fetch_weather(self) -> None:
        """Fetch current weather from met.no locationforecast and fill spinboxes."""
        lat = self._shooter_point.lat if self._shooter_point else 60.0
        lon = self._shooter_point.lon if self._shooter_point else 10.0
        self._status_bar.setText(
            f"Fetching weather from met.no for {lat:.4f}, {lon:.4f}…"
        )
        try:
            import json as _json
            import urllib.request

            url = (
                f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
                f"?lat={lat:.4f}&lon={lon:.4f}"
            )
            req = urllib.request.Request(
                url, headers={"User-Agent": "Hjemmelading/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read())
            instant = data["properties"]["timeseries"][0]["data"]["instant"]["details"]
            temp = float(instant.get("air_temperature", 15.0))
            press = float(instant.get("air_pressure_at_sea_level", 1013.25))
            humid = float(instant.get("relative_humidity", 50.0))
            wind_s = float(instant.get("wind_speed", 0.0))
            wind_d = float(instant.get("wind_from_direction", 270.0))
            self._temp_spin.setValue(temp)
            self._press_spin.setValue(press)
            self._hum_spin.setValue(humid)
            self._wind_spin.setValue(wind_s)
            self._winddir_spin.setValue(wind_d)
            self._apply_conditions()
            self._status_bar.setText(
                f"Vær hentet: {temp:+.1f}°C  {press:.0f} hPa  "
                f"RF {humid:.0f}%  Vind {wind_s:.1f} m/s fra {wind_d:.0f}°"
            )
        except Exception as exc:
            self._status_bar.setText(f"Vær-henting feilet: {exc}")

    # ------------------------------------------------------------------
    # Full refresh
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:
        if self._session is None:
            return
        session = self._session
        atm = session.atmosphere
        if atm is None:
            return

        # DA badge
        da = atm.surface_layer.density_altitude_m
        self._da_badge.setText(f"DA: {da:+.0f}m")

        # DOPE card
        try:
            dope = build_dope_card(session)
            self._dope_panel.set_dope_card(dope)
        except Exception as exc:
            self._status_bar.setText(f"DOPE error: {exc}")

        # Atmosphere panel
        self._atm_panel.set_atmosphere(atm)

        # Range tab: update atmosphere and profile but keep targets
        if self._range_tab._session is None:
            self._range_tab.set_session(
                RangeSession(
                    profile=session.profile,
                    atmosphere=atm,
                    clicks_per_moa=session.clicks_per_moa,
                    scope_unit=session.scope_unit,
                    latitude_deg=session.latitude_deg,
                )
            )
        else:
            rs = self._range_tab._session
            rs.profile = session.profile
            rs.atmosphere = atm
            rs.clicks_per_moa = session.clicks_per_moa
            rs.scope_unit = session.scope_unit
            self._range_tab._compute()

        # Hunting tab
        self._hunting_tab.set_session(session)

        # Bullet journey
        try:
            self._refresh_journey(session)
        except Exception:
            pass

    def _refresh_journey(self, session: FieldSession) -> None:
        if self._journey_widget is None:
            return
        from ..field_planning.journey_data import BulletJourneyData

        target = FieldTarget(
            position=GeoPoint(60.0, 10.0),
            slant_distance_m=1000.0,
            distance_m=1000.0,
        )
        points = build_field_solution(session, target, step_m=10.0)
        if not points:
            return
        data = BulletJourneyData.from_trajectory(
            points=points,
            terrain=None,
            zero_distance_m=session.profile.zero_distance_m,
            ethical_energy_j=1500.0,
        )
        self._journey_widget.set_data(data)

    # ------------------------------------------------------------------
    # Map panel callbacks
    # ------------------------------------------------------------------

    def _on_map_shooter_moved(self, point: GeoPoint) -> None:
        self._shooter_point = point
        self._map_target_count = 0
        if self._session is not None:
            self._session = FieldSession(
                profile=self._session.profile,
                atmosphere=self._session.atmosphere,
                targets=self._session.targets,
                latitude_deg=point.lat,
                azimuth_deg=self._session.azimuth_deg,
                clicks_per_moa=self._session.clicks_per_moa,
                scope_unit=self._session.scope_unit,
            )
        self._status_bar.setText(f"Shooting post: {point.lat:.6f}, {point.lon:.6f}")

    def _on_map_target_added(self, point: GeoPoint) -> None:
        from ..ui.field_map_panel import _bearing_deg, _haversine_m

        self._map_target_count += 1
        label = f"Mål {self._map_target_count}"

        if self._shooter_point is not None:
            dist = _haversine_m(
                self._shooter_point.lat,
                self._shooter_point.lon,
                point.lat,
                point.lon,
            )
            brg = _bearing_deg(
                self._shooter_point.lat,
                self._shooter_point.lon,
                point.lat,
                point.lon,
            )
        else:
            dist = 300.0
            brg = 0.0

        # Push to Range tab
        self._range_tab.add_map_target(label, dist, brg)

        # Push to Hunting tab
        self._hunting_tab.add_aim_point(label, dist, brg)

        self._status_bar.setText(
            f"{label}: {dist:.0f} m  {brg:.1f}°  " f"({point.lat:.5f}, {point.lon:.5f})"
        )

    # ------------------------------------------------------------------
    # Load profiles from DB into combo box
    # ------------------------------------------------------------------

    def populate_rifles(self, profiles: list[WeaponBallisticProfile]) -> None:
        """Fill rifle dropdown from a list of pre-built profiles."""
        self._available_profiles = profiles
        self._rifle_combo.blockSignals(True)
        self._rifle_combo.clear()
        for p in profiles:
            self._rifle_combo.addItem(f"{p.rifle_name}  [{p.caliber}]")
        self._rifle_combo.blockSignals(False)
        if profiles:
            self._set_profile(profiles[0])
