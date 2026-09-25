"""
Tamil Nadu Geospatial Integration Service for ULAG
Manages access to 20 urban vector layers, 5 state thematic/demographic maps,
and municipal road infrastructure data (Coimbatore & Statewide).
"""

import os
import json
import csv
from typing import Dict, List, Any, Optional
from pathlib import Path
from backend.app.schemas.tamil_nadu import (
    TamilNaduLayerMetadata, TamilNaduCatalogResponse,
    CoimbatoreRoadRecord, RoadInventoryResponse, TamilNaduDistrictDemographics
)
from backend.app.services.pipeline import ROOT_DIR

TN_DATA_DIR = os.path.join(str(ROOT_DIR), "data", "tamil_nadu")
THEMATIC_DIR = os.path.join(TN_DATA_DIR, "thematic_maps")
VECTOR_DIR = os.path.join(TN_DATA_DIR, "vector_layers")
INFRA_DIR = os.path.join(TN_DATA_DIR, "infrastructure")

LAYER_METADATA_CONFIG = {
    # 20 Vector Layers
    "Aadhar_Enrollment_Center": {
        "category": "Civic Services",
        "agency": "UIDAI / GCC / TNeGA",
        "description": "Aadhaar enrollment and biometric update centres across Chennai and Coimbatore."
    },
    "Amma_Unavagam_GCC": {
        "category": "Civic Services",
        "agency": "Greater Chennai Corporation (GCC)",
        "description": "Subsidized municipal food canteens operated by Women Self-Help Groups across GCC zones."
    },
    "Anganwadi_Centres": {
        "category": "Civic Services",
        "agency": "Social Welfare & Women Empowerment Dept / ICDS",
        "description": "Integrated Child Development Services (ICDS) daycare and nutrition centres."
    },
    "Arts_and_Science_Collage": {
        "category": "Education",
        "agency": "Higher Education Department, Tamil Nadu",
        "description": "Government and autonomous arts and science college campus locations."
    },
    "Block_Boundary": {
        "category": "Administrative",
        "agency": "Rural Development & Panchayat Raj Dept",
        "description": "Panchayat block and rural development administrative territorial boundaries."
    },
    "Buildings_Locations": {
        "category": "Infrastructure",
        "agency": "Public Works Dept (PWD) / Municipal Corporations",
        "description": "Prominent administrative, institutional, and civic building footprints."
    },
    "Burial_Ground_Locations": {
        "category": "Civic Services",
        "agency": "Municipal Health & Sanitation Dept",
        "description": "Municipal gasifier, electric crematoriums, and community burial grounds."
    },
    "Bus_shelter_Locations": {
        "category": "Transportation",
        "agency": "Metropolitan Transport Corporation (MTC) / CUMTA",
        "description": "Modern bus shelters and passenger waiting facilities along major transit corridors."
    },
    "Chennai_Metro_Rail_Route": {
        "category": "Transportation",
        "agency": "Chennai Metro Rail Limited (CMRL)",
        "description": "Corridor alignments for Blue Line (Wimco Nagar to Airport) and Green Line."
    },
    "Chennai_Metro_Rail_Station": {
        "category": "Transportation",
        "agency": "Chennai Metro Rail Limited (CMRL)",
        "description": "Underground and elevated metro stations with multi-modal transport interchanges."
    },
    "Chennai_Outer_Boundary": {
        "category": "Administrative",
        "agency": "Greater Chennai Corporation (GCC)",
        "description": "Statutory territorial jurisdiction of Greater Chennai Corporation (426 sq km, 15 Zones)."
    },
    "Chennai_Region_Boundary": {
        "category": "Administrative",
        "agency": "Chennai Metropolitan Development Authority (CMDA)",
        "description": "Chennai Metropolitan Area (CMA) planning boundary (1,189 sq km)."
    },
    "CMWSSB_Decanting_Location": {
        "category": "Utilities",
        "agency": "CMWSSB (Metro Water)",
        "description": "Licensed sewage decanting stations and septage reception points."
    },
    "CMWSSB_Sewerage_Pumping_Stations": {
        "category": "Utilities",
        "agency": "CMWSSB (Metro Water)",
        "description": "Major sewage pumping stations (SPS) with SCADA automation and generator backups."
    },
    "Cold_Storages": {
        "category": "Infrastructure",
        "agency": "Agricultural Marketing and Agri-Business Dept",
        "description": "Temperature-controlled multi-commodity perishable cold storage infrastructure."
    },
    "Common_Service_Centres": {
        "category": "Civic Services",
        "agency": "CSC e-Governance Services India / TNeGA",
        "description": "Citizen digital service kiosks for land revenue certificates and central schemes."
    },
    "Community_Farm_Schools_CFS": {
        "category": "Education",
        "agency": "Agriculture and Farmers Welfare Dept / ATMA",
        "description": "Field-level agricultural training and organic farming demonstration schools."
    },
    "Community_Skill_School_CSS": {
        "category": "Education",
        "agency": "Tamil Nadu Skill Development Corporation (TNSDC)",
        "description": "Vocational technical skill academies for industry-aligned workforce development."
    },
    "Corporations": {
        "category": "Administrative",
        "agency": "Municipal Administration & Water Supply Dept",
        "description": "All 21 Municipal Corporations of Tamil Nadu with administrative parameters."
    },
    "CUMTA_Outer_Boundary": {
        "category": "Transportation",
        "agency": "Chennai Unified Metropolitan Transport Authority",
        "description": "Statutory planning jurisdiction of CUMTA for unified urban mobility (1,189 sq km)."
    },
    # Thematic Maps
    "Distribution_of_e_Sevai_Centres_In_Tamil_Nadu": {
        "file": "tn_e_sevai_centres.geojson",
        "category": "Thematic Maps",
        "agency": "Tamil Nadu e-Governance Agency (TNeGA)",
        "description": "Statewide distribution of e-Sevai citizen service centres across all 38 districts."
    },
    "Tamil_Nadu_Districts": {
        "file": "tamil_nadu_districts.geojson",
        "category": "Administrative",
        "agency": "Survey and Land Records Dept / Revenue Administration",
        "description": "Administrative district boundaries and headquarters of Tamil Nadu."
    }
}

