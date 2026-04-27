"""Field Map Panel — interactive map for placing shooter position and targets.

Primary renderer: QWebEngineView + Leaflet (OpenStreetMap tiles).
Fallback: coordinate-entry panel if QtWebEngine is not installed.

Elevation profile (pyqtgraph) shows terrain between shooter and selected target.

Signals emitted::

    shooter_moved(GeoPoint)   — user repositioned shooter
    target_added(GeoPoint)    — user added a target by clicking the map
    target_removed(int)       — user removed target by index

Usage::

    panel = FieldMapPanel(parent)
    panel.set_shooter(GeoPoint(60.1, 10.5))
    panel.target_selected.connect(my_handler)
"""

from __future__ import annotations

import math

from ..field_planning.models import GeoPoint
from ..qt_compat import (
    BINDING,
    QDoubleSpinBox,
    QFont,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    Signal,
)

# ---------------------------------------------------------------------------
# Optional: QtWebEngine
# ---------------------------------------------------------------------------

try:
    if BINDING == "PyQt6":
        from PyQt6.QtCore import QObject
        from PyQt6.QtCore import pyqtSlot as _Slot
        from PyQt6.QtWebChannel import QWebChannel
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    else:
        from PySide6.QtCore import QObject
        from PySide6.QtCore import Slot as _Slot
        from PySide6.QtWebChannel import QWebChannel
        from PySide6.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except Exception:
    _HAS_WEBENGINE = False
    QWebEngineView = None  # type: ignore[assignment,misc]
    QWebChannel = None  # type: ignore[assignment]
    QObject = object  # type: ignore[assignment,misc]

    def _Slot(*a, **k):  # type: ignore[misc]
        return lambda f: f


# ---------------------------------------------------------------------------
# Optional: pyqtgraph elevation profile
# ---------------------------------------------------------------------------

try:
    import pyqtgraph as pg

    _HAS_PG = True
except Exception:
    pg = None  # type: ignore[assignment]
    _HAS_PG = False

# ---------------------------------------------------------------------------
# Leaflet HTML template
# ---------------------------------------------------------------------------

_LEAFLET_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  crossorigin=""></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<style>
  html, body { margin:0; padding:0; height:100%; }
  #map { width:100%; height:100vh; background:#1a1e24; }
  #status {
    position:fixed; bottom:12px; left:50%; transform:translateX(-50%);
    background:rgba(0,0,0,0.72); color:#e0e6ed; padding:5px 14px;
    border-radius:14px; font:13px/1.4 sans-serif; z-index:9999;
    pointer-events:none; white-space:nowrap;
  }
</style>
</head>
<body>
<div id="map"></div>
<div id="status">Klikk på kart for å sette skytepost</div>
<script>
var map = L.map('map', {preferCanvas:true}).setView([60.0, 10.0], 10);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution:'© OpenStreetMap',
  maxZoom:19
}).addTo(map);

var bridge = null;
var clickMode = 'shooter';
var shooterMarker = null;
var targetMarkers = [];
var shootingLines = [];

new QWebChannel(qt.webChannelTransport, function(ch) {
  bridge = ch.objects.bridge;
  bridge.statusChanged.connect(function(txt){ setStatus(txt); });
});

function setClickMode(mode) {
  clickMode = mode;
  var labels = {shooter:'Klikk for skytepost', target:'Klikk for mål', none:''};
  setStatus(labels[mode] || '');
}

function setStatus(txt) {
  document.getElementById('status').textContent = txt;
}

map.on('click', function(e) {
  if (!bridge || clickMode === 'none') return;
  bridge.onMapClick(e.latlng.lat, e.latlng.lng, clickMode);
});

// Shooter marker (orange circle)
function setShooter(lat, lon) {
  if (shooterMarker) map.removeLayer(shooterMarker);
  var ic = L.divIcon({className:'', html:
    '<div style="width:14px;height:14px;background:#ff6600;border:2.5px solid #fff;'+
    'border-radius:50%;box-shadow:0 0 4px #000;"></div>',
    iconAnchor:[7,7]});
  shooterMarker = L.marker([lat,lon],{icon:ic,zIndexOffset:1000})
    .addTo(map).bindPopup('<b>Skytepost</b><br>'+lat.toFixed(6)+', '+lon.toFixed(6));
  _updateLines();
}

