"""
Adversarial & Edge-Case Test Suite for ULAG Spatial Parcel Matching Engine (Phase 19)
Tests 15 distinct spatial, topological, geodetic, and attribute edge cases designed
to stress-test and verify mathematical correctness of the matching engine.
"""

import pytest
import math
from shapely.geometry import Polygon, MultiPolygon, Point, mapping
from shapely.affinity import translate, scale, rotate

from backend.app.services.matching.matcher import (
    ParcelMatcher, compute_boundary_deviations, calculate_attribute_similarity
)
from backend.app.services.geometry.crs import (
    project_geometry, project_point, validate_and_repair_geometry, get_optimal_projected_crs
)

# Reference Base (Coimbatore, Tamil Nadu)
BASE_LON = 76.9558
BASE_LAT = 11.0168
CRS = "EPSG:32643"

def make_poly(center_x: float, center_y: float, w: float, h: float) -> Polygon:
    w2, h2 = w / 2.0, h / 2.0
    return Polygon([
        (center_x - w2, center_y - h2),
        (center_x + w2, center_y - h2),
        (center_x + w2, center_y + h2),
        (center_x - w2, center_y + h2),
        (center_x - w2, center_y - h2)
    ])

def to_wgs84(poly_m: Polygon) -> Polygon:
    # Convert metric offsets to degrees for test feature generation
    m_per_deg_lat = 111132.95
    m_per_deg_lon = 111132.95 * math.cos(math.radians(BASE_LAT))
    coords = []
    for x, y in poly_m.exterior.coords:
        dlon = x / m_per_deg_lon
        dlat = y / m_per_deg_lat
        coords.append((BASE_LON + dlon, BASE_LAT + dlat))
    return Polygon(coords)

