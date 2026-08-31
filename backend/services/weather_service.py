import os
import asyncio
import time
from typing import Dict, Any, Optional

try:
    import httpx
except ImportError:
    httpx = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .thermal_stress_service import ThermalStressService


class WeatherService:
    """
    Service to fetch current weather and weather forecasts
    from Open-Meteo.

    Includes simple in-memory caching to reduce repeated
    API requests and avoid Open-Meteo rate limits.
    """

    def __init__(self):
        self.base_url = os.getenv(
            "OPEN_METEO_BASE_URL",
            "https://api.open-meteo.com/v1/forecast"
        )

        # Cache storage
        self.current_cache: Dict[str, Any] = {}
        self.forecast_cache: Dict[str, Any] = {}

        # Cache duration in seconds
        self.current_cache_duration = 600       # 10 minutes
        self.forecast_cache_duration = 1800     # 30 minutes

    # =====================================================
    # CACHE HELPERS
    # =====================================================

    def _location_key(self, lat: float, lon: float) -> str:
        """
        Creates a consistent cache key for a location.
        """
        return f"{round(lat, 4)}_{round(lon, 4)}"

    def _get_cached(
        self,
        cache: Dict[str, Any],
        key: str,
        duration: int
    ) -> Optional[Dict[str, Any]]:
        """
        Returns cached data if it is still valid.
        """
        cached = cache.get(key)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age < duration:
            return cached["data"]

        # Remove expired cache
        cache.pop(key, None)

        return None

    def _save_cache(
        self,
        cache: Dict[str, Any],
        key: str,
        data: Dict[str, Any]
    ):
        """
        Saves data into cache.
        """
        cache[key] = {
            "timestamp": time.time(),
            "data": data
        }

    # =====================================================
    # CURRENT WEATHER
    # =====================================================

    async def get_current_weather(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:

        if httpx is None:
            return self._current_fallback(
                lat,
                lon,
                "httpx library is not installed"
            )

        cache_key = self._location_key(lat, lon)

        # -------------------------------------------------
        # CHECK CACHE
        # -------------------------------------------------

        cached_data = self._get_cached(
            self.current_cache,
            cache_key,
            self.current_cache_duration
        )

        if cached_data:
            cached_copy = dict(cached_data)
            cached_copy["status"] = "success_cached"
            return cached_copy

        # -------------------------------------------------
        # OPEN-METEO PARAMETERS
        # -------------------------------------------------

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "wind_speed_10m,"
                "surface_pressure,"
                "precipitation,"
                "weather_code"
            ),
            "timezone": "auto"
        }

        # -------------------------------------------------
        # API REQUEST
        # -------------------------------------------------

        try:

            async with httpx.AsyncClient(
                timeout=15.0
            ) as client:

                response = await client.get(
                    self.base_url,
                    params=params
                )

                # Rate limit
                if response.status_code == 429:

                    raise Exception(
                        "Open-Meteo rate limit reached (429)"
                    )

                response.raise_for_status()

                data = response.json()

            current = data.get(
                "current",
                {}
            )

            temp = current.get(
                "temperature_2m"
            )

            humidity = current.get(
                "relative_humidity_2m"
            )

            if temp is None or humidity is None:

                raise Exception(
                    "Open-Meteo returned incomplete weather data"
                )

            # -------------------------------------------------
            # THERMAL STRESS
            # -------------------------------------------------

            thermal_metrics = (
                ThermalStressService
                .get_thermal_stress_summary(
                    temp,
                    humidity
                )
            )

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            result = {

                "latitude": lat,

                "longitude": lon,

                "timezone":
                    data.get(
                        "timezone",
                        "UTC"
                    ),

                "time":
                    current.get(
                        "time"
                    ),

                "temperature_c":
                    temp,

                "relative_humidity":
                    humidity,

                "apparent_temperature_c":
                    current.get(
                        "apparent_temperature",
                        temp
                    ),

                "wind_speed_kmh":
                    current.get(
                        "wind_speed_10m",
                        0.0
                    ),

                "surface_pressure_hpa":
                    current.get(
                        "surface_pressure",
                        1013.25
                    ),

                "precipitation_mm":
                    current.get(
                        "precipitation",
                        0.0
                    ),

                "weather_code":
                    current.get(
                        "weather_code",
                        0
                    ),

                "thermal_stress":
                    thermal_metrics,

                "status":
                    "success"
            }

            # -------------------------------------------------
            # SAVE TO CACHE
            # -------------------------------------------------

            self._save_cache(
                self.current_cache,
                cache_key,
                result
            )

            return result

        except Exception as e:

            print(
                f"Weather API error for "
                f"{lat}, {lon}: {e}"
            )

            # -------------------------------------------------
            # CHECK OLD CACHE BEFORE FALLBACK
            # -------------------------------------------------

            old_cache = self.current_cache.get(
                cache_key
            )

            if old_cache:

                stale_data = dict(
                    old_cache["data"]
                )

                stale_data["status"] = (
                    "stale_cached_data"
                )

                stale_data["error"] = str(e)

                return stale_data

            # -------------------------------------------------
            # FALLBACK
            # -------------------------------------------------

            return self._current_fallback(
                lat,
                lon,
                str(e)
            )

    # =====================================================
    # CURRENT WEATHER FALLBACK
    # =====================================================

    def _current_fallback(
        self,
        lat: float,
        lon: float,
        error_message: str
    ) -> Dict[str, Any]:

        # Development fallback values
        temp_fallback = 35.0
        rh_fallback = 50.0

        thermal_metrics = (
            ThermalStressService
            .get_thermal_stress_summary(
                temp_fallback,
                rh_fallback
            )
        )

        return {

            "latitude": lat,

            "longitude": lon,

            "timezone": "UTC",

            "time": None,

            "status":
                "fallback_offline_data",

            "error":
                error_message,

            "temperature_c":
                temp_fallback,

            "relative_humidity":
                rh_fallback,

            "apparent_temperature_c":
                temp_fallback + 2.0,

            "wind_speed_kmh":
                12.0,

            "surface_pressure_hpa":
                1010.0,

            "precipitation_mm":
                0.0,

            "weather_code":
                0,

            "thermal_stress":
                thermal_metrics
        }

    # =====================================================
    # WEATHER FORECAST
    # =====================================================

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7
    ) -> Dict[str, Any]:

        if httpx is None:
            return self._forecast_fallback(
                lat,
                lon,
                "httpx library is not installed"
            )

        cache_key = (
            f"{self._location_key(lat, lon)}"
            f"_{min(max(days, 1), 14)}"
        )

        # -------------------------------------------------
        # CHECK CACHE
        # -------------------------------------------------

        cached_data = self._get_cached(
            self.forecast_cache,
            cache_key,
            self.forecast_cache_duration
        )

        if cached_data:

            cached_copy = dict(
                cached_data
            )

            cached_copy["status"] = (
                "success_cached"
            )

            return cached_copy

        # -------------------------------------------------
        # FORECAST PARAMETERS
        # -------------------------------------------------

        forecast_days = min(
            max(days, 1),
            14
        )

        params = {

            "latitude":
                lat,

            "longitude":
                lon,

            "daily":
                ",".join([
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "apparent_temperature_max",
                    "precipitation_sum",
                    "wind_speed_10m_max"
                ]),

            "hourly":
                ",".join([
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature"
                ]),

            "forecast_days":
                forecast_days,

            "timezone":
                "auto"
        }

        last_error = None

        # -------------------------------------------------
        # RETRY UP TO 3 TIMES
        # -------------------------------------------------

        for attempt in range(3):

            try:

                async with httpx.AsyncClient(
                    timeout=20.0
                ) as client:

                    response = await client.get(
                        self.base_url,
                        params=params
                    )

                    # -------------------------------------------------
                    # RATE LIMIT
                    # -------------------------------------------------

                    if response.status_code == 429:

                        last_error = (
                            "Open-Meteo rate limit reached (429)"
                        )

                        if attempt < 2:

                            await asyncio.sleep(
                                5 * (attempt + 1)
                            )

                            continue

                        raise Exception(
                            last_error
                        )

                    response.raise_for_status()

                    data = response.json()

                # -------------------------------------------------
                # EXTRACT DATA
                # -------------------------------------------------

                daily_data = data.get(
                    "daily",
                    {}
                )

                hourly_data = data.get(
                    "hourly",
                    {}
                )

                if not hourly_data:

                    raise Exception(
                        "No hourly forecast data available"
                    )

                # -------------------------------------------------
                # RESULT
                # -------------------------------------------------

                result = {

                    "latitude":
                        lat,

                    "longitude":
                        lon,

                    "timezone":
                        data.get(
                            "timezone",
                            "UTC"
                        ),

                    "daily":
                        daily_data,

                    "hourly":
                        hourly_data,

                    "status":
                        "success"
                }

                # -------------------------------------------------
                # SAVE TO CACHE
                # -------------------------------------------------

                self._save_cache(
                    self.forecast_cache,
                    cache_key,
                    result
                )

                return result

            except Exception as e:

                last_error = str(e)

                print(
                    f"Forecast API attempt "
                    f"{attempt + 1} failed: "
                    f"{last_error}"
                )

                if attempt < 2:

                    await asyncio.sleep(
                        3 * (attempt + 1)
                    )

        # -------------------------------------------------
        # CHECK OLD FORECAST CACHE
        # -------------------------------------------------

        old_cache = self.forecast_cache.get(
            cache_key
        )

        if old_cache:

            stale_data = dict(
                old_cache["data"]
            )

            stale_data["status"] = (
                "stale_cached_data"
            )

            stale_data["error"] = (
                last_error or
                "Forecast temporarily unavailable"
            )

            return stale_data

        # -------------------------------------------------
        # FORECAST FALLBACK
        # -------------------------------------------------

        return self._forecast_fallback(
            lat,
            lon,
            last_error or
            "Unable to fetch forecast"
        )

    # =====================================================
    # FORECAST FALLBACK
    # =====================================================

    def _forecast_fallback(
        self,
        lat: float,
        lon: float,
        error_message: str
    ) -> Dict[str, Any]:

        return {

            "latitude":
                lat,

            "longitude":
                lon,

            "timezone":
                "UTC",

            "status":
                "forecast_unavailable",

            "error":
                error_message,

            "daily":
                {},

            "hourly":
                {}
        }
