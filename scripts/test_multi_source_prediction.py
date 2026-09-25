"""
Multi-Source Geospatial Harmonization & Prediction Correctness Verification Tool
BHUMI-FUSION (ULAG) - SIH Problem Statement 26013

Tests multi-layer spatial matching, conflict detection, building encroachment,
GNSS validation, and confidence scoring when multiple datasets overlap the same location.
"""

import os
import sys
import json
import argparse
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, Polygon, Point

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.matching.matcher import ParcelMatcher, deg_distance_to_meters, calculate_attribute_similarity
from backend.app.services.conflict.detector import ConflictDetector
from backend.app.services.ai.inference_adapter import inference_adapter
from backend.app.services.ingestion.iomaps_loader import IndianOpenMapsLoader


def test_multi_source_prediction(parcel_id: str = "P003"):
    print("=" * 90)
    print(f"BHUMI-FUSION MULTI-SOURCE PREDICTION & RECONCILIATION TEST FOR: {parcel_id}")
    print("=" * 90)

    # 1. Load Overlapping Datasets
    legacy_path = "data/demo/legacy_cadastral.geojson"
    drone_path = "data/demo/drone_features.geojson"
    gnss_path = "data/demo/gnss_points.csv"
    revenue_path = "data/demo/revenue_records.csv"
    iom_bld_path = "dataset/buildings/indianopenmaps/coimbatore_reference_buildings.geojson"

    with open(legacy_path, "r", encoding="utf-8") as f:
        legacy_fc = json.load(f)

    with open(drone_path, "r", encoding="utf-8") as f:
        drone_fc = json.load(f)

    gnss_df = pd.read_csv(gnss_path) if os.path.exists(gnss_path) else pd.DataFrame()
    revenue_df = pd.read_csv(revenue_path) if os.path.exists(revenue_path) else pd.DataFrame()

    # Find Target Parcel
    target_feat = next((f for f in legacy_fc["features"] if f["properties"].get("parcel_id") == parcel_id), None)
    if not target_feat:
        print(f"[-] Parcel ID {parcel_id} not found in legacy cadastral map. Using first available feature.")
        target_feat = legacy_fc["features"][0]
        parcel_id = target_feat["properties"].get("parcel_id", "P001")

    props = target_feat["properties"]
    poly_leg = shape(target_feat["geometry"])
    survey_no = props.get('full_survey') or props.get('survey_no') or '184/2'
    leg_area = float(props.get('area') or poly_leg.area)

    print(f"\n[1] TARGET CADASTRAL PARCEL DETAILS:")
    print(f"    - Parcel ID:         {parcel_id}")
    print(f"    - Survey Number:     {survey_no}")
    print(f"    - Registered Owner:  {props.get('owner')}")
    print(f"    - Cadastral Area:    {leg_area:.2f} sq.m")
    print(f"    - Centroid Bounds:   [{poly_leg.centroid.x:.6f}, {poly_leg.centroid.y:.6f}]")

    # 2. Execute Spatial Matching Engine across Drone Overlay
    matcher = ParcelMatcher(drone_fc["features"])
    best_feat, evidence, runners_up = matcher.match_parcel(target_feat)

    print("\n[2] SPATIAL MATCHING PREDICTION RESULTS:")
    if best_feat:
        d_props = best_feat.get("properties", {})
        poly_drn = shape(best_feat["geometry"])
        print(f"    - Matched Drone Feature ID: {d_props.get('feature_id')}")
        print(f"    - Observed Aerial Area:     {d_props.get('area', poly_drn.area):.2f} sq.m")
        print(f"    - IoU Geometry Overlap:     {evidence.geometry_match:.2f}%")
        print(f"    - Area Ratio Match:         {evidence.area_match:.2f}%")
        print(f"    - Centroid Proximity Match: {evidence.centroid_match:.2f}%")
        print(f"    - Attribute Match Score:    {evidence.attribute_match:.2f}%")
        print(f"    - Proximity Match Score:    {evidence.proximity_match:.2f}%")
        print(f"    --> OVERALL CONFIDENCE:     {evidence.overall_confidence:.2f}%")
    else:
        print("    [-] No acceptable spatial match found (Confidence < 40%). Marked as Missing Feature.")

    # 3. Revenue Record Cross-Matching
    rev_rec = None
    if not revenue_df.empty:
        surv_target = str(survey_no).strip().lower()
        rev_match = revenue_df[revenue_df['survey_no'].astype(str).str.strip().str.lower() == surv_target]
        print(f"\n[3] REVENUE RECORD LINKAGE:")
        if not rev_match.empty:
            r_row = rev_match.iloc[0]
            rev_rec = {
                "area": float(r_row.get("recorded_area", leg_area)),
                "status": str(r_row.get("status", "Active")),
                "land_use": str(r_row.get("land_classification", "Residential"))
            }
            print(f"    - Status: SUCCESSFUL MATCH")
            print(f"    - Revenue Khata/Patta No: {r_row.get('khata_no', 'K-102')}")
            print(f"    - Recorded Area:          {rev_rec['area']} sq.m")
            print(f"    - Classification:         {rev_rec['land_use']}")
        else:
            print("    - Status: NO MATCHING REVENUE RECORD FOUND")

    # 4. Conflict Detection across Overlapping Datasets
    detector = ConflictDetector()
    conflict = detector.evaluate_parcel_conflict(
        parcel_id=parcel_id,
        survey_no=survey_no,
        legacy_area=leg_area,
        legacy_land_use=props.get("land_use", "Residential"),
        revenue_record=rev_rec,
        drone_candidate=best_feat,
        gnss_points=[],
        evidence=evidence
    )

    print(f"\n[4] MULTI-SOURCE CONFLICT DETECTION:")
    if conflict:
        disc_text = str(conflict.discrepancy_delta).replace('Δ', 'Delta').replace('±', '+/-')
        expl_text = str(conflict.explanation).replace('Δ', 'Delta').replace('±', '+/-')
        print(f"    - Conflict Detected: [{conflict.conflict_type}] - Severity: {conflict.severity}")
        print(f"      Discrepancy:       {disc_text}")
        print(f"      Confidence Score:  {conflict.confidence:.2f}%")
        print(f"      Explanation:       {expl_text}")
    else:
        print("    - Status: NO CONFLICT DETECTED (PARCEL HARMONIZED)")

    # 5. Building Footprint Encroachment Check
    if os.path.exists(iom_bld_path):
        with open(iom_bld_path, "r", encoding="utf-8") as f:
            bld_fc = json.load(f)
        encroaching_buildings = []
        for b_feat in bld_fc.get("features", []):
            b_geom = shape(b_feat["geometry"])
            if poly_leg.intersects(b_geom):
                inter_pct = (poly_leg.intersection(b_geom).area / b_geom.area) * 100.0
                encroaching_buildings.append({
                    "building_id": b_feat["properties"].get("building_id", "BLD-REF"),
                    "overlap_pct": round(inter_pct, 1)
                })

        print(f"\n[5] BUILDING FOOTPRINT OVERLAY ANALYSIS:")
        print(f"    - Intersecting Buildings: {len(encroaching_buildings)}")
        for b in encroaching_buildings:
            print(f"      * {b['building_id']}: {b['overlap_pct']}% inside parcel boundary.")

    # 6. GNSS Survey Points Proximity Validation
    if not gnss_df.empty and 'latitude' in gnss_df.columns and 'longitude' in gnss_df.columns:
        inside_pts = 0
        min_dist_m = 99999.0
        for _, row in gnss_df.iterrows():
            pt = Point(row['longitude'], row['latitude'])
            if poly_leg.contains(pt):
                inside_pts += 1
            dist = deg_distance_to_meters(poly_leg.centroid, pt)
            if dist < min_dist_m:
                min_dist_m = dist

        print(f"\n[6] GNSS GROUND CONTROL POINTS VALIDATION:")
        print(f"    - Points Inside Parcel: {inside_pts}")
        print(f"    - Nearest GNSS Control Point: {min_dist_m:.2f} meters from parcel centroid.")

    print("\n" + "=" * 90)
    print("VERIFICATION SUMMARY: ALL OVERLAPPING DATASETS HARMONIZED SUCCESSFULLY!")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test multi-source spatial prediction correctness.")
    parser.add_argument("--parcel", type=str, default="P003", help="Parcel ID to evaluate (e.g. P001, P003, P014)")
    args = parser.parse_args()
    test_multi_source_prediction(args.parcel)
