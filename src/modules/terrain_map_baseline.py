from __future__ import annotations

"""Compact, import-safe baseline for terrain_map helpers.

This file is a clean baseline used for triage and unit tests. It keeps
heavy GUI/network dependencies optional so CI and linters can import
it without PyQt or folium installed. Use this as the canonical
implementation while we surgically fix `terrain_map.py`.
"""

import importlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

logger = logging.getLogger(__name__)

_HAS_REQUESTS = False
_HAS_FOLIUM = False

try:
    import requests  # type: ignore

    _HAS_REQUESTS = True
except Exception:
    requests = None  # type: ignore

try:
    import folium  # type: ignore

    _HAS_FOLIUM = True
except Exception:
    folium = None  # type: ignore


class _StubWidget:
    pass


if TYPE_CHECKING:
    from PyQt6.QtGui import QFont, QPainter, QPdfWriter
    from PyQt6.QtWidgets import (
        QDoubleSpinBox,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    _HAS_QT = True
else:
    _HAS_QT = False
    try:
        from PyQt6.QtGui import QFont, QPainter, QPdfWriter
        from PyQt6.QtWidgets import (
            QDoubleSpinBox,
            QFileDialog,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QMessageBox,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )

        _HAS_QT = True
    except Exception:

        class _StubSignal:
            def connect(self, *_a: Any, **_kw: Any) -> None:
                return None

        class _StubWidget:
            def __init__(self, *_a: Any, **_kw: Any) -> None:
                return None

            def __getattr__(self, _name: str) -> Any:
                return _StubWidget()

            def setLayout(self, *_a: Any, **_kw: Any) -> None:
                return None

            def addWidget(self, *_a: Any, **_kw: Any) -> None:
                return None

            def addLayout(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setReadOnly(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setText(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setPlaceholderText(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setRange(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setDecimals(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setValue(self, *_a: Any, **_kw: Any) -> None:
                return None

            def setFont(self, *_a: Any, **_kw: Any) -> None:
                return None

            def text(self) -> str:
                return ""

            def value(self) -> float:
                return 0.0

            def currentRow(self) -> int:
                return -1

            def item(self, *_a: Any, **_kw: Any) -> Any:
                return None

            def clear(self) -> None:
                return None

            def addItem(self, *_a: Any, **_kw: Any) -> None:
                return None

            @property
            def clicked(self) -> _StubSignal:
                return _StubSignal()

        class _StubFont(_StubWidget):
            class Weight:
                Bold = 0

        class _StubPainter(_StubWidget):
            def drawText(self, *_a: Any, **_kw: Any) -> None:
                return None

            def end(self) -> None:
                return None

        class _StubPdfWriter(_StubWidget):
            pass

        class _StubFileDialog:
            @staticmethod
            def getSaveFileName(*_a: Any, **_kw: Any) -> tuple[str, str]:
                return ("", "")

        class _StubMessageBox:
            @staticmethod
            def warning(*_a: Any, **_kw: Any) -> None:
                return None

            @staticmethod
            def information(*_a: Any, **_kw: Any) -> None:
                return None

        QFont = _StubFont  # type: ignore[assignment]
        QPainter = _StubPainter  # type: ignore[assignment]
        QPdfWriter = _StubPdfWriter  # type: ignore[assignment]
        QFileDialog = _StubFileDialog  # type: ignore[assignment]
        QGroupBox = _StubWidget  # type: ignore[assignment]
        QHBoxLayout = _StubWidget  # type: ignore[assignment]
        QLabel = _StubWidget  # type: ignore[assignment]
        QLineEdit = _StubWidget  # type: ignore[assignment]
        QListWidget = _StubWidget  # type: ignore[assignment]
        QMessageBox = _StubMessageBox  # type: ignore[assignment]
        QPushButton = _StubWidget  # type: ignore[assignment]
        QDoubleSpinBox = _StubWidget  # type: ignore[assignment]
        QTextEdit = _StubWidget  # type: ignore[assignment]
        QVBoxLayout = _StubWidget  # type: ignore[assignment]
        QWidget = _StubWidget  # type: ignore[assignment]
        _HAS_QT = False

# Avoid importing PyQt types here; this baseline is import-safe in CI/headless.

try:
    _safe_logger_module = importlib.import_module("HjemmeladingApp.utils.safe_logger")
    append_exception = getattr(_safe_logger_module, "append_exception")  # type: ignore
except Exception:

    def append_exception(msg: str = "", exc: BaseException | None = None, app_name: str = "") -> None:  # type: ignore
        return None


try:
    _network_module = importlib.import_module("src.modules.network")
    NetworkWorker = getattr(_network_module, "NetworkWorker")  # type: ignore
except Exception:
    NetworkWorker = None  # type: ignore

_weather_cache: Dict[Tuple[float, float], dict] = {}


def _resolve_config_dir() -> Path:
    for module_name in ("HjemmeladingApp.config", "src.config"):
        try:
            mod = importlib.import_module(module_name)
            get_config_dir = getattr(mod, "get_config_dir", None)
            if callable(get_config_dir):
                result = get_config_dir()
                if isinstance(result, Path):
                    return result
                if isinstance(result, str):
                    return Path(result)
        except Exception:
            continue
    return Path.cwd()


def _favorites_path() -> Path:
    return _resolve_config_dir() / "terrain_favorites.json"


def _load_favorites() -> list[dict[str, Any]]:
    path = _favorites_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []
    return []


def _save_favorites(items: list[dict[str, Any]]) -> None:
    path = _favorites_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _cache_key(lat: float, lon: float) -> Tuple[float, float]:
    return (round(float(lat), 5), round(float(lon), 5))


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def format_terrain_risk_text(summary: Optional[dict[str, Any]]) -> str:
    if not summary:
        return "Terrain risk has not been analyzed yet."
    title = str(summary.get("title") or "Terrain Risk")
    message = str(summary.get("message") or "").strip()
    score = summary.get("score")
    checks = [
        str(item).strip() for item in (summary.get("checks") or []) if str(item).strip()
    ]
    lines = [title]
    if score is not None:
        lines.append(f"Score: {score}")
    if message:
        lines.append(message)
    if checks:
        lines.append("")
        lines.append("Checks:")
        lines.extend(f"- {item}" for item in checks)
    return "\n".join(lines)


def fetch_weather_data_owm(
    lat: float, lon: float, api_key: Optional[str] = None, timeout: int = 8
) -> Optional[dict]:
    if not _HAS_REQUESTS or requests is None:
        return None
    try:
        key = _cache_key(lat, lon)
    except Exception:
        return None
    if key in _weather_cache:
        return _weather_cache[key]
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "units": "metric", "appid": api_key},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        _weather_cache[key] = data
        return data
    except Exception as exc:
        logger.debug("fetch_weather_data_owm failed: %s", exc)
        try:
            append_exception("fetch_weather_data_owm failed", exc)
        except Exception:
            pass
        return None


def fetch_weather_data_yr(
    lat: float,
    lon: float,
    timeout: int = 10,
    user_agent: str = "ValkyrieBallistics/1.0 (+https://example.local)",
) -> Optional[dict]:
    """Fetch weather from met.no / YR (locationforecast compact).

    The met.no API requires a descriptive User-Agent header. No API key
    is needed. Returns parsed JSON on success or None on failure.
    """
    if not _HAS_REQUESTS or requests is None:
        return None
    try:
        key = _cache_key(lat, lon)
    except Exception:
        return None
    if key in _weather_cache:
        return _weather_cache[key]
    try:
        headers = {"User-Agent": user_agent}
        url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        _weather_cache[key] = data
        return data
    except Exception as exc:
        logger.debug("fetch_weather_data_yr failed: %s", exc)
        try:
            append_exception("fetch_weather_data_yr failed", exc)
        except Exception:
            pass
        return None


def fetch_weather(
    provider: str,
    lat: float,
    lon: float,
    *,
    api_key: Optional[str] = None,
    timeout: int = 10,
    manual_data: Optional[dict] = None,
    **kwargs,
) -> Optional[dict]:
    """Dispatch weather fetch to a chosen provider.

    provider: one of 'auto', 'owm', 'openweathermap', 'yr', 'metno', 'manual'.
    - 'auto': prefer OWM if api_key provided, otherwise YR.
    - 'manual': returns `manual_data` (used for advanced equipment inputs).

    Additional provider-specific kwargs are forwarded.
    """
    p = (provider or "auto").lower()
    if p in ("auto", "default"):
        if api_key:
            p = "owm"
        else:
            p = "yr"

    if p in ("owm", "openweathermap"):
        return fetch_weather_data_owm(lat, lon, api_key=api_key, timeout=timeout)
    if p in ("yr", "metno", "met"):
        # allow custom user_agent via kwargs
        ua = kwargs.get("user_agent", "ValkyrieBallistics/1.0 (+https://example.local)")
        return fetch_weather_data_yr(lat, lon, timeout=timeout, user_agent=ua)
    if p in ("manual",):
        return manual_data

    # Unknown provider: fallback to auto behavior
    if api_key:
        return fetch_weather_data_owm(lat, lon, api_key=api_key, timeout=timeout)
    return fetch_weather_data_yr(lat, lon, timeout=timeout)


def fetch_weather_for_viewer_async(
    viewer: "TerrainMapViewer", api_key: Optional[str] = None
) -> None:
    """Asynchronously fetch weather for a viewer using the viewer's settings.

    The viewer may provide the following optional attributes which this
    function will respect if present:
    - `weather_provider`: provider string (see `fetch_weather`)
    - `weather_api_key`: API key for providers that need it (e.g. OWM)
    - `weather_manual_data`: dict with manual weather info (for 'manual')
    - `weather_user_agent`: custom User-Agent for YR requests
    """
    if not _HAS_REQUESTS:
        return

    # Read provider details from the viewer if available
    provider = getattr(viewer, "weather_provider", "auto")
    api_key = getattr(viewer, "weather_api_key", api_key)
    manual_data = getattr(viewer, "weather_manual_data", None)
    user_agent = getattr(viewer, "weather_user_agent", None)

    # Defensively obtain lat/lon values from viewer
    shooter_lat_obj = getattr(viewer, "shooter_lat", None)
    shooter_lon_obj = getattr(viewer, "shooter_lon", None)
    try:
        lat_getter = getattr(shooter_lat_obj, "value", None)
        lon_getter = getattr(shooter_lon_obj, "value", None)
        lat = _to_float(lat_getter() if callable(lat_getter) else None, 59.9139)
        lon = _to_float(lon_getter() if callable(lon_getter) else None, 10.7522)
    except Exception:
        return

    def _write(res: Optional[dict]) -> None:
        wd = getattr(viewer, "weather_display", None)
        if wd is not None:
            try:
                if hasattr(wd, "setText"):
                    wd.setText(str(res)[:2000])
                else:
                    viewer.weather_display = res
            except Exception:
                pass

    def _task(
        a: float,
        b: float,
        provider_arg: str,
        key: Optional[str],
        manual: Optional[dict],
        ua: Optional[str],
    ) -> Optional[dict]:
        try:
            return fetch_weather(
                provider_arg, a, b, api_key=key, manual_data=manual, user_agent=ua
            )
        except Exception as exc:
            logger.debug("_task fetch error: %s", exc)
            return None

    if NetworkWorker is None:
        _write(
            fetch_weather(
                provider,
                lat,
                lon,
                api_key=api_key,
                manual_data=manual_data,
                user_agent=user_agent,
            )
        )
        return

    worker = NetworkWorker(
        _task, args=(lat, lon, provider, api_key, manual_data, user_agent)
    )

    def _on_finished(res: Optional[dict]) -> None:
        _write(res)

    def _on_error(exc: Exception) -> None:
        logger.debug("worker error: %s", exc)

    worker.on_finished = _on_finished
    worker.on_error = _on_error
    try:
        worker.start()
    except Exception:
        logger.debug("Could not start NetworkWorker")


def get_elevation(lat: float, lon: float) -> Optional[float]:
    if not _HAS_REQUESTS or requests is None:
        return None
    try:
        url = f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            return None
        return results[0].get("elevation")
    except Exception as exc:
        logger.debug("get_elevation failed: %s", exc)
        return None


def _safe_add_marker(
    map_obj: Any, location: Tuple[float, float], popup: Optional[str] = None
) -> None:
    if not _HAS_FOLIUM or folium is None or map_obj is None:
        return
    try:
        folium.Marker(location=location, popup=popup).add_to(map_obj)
    except Exception:
        logger.debug("_safe_add_marker failed")


def _safe_add_polyline(
    map_obj: Any, locations: List[Tuple[float, float]], **_: Any
) -> None:
    if not _HAS_FOLIUM or folium is None or map_obj is None:
        return
    try:
        folium.PolyLine(locations=locations).add_to(map_obj)
    except Exception:
        logger.debug("_safe_add_polyline failed")


class PurposeSelectionDialog:
    def __init__(self, parent: Optional[Any] = None) -> None:
        self._choice = "range"

    def get_purpose(self) -> str:
        return self._choice


BaseTerrainWidget: Type[Any] = QWidget if _HAS_QT else _StubWidget


class TerrainMapViewer(BaseTerrainWidget):
    def __init__(self, parent: Optional[Any] = None, db: Optional[Any] = None) -> None:
        if _HAS_QT:
            super().__init__(parent)
        else:
            self.parent = parent
        self.db = db
        self.map_view: Optional[Any] = None
        self.shooter_lat: Optional[Any] = None
        self.shooter_lon: Optional[Any] = None
        self.target_lat: Optional[Any] = None
        self.target_lon: Optional[Any] = None
        self.weather_display: Optional[Any] = None
        self.terrain_risk_display: Optional[Any] = None
        self.fav_list: Optional[Any] = None
        self.fav_name: Optional[Any] = None
        self.fav_note: Optional[Any] = None
        if not _HAS_QT:
            return
        self._init_ui()
        self._refresh_favorites()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("Terrain Map")
        header.setProperty("variant", "cardTitle")
        layout.addWidget(header)

        subtitle = QLabel("Coordinates, favorites, and weather for terrain planning.")
        subtitle.setProperty("variant", "cardSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        coord_group = QGroupBox("Coordinates")
        coord_group.setProperty("variant", "panel")
        coord_layout = QHBoxLayout()
        coord_group.setLayout(coord_layout)

        self.shooter_lat = QDoubleSpinBox()
        self.shooter_lat.setRange(-90, 90)
        self.shooter_lat.setDecimals(6)
        self.shooter_lat.setValue(59.9139)
        coord_layout.addWidget(QLabel("Shooter Lat"))
        coord_layout.addWidget(self.shooter_lat)

        self.shooter_lon = QDoubleSpinBox()
        self.shooter_lon.setRange(-180, 180)
        self.shooter_lon.setDecimals(6)
        self.shooter_lon.setValue(10.7522)
        coord_layout.addWidget(QLabel("Shooter Lon"))
        coord_layout.addWidget(self.shooter_lon)

        self.target_lat = QDoubleSpinBox()
        self.target_lat.setRange(-90, 90)
        self.target_lat.setDecimals(6)
        self.target_lat.setValue(59.9139)
        coord_layout.addWidget(QLabel("Target Lat"))
        coord_layout.addWidget(self.target_lat)

        self.target_lon = QDoubleSpinBox()
        self.target_lon.setRange(-180, 180)
        self.target_lon.setDecimals(6)
        self.target_lon.setValue(10.7522)
        coord_layout.addWidget(QLabel("Target Lon"))
        coord_layout.addWidget(self.target_lon)

        layout.addWidget(coord_group)

        fav_group = QGroupBox("Favorites")
        fav_group.setProperty("variant", "panel")
        fav_layout = QVBoxLayout()
        fav_group.setLayout(fav_layout)

        name_row = QHBoxLayout()
        self.fav_name = QLineEdit()
        self.fav_name.setPlaceholderText("Favorite name")
        name_row.addWidget(self.fav_name)
        self.fav_note = QLineEdit()
        self.fav_note.setPlaceholderText("Notes")
        name_row.addWidget(self.fav_note)
        fav_layout.addLayout(name_row)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save Favorite")
        btn_save.setProperty("variant", "primary")
        btn_save.clicked.connect(self._save_favorite)
        btn_row.addWidget(btn_save)
        btn_load = QPushButton("Load Favorite")
        btn_load.setProperty("variant", "ghost")
        btn_load.clicked.connect(self._load_selected_favorite)
        btn_row.addWidget(btn_load)
        btn_delete = QPushButton("Delete Favorite")
        btn_delete.setProperty("variant", "ghost")
        btn_delete.clicked.connect(self._delete_selected_favorite)
        btn_row.addWidget(btn_delete)
        fav_layout.addLayout(btn_row)

        self.fav_list = QListWidget()
        fav_layout.addWidget(self.fav_list)
        layout.addWidget(fav_group)

        self.map_view = QTextEdit()
        self.map_view.setReadOnly(True)
        self.map_view.setText("Map preview is not available in this baseline view.")
        layout.addWidget(self.map_view, 1)

        weather_row = QHBoxLayout()
        btn_weather = QPushButton("Fetch Weather")
        btn_weather.setProperty("variant", "primary")
        btn_weather.clicked.connect(self.request_weather_async)
        weather_row.addWidget(btn_weather)
        btn_terrain = QPushButton("Analyze Terrain")
        btn_terrain.setProperty("variant", "ghost")
        btn_terrain.clicked.connect(self.update_terrain_risk)
        weather_row.addWidget(btn_terrain)
        layout.addLayout(weather_row)

        self.weather_display = QTextEdit()
        self.weather_display.setReadOnly(True)
        layout.addWidget(self.weather_display)

        self.terrain_risk_display = QTextEdit()
        self.terrain_risk_display.setReadOnly(True)
        self.terrain_risk_display.setText("Terrain risk has not been analyzed yet.")
        layout.addWidget(self.terrain_risk_display)

        export_btn = QPushButton("Export PDF")
        export_btn.setProperty("variant", "ghost")
        export_btn.clicked.connect(self.export_pdf)
        layout.addWidget(export_btn)

    def _current_coords(self) -> dict[str, float]:
        if not self.shooter_lat or not self.shooter_lon:
            return {
                "shooter_lat": 0.0,
                "shooter_lon": 0.0,
                "target_lat": 0.0,
                "target_lon": 0.0,
            }
        if not self.target_lat or not self.target_lon:
            return {
                "shooter_lat": 0.0,
                "shooter_lon": 0.0,
                "target_lat": 0.0,
                "target_lon": 0.0,
            }
        return {
            "shooter_lat": float(self.shooter_lat.value()),
            "shooter_lon": float(self.shooter_lon.value()),
            "target_lat": float(self.target_lat.value()),
            "target_lon": float(self.target_lon.value()),
        }

    def _refresh_favorites(self) -> None:
        if not self.fav_list:
            return
        self.fav_list.clear()
        favs = _load_favorites()
        for item in favs:
            name = str(item.get("name", ""))
            if name:
                self.fav_list.addItem(name)

    def _selected_favorite(self) -> Optional[dict[str, Any]]:
        if not self.fav_list:
            return None
        items = self.fav_list.selectedItems()
        if not items:
            return None
        name = items[0].text()
        for item in _load_favorites():
            if item.get("name") == name:
                return item
        return None

    def _save_favorite(self) -> None:
        if not self.fav_name:
            return
        name = self.fav_name.text().strip()
        if not name:
            try:
                QMessageBox.warning(self, "Favorites", "Name is required")
            except Exception:
                pass
            return

        coords = self._current_coords()
        note = self.fav_note.text().strip() if self.fav_note else ""
        fav = {
            "name": name,
            "note": note,
            "updated": datetime.utcnow().isoformat() + "Z",
            "shooter": {
                "lat": coords["shooter_lat"],
                "lon": coords["shooter_lon"],
            },
            "target": {
                "lat": coords["target_lat"],
                "lon": coords["target_lon"],
            },
        }

        items = _load_favorites()
        replaced = False
        for idx, existing in enumerate(items):
            if existing.get("name") == name:
                items[idx] = fav
                replaced = True
                break
        if not replaced:
            items.append(fav)
        _save_favorites(items)
        self._refresh_favorites()

    def _load_selected_favorite(self) -> None:
        fav = self._selected_favorite()
        if not fav:
            return
        shooter = fav.get("shooter", {})
        target = fav.get("target", {})
        try:
            if self.shooter_lat:
                self.shooter_lat.setValue(float(shooter.get("lat", 0.0)))
            if self.shooter_lon:
                self.shooter_lon.setValue(float(shooter.get("lon", 0.0)))
            if self.target_lat:
                self.target_lat.setValue(float(target.get("lat", 0.0)))
            if self.target_lon:
                self.target_lon.setValue(float(target.get("lon", 0.0)))
            if self.fav_note:
                self.fav_note.setText(str(fav.get("note", "")))
        except Exception:
            pass

    def _delete_selected_favorite(self) -> None:
        fav = self._selected_favorite()
        if not fav:
            return
        name = fav.get("name")
        items = [item for item in _load_favorites() if item.get("name") != name]
        _save_favorites(items)
        self._refresh_favorites()

    def request_weather_async(self, api_key: Optional[str] = None) -> None:
        try:
            fetch_weather_for_viewer_async(self, api_key=api_key)
        except Exception:
            pass

    def _build_simple_terrain_profile(self) -> list[tuple[float, float, Any]]:
        coords = self._current_coords()
        points = []
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            lat = coords["shooter_lat"] + (
                (coords["target_lat"] - coords["shooter_lat"]) * fraction
            )
            lon = coords["shooter_lon"] + (
                (coords["target_lon"] - coords["shooter_lon"]) * fraction
            )
            points.append((lat, lon, get_elevation(lat, lon)))
        return points

    def update_terrain_risk(self) -> None:
        try:
            terrain_module = importlib.import_module("src.modules.terrain_map")
            analyzer = getattr(
                terrain_module, "analyze_terrain_risk_from_profile", None
            )
        except Exception:
            analyzer = None
        if not callable(analyzer):
            if self.terrain_risk_display and hasattr(
                self.terrain_risk_display, "setText"
            ):
                self.terrain_risk_display.setText(
                    "Terrain risk is not available in this view right now."
                )
            return

        profile = self._build_simple_terrain_profile()
        summary = analyzer(profile, {})
        if self.terrain_risk_display and hasattr(self.terrain_risk_display, "setText"):
            self.terrain_risk_display.setText(
                format_terrain_risk_text(summary if isinstance(summary, dict) else None)
            )

    def export_pdf(self) -> None:
        if not _HAS_QT:
            return
        try:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            default_name = f"terrain_report_{ts}.pdf"
        except Exception:
            default_name = "terrain_report.pdf"

        try:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Terrain PDF",
                default_name,
                "PDF Files (*.pdf)",
            )
        except Exception:
            path = ""

        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        coords = self._current_coords()
        fav = self._selected_favorite()
        note = ""
        if fav:
            note = str(fav.get("note", ""))

        try:
            writer = QPdfWriter(path)
            painter = QPainter(writer)
            painter.setFont(QFont("Arial", 12))
            y = 80
            lines = [
                "Terrain Export",
                f"Created: {datetime.utcnow().isoformat()}Z",
                f"Shooter Lat: {coords['shooter_lat']:.6f}",
                f"Shooter Lon: {coords['shooter_lon']:.6f}",
                f"Target Lat: {coords['target_lat']:.6f}",
                f"Target Lon: {coords['target_lon']:.6f}",
            ]
            if fav:
                lines.append(f"Favorite: {fav.get('name')}")
            if note:
                lines.append(f"Notes: {note}")

            for line in lines:
                painter.drawText(60, y, line)
                y += 20
            painter.end()
        except Exception:
            try:
                QMessageBox.warning(
                    self,
                    "Export Terrain PDF",
                    "Failed to export PDF.",
                )
            except Exception:
                pass
            return

        try:
            QMessageBox.information(
                self,
                "Export Terrain PDF",
                f"PDF created:\n{path}",
            )
        except Exception:
            pass


__all__ = [
    "TerrainMapViewer",
    "PurposeSelectionDialog",
    "_safe_add_marker",
    "_safe_add_polyline",
    "get_elevation",
    "fetch_weather_data_owm",
    "fetch_weather_data_yr",
    "fetch_weather",
    "fetch_weather_for_viewer_async",
]
