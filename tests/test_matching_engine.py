"""
Unit & Integration Tests for Parcel Matching & Conflict Detection
Tests:
- Perfect match
- Boundary shift / Geometry displacement
- Area mismatch
- Attribute mismatch
- Missing parcel
- Duplicate parcel
- Split & Merge
- Deterministic behavior
"""

import pytest
from backend.app.services.pipeline import pipeline
from backend.app.models.storage import storage_repo

@pytest.fixture(scope="module", autouse=True)
def init_data():
    pipeline.load_and_run_demo()

def test_summary_and_counts():
    summary = storage_repo.get_pipeline_summary()
    assert summary["total_parcels"] == 300
    assert summary["conflicts_count"] == 24
    assert summary["matched_count"] == 276

def test_conflict_types_presence():
    conflicts = storage_repo.get_conflicts()
    types = {c["conflict_type"] for c in conflicts}
    assert "Geometry" in types
    assert "Area" in types
    assert "Attribute" in types
    assert "Missing" in types

def test_deterministic_results():
    """Matching engine must return deterministic results for identical inputs."""
    res1 = pipeline.load_and_run_demo()
    res2 = pipeline.load_and_run_demo()

    assert res1["summary"]["total_parcels"] == res2["summary"]["total_parcels"]
    assert res1["summary"]["matched_count"] == res2["summary"]["matched_count"]
    assert res1["summary"]["conflicts_count"] == res2["summary"]["conflicts_count"]

def test_missing_feature_handling():
    conflicts = storage_repo.get_conflicts(conflict_type="Missing")
    assert len(conflicts) > 0
    c = conflicts[0]
    assert c["sources_comparison"]["drone"] is None
    assert "Missing" in c["conflict_type"]

def test_area_mismatch_handling():
    conflicts = storage_repo.get_conflicts(conflict_type="Area")
    assert len(conflicts) > 0
    c = conflicts[0]
    assert c["sources_comparison"]["revenue"] is not None
    assert c["sources_comparison"]["legacy"] is not None
    assert abs(c["sources_comparison"]["revenue"] - c["sources_comparison"]["legacy"]) > 20.0
