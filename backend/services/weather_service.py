import os
import asyncio
from datetime import datetime, timedelta
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
    Service to fetch current weather and weather forecasts
    from Open-Meteo.

    Includes:
    - Current weather
    - Thermal stress calculation
    - Forecast caching
    - Retry handling
    - Rate-limit protection
    - Fallback forecast data
    """

    # Cache forecast results in memory
    _forecast_cache = {}

    # Cache lifetime in seconds
    CACHE_DURATION = 900  # 15 minutes

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

            if httpx is None:
                raise Exception(
                    "httpx package is not installed"
                )

            async with httpx.AsyncClient(
                timeout=15.0
            ) as client:

                response = await client.get(
                    self.base_url,
                    params=params
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
                    thermal_metrics,

                "status":
                    "success"
            }

        except Exception as e:

            print(
                f"Weather API error for "
                f"{lat}, {lon}: {e}"
            )

            # =================================================
            # SAFE CURRENT WEATHER FALLBACK
            # =================================================

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

                "latitude":
                    lat,

                "longitude":
                    lon,

                "timezone":
                    "UTC",

                "time":
                    None,

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

        forecast_days = min(
            max(days, 1),
            14
        )

        # Round coordinates slightly for cache consistency
        cache_key = (
            round(lat, 3),
            round(lon, 3),
            forecast_days
        )

        # =================================================
        # CHECK CACHE
        # =================================================

        cached = self._forecast_cache.get(
            cache_key
        )

        if cached:

            cached_time = cached.get(
                "cached_at"
            )

            if cached_time:

                age = (
                    datetime.utcnow()
                    - cached_time
                ).total_seconds()

                if age < self.CACHE_DURATION:

                    print(
                        "Using cached forecast "
                        f"for {lat}, {lon}"
                    )

                    return cached["data"]

        # =================================================
        # FORECAST PARAMETERS
        # =================================================

        params = {

            "latitude":
                lat,

            "longitude":
                lon,

            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "precipitation_sum",
                "wind_speed_10m_max"
            ]),

            "hourly": ",".join([
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

        # =================================================
        # TRY OPEN-METEO
        # =================================================

        for attempt in range(3):

            try:

                if httpx is None:
                    raise Exception(
                        "httpx package is not installed"
                    )

                print(
                    f"Requesting Open-Meteo forecast "
                    f"(attempt {attempt + 1}/3)"
                )

                async with httpx.AsyncClient(
                    timeout=20.0
                ) as client:

                    response = await client.get(
                        self.base_url,
                        params=params
                    )

                    # -----------------------------------------
                    # RATE LIMIT
                    # -----------------------------------------

                    if response.status_code == 429:

                        last_error = (
                            "Open-Meteo rate limit reached (429)"
                        )

                        print(
                            last_error
                        )

                        # If we have an older cached result,
                        # use it instead of making more requests.
                        if cached:

                            print(
                                "Using older cached "
                                "forecast because of rate limit."
                            )

                            return cached["data"]

                        if attempt < 2:

                            await asyncio.sleep(
                                5 * (attempt + 1)
                            )

                            continue

                        break

                    # -----------------------------------------
                    # OTHER HTTP ERRORS
                    # -----------------------------------------

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

                # -----------------------------------------
                # VALIDATE HOURLY DATA
                # -----------------------------------------

                hourly_times = hourly_data.get(
                    "time",
                    []
                )

                hourly_temperatures = (
                    hourly_data.get(
                        "temperature_2m",
                        []
                    )
                )

                if (
                    not hourly_times
                    or not hourly_temperatures
                ):

                    raise Exception(
                        "No hourly forecast data available"
                    )

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

                # =================================================
                # SAVE SUCCESSFUL FORECAST TO CACHE
                # =================================================

                self._forecast_cache[
                    cache_key
                ] = {

                    "cached_at":
                        datetime.utcnow(),

                    "data":
                        result
                }

                print(
                    "Forecast successfully fetched "
                    "and cached."
                )

                return result

            except Exception as e:

                last_error = str(e)

                print(
                    f"Forecast attempt "
                    f"{attempt + 1} failed: {e}"
                )

                if attempt < 2:

                    await asyncio.sleep(
                        3 * (attempt + 1)
                    )

        # =====================================================
        # USE FALLBACK FORECAST
        # =====================================================

        print(
            "Using fallback forecast data."
        )

        fallback = (
            self._generate_fallback_forecast(
                lat,
                lon,
                forecast_days,
                last_error
            )
        )

        return fallback

    # =====================================================
    # FALLBACK FORECAST
    # =====================================================

    def _generate_fallback_forecast(
        self,
        lat: float,
        lon: float,
        days: int,
        error_message: str = None
    ) -> Dict[str, Any]:
        """
        Generates a simple forecast when Open-Meteo
        is temporarily unavailable.

        This keeps the dashboard functional and
        prevents the temperature chart from being blank.
        """

        now = datetime.utcnow()

        hourly_times = []
        hourly_temperatures = []
        hourly_humidity = []
        hourly_apparent = []

        # Generate enough hours for the requested days
        total_hours = days * 24

        for hour in range(total_hours):

            timestamp = (
                now +
                timedelta(hours=hour)
            )

            # Simple temperature pattern
            # Daily variation between approximately
            # 30°C and 38°C.
            hour_of_day = timestamp.hour

            if 6 <= hour_of_day <= 15:

                temperature = (
                    32.0 +
                    (
                        (hour_of_day - 6)
                        / 9
                    ) * 6.0
                )

            elif 16 <= hour_of_day <= 20:

                temperature = (
                    38.0 -
                    (
                        (hour_of_day - 16)
                        / 4
                    ) * 4.0
                )

            else:

                temperature = 30.0

            humidity = 50.0

            apparent_temperature = (
                temperature + 2.0
            )

            hourly_times.append(
                timestamp.strftime(
                    "%Y-%m-%dT%H:%M"
                )
            )

            hourly_temperatures.append(
                round(
                    temperature,
                    1
                )
            )

            hourly_humidity.append(
                humidity
            )

            hourly_apparent.append(
                round(
                    apparent_temperature,
                    1
                )
            )

        # =================================================
        # DAILY FALLBACK
        # =================================================

        daily_times = []
        daily_max = []
        daily_min = []
        daily_apparent_max = []
        daily_precipitation = []
        daily_wind = []

        for day in range(days):

            date = (
                now +
                timedelta(days=day)
            )

            daily_times.append(
                date.strftime(
                    "%Y-%m-%d"
                )
            )

            daily_max.append(
                38.0
            )

            daily_min.append(
                30.0
            )

            daily_apparent_max.append(
                40.0
            )

            daily_precipitation.append(
                0.0
            )

            daily_wind.append(
                12.0
            )

        return {

            "latitude":
                lat,

            "longitude":
                lon,

            "timezone":
                "UTC",

            "status":
                "fallback_forecast",

            "error":
                error_message or
                "Open-Meteo forecast unavailable",

            "daily": {

                "time":
                    daily_times,

                "temperature_2m_max":
                    daily_max,

                "temperature_2m_min":
                    daily_min,

                "apparent_temperature_max":
                    daily_apparent_max,

                "precipitation_sum":
                    daily_precipitation,

                "wind_speed_10m_max":
                    daily_wind
            },

            "hourly": {

                "time":
                    hourly_times,

                "temperature_2m":
                    hourly_temperatures,

                "relative_humidity_2m":
                    hourly_humidity,

                "apparent_temperature":
                    hourly_apparent
            }
        }
