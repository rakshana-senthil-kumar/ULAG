# BHUMI-FUSION V2 Data Model & Schemas

## Canonical Entities

### 1. Canonical Parcel (`CanonicalParcel`)
- `parcel_uid`: Unique string ID
- `survey_number`: Standardized survey number
- `subdivision_number`: Standardized subdivision number
- `full_survey`: Formatted reference (`184/2`)
- `geometry_geojson`: GeoJSON geometry mapping (EPSG:4326)
- `metric_geometry_geojson`: Projected metric geometry mapping (EPSG:32643)
- `area_m2`: Calculated metric surface area in square meters
- `land_use`: Standardized classification (Residential, Commercial, Agricultural, Industrial, Institutional, Mixed Use)
- `confidence`: 8-dimension multi-dimensional confidence breakdown
- `provenance`: Data lineage record

### 2. Canonical Building (`CanonicalBuilding`)
- `building_id`: Unique building structure ID
- `parcel_uid`: Parent parcel identifier
- `geometry_geojson`: Building polygon footprint GeoJSON
- `area_m2`: Structural footprint area
- `building_type`: Classification (Residential Structure, Commercial Complex)
- `confidence`: AI extraction confidence rating (0-100)
- `model_version`: AI model identifier (`YOLO+SAM-BuildingExtractor-v1.0`)

### 3. Provenance Record (`ProvenanceRecord`)
- `feature_id`: Target feature identifier
- `source_dataset`: Name of origin dataset
- `source_type`: Ingestion layer type (Legacy, Drone, GNSS, Revenue, Municipal)
- `crs_used`: Coordinate system transformation applied
- `transformations_applied`: Audit list of pipeline operations
- `reconciliation_decision`: Final geometry source selection
- `reviewer`: Officer ID recording the decision
