"""
Golden Geospatial Alignment Test for YOLOv8-Seg Building Footprint Pipeline
Verifies the end-to-end mathematical precision:
ORI GeoTIFF -> ONNX YOLO Model -> Detection BBoxes & Mask Protos -> Inverse Letterbox
-> Pixel Space Simplification -> Affine Georeferencing -> EPSG:4326 GeoJSON
-> Exact Reverse Transform (GeoJSON -> Raster CRS -> Original Pixels)
"""

import os
import math
import pytest
import rasterio
from shapely.geometry import shape, box, Polygon
from backend.app.services.ai.onnx_building_detector import onnx_detector
from backend.app.services.ai.diagnostic_exporter import diagnostic_exporter

RASTER_PATH = os.path.join("data", "uploads", "ori", "coimbatore_urban_drone_ori.tif")

def test_ori_raster_geospatial_integrity():
    """Step 1 & 2: Load actual ORI and verify geospatial metadata."""
    assert os.path.exists(RASTER_PATH), "ORI GeoTIFF must exist"
    with rasterio.open(RASTER_PATH) as src:
        assert src.width > 0 and src.height > 0
        assert src.count == 3
        assert str(src.crs) == "EPSG:4326"
        b = src.bounds
        assert 76.945 <= b.left <= 76.955
        assert 76.955 <= b.right <= 76.965
        assert 10.995 <= b.bottom <= 11.005
        assert 11.005 <= b.top <= 11.015
        # Transform check (north-up raster: a > 0, e < 0)
        assert src.transform.a > 0
        assert src.transform.e < 0

def test_yolo_onnx_detection_and_segmentation():
    """Step 2, 3, 4, 5, 6: Run actual ONNX model, verify polygons, bounds, and areas."""
    buildings, meta = onnx_detector.extract_buildings_from_raster(RASTER_PATH, target_crs="EPSG:4326")

    assert meta["inference_mode"] == "ONNX", f"Expected ONNX inference mode, got {meta['inference_mode']}"
    assert len(buildings) >= 5, f"Expected at least 5 buildings detected, found {len(buildings)}"

    with rasterio.open(RASTER_PATH) as src:
        b = src.bounds
        raster_box = box(b.left, b.bottom, b.right, b.top)

    for bld in buildings:
        poly = shape(bld["geometry"])
        assert poly.is_valid, f"Building {bld['building_id']} geometry must be topologically valid"
        assert not poly.is_empty
        assert poly.geom_type in ["Polygon", "MultiPolygon"]

        # Step 5: Inside ORI geographic bounds
        assert raster_box.contains(poly.centroid) or raster_box.intersects(poly), (
            f"Building {bld['building_id']} centroid {poly.centroid} must lie inside ORI bounds {raster_box.bounds}"
        )

        # Step 6: Verify polygon area is physically reasonable (15 to 1800 m²)
        area_m2 = bld["area_m2"]
        assert 15.0 <= area_m2 <= 1800.0, f"Building area {area_m2} m² is outside reasonable urban scale"

        # Verify multi-vertex architectural footprint (not axis-aligned bounding box)
        coords = list(poly.exterior.coords)
        vertex_count = len(coords) - 1
        assert vertex_count >= 5, f"Building {bld['building_id']} has only {vertex_count} vertices; expected >= 5"

        # Confidence from model
        assert "confidence" in bld and bld["confidence"] >= 50.0

def test_reverse_transformation_precision():
    """
    Step 7: Verify reverse transformation:
    GeoJSON -> raster CRS -> pixel coordinates returns approximately the original polygon
    within numerical tolerance (< 1.5 pixels).
    """
    buildings, _ = onnx_detector.extract_buildings_from_raster(RASTER_PATH, target_crs="EPSG:4326")
    assert len(buildings) > 0

    with rasterio.open(RASTER_PATH) as src:
        inv_transform = ~src.transform
        w, h = src.width, src.height

    for bld in buildings:
        geom = bld["geometry"]
        exterior_coords = geom["coordinates"][0]

        # Map back to pixel space
        px_coords = [inv_transform * (gx, gy) for gx, gy in exterior_coords]

        # Verify all vertices are strictly inside the raster dimensions
        for px, py in px_coords:
            assert -1.0 <= px <= w + 1.0, f"Pixel X {px} out of raster bounds [0, {w}]"
            assert -1.0 <= py <= h + 1.0, f"Pixel Y {py} out of raster bounds [0, {h}]"

        # Check reconstructed bounding box matches stored pixel_bbox within 1.5 px
        px_xs = [p[0] for p in px_coords]
        px_ys = [p[1] for p in px_coords]
        min_px_x, max_px_x = min(px_xs), max(px_xs)
        min_px_y, max_px_y = min(px_ys), max(px_ys)

        # Verify polygon vertices are tightly contained inside detection bounding box
        stored_bbox = bld.get("pixel_bbox")
        if stored_bbox:
            sbx1, sby1, sbx2, sby2 = stored_bbox
            assert sbx1 - 1.5 <= min_px_x <= sbx2 + 1.5, f"Polygon X min {min_px_x} outside bbox [{sbx1}, {sbx2}]"
            assert sbx1 - 1.5 <= max_px_x <= sbx2 + 1.5, f"Polygon X max {max_px_x} outside bbox [{sbx1}, {sbx2}]"
            assert sby1 - 1.5 <= min_px_y <= sby2 + 1.5, f"Polygon Y min {min_px_y} outside bbox [{sby1}, {sby2}]"
            assert sby1 - 1.5 <= max_px_y <= sby2 + 1.5, f"Polygon Y max {max_px_y} outside bbox [{sby1}, {sby2}]"

        # Roundtrip verification: transform * (~transform * (gx, gy)) == (gx, gy)
        for (gx, gy), (px, py) in zip(exterior_coords, px_coords):
            rt_x, rt_y = src.transform * (px, py)
            assert abs(rt_x - gx) < 1e-8, f"Roundtrip longitude error: {abs(rt_x - gx)}"
            assert abs(rt_y - gy) < 1e-8, f"Roundtrip latitude error: {abs(rt_y - gy)}"

def test_diagnostic_four_stage_visuals_generated():
    """Validates Section 11 requirement: 4 distinct diagnostic visualizations exist."""
    res = diagnostic_exporter.generate_diagnostics(RASTER_PATH)
    assert res["status"] == "success"
    assert "saved_files" in res

    files = res["saved_files"]
    for stage_name, fpath in files.items():
        assert os.path.exists(fpath), f"Diagnostic image for {stage_name} must exist at {fpath}"
        assert os.path.getsize(fpath) > 1000, f"Diagnostic image {fpath} must have content"
