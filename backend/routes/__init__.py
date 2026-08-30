"""API routes package for HeatWave Early Warning System."""
from .weather import router as weather_router
from .risk import router as risk_router
from .alerts import router as alerts_router

__all__ = ["weather_router", "risk_router", "alerts_router"]
