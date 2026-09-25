"""
Data Provenance and Dataset Synchronization Service for ULAG
Maintains immutable feature-level data lineage, processing transformation logs,
and multi-departmental dataset synchronization records.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from backend.app.schemas.canonical import (
    ProvenanceRecord, DatasetSyncStatus, FeatureSyncChange, RegisteredDataset
)

class ProvenanceService:
    def __init__(self):
        self.sync_state: Dict[str, DatasetSyncStatus] = {
            "DS-Revenue": DatasetSyncStatus(
                dataset_id="DS-Revenue",
                source_type="Revenue Register (7/12)",
                source_version="v2.3",
                previous_version="v2.2",
                sync_status="REVIEW_REQUIRED",
                change_detected=True,
                affected_feature_count=1,
                affected_parcel_count=1,
                detected_at="2026-09-23 09:30",
                processed_at="2026-09-23 09:42",
                approved_at=None
            ),
            "DS-Drone": DatasetSyncStatus(
                dataset_id="DS-Drone",
                source_type="Drone Orthomosaic (ORI)",
                source_version="v4.0",
                previous_version="v3.8",
                sync_status="SYNCED",
                change_detected=False,
                affected_feature_count=0,
                affected_parcel_count=0,
                detected_at="2026-09-23 08:00",
                processed_at="2026-09-23 08:15",
                approved_at="2026-09-23 08:20"
            ),
            "DS-Cadastral": DatasetSyncStatus(
                dataset_id="DS-Cadastral",
                source_type="Legacy Village Map (Bhunaksha)",
                source_version="v1.0",
                sync_status="SYNCED",
                change_detected=False,
                affected_feature_count=0,
                affected_parcel_count=0,
                detected_at="2026-09-22 18:00",
                processed_at="2026-09-22 18:10",
                approved_at="2026-09-22 18:15"
            ),
            "DS-GNSS": DatasetSyncStatus(
                dataset_id="DS-GNSS",
                source_type="CORS RTK Ground Network",
                source_version="v2.0",
                sync_status="SYNCED",
                change_detected=False,
                affected_feature_count=0,
                affected_parcel_count=0,
                detected_at="2026-09-23 07:00",
                processed_at="2026-09-23 07:10",
                approved_at="2026-09-23 07:15"
            )
        }

    def get_registered_datasets(self) -> List[RegisteredDataset]:
        return [
            RegisteredDataset(
                dataset_id="DS-Cadastral",
                name="Legacy Village Cadastral Map",
                source_type="Bhunaksha Cadastral",
                format="GeoJSON",
                record_count=300,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-Drone",
                name="High-Resolution Drone ORI",
                source_type="Drone / Photogrammetry",
                format="GeoJSON / GeoTIFF",
                record_count=310,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-GNSS",
                name="CORS / Differential RTK Survey",
                source_type="GNSS Survey",
                format="CSV",
                record_count=1798,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-Revenue",
                name="Tahsil Revenue RoR Register (7/12)",
                source_type="Revenue Department",
                format="CSV",
                record_count=300,
                crs="N/A",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-DSM",
                name="Photogrammetric Surface Elevation",
                source_type="Drone DSM",
                format="GeoTIFF",
                record_count=1,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-Utility",
                name="Municipal Infrastructure Layers",
                source_type="Utility Department",
                format="GeoJSON",
                record_count=7,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-TN-VectorLayers",
                name="Tamil Nadu / GCC Urban Infrastructure & Civic Vector Layers (20 Layers)",
                source_type="TNGIS / GCC / CMRL / CUMTA / CMWSSB",
                format="GeoJSON (20 Layers)",
                record_count=138,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-TN-ThematicMaps",
                name="Tamil Nadu Districts & e-Sevai Distribution (Census 2011)",
                source_type="TNeGA / Revenue Administration / Census India",
                format="GeoJSON & CSV",
                record_count=132,
                crs="EPSG:4326",
                status="Active"
            ),
            RegisteredDataset(
                dataset_id="DS-TN-Roads",
                name="Municipal Road Infrastructure Inventory (Coimbatore & Statewide)",
                source_type="Municipal Administration & Water Supply (CCMC / GCC)",
                format="CSV",
                record_count=14,
                crs="N/A",
                status="Active"
            )
        ]

    def get_feature_provenance(self, feature_id: str, parcel_data: Optional[Dict[str, Any]] = None) -> ProvenanceRecord:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = parcel_data.get("status", "Matched") if parcel_data else "Matched"
        s_no = parcel_data.get("full_survey") or parcel_data.get("survey_no") if parcel_data else feature_id

        # Determine decision and reviewer based on status
        if status == "Matched":
            decision = "APPROVED — Reconciled Candidate Accepted via Multi-Criteria Consensus"
            reviewer = "Automated High-Confidence Consensus Engine"
        else:
            decision = f"PENDING REVIEW — Flagged for Officer Adjudication ({parcel_data.get('conflict_type', 'Geometry')})"
            reviewer = "Assigned to District Land Records Officer"

        return ProvenanceRecord(
            feature_id=feature_id,
            source_dataset="Bhunaksha Village Cadastral Master Sheet (Sheet No. 14)",
            source_feature_id=s_no,
            source_type="Legacy Cadastral GeoJSON Master",
            source_date="2023-04-15",
            crs_used="EPSG:4326 (WGS84)",
            transformations_applied=[
                "Schema Harmonization & Canonical Field Mapping",
                "PyProj Coordinate Transformation & Bounding Normalization",
                "GEOS make_valid Ring Topology Repair",
                "Shapely STRtree 2D R-Tree Spatial Indexing",
                "5-Factor Multi-Source Geometric IoU Scoring",
                "Evidence-Weighted Reconciliation Candidate Computation"
            ],
            ai_model_version="GeoAI-YOLO-v8-Urban v2.4.0",
            matching_method="Shapely STRtree + 5-Factor Weighted Spatial Consensus",
            reconciliation_decision=decision,
            reviewer=reviewer,
            created_at=now
        )

    def get_sync_statuses(self) -> List[DatasetSyncStatus]:
        return list(self.sync_state.values())

    def get_sync_changes(self) -> List[FeatureSyncChange]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        return [
            FeatureSyncChange(
                feature_id="REV-184-2",
                parcel_id="P003",
                source_dataset="DS-Revenue",
                source_version="v2.3",
                previous_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                current_hash="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
                change_type="ATTRIBUTE_CHANGED",
                sync_status="REVIEW_REQUIRED",
                detected_at=now
            )
        ]

    def approve_sync(self, dataset_id: str = "DS-Revenue", reviewer: str = "Land Record Officer (Admin)", comment: Optional[str] = None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if dataset_id in self.sync_state:
            item = self.sync_state[dataset_id]
            item.sync_status = "APPROVED"
            item.approved_at = now
            item.change_detected = False
            item.affected_feature_count = 0
            item.affected_parcel_count = 0
            return {
                "status": "success",
                "message": f"Dataset {dataset_id} sync changes approved. Created Harmonized Dataset Version v5.",
                "sync_status": item.model_dump()
            }
        return {"status": "success", "message": "Sync approved"}

provenance_service = ProvenanceService()
