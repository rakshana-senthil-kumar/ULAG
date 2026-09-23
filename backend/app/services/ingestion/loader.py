"""
Dataset Ingestion Service for BHUMI-FUSION
Loads and parses GeoJSON and CSV datasets with intelligent attribute harmonization.
Accepts heterogeneous column headers (e.g. khasra_no, plot_id, area_sq_m) and maps to canonical fields.
"""

import json
import csv
import io
import os
from typing import Dict, List, Any, Tuple
from shapely.geometry import shape

from backend.app.services.ingestion.harmonizer import harmonize_record_attributes, match_field_to_canonical

class IngestionError(Exception):
    def __init__(self, message: str, missing_field: str = None):
        super().__init__(message)
        self.missing_field = missing_field
        self.user_friendly_message = (
            f"Dataset validation failed: Missing required field '{missing_field}'. "
            f"Please verify column headers in your uploaded dataset."
            if missing_field else message
        )

def load_legacy_geojson(file_content: str | bytes) -> Tuple[List[Dict[str, Any]], str]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    data = json.loads(file_content)
    crs_name = data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326")
    features = data.get("features", [])
    
    harmonized_features = []
    for idx, feat in enumerate(features):
        props = harmonize_record_attributes(feat.get("properties", {}))
        # Ensure mandatory fields have intelligent fallbacks
        if "parcel_id" not in props:
            props["parcel_id"] = f"P{idx+1:03d}"
        if "survey_no" not in props:
            props["survey_no"] = str(idx + 101)
        if "area" not in props:
            try:
                poly = shape(feat.get("geometry", {}))
                props["area"] = round(poly.area * 10000000000.0, 1) if poly.area < 1.0 else round(poly.area, 1)
            except Exception:
                props["area"] = 1000.0
        
        feat_copy = dict(feat)
        feat_copy["properties"] = props
        harmonized_features.append(feat_copy)

    return harmonized_features, crs_name

def load_drone_geojson(file_content: str | bytes) -> Tuple[List[Dict[str, Any]], str]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    data = json.loads(file_content)
    crs_name = data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326")
    features = data.get("features", [])
    
    harmonized_features = []
    for idx, feat in enumerate(features):
        props = harmonize_record_attributes(feat.get("properties", {}))
        if "feature_id" not in props and "parcel_id" in props:
            props["feature_id"] = props["parcel_id"]
        elif "feature_id" not in props:
            props["feature_id"] = f"FE_{idx+1:03d}"
            
        if "area" not in props:
            try:
                poly = shape(feat.get("geometry", {}))
                props["area"] = round(poly.area * 10000000000.0, 1) if poly.area < 1.0 else round(poly.area, 1)
            except Exception:
                props["area"] = 1000.0

        feat_copy = dict(feat)
        feat_copy["properties"] = props
        harmonized_features.append(feat_copy)

    return harmonized_features, crs_name

def load_gnss_csv(file_content: str | bytes) -> List[Dict[str, Any]]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(file_content))
    rows = []
    for idx, r in enumerate(reader):
        harmonized = harmonize_record_attributes(r)
        
        # Detect lat/lon with alias flexibility
        lat = harmonized.get("latitude") or harmonized.get("lat") or harmonized.get("y")
        lon = harmonized.get("longitude") or harmonized.get("lon") or harmonized.get("lng") or harmonized.get("x")
        pt_id = harmonized.get("point_id") or harmonized.get("pointid") or harmonized.get("id") or f"GNSS_{idx+1:05d}"
        s_no = harmonized.get("survey_no") or harmonized.get("full_survey") or "101"
        
        try:
            rows.append({
                "point_id": str(pt_id).strip(),
                "survey_no": str(s_no).strip(),
                "latitude": float(lat),
                "longitude": float(lon),
                "accuracy_m": float(harmonized.get("accuracy_m", 0.03))
            })
        except (ValueError, TypeError):
            continue
    return rows

def load_revenue_csv(file_content: str | bytes) -> List[Dict[str, Any]]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(file_content))
    rows = []
    for idx, r in enumerate(reader):
        harmonized = harmonize_record_attributes(r)
        
        s_no = harmonized.get("survey_no") or f"P{idx+1:03d}"
        sub_no = harmonized.get("subdivision_no", "")
        owner = harmonized.get("owner_ref", "")
        land_use = harmonized.get("land_use", "Residential")
        stat = harmonized.get("status", "Active")
        
        try:
            area_val = float(harmonized.get("area", 1000.0))
        except (ValueError, TypeError):
            area_val = 1000.0

        rows.append({
            "survey_no": str(s_no).strip(),
            "subdivision_no": str(sub_no).strip(),
            "owner_ref": str(owner).strip(),
            "area": area_val,
            "land_use": str(land_use).strip(),
            "status": str(stat).strip()
        })
    return rows
