# BHUMI-FUSION REST API Reference

All endpoints are hosted by FastAPI with prefix `/api` and automatic OpenAPI documentation at `/docs`.

---

## Ingestion & Pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/demo/load` | Trigger end-to-end ingestion and reconciliation for synthetic demo datasets. |
| `POST` | `/api/datasets/upload` | Multipart upload for custom legacy GeoJSON, drone GeoJSON, GNSS CSV, and revenue CSV. |
| `POST` | `/api/reconciliation/run` | Re-executes matching and conflict detection pipeline on current database state. |
| `GET` | `/api/reconciliation/summary` | Returns high-level metrics (total parcels, matched count, conflicts count, CRS). |

---

## Parcel Queries & WebGIS Fabric

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/parcels` | Query list of parcels with optional `?status=All|Matched|Conflict` and `?search=`. |
| `GET` | `/api/parcels/{id}` | Detailed parcel record with multi-source GeoJSON and evidence breakdowns. |
| `GET` | `/api/parcels/geojson` | **Full Fabric WebGIS GeoJSON** FeatureCollection containing all 300 parcels. |
| `GET` | `/api/parcels/{id}/evidence` | Mathematical breakdown of the 5-factor scoring engine and recommendation rationale. |

---

## Conflict Adjudication & Human Review

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/conflicts` | Returns all detected conflicts with type filter (`?type=All|Geometry|Area|Attribute|Missing`). |
| `GET` | `/api/conflicts/{id}` | Detail of specific conflict case. |
| `POST` | `/api/conflicts/{id}/approve` | Officer approves recommended reconciliation candidate with audit record. |
| `POST` | `/api/conflicts/{id}/reject` | Officer rejects candidate, marking record in dispute. |
| `POST` | `/api/conflicts/{id}/manual-review` | Flags record for joint on-site field survey inspection. |

---

## GeoAI & Canonicals (v2)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v2/buildings` | Returns AI/YOLO extracted building footprints within parcels. |
| `GET` | `/api/v2/changes` | Temporal change detection events (new construction, boundary shifts, conversions). |
| `GET` | `/api/v2/topology/issues` | Planar topology validation issues (overlaps, slivers, self-intersections). |
| `GET` | `/api/v2/provenance/{id}` | Complete W3C PROV-compliant data transformation history and lineage. |
| `GET` | `/api/v2/models` | Registry of registered AI/ML models with evaluation metrics (precision, recall, IoU). |
| `GET` | `/api/v2/dsm-dtm` | Registered elevation raster metadata (resolution, min/max elevation, bounds). |
| `GET` | `/api/v2/parcels/{id}/elevation` | Zonal elevation metrics (min, max, mean, slope) for a specific parcel. |
| `GET` | `/api/v2/utilities` | Municipal utility network layers (power, water, sewer, telecom). |
| `GET` | `/api/v2/parcels/{id}/utility` | Utility network distance and count association for a parcel. |

---

## Data Export & Interoperability

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/export/parcels?format=geojson` | Download standardized OGC GeoJSON FeatureCollection of reconciled records. |
| `GET` | `/api/export/parcels?format=csv` | Download tabular CSV report of reconciled cadastral land records. |
