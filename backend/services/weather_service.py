import os
from typing import Dict, Any

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
    Service to fetch live meteorological observations and weather forecasts
    from Open-Meteo.
    """

    def __init__(self):
        self.base_url = os.getenv(
            "OPEN_METEO_BASE_URL",
            "https://api.open-meteo.com/v1/forecast"
        )

    # =====================================================
    # CURRENT WEATHER
    # =====================================================

    async def get_current_weather(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:

        params = {
            "latitude": lat,
            "longitude": lon,

            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "wind_speed_10m",
                "surface_pressure",
                "precipitation",
                "weather_code"
            ],

            "timezone": "auto"
        }

        try:

            async with httpx.AsyncClient(timeout=10.0) as client:

                response = await client.get(
                    self.base_url,
                    params=params
                )

                response.raise_for_status()

                data = response.json()

            current = data.get("current", {})

            temp = current.get(
                "temperature_2m",
                0.0
            )

            humidity = current.get(
                "relative_humidity_2m",
                0.0
            )

            # Calculate thermal stress
            thermal_metrics = (
                ThermalStressService
                .get_thermal_stress_summary(
                    temp,
                    humidity
                )
            )

            return {

                "latitude": lat,

                "longitude": lon,

                "timezone":
                    data.get(
                        "timezone",
                        "UTC"
                    ),

                "time":
                    current.get("time"),

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
                    thermal_metrics
            }

        except Exception as e:

            # Offline fallback

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

                "status":
                    "fallback_offline_data",

                "error":
                    str(e),

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

        params = {

            "latitude": lat,

            "longitude": lon,

            # Daily forecast
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "precipitation_sum",
                "wind_speed_10m_max"
            ],

            # Hourly forecast
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature"
            ],

            "forecast_days":
                min(
                    max(days, 1),
                    14
                ),

            "timezone":
                "auto"
        }

        try:

            async with httpx.AsyncClient(
                timeout=10.0
            ) as client:

                response = await client.get(
                    self.base_url,
                    params=params
                )

                response.raise_for_status()

                data = response.json()

            daily_data = data.get(
                "daily",
                {}
            )

            hourly_data = data.get(
                "hourly",
                {}
            )

            # IMPORTANT:
            # We now return BOTH daily and hourly data.
            return {

                "latitude": lat,

                "longitude": lon,

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

        except Exception as e:

            return {

                "latitude": lat,

                "longitude": lon,

                "timezone": "UTC",

                "status":
                    "error_fetching_forecast",

                "error":
                    str(e),

                "daily": {},

                "hourly": {}
            }