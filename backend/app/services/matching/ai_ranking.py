"""
ULAG AI-Assisted Spatial Harmonization & Candidate Ranking Service
Augments the deterministic 5-factor matching engine with derived geometric & spatial features,
explainability reporting, and strict legal hard-conflict gates.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform
import pyproj

try:
    from backend.app.models.storage import storage_repo
except ImportError:
    from app.models.storage import storage_repo


class HarmonizationFeatureExtractor:
    """Extracts extended geometric, topological, and contextual features for candidate pairs."""

    @staticmethod
    def calculate_compactness(geom: Polygon) -> float:
        """Polsby-Popper / Isoperimetric Quotient: 4 * pi * Area / Perimeter^2."""
        try:
            area = geom.area
            perimeter = geom.length
            if perimeter <= 0:
                return 0.0
            return (4.0 * math.pi * area) / (perimeter ** 2)
        except Exception:
            return 0.0

    @staticmethod
    def calculate_hausdorff_distance(geom_a: Polygon, geom_b: Polygon) -> float:
        """Computes the directed/undirected Hausdorff distance between two boundary geometries."""
        try:
            return float(geom_a.exterior.hausdorff_distance(geom_b.exterior))
        except Exception:
            return 999.0

    @staticmethod
    def calculate_vertex_similarity(geom_a: Polygon, geom_b: Polygon) -> float:
        """Vertex count ratio similarity [0.0 - 1.0]."""
        try:
            v_a = len(geom_a.exterior.coords)
            v_b = len(geom_b.exterior.coords)
            return min(v_a, v_b) / max(v_a, v_b) if max(v_a, v_b) > 0 else 1.0
        except Exception:
            return 0.5


class AIRankedHarmonizer:
    """
    AI-Assisted Candidate Harmonization Ranker.
    Keeps deterministic 5-factor scoring (Geometry 35%, Area 20%, Centroid 20%, Attributes 15%, Proximity 10%)
    authoritative, enriches with learned spatial features, generates explainable textual audits,
    and applies inviolable legal/geometric gates.
    """

    # Hard Legal/Geometric Gates:
    MAX_PERMISSIBLE_HAUSDORFF_METERS = 25.0
    MIN_GEOMETRIC_IOU_GATE = 0.20
    AREA_DEVIATION_HARD_LIMIT = 0.50 # If area difference > 50%, candidate fails hard gate

    def evaluate_candidate(
        self,
        base_parcel: Dict[str, Any],
        candidate_parcel: Dict[str, Any],
        base_geom: Polygon,
        candidate_geom: Polygon,
        gnss_support: bool = False,
        utility_conflict: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates a candidate match between base parcel (e.g. Cadastral) and candidate (e.g. Drone Survey / Revenue).
        """
        # 1. Deterministic 5-Factor Scoring
        # Factor A: Geometry (IoU)
        intersection_area = base_geom.intersection(candidate_geom).area
        union_area = base_geom.union(candidate_geom).area
        iou = intersection_area / union_area if union_area > 0 else 0.0
        score_geom = min(1.0, max(0.0, iou))

        # Factor B: Area
        area_a = base_geom.area
        area_b = candidate_geom.area
        area_ratio = min(area_a, area_b) / max(area_a, area_b) if max(area_a, area_b) > 0 else 0.0
        score_area = area_ratio

        # Factor C: Centroid Distance
        c_a = base_geom.centroid
        c_b = candidate_geom.centroid
        centroid_dist = math.hypot(c_a.x - c_b.x, c_a.y - c_b.y)
        # 0m = 1.0, 50m = 0.0
        score_centroid = max(0.0, 1.0 - (centroid_dist / 50.0))

        # Factor D: Attributes
        attr_matches = 0
        total_attrs = 0
        for k in ["owner_name", "village", "taluk", "survey_number", "land_use"]:
            v_a = str(base_parcel.get(k, "")).strip().lower()
            v_b = str(candidate_parcel.get(k, "")).strip().lower()
            if v_a and v_b:
                total_attrs += 1
                if v_a == v_b:
                    attr_matches += 1
                elif v_a in v_b or v_b in v_a:
                    attr_matches += 0.5
        score_attrs = (attr_matches / total_attrs) if total_attrs > 0 else 0.70

        # Factor E: Proximity
        score_proximity = score_centroid # Re-scaled proximity

        # Weighted Deterministic Base (35%, 20%, 20%, 15%, 10%)
        deterministic_score = (
            score_geom * 0.35 +
            score_area * 0.20 +
            score_centroid * 0.20 +
            score_attrs * 0.15 +
            score_proximity * 0.10
        )

        # 2. Advanced Feature Extraction
        extractor = HarmonizationFeatureExtractor()
        comp_a = extractor.calculate_compactness(base_geom)
        comp_b = extractor.calculate_compactness(candidate_geom)
        compactness_diff = abs(comp_a - comp_b)

        hausdorff_dist = extractor.calculate_hausdorff_distance(base_geom, candidate_geom)
        vertex_sim = extractor.calculate_vertex_similarity(base_geom, candidate_geom)

        # 3. AI-Assisted Bonus / Penalty Modifier (-5% to +5%)
        ai_modifier = 0.0
        if hausdorff_dist < 2.0:
            ai_modifier += 0.03
        elif hausdorff_dist > 15.0:
            ai_modifier -= 0.04

        if vertex_sim > 0.85:
            ai_modifier += 0.02

        if gnss_support:
            ai_modifier += 0.03 # Ground truth GNSS verification confirms boundaries

        if utility_conflict:
            ai_modifier -= 0.05 # Utility easement encroachment detected

        final_confidence = min(0.99, max(0.01, deterministic_score + ai_modifier))

        # 4. Hard Legal / Geometric Gates
        gate_passed = True
        gate_reasons = []

        if iou < self.MIN_GEOMETRIC_IOU_GATE:
            gate_passed = False
            gate_reasons.append(f"Hard Gate Failed: Geometric IoU ({iou:.2f}) < threshold ({self.MIN_GEOMETRIC_IOU_GATE})")

        if hausdorff_dist > self.MAX_PERMISSIBLE_HAUSDORFF_METERS:
            gate_passed = False
            gate_reasons.append(f"Hard Gate Failed: Boundary Hausdorff distance ({hausdorff_dist:.1f}m) exceeds legal threshold ({self.MAX_PERMISSIBLE_HAUSDORFF_METERS}m)")

        if (1.0 - area_ratio) > self.AREA_DEVIATION_HARD_LIMIT:
            gate_passed = False
            gate_reasons.append(f"Hard Gate Failed: Area deviation ({abs(area_a - area_b):.1f}m2, {(1.0-area_ratio)*100:.1f}%) exceeds allowable 50% limit")

        # 5. Explainable Reasoning Generation
        reasons = []
        if score_geom >= 0.80:
            reasons.append("Strong geometric boundary alignment.")
        elif score_geom >= 0.50:
            reasons.append("Moderate geometric overlap with minor edge discrepancies.")
        else:
            reasons.append("Low geometric boundary overlap.")

        if score_area >= 0.90:
            reasons.append(f"High area concordance ({area_a:.1f}m2 vs {area_b:.1f}m2).")
        else:
            reasons.append(f"Noticeable area variation ({abs(area_a - area_b):.1f}m2 difference).")

        if gnss_support:
            reasons.append("Verified by high-precision GNSS/CORS control points.")
        if utility_conflict:
            reasons.append("Caution: Parcel intersects with utility corridor/easement.")

        if not gate_passed:
            reasons.extend(gate_reasons)
            decision = "REJECTED_BY_HARD_GATE"
        elif final_confidence >= 0.85:
            decision = "AUTO_MATCH_RECOMMENDED"
        elif final_confidence >= 0.65:
            decision = "MANUAL_ADJUDICATION_REQUIRED"
        else:
            decision = "LOW_CONFIDENCE_MATCH"

        explanation_text = " ".join(reasons)

        return {
            "base_parcel_id": base_parcel.get("parcel_id") or base_parcel.get("id"),
            "candidate_parcel_id": candidate_parcel.get("parcel_id") or candidate_parcel.get("id"),
            "factor_scores": {
                "geometry_iou": round(score_geom, 3),
                "area_similarity": round(score_area, 3),
                "centroid_proximity": round(score_centroid, 3),
                "attribute_matching": round(score_attrs, 3),
                "proximity": round(score_proximity, 3)
            },
            "learned_features": {
                "hausdorff_distance_m": round(hausdorff_dist, 2),
                "vertex_similarity": round(vertex_sim, 3),
                "compactness_base": round(comp_a, 3),
                "compactness_candidate": round(comp_b, 3),
                "gnss_corroborated": gnss_support,
                "utility_conflict": utility_conflict
            },
            "deterministic_score": round(deterministic_score, 4),
            "final_confidence": round(final_confidence, 4),
            "quality_tier": "HIGH" if final_confidence >= 0.85 else ("MEDIUM" if final_confidence >= 0.65 else "LOW"),
            "hard_gates_passed": gate_passed,
            "gate_failures": gate_reasons,
            "decision": decision,
            "explanation": explanation_text
        }


ai_harmonizer = AIRankedHarmonizer()
