# BHUMI-FUSION
### Automated Integration and Intelligent Harmonization of Multi-source Geospatial Data for Urban Land Record Management
**Smart India Hackathon Problem Statement 26013**

---

## 🌟 Executive Summary

**BHUMI-FUSION** is an enterprise-grade geospatial integration and intelligent harmonization platform engineered for urban land administration authorities. It harmonizes heterogeneous geospatial datasets across **Drone Imagery (ORI)**, **DSM/DTM Elevation Rasters**, **Legacy Cadastral Vector Maps**, **Revenue 7/12 Records**, **CORS/GNSS RTK Field Surveys**, and **Municipal Utility Networks**.

The system replaces arbitrary rule-based overrides with genuine **PyProj geodetic coordinate transformations**, **Shapely STRtree 2D R-Tree spatial indexing**, **5-factor explainable confidence scoring**, **Rasterio-powered zonal elevation statistics**, **GeoAI building footprint extraction**, **bi-temporal vector change detection**, and an interactive **Leaflet Full-Fabric WebGIS**.

---

## 🚀 Quick Start (Windows)

### 1. One-Click Launch
Double-click [`start.bat`](start.bat) or run in PowerShell / Command Prompt:
```cmd
start.bat
```
This automatically:
- Checks Python environment and launches the **FastAPI Backend** on `http://127.0.0.1:8000`
- Launches the **Vite + React 19 Frontend** on `http://localhost:5173`
- Launches the browser to the live WebGIS dashboard

### 2. One-Click Stop
Double-click [`stop.bat`](stop.bat) or run:
```cmd
stop.bat
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend & Services** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2 |
| **Spatial Engine** | Shapely 2.0 (`STRtree` 2D spatial index, `make_valid`, IoU), PyProj (Geodetic CRS Transformer) |
| **Raster Engine** | Rasterio, GDAL, Affine (windowed GeoTIFF reads & zonal statistics) |
| **AI / Machine Learning**| Ultralytics YOLOv8, PyTorch, scikit-learn, ONNX Runtime |
| **Data Storage** | SQLite (Zero-config local runtime) & PostgreSQL / PostGIS Ready |
| **Frontend WebGIS** | React 19, TypeScript, Vite, Tailwind CSS v4, Leaflet GIS Engine, Lucide Icons |
| **Testing** | Pytest, TestClient, AnyIO |

---

## 📊 End-to-End Pipeline

```
Heterogeneous Datasets (Drone ORI, DSM, Cadastral, Revenue, GNSS, Utilities)
                               │
                               ▼
  1. Flexible Schema Ingestion & Synonym Harmonization
                               │
                               ▼
  2. Geodetic CRS Transformation (EPSG:4326 <-> EPSG:32643 via PyProj)
                               │
                               ▼
  3. Planar Topology Validation & Repair (Shapely STRtree + make_valid)
                               │
                               ▼
  4. Spatial Candidate Matching (STRtree 2D R-Tree)
                               │
                               ▼
  5. Explainable 5-Factor Confidence Scoring (No Hardcoding)
     [35% Geometry IoU + 20% Area + 20% Centroid + 15% Attributes + 10% Proximity]
                               │
                               ▼
  6. GeoAI Building Extraction & Elevation Zonal Statistics (Rasterio)
                               │
                               ▼
  7. Multi-Source Conflict Detection & Triage Categorization
                               │
                               ▼
  8. Audited Human-in-the-Loop Review Workflow
                               │
                               ▼
  9. Standardized OGC GeoJSON & Tabular CSV Interoperable Export
```

---

## 🧪 Automated Testing

Execute the complete 16-test suite verifying the matching engine, API endpoints, evaluation report, and dynamic scoring:
```cmd
python -m pytest -v
```

Execute frontend type-checking and production build:
```cmd
cd frontend
npm run build
```

---

## 📚 Technical Documentation

- 🏛️ [System Architecture & Data Flows](docs/architecture.md)
- 🔌 [REST API Endpoints Reference](docs/api.md)
- 🗄️ [Geospatial Data Model & Database Schema](docs/data-model.md)
- 🧠 [GeoAI Building Extraction & Computer Vision](docs/ai.md)
- 🧭 [Evaluator Demo Walkthrough Guide](docs/demo.md)
