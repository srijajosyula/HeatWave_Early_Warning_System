from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..services.weather_service import WeatherService
from ..services.thermal_stress_service import ThermalStressService

router = APIRouter(prefix="/api/weather", tags=["Weather & Thermal Stress"])
weather_service = WeatherService()


@router.get("/current", summary="Get Current Weather and Thermal Stress")
async def get_current_weather(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees", example=28.6139),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees", example=77.2090)
):
    """
    Fetches real-time weather observations for given coordinates and computes
    associated thermal stress indices (Heat Index, Wet-Bulb, Humidex).
    """
    try:
        data = await weather_service.get_current_weather(lat=lat, lon=lon)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")


@router.get("/forecast", summary="Get Weather Forecast")
async def get_weather_forecast(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees", example=28.6139),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees", example=77.2090),
    days: int = Query(7, ge=1, le=14, description="Forecast horizon in days")
):
    """
    Fetches multi-day weather forecast with temperature and thermal metrics.
    """
    try:
        data = await weather_service.get_forecast(lat=lat, lon=lon, days=days)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast: {str(e)}")


@router.get("/thermal-stress", summary="Compute Thermal Stress from Custom Values")
async def compute_thermal_stress(
    temperature_c: float = Query(..., ge=-30.0, le=65.0, description="Temperature in Celsius", example=42.0),
    relative_humidity: float = Query(..., ge=0.0, le=100.0, description="Relative humidity percentage", example=55.0)
):
    """
    Calculates Heat Index, Wet-Bulb temperature, and Humidex directly from custom temperature & humidity inputs.
    """
    return ThermalStressService.get_thermal_stress_summary(temperature_c, relative_humidity)
