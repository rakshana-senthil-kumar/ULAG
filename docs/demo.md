# BHUMI-FUSION End-to-End Demo Workflow Guide

**Smart India Hackathon Problem Statement 26013**

Follow this deterministic workflow to evaluate the complete platform capabilities.

---

## 1. Quick Launch
Double-click `start.bat` on Windows or execute:
```bash
# Terminal 1: Backend
python -m uvicorn backend.app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```
Open browser at: `http://localhost:5173`

---

## 2. Step-by-Step Evaluator Walkthrough

### Step 1: Ingestion & Multi-Source Validation (`/workspace`)
1. Click **Data Ingestion** in the sidebar.
2. Review the 6 registered multi-source data cards:
   - **Cadastral:** 300 vector parcels in EPSG:4326.
   - **Drone ORI:** Orthorectified high-resolution vector fabric in UTM EPSG:32643.
   - **GNSS RTK:** Millimeter-accurate CORS boundary observations.
   - **Revenue Register:** Tabular 7/12 land records.
   - **DSM / DTM:** Real GeoTIFF raster elevation dataset (`data/demo/pune_dsm.tif`).
   - **Utility Network:** Municipal electricity, water, and telecom lines.
3. Click **Run Harmonization**. Watch the 9-stage stepper execute real schema harmonization, PyProj CRS transformation, STRtree indexing, and geometry validation.

### Step 2: Full-Fabric WebGIS Inspection (`/reconcile`)
1. Navigate to the **Harmonization Workspace**.
2. Notice the **Full Cadastral Fabric** rendered in the background with all 300 parcels visible simultaneously.
3. Hover over any parcel to inspect survey plot number, status, and calculated confidence.
4. Click on any parcel in the fabric to immediately focus the inspector and view its 5-factor mathematical score breakdown.
5. Click **Compare Sources Mode** to view side-by-side area metrics: Legacy vs Drone vs GNSS vs Revenue.
6. Toggle the **Cadastral Fabric**, **Legacy**, **Drone**, **GNSS**, and **Reconciled** layer switches.

### Step 3: Conflict Adjudication & Human Review (`/conflicts` and `/review`)
1. Navigate to **Conflicts & Review**.
2. Filter conflicts by type: `Geometry`, `Area`, `Attribute`, or `Missing`.
3. Select a conflict (e.g. `P003` / Survey `184/2`).
4. Inspect the multi-source evidence:
   - Drone boundary: 1541.0 m²
   - Legacy map: 1487.0 m²
   - GNSS RTK survey: 1535.0 m²
   - Revenue register: 1520.0 m²
5. Click **Approve Reconciliation**. Provide an audit comment: `"Approved based on GNSS and Drone ORI alignment"`.
6. Notice the parcel status dynamically updates to `Matched` and the audit log records the officer identity and timestamp.

### Step 4: Temporal Change Detection & Visual Split Analysis (`/changes`)
1. Navigate to **Change Detection**.
2. Interact with the **Before / After Split Map Slider**:
   - Left side: 2023 Historical Cadastral register vector boundaries.
   - Right side: 2026 Drone ORI boundaries + AI-extracted building footprints.
   - Drag the center divider to observe newly constructed buildings and shifted physical fences.
3. Filter detected change events: `New Buildings`, `Boundary Shifts`, or `Land Use Conversions`.

### Step 5: Data Provenance & Inter-Departmental Export
1. On the **Reconcile Workspace** or **Provenance** view:
   - Inspect the complete transformation lineage: Original File → CRS Reprojection → Topology Repair → 5-Factor STRtree Matching → Officer Approval.
2. In the top-right toolbar of the map:
   - Click **GeoJSON** to download the harmonized OGC-standard `harmonized_cadastral_parcels.geojson` FeatureCollection.
   - Click **CSV** to download the `harmonized_land_records.csv` tabular report.
3. Both files contain genuine, calculated, un-hardcoded parcel geometries and consensual areas.
