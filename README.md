# BHUMI-FUSION
### AI-Powered Cadastral Reconciliation & Geospatial Harmonization Platform
Problem Statement 26013: Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management

---

## Quick Start (Windows)

### 1. One-Click Launch
Double-click [`start.bat`](start.bat) or run in terminal:
```cmd
start.bat
```
This automatically:
- Starts the **Python FastAPI Backend** at `http://127.0.0.1:8000`
- Starts the **Vite + React Frontend** at `http://localhost:5173`
- Opens the application in your default browser

### 2. One-Click Stop
Double-click [`stop.bat`](stop.bat) or run in terminal:
```cmd
stop.bat
```
This terminates all backend and frontend services and frees ports `8000` and `5173`.

---

## Architecture & Technology Stack

- **Backend:** Python 3.10+
  - FastAPI + Uvicorn
  - Shapely 2.0 (`STRtree` spatial indexing, topological intersection, IoU)
  - GeoPandas, PyProj, scikit-learn
  - SQLite (out-of-the-box zero-config persistence) & PostgreSQL/PostGIS migration (`database/migrations/001_initial_schema.sql`)
- **Frontend:**
  - React 19, TypeScript, Vite
  - Tailwind CSS v4
  - MapLibre GL JS (high-performance vector/raster geospatial rendering)
  - Lucide Icons

---

## Manual Execution (Alternative)

### Backend:
```cmd
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs: `http://127.0.0.1:8000/docs`

### Frontend:
```cmd
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Automated Tests
```cmd
python -m pytest tests/
```
All 13 test suites (matching engine, flagship parcel 184/2, and REST endpoints) will execute and report precision/recall.