// Target marker (coloured square)
function addTarget(lat, lon, label, color) {
  color = color || '#40c0ff';
  var ic = L.divIcon({className:'', html:
    '<div style="width:11px;height:11px;background:'+color+';border:2px solid #fff;'+
    'border-radius:2px;box-shadow:0 0 3px #000;"></div>',
    iconAnchor:[5,5]});
  var m = L.marker([lat,lon],{icon:ic})
    .addTo(map).bindPopup('<b>'+label+'</b><br>'+lat.toFixed(6)+', '+lon.toFixed(6));
  targetMarkers.push(m);
  _updateLines();
}

function clearTargets() {
  targetMarkers.forEach(function(m){ map.removeLayer(m); });
  targetMarkers = [];
  shootingLines.forEach(function(l){ map.removeLayer(l); });
  shootingLines = [];
}

function _updateLines() {
  shootingLines.forEach(function(l){ map.removeLayer(l); });
  shootingLines = [];
  if (!shooterMarker || targetMarkers.length === 0) return;
  var s = shooterMarker.getLatLng();
  targetMarkers.forEach(function(m){
    var l = L.polyline([s, m.getLatLng()],
      {color:'#ff7700',weight:2,dashArray:'7,5',opacity:0.75}).addTo(map);
    shootingLines.push(l);
  });
}

function panTo(lat, lon, zoom) {
  map.setView([lat,lon], zoom != null ? zoom : map.getZoom());
}

