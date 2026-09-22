"""
BHUMI-FUSION Configuration
Defines source reliability weights, confidence model weights, and thresholds.
All weights are transparent configuration data, NOT claimed as machine-learned black-box weights.
"""

from typing import Dict

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

def classify_confidence_status(score: float) -> str:
    if score >= THRESHOLD_HIGH_CONFIDENCE:
        return "Matched"
    elif score >= THRESHOLD_REVIEW:
        return "Review"
    else:
        return "Conflict"
