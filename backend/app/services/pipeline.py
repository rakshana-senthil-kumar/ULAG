"""
Pipeline Coordinator Service for ULAG
Orchestrates the entire end-to-end cadastral reconciliation workflow:
Ingestion -> Validation -> Spatial Matching -> Conflict Detection -> Reconciliation -> Storage
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from shapely.geometry import shape, mapping

from backend.app.services.ingestion.loader import (
    load_legacy_geojson, load_drone_geojson, load_gnss_csv, load_revenue_csv
)
from backend.app.services.validation.validator import validate_and_normalize_datasets
from backend.app.services.matching.matcher import ParcelMatcher
from backend.app.services.conflict.detector import ConflictDetector
from backend.app.services.reconciliation.engine import ReconciliationEngine
from backend.app.models.storage import storage_repo
from backend.app.schemas.cadastral import (
    SourceAreaComparison, EvidenceMetrics, ParcelRecommendation, ValidationReport
)
from backend.app.config import classify_confidence_status

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
DEMO_DIR = os.path.join(str(ROOT_DIR), "data", "demo")

class ReconciliationPipeline:
    def __init__(self):
        self.matcher = None
        self.conflict_detector = ConflictDetector()
        self.reconciliation_engine = ReconciliationEngine()
        self.last_validation_report = None

    def run_pipeline(
        self,
        legacy_raw: str | bytes,
        drone_raw: str | bytes,
        gnss_raw: str | bytes,
        revenue_raw: str | bytes
    ) -> Dict[str, Any]:
        
        # 1. Ingestion
        legacy_feats, leg_crs = load_legacy_geojson(legacy_raw)
        drone_feats, drn_crs = load_drone_geojson(drone_raw)
        gnss_pts = load_gnss_csv(gnss_raw)
        revenue_recs = load_revenue_csv(revenue_raw)

        # Build quick lookups for revenue and GNSS by survey_no
        revenue_map = {}
        for r in revenue_recs:
            s_key = f"{r['survey_no']}/{r.get('subdivision_no', '')}".strip("/")
            revenue_map[s_key] = r
            revenue_map[r['survey_no']] = r

        gnss_map = {}
        for pt in gnss_pts:
            s_key = pt["survey_no"]
            if s_key not in gnss_map:
                gnss_map[s_key] = []
            gnss_map[s_key].append(pt)

        # 2. Validation & Normalization
        val_report, rep_legacy, rep_drone = validate_and_normalize_datasets(
            legacy_feats, drone_feats, gnss_pts, revenue_recs, leg_crs, drn_crs
        )
        self.last_validation_report = val_report

        # 3. Spatial Indexing and Matching
        self.matcher = ParcelMatcher(rep_drone)
        self.conflict_detector = ConflictDetector()

        parcels_data = []
        conflicts_data = []

        total_parcels = len(rep_legacy)
        matched_count = 0
        conflicts_count = 0
        review_count = 0

        for legacy_feat in rep_legacy:
            props = legacy_feat.get("properties", {})
            p_id = props.get("parcel_id", f"P{len(parcels_data)+1:03d}")
            survey_no = str(props.get("survey_no", ""))
            subdiv_no = str(props.get("subdivision_no", "1"))
            full_survey = props.get("full_survey") or f"{survey_no}/{subdiv_no}"
            legacy_area = float(props.get("area", 1000.0))
            land_use = props.get("land_use", "Residential")

            # Look up Revenue and GNSS prior to matching
            rev_rec = revenue_map.get(full_survey) or revenue_map.get(survey_no)
            gnss_for_parcel = gnss_map.get(full_survey) or gnss_map.get(survey_no) or []

            # Match with Drone incorporating GNSS verification
            drone_cand, evidence, runners_up = self.matcher.match_parcel(legacy_feat, gnss_for_parcel)

            # Calculate real GNSS surface area estimate if points available using projected metric CRS
            gnss_area_val = None
            if len(gnss_for_parcel) >= 3:
                try:
                    from shapely.geometry import Polygon
                    from backend.app.services.geometry.crs import project_point
                    proj_crs = self.matcher.projected_crs
                    m_pts = [project_point(pt["longitude"], pt["latitude"], src_crs="EPSG:4326", target_crs=proj_crs) for pt in gnss_for_parcel]
                    gnss_poly = Polygon(m_pts)
                    gnss_area_val = round(abs(gnss_poly.area), 1)
                except Exception:
                    gnss_area_val = legacy_area

            # Area comparison
            drone_area_val = drone_cand["properties"]["area"] if drone_cand else None
            rev_area_val = rev_rec["area"] if rev_rec else None

            source_comp = SourceAreaComparison(
                legacy=legacy_area,
                revenue=rev_area_val,
                drone=drone_area_val,
                gnss=gnss_area_val
            )

            # Conflict Detection
            conflict_item = self.conflict_detector.evaluate_parcel_conflict(
                parcel_id=p_id,
                survey_no=full_survey,
                legacy_area=legacy_area,
                legacy_land_use=land_use,
                revenue_record=rev_rec,
                drone_candidate=drone_cand,
                gnss_points=gnss_for_parcel,
                evidence=evidence
            )

            # Determine parcel status (gated by hard constraints and conflict detector)
            if conflict_item:
                status = "Conflict"
                conflicts_count += 1
                conflicts_data.append(conflict_item.model_dump())
            elif evidence.overall_confidence >= 90.0:
                status = "Matched"
                matched_count += 1
            else:
                status = "Review"
                review_count += 1

            # Reconciliation Recommendation
            rec = self.reconciliation_engine.compute_recommendation(
                survey_no=full_survey,
                sources=source_comp,
                evidence=evidence,
                drone_candidate=drone_cand,
                gnss_points=gnss_for_parcel,
                conflict_type=conflict_item.conflict_type if conflict_item else None
            )

            # Determine reconciled geometry
            reconciled_geom = drone_cand["geometry"] if drone_cand else legacy_feat["geometry"]

            drone_cand_id = drone_cand.get("id") or drone_cand.get("properties", {}).get("feature_id") if drone_cand else None

            parcels_data.append({
                "parcel_id": p_id,
                "survey_no": survey_no,
                "subdivision_no": subdiv_no,
                "full_survey": full_survey,
                "land_use": land_use,
                "legacy_area": legacy_area,
                "confidence": evidence.overall_confidence,
                "status": status,
                "conflict_type": conflict_item.conflict_type if conflict_item else None,
                "source_comparison": source_comp.model_dump(),
                "evidence": evidence.model_dump(),
                "recommendation": rec.model_dump(),
                "legacy_geometry": legacy_feat.get("geometry"),
                "drone_geometry": drone_cand.get("geometry") if drone_cand else None,
                "drone_candidate_id": drone_cand_id,
                "reconciled_geometry": reconciled_geom,
                "gnss_points": gnss_for_parcel
            })

        summary = {
            "total_parcels": total_parcels,
            "matched_count": matched_count,
            "conflicts_count": conflicts_count,
            "review_count": review_count,
            "crs": "EPSG:4326",
            "last_run_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Persist to database
        storage_repo.save_pipeline_results(parcels_data, conflicts_data, summary)

        return {
            "summary": summary,
            "validation": val_report.model_dump(),
            "parcels_count": len(parcels_data),
            "conflicts_count": len(conflicts_data)
        }

    def load_and_run_demo(self) -> Dict[str, Any]:
        """Loads demo files from data/demo/ and runs full reconciliation pipeline."""
        with open(os.path.join(DEMO_DIR, "legacy_cadastral.geojson"), "rb") as f:
            legacy_raw = f.read()
        with open(os.path.join(DEMO_DIR, "drone_features.geojson"), "rb") as f:
            drone_raw = f.read()
        with open(os.path.join(DEMO_DIR, "gnss_points.csv"), "rb") as f:
            gnss_raw = f.read()
        with open(os.path.join(DEMO_DIR, "revenue_records.csv"), "rb") as f:
            revenue_raw = f.read()

        return self.run_pipeline(legacy_raw, drone_raw, gnss_raw, revenue_raw)

pipeline = ReconciliationPipeline()
