# ML Model Storage 🧠

This folder is dedicated to storing trained machine learning models, scalers, and preprocessing pipelines developed for heatwave health-risk prediction.

### Supported Model Formats
- Scikit-Learn / XGBoost / LightGBM: `heatwave_risk_model.pkl` or `.joblib`
- PyTorch: `.pt` or `.pth`
- ONNX: `.onnx`
- Metadata: `model_metadata.json` (describing feature names, scaling factors, version, and performance metrics)

### Expected Features (Example)
The backend expects input features such as:
1. `temperature_c`: Air Temperature (°C)
2. `relative_humidity`: Relative Humidity (%)
3. `heat_index_c`: Calculated Heat Index (°C)
4. `wind_speed_kmh`: Wind Speed (km/h)
5. `solar_radiation`: Solar Radiation ($W/m^2$)
6. `duration_hours_above_threshold`: Continuous hours above critical temperature
7. `vulnerability_index`: Population density, elderly percentage, or urban heat island factor (0.0 to 1.0)

### Backend Hook
The backend loader in `backend/services/ml_service.py` is configured to look inside this `models/` directory for the model file specified in `backend/.env`.
