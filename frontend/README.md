# Frontend Dashboard 💻

This folder is reserved for the HeatWave Early Warning System frontend dashboard application.

### Planned Tech Stack
- **Framework**: React / Vite or Next.js
- **Mapping & Geospatial**: Leaflet / Mapbox GL (for zone-wise heatwave risk visualization)
- **Data Visualization**: Recharts / Chart.js (for temperature trends, heat index, and hourly risk projections)
- **UI Components & Styling**: Tailwind CSS / Lucide Icons

### Connection to Backend
The frontend connects to the FastAPI backend at `https://heatwave-early-warning-system.onrender.com/api`.

Ensure CORS origins in `backend/.env` include your frontend dev server port (e.g. `5173` or `3000`).

