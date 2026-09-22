"""
Dataset Ingestion Service for BHUMI-FUSION
Loads and parses GeoJSON and CSV datasets with strict field checks and user-friendly validation.
"""

import json
import csv
import io
import os
from typing import Dict, List, Any, Tuple
from shapely.geometry import shape

REQUIRED_LEGACY_FIELDS = {"parcel_id", "survey_no", "area"}
REQUIRED_DRONE_FIELDS = {"feature_id", "area"}
REQUIRED_GNSS_FIELDS = {"point_id", "survey_no", "latitude", "longitude"}
REQUIRED_REVENUE_FIELDS = {"survey_no", "area"}

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
    
    # Check first feature schema
    if features:
        props = features[0].get("properties", {})
        for req in REQUIRED_LEGACY_FIELDS:
            if req not in props:
                raise IngestionError(f"Missing field in legacy cadastral: {req}", missing_field=req)
    return features, crs_name

def load_drone_geojson(file_content: str | bytes) -> Tuple[List[Dict[str, Any]], str]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    data = json.loads(file_content)
    crs_name = data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326")
    features = data.get("features", [])
    
    if features:
        props = features[0].get("properties", {})
        for req in REQUIRED_DRONE_FIELDS:
            if req not in props:
                raise IngestionError(f"Missing field in drone features: {req}", missing_field=req)
    return features, crs_name

def load_gnss_csv(file_content: str | bytes) -> List[Dict[str, Any]]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(file_content))
    headers = set(reader.fieldnames or [])
    for req in REQUIRED_GNSS_FIELDS:
        if req not in headers:
            raise IngestionError(f"Missing field in GNSS CSV: {req}", missing_field=req)
    rows = []
    for r in reader:
        try:
            rows.append({
                "point_id": r["point_id"].strip(),
                "survey_no": r["survey_no"].strip(),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "accuracy_m": float(r.get("accuracy_m", 0.03))
            })
        except ValueError:
            continue
    return rows

def load_revenue_csv(file_content: str | bytes) -> List[Dict[str, Any]]:
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(file_content))
    headers = set(reader.fieldnames or [])
    for req in REQUIRED_REVENUE_FIELDS:
        if req not in headers:
            raise IngestionError(f"Missing field in revenue CSV: {req}", missing_field=req)
    rows = []
    for r in reader:
        try:
            rows.append({
                "survey_no": r["survey_no"].strip(),
                "subdivision_no": r.get("subdivision_no", "").strip(),
                "owner_ref": r.get("owner_ref", "").strip(),
                "area": float(r["area"]),
                "land_use": r.get("land_use", "").strip(),
                "status": r.get("status", "Active").strip()
            })
        except ValueError:
            continue
    return rows
