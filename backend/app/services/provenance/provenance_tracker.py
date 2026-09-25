"""
Provenance & Lineage Tracking Service for BHUMI-FUSION V2
Tracks full data lineage, transformation history, AI model runs, and human officer decisions
for every canonical feature in the platform.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.app.schemas.canonical import ProvenanceRecord

class ProvenanceTracker:
    def __init__(self):
        self._provenance_store: Dict[str, ProvenanceRecord] = {}

    def create_provenance_record(
        self,
        feature_id: str,
        source_dataset: str,
        source_feature_id: Optional[str] = None,
        source_type: str = "Legacy Cadastral",
        transformations: List[str] = None,
        ai_model_version: Optional[str] = None,
        reconciliation_decision: Optional[str] = None,
        reviewer: Optional[str] = None
    ) -> ProvenanceRecord:
        
        default_transformations = [
            "Ingestion & Schema Normalization",
            "EPSG:4326 to Metric EPSG:32643 Transformation",
            "Topology Repair (shapely.validation.make_valid)",
            "STRtree R-Tree Candidate Matching",
            "5-Factor Evidence Weighted Scoring"
        ]

        record = ProvenanceRecord(
            feature_id=feature_id,
            source_dataset=source_dataset,
            source_feature_id=source_feature_id or feature_id,
            source_type=source_type,
            source_date="2026-09-22",
            crs_used="EPSG:4326 / EPSG:32643",
            transformations_applied=transformations or default_transformations,
            ai_model_version=ai_model_version or "YOLO+SAM-BuildingExtractor-v1.0",
            matching_method="STRtree R-Tree + Multi-factor Scoring",
            reconciliation_decision=reconciliation_decision,
            reviewer=reviewer,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self._provenance_store[feature_id] = record
        return record

    def get_provenance(self, feature_id: str) -> Optional[ProvenanceRecord]:
        return self._provenance_store.get(feature_id)

    def get_provenance_record(self, feature_id: str) -> Optional[ProvenanceRecord]:
        return self.get_provenance(feature_id)

provenance_tracker = ProvenanceTracker()
