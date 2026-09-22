from backend.app.services.ingestion.loader import load_legacy_geojson, load_revenue_csv
import json

with open("data/demo/legacy_cadastral.geojson", "rb") as f:
    leg, _ = load_legacy_geojson(f.read())
with open("data/demo/revenue_records.csv", "rb") as f:
    rev = load_revenue_csv(f.read())

print("Total legacy:", len(leg))
print("Total revenue:", len(rev))

rev_map = {}
for r in rev:
    full = f"{r['survey_no']}/{r['subdivision_no']}"
    rev_map[full] = r

mismatches = []
not_found = []
for p in leg:
    props = p["properties"]
    full = props["full_survey"]
    if full not in rev_map:
        not_found.append(full)
    else:
        if rev_map[full]["land_use"] != props["land_use"]:
            mismatches.append(props["parcel_id"])

print("Not found count:", len(not_found))
print("Land use mismatch count:", len(mismatches), mismatches)
