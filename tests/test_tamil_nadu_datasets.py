"""
Test Suite for Tamil Nadu Geospatial Layers, Thematic Maps, and Road Infrastructure
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_tamil_nadu_layer_catalog():
    response = client.get("/api/tamil-nadu/layers")
    assert response.status_code == 200
    data = response.json()
    assert data["total_layers"] >= 20
    assert data["vector_layers_count"] == 20
    assert data["thematic_maps_count"] == 5
    
    layer_names = [l["layer_name"] for l in data["layers"]]
    # Check key layers from user specifications
    expected_layers = [
        "Aadhar_Enrollment_Center", "Amma_Unavagam_GCC", "Anganwadi_Centres",
        "Arts_and_Science_Collage", "Block_Boundary", "Buildings_Locations",
        "Burial_Ground_Locations", "Bus_shelter_Locations", "Chennai_Metro_Rail_Route",
        "Chennai_Metro_Rail_Station", "Chennai_Outer_Boundary", "Chennai_Region_Boundary",
        "CMWSSB_Decanting_Location", "CMWSSB_Sewerage_Pumping_Stations", "Cold_Storages",
        "Common_Service_Centres", "Community_Farm_Schools_CFS", "Community_Skill_School_CSS",
        "Corporations", "CUMTA_Outer_Boundary"
    ]
    for exp in expected_layers:
        assert exp in layer_names, f"Expected layer {exp} in catalog"

def test_tamil_nadu_vector_geojson_fetch():
    # Test CMRL stations
    response = client.get("/api/tamil-nadu/layers/Chennai_Metro_Rail_Station")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    assert data["features"][0]["geometry"]["type"] == "Point"

    # Test Metro Route
    response = client.get("/api/tamil-nadu/layers/Chennai_Metro_Rail_Route")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 2
    assert data["features"][0]["geometry"]["type"] == "LineString"

    # Test Corporations
    response = client.get("/api/tamil-nadu/layers/Corporations")
    assert response.status_code == 200
    data = response.json()
    assert len(data["features"]) >= 15
    coimbatore_found = any(f["properties"].get("city_name") == "Coimbatore" for f in data["features"])
    assert coimbatore_found

def test_tamil_nadu_road_inventory():
    response = client.get("/api/tamil-nadu/road-inventory")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Coimbatore"
    summary = data["summary"]
    assert "2112" in summary["total_road_length_km"]
    assert "808" in summary["tar_roads_km"]
    assert "256" in summary["concrete_roads_km"]
    assert "40" in summary["footpath_both_sides_km"]
    assert "70" in summary["footpath_one_side_km"]
    assert len(data["records"]) > 0
    assert len(data["statewide_comparison"]) > 0

def test_tamil_nadu_census_demographics():
    response = client.get("/api/tamil-nadu/census-demographics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 20
    districts = [d["district_name"] for d in data]
    assert "Chennai" in districts
    assert "Coimbatore" in districts
    assert "Madurai" in districts

def test_provenance_registered_datasets_includes_tn():
    response = client.get("/api/datasets")
    assert response.status_code == 200
    datasets = response.json()
    dataset_ids = [d["dataset_id"] for d in datasets]
    assert "DS-TN-VectorLayers" in dataset_ids
    assert "DS-TN-ThematicMaps" in dataset_ids
    assert "DS-TN-Roads" in dataset_ids
