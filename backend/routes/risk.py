from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ..services.ml_service import MLService
from ..services.thermal_stress_service import ThermalStressService


router = APIRouter(
    prefix="/api/risk",
    tags=["HeatWave Risk & ML Inference"]
)

ml_service = MLService()


class ZoneRiskRequest(BaseModel):

    zone_id: str = Field(
        ...,
        description="Identifier of the administrative zone or ward"
    )

    zone_name: Optional[str] = Field(
        "North Zone",
        description="Name of the zone or city"
    )

    temperature_c: float = Field(
        ...,
        description="Air temperature in Celsius"
    )

    humidity_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Relative humidity percentage"
    )

    wind_speed_kmh: float = Field(
        ...,
        ge=0,
        description="Wind speed in km/h"
    )

    solar_radiation_wm2: float = Field(
        ...,
        ge=0,
        description="Solar radiation in W/m²"
    )

    elderly_density: float = Field(
        ...,
        ge=0,
        description="Density/proportion of elderly population"
    )

    outdoor_worker_density: float = Field(
        ...,
        ge=0,
        description="Density/proportion of outdoor workers"
    )

    population_density: float = Field(
        ...,
        ge=0,
        description="Population density"
    )

    healthcare_access: float = Field(
        ...,
        ge=0,
        description="Healthcare access indicator"
    )

    additional_features: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional optional features"
    )


@router.get(
    "/model-status",
    summary="Check ML Model Readiness"
)
async def get_ml_model_status():

    return ml_service.get_status()


@router.post(
    "/predict",
    summary="Predict Zone Heatwave Health Risk"
)
async def predict_zone_risk(request: ZoneRiskRequest):

    # ==========================================
    # 1. CALCULATE THERMAL STRESS
    # ==========================================

    thermal_result = ThermalStressService.get_thermal_stress_summary(
        temperature_c=request.temperature_c,
        relative_humidity=request.humidity_percent,
        wind_speed_kmh=request.wind_speed_kmh,
        solar_radiation_wm2=request.solar_radiation_wm2
    )

    # ==========================================
    # 2. PREPARE FEATURES FOR ML MODEL
    # ==========================================

    features_dict = {
        "temperature_c": request.temperature_c,
        "humidity_percent": request.humidity_percent,
        "wind_speed_kmh": request.wind_speed_kmh,
        "solar_radiation_wm2": request.solar_radiation_wm2,
        "elderly_density": request.elderly_density,
        "outdoor_worker_density": request.outdoor_worker_density,
        "population_density": request.population_density,
        "healthcare_access": request.healthcare_access,

        # WBGT calculated by ThermalStressService
        "wbgt": thermal_result["wbgt_c"]
    }

    # Add any optional custom features
    if request.additional_features:
        features_dict.update(request.additional_features)

    # ==========================================
    # 3. RUN ML MODEL
    # ==========================================

    ml_result = ml_service.predict_zone_risk(features_dict)

    # ==========================================
    # 4. RETURN COMPLETE RESULT
    # ==========================================

    return {
        "zone_id": request.zone_id,
        "zone_name": request.zone_name,

        "thermal_stress": thermal_result,

        "ml_inference_result": ml_result
    }