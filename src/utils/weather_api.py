"""
Multi-Weather API Service
Integrerer flere værdata-kilder med automatisk fallback
"""

from datetime import datetime
from typing import Dict, List, Optional

import requests  # type: ignore[import-untyped]
from src.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


class WeatherAPIService:
    """Håndterer flere vær-APIer med fallback"""

    def __init__(self):
        """Initialiserer service"""
        # API keys (sett opp i settings)
        self.openweathermap_key = ""  # Gratis: https://openweathermap.org/api
        self.weatherapi_key = ""  # Gratis: https://www.weatherapi.com/

        # Priority order (Yr.no først siden den er best for Norge)
        self.providers = ["yr.no", "openweathermap", "weatherapi"]

    def get_weather(self, lat: float, lon: float) -> Dict:
        """
        Henter værdata fra beste tilgjengelige kilde
        Prøver kilder i rekkefølge til en fungerer
        """
        errors = []

        for provider in self.providers:
            try:
                if provider == "yr.no":
                    data = self._get_yrno(lat, lon)
                elif provider == "openweathermap" and self.openweathermap_key:
                    data = self._get_openweathermap(lat, lon)
                elif provider == "weatherapi" and self.weatherapi_key:
                    data = self._get_weatherapi(lat, lon)
                else:
                    continue

                if data:
                    data["source"] = provider
                    return data

            except Exception as e:
                errors.append(f"{provider}: {str(e)}")
                continue

        # Ingen kilder fungerte
        return {
            "error": True,
            "message": "Alle vær-kilder feilet:\n" + "\n".join(errors),
        }

    def _get_yrno(self, lat: float, lon: float) -> Optional[Dict]:
        """Henter data fra Yr.no (Meteorologisk Institutt)"""
        url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
        params = {"lat": lat, "lon": lon}
        headers = {
            "User-Agent": "ReloadingWorkshopManager/1.0 (https://github.com/yourusername)"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        current = data["properties"]["timeseries"][0]["data"]["instant"]["details"]

        return {
            "temperature": current.get("air_temperature"),
            "pressure": current.get("air_pressure_at_sea_level"),
            "humidity": current.get("relative_humidity"),
            "wind_speed": current.get("wind_speed"),
            "wind_direction": current.get("wind_from_direction"),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_openweathermap(self, lat: float, lon: float) -> Optional[Dict]:
        """Henter data fra OpenWeatherMap"""
        if not self.openweathermap_key:
            return None

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.openweathermap_key,
            "units": "metric",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "temperature": data["main"]["temp"],
            "pressure": data["main"]["pressure"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "wind_direction": data["wind"].get("deg", 0),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_weatherapi(self, lat: float, lon: float) -> Optional[Dict]:
        """Henter data fra WeatherAPI.com"""
        if not self.weatherapi_key:
            return None

        url = "http://api.weatherapi.com/v1/current.json"
        params = {"key": self.weatherapi_key, "q": f"{lat},{lon}", "aqi": "no"}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        current = data["current"]

        return {
            "temperature": current["temp_c"],
            "pressure": current["pressure_mb"],
            "humidity": current["humidity"],
            "wind_speed": current["wind_kph"] / 3.6,  # Convert to m/s
            "wind_direction": current["wind_degree"],
            "timestamp": datetime.now().isoformat(),
        }

    def set_api_keys(
        self, openweathermap: Optional[str] = None, weatherapi: Optional[str] = None
    ) -> None:
        """Setter API-nøkler"""
        if openweathermap:
            self.openweathermap_key = openweathermap
        if weatherapi:
            self.weatherapi_key = weatherapi

    def get_forecast(
        self, lat: float, lon: float, hours: int = 48
    ) -> Optional[List[Dict]]:
        """
        Henter værvarsling for neste X timer
        Kun Yr.no støtter dette gratis
        """
        try:
            url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
            params = {"lat": lat, "lon": lon}
            headers = {"User-Agent": "ReloadingWorkshopManager/1.0"}

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            timeseries = data["properties"]["timeseries"][:hours]

            forecast = []
            for entry in timeseries:
                instant = entry["data"]["instant"]["details"]
                forecast.append(
                    {
                        "time": entry["time"],
                        "temperature": instant.get("air_temperature"),
                        "pressure": instant.get("air_pressure_at_sea_level"),
                        "humidity": instant.get("relative_humidity"),
                        "wind_speed": instant.get("wind_speed"),
                        "wind_direction": instant.get("wind_from_direction"),
                    }
                )

            return forecast

        except Exception as e:
            logger.error("Forecast error: %s", e)
            return None

    def compare_sources(self, lat: float, lon: float) -> Dict:
        """
        Sammenligner data fra alle tilgjengelige kilder
        Nyttig for å se hvor store avvik det er
        """
        results = {}

        for provider in self.providers:
            try:
                if provider == "yr.no":
                    results[provider] = self._get_yrno(lat, lon)
                elif provider == "openweathermap" and self.openweathermap_key:
                    results[provider] = self._get_openweathermap(lat, lon)
                elif provider == "weatherapi" and self.weatherapi_key:
                    results[provider] = self._get_weatherapi(lat, lon)
            except Exception as e:
                logger.debug(
                    "Weather provider '%s' failed: %s", provider, e, exc_info=True
                )
                try:
                    from HjemmeladingApp.utils.safe_logger import append_exception

                    append_exception(f"Weather provider {provider} failed", e)
                except Exception:
                    pass
                results[provider] = None

        return results


# Global instance
_weather_service = None


def get_weather_service() -> WeatherAPIService:
    """Returnerer singleton weather service"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherAPIService()
    return _weather_service
