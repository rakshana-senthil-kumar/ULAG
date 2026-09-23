"""
Intelligent Attribute Harmonization Service for BHUMI-FUSION
Normalizes heterogeneous land record schemas into a canonical schema
using synonym lookup, normalization, and fuzzy string matching.
"""

from typing import Dict, Any, Tuple, Optional
import re
from difflib import SequenceMatcher

CANONICAL_SYNONYMS = {
    "survey_no": [
        "survey_no", "surveyno", "survey_number", "surveynumber", "survey_id",
        "khasra_no", "khasra", "khasrano", "plot_no", "plotno", "plot_id", "plotid", "cts_no", "ctsno"
    ],
    "subdivision_no": [
        "subdivision_no", "subdivision", "sub_division", "sub_div", "subdiv", "hissa_no", "pothi_no"
    ],
    "parcel_id": [
        "parcel_id", "parcelid", "parcel_uid", "id", "uid", "gid", "objectid", "feature_id"
    ],
    "area": [
        "area", "extent", "area_sq_m", "area_m2", "total_area", "sqm", "size_sqm", "land_area", "rakba"
    ],
    "owner_ref": [
        "owner_ref", "owner_name", "ownername", "property_holder", "holder_name",
        "owner", "khata_no", "khatano", "khatedar", "proprietor"
    ],
    "land_use": [
        "land_use", "landuse", "usage", "property_type", "type", "category", "classification"
    ],
    "status": [
        "status", "dispute_status", "record_status", "state", "registration_status"
    ]
}

def clean_key(key: str) -> str:
    """Normalize string by removing non-alphanumeric chars and lowering case."""
    return re.sub(r"[^a-z0-9]", "", str(key).strip().lower())

def match_field_to_canonical(source_field: str) -> Tuple[Optional[str], float, str]:
    """
    Matches a source field header to canonical schema.
    Returns: (canonical_name, confidence_pct, method)
    """
    s_clean = clean_key(source_field)
    
    # 1. Exact canonical check
    for canonical, synonyms in CANONICAL_SYNONYMS.items():
        if s_clean == clean_key(canonical):
            return canonical, 100.0, "Exact Match"
            
    # 2. Synonym dictionary check
    for canonical, synonyms in CANONICAL_SYNONYMS.items():
        for syn in synonyms:
            if s_clean == clean_key(syn):
                return canonical, 96.0, "Synonym Dictionary"
                
    # 3. Fuzzy similarity matching
    best_canonical = None
    best_ratio = 0.0
    for canonical, synonyms in CANONICAL_SYNONYMS.items():
        for syn in synonyms:
            ratio = SequenceMatcher(None, s_clean, clean_key(syn)).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_canonical = canonical
                
    if best_ratio >= 0.78:
        return best_canonical, round(best_ratio * 100, 1), "Fuzzy Match"
        
    return None, 0.0, "Unmapped"

def harmonize_record_attributes(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms dictionary attributes into canonical fields while preserving original keys.
    """
    harmonized = dict(record)
    for k, v in record.items():
        canonical, conf, method = match_field_to_canonical(k)
        if canonical and canonical not in harmonized:
            harmonized[canonical] = v
            
    # Derive composite full_survey if possible
    if "survey_no" in harmonized:
        s_no = str(harmonized["survey_no"]).strip()
        sub_no = str(harmonized.get("subdivision_no", "")).strip()
        if sub_no and sub_no != "None":
            harmonized["full_survey"] = f"{s_no}/{sub_no}"
        else:
            harmonized["full_survey"] = s_no
            
    return harmonized
