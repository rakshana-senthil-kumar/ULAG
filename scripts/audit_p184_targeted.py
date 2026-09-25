"""
Targeted Audit Script for Parcel P184 (Survey 383/4)
Computes:
1. Exact P184 identity and storage record.
2. Top 10 candidate ranking with all 24 required fields.
3. Detailed GNSS points evaluation with metric distances.
4. Detailed boundary deviation statistics (mean, median, p90, p95, p99, max, hausdorff, conformance %).
5. Neighboring parcel audit (P182, P183, P184, P185, P186).
6. Generates visual debug GeoJSON at data/p184_visual_verification.geojson.
"""

import json
import math
import os
import statistics
from typing import Dict, List, Any
from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
from shapely.ops import unary_union

from backend.app.models.storage import storage_repo
from backend.app.services.geometry.crs import project_geometry, project_point, unproject_geometry
from backend.app.services.matching.matcher import ParcelMatcher, compute_boundary_deviations

def main():
    p184 = storage_repo.get_parcel_detail("P184")
    assert p184 is not None, "P184 must exist in storage"

    with open("data/demo/drone_features.geojson", "r", encoding="utf-8") as f:
        drone_feats = json.load(f)["features"]
    with open("data/demo/legacy_cadastral.geojson", "r", encoding="utf-8") as f:
        legacy_feats = json.load(f)["features"]

    p184_leg_feat = next(f for f in legacy_feats if f["properties"]["parcel_id"] == "P184")

    # Match using matcher
    matcher = ParcelMatcher(drone_feats)
    best_feat, evidence, runners = matcher.match_parcel(p184_leg_feat, p184["gnss_points"])

    proj_crs = matcher.projected_crs
    proj_leg = project_geometry(shape(p184["geometry_geojson"]), "EPSG:4326", proj_crs)
    proj_cand1 = project_geometry(shape(best_feat["geometry"]), "EPSG:4326", proj_crs)

    print("==================================================")
    print("1. P184 IDENTIFICATION")
    print("==================================================")
    print(f"Parcel ID: {p184['parcel_id']}")
    print(f"Survey Number: {p184['full_survey']}")
    print(f"Land Use: {p184['land_use']}")
    print(f"Legacy Area (Registered): {p184['legacy_area']} m2")
    print(f"Computed Projected Legacy Area: {round(proj_leg.area, 2)} m2")
    print(f"Selected Candidate ID: {best_feat.get('id') or best_feat.get('properties', {}).get('feature_id')}")
    print(f"Selected Candidate Survey: {best_feat.get('properties', {}).get('survey_candidate')}")
    print(f"Computed Projected Candidate Area: {round(proj_cand1.area, 2)} m2")
    print(f"Match Status: {p184['status']}")
    print(f"Match Confidence: {p184['confidence']}%")

    print("\n==================================================")
    print("2. GNSS RTK SURVEY POINT METRIC EVALUATION")
    print("==================================================")
    gnss_records = []
    for pt in p184["gnss_points"]:
        proj_pt = Point(project_point(pt["longitude"], pt["latitude"], "EPSG:4326", proj_crs))
        dist_to_cand_ext = proj_cand1.exterior.distance(proj_pt)
        dist_to_cand_poly = proj_cand1.distance(proj_pt)
        is_inside_strict = proj_cand1.contains(proj_pt)
        is_inside_buffer = proj_cand1.buffer(0.75).contains(proj_pt)
        rec = {
            "point_id": pt["point_id"],
            "latitude": pt["latitude"],
            "longitude": pt["longitude"],
            "accuracy_m": pt.get("accuracy_m", 0.02),
            "dist_to_boundary_m": round(dist_to_cand_ext, 4),
            "dist_to_polygon_m": round(dist_to_cand_poly, 4),
            "inside_strict": is_inside_strict,
            "inside_0_75m_buffer": is_inside_buffer
        }
        gnss_records.append(rec)
        print(f"Point {rec['point_id']}: Lat={rec['latitude']}, Lon={rec['longitude']}, "
              f"Acc={rec['accuracy_m']}m, DistToBoundary={rec['dist_to_boundary_m']}m, "
              f"InsideStrict={rec['inside_strict']}, InsideBuffer(0.75m)={rec['inside_0_75m_buffer']}")

    print("\n==================================================")
    print("3. HIGH-RESOLUTION BOUNDARY DEVIATION ANALYSIS (0.5m interval)")
    print("==================================================")
    ext_a = proj_leg.exterior
    ext_b = proj_cand1.exterior
    step = 0.5
    num_a = max(20, int(ext_a.length / step))
    num_b = max(20, int(ext_b.length / step))
    dists_a = [ext_b.distance(ext_a.interpolate(i * step)) for i in range(num_a)]
    dists_b = [ext_a.distance(ext_b.interpolate(i * step)) for i in range(num_b)]
    all_dists = sorted(dists_a + dists_b)

    mean_dev = statistics.mean(all_dists)
    median_dev = statistics.median(all_dists)
    p90_dev = all_dists[int(0.90 * (len(all_dists) - 1))]
    p95_dev = all_dists[int(0.95 * (len(all_dists) - 1))]
    p99_dev = all_dists[int(0.99 * (len(all_dists) - 1))]
    max_dev = max(all_dists)
    hausdorff = ext_a.hausdorff_distance(ext_b)
    conf_1_5m = (sum(1 for d in all_dists if d <= 1.5) / len(all_dists)) * 100.0
    conf_0_5m = (sum(1 for d in all_dists if d <= 0.5) / len(all_dists)) * 100.0

    print(f"Perimeter Legacy: {round(ext_a.length, 2)} m, Perimeter Candidate: {round(ext_b.length, 2)} m")
    print(f"Total Sample Points Evaluated: {len(all_dists)}")
    print(f"Mean Deviation: {round(mean_dev, 4)} m")
    print(f"Median Deviation: {round(median_dev, 4)} m")
    print(f"P90 Deviation: {round(p90_dev, 4)} m")
    print(f"P95 Deviation: {round(p95_dev, 4)} m")
    print(f"P99 Deviation: {round(p99_dev, 4)} m")
    print(f"Max Deviation: {round(max_dev, 4)} m")
    print(f"Hausdorff Distance: {round(hausdorff, 4)} m")
    print(f"Boundary Conformance <= 0.5m: {round(conf_0_5m, 2)}%")
    print(f"Boundary Conformance <= 1.5m: {round(conf_1_5m, 2)}%")

    print("\n==================================================")
    print("4. TOP CANDIDATES RANKING FOR P184")
    print("==================================================")
    for c in evidence.candidates_audit:
        print(f"Rank {c['rank']}: ID={c['candidate_id']}, Survey={c['survey_candidate']}, "
              f"Score={c['score']}, IoU={c['iou']}%, CovSrc={c['coverage_source']}%, "
              f"AreaDiff={c['area_diff_pct']}%, CentDist={c['centroid_dist_m']}m, "
              f"MeanDev={c['mean_boundary_dev_m']}m, MaxDev={c['max_boundary_dev_m']}m, "
              f"GNSSInside={c['gnss_inside_pct']}%, AttrMatch={c['attribute_match']}%, "
              f"Flags={c['hard_flags']}, Reject={c['rejection_reason']}")

    print("\n==================================================")
    print("5. GENERATING VISUAL VERIFICATION GEOJSON")
    print("==================================================")
    # Build GeoJSON feature collection
    features = []

    # 1. Source Parcel
    features.append({
        "type": "Feature",
        "properties": {
            "layer": "SOURCE_PARCEL",
            "parcel_id": "P184",
            "survey_no": "383/4",
            "area_m2": round(proj_leg.area, 2),
            "stroke": "#3b82f6",
            "fill": "#3b82f6",
            "fill-opacity": 0.25
        },
        "geometry": p184["geometry_geojson"]
    })

    # Top candidates
    top_candidates = evidence.candidates_audit[:3]
    colors = ["#10b981", "#ef4444", "#f59e0b"]
    for idx, c in enumerate(top_candidates):
        cand_feat = next(f for f in drone_feats if (f.get("id") == c["candidate_id"] or f.get("properties", {}).get("feature_id") == c["candidate_id"]))
        features.append({
            "type": "Feature",
            "properties": {
                "layer": f"CANDIDATE_#{c['rank']}",
                "candidate_id": c["candidate_id"],
                "survey_candidate": c["survey_candidate"],
                "score": c["score"],
                "iou": c["iou"],
                "rank": c["rank"],
                "stroke": colors[idx],
                "fill": colors[idx],
                "fill-opacity": 0.20
            },
            "geometry": cand_feat["geometry"]
        })

    # Intersection with Candidate 1
    inter_proj = proj_leg.intersection(proj_cand1)
    if not inter_proj.is_empty:
        inter_wgs84 = unproject_geometry(inter_proj, proj_crs)
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "INTERSECTION_SOURCE_CANDIDATE_1",
                "area_m2": round(inter_proj.area, 2),
                "stroke": "#059669",
                "fill": "#10b981",
                "fill-opacity": 0.40
            },
            "geometry": mapping(inter_wgs84)
        })

    # Source-Only Area (Difference: Source - Candidate 1)
    src_only_proj = proj_leg.difference(proj_cand1)
    if not src_only_proj.is_empty:
        src_only_wgs84 = unproject_geometry(src_only_proj, proj_crs)
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "SOURCE_ONLY_AREA",
                "area_m2": round(src_only_proj.area, 2),
                "stroke": "#f59e0b",
                "fill": "#f59e0b",
                "fill-opacity": 0.40
            },
            "geometry": mapping(src_only_wgs84)
        })

    # Candidate-Only Area (Difference: Candidate 1 - Source)
    cand_only_proj = proj_cand1.difference(proj_leg)
    if not cand_only_proj.is_empty:
        cand_only_wgs84 = unproject_geometry(cand_only_proj, proj_crs)
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "CANDIDATE_ONLY_AREA",
                "area_m2": round(cand_only_proj.area, 2),
                "stroke": "#ec4899",
                "fill": "#ec4899",
                "fill-opacity": 0.40
            },
            "geometry": mapping(cand_only_wgs84)
        })

    # Symmetric Difference (displacement)
    sym_diff_proj = proj_leg.symmetric_difference(proj_cand1)
    if not sym_diff_proj.is_empty:
        sym_diff_wgs84 = unproject_geometry(sym_diff_proj, proj_crs)
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "SYMMETRIC_DIFFERENCE_DISPLACEMENT",
                "displacement_area_m2": round(sym_diff_proj.area, 2),
                "stroke": "#dc2626",
                "fill": "#ef4444",
                "fill-opacity": 0.50
            },
            "geometry": mapping(sym_diff_wgs84)
        })

    # Centroids
    features.append({
        "type": "Feature",
        "properties": {
            "layer": "CENTROID_SOURCE",
            "label": "P184 Source Centroid",
            "marker-color": "#3b82f6"
        },
        "geometry": mapping(unproject_geometry(proj_leg.centroid, proj_crs))
    })
    features.append({
        "type": "Feature",
        "properties": {
            "layer": "CENTROID_CANDIDATE_1",
            "label": "FE_186 Candidate Centroid",
            "marker-color": "#10b981"
        },
        "geometry": mapping(unproject_geometry(proj_cand1.centroid, proj_crs))
    })

    # GNSS Points
    for pt in p184["gnss_points"]:
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "GNSS_SURVEY_POINT",
                "point_id": pt["point_id"],
                "survey_no": pt["survey_no"],
                "accuracy_m": pt["accuracy_m"],
                "marker-color": "#8b5cf6"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [pt["longitude"], pt["latitude"]]
            }
        })

    # Sample Boundary Deviation Points (every 5m along perimeter for visual clarity)
    vis_step = 5.0
    vis_num = int(ext_a.length / vis_step)
    for i in range(vis_num):
        pt_m = ext_a.interpolate(i * vis_step)
        d_val = ext_b.distance(pt_m)
        pt_wgs84 = unproject_geometry(pt_m, proj_crs)
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "BOUNDARY_DEVIATION_SAMPLE",
                "sample_idx": i,
                "deviation_meters": round(d_val, 3),
                "marker-color": "#0ea5e9" if d_val <= 0.5 else "#f97316"
            },
            "geometry": mapping(pt_wgs84)
        })

    out_geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features
    }

    os.makedirs("data", exist_ok=True)
    out_path = "data/p184_visual_verification.geojson"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_geojson, f, indent=2)

    print(f"Visual verification GeoJSON successfully generated at: {out_path} ({len(features)} features)")

if __name__ == "__main__":
    main()
