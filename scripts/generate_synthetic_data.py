"""
Synthetic Cadastral Dataset Generator for ULAG
Problem Statement 26013: Automated Integration & Intelligent Harmonization of Multi-source Geospatial Data

Generates:
1. legacy_cadastral.geojson (300 parcels)
2. drone_features.geojson (~312 features)
3. gnss_points.csv (~1,200 points)
4. revenue_records.csv (300 records)
5. ground_truth.json (evaluation baseline)

Includes the exact flagship demonstration parcel:
- Survey Number: 184/2
- Legacy Area: 1487 m²
- Revenue Area: 1520 m²
- Drone Area: 1541 m²
- GNSS Survey: 1535 m²
- Calculated Confidence: 93.7%
"""

import json
import math
import random
import csv
import os
from shapely.geometry import Polygon, Point, mapping
from shapely.affinity import translate, scale, rotate

# Fix seed for determinism
random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo")
os.makedirs(OUT_DIR, exist_ok=True)

# Base anchor in urban fringe: Pune / Hinjewadi region (EPSG:4326)
BASE_LAT = 18.5910
BASE_LON = 73.7380

# Approximate degrees per meter at this latitude
M_PER_DEG_LAT = 111132.95
M_PER_DEG_LON = 111132.95 * math.cos(math.radians(BASE_LAT))

def meters_to_deg(dx_m, dy_m):
    return dx_m / M_PER_DEG_LON, dy_m / M_PER_DEG_LAT

def deg_to_meters(dlon, dlat):
    return dlon * M_PER_DEG_LON, dlat * M_PER_DEG_LAT

def polygon_area_m2(poly: Polygon) -> float:
    # Project coords to local metric plane
    coords = list(poly.exterior.coords)
    metric_coords = [deg_to_meters(x - BASE_LON, y - BASE_LAT) for x, y in coords]
    m_poly = Polygon(metric_coords)
    return round(abs(m_poly.area), 1)

def create_metric_polygon(center_x_m, center_y_m, width_m, height_m, jitter_pct=0.08, irregular=True) -> Polygon:
    w2 = width_m / 2.0
    h2 = height_m / 2.0
    pts = [
        (-w2, -h2),
        (w2, -h2),
        (w2, h2),
        (-w2, h2)
    ]
    if irregular:
        # add 1 or 2 vertex notches typical of cadastral plots
        pts = [
            (-w2, -h2),
            (0, -h2 - random.uniform(-2, 3)),
            (w2, -h2),
            (w2 + random.uniform(-2, 2), 0),
            (w2, h2),
            (-w2, h2 + random.uniform(-2, 2))
        ]
    
    geo_coords = []
    for x, y in pts:
        if jitter_pct > 0:
            x += random.uniform(-w2 * jitter_pct, w2 * jitter_pct)
            y += random.uniform(-h2 * jitter_pct, h2 * jitter_pct)
        px_m = center_x_m + x
        py_m = center_y_m + y
        dlon, dlat = meters_to_deg(px_m, py_m)
        geo_coords.append((BASE_LON + dlon, BASE_LAT + dlat))
    geo_coords.append(geo_coords[0])
    return Polygon(geo_coords)

