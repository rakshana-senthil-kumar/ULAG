"""
Synthetic & Empirical Tamil Nadu Geospatial Dataset Generator for ULAG
Generates sample datasets and layers matching Tamil Nadu GIS & Municipal inventories:

1. Thematic & Demographic Maps:
   - Distribution of e-Sevai Centres In Tamil Nadu (GeoJSON & CSV)
   - Tamil Nadu Districts (GeoJSON & CSV)
   - Tamil Nadu SC & ST Population Census 2011 (CSV & GeoJSON)
   - Tamil Nadu SC Population Census 2011 (CSV)
   - Tamil Nadu ST Population Census 2011 (CSV)

2. Vector Layers (20 Layers):
   - Aadhar_Enrollment_Center
   - Amma_Unavagam_GCC
   - Anganwadi_Centres
   - Arts_and_Science_Collage
   - Block_Boundary
   - Buildings_Locations
   - Burial_Ground_Locations
   - Bus_shelter_Locations
   - Chennai_Metro_Rail_Route
   - Chennai_Metro_Rail_Station
   - Chennai_Outer_Boundary
   - Chennai_Region_Boundary
   - CMWSSB_Decanting_Location
   - CMWSSB_Sewerage_Pumping_Stations
   - Cold_Storages
   - Common_Service_Centres
   - Community_Farm_Schools_CFS
   - Community_Skill_School_CSS
   - Corporations
   - CUMTA_Outer_Boundary

3. Road Infrastructure:
   - Coimbatore Road Infrastructure (CSV & GeoJSON)
   - Tamil Nadu Municipal Corporations Road Network Inventory (CSV)
"""

import json
import csv
import os
import math
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TN_DATA_DIR = os.path.join(BASE_DIR, "data", "tamil_nadu")
THEMATIC_DIR = os.path.join(TN_DATA_DIR, "thematic_maps")
VECTOR_DIR = os.path.join(TN_DATA_DIR, "vector_layers")
INFRA_DIR = os.path.join(TN_DATA_DIR, "infrastructure")

for d in [TN_DATA_DIR, THEMATIC_DIR, VECTOR_DIR, INFRA_DIR]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------
# 1. TAMIL NADU DISTRICTS & CENSUS 2011 DEMOGRAPHICS
# -------------------------------------------------------------
DISTRICTS_DATA = [
    {"code": "TN-01", "name": "Chennai", "hq": "Chennai", "lat": 13.0827, "lon": 80.2707, "area_sqkm": 426, "tot_pop": 4646732, "sc_pop": 662584, "st_pop": 10227, "literacy": 90.18, "taluks": 16},
    {"code": "TN-02", "name": "Coimbatore", "hq": "Coimbatore", "lat": 11.0168, "lon": 76.9558, "area_sqkm": 4723, "tot_pop": 3458045, "sc_pop": 535496, "st_pop": 28342, "literacy": 83.98, "taluks": 11},
    {"code": "TN-03", "name": "Madurai", "hq": "Madurai", "lat": 9.9252, "lon": 78.1198, "area_sqkm": 3741, "tot_pop": 3038252, "sc_pop": 408480, "st_pop": 11202, "literacy": 83.45, "taluks": 11},
    {"code": "TN-04", "name": "Tiruchirappalli", "hq": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047, "area_sqkm": 4403, "tot_pop": 2722290, "sc_pop": 466847, "st_pop": 18236, "literacy": 83.23, "taluks": 11},
    {"code": "TN-05", "name": "Salem", "hq": "Salem", "lat": 11.6643, "lon": 78.1460, "area_sqkm": 5245, "tot_pop": 3482056, "sc_pop": 579893, "st_pop": 119369, "literacy": 72.86, "taluks": 13},
    {"code": "TN-06", "name": "Tiruppur", "hq": "Tiruppur", "lat": 11.1085, "lon": 77.3411, "area_sqkm": 5186, "tot_pop": 2479052, "sc_pop": 396015, "st_pop": 5427, "literacy": 78.68, "taluks": 9},
    {"code": "TN-07", "name": "Erode", "hq": "Erode", "lat": 11.3410, "lon": 77.7172, "area_sqkm": 5722, "tot_pop": 2251744, "sc_pop": 369803, "st_pop": 22002, "literacy": 72.58, "taluks": 10},
    {"code": "TN-08", "name": "Tirunelveli", "hq": "Tirunelveli", "lat": 8.7139, "lon": 77.7567, "area_sqkm": 6823, "tot_pop": 1665253, "sc_pop": 284126, "st_pop": 5410, "literacy": 82.50, "taluks": 8},
    {"code": "TN-09", "name": "Vellore", "hq": "Vellore", "lat": 12.9165, "lon": 79.1325, "area_sqkm": 3925, "tot_pop": 1614242, "sc_pop": 352104, "st_pop": 19482, "literacy": 79.17, "taluks": 6},
    {"code": "TN-10", "name": "Thoothukudi", "hq": "Thoothukudi", "lat": 8.7642, "lon": 78.1348, "area_sqkm": 4707, "tot_pop": 1750176, "sc_pop": 348120, "st_pop": 4902, "literacy": 86.16, "taluks": 10},
    {"code": "TN-11", "name": "Thanjavur", "hq": "Thanjavur", "lat": 10.7870, "lon": 79.1378, "area_sqkm": 3411, "tot_pop": 2405890, "sc_pop": 455060, "st_pop": 3680, "literacy": 82.64, "taluks": 9},
    {"code": "TN-12", "name": "Dindigul", "hq": "Dindigul", "lat": 10.3673, "lon": 77.9803, "area_sqkm": 6266, "tot_pop": 2159775, "sc_pop": 452140, "st_pop": 8214, "literacy": 76.26, "taluks": 10},
    {"code": "TN-13", "name": "Kanchipuram", "hq": "Kanchipuram", "lat": 12.8342, "lon": 79.7036, "area_sqkm": 1704, "tot_pop": 1166401, "sc_pop": 282405, "st_pop": 16420, "literacy": 84.49, "taluks": 5},
    {"code": "TN-14", "name": "Tiruvallur", "hq": "Tiruvallur", "lat": 13.1432, "lon": 79.9082, "area_sqkm": 3422, "tot_pop": 3728104, "sc_pop": 821190, "st_pop": 47210, "literacy": 84.03, "taluks": 9},
    {"code": "TN-15", "name": "Cuddalore", "hq": "Cuddalore", "lat": 11.7480, "lon": 79.7714, "area_sqkm": 3678, "tot_pop": 2605914, "sc_pop": 763914, "st_pop": 15420, "literacy": 78.04, "taluks": 10},
    {"code": "TN-16", "name": "Viluppuram", "hq": "Viluppuram", "lat": 11.9401, "lon": 79.4861, "area_sqkm": 3725, "tot_pop": 2092700, "sc_pop": 586320, "st_pop": 48120, "literacy": 71.88, "taluks": 9},
    {"code": "TN-17", "name": "Tiruvannamalai", "hq": "Tiruvannamalai", "lat": 12.2253, "lon": 79.0747, "area_sqkm": 6191, "tot_pop": 2464875, "sc_pop": 565240, "st_pop": 91240, "literacy": 74.21, "taluks": 12},
    {"code": "TN-18", "name": "Dharmapuri", "hq": "Dharmapuri", "lat": 12.1211, "lon": 78.1582, "area_sqkm": 4497, "tot_pop": 1506843, "sc_pop": 245210, "st_pop": 63210, "literacy": 68.54, "taluks": 7},
    {"code": "TN-19", "name": "Krishnagiri", "hq": "Krishnagiri", "lat": 12.5186, "lon": 78.2137, "area_sqkm": 5143, "tot_pop": 1879809, "sc_pop": 267320, "st_pop": 22140, "literacy": 71.46, "taluks": 8},
    {"code": "TN-20", "name": "Namakkal", "hq": "Namakkal", "lat": 11.2189, "lon": 78.1674, "area_sqkm": 3368, "tot_pop": 1726601, "sc_pop": 345120, "st_pop": 57840, "literacy": 74.63, "taluks": 8},
    {"code": "TN-21", "name": "Nilgiris", "hq": "Udhagamandalam", "lat": 11.4102, "lon": 76.6950, "area_sqkm": 2549, "tot_pop": 735394, "sc_pop": 235840, "st_pop": 32813, "literacy": 85.20, "taluks": 6},
    {"code": "TN-22", "name": "Kanyakumari", "hq": "Nagercoil", "lat": 8.1833, "lon": 77.4119, "area_sqkm": 1672, "tot_pop": 1870374, "sc_pop": 74210, "st_pop": 7820, "literacy": 91.75, "taluks": 6},
]

