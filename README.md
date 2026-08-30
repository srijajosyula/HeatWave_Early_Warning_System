# HeatWave Early Warning System 🌡️🚨

A modular, full-stack early warning platform designed to predict, monitor, and alert against extreme heatwave risks and thermal stress in real-time. Built for the **Smart India Hackathon (SIH)**.

---

## 📁 Project Architecture

```
HeatWave_Early_Warning_System/
│
├── backend/                        # FastAPI Backend Application
│   ├── main.py                     # Entry point & CORS configuration
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment configurations
│   ├── routes/                     # API Route Handlers
│   │   ├── weather.py              # Weather data & thermal stress endpoints
│   │   ├── risk.py                 # ML model status & zone risk prediction
│   │   └── alerts.py               # Early warning generation & active alerts
│   ├── services/                   # Business Logic & External Integrations
│   │   ├── weather_service.py      # Real-time & forecast meteorological client
│   │   ├── thermal_stress_service.py # Heat Index, Wet-Bulb & thermal stress math
│   │   ├── ml_service.py           # ML Model Loader & Inference Manager
│   │   └── alert_service.py        # Advisory & alert tier evaluation engine
│   └── data/                       # Backend local cache / sample zone configs
│
├── frontend/                       # Web Dashboard (UI)
│
├── models/                         # Trained ML model weights (.pkl, .joblib, .onnx)
│
├── data/                           # Datasets, GeoJSON, and boundary files
│
└── README.md                       # Project Overview & Setup Guide
```

---

## 🚀 Getting Started with the Backend

### 1. Prerequisites
- Python 3.9+ installed
- Virtual environment tool (`venv` or `conda`)

### 2. Setup Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Backend API Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Or from the project root:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Interactive API Documentation
Once the server is running, explore and test the endpoints directly in your browser:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status & metadata |
| `GET` | `/health` | Healthcheck endpoint |
| `GET` | `/api/weather/current` | Fetch current weather and thermal stress metrics |
| `GET` | `/api/weather/forecast` | Fetch multi-day weather forecast with heat index |
| `GET` | `/api/risk/model-status` | Check if the ML model artifact is loaded & ready |
| `POST` | `/api/risk/predict` | Predict heatwave risk for a given zone/feature set |
| `GET` | `/api/alerts/active` | Get active heatwave alerts |
| `POST` | `/api/alerts/evaluate` | Evaluate meteorological metrics against alert thresholds |

---

## 🧠 ML Integration Guide
Place trained ML models in the `models/` folder. The backend's `ml_service.py` is configured to look for model files without making fake predictions. See `models/README.md` for details.
