"""
Unit and Integration Tests for Explicit Dataset Synchronization (SIH PS Gap 3)
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.sync.sync_engine import sync_engine

client = TestClient(app)

def test_dataset_change_detection():
    status_rec, changes = sync_engine.run_demo_update_detection()
    assert status_rec.change_detected is True
    assert status_rec.sync_status == "SYNC_REQUIRED"
    assert len(changes) > 0
    assert any(c.change_type in ["AREA_CHANGED", "ATTRIBUTE_CHANGED", "MODIFIED"] for c in changes)

def test_affected_parcel_detection():
    res = client.get("/api/v2/sync/changes")
    assert res.status_code == 200
    changes = res.json()
    affected_parcels = [c["parcel_id"] for c in changes]
    assert "P003" in affected_parcels

def test_sync_status_transition():
    proc_res = client.post("/api/v2/sync/process?dataset_id=DS-Revenue")
    assert proc_res.status_code == 200
    p_data = proc_res.json()
    assert p_data["sync_status"]["sync_status"] == "REVIEW_REQUIRED"

def test_reconciliation_after_source_update():
    app_res = client.post("/api/v2/sync/approve?dataset_id=DS-Revenue&reviewer=Officer%20Test")
    assert app_res.status_code == 200
    a_data = app_res.json()
    assert a_data["status"] == "APPROVED"
    assert "new_dataset_version" in a_data
    assert "provenance_record" in a_data
