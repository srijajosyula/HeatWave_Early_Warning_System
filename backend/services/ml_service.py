import os
import joblib
from pathlib import Path
from typing import Dict, Any, Optional


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class MLService:
    """
    Service responsible for loading and running inference on the trained ML HeatWave
    health-risk model developed by the data science team member.
    
    Adheres to strict principles:
    - Zero fake predictions.
    - Gracefully communicates model readiness state.
    - Isolated from API routes and mathematical thermal calculations.
    """

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = str(Path(__file__).resolve().parents[2]/ "models"/ "heatwave_health_model.pkl")

        self.model_path = Path(model_path)
        self.model = None

        print(f"[MLService] Looking for model at: {self.model_path}")
        print(f"[MLService] Model exists: {self.model_path.is_file()}")

        self._load_model_if_present()

    def _load_model_if_present(self) -> None:
        """
        Attempts to load model artifact if the file exists on disk.
        """
        if self.model_path.is_file():
            try:
                self.model = joblib.load(self.model_path)
                print(f"[MLService] Model loaded successfully!")
                # Placeholder for loading Scikit-Learn / Joblib / PyTorch model
            except Exception as e:
                self.model = None
                print(f"[MLService] Model file found at {self.model_path} but failed to load: {e}")
        else:
            self.model = None

    def is_model_loaded(self) -> bool:
        """Returns True only if a real ML model artifact is loaded in memory."""
        return self.model is not None

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current readiness status of the ML model.
        """
        file_exists = self.model_path.is_file()
        return {
            "model_ready": self.is_model_loaded(),
            "model_file_exists": file_exists,
            "model_path": str(self.model_path),
            "status": "ready" if self.is_model_loaded() else "pending_model_artifact",
            "message": (
                "ML model is loaded and ready for inference."
                if self.is_model_loaded()
                else "No ML model loaded. Place your teammate's trained model file in the 'models/' directory to enable ML-based risk predictions."
            )
        }

    def predict_zone_risk(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the trained Random Forest model and returns
        a health-risk score from 0 to 100 with a risk category.
        """

        if not self.is_model_loaded():
            return {
                "success": False,
                "error": "ML_MODEL_NOT_LOADED",
                "message": "The machine learning risk model has not been loaded.",
                "model_status": self.get_status()
                }

        try:
            # Exact features used during model training
            required_features = [
                "temperature_c",
                "humidity_percent",
                "wind_speed_kmh",
                "solar_radiation_wm2",
                "elderly_density",
                "outdoor_worker_density",
                "population_density",
                "healthcare_access",
                "wbgt"
                ]

            # Check for missing features
            missing_features = [
                feature
                for feature in required_features
                if feature not in features
                ]

            if missing_features:
                return {
                    "success": False,
                    "error": "MISSING_FEATURES",
                    "message": "Required ML features are missing.",
                    "missing_features": missing_features
                }

            # Create input in the exact order used during training
            features_vector = [[
                features["temperature_c"],
                features["humidity_percent"],
                features["wind_speed_kmh"],
                features["solar_radiation_wm2"],
                features["elderly_density"],
                features["outdoor_worker_density"],
                features["population_density"],
                features["healthcare_access"],
                features["wbgt"]
                ]]

            # Run the actual trained Random Forest model
            prediction = float(self.model.predict(features_vector)[0])

            # Keep score between 0 and 100
            risk_score = max(0.0, min(100.0, prediction))

            # Convert score into a simple category
            if risk_score < 25:
                risk_level = "Low"
            elif risk_score < 50:
                risk_level = "Moderate"
            elif risk_score < 75:
                risk_level = "High"
            else:
                risk_level = "Extreme"

            # Get model probability if supported
            prediction_probability = None

            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(features_vector)[0]
                prediction_probability = float(max(probabilities))

            return {
                "success": True,
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "prediction_probability": prediction_probability,
                "features_used": features
                }

        except Exception as e:
            return {
                "success": False,
                "error": "INFERENCE_ERROR",
                "message": str(e)
            }