-- BHUMI-FUSION Database Schema
-- Problem Statement 26013: AI-Powered Cadastral Reconciliation & Geospatial Harmonization Platform
-- PostgreSQL + PostGIS Compatible Migration

CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Datasets Table
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dataset_type VARCHAR(64) NOT NULL, -- 'legacy_cadastral', 'drone_features', 'gnss_points', 'revenue_records'
    file_format VARCHAR(32) NOT NULL,
    crs VARCHAR(64) DEFAULT 'EPSG:4326',
    record_count INTEGER NOT NULL DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(128)
);

-- 2. Source Reliability Configuration Table
CREATE TABLE IF NOT EXISTS source_reliability (
    source_type VARCHAR(64) PRIMARY KEY,
    reliability_weight NUMERIC(4, 3) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO source_reliability (source_type, reliability_weight, description) VALUES
('GNSS/CORS', 0.970, 'Differential RTK/CORS ground receiver network'),
('Ground Truth', 0.950, 'Physical ground boundary tie-in measurements'),
('Drone/ORI', 0.900, 'Ortho-rectified imagery photogrammetric feature extraction'),
('Municipal GIS', 0.820, 'Urban local body spatial boundary records'),
('Revenue', 0.780, 'Tehsildar land revenue register area & subdivision entries'),
('Legacy Cadastral', 0.650, 'Digitized colonial / historical village map sheets (bhunaksha)')
ON CONFLICT (source_type) DO UPDATE SET reliability_weight = EXCLUDED.reliability_weight;

-- 3. Source Features (Original Source Data Preservation)
CREATE TABLE IF NOT EXISTS source_features (
    feature_id VARCHAR(64) PRIMARY KEY,
    dataset_id VARCHAR(64) REFERENCES datasets(dataset_id),
    source_type VARCHAR(64) NOT NULL,
    survey_identifier VARCHAR(128) NOT NULL,
    area_m2 NUMERIC(12, 2),
    attributes JSONB,
    original_geometry GEOMETRY(Geometry, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Parcels Table (Master Cadastral Entities)
CREATE TABLE IF NOT EXISTS parcels (
    parcel_id VARCHAR(64) PRIMARY KEY,
    survey_no VARCHAR(64) NOT NULL,
    subdivision_no VARCHAR(32),
    full_survey VARCHAR(128) NOT NULL,
    land_use VARCHAR(64),
    legacy_area_m2 NUMERIC(12, 2) NOT NULL,
    legacy_geometry GEOMETRY(Polygon, 4326) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Parcel Matches Table
CREATE TABLE IF NOT EXISTS parcel_matches (
    match_id VARCHAR(64) PRIMARY KEY,
    parcel_id VARCHAR(64) REFERENCES parcels(parcel_id),
    drone_feature_id VARCHAR(64),
    geometry_score NUMERIC(5, 2) NOT NULL,
    area_score NUMERIC(5, 2) NOT NULL,
    centroid_score NUMERIC(5, 2) NOT NULL,
    attribute_score NUMERIC(5, 2) NOT NULL,
    proximity_score NUMERIC(5, 2) NOT NULL,
    overall_confidence NUMERIC(5, 2) NOT NULL,
    status VARCHAR(32) NOT NULL, -- 'Matched', 'Review', 'Conflict'
    matched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Conflicts Table
CREATE TABLE IF NOT EXISTS conflicts (
    conflict_id VARCHAR(64) PRIMARY KEY,
    parcel_id VARCHAR(64) REFERENCES parcels(parcel_id),
    conflict_type VARCHAR(64) NOT NULL, -- 'Geometry', 'Area', 'Attribute', 'Missing', 'Split', 'Merge', 'Duplicate'
    severity VARCHAR(32) NOT NULL, -- 'High', 'Medium', 'Low'
    source_values JSONB NOT NULL,
    recommended_value JSONB,
    confidence NUMERIC(5, 2) NOT NULL,
    explanation TEXT NOT NULL,
    status VARCHAR(32) DEFAULT 'Pending', -- 'Pending', 'Approved', 'Rejected', 'Manual Review'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Reconciliation Results Table
CREATE TABLE IF NOT EXISTS reconciliation_results (
    reconciliation_id VARCHAR(64) PRIMARY KEY,
    parcel_id VARCHAR(64) REFERENCES parcels(parcel_id),
    recommended_area_m2 NUMERIC(12, 2) NOT NULL,
    geometry_source VARCHAR(128) NOT NULL,
    confidence NUMERIC(5, 2) NOT NULL,
    explanation TEXT NOT NULL,
    reconciled_geometry GEOMETRY(Geometry, 4326),
    review_status VARCHAR(32) DEFAULT 'Pending',
    reconciled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Review Actions Table (Human-in-the-Loop Audit Trail)
CREATE TABLE IF NOT EXISTS review_actions (
    action_id VARCHAR(64) PRIMARY KEY,
    conflict_id VARCHAR(64) REFERENCES conflicts(conflict_id),
    parcel_id VARCHAR(64) REFERENCES parcels(parcel_id),
    action VARCHAR(32) NOT NULL, -- 'ACCEPT', 'REJECT', 'MANUAL_REVIEW'
    decided_by VARCHAR(128) NOT NULL,
    decision_comment TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial Indices
CREATE INDEX IF NOT EXISTS idx_parcels_geom ON parcels USING GIST (legacy_geometry);
CREATE INDEX IF NOT EXISTS idx_source_features_geom ON source_features USING GIST (original_geometry);
CREATE INDEX IF NOT EXISTS idx_reconciled_geom ON reconciliation_results USING GIST (reconciled_geometry);
