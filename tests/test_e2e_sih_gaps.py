"""
End-to-End Test Suite for Complete SIH 26013 Workflow with DSM, Utility & Synchronization
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_full_sih_26013_e2e_flow():
    # 1. Load full demo pipeline
    demo_res = client.post("/api/demo/load")
    assert demo_res.status_code == 200
    assert demo_res.json()["status"] == "success"

    # 2. Check complete 10-category dataset registry
    datasets_res = client.get("/api/datasets")
    assert datasets_res.status_code == 200
    datasets = datasets_res.json()
    assert len(datasets) >= 10
    categories = set(d.get("source_type") for d in datasets)
    assert "Legacy Cadastral" in categories
    assert "Revenue Records" in categories
    assert "Drone ORI" in categories
    assert "DSM" in categories
    assert "DTM" in categories
    assert "GNSS/CORS" in categories
    assert "Utility Network" in categories
    assert "Building Footprints" in categories

    # 3. Verify DSM/DTM elevation evidence on parcel
    elev_res = client.get("/api/v2/parcels/P003/elevation")
    assert elev_res.status_code == 200
    assert elev_res.json()["has_elevation_data"] is True

    # 4. Verify Utility Network spatial association on parcel
    util_res = client.get("/api/v2/parcels/P003/utility")
    assert util_res.status_code == 200
    assert util_res.json()["utility_count"] > 0

    # 5. Trigger source update change detection (Dataset Synchronization)
    sync_check = client.post("/api/v2/sync/check")
    assert sync_check.status_code == 200
    check_data = sync_check.json()
    assert check_data["status"] == "CHECK_COMPLETED"
    assert check_data["sync_status"]["change_detected"] is True

    # 6. Recalculate reconciliation
    sync_proc = client.post("/api/v2/sync/process?dataset_id=DS-Revenue")
    assert sync_proc.status_code == 200
    assert sync_proc.json()["sync_status"]["sync_status"] == "REVIEW_REQUIRED"

    # 7. Officer approves reconciliation
    sync_app = client.post("/api/v2/sync/approve?dataset_id=DS-Revenue&reviewer=Senior%20GIS%20Officer")
    assert sync_app.status_code == 200
    app_data = sync_app.json()
    assert app_data["status"] == "APPROVED"
    assert app_data["new_dataset_version"]["version_number"] > 0

    # 8. Verify provenance audit entry
    prov_res = client.get("/api/v2/provenance/P003")
    assert prov_res.status_code == 200
    assert prov_res.json()["feature_id"] == "P003"
