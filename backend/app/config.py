"""
ULAG Configuration
Defines source reliability weights, confidence model weights, and thresholds.
All weights are transparent configuration data, NOT claimed as machine-learned black-box weights.
"""

from typing import Dict

# CRS Configuration
INTERCHANGE_CRS: str = "EPSG:4326"
METRIC_CRS_DEFAULT: str = "EPSG:32643"

# Source Reliability Configuration Table
# These represent institutional and technical measurement fidelity
SOURCE_RELIABILITY: Dict[str, float] = {
    "GNSS/CORS": 0.97,
    "Ground Truth": 0.95,
    "Drone/ORI": 0.90,
    "Municipal GIS": 0.82,
    "Revenue": 0.78,
    "Legacy Cadastral": 0.65
}

# Match Score Weights (Sum = 1.00)
# match_score = 0.35*geom + 0.20*area + 0.20*centroid + 0.15*attr + 0.10*prox
MATCH_WEIGHTS: Dict[str, float] = {
    "geometry": 0.35,
    "area": 0.20,
    "centroid": 0.20,
    "attribute": 0.15,
    "proximity": 0.10
}

# Confidence Classification Thresholds (0 - 100)
THRESHOLD_HIGH_CONFIDENCE = 90.0
THRESHOLD_REVIEW = 75.0

# Configurable Spatial Harmonization & Geodetic Tolerances
BOUNDARY_TOLERANCE_METERS = 1.5
BOUNDARY_SAMPLE_INTERVAL_METERS = 0.5
MAX_PERMISSIBLE_BOUNDARY_DEVIATION_METERS = 12.0
MEAN_PERMISSIBLE_BOUNDARY_DEVIATION_METERS = 4.5
MAX_PERMISSIBLE_AREA_DIFFERENCE_PCT = 25.0
MIN_IOU_FOR_AUTO_MATCH = 65.0
GNSS_RTK_BUFFER_TOLERANCE_METERS = 0.75
SPATIAL_INDEX_SEARCH_RADIUS_METERS = 35.0
TOPOLOGY_SLIVER_AREA_M2: float = 5.0
TOPOLOGY_OVERLAP_TOLERANCE_M2: float = 0.5

def classify_confidence_status(score: float, hard_flags: list = None) -> str:
    if hard_flags and len(hard_flags) > 0:
        return "Conflict"
    if score >= THRESHOLD_HIGH_CONFIDENCE:
        return "Matched"
    elif score >= THRESHOLD_REVIEW:
        return "Review"
    else:
        return "Conflict"

