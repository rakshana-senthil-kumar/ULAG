"""
Unit and Integration Tests for Utility Network Data Support (SIH PS Gap 2)
"""

import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.utility_service import utility_service

client = TestClient(app)

def test_utility_geojson_ingestion():
    demo_utility_path = os.path.join("data", "demo", "utility_network.geojson")
    assert os.path.exists(demo_utility_path)

    with open(demo_utility_path, "r", encoding="utf-8") as f:
        content = f.read()

    ingested = utility_service.ingest_utility_geojson(content, source_name="DEMO DATASET (Municipal Utilities)")
    assert len(ingested) >= 5
    u_types = set(a.utility_type for a in ingested)
    assert "Electricity" in u_types
    assert "Water" in u_types
    assert "Telecom" in u_types

def test_utility_parcel_association():
    assoc = utility_service.compute_parcel_utility_association("P003")
    assert assoc.parcel_id == "P003"
    assert assoc.utility_count > 0
    assert assoc.electricity_count >= 1
    assert assoc.nearest_utility_distance_m >= 0

def test_utility_spatial_query():
    res = client.get("/api/v2/utilities")
    assert res.status_code == 200
    utilities = res.json()
    assert len(utilities) > 0

    parcel_util_res = client.get("/api/v2/parcels/P003/utility")
    assert parcel_util_res.status_code == 200
    p_util = parcel_util_res.json()
    assert p_util["parcel_id"] == "P003"
    assert p_util["electricity_count"] >= 1
