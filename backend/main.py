import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import route handlers
from .routes import weather_router, risk_router, alerts_router

# Initialize FastAPI application
app = FastAPI(
    title="HeatWave Early Warning System API",
    description="Modular backend API for real-time heatwave forecasting, thermal stress calculations, ML health-risk prediction, and early warning advisories.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins_raw = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:5500,http://localhost:5500"
)
origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(weather_router)
app.include_router(risk_router)
app.include_router(alerts_router)


@app.get("/", tags=["General"])
async def root():
    """Root endpoint returning API status and links to documentation."""
    return {
        "project": "HeatWave Early Warning System API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "modules": [
            {"route": "/api/weather", "description": "Meteorological data & thermal stress metrics"},
            {"route": "/api/risk", "description": "Zone risk evaluation & ML model manager"},
            {"route": "/api/alerts", "description": "Early warning alerts & public health advisories"}
        ]
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