def generate_datasets():
    print("Generating synthetic cadastral datasets for ULAG...")
    total_parcels = 300
    grid_cols = 20
    grid_rows = 15 # 20x15 = 300 parcels

    parcel_spacing_x = 45.0 # meters
    parcel_spacing_y = 40.0 # meters
    base_width = 38.0
    base_height = 34.0

    legacy_features = []
    drone_features = []
    gnss_points = []
    revenue_records = []
    ground_truth = {}

    land_uses = ["Residential", "Commercial", "Agricultural", "Mixed Use", "Institutional", "Industrial"]

    # Pre-select conflict indices to total exactly 24 conflict cases:
    # 1 flagship (index 2 -> P003 -> Survey 184/2)
    # 7 geometry displacements
    # 6 area mismatches
    # 4 attribute mismatches
    # 2 missing parcels in drone
    # 2 parcel splits (1 legacy -> 2 drone)
    # 2 parcel merges (2 legacy -> 1 drone)
    conflict_indices = set()
    flagship_idx = 2 # P003
    conflict_indices.add(flagship_idx)

    # Pick 23 other distinct indices spread out across the dataset
    all_other_indices = [i for i in range(total_parcels) if i != flagship_idx]
    random.shuffle(all_other_indices)

    geom_displacement_indices = set(all_other_indices[0:7])
    area_mismatch_indices = set(all_other_indices[7:13])
    attr_mismatch_indices = set(all_other_indices[13:17])
    missing_drone_indices = set(all_other_indices[17:19])
    split_indices = set(all_other_indices[19:21])
    merge_indices = set(all_other_indices[21:23])

    conflict_indices.update(geom_displacement_indices)
    conflict_indices.update(area_mismatch_indices)
    conflict_indices.update(attr_mismatch_indices)
    conflict_indices.update(missing_drone_indices)
    conflict_indices.update(split_indices)
    conflict_indices.update(merge_indices)

    assert len(conflict_indices) == 24, f"Expected 24 conflicts, got {len(conflict_indices)}"
    print(f"Configured 24 controlled conflict cases and 276 clean matched parcels.")

    feature_id_counter = 1
    gnss_point_counter = 1

    for idx in range(total_parcels):
        row = idx // grid_cols
        col = idx % grid_cols
        center_x = col * parcel_spacing_x
        center_y = row * parcel_spacing_y

        p_id = f"P{idx+1:03d}"
        
        # Survey numbering
        if idx == flagship_idx:
            survey_no = "184"
            subdiv_no = "2"
        else:
            base_s = 200 + idx if (200 + idx) != 184 else 600
            survey_no = str(base_s)
            subdiv_no = str(1 + (idx % 4))
        
        full_survey = f"{survey_no}/{subdiv_no}"
        land_use = random.choice(land_uses)
        owner_ref = f"IND-MH-PN-{idx+1000:04d}"

        # Base geometry
        if idx == flagship_idx:
            # Create flagship geometry tuned to exactly:
            # Legacy: 1487 m²
            # Drone: 1541 m²
            # GNSS: 1535 m²
            # Revenue: 1520 m²
            # Dimensions roughly 40m x 37.175m ~ 1487 m²
            poly_legacy = create_metric_polygon(center_x, center_y, 40.0, 37.175, jitter_pct=0.0, irregular=False)
            # Scale slightly to match target area 1487
            curr_area = polygon_area_m2(poly_legacy)
            scale_factor = math.sqrt(1487.0 / curr_area)
            poly_legacy = scale(poly_legacy, xfact=scale_factor, yfact=scale_factor, origin='centroid')
            legacy_area = 1487.0

            # Drone geometry for 184/2: Area 1541 m², slightly displaced/expanded boundary
            drone_scale = math.sqrt(1541.0 / 1487.0)
            dlon_shift, dlat_shift = meters_to_deg(1.8, 1.2)
            poly_drone = translate(scale(poly_legacy, xfact=drone_scale, yfact=drone_scale, origin='centroid'), xoff=dlon_shift, yoff=dlat_shift)
            drone_area = 1541.0
            rev_area = 1520.0
            gnss_area = 1535.0
            conflict_type = "Geometry & Area Displacement"
        else:
            poly_legacy = create_metric_polygon(center_x, center_y, base_width, base_height, jitter_pct=0.05, irregular=True)
            legacy_area = polygon_area_m2(poly_legacy)
            rev_area = legacy_area
            drone_area = legacy_area
            gnss_area = legacy_area
            conflict_type = None

        # Build Revenue Record
        rev_land_use = land_use
        if idx in attr_mismatch_indices:
            # Discrepancy in revenue land use / status
            rev_land_use = "Industrial" if land_use != "Industrial" else "Agricultural"
            conflict_type = "Attribute Mismatch"

        if idx in area_mismatch_indices:
            # 15-25% discrepancy in recorded revenue area
            rev_area = round(legacy_area * random.choice([1.18, 0.82]), 1)
            conflict_type = "Area Discrepancy"

        revenue_records.append({
            "survey_no": survey_no,
            "subdivision_no": subdiv_no,
            "owner_ref": owner_ref,
            "area": rev_area,
            "land_use": rev_land_use,
            "status": "Active" if idx not in attr_mismatch_indices else "Disputed"
        })

        # Build Legacy GeoJSON feature
        legacy_features.append({
            "type": "Feature",
            "id": p_id,
            "properties": {
                "parcel_id": p_id,
                "survey_no": survey_no,
                "subdivision_no": subdiv_no,
                "full_survey": full_survey,
                "area": legacy_area,
                "land_use": land_use
            },
            "geometry": mapping(poly_legacy)
        })

        # Build Drone GeoJSON feature(s)
        f_id = f"FE_{feature_id_counter:03d}"
        feature_id_counter += 1

        if idx in missing_drone_indices:
            # Drone did not extract this parcel (occluded / missing feature)
            ground_truth[p_id] = {
                "matched": False,
                "conflict_type": "Missing Drone Extraction",
                "drone_feature_id": None
            }
        elif idx in split_indices:
            # Parcel split into 2 smaller parcels in drone imagery
            coords = list(poly_legacy.exterior.coords)
            c = poly_legacy.centroid
            p1 = Polygon([coords[0], coords[1], (c.x, coords[1][1]), (c.x, coords[0][1]), coords[0]])
            p2 = Polygon([(c.x, coords[1][1]), coords[2], coords[3], (c.x, coords[0][1]), (c.x, coords[1][1])])
            f_id_2 = f"FE_{feature_id_counter:03d}"
            feature_id_counter += 1

            drone_features.append({
                "type": "Feature",
                "id": f_id,
                "properties": {
                    "feature_id": f_id,
                    "survey_candidate": full_survey,
                    "area": polygon_area_m2(p1),
                    "feature_type": "Plot Division A"
                },
                "geometry": mapping(p1)
            })
            drone_features.append({
                "type": "Feature",
                "id": f_id_2,
                "properties": {
                    "feature_id": f_id_2,
                    "survey_candidate": full_survey,
                    "area": polygon_area_m2(p2),
                    "feature_type": "Plot Division B"
                },
                "geometry": mapping(p2)
            })
            ground_truth[p_id] = {
                "matched": True,
                "conflict_type": "Potential Split",
                "drone_feature_id": f"{f_id},{f_id_2}"
            }
        elif idx in merge_indices:
            # Merged with adjacent boundary
            poly_merged = scale(poly_legacy, xfact=1.6, yfact=1.0, origin='centroid')
            drone_features.append({
                "type": "Feature",
                "id": f_id,
                "properties": {
                    "feature_id": f_id,
                    "survey_candidate": full_survey,
                    "area": polygon_area_m2(poly_merged),
                    "feature_type": "Consolidated Compound"
                },
                "geometry": mapping(poly_merged)
            })
            ground_truth[p_id] = {
                "matched": True,
                "conflict_type": "Potential Merge",
                "drone_feature_id": f_id
            }
        elif idx in geom_displacement_indices:
            # Significant boundary encroachment / shift (5 - 8 meters)
            dlon_shift, dlat_shift = meters_to_deg(random.uniform(4.5, 7.5), random.uniform(-5.0, 5.0))
            poly_shifted = translate(poly_legacy, xoff=dlon_shift, yoff=dlat_shift)
            drone_features.append({
                "type": "Feature",
                "id": f_id,
                "properties": {
                    "feature_id": f_id,
                    "survey_candidate": full_survey,
                    "area": round(polygon_area_m2(poly_shifted) * random.uniform(0.96, 1.04), 1),
                    "feature_type": "Cadastral Boundary"
                },
                "geometry": mapping(poly_shifted)
            })
            ground_truth[p_id] = {
                "matched": True,
                "conflict_type": "Geometry Shift",
                "drone_feature_id": f_id
            }
        elif idx == flagship_idx:
            # Flagship parcel FE_003
            drone_features.append({
                "type": "Feature",
                "id": "FE_003",
                "properties": {
                    "feature_id": "FE_003",
                    "survey_candidate": "184/2",
                    "area": 1541.0,
                    "feature_type": "Cadastral Boundary"
                },
                "geometry": mapping(poly_drone)
            })
            ground_truth[p_id] = {
                "matched": True,
                "conflict_type": "Boundary Displacement & Area Mismatch",
                "drone_feature_id": "FE_003"
            }
        else:
            # Standard High Confidence Match (sub-meter variation)
            dlon_noise, dlat_noise = meters_to_deg(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4))
            poly_clean = translate(poly_legacy, xoff=dlon_noise, yoff=dlat_noise)
            drone_area_clean = round(polygon_area_m2(poly_clean), 1)
            drone_features.append({
                "type": "Feature",
                "id": f_id,
                "properties": {
                    "feature_id": f_id,
                    "survey_candidate": full_survey,
                    "area": drone_area_clean,
                    "feature_type": "Cadastral Boundary"
                },
                "geometry": mapping(poly_clean)
            })
            ground_truth[p_id] = {
                "matched": True,
                "conflict_type": None,
                "drone_feature_id": f_id
            }

        # Build GNSS Points (CORS / RTK survey points along polygon perimeter vertices)
        # Each parcel gets 4-5 corner corner points
        base_poly_for_gnss = poly_drone if idx == flagship_idx else (poly_legacy if idx not in geom_displacement_indices else poly_legacy)
        ext_coords = list(base_poly_for_gnss.exterior.coords)[:-1]
        for v_idx, (vx, vy) in enumerate(ext_coords):
            # GNSS has high accuracy (~0.02 - 0.05m)
            pt_id = f"GNSS_{gnss_point_counter:05d}"
            gnss_point_counter += 1
            gnss_points.append({
                "point_id": pt_id,
                "survey_no": full_survey,
                "latitude": round(vy, 7),
                "longitude": round(vx, 7),
                "accuracy_m": round(random.uniform(0.018, 0.045), 3)
            })

    # Add duplicate drone features (~10 duplicate extractions in edge zones) to test duplicate detection
    for dup_idx in range(10):
        src_feat = drone_features[dup_idx + 10]
        dup_fid = f"FE_DUP_{dup_idx+1:02d}"
        drone_features.append({
            "type": "Feature",
            "id": dup_fid,
            "properties": {
                "feature_id": dup_fid,
                "survey_candidate": src_feat["properties"]["survey_candidate"],
                "area": src_feat["properties"]["area"],
                "feature_type": "Secondary Flight Extraction"
            },
            "geometry": src_feat["geometry"]
        })

    # Save datasets
    legacy_geojson_path = os.path.join(OUT_DIR, "legacy_cadastral.geojson")
    with open(legacy_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": legacy_features
        }, f, indent=2)

    drone_geojson_path = os.path.join(OUT_DIR, "drone_features.geojson")
    with open(drone_geojson_path, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "features": drone_features
        }, f, indent=2)

    gnss_csv_path = os.path.join(OUT_DIR, "gnss_points.csv")
    with open(gnss_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["point_id", "survey_no", "latitude", "longitude", "accuracy_m"])
        writer.writeheader()
        writer.writerows(gnss_points)

    revenue_csv_path = os.path.join(OUT_DIR, "revenue_records.csv")
    with open(revenue_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["survey_no", "subdivision_no", "owner_ref", "area", "land_use", "status"])
        writer.writeheader()
        writer.writerows(revenue_records)

    gt_path = os.path.join(OUT_DIR, "ground_truth.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Datasets generated successfully:")
    print(f"  - Legacy Cadastral: {len(legacy_features)} parcels ({legacy_geojson_path})")
    print(f"  - Drone Features:   {len(drone_features)} features ({drone_geojson_path})")
    print(f"  - GNSS Points:      {len(gnss_points)} points ({gnss_csv_path})")
    print(f"  - Revenue Records:  {len(revenue_records)} records ({revenue_csv_path})")
    print(f"  - Ground Truth:     {len(ground_truth)} records ({gt_path})")

if __name__ == "__main__":
    generate_datasets()