function fitAll() {
  var pts = [];
  if (shooterMarker) pts.push(shooterMarker.getLatLng());
  targetMarkers.forEach(function(m){ pts.push(m.getLatLng()); });
  if (pts.length > 1) map.fitBounds(L.latLngBounds(pts), {padding:[40,40]});
  else if (pts.length === 1) map.setView(pts[0], 14);
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Python ↔ JavaScript bridge
# ---------------------------------------------------------------------------


class _MapBridge(QObject):  # type: ignore[misc]
    """Receives click events from the Leaflet JS layer."""

    map_clicked = Signal(float, float, str)
    statusChanged = Signal(str)

    @_Slot(float, float, str)
    def onMapClick(self, lat: float, lon: float, mode: str) -> None:
        self.map_clicked.emit(lat, lon, mode)


# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(min(1.0, a)))


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _fetch_elevation_profile(
    lat1: float, lon1: float, lat2: float, lon2: float, n: int = 20
) -> list[tuple[float, float]]:
    """Return (distance_m, elevation_m) pairs. Falls back to empty list."""
    try:
        import requests  # type: ignore[import-untyped]

        lats = [lat1 + (lat2 - lat1) * i / (n - 1) for i in range(n)]
        lons = [lon1 + (lon2 - lon1) * i / (n - 1) for i in range(n)]
        locations = "|".join(f"{la},{lo}" for la, lo in zip(lats, lons))
        url = f"https://api.opentopodata.org/v1/srtm30m?locations={locations}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        total = _haversine_m(lat1, lon1, lat2, lon2)
        return [
            (total * i / (n - 1), float(r.get("elevation") or 0))
            for i, r in enumerate(results)
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------


class FieldMapPanel(QWidget):
    """Interactive map for field position planning.

    Signals::

        shooter_moved(GeoPoint)
        target_added(GeoPoint)
        target_removed(int)      index into internal list
    """

    shooter_moved = Signal(object)
    target_added = Signal(object)
    target_removed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shooter: GeoPoint | None = None
        self._targets: list[tuple[GeoPoint, str]] = []  # (point, label)
        self._click_mode: str = "shooter"
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_shooter(self, point: GeoPoint) -> None:
        self._shooter = point
        self._lat_spin.setValue(point.lat)
        self._lon_spin.setValue(point.lon)
        if _HAS_WEBENGINE and self._webview is not None:
            self._js(f"setShooter({point.lat}, {point.lon})")
            self._js(f"panTo({point.lat}, {point.lon}, 12)")
        self._refresh_target_table()

    def add_target(self, point: GeoPoint, label: str = "") -> None:
        idx = len(self._targets)
        if not label:
            label = f"Mål {idx + 1}"
        self._targets.append((point, label))
        color = _target_color(idx)
        if _HAS_WEBENGINE and self._webview is not None:
            self._js(f"addTarget({point.lat}, {point.lon}, '{label}', '{color}')")
        self._refresh_target_table()
        self.target_added.emit(point)

    def clear_targets(self) -> None:
        self._targets.clear()
        if _HAS_WEBENGINE and self._webview is not None:
            self._js("clearTargets()")
        self._refresh_target_table()

    def fit_all(self) -> None:
        if _HAS_WEBENGINE and self._webview is not None:
            self._js("fitAll()")

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(4, 4, 4, 4)

        root.addWidget(self._build_toolbar())

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: map + elevation profile
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(2)

        self._webview = None
        if _HAS_WEBENGINE:
            try:
                self._webview = QWebEngineView()
                self._channel = QWebChannel()
                self._bridge = _MapBridge()
                self._bridge.map_clicked.connect(self._on_map_click)
                self._channel.registerObject("bridge", self._bridge)
                self._webview.page().setWebChannel(self._channel)
                self._webview.setHtml(_LEAFLET_HTML)
                self._webview.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                lv.addWidget(self._webview, stretch=4)
            except Exception:
                self._webview = None

        if self._webview is None:
            fallback = QLabel(
                "Interaktivt kart krever PyQt6-WebEngine / PySide6-WebEngineWidgets.\n"
                "Bruk koordinatinntasting til høyre."
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet(
                "color: #888; font-size: 10.5pt; background: #1a1e24;"
            )
            fallback.setMinimumHeight(200)
            lv.addWidget(fallback, stretch=4)

        lv.addWidget(self._build_elevation_widget(), stretch=1)
        splitter.addWidget(left)

        # Right: shooter coords + target list + info
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)
        rv.setSpacing(6)
        rv.addWidget(self._build_shooter_panel())
        rv.addWidget(self._build_target_panel(), stretch=1)
        rv.addWidget(self._build_info_panel())
        splitter.addWidget(right)

        splitter.setSizes([600, 280])
        root.addWidget(splitter)

    def _build_toolbar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #2c313a; border-radius: 4px;")
        h = QHBoxLayout(w)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(8)

        title = QLabel("KARTKONTROLL")
        f = QFont()
        f.setBold(True)
        f.setPointSize(10)
        title.setFont(f)
        title.setStyleSheet("color: #b0b6be;")
        h.addWidget(title)
        h.addStretch()

        self._shooter_btn = QPushButton("🔫 Sett skytepost")
        self._shooter_btn.setCheckable(True)
        self._shooter_btn.setChecked(True)
        self._shooter_btn.setStyleSheet(
            "QPushButton:checked { background: #ff6600; color: white; font-weight: bold; }"
        )
        self._shooter_btn.clicked.connect(lambda: self._set_click_mode("shooter"))
        h.addWidget(self._shooter_btn)

        self._target_btn = QPushButton("🎯 Legg til mål")
        self._target_btn.setCheckable(True)
        self._target_btn.setStyleSheet(
            "QPushButton:checked { background: #27ae60; color: white; font-weight: bold; }"
        )
        self._target_btn.clicked.connect(lambda: self._set_click_mode("target"))
        h.addWidget(self._target_btn)

        clear_btn = QPushButton("🗑 Fjern mål")
        clear_btn.clicked.connect(self.clear_targets)
        h.addWidget(clear_btn)

        fit_btn = QPushButton("⊡ Tilpass kart")
        fit_btn.clicked.connect(self.fit_all)
        h.addWidget(fit_btn)

        return w

    def _build_shooter_panel(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #23272e; border-radius: 4px; padding: 2px;")
        v = QVBoxLayout(w)
        v.setContentsMargins(6, 4, 6, 4)
        v.setSpacing(4)

        hdr = QLabel("Skytepost")
        f = QFont()
        f.setBold(True)
        hdr.setFont(f)
        hdr.setStyleSheet("color: #ff8040;")
        v.addWidget(hdr)

        row = QHBoxLayout()
        row.setSpacing(4)
        row.addWidget(QLabel("Lat:"))
        self._lat_spin = QDoubleSpinBox()
        self._lat_spin.setRange(-90, 90)
        self._lat_spin.setDecimals(6)
        self._lat_spin.setValue(60.0)
        self._lat_spin.setFixedWidth(110)
        row.addWidget(self._lat_spin)

        row.addWidget(QLabel("Lon:"))
        self._lon_spin = QDoubleSpinBox()
        self._lon_spin.setRange(-180, 180)
        self._lon_spin.setDecimals(6)
        self._lon_spin.setValue(10.0)
        self._lon_spin.setFixedWidth(110)
        row.addWidget(self._lon_spin)

        set_btn = QPushButton("Sett")
        set_btn.setFixedWidth(50)
        set_btn.clicked.connect(self._on_manual_shooter)
        row.addWidget(set_btn)
        row.addStretch()
        v.addLayout(row)
        return w

    def _build_target_panel(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Mål")
        f = QFont()
        f.setBold(True)
        hdr.setFont(f)
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        rem_btn = QPushButton("– Fjern valgt")
        rem_btn.setFixedWidth(90)
        rem_btn.clicked.connect(self._remove_selected_target)
        hdr_row.addWidget(rem_btn)

        elev_btn = QPushButton("⛰ Høydeprofil")
        elev_btn.setFixedWidth(100)
        elev_btn.clicked.connect(self._fetch_elevation)
        hdr_row.addWidget(elev_btn)
        v.addLayout(hdr_row)

        self._target_table = QTableWidget()
        self._target_table.setColumnCount(5)
        self._target_table.setHorizontalHeaderLabels(
            ["Navn", "Lat", "Lon", "Avst. m", "Retning °"]
        )
        hh = self._target_table.horizontalHeader()
        if hh:
            hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            hh.setStretchLastSection(True)
        self._target_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._target_table.setAlternatingRowColors(True)
        self._target_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._target_table.setStyleSheet("font-size: 10pt;")
        self._target_table.itemSelectionChanged.connect(self._on_target_selected)
        v.addWidget(self._target_table)
        return w

    def _build_info_panel(self) -> QWidget:
        self._info_label = QLabel("Ingen mål valgt.")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(
            "color: #b0b6be; font-size: 9.5pt; background: #1c2028; "
            "padding: 4px 6px; border-radius: 3px;"
        )
        return self._info_label

    def _build_elevation_widget(self) -> QWidget:
        if _HAS_PG:
            self._elev_plot: pg.PlotWidget | None = pg.PlotWidget()
            self._elev_plot.setBackground("#161a1f")
            self._elev_plot.setTitle("Høydeprofil (m)", color="#b0b6be", size="9pt")
            self._elev_plot.getAxis("left").setLabel("Høyde m", color="#b0b6be")
            self._elev_plot.getAxis("bottom").setLabel("Avstand m", color="#b0b6be")
            self._elev_plot.setMaximumHeight(160)
            return self._elev_plot
        else:
            self._elev_plot = None
            lbl = QLabel("Høydeprofil: krever pyqtgraph")
            lbl.setStyleSheet("color: #555; font-size: 9pt;")
            lbl.setFixedHeight(40)
            return lbl

    # ------------------------------------------------------------------
    # Interaction handlers
    # ------------------------------------------------------------------

    def _set_click_mode(self, mode: str) -> None:
        self._click_mode = mode
        self._shooter_btn.setChecked(mode == "shooter")
        self._target_btn.setChecked(mode == "target")
        if _HAS_WEBENGINE and self._webview is not None:
            self._js(f"setClickMode('{mode}')")

    def _on_map_click(self, lat: float, lon: float, mode: str) -> None:
        if mode == "shooter":
            point = GeoPoint(lat, lon)
            self.set_shooter(point)
            self.shooter_moved.emit(point)
            self._set_click_mode("target")
        elif mode == "target":
            self.add_target(GeoPoint(lat, lon))

    def _on_manual_shooter(self) -> None:
        point = GeoPoint(self._lat_spin.value(), self._lon_spin.value())
        self.set_shooter(point)
        self.shooter_moved.emit(point)

    def _remove_selected_target(self) -> None:
        rows = sorted(
            {idx.row() for idx in self._target_table.selectedIndexes()},
            reverse=True,
        )
        for r in rows:
            if 0 <= r < len(self._targets):
                self._targets.pop(r)
                self.target_removed.emit(r)
        # Rebuild map markers from scratch
        if _HAS_WEBENGINE and self._webview is not None:
            self._js("clearTargets()")
            for i, (pt, lbl) in enumerate(self._targets):
                color = _target_color(i)
                self._js(f"addTarget({pt.lat}, {pt.lon}, '{lbl}', '{color}')")
        self._refresh_target_table()

    def _on_target_selected(self) -> None:
        rows = list({idx.row() for idx in self._target_table.selectedIndexes()})
        if not rows or self._shooter is None:
            self._info_label.setText("Ingen mål valgt.")
            return
        row = rows[0]
        if row >= len(self._targets):
            return
        pt, lbl = self._targets[row]
        dist = _haversine_m(self._shooter.lat, self._shooter.lon, pt.lat, pt.lon)
        brg = _bearing_deg(self._shooter.lat, self._shooter.lon, pt.lat, pt.lon)
        self._info_label.setText(
            f"{lbl}  |  {dist:.0f} m  |  {brg:.1f}°  |  "
            f"Lat {pt.lat:.6f}  Lon {pt.lon:.6f}"
        )

    def _fetch_elevation(self) -> None:
        if self._shooter is None:
            self._info_label.setText("Sett skytepost først.")
            return
        rows = list({idx.row() for idx in self._target_table.selectedIndexes()})
        if not rows:
            self._info_label.setText("Velg et mål i listen for å hente høydeprofil.")
            return
        row = rows[0]
        if row >= len(self._targets):
            return
        pt, lbl = self._targets[row]
        self._info_label.setText(f"Henter høydedata for {lbl}…")
        profile = _fetch_elevation_profile(
            self._shooter.lat, self._shooter.lon, pt.lat, pt.lon
        )
        if not profile:
            self._info_label.setText("Høydedata ikke tilgjengelig (krever internett).")
            return
        self._draw_elevation_profile(profile)
        self._info_label.setText(
            f"{lbl}  |  {profile[-1][0]:.0f} m  |  "
            f"Min elev: {min(e for _, e in profile):.0f} m  "
            f"Max: {max(e for _, e in profile):.0f} m"
        )

    def _draw_elevation_profile(self, profile: list[tuple[float, float]]) -> None:
        if not _HAS_PG or self._elev_plot is None:
            return
        xs = [p[0] for p in profile]
        ys = [p[1] for p in profile]
        self._elev_plot.clear()
        fill = pg.FillBetweenItem(
            pg.PlotDataItem(xs, ys, pen=pg.mkPen("#5080c0", width=2)),
            pg.PlotDataItem(xs, [0] * len(xs), pen=None),
            brush=pg.mkBrush("#1a3050"),
        )
        self._elev_plot.addItem(fill)
        self._elev_plot.plot(xs, ys, pen=pg.mkPen("#80b0ff", width=2))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_target_table(self) -> None:
        self._target_table.setRowCount(len(self._targets))
        for i, (pt, lbl) in enumerate(self._targets):

            def _c(text: str) -> QTableWidgetItem:
                it = QTableWidgetItem(text)
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                return it

            dist_str = "—"
            brg_str = "—"
            if self._shooter is not None:
                dist = _haversine_m(
                    self._shooter.lat, self._shooter.lon, pt.lat, pt.lon
                )
                brg = _bearing_deg(self._shooter.lat, self._shooter.lon, pt.lat, pt.lon)
                dist_str = f"{dist:.0f}"
                brg_str = f"{brg:.1f}"

            self._target_table.setItem(i, 0, _c(lbl))
            self._target_table.setItem(i, 1, _c(f"{pt.lat:.6f}"))
            self._target_table.setItem(i, 2, _c(f"{pt.lon:.6f}"))
            self._target_table.setItem(i, 3, _c(dist_str))
            self._target_table.setItem(i, 4, _c(brg_str))

    def _js(self, script: str) -> None:
        if self._webview is not None:
            self._webview.page().runJavaScript(script)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TARGET_COLORS = [
    "#40c0ff",
    "#60d060",
    "#f0c040",
    "#e060a0",
    "#80e0c0",
    "#c080ff",
    "#ff8040",
    "#a0d0ff",
]


def _target_color(idx: int) -> str:
    return _TARGET_COLORS[idx % len(_TARGET_COLORS)]
