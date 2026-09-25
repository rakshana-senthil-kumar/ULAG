"""
Unit and Integration Test Suite for Selective IndianOpenMaps Data Integration
SIH Problem Statement 26013 - Urban Land Record Harmonization
"""

import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.iomaps_loader import iomaps_loader
from backend.app.services.matching.matcher import spatial_matcher

client = TestClient(app)

def test_iomaps_layer_loading():
    summary = iomaps_loader.load_all_iomaps_layers()
    assert summary["status"] == "SUCCESS"
    assert summary["provider"] == "IndianOpenMaps"
    assert summary["aoi"] == "Coimbatore, Tamil Nadu"
    assert len(summary["layers"]) == 5
    assert summary["layers"]["buildings"]["count"] > 0
    assert summary["layers"]["transport"]["count"] > 0
    assert summary["layers"]["boundaries"]["count"] > 0
    assert summary["layers"]["water"]["count"] > 0
    assert summary["layers"]["power"]["count"] > 0

def test_iomaps_provenance_metadata():
    bld_meta = os.path.join("dataset", "buildings", "indianopenmaps", "metadata.json")
    assert os.path.exists(bld_meta)
    
    tr_meta = os.path.join("dataset", "transport", "indianopenmaps", "metadata.json")
    assert os.path.exists(tr_meta)

    wtr_meta = os.path.join("dataset", "water", "indianopenmaps", "metadata.json")
    assert os.path.exists(wtr_meta)

def test_reference_building_comparison():
    from backend.app.services.ai.extractor import building_extractor
    from backend.app.services.pipeline import pipeline
    pipeline.load_and_run_demo()
    
    drone_blds, _ = building_extractor.extract_buildings_from_drone_features([
        {
            "properties": {"parcel_id": "P003"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[73.7375, 18.5905], [73.73785, 18.5905], [73.73785, 18.59080], [73.7375, 18.59080], [73.7375, 18.5905]]]
            }
        }
    ])
    
    ref_blds = iomaps_loader.load_buildings_layer()
    match_results = spatial_matcher.match_buildings_reference([b.model_dump() for b in drone_blds], ref_blds)
    assert len(match_results) > 0
    assert "match_status" in match_results[0]
    assert "iou_percentage" in match_results[0]

def test_parcel_reference_layer_intersections():
    parcel_geom = {
        "type": "Polygon",
        "coordinates": [[[73.7370, 18.5900], [73.7400, 18.5900], [73.7400, 18.5930], [73.7370, 18.5930], [73.7370, 18.5900]]]
    }
    iomaps_data = {
        "buildings": iomaps_loader.load_buildings_layer(),
        "transport": iomaps_loader.load_transport_layer(),
        "boundaries": iomaps_loader.load_boundaries_layer(),
        "water": iomaps_loader.load_water_layer(),
        "power": iomaps_loader.load_power_layer()
    }
    analysis = spatial_matcher.evaluate_parcel_reference_layers(parcel_geom, iomaps_data)
    assert "reference_building_count" in analysis
    assert "nearest_road_distance_m" in analysis
    assert "waterbody_overlap" in analysis
    assert "power_line_intersection" in analysis

def test_iomaps_api_endpoints():
    res_sum = client.get("/api/v2/iomaps/summary")
    assert res_sum.status_code == 200
    assert res_sum.json()["status"] == "SUCCESS"

    res_bld = client.get("/api/v2/reference-buildings")
    assert res_bld.status_code == 200
    assert len(res_bld.json()) > 0

    res_rd = client.get("/api/v2/transport-roads")
    assert res_rd.status_code == 200
    assert len(res_rd.json()) > 0

    res_wtr = client.get("/api/v2/water-features")
    assert res_wtr.status_code == 200
    assert len(res_wtr.json()) > 0

    res_pwr = client.get("/api/v2/power-infra")
    assert res_pwr.status_code == 200
    assert len(res_pwr.json()) > 0

    res_adm = client.get("/api/v2/admin-boundaries")
    assert res_adm.status_code == 200
    assert len(res_adm.json()) > 0

    res_anl = client.get("/api/v2/parcels/P003/iomaps-analysis")
    assert res_anl.status_code == 200
    assert res_anl.json()["nearest_road_distance_m"] >= 0