class TamilNaduService:
    def __init__(self):
        pass

    def get_catalog(self) -> TamilNaduCatalogResponse:
        """Returns catalog of all registered Tamil Nadu layers with metadata."""
        layers: List[TamilNaduLayerMetadata] = []

        # Vector layers
        if os.path.exists(VECTOR_DIR):
            for fname in sorted(os.listdir(VECTOR_DIR)):
                if fname.endswith(".geojson"):
                    layer_name = fname.replace(".geojson", "")
                    cfg = LAYER_METADATA_CONFIG.get(layer_name, {
                        "category": "Urban Vector Layer",
                        "agency": "Government of Tamil Nadu",
                        "description": f"Vector layer for {layer_name}"
                    })
                    fpath = os.path.join(VECTOR_DIR, fname)
                    geom_type = "Point"
                    feat_count = 0
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            feats = data.get("features", [])
                            feat_count = len(feats)
                            if feat_count > 0:
                                geom_type = feats[0].get("geometry", {}).get("type", "Point")
                    except Exception:
                        pass

                    layers.append(TamilNaduLayerMetadata(
                        layer_id=f"LYR-TN-{layer_name}",
                        layer_name=layer_name,
                        category=cfg.get("category", "Vector"),
                        geometry_type=geom_type,
                        feature_count=feat_count,
                        format="GeoJSON",
                        crs="EPSG:4326",
                        source_agency=cfg.get("agency", "Government of Tamil Nadu"),
                        description=cfg.get("description", "")
                    ))

        # Thematic maps
        thematic_files = [
            ("Distribution_of_e_Sevai_Centres_In_Tamil_Nadu", "tn_e_sevai_centres.geojson", "Civic Services", "Point", "TNeGA", "Distribution of e-Sevai Centres across Tamil Nadu districts"),
            ("Tamil_Nadu_Districts", "tamil_nadu_districts.geojson", "Administrative", "Polygon", "Revenue Administration", "Tamil Nadu District Boundaries and demographic attributes")
        ]
        for l_name, fname, cat, g_type, agency, desc in thematic_files:
            fpath = os.path.join(THEMATIC_DIR, fname)
            feat_count = 0
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        feat_count = len(data.get("features", []))
                except Exception:
                    pass

            layers.append(TamilNaduLayerMetadata(
                layer_id=f"LYR-TN-{l_name}",
                layer_name=l_name,
                category=cat,
                geometry_type=g_type,
                feature_count=feat_count,
                format="GeoJSON",
                crs="EPSG:4326",
                source_agency=agency,
                description=desc
            ))

        return TamilNaduCatalogResponse(
            total_layers=len(layers),
            thematic_maps_count=5,
            vector_layers_count=20,
            infrastructure_tables_count=2,
            layers=layers
        )

    def get_layer_geojson(self, layer_name: str) -> Optional[Dict[str, Any]]:
        """Loads and returns GeoJSON for a specified layer."""
        # Check vector directory
        v_path = os.path.join(VECTOR_DIR, f"{layer_name}.geojson")
        if os.path.exists(v_path):
            with open(v_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Check thematic directory
        t_candidates = [
            f"{layer_name}.geojson",
            f"{layer_name.lower()}.geojson",
            "tamil_nadu_districts.geojson" if "district" in layer_name.lower() else None,
            "tn_e_sevai_centres.geojson" if "sevai" in layer_name.lower() else None
        ]
        for cand in t_candidates:
            if cand and os.path.exists(os.path.join(THEMATIC_DIR, cand)):
                with open(os.path.join(THEMATIC_DIR, cand), "r", encoding="utf-8") as f:
                    return json.load(f)

        return None

    def get_road_inventory(self) -> RoadInventoryResponse:
        """Parses and returns Coimbatore and statewide municipal road infrastructure data."""
        cbe_csv = os.path.join(INFRA_DIR, "coimbatore_road_infrastructure.csv")
        records: List[CoimbatoreRoadRecord] = []
        summary = {
            "city_name": "Coimbatore",
            "total_road_length_km": "2112 km",
            "tar_roads_km": "808 km",
            "concrete_roads_km": "256 km",
            "footpath_both_sides_km": "40 km",
            "footpath_one_side_km": "70 km",
            "tar_percentage": round((808 / 2112) * 100, 1),
            "concrete_percentage": round((256 / 2112) * 100, 1),
            "footpath_coverage_percentage": round(((40 + 70) / 2112) * 100, 1)
        }

        if os.path.exists(cbe_csv):
            with open(cbe_csv, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 9 and row[0].strip():
                        records.append(CoimbatoreRoadRecord(
                            city_name=row[0].strip(),
                            zone_name=row[1].strip(),
                            ward_name=row[2].strip(),
                            ward_no=row[3].strip(),
                            total_length_km=row[4].strip(),
                            tar_roads_km=row[5].strip(),
                            concrete_roads_km=row[6].strip(),
                            footpath_both_sides_km=row[7].strip(),
                            footpath_one_side_km=row[8].strip()
                        ))

        # Statewide comparison
        state_csv = os.path.join(INFRA_DIR, "tamil_nadu_corporations_road_inventory.csv")
        state_comp = []
        if os.path.exists(state_csv):
            with open(state_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    state_comp.append(dict(r))

        return RoadInventoryResponse(
            city="Coimbatore",
            summary=summary,
            records=records,
            statewide_comparison=state_comp
        )

    def get_census_demographics(self) -> List[TamilNaduDistrictDemographics]:
        """Returns Census 2011 SC/ST demographic statistics for Tamil Nadu districts."""
        geojson_path = os.path.join(THEMATIC_DIR, "tamil_nadu_districts.geojson")
        results = []
        if os.path.exists(geojson_path):
            with open(geojson_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for feat in data.get("features", []):
                    props = feat.get("properties", {})
                    results.append(TamilNaduDistrictDemographics(
                        district_code=props.get("district_code", ""),
                        district_name=props.get("district_name", ""),
                        headquarters=props.get("headquarters", ""),
                        total_population=props.get("total_population", 0),
                        sc_population=props.get("sc_population", 0),
                        sc_percentage=props.get("sc_percentage", 0.0),
                        st_population=props.get("st_population", 0),
                        st_percentage=props.get("st_percentage", 0.0),
                        combined_sc_st_population=props.get("sc_st_combined_population", 0),
                        combined_percentage=props.get("sc_st_combined_percentage", 0.0),
                        literacy_rate=props.get("literacy_rate", 0.0),
                        taluks_count=props.get("taluks_count", 0)
                    ))
        return results

tn_service = TamilNaduService()
