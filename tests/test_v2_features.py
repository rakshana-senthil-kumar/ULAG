"""
Test Suite for BHUMI-FUSION V2 Advanced Features
Validates CRS transformation, AI Building Extraction, Attribute Harmonization,
Topology Repair, Temporal Change Detection, Versioning, Provenance, and V2 API routes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.crs.crs_engine import detect_optimal_metric_crs, calculate_metric_spatial_properties
from backend.app.services.ai.extractor import building_extractor
from backend.app.services.attribute.attribute_harmonizer import attribute_harmonizer
from backend.app.services.topology.topology_engine import topology_engine
from backend.app.services.change_detection.change_detector import change_detector
from backend.app.services.versioning.version_manager import version_manager
from backend.app.services.provenance.provenance_tracker import provenance_tracker
from backend.app.services.confidence.confidence_calculator import confidence_calculator
from backend.app.schemas.cadastral import EvidenceMetrics

client = TestClient(app)

def test_crs_engine_metric_detection():
    # Hinjewadi/Pune region longitude ~73.738, latitude ~18.591 -> UTM Zone 43N
    crs = detect_optimal_metric_crs(73.7380, 18.5910)
    assert crs == "EPSG:32643"

def test_attribute_harmonizer():
    raw_props = {
        "plot_id": "205",
        "hissa_no": "3",
        "extent": "1250.5",
        "zoning": "res"
    }
    result = attribute_harmonizer.harmonize_record(raw_props)
    assert result.survey_number == "205"
    assert result.subdivision_number == "3"
    assert result.full_survey == "205/3"
    assert result.area_m2 == 1250.5
    assert result.land_use == "Residential"

def test_topology_engine_repair():
    # Self-intersecting bowtie polygon
    bowtie_geom = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [0, 2], [2, 0], [2, 2], [0, 0]]]
    }
    repaired_dict, issues = topology_engine.validate_and_repair_geometry(bowtie_geom, "TEST-01")
    assert len(issues) == 1
    assert issues[0].issue_type == "Self-Intersection"
    assert issues[0].auto_fixed is True

def test_provenance_tracker():
    record = provenance_tracker.create_provenance_record(
        feature_id="P184_2",
        source_dataset="Legacy Cadastral",
        reconciliation_decision="GNSS + Drone geometry"
    )
    assert record.feature_id == "P184_2"
    assert "EPSG:32643" in record.crs_used
    assert len(record.transformations_applied) >= 4

def test_version_manager():
    initial_history = version_manager.get_version_history("DS-TestUnit")
    initial_count = len(initial_history)
    v1 = version_manager.register_version("DS-TestUnit", 300, "Version 1")
    assert v1.version_number == initial_count + 1
    assert v1.active is True

    v2 = version_manager.register_version("DS-TestUnit", 300, "Version 2")
    assert v2.version_number == v1.version_number + 1
    assert v2.active is True

    history = version_manager.get_version_history("DS-TestUnit")
    assert len(history) == initial_count + 2
    assert history[-2].active is False  # v1 deactivated

def test_v2_api_routes():
    # Load pipeline first
    client.post("/api/demo/load")

    res_bld = client.get("/api/v2/buildings")
    assert res_bld.status_code == 200
    buildings = res_bld.json()
    assert len(buildings) > 0

    res_chg = client.get("/api/v2/changes")
    assert res_chg.status_code == 200
    changes = res_chg.json()
    assert len(changes) > 0

    res_models = client.get("/api/v2/models")
    assert res_models.status_code == 200
    models = res_models.json()
    assert len(models) >= 3
