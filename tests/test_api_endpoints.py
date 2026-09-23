"""
Test Suite for FastAPI REST Endpoints
Validates API responses, schema integrity, and evaluation metrics.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.pipeline import pipeline

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def init_demo():
    pipeline.load_and_run_demo()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_reconciliation_summary():
    response = client.get("/api/reconciliation/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_parcels"] == 300
    assert data["conflicts_count"] == 24
    assert data["matched_count"] == 276

def test_list_parcels():
    response = client.get("/api/parcels?status=All")
    assert response.status_code == 200
    parcels = response.json()
    assert len(parcels) == 300

def test_flagship_parcel_endpoint():
    response = client.get("/api/parcels/P003")
    assert response.status_code == 200
    data = response.json()
    assert "184/2" in data["full_survey"]
    assert 88.0 <= data["confidence"] <= 98.0
    assert data["sources_comparison"]["legacy"] == 1487.0
    assert data["sources_comparison"]["drone"] == 1541.0
    assert data["sources_comparison"]["gnss"] is not None
    assert data["sources_comparison"]["revenue"] == 1520.0

def test_conflicts_endpoint():
    response = client.get("/api/conflicts?type=All")
    assert response.status_code == 200
    conflicts = response.json()
    assert len(conflicts) == 24

def test_evaluation_report():
    response = client.get("/api/evaluation/report")
    assert response.status_code == 200
    eval_data = response.json()
    assert eval_data["total_known_parcels"] == 300
    assert eval_data["precision_percentage"] >= 95.0
    assert eval_data["recall_percentage"] >= 95.0

def test_v2_canonical_endpoints():
    # 1. Buildings GeoAI
    res_b = client.get("/api/v2/buildings")
    assert res_b.status_code == 200
    bldgs = res_b.json()
    assert len(bldgs) > 0
    assert "building_id" in bldgs[0]
    assert "area_m2" in bldgs[0]

    # 2. Temporal Changes
    res_c = client.get("/api/v2/changes")
    assert res_c.status_code == 200
    changes = res_c.json()
    assert len(changes) > 0
    assert "change_type" in changes[0]

    # 3. Topology issues
    res_t = client.get("/api/v2/topology/issues")
    assert res_t.status_code == 200
    assert isinstance(res_t.json(), list)

    # 4. Raster DSM/DTM
    res_dsm = client.get("/api/v2/dsm-dtm")
    assert res_dsm.status_code == 200
    dsm_data = res_dsm.json()
    assert len(dsm_data) > 0
    assert dsm_data[0]["resolution"] > 0
    assert dsm_data[0]["min_elevation"] > 0

    # 5. Utilities
    res_u = client.get("/api/v2/utilities")
    assert res_u.status_code == 200
    utilities = res_u.json()
    assert len(utilities) > 0
    assert "utility_type" in utilities[0]

    # 6. Models
    res_m = client.get("/api/v2/models")
    assert res_m.status_code == 200
    models = res_m.json()
    assert len(models) >= 3

    # 7. Sync status
    res_s = client.get("/api/v2/sync/status")
    assert res_s.status_code == 200
    sync_status = res_s.json()
    assert len(sync_status) > 0

def test_parcels_geojson_webgis():
    res = client.get("/api/parcels/geojson")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 300
    first_feat = data["features"][0]
    assert "geometry" in first_feat
    assert "properties" in first_feat
    assert "parcel_id" in first_feat["properties"]

def test_export_endpoints():
    # GeoJSON export
    res_geo = client.get("/api/export/parcels?format=geojson")
    assert res_geo.status_code == 200
    data_geo = res_geo.json()
    assert data_geo["type"] == "FeatureCollection"
    assert len(data_geo["features"]) == 300

    # CSV export
    res_csv = client.get("/api/export/parcels?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    lines = res_csv.text.strip().split("\n")
    assert len(lines) == 301  # header + 300 parcels
    assert "parcel_id,survey_no" in lines[0]

