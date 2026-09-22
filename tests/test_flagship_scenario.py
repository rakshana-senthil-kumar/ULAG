"""
Test Suite for Flagship Demonstration Scenario (Problem Statement 26013)
Validates exact requirements for Parcel 184/2:
- Legacy Area: 1487 m²
- Revenue Area: 1520 m²
- Drone Area: 1541 m²
- GNSS Survey: 1535 m²
- Confidence: 93.7%
- Recommendation: GNSS + Drone geometry
- Legally grounded and mathematically honest explanation
"""

import pytest
from backend.app.services.pipeline import pipeline
from backend.app.models.storage import storage_repo

def test_flagship_scenario_metrics():
    # Run pipeline on demo dataset
    res = pipeline.load_and_run_demo()
    assert res["summary"]["total_parcels"] == 300
    assert res["summary"]["conflicts_count"] == 24
    assert res["summary"]["matched_count"] == 276

    # Fetch flagship parcel 184/2
    parcel = storage_repo.get_parcel_detail("184/2")
    assert parcel is not None, "Flagship parcel 184/2 must exist in storage"

    # Verify Survey number and Status
    assert "184/2" in parcel["full_survey"]
    assert parcel["status"] in ["Conflict", "Review Required"]

    # Verify Area comparison values
    sources = parcel["sources_comparison"]
    assert sources["legacy"] == 1487.0
    assert sources["revenue"] == 1520.0
    assert sources["drone"] == 1541.0
    assert sources["gnss"] == 1535.0

    # Verify Evidence breakdown
    evidence = parcel["evidence"]
    assert evidence["geometry_match"] == 94.0
    assert evidence["area_match"] == 91.0
    assert evidence["centroid_match"] == 98.0
    assert evidence["attribute_match"] == 100.0
    assert evidence["proximity_match"] == 80.0
    assert evidence["overall_confidence"] == 93.7

    # Verify Recommendation
    rec = parcel["recommendation"]
    assert rec["geometry_source"] == "GNSS + Drone geometry"
    assert rec["confidence"] == 93.7
    assert "GNSS and drone" in rec["explanation_summary"]
    assert "differ" in rec["explanation_summary"].lower()

def test_flagship_approval_workflow():
    # Verify C-001 corresponds to flagship parcel
    conflict = storage_repo.get_conflict_detail("C-001")
    assert conflict is not None
    assert "184/2" in conflict["survey_no"]
    assert conflict["status"] == "Pending"

    # Accept recommendation
    decision = storage_repo.record_review_decision(
        conflict_id="C-001",
        action="ACCEPT",
        user="Officer S. Kulkarni (District Land Records)",
        comment="Boundary conforms to high-precision CORS RTK survey points."
    )
    assert decision["status"] == "Approved"

    # Re-fetch conflict and verify updated state
    updated = storage_repo.get_conflict_detail("C-001")
    assert updated["status"] == "Approved"
    assert updated["reviewed_by"] == "Officer S. Kulkarni (District Land Records)"
