"""
Unit and Integration Tests for DSM/DTM Elevation Ingestion (SIH PS Gap 1)
"""

import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.elevation_service import elevation_service

client = TestClient(app)

def test_dsm_ingestion():
    demo_dsm = os.path.join("data", "demo", "pune_dsm_demo.tif")
    assert os.path.exists(demo_dsm)

    with open(demo_dsm, "rb") as f:
        content = f.read()

    meta = elevation_service.ingest_elevation_dataset(
        file_name="pune_dsm_demo.tif",
        file_bytes=content,
        dataset_type="DSM",
        source_name="Drone LiDAR DEM"
    )
    assert meta.dataset_type == "DSM"
    assert meta.processing_status == "VALIDATED"
    assert meta.min_elevation > 0
    assert meta.max_elevation >= meta.min_elevation

def test_dtm_ingestion():
    demo_dtm = os.path.join("data", "demo", "pune_dtm_demo.tif")
    assert os.path.exists(demo_dtm)

    with open(demo_dtm, "rb") as f:
        content = f.read()

    meta = elevation_service.ingest_elevation_dataset(
        file_name="pune_dtm_demo.tif",
        file_bytes=content,
        dataset_type="DTM",
        source_name="Bare Earth Terrain Model"
    )
    assert meta.dataset_type == "DTM"
    assert meta.processing_status == "VALIDATED"

def test_raster_metadata_validation():
    res = client.get("/api/v2/dsm-dtm")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 2
    types = [d["dataset_type"] for d in datasets]
    assert "DSM" in types
    assert "DTM" in types

def test_dsm_parcel_association():
    res = client.get("/api/v2/parcels/P003/elevation")
    assert res.status_code == 200
    elev = res.json()
    assert elev["parcel_id"] == "P003"
    assert elev["has_elevation_data"] is True
    assert elev["min_elevation_m"] is not None
    assert elev["max_elevation_m"] is not None
    assert elev["elevation_range_m"] >= 0
    assert elev["slope_deg"] >= 0
