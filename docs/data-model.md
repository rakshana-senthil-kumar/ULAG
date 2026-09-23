# ULAG Geospatial Data Model

---

## 1. Relational Entities (SQLite / PostgreSQL with PostGIS)

### 1.1 `parcels` Table
Stores harmonized and multi-source parcel records:
- `parcel_id` (TEXT, PK): Unique parcel identifier (e.g. `P003`).
- `survey_no` (TEXT): Main survey plot number.
- `subdivision_no` (TEXT, Nullable): Sub-division or plot share index.
- `full_survey` (TEXT, Indexed): Canonical composite survey number (e.g. `184/2`).
- `land_use` (TEXT): Categorical classification (Agricultural, Residential, Commercial).
- `legacy_area` (REAL): Recorded legal area in square meters.
- `legacy_geometry` (TEXT/GEOMETRY): GeoJSON string or PostGIS Polygon in EPSG:4326.
- `drone_geometry` (TEXT/GEOMETRY): Extracted drone vector boundary.
- `reconciled_geometry` (TEXT/GEOMETRY): Recommended consensual geometry.
- `gnss_points` (JSON): Array of associated RTK survey observations.
- `confidence` (REAL): 5-factor explainable score (0.0 to 100.0).
- `status` (TEXT): `Matched`, `Conflict`, or `Review`.
- `conflict_type` (TEXT, Nullable): `Geometry`, `Area`, `Attribute`, `Missing`, `Overlap`, or `None`.
- `source_comparison` (JSON): Object holding recorded area values across all sources.
- `evidence` (JSON): Detailed breakdown of individual similarity factors.
- `recommendation` (JSON): Recommended area, geometry source, and natural language rationale.

### 1.2 `conflicts` Table
Tracks detected spatial and attribute divergences:
- `conflict_id` (TEXT, PK): Identifier (e.g. `C-001`).
- `parcel_id` (TEXT, FK): Target parcel identifier.
- `survey_no` (TEXT): Associated survey plot number.
- `conflict_type` (TEXT): Categorical conflict type.
- `severity` (TEXT): `High`, `Medium`, or `Low`.
- `confidence` (REAL): Pipeline confidence score at conflict detection time.
- `discrepancy_delta` (TEXT): Metric variance (e.g. `+54 m² (+3.6%)`).
- `sources_comparison` (JSON): Cross-source comparison dict.
- `explanation` (TEXT): Natural language explanation of root cause.
- `status` (TEXT): `Pending`, `Approved`, `Rejected`, or `Manual Review`.
- `reviewed_by` (TEXT, Nullable): Officer user ID.
- `timestamp` (TEXT): Last adjudication or update timestamp.

### 1.3 `review_actions` Table (Audit Trail)
- `action_id` (INTEGER, PK, Auto): Audit record sequence.
- `conflict_id` (TEXT): Related conflict ID.
- `parcel_id` (TEXT): Target parcel ID.
- `action` (TEXT): `ACCEPT`, `REJECT`, or `MANUAL_REVIEW`.
- `decided_by` (TEXT): Officer identity.
- `comment` (TEXT): Adjudication remarks.
- `timestamp` (TEXT): Immutable record timestamp.

---

## 2. Canonical Ingestion Schema

```typescript
interface RegisteredDataset {
  dataset_id: string;
  dataset_name: string;
  source_type: 'Cadastral' | 'Drone' | 'GNSS' | 'Revenue' | 'DSM' | 'Utility';
  format: 'GeoJSON' | 'Shapefile' | 'CSV' | 'GeoTIFF';
  original_crs: string;
  normalized_crs: 'EPSG:32643' | 'EPSG:4326';
  feature_count: number;
  status: 'Validated' | 'Processing' | 'Synced';
}
```