# -------------------------------------------------------------
# TEST 1: Two adjacent parcels with similar areas
# -------------------------------------------------------------
def test_case_01_adjacent_parcels_similar_area():
    p1 = to_wgs84(make_poly(0, 0, 40, 30))
    p2_adjacent = to_wgs84(make_poly(42, 0, 40, 30))

    drone_feats = [{
        "type": "Feature",
        "id": "DRONE_ADJ_1",
        "properties": {"feature_id": "DRONE_ADJ_1", "survey_candidate": "100/1", "area": 1200.0},
        "geometry": mapping(p2_adjacent)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P01", "survey_no": "100", "subdivision_no": "1", "area": 1200.0}, "geometry": mapping(p1)}
    best, evidence, runners = matcher.match_parcel(legacy)
    # Adjacent parcel should have ~0 IoU and should NOT be auto-matched
    assert evidence.geometry_match < 5.0
    assert evidence.overall_confidence < 65.0
    assert len(evidence.hard_constraint_flags) > 0

# -------------------------------------------------------------
# TEST 2: Two parcels with similar centroids but different boundaries
# -------------------------------------------------------------
def test_case_02_similar_centroids_different_shapes():
    # Square vs narrow cross with identical centroid (0,0)
    p_square = to_wgs84(make_poly(0, 0, 40, 40)) # 1600 m²
    p_long = to_wgs84(make_poly(0, 0, 100, 16))   # 1600 m²
    
    drone_feats = [{
        "type": "Feature",
        "id": "DRONE_CROSS",
        "properties": {"feature_id": "DRONE_CROSS", "survey_candidate": "101/1", "area": 1600.0},
        "geometry": mapping(p_long)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P02", "survey_no": "101", "subdivision_no": "1", "area": 1600.0}, "geometry": mapping(p_square)}
    best, evidence, runners = matcher.match_parcel(legacy)
    # Even though centroid is identical and areas are identical, IoU and boundary deviation must flag a conflict
    assert evidence.centroid_match >= 90.0
    assert evidence.geometry_match < 50.0  # IoU is low due to shape difference
    assert evidence.overall_confidence <= 65.0

# -------------------------------------------------------------
# TEST 3: Same survey number but completely wrong geometry
# -------------------------------------------------------------
def test_case_03_same_survey_wrong_geometry():
    p_here = to_wgs84(make_poly(0, 0, 30, 30))
    p_far = to_wgs84(make_poly(200, 200, 30, 30)) # 280m away

    drone_feats = [{
        "type": "Feature",
        "id": "DRONE_FAR",
        "properties": {"feature_id": "DRONE_FAR", "survey_candidate": "102/1", "area": 900.0},
        "geometry": mapping(p_far)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P03", "survey_no": "102", "subdivision_no": "1", "area": 900.0}, "geometry": mapping(p_here)}
    best, evidence, runners = matcher.match_parcel(legacy)
    # Survey number matches (100%), but geometry is far away: must NOT be matched!
    assert best is None
    assert evidence.overall_confidence == 0.0

# -------------------------------------------------------------
# TEST 4: Same area but completely different geometry
# -------------------------------------------------------------
def test_case_04_same_area_different_geometry():
    p1 = to_wgs84(make_poly(0, 0, 50, 20)) # 1000 m²
    p2 = to_wgs84(make_poly(5, 5, 20, 50)) # 1000 m² (rotated 90 deg)

    drone_feats = [{
        "type": "Feature",
        "id": "DRONE_ROT",
        "properties": {"feature_id": "DRONE_ROT", "survey_candidate": "103/1", "area": 1000.0},
        "geometry": mapping(p2)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P04", "survey_no": "103", "subdivision_no": "1", "area": 1000.0}, "geometry": mapping(p1)}
    best, evidence, runners = matcher.match_parcel(legacy)
    assert evidence.area_match == 100.0
    # Overlap is only partial (center 20x20 intersection out of 1600 union = ~25% IoU)
    assert evidence.geometry_match < 40.0
    assert evidence.overall_confidence <= 65.0

# -------------------------------------------------------------
# TEST 5: High IoU but large boundary deviation
# -------------------------------------------------------------
def test_case_05_high_iou_boundary_spike():
    # Polygon with a narrow spike extending 18 meters outward
    base_poly = make_poly(0, 0, 40, 40)
    # Candidate with an illegal 18-meter boundary protrusion
    spike_poly = Polygon([
        (-20, -20), (20, -20), (20, 0), (38, 0), (38, 2), (20, 2), (20, 20), (-20, 20), (-20, -20)
    ])
    devs = compute_boundary_deviations(project_geometry(to_wgs84(base_poly)), project_geometry(to_wgs84(spike_poly)))
    assert devs["max_dev"] >= 16.0  # Spike detected
    assert devs["conformance_pct"] < 95.0

# -------------------------------------------------------------
# TEST 6: GNSS point inside wrong candidate
# -------------------------------------------------------------
def test_case_06_gnss_point_contradiction():
    p1 = to_wgs84(make_poly(0, 0, 40, 40))
    p_wrong = to_wgs84(make_poly(50, 0, 40, 40))

    # GNSS points located in p1
    m_per_deg_lat = 111132.95
    m_per_deg_lon = 111132.95 * math.cos(math.radians(BASE_LAT))
    gnss_pts = [
        {"point_id": f"G_{i}", "latitude": BASE_LAT + (y / m_per_deg_lat), "longitude": BASE_LON + (x / m_per_deg_lon)}
        for i, (x, y) in enumerate([(-10, -10), (10, -10), (10, 10), (-10, 10)])
    ]

    drone_feats = [{
        "type": "Feature",
        "id": "DRONE_SHIFTED",
        "properties": {"feature_id": "DRONE_SHIFTED", "survey_candidate": "105/1", "area": 1600.0},
        "geometry": mapping(p_wrong)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P06", "survey_no": "105", "subdivision_no": "1", "area": 1600.0}, "geometry": mapping(p1)}
    best, evidence, runners = matcher.match_parcel(legacy, gnss_points=gnss_pts)
    assert evidence.gnss_inside_percentage == 0.0
    assert evidence.gnss_status == "LOW"

# -------------------------------------------------------------
# TEST 7: Different CRS Handling
# -------------------------------------------------------------
def test_case_07_crs_determination():
    # Coimbatore (76.96°E) -> Zone 43
    crs_cbe = get_optimal_projected_crs(76.9558, 11.0168)
    assert crs_cbe == "EPSG:32643"
    # Chennai (80.27°E) -> Zone 44
    crs_che = get_optimal_projected_crs(80.2707, 13.0827)
    assert crs_che == "EPSG:32644"

# -------------------------------------------------------------
# TEST 8: Self-intersecting invalid polygon repair
# -------------------------------------------------------------
def test_case_08_self_intersection_repair():
    # Bow-tie polygon
    bowtie = Polygon([(0, 0), (20, 20), (20, 0), (0, 20), (0, 0)])
    assert not bowtie.is_valid
    repaired, was_rep, reason = validate_and_repair_geometry(bowtie, "TEST_BOWTIE")
    assert was_rep
    assert repaired.is_valid
    assert repaired.area > 0

# -------------------------------------------------------------
# TEST 9: Multipart polygon resolution
# -------------------------------------------------------------
def test_case_09_multipart_resolution():
    poly1 = make_poly(0, 0, 30, 30) # 900 m²
    poly2 = make_poly(50, 50, 10, 10) # 100 m²
    mp = MultiPolygon([poly1, poly2])
    devs = compute_boundary_deviations(mp, poly1)
    assert devs["mean_dev"] <= 0.1
    assert devs["conformance_pct"] >= 99.0

# -------------------------------------------------------------
# TEST 10: Split Parcel Detection
# -------------------------------------------------------------
def test_case_10_split_parcel_detection():
    full_poly = to_wgs84(make_poly(0, 0, 40, 40)) # 1600 m²
    half1 = to_wgs84(make_poly(-10, 0, 20, 40))   # 800 m²
    half2 = to_wgs84(make_poly(10, 0, 20, 40))    # 800 m²

    drone_feats = [
        {"type": "Feature", "id": "FE_SPLIT_1", "properties": {"feature_id": "FE_SPLIT_1", "feature_type": "Plot Division A", "survey_candidate": "109/1", "area": 800.0}, "geometry": mapping(half1)},
        {"type": "Feature", "id": "FE_SPLIT_2", "properties": {"feature_id": "FE_SPLIT_2", "feature_type": "Plot Division B", "survey_candidate": "109/1", "area": 800.0}, "geometry": mapping(half2)}
    ]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P10", "survey_no": "109", "subdivision_no": "1", "area": 1600.0}, "geometry": mapping(full_poly)}
    best, evidence, runners = matcher.match_parcel(legacy)
    # In a split, individual candidate has only ~50% coverage of source
    assert evidence.coverage_source <= 55.0
    assert len(evidence.candidates_audit) >= 2

# -------------------------------------------------------------
# TEST 11: Merged Parcel Detection
# -------------------------------------------------------------
def test_case_11_merged_parcel():
    p1 = to_wgs84(make_poly(0, 0, 30, 30)) # 900 m²
    p_big = to_wgs84(make_poly(0, 0, 60, 30)) # 1800 m² (consolidated)

    drone_feats = [{
        "type": "Feature", "id": "FE_MERGED", "properties": {"feature_id": "FE_MERGED", "feature_type": "Consolidated Compound", "survey_candidate": "110/1", "area": 1800.0}, "geometry": mapping(p_big)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P11", "survey_no": "110", "subdivision_no": "1", "area": 900.0}, "geometry": mapping(p1)}
    best, evidence, runners = matcher.match_parcel(legacy)
    assert evidence.area_difference_pct >= 45.0
    assert evidence.coverage_candidate <= 55.0

# -------------------------------------------------------------
# TEST 12: Overlapping Candidates Ranking
# -------------------------------------------------------------
def test_case_12_overlapping_candidates_ranking():
    source = to_wgs84(make_poly(0, 0, 40, 40))
    cand_perfect = to_wgs84(make_poly(0.2, 0.2, 40, 40)) # IoU ~98%
    cand_shifted = to_wgs84(make_poly(5, 5, 40, 40))     # IoU ~75%

    drone_feats = [
        {"type": "Feature", "id": "CAND_SHIFTED", "properties": {"feature_id": "CAND_SHIFTED", "survey_candidate": "111/1", "area": 1600.0}, "geometry": mapping(cand_shifted)},
        {"type": "Feature", "id": "CAND_PERFECT", "properties": {"feature_id": "CAND_PERFECT", "survey_candidate": "111/1", "area": 1600.0}, "geometry": mapping(cand_perfect)}
    ]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P12", "survey_no": "111", "subdivision_no": "1", "area": 1600.0}, "geometry": mapping(source)}
    best, evidence, runners = matcher.match_parcel(legacy)
    # The perfect candidate must be selected as rank 1
    assert best["id"] == "CAND_PERFECT"
    assert evidence.candidates_audit[0]["candidate_id"] == "CAND_PERFECT"
    assert evidence.candidates_audit[1]["candidate_id"] == "CAND_SHIFTED"
    assert evidence.candidates_audit[0]["score"] > evidence.candidates_audit[1]["score"]

# -------------------------------------------------------------
# TEST 13: Very Small Parcel (e.g. 45 m²)
# -------------------------------------------------------------
def test_case_13_small_parcel():
    small_poly = to_wgs84(make_poly(0, 0, 7.5, 6.0)) # 45 m²
    cand_poly = to_wgs84(make_poly(0.1, 0.1, 7.5, 6.0))

    drone_feats = [{
        "type": "Feature", "id": "FE_SMALL", "properties": {"feature_id": "FE_SMALL", "survey_candidate": "112/1", "area": 45.0}, "geometry": mapping(cand_poly)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P13", "survey_no": "112", "subdivision_no": "1", "area": 45.0}, "geometry": mapping(small_poly)}
    best, evidence, runners = matcher.match_parcel(legacy)
    assert best is not None
    assert evidence.overall_confidence >= 90.0

# -------------------------------------------------------------
# TEST 14: Large Parcel (e.g. 25,000 m²)
# -------------------------------------------------------------
def test_case_14_large_parcel():
    large_poly = to_wgs84(make_poly(0, 0, 200, 125)) # 25,000 m²
    cand_poly = to_wgs84(make_poly(0.5, 0.5, 200, 125))

    drone_feats = [{
        "type": "Feature", "id": "FE_LARGE", "properties": {"feature_id": "FE_LARGE", "survey_candidate": "113/1", "area": 25000.0}, "geometry": mapping(cand_poly)
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P14", "survey_no": "113", "subdivision_no": "1", "area": 25000.0}, "geometry": mapping(large_poly)}
    best, evidence, runners = matcher.match_parcel(legacy)
    assert best is not None
    assert evidence.overall_confidence >= 90.0

# -------------------------------------------------------------
# TEST 15: Significant Drone vs Legacy Geometry Discrepancy
# -------------------------------------------------------------
def test_case_15_drone_significant_shift():
    # 7.5 meter boundary shift (encroachment)
    legacy_m = make_poly(0, 0, 38, 34)
    shifted_m = translate(legacy_m, xoff=7.5, yoff=5.0) # ~9m displacement

    drone_feats = [{
        "type": "Feature", "id": "FE_SHIFTED", "properties": {"feature_id": "FE_SHIFTED", "survey_candidate": "114/1", "area": 1292.0}, "geometry": mapping(to_wgs84(shifted_m))
    }]
    matcher = ParcelMatcher(drone_feats)
    legacy = {"type": "Feature", "properties": {"parcel_id": "P15", "survey_no": "114", "subdivision_no": "1", "area": 1292.0}, "geometry": mapping(to_wgs84(legacy_m))}
    best, evidence, runners = matcher.match_parcel(legacy)
    # Large boundary shift must trigger hard constraint flags
    assert len(evidence.hard_constraint_flags) > 0
    assert evidence.overall_confidence <= 65.0
    assert any("boundary deviation" in f.lower() for f in evidence.hard_constraint_flags)
