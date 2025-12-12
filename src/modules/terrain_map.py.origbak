from __future__ import annotations

"""Compact, import-safe baseline for terrain_map helpers.

This file is a clean baseline used for triage and unit tests. It keeps
heavy GUI/network dependencies optional so CI and linters can import
it without PyQt or folium installed. Use this as the canonical
implementation while we surgically fix `terrain_map.py`.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

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

# Avoid importing PyQt types here; this baseline is import-safe in CI/headless.

try:
    from HjemmeladingApp.utils.safe_logger import append_exception  # type: ignore
except Exception:

    def append_exception(msg: str = "", exc: BaseException | None = None, app_name: str = "") -> None:  # type: ignore
        return None


try:
    from src.modules.network import NetworkWorker  # type: ignore
except Exception:
    NetworkWorker = None  # type: ignore

_weather_cache: Dict[Tuple[float, float], dict] = {}


def _cache_key(lat: float, lon: float) -> Tuple[float, float]:
    return (round(float(lat), 5), round(float(lon), 5))


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


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


def fetch_weather_for_viewer_async(
    viewer: "TerrainMapViewer", api_key: Optional[str] = None
) -> None:
    if not _HAS_REQUESTS:
        return

    # Defensively obtain getter callables for shooter_lat/shooter_lon so
    # static type checkers don't warn about calling methods on None.
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

    if NetworkWorker is None:
        _write(fetch_weather_data_owm(lat, lon, api_key))
        return

    def _task(a: float, b: float, key: Optional[str] = None) -> Optional[dict]:
        return fetch_weather_data_owm(a, b, key)

    worker = NetworkWorker(_task, args=(lat, lon, api_key))

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


class TerrainMapViewer:
    def __init__(self, parent: Optional[Any] = None, db: Optional[Any] = None) -> None:
        self.parent = parent
        self.db = db
        self.map_view: Optional[Any] = None
        self.shooter_lat: Optional[Any] = None
        self.shooter_lon: Optional[Any] = None
        self.weather_display: Optional[Any] = None

    def request_weather_async(self, api_key: Optional[str] = None) -> None:
        try:
            fetch_weather_for_viewer_async(self, api_key=api_key)
        except Exception:
            pass


__all__ = [
    "TerrainMapViewer",
    "PurposeSelectionDialog",
    "_safe_add_marker",
    "_safe_add_polyline",
    "get_elevation",
    "fetch_weather_data_owm",
    "fetch_weather_for_viewer_async",
]
