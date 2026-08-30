from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from ..services.alert_service import AlertService
from ..services.thermal_stress_service import ThermalStressService

router = APIRouter(prefix="/api/alerts", tags=["Early Warning Alerts & Advisories"])


class AlertEvaluationRequest(BaseModel):
    zone_name: str = Field("Central District", example="Central District")
    temperature_c: float = Field(..., example=43.0, description="Ambient temperature in °C")
    relative_humidity: float = Field(..., example=55.0, description="Relative humidity in %")
    heat_index_c: Optional[float] = Field(None, example=52.4, description="Optional precomputed Heat Index")


@router.post("/evaluate", summary="Evaluate Alert Tier and Advisories")
async def evaluate_alert(request: AlertEvaluationRequest):
    """
    Evaluates weather metrics and returns actionable heatwave alert tiers
    (Green, Yellow, Orange, Red) alongside tailored advisories for the public,
    vulnerable groups, and outdoor laborers.
    """
    # If heat index not provided, calculate it
    heat_index = request.heat_index_c
    if heat_index is None:
        heat_index = ThermalStressService.calculate_heat_index(request.temperature_c, request.relative_humidity)

    evaluation = AlertService.evaluate_alert(
        temperature_c=request.temperature_c,
        heat_index_c=heat_index,
        zone_name=request.zone_name
    )
    return evaluation


@router.get("/active", summary="Get Active Heatwave Alerts")
async def get_active_alerts():
    """
    Returns active heatwave warnings across monitored zones.
    """
    # Sample active alerts for demo/hackathon display
    return {
        "count": 1,
        "active_alerts": [
            {
                "zone_id": "zone_sample_01",
                "zone_name": "Demo Metropolitan Area",
                "alert_level": "ORANGE",
                "severity": "HIGH",
                "color_code": "#F97316",
                "effective_from": "2026-08-29T10:00:00Z",
                "expires_at": "2026-08-29T18:00:00Z",
                "message": "Heatwave Warning: Temperatures expected to exceed 42°C with high thermal stress."
            }
        ]
    }
