import os
import asyncio
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

    try:

        async with httpx.AsyncClient(timeout=15.0) as client:

            response = await client.get(
                self.base_url,
                params=params
            )

            response.raise_for_status()

            data = response.json()

        current = data.get("current", {})

        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")

        if temp is None or humidity is None:
            raise Exception("Open-Meteo returned incomplete weather data")

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
            "timezone": data.get("timezone", "UTC"),
            "time": current.get("time"),

            "temperature_c": temp,
            "relative_humidity": humidity,

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

            "status": "success"
        }

    except Exception as e:

        print(
            f"Weather API error for "
            f"{lat}, {lon}: {e}"
        )

        # Safe fallback so dashboard still works
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

            "status": "fallback_offline_data",

            "error": str(e),

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

            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "precipitation_sum",
                "wind_speed_10m_max"
            ]),

            "hourly": ","([
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature"
            ]),

            "forecast_days":
                min(
                    max(days, 1),
                    14
                ),

            "timezone": "auto"
        }

        last_error = None

        # Retry up to 3 times
        for attempt in range(3):

            try:

                async with httpx.AsyncClient(
                    timeout=20.0
                ) as client:

                    response = await client.get(
                        self.base_url,
                        params=params
                    )

                    # Handle rate limiting
                    if response.status_code == 429:

                        last_error = (
                            "Open-Meteo rate limit reached"
                        )

                        if attempt < 2:
                            await asyncio.sleep(
                                2 * (attempt + 1)
                            )
                            continue

                        raise Exception(last_error)

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

                if not hourly_data:
                    raise Exception(
                        "No hourly forecast data available"
                    )

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

                last_error = str(e)

                if attempt < 2:
                    await asyncio.sleep(
                        1 * (attempt + 1)
                    )
                    continue

        # =================================================
        # FORECAST ERROR
        # =================================================

        return {

            "latitude": lat,

            "longitude": lon,

            "timezone": "UTC",

            "status":
                "foracast_unavailable",

            "error":
                last_error or
                "Unable to fetch forecast",

            "daily": {},

            "hourly": {}
        }
