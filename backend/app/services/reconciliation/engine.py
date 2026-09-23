"""
Reconciliation Engine for ULAG
Produces evidence-weighted recommendations based on source reliability weights.
Preserves original source records and computes authoritative reconciled candidates.
"""

from typing import Dict, List, Any, Optional
from backend.app.config import SOURCE_RELIABILITY
from backend.app.schemas.cadastral import (
    SourceAreaComparison, EvidenceMetrics, ParcelRecommendation
)
from backend.app.services.explanation.explainer import generate_reconciliation_explanation

class ReconciliationEngine:
    def compute_recommendation(
        self,
        survey_no: str,
        sources: SourceAreaComparison,
        evidence: EvidenceMetrics,
        drone_candidate: Optional[Dict[str, Any]],
        gnss_points: List[Dict[str, Any]],
        conflict_type: Optional[str] = None
    ) -> ParcelRecommendation:
        # Evidence-weighted calculation across all sources
        # Weights: GNSS (0.97), Drone (0.90), Revenue (0.78), Legacy (0.65)
        weighted_sum = 0.0
        total_weight = 0.0

        if sources.gnss and len(gnss_points) >= 3:
            w = SOURCE_RELIABILITY["GNSS/CORS"]
            weighted_sum += sources.gnss * w
            total_weight += w

        if sources.drone:
            w = SOURCE_RELIABILITY["Drone/ORI"]
            weighted_sum += sources.drone * w
            total_weight += w

        if sources.revenue:
            w = SOURCE_RELIABILITY["Revenue"]
            weighted_sum += sources.revenue * w
            total_weight += w

        if sources.legacy:
            w = SOURCE_RELIABILITY["Legacy Cadastral"]
            weighted_sum += sources.legacy * w
            total_weight += w

        rec_area = round(weighted_sum / total_weight, 1) if total_weight > 0 else (sources.legacy or 0.0)

        if len(gnss_points) >= 3 and drone_candidate:
            geom_source = "GNSS + Drone geometry"
        elif drone_candidate:
            geom_source = "Drone ORI Feature Extraction"
        else:
            geom_source = "Legacy Cadastral (Pending Survey Verification)"

        summary, details = generate_reconciliation_explanation(survey_no, sources, evidence, conflict_type)

        return ParcelRecommendation(
            geometry_source=geom_source,
            recommended_area=rec_area,
            confidence=evidence.overall_confidence,
            explanation_summary=summary,
            explanation_details=details
        )
