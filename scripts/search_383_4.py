import json
import csv
import os

print("=== OCCURRENCES OF 383/4 ACROSS DATASETS ===")

# 1. legacy_cadastral.geojson
with open("data/demo/legacy_cadastral.geojson", "r", encoding="utf-8") as f:
    d = json.load(f)
    for feat in d["features"]:
        p = feat["properties"]
        if p.get("survey_no") == "383" or "383/4" in str(p.get("full_survey")):
            print(f"SOURCE: legacy_cadastral.geojson | LAYER: Cadastral | PARCEL_ID: {p.get('parcel_id')} | SURVEY: {p.get('full_survey')} | AREA: {p.get('area')} m2 | GEOM_TYPE: {feat['geometry']['type']}")

# 2. drone_features.geojson
with open("data/demo/drone_features.geojson", "r", encoding="utf-8") as f:
    d = json.load(f)
    for feat in d["features"]:
        p = feat["properties"]
        if p.get("survey_candidate") == "383/4" or "383" in str(p.get("survey_candidate")):
            c_id = feat.get("id") or p.get("feature_id")
            print(f"SOURCE: drone_features.geojson | LAYER: Drone ORI | CANDIDATE_ID: {c_id} | CANDIDATE_SURVEY: {p.get('survey_candidate')} | AREA: {p.get('area')} m2 | GEOM_TYPE: {feat['geometry']['type']}")

# 3. revenue_records.csv
with open("data/demo/revenue_records.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("survey_no") == "383" and row.get("subdivision_no") == "4":
            print(f"SOURCE: revenue_records.csv | LAYER: Revenue (7/12) | SURVEY: {row.get('survey_no')}/{row.get('subdivision_no')} | OWNER: {row.get('owner_name')} | AREA: {row.get('area')} m2 | LAND_USE: {row.get('land_use')}")

# 4. gnss_points.csv
with open("data/demo/gnss_points.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    pts = [row for row in reader if row.get("survey_no") == "383/4"]
    pt_ids = [p["point_id"] for p in pts]
    print(f"SOURCE: gnss_points.csv | LAYER: GNSS RTK Ground Survey | SURVEY: 383/4 | POINTS_COUNT: {len(pts)} | POINT_IDS: {pt_ids}")
