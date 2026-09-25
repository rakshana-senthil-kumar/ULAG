"""
End-to-End Integration & Regression Test Suite for BHUMI-FUSION V2
Validates full E2E pipeline:
Upload/Ingestion -> Validation -> CRS Metric Transformation -> AI Feature Extraction ->
Spatial Matching -> Attribute Harmonization -> Topology Validation -> Change Detection ->
Conflict Resolution -> Multi-Dimensional Confidence -> Provenance Lineage -> Review & Publish.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.pipeline import pipeline

client = TestClient(app)

def test_full_e2e_pipeline_flow():
    # 1. Trigger pipeline execution
    load_res = client.post("/api/demo/load")
    assert load_res.status_code == 200
    data = load_res.json()
    assert data["status"] == "success"
    assert data["summary"]["total_parcels"] == 300

    # 2. Verify Datasets Metadata Endpoint
    datasets_res = client.get("/api/datasets")
    assert datasets_res.status_code == 200
    datasets = datasets_res.json()
    assert len(datasets) >= 10

    # 3. Verify AI Building Footprints
    buildings_res = client.get("/api/v2/buildings")
    assert buildings_res.status_code == 200
    buildings = buildings_res.json()
    assert len(buildings) > 0

    # 4. Verify Topology Issues Detection & Auto-repair
    topology_res = client.get("/api/v2/topology/issues")
    assert topology_res.status_code == 200

    # 5. Verify Temporal Changes
    changes_res = client.get("/api/v2/changes")
    assert changes_res.status_code == 200
    changes = changes_res.json()
    assert len(changes) > 0

    # 6. Verify Formal Conflict Resolution Action
    resolve_res = client.post("/api/conflicts/C-001/resolve", json={
        "action": "ACCEPT_SOURCE_A",
        "user": "District Land Officer",
        "comment": "Conforms to GNSS RTK survey points."
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["decision"] == "ACCEPT_SOURCE_A"

    # 7. Verify Provenance Lineage Query
    prov_res = client.get("/api/v2/provenance/P003")
    assert prov_res.status_code == 200
    prov = prov_res.json()
    assert prov["feature_id"] == "P003"
    assert len(prov["transformations_applied"]) >= 4

    # 8. Verify Comprehensive Evaluation Report (Tagged SYNTHETIC DATASET EVALUATION)
    eval_res = client.get("/api/evaluation/comprehensive")
    assert eval_res.status_code == 200
    report = eval_res.json()
    assert report["evaluation_type"] == "SYNTHETIC DATASET EVALUATION"
    assert report["spatial_matching"]["precision"] >= 95.0
