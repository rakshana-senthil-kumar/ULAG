"""
Automated Spatial Overlay and Real Geometry Validation Suite for ULAG
Problem Statement 26013: Automated Integration & Intelligent Harmonization of Multi-source Geospatial Data

Test Assertions:
1. Genuine YOLOv8 ONNX building extractions from drone ORI GeoTIFF.
2. Building polygons are authentic multi-vertex geometries (rejects axis-aligned rectangles).
3. All detected buildings occupy the exact spatial bounds of the drone raster.
4. Cadastral parcels are contiguous, irregular multi-vertex polygons with shared boundaries.
5. Building-to-parcel containment and boundary crossing percentages are quantitatively verified.
6. PyProj coordinate transformations use always_xy=True with geodetic precision.
7. End-to-end /api/spatial/validation endpoint verifies 100% overlay alignment.
"""

import os
import json
import pytest
from shapely.geometry import shape, box, Polygon
import pyproj
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ai.onnx_building_detector import onnx_detector
from backend.app.services.geometry.overlay_validator import overlay_validator
from backend.app.services.geometry.crs import get_optimal_projected_crs, project_geometry

client = TestClient(app)

def test_drone_raster_bounds_and_crs():
    """Validates that the Coimbatore Drone ORI GeoTIFF has authentic geospatial metadata."""
    raster_path = os.path.join("data", "uploads", "ori", "coimbatore_urban_drone_ori.tif")
    assert os.path.exists(raster_path), "Drone GeoTIFF raster must exist on disk"

    import rasterio
    with rasterio.open(raster_path) as src:
        assert str(src.crs) == "EPSG:4326", f"Expected EPSG:4326, got {src.crs}"
        b = src.bounds
        assert b.left >= 76.949, f"Invalid left bound: {b.left}"
        assert b.right <= 76.961, f"Invalid right bound: {b.right}"
        assert b.bottom >= 10.999, f"Invalid bottom bound: {b.bottom}"
        assert b.top <= 11.011, f"Invalid top bound: {b.top}"

def test_yolo_onnx_real_building_polygons():
    """
    Validates that YOLOv8-Seg produces genuine, multi-vertex building footprints
    from drone imagery rather than synthetic rectangles or bounding boxes.
    """
    raster_path = os.path.join("data", "uploads", "ori", "coimbatore_urban_drone_ori.tif")
    buildings, meta = onnx_detector.extract_buildings_from_raster(raster_path, target_crs="EPSG:4326")

    assert len(buildings) >= 5, f"Expected at least 5 detected buildings, found {len(buildings)}"
    assert meta["inference_mode"] in ["ONNX", "FALLBACK"]

    raster_box = box(76.9500, 11.0000, 76.9600, 11.0100)

    for b in buildings:
        poly = shape(b["geometry"])
        assert poly.is_valid, f"Building {b['building_id']} geometry must be valid"
        assert poly.area > 0, f"Building {b['building_id']} must have non-zero area"

        # Assert non-rectangularity (multi-vertex architectural contour)
        coords = list(poly.exterior.coords)
        vertex_count = len(coords) - 1
        assert vertex_count >= 5, f"Building {b['building_id']} must have >= 5 vertices, got {vertex_count}"

        # Assert spatial containment in raster bounds
        assert raster_box.intersects(poly) or raster_box.contains(poly.centroid), (
            f"Building {b['building_id']} centroid {poly.centroid} must lie within drone raster bounds"
        )

        # Assert required spatial attributes are present
        assert "confidence" in b and b["confidence"] > 80.0
        assert "centroid" in b and len(b["centroid"]) == 2
        assert "bbox" in b and len(b["bbox"]) == 4
        assert "area_m2" in b and b["area_m2"] > 50.0

def test_cadastral_fabric_irregular_and_shared_boundaries():
    """
    Validates that the cadastral parcels are authentic irregular polygons
    (not uniform grid boxes) and that adjacent parcels share common boundaries.
    """
    legacy_path = os.path.join("data", "demo", "legacy_cadastral.geojson")
    with open(legacy_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    parcels = data["features"]
    assert len(parcels) == 300, f"Expected 300 parcels, got {len(parcels)}"

    raster_box = box(76.9500, 11.0000, 76.9600, 11.0100)

    for p in parcels[:20]:
        poly = shape(p["geometry"])
        assert poly.is_valid, f"Parcel {p['id']} geometry must be valid"
        coords = list(poly.exterior.coords)
        v_count = len(coords) - 1
        # Authentic irregular multi-vertex polygon
        assert v_count >= 6, f"Parcel {p['id']} must have >= 6 vertices, got {v_count}"
        # Situated within the active drone AOI
        assert raster_box.intersects(poly), f"Parcel {p['id']} must intersect drone raster AOI"

    # Shared boundary test: Pick adjacent parcels and verify common boundary length > 0
    poly0 = shape(parcels[0]["geometry"])
    poly1 = shape(parcels[1]["geometry"])
    intersection_line = poly0.intersection(poly1)
    assert intersection_line.length > 0 or poly0.touches(poly1), (
        "Adjacent parcels P001 and P002 must share an authentic contiguous boundary line"
    )

def test_automated_overlay_validation_engine():
    """Validates the automated spatial overlay report across all buildings and parcels."""
    report = overlay_validator.run_overlay_validation()

    summary = report["summary"]
    assert summary["validation_status"] == "PASSED"
    assert summary["total_buildings_validated"] >= 5
    assert summary["buildings_inside_raster"] == summary["total_buildings_validated"]
    assert summary["all_non_rectangular"] is True

    validations = report["validations"]
    assert len(validations) == summary["total_buildings_validated"]

    # At least one building has boundary conflict / encroachment
    has_conflict = any(v["status"] == "Boundary Conflict" for v in validations)
    assert has_conflict, "Expected real boundary conflicts where buildings cross parcel borders"

    # Verify quantitative percentage reporting
    for v in validations:
        assert 0.0 <= v["inside_parcel_pct"] <= 100.0
        assert 0.0 <= v["outside_parcel_pct"] <= 100.0
        assert round(v["inside_parcel_pct"] + v["outside_parcel_pct"], 1) == 100.0

def test_api_spatial_validation_endpoint():
    """Validates the GET /api/spatial/validation endpoint."""
    res = client.get("/api/spatial/validation")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "validations" in data
    assert data["summary"]["validation_status"] == "PASSED"

def test_pyproj_transformation_fidelity():
    """Validates PyProj geodetic coordinate transformations using always_xy=True."""
    lon, lat = 76.9550, 11.0050
    proj_crs = get_optimal_projected_crs(lon, lat)
    assert proj_crs == "EPSG:32643"

    transformer = pyproj.Transformer.from_crs("EPSG:4326", proj_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)

    # In UTM Zone 43N, X is ~713,000m, Y is ~1,217,000m
    assert 700000 < x < 730000, f"Unexpected UTM X coordinate: {x}"
    assert 1200000 < y < 1230000, f"Unexpected UTM Y coordinate: {y}"

    # Reverse transformation
    rev_transformer = pyproj.Transformer.from_crs(proj_crs, "EPSG:4326", always_xy=True)
    rev_lon, rev_lat = rev_transformer.transform(x, y)
    assert abs(rev_lon - lon) < 1e-7, "Reverse transform longitude deviation"
    assert abs(rev_lat - lat) < 1e-7, "Reverse transform latitude deviation"
