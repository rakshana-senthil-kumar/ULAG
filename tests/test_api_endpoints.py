"""
Test Suite for FastAPI REST Endpoints
Validates API responses, schema integrity, and evaluation metrics.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

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
    assert data["confidence"] == 93.7
    assert data["sources_comparison"]["legacy"] == 1487.0
    assert data["sources_comparison"]["drone"] == 1541.0
    assert data["sources_comparison"]["gnss"] == 1535.0
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