def make_district_polygon(lon: float, lat: float, delta: float = 0.22) -> Dict[str, Any]:
    """Generates an illustrative boundary polygon around district centroid."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [round(lon - delta, 5), round(lat - delta * 0.8, 5)],
            [round(lon + delta, 5), round(lat - delta * 0.9, 5)],
            [round(lon + delta * 1.1, 5), round(lat + delta * 0.7, 5)],
            [round(lon - delta * 0.8, 5), round(lat + delta, 5)],
            [round(lon - delta, 5), round(lat - delta * 0.8, 5)]
        ]]
    }

def generate_thematic_maps():
    print("Generating Tamil Nadu Thematic & Demographic Datasets...")
    
    # 1. Districts GeoJSON
    dist_features = []
    for d in DISTRICTS_DATA:
        sc_pct = round((d["sc_pop"] / d["tot_pop"]) * 100, 2)
        st_pct = round((d["st_pop"] / d["tot_pop"]) * 100, 2)
        combined_sc_st = d["sc_pop"] + d["st_pop"]
        combined_pct = round((combined_sc_st / d["tot_pop"]) * 100, 2)

        dist_features.append({
            "type": "Feature",
            "id": d["code"],
            "properties": {
                "district_code": d["code"],
                "district_name": d["name"],
                "headquarters": d["hq"],
                "area_sq_km": d["area_sqkm"],
                "total_population": d["tot_pop"],
                "sc_population": d["sc_pop"],
                "sc_percentage": sc_pct,
                "st_population": d["st_pop"],
                "st_percentage": st_pct,
                "sc_st_combined_population": combined_sc_st,
                "sc_st_combined_percentage": combined_pct,
                "literacy_rate": d["literacy"],
                "taluks_count": d["taluks"],
                "centroid": [d["lon"], d["lat"]]
            },
            "geometry": make_district_polygon(d["lon"], d["lat"])
        })

    dist_geojson_path = os.path.join(THEMATIC_DIR, "tamil_nadu_districts.geojson")
    with open(dist_geojson_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": dist_features}, f, indent=2)

    # 2. SC & ST Combined Population Census 2011 CSV
    sc_st_csv_path = os.path.join(THEMATIC_DIR, "tn_sc_st_population_census2011.csv")
    with open(sc_st_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["District Code", "District Name", "Total Persons", "SC Population", "SC Percentage", "ST Population", "ST Percentage", "Combined SC/ST Population", "Combined Percentage"])
        for d in DISTRICTS_DATA:
            sc_p = round((d["sc_pop"] / d["tot_pop"]) * 100, 2)
            st_p = round((d["st_pop"] / d["tot_pop"]) * 100, 2)
            comb = d["sc_pop"] + d["st_pop"]
            comb_p = round((comb / d["tot_pop"]) * 100, 2)
            writer.writerow([d["code"], d["name"], d["tot_pop"], d["sc_pop"], sc_p, d["st_pop"], st_p, comb, comb_p])

    # 3. SC Population Census 2011 CSV
    sc_csv_path = os.path.join(THEMATIC_DIR, "tn_sc_population_census2011.csv")
    with open(sc_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["District Code", "District Name", "Total SC Population", "SC Male", "SC Female", "SC Literacy Rate", "SC Rural Percentage", "SC Urban Percentage"])
        for d in DISTRICTS_DATA:
            sc_m = int(d["sc_pop"] * 0.498)
            sc_f = d["sc_pop"] - sc_m
            writer.writerow([d["code"], d["name"], d["sc_pop"], sc_m, sc_f, round(d["literacy"] * 0.94, 2), 64.2, 35.8])

    # 4. ST Population Census 2011 CSV
    st_csv_path = os.path.join(THEMATIC_DIR, "tn_st_population_census2011.csv")
    with open(st_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["District Code", "District Name", "Total ST Population", "ST Male", "ST Female", "Prominent Tribal Groups", "ST Literacy Rate", "Forest Area Pct"])
        for d in DISTRICTS_DATA:
            st_m = int(d["st_pop"] * 0.505)
            st_f = d["st_pop"] - st_m
            writer.writerow([d["code"], d["name"], d["st_pop"], st_m, st_f, "Irular, Malayali, Toda, Kota, Kurumbas", round(d["literacy"] * 0.78, 2), 21.4])

    # 5. e-Sevai Centres Distribution (GeoJSON & CSV)
    e_sevai_features = []
    e_sevai_rows = []
    sevai_id = 1
    for d in DISTRICTS_DATA:
        # Generate 4-8 representative e-Sevai centres per district
        num_centres = 6 if d["name"] in ["Chennai", "Coimbatore", "Madurai"] else 4
        for i in range(num_centres):
            cid = f"ESV-TN-{sevai_id:04d}"
            cname = f"e-Sevai Centre - {d['name']} Centre #{i+1}"
            clat = d["lat"] + (i * 0.015 - 0.03)
            clon = d["lon"] + (i * 0.018 - 0.03)
            footfall = 140 + (i * 25)
            agency = "TACTV (Tamil Nadu Arasu Cable TV Corporation)" if i % 2 == 0 else "PACCS / VLE"
            
            feat = {
                "type": "Feature",
                "id": cid,
                "properties": {
                    "centre_id": cid,
                    "centre_name": cname,
                    "district": d["name"],
                    "operating_agency": agency,
                    "services": "Patta/Chitta, Income Certificate, Community Certificate, Encumbrance, Aadhar Services, Utility Bills",
                    "daily_avg_footfall": footfall,
                    "status": "Active / Operational",
                    "working_hours": "09:30 AM - 05:30 PM",
                    "latitude": round(clat, 5),
                    "longitude": round(clon, 5)
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(clon, 5), round(clat, 5)]
                }
            }
            e_sevai_features.append(feat)
            e_sevai_rows.append([cid, cname, d["name"], agency, footfall, "Active", round(clat, 5), round(clon, 5)])
            sevai_id += 1

    e_sevai_geojson_path = os.path.join(THEMATIC_DIR, "tn_e_sevai_centres.geojson")
    with open(e_sevai_geojson_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": e_sevai_features}, f, indent=2)

    e_sevai_csv_path = os.path.join(THEMATIC_DIR, "tn_e_sevai_centres.csv")
    with open(e_sevai_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Centre ID", "Centre Name", "District", "Agency", "Daily Footfall", "Status", "Latitude", "Longitude"])
        writer.writerows(e_sevai_rows)

    print(f"Generated Thematic Maps in {THEMATIC_DIR}")

# -------------------------------------------------------------
# 2. VECTOR GIS LAYERS (20 LAYERS)
# -------------------------------------------------------------
def generate_vector_layers():
    print("Generating 20 Vector GIS Layers...")

    # Helper to save geojson
    def save_layer(layer_name: str, features: List[Dict[str, Any]]):
        path = os.path.join(VECTOR_DIR, f"{layer_name}.geojson")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "type": "FeatureCollection",
                "name": layer_name,
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "features": features
            }, f, indent=2)

    # 1. Aadhar_Enrollment_Center
    save_layer("Aadhar_Enrollment_Center", [
        {
            "type": "Feature",
            "id": f"AEC_{i+1:03d}",
            "properties": {
                "center_id": f"AEC_{i+1:03d}",
                "name": name,
                "center_type": "Bank / Post Office / GCC Center",
                "address": addr,
                "district": dist,
                "pin_code": pin,
                "contact": "+91 44 2561 9200",
                "status": "Operational"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, addr, dist, pin, lon, lat) in enumerate([
            ("Rippon Building UIDAI Center", "GCC Headquarters, EVR Periyar Salai, Park Town", "Chennai", 600003, 80.2764, 13.0827),
            ("Mylapore Post Office Aadhaar Kiosk", "Kutchery Road, Mylapore", "Chennai", 600004, 80.2685, 13.0339),
            ("T. Nagar Head Post Office AEC", "Prakasam Road, T. Nagar", "Chennai", 600017, 80.2337, 13.0418),
            ("Anna Nagar GCC Regional Office AEC", "3rd Avenue, Anna Nagar East", "Chennai", 600102, 80.2185, 13.0850),
            ("Adyar Corporation Community Hall AEC", "Lattice Bridge Road, Adyar", "Chennai", 600020, 80.2565, 13.0012),
            ("Coimbatore Corporation Central Aadhaar Seva Kendra", "Town Hall, Raja Street", "Coimbatore", 641001, 76.9616, 11.0018),
            ("Gandhipuram Post Office Aadhaar Center", "Cross Cut Road, Gandhipuram", "Coimbatore", 641012, 76.9678, 11.0183),
            ("RS Puram Citizen Service Facilitation Center", "DB Road, RS Puram", "Coimbatore", 641002, 76.9482, 11.0089)
        ])
    ])

    # 2. Amma_Unavagam_GCC
    save_layer("Amma_Unavagam_GCC", [
        {
            "type": "Feature",
            "id": f"AU_{i+1:03d}",
            "properties": {
                "canteen_id": f"AU_{i+1:03d}",
                "name": f"Amma Unavagam - {zone_name}",
                "gcc_zone": zone_no,
                "ward_no": ward,
                "menu": "Idli (Re 1), Sambar Rice (Rs 5), Curd Rice (Rs 3), Chapati (Rs 3)",
                "beneficiaries_daily": daily,
                "women_shg_operating": shg,
                "status": "Functional"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (zone_name, zone_no, ward, daily, shg, lon, lat) in enumerate([
            ("Royapuram GH", "Zone 5 (Royapuram)", 54, 1200, "Annai Theresa Magalir Kuzhu", 80.2882, 13.1042),
            ("Thiru-Vi-Ka Nagar Market", "Zone 6 (Thiru-Vi-Ka Nagar)", 72, 950, "Bharathiyar SHG", 80.2450, 13.1118),
            ("Ambattur Estate Road", "Zone 7 (Ambattur)", 82, 1100, "Vaanavil SHG", 80.1620, 13.0980),
            ("Kilpauk Medical College Hospital", "Zone 8 (Anna Nagar)", 102, 1400, "Karpagam SHG", 80.2432, 13.0805),
            ("Teynampet DMS Complex", "Zone 9 (Teynampet)", 118, 1300, "Semmozhi SHG", 80.2480, 13.0450),
            ("Kodambakkam Trustpuram", "Zone 10 (Kodambakkam)", 131, 850, "Malar SHG", 80.2240, 13.0520),
            ("Adyar Shastri Nagar", "Zone 13 (Adyar)", 175, 1050, "Poompuhar SHG", 80.2590, 12.9980)
        ])
    ])

    # 3. Anganwadi_Centres
    save_layer("Anganwadi_Centres", [
        {
            "type": "Feature",
            "id": f"AW_{i+1:03d}",
            "properties": {
                "anganwadi_id": f"AW_{i+1:03d}",
                "project_name": "ICDS Urban Project Tamil Nadu",
                "center_name": f"Anganwadi Child Care Center - {loc}",
                "children_enrolled": count,
                "nutrition_scheme": "Puratchi Thalaivar MGR Nutritious Meal Programme",
                "worker_name": worker,
                "contact": "+91 94440 12345"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (loc, count, worker, lon, lat) in enumerate([
            ("Perambur Subbarayan Nagar", 42, "Tmt. Lakshmi R", 80.2380, 13.1080),
            ("Triplicane Canal Bank", 38, "Tmt. Revathi M", 80.2780, 13.0550),
            ("Saidapet West Todd Hunter Nagar", 45, "Tmt. Jayanthi K", 80.2210, 13.0210),
            ("Velachery Gandhi Salai", 50, "Tmt. Sumathi S", 80.2240, 12.9810),
            ("Coimbatore Ramanathapuram Ward 64", 36, "Tmt. Vasantha P", 76.9920, 10.9980),
            ("Coimbatore Saibaba Colony Ward 22", 40, "Tmt. Selvi G", 76.9420, 11.0260)
        ])
    ])

    # 4. Arts_and_Science_Collage
    save_layer("Arts_and_Science_Collage", [
        {
            "type": "Feature",
            "id": f"COL_{i+1:03d}",
            "properties": {
                "institution_id": f"COL_{i+1:03d}",
                "institution_name": name,
                "affiliation": affil,
                "established_year": yr,
                "naac_grade": naac,
                "campus_area_acres": acres,
                "type": "Government / Aided / Autonomous"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, affil, yr, naac, acres, lon, lat) in enumerate([
            ("Presidency College (Autonomous)", "University of Madras", 1840, "A+", 22.5, 80.2828, 13.0617),
            ("Madras Christian College (MCC)", "University of Madras", 1837, "A++", 320.0, 80.1235, 12.9238),
            ("Loyola College (Autonomous)", "University of Madras", 1925, "A++", 96.0, 80.2355, 13.0633),
            ("Queen Mary's College (Autonomous)", "University of Madras", 1914, "A", 17.0, 80.2801, 13.0475),
            ("PSG College of Arts and Science", "Bharathiar University", 1947, "A++", 85.0, 77.0340, 11.0340),
            ("Government Arts College, Coimbatore", "Bharathiar University", 1852, "A", 28.0, 76.9740, 11.0020)
        ])
    ])

    # 5. Block_Boundary
    save_layer("Block_Boundary", [
        {
            "type": "Feature",
            "id": f"BLK_{i+1:03d}",
            "properties": {
                "block_code": f"TN-BLK-{i+1:03d}",
                "block_name": b_name,
                "district": dist,
                "panchayats_count": panchayats,
                "rural_population": pop,
                "area_sq_km": area
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [round(lon - 0.04, 5), round(lat - 0.04, 5)],
                    [round(lon + 0.04, 5), round(lat - 0.04, 5)],
                    [round(lon + 0.04, 5), round(lat + 0.04, 5)],
                    [round(lon - 0.04, 5), round(lat + 0.04, 5)],
                    [round(lon - 0.04, 5), round(lat - 0.04, 5)]
                ]]
            }
        }
        for i, (b_name, dist, panchayats, pop, area, lon, lat) in enumerate([
            ("St. Thomas Mount Block", "Chengalpattu", 15, 210000, 125.4, 80.1800, 12.9600),
            ("Kattankulathur Block", "Chengalpattu", 39, 185000, 240.2, 80.0400, 12.8200),
            ("Villivakkam Block", "Tiruvallur", 13, 142000, 110.8, 80.1500, 13.1200),
            ("Periyanayakkanpalayam Block", "Coimbatore", 9, 168000, 195.0, 76.9300, 11.1400),
            ("Thondamuthur Block", "Coimbatore", 10, 145000, 215.6, 76.8200, 10.9800)
        ])
    ])

    # 6. Buildings_Locations
    save_layer("Buildings_Locations", [
        {
            "type": "Feature",
            "id": f"BLD_{i+1:03d}",
            "properties": {
                "building_id": f"BLD_{i+1:03d}",
                "building_name": name,
                "use_category": cat,
                "floors": flr,
                "footprint_area_sqm": area,
                "construction_year": yr
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [round(lon - 0.0008, 6), round(lat - 0.0006, 6)],
                    [round(lon + 0.0008, 6), round(lat - 0.0006, 6)],
                    [round(lon + 0.0008, 6), round(lat + 0.0006, 6)],
                    [round(lon - 0.0008, 6), round(lat + 0.0006, 6)],
                    [round(lon - 0.0008, 6), round(lat - 0.0006, 6)]
                ]]
            }
        }
        for i, (name, cat, flr, area, yr, lon, lat) in enumerate([
            ("Ripon Building - GCC Secretariat", "Government / Heritage", 3, 7800, 1913, 80.2764, 13.0827),
            ("Tamil Nadu Legislative Assembly Secretariat (Fort St. George)", "State Government", 4, 14200, 1644, 80.2872, 13.0795),
            ("Madras High Court Administrative Block", "Judiciary", 3, 12500, 1892, 80.2870, 13.0878),
            ("Coimbatore Municipal Corporation Head Office", "Municipal Civic Center", 4, 6200, 1985, 76.9620, 11.0020),
            ("CMDA Thalamuthu Natarajan Maaligai", "Urban Development Authority", 10, 11500, 1982, 80.2610, 13.0780),
            ("TIDEL Park IT Complex", "Commercial IT / SEZ", 13, 28000, 2000, 80.2470, 12.9890)
        ])
    ])

    # 7. Burial_Ground_Locations
    save_layer("Burial_Ground_Locations", [
        {
            "type": "Feature",
            "id": f"BG_{i+1:03d}",
            "properties": {
                "facility_id": f"BG_{i+1:03d}",
                "name": name,
                "facility_type": f_type,
                "crematorium_units": gas_units,
                "maintaining_authority": auth,
                "area_acres": acres
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, f_type, gas_units, auth, acres, lon, lat) in enumerate([
            ("Mylapore Electric Crematorium", "Gasifier & Electric Crematorium", 2, "Greater Chennai Corporation", 4.2, 80.2740, 13.0310),
            ("Besant Nagar Cremation Ground", "LPG Crematorium & Burial Grounds", 2, "Greater Chennai Corporation", 6.5, 80.2670, 12.9990),
            ("Kilpauk Cemetery & Crematorium", "Crematorium & Multi-faith Cemetery", 2, "Greater Chennai Corporation", 8.0, 80.2400, 13.0780),
            ("Otteri Cremation Grounds", "Electric Crematorium", 2, "Greater Chennai Corporation", 5.0, 80.2520, 13.0940),
            ("Coimbatore Sungam Gas Crematorium", "LPG Gas Crematorium", 3, "Coimbatore City Municipal Corporation", 4.8, 76.9820, 10.9940)
        ])
    ])

    # 8. Bus_shelter_Locations
    save_layer("Bus_shelter_Locations", [
        {
            "type": "Feature",
            "id": f"BS_{i+1:03d}",
            "properties": {
                "shelter_id": f"BS_{i+1:03d}",
                "bus_stop_name": name,
                "corridor_road": corridor,
                "shelter_type": "Stainless Steel Modern Shelter / Digital Display",
                "routes_served": routes,
                "depot": depot
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, corridor, routes, depot, lon, lat) in enumerate([
            ("Central Railway Station Bus Stop", "Poonamallee High Road", "15B, 17D, 27B, 11G, 54, 570", "Central Depot", 80.2740, 13.0820),
            ("Anna Flyover / Gemini Stop", "Anna Salai (Mount Road)", "18A, 23C, 29C, 51A, A1", "Teynampet Depot", 80.2510, 13.0520),
            ("T. Nagar Panagal Park Bus Stand", "Usman Road", "47A, 47D, 12B, 11H, 29C", "T. Nagar Depot", 80.2310, 13.0400),
            ("Adyar Signal Bus Stop", "Lattice Bridge Road / Sardar Patel Road", "29C, 5E, 23C, 570, 19B", "Adyar Depot", 80.2580, 13.0060),
            ("Koyambedu CMBT Arterial Stop", "Jawaharlal Nehru Road (100 Ft Rd)", "153, 570, 70, 114, 27C", "Koyambedu Depot", 80.2050, 13.0690),
            ("Coimbatore Gandhipuram Central Bus Shelter", "Dr. Nanjappa Road", "1C, 7C, 11A, 22, 70", "Gandhipuram Depot", 76.9680, 11.0170)
        ])
    ])

    # 9. Chennai_Metro_Rail_Route
    save_layer("Chennai_Metro_Rail_Route", [
        {
            "type": "Feature",
            "id": "CMRL_LINE_1",
            "properties": {
                "line_id": "CMRL-L1",
                "line_name": "Blue Line (Corridor 1)",
                "terminal_stations": "Wimco Nagar Depot <-> Chennai International Airport",
                "length_km": 32.65,
                "status": "Operational",
                "track_gauge": "Standard Gauge (1435 mm)",
                "traction": "25 kV AC Overhead Catenary"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [80.3080, 13.1650], [80.2920, 13.1250], [80.2850, 13.0980], [80.2760, 13.0820],
                    [80.2640, 13.0640], [80.2500, 13.0460], [80.2380, 13.0300], [80.2180, 13.0080],
                    [80.1980, 12.9920], [80.1650, 12.9810]
                ]
            }
        },
        {
            "type": "Feature",
            "id": "CMRL_LINE_2",
            "properties": {
                "line_id": "CMRL-L2",
                "line_name": "Green Line (Corridor 2)",
                "terminal_stations": "Puratchi Thalaivar Dr. M.G. Ramachandran Central <-> St. Thomas Mount",
                "length_km": 22.0,
                "status": "Operational",
                "track_gauge": "Standard Gauge (1435 mm)",
                "traction": "25 kV AC Overhead Catenary"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [80.2760, 13.0820], [80.2450, 13.0810], [80.2180, 13.0850], [80.2050, 13.0690],
                    [80.2080, 13.0420], [80.2120, 13.0240], [80.1980, 12.9920]
                ]
            }
        }
    ])

    # 10. Chennai_Metro_Rail_Station
    save_layer("Chennai_Metro_Rail_Station", [
        {
            "type": "Feature",
            "id": f"CMRL_STN_{i+1:02d}",
            "properties": {
                "station_id": f"CMRL-S{i+1:02d}",
                "station_name": stn,
                "line": line,
                "type": stn_type,
                "interchange": inter,
                "daily_footfall": footfall,
                "accessibility": "Full Barrier-free, Elevators, Tactile Flooring"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (stn, line, stn_type, inter, footfall, lon, lat) in enumerate([
            ("Chennai Central Metro", "Blue & Green Line Interchange", "Underground", "Chennai Central Suburban & Southern Railway Hub", 38000, 80.2760, 13.0820),
            ("Government Estate", "Blue Line", "Underground", "Omandurar Medical Multi-Speciality", 18500, 80.2700, 13.0680),
            ("AG-DMS", "Blue Line", "Underground", "Directorate of Medical Services", 16200, 80.2490, 13.0450),
            ("Nandanam", "Blue Line", "Underground", "Anna Salai Junction", 14800, 80.2390, 13.0310),
            ("Guindy Metro", "Blue Line", "Elevated", "Guindy Suburban Railway Hub", 26500, 80.2140, 13.0080),
            ("Chennai Airport Metro", "Blue Line Terminal", "Elevated", "Chennai International Airport T1/T4", 32000, 80.1650, 12.9810),
            ("Koyambedu Metro", "Green Line", "Elevated", "CMBT Bus Terminal & Market Hub", 29000, 80.2050, 13.0690),
            ("Anna Nagar East", "Green Line", "Underground", "Residential & Commercial Center", 15200, 80.2180, 13.0850)
        ])
    ])

    # 11. Chennai_Outer_Boundary (GCC Limit - 426 sq km)
    save_layer("Chennai_Outer_Boundary", [{
        "type": "Feature",
        "id": "GCC_BOUNDARY_426SQKM",
        "properties": {
            "entity": "Greater Chennai Corporation (GCC)",
            "jurisdiction": "15 Zones, 200 Wards",
            "statutory_area_sq_km": 426.0,
            "population_2011": 4646732,
            "estimated_current_pop": 7100000,
            "crs": "EPSG:4326"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [80.1800, 13.2100], [80.3150, 13.2000], [80.3350, 13.1200], [80.2950, 12.9800],
                [80.2550, 12.8700], [80.1900, 12.8900], [80.1300, 12.9900], [80.1200, 13.1100],
                [80.1800, 13.2100]
            ]]
        }
    }])

    # 12. Chennai_Region_Boundary (CMA Limit - 1,189 sq km)
    save_layer("Chennai_Region_Boundary", [{
        "type": "Feature",
        "id": "CMA_BOUNDARY_1189SQKM",
        "properties": {
            "entity": "Chennai Metropolitan Area (CMA)",
            "planning_authority": "Chennai Metropolitan Development Authority (CMDA)",
            "area_sq_km": 1189.0,
            "includes": "Chennai District + parts of Tiruvallur, Kanchipuram, Chengalpattu Districts",
            "master_plan": "Third Master Plan for CMA (2026-2046)"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [80.1200, 13.3400], [80.3600, 13.3100], [80.3800, 13.1200], [80.3100, 12.8000],
                [80.1800, 12.7200], [79.9800, 12.7900], [79.9200, 13.0500], [80.0100, 13.2800],
                [80.1200, 13.3400]
            ]]
        }
    }])

    # 13. CMWSSB_Decanting_Location
    save_layer("CMWSSB_Decanting_Location", [
        {
            "type": "Feature",
            "id": f"CMWSSB_DEC_{i+1:02d}",
            "properties": {
                "decanting_point_id": f"DEC-TN-{i+1:02d}",
                "location_name": name,
                "sewage_treatment_plant_linked": stp,
                "tanker_lorry_capacity_daily": tankers,
                "operating_agency": "Chennai Metropolitan Water Supply and Sewerage Board",
                "monitoring": "Automated Flow Metres & Bio-sensor SCADA"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, stp, tankers, lon, lat) in enumerate([
            ("Koyambedu Decanting Facility", "Koyambedu 120 MLD STP", 350, 80.1980, 13.0640),
            ("Nesapakkam Decanting Station", "Nesapakkam 114 MLD STP", 280, 80.1920, 13.0290),
            ("Perungudi OMR Decanting Depot", "Perungudi 126 MLD STP", 420, 80.2360, 12.9550),
            ("Kodungaiyur North Decanting Hub", "Kodungaiyur 270 MLD STP", 500, 80.2620, 13.1360)
        ])
    ])

    # 14. CMWSSB_Sewerage_Pumping_Stations
    save_layer("CMWSSB_Sewerage_Pumping_Stations", [
        {
            "type": "Feature",
            "id": f"CMWSSB_SPS_{i+1:02d}",
            "properties": {
                "station_id": f"SPS-TN-{i+1:02d}",
                "sps_name": f"{loc} Sewage Pumping Station",
                "pumping_capacity_mld": mld,
                "generators_standby_kva": gen,
                "scada_connected": True,
                "authority": "CMWSSB Sewerage Infrastructure Wing"
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (loc, mld, gen, lon, lat) in enumerate([
            ("Purasawalkam SPS", 45.0, 750, 80.2540, 13.0910),
            ("T. Nagar North SPS", 60.0, 1000, 80.2380, 13.0480),
            ("Adyar Greenways SPS", 55.0, 1000, 80.2620, 13.0180),
            ("Velachery Main Road SPS", 40.0, 625, 80.2200, 12.9820),
            ("Anna Nagar Central SPS", 50.0, 750, 80.2100, 13.0880)
        ])
    ])

    # 15. Cold_Storages
    save_layer("Cold_Storages", [
        {
            "type": "Feature",
            "id": f"CS_{i+1:02d}",
            "properties": {
                "storage_id": f"CS-TN-{i+1:02d}",
                "facility_name": name,
                "commodities_handled": items,
                "capacity_metric_tons": mt,
                "temperature_range_celsius": temp,
                "district": dist
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, items, mt, temp, dist, lon, lat) in enumerate([
            ("Koyambedu Wholesale Perishable Cold Hub", "Fruits, Vegetables, Flowers", 12000, "0°C to +8°C", "Chennai", 80.2020, 13.0670),
            ("Madhavaram Dairy & Agri Cold Storage", "Milk, Dairy Products, Frozen Poultry", 8500, "-18°C to +4°C", "Chennai", 80.2310, 13.1480),
            ("Coimbatore Mettupalayam Road Cold Complex", "Potatoes, Carrots, Hill Produce", 15000, "+2°C to +6°C", "Coimbatore", 76.9450, 11.0520),
            ("Pollachi Agro Processing Cold Unit", "Coconut, Tender Coconut Kernels, Spices", 6000, "+4°C to +10°C", "Coimbatore", 77.0080, 10.6580)
        ])
    ])

    # 16. Common_Service_Centres
    save_layer("Common_Service_Centres", [
        {
            "type": "Feature",
            "id": f"CSC_{i+1:03d}",
            "properties": {
                "csc_id": f"CSC-TN-{i+1:03d}",
                "vle_name": vle,
                "center_location": loc,
                "district": dist,
                "digital_services": "PM-Kisan, Digital Seva, PAN Card, Ayushman Bharat, Insurance, Land Mutation Support",
                "monthly_transactions": trans
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (vle, loc, dist, trans, lon, lat) in enumerate([
            ("S. Murugesan VLE", "Thiruvanmiyur Bus Terminus", "Chennai", 480, 80.2600, 12.9860),
            ("P. Sundaram VLE", "Kolathur Market Salai", "Chennai", 520, 80.2180, 13.1250),
            ("K. Selvam VLE", "Peelamedu Main Bazaar", "Coimbatore", 610, 77.0180, 11.0280),
            ("M. Natarajan VLE", "Saravanampatti Tech Corridor", "Coimbatore", 580, 76.9980, 11.0780)
        ])
    ])

    # 17. Community_Farm_Schools_CFS
    save_layer("Community_Farm_Schools_CFS", [
        {
            "type": "Feature",
            "id": f"CFS_{i+1:02d}",
            "properties": {
                "school_id": f"CFS-TN-{i+1:02d}",
                "name": name,
                "scheme": "ATMA (Agricultural Technology Management Agency)",
                "specialization": spec,
                "farmer_beneficiaries_trained": count,
                "demo_plots_acres": plots
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, spec, count, plots, lon, lat) in enumerate([
            ("Kancheepuram Organic Rice Farm School", "System of Rice Intensification (SRI)", 340, 5.0, 79.7120, 12.8250),
            ("Tiruvallur Precision Horticulture School", "Drip Irrigation & Drip fertigation", 280, 4.5, 79.9150, 13.1380),
            ("Thondamuthur Vegetable & Floriculture School", "Polyhouse Protected Cultivation", 410, 6.0, 76.8320, 10.9850),
            ("Pollachi Coconut Intercropping Farm School", "Agroforestry & Intercropping", 320, 8.0, 76.9950, 10.6620)
        ])
    ])

    # 18. Community_Skill_School_CSS
    save_layer("Community_Skill_School_CSS", [
        {
            "type": "Feature",
            "id": f"CSS_{i+1:02d}",
            "properties": {
                "center_id": f"CSS-TN-{i+1:02d}",
                "center_name": name,
                "implementing_agency": "Tamil Nadu Skill Development Corporation (TNSDC)",
                "vocational_trades": trades,
                "youth_certified_annual": certs,
                "placement_rate_pct": placement
            },
            "geometry": {"type": "Point", "coordinates": [lon, lat]}
        }
        for i, (name, trades, certs, placement, lon, lat) in enumerate([
            ("Guindy Urban Skill Academy", "CNC Machining, Industrial Automation, EV Servicing", 750, 88.5, 80.2080, 13.0110),
            ("Ambattur Manufacturing Skill Center", "Tool & Die Making, Precision Welding, Robotics", 620, 86.0, 80.1580, 13.1020),
            ("Coimbatore Textile & Apparel Skill Center", "Garment CAD, High-speed Stitching, Quality Audit", 890, 91.2, 76.9850, 11.0320),
            ("Coimbatore Foundry & Auto Skill Center", "Pattern Making, Foundry Tech, EV Powertrain", 540, 84.5, 77.0120, 11.0150)
        ])
    ])

    # 19. Corporations (Municipal Corporations of Tamil Nadu)
    corporations = [
        ("Chennai", "Greater Chennai Corporation (GCC)", 426.0, 4646732, 1688, 80.2707, 13.0827),
        ("Coimbatore", "Coimbatore City Municipal Corporation (CCMC)", 257.0, 1601438, 1981, 76.9558, 11.0168),
        ("Madurai", "Madurai City Municipal Corporation", 147.9, 1561129, 1971, 78.1198, 9.9252),
        ("Tiruchirappalli", "Tiruchirappalli City Municipal Corporation", 167.2, 916857, 1994, 78.7047, 10.7905),
        ("Salem", "Salem City Municipal Corporation", 91.3, 829267, 1994, 78.1460, 11.6643),
        ("Tiruppur", "Tiruppur City Municipal Corporation", 159.3, 877778, 2008, 77.3411, 11.1085),
        ("Erode", "Erode City Municipal Corporation", 109.5, 498121, 2008, 77.7172, 11.3410),
        ("Tirunelveli", "Tirunelveli City Municipal Corporation", 108.6, 473637, 1994, 77.7567, 8.7139),
        ("Vellore", "Vellore City Municipal Corporation", 87.9, 503746, 2008, 79.1325, 12.9165),
        ("Thoothukudi", "Thoothukudi City Municipal Corporation", 90.6, 411628, 2008, 78.1348, 8.7642),
        ("Thanjavur", "Thanjavur City Municipal Corporation", 128.5, 322120, 2014, 79.1378, 10.7870),
        ("Dindigul", "Dindigul City Municipal Corporation", 75.0, 292512, 2014, 77.9803, 10.3673),
        ("Hosur", "Hosur City Municipal Corporation", 72.4, 245000, 2019, 77.8253, 12.7409),
        ("Nagercoil", "Nagercoil City Municipal Corporation", 50.0, 224849, 2019, 77.4119, 8.1833),
        ("Avadi", "Avadi City Municipal Corporation", 65.0, 345996, 2019, 80.1010, 13.1147),
        ("Tambaram", "Tambaram City Municipal Corporation", 87.6, 960887, 2021, 80.1200, 12.9249),
        ("Kancheepuram", "Kancheepuram City Municipal Corporation", 36.1, 234409, 2021, 79.7036, 12.8342),
        ("Karur", "Karur City Municipal Corporation", 53.0, 234144, 2021, 78.0816, 10.9601),
        ("Cuddalore", "Cuddalore City Municipal Corporation", 45.0, 218500, 2021, 79.7714, 11.7480),
        ("Sivakasi", "Sivakasi City Municipal Corporation", 53.6, 234700, 2021, 77.7974, 9.4533),
        ("Kumbakonam", "Kumbakonam City Municipal Corporation", 48.0, 222000, 2021, 79.3780, 10.9602)
    ]

    save_layer("Corporations", [
        {
            "type": "Feature",
            "id": f"CORP_{i+1:02d}",
            "properties": {
                "corp_id": f"CORP-TN-{i+1:02d}",
                "city_name": city,
                "corporation_title": title,
                "area_sq_km": area,
                "population_census2011": pop,
                "established_year": yr,
                "administrative_zones": 5 if area > 100 else 4,
                "state": "Tamil Nadu"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [round(lon - 0.05, 5), round(lat - 0.04, 5)],
                    [round(lon + 0.05, 5), round(lat - 0.04, 5)],
                    [round(lon + 0.05, 5), round(lat + 0.04, 5)],
                    [round(lon - 0.05, 5), round(lat + 0.04, 5)],
                    [round(lon - 0.05, 5), round(lat - 0.04, 5)]
                ]]
            }
        }
        for i, (city, title, area, pop, yr, lon, lat) in enumerate(corporations)
    ])

    # 20. CUMTA_Outer_Boundary
    save_layer("CUMTA_Outer_Boundary", [{
        "type": "Feature",
        "id": "CUMTA_OUTER_JURISDICTION",
        "properties": {
            "authority": "Chennai Unified Metropolitan Transport Authority (CUMTA)",
            "statutory_act": "CUMTA Act, 2010 (Amended 2019)",
            "purpose": "Integrated Multimodal Public Transport Planning and Governance",
            "jurisdiction_area_sq_km": 1189.0,
            "transport_modes_coordinated": "CMRL Metro, Southern Railway Suburban, MTC Buses, MRTS, Feeder Micro-mobility"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [80.1200, 13.3400], [80.3600, 13.3100], [80.3800, 13.1200], [80.3100, 12.8000],
                [80.1800, 12.7200], [79.9800, 12.7900], [79.9200, 13.0500], [80.0100, 13.2800],
                [80.1200, 13.3400]
            ]]
        }
    }])

    print(f"Generated all 20 Vector Layers in {VECTOR_DIR}")

# -------------------------------------------------------------
# 3. ROAD INFRASTRUCTURE & COIMBATORE INVENTORY
# -------------------------------------------------------------
def generate_road_infrastructure():
    print("Generating Road Infrastructure Datasets...")

    # CSV matching user exact fields
    coimbatore_csv_path = os.path.join(INFRA_DIR, "coimbatore_road_infrastructure.csv")
    with open(coimbatore_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "City Name", "Zone Name", "Ward Name", "Ward No.",
            "Length of Roads (in km)", "Length of Tar Roads (in km)", "Length of Concrete Roads (in km)",
            "Length of Roads with footpaths on both sides (in km)", "Length of Roads with footpaths on one side (in km)"
        ])
        # Summary row (user provided)
        writer.writerow(["Coimbatore", "NA", "NA", "NA", "2112 km", "808 km", "256 km", "40km", "70km"])
        
        # Zone-wise and Ward breakdowns
        zones_data = [
            ("Central Zone", "Gandhipuram", 62, 420.5, 172.0, 58.0, 12.5, 18.0),
            ("Central Zone", "RS Puram", 63, 385.0, 155.0, 48.0, 10.0, 15.0),
            ("East Zone", "Singanallur", 57, 445.0, 168.0, 52.0, 6.0, 12.5),
            ("East Zone", "Peelamedu", 38, 410.0, 160.0, 46.0, 5.5, 11.0),
            ("West Zone", "RS Puram West", 23, 226.5, 78.0, 24.0, 3.0, 6.5),
            ("North Zone", "Saravanampatti", 14, 115.0, 42.0, 15.0, 1.5, 4.0),
            ("South Zone", "Kuniyamuthur", 88, 110.0, 33.0, 13.0, 1.5, 3.0)
        ]
        for z_name, w_name, w_no, total, tar, conc, fp_both, fp_one in zones_data:
            writer.writerow(["Coimbatore", z_name, w_name, w_no, f"{total} km", f"{tar} km", f"{conc} km", f"{fp_both} km", f"{fp_one} km"])

    # Multi-corporation road network comparison CSV
    state_roads_csv = os.path.join(INFRA_DIR, "tamil_nadu_corporations_road_inventory.csv")
    with open(state_roads_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Corporation Name", "Total Road Length (km)", "Tar / Bituminous (km)",
            "Cement Concrete (km)", "Footpaths Both Sides (km)", "Footpaths Single Side (km)",
            "Stormwater Drain Covered Roads (km)", "LED Streetlight Coverage Pct"
        ])
        writer.writerow(["Chennai (GCC)", 3870, 2820, 640, 410, 680, 2100, 98.4])
        writer.writerow(["Coimbatore", 2112, 808, 256, 40, 70, 680, 94.2])
        writer.writerow(["Madurai", 1480, 920, 210, 32, 55, 490, 91.5])
        writer.writerow(["Tiruchirappalli", 1240, 810, 185, 28, 48, 410, 92.0])
        writer.writerow(["Salem", 1120, 740, 160, 22, 40, 360, 89.6])
        writer.writerow(["Tiruppur", 1350, 860, 195, 25, 44, 430, 90.8])

    print(f"Generated Road Infrastructure Datasets in {INFRA_DIR}")

if __name__ == "__main__":
    generate_thematic_maps()
    generate_vector_layers()
    generate_road_infrastructure()
    print("All Tamil Nadu datasets successfully generated!")
