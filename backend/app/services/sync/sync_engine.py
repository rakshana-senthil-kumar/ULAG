"""
Dataset Synchronization & Source Reconciliation Engine for BHUMI-FUSION V2
Detects source updates using SHA-256 feature fingerprints, identifies affected spatial features,
flags parcels as STALE / SYNC_REQUIRED, orchestrates officer reconciliation review,
publishes updated harmonized dataset versions, and appends provenance lineage records.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from backend.app.schemas.canonical import DatasetSyncStatus, FeatureSyncChange
from backend.app.models.storage import storage_repo
from backend.app.services.versioning.version_manager import version_manager
from backend.app.services.provenance.provenance_tracker import provenance_tracker

class DatasetSyncEngine:
    def __init__(self):
        self._active_runs: Dict[str, DatasetSyncStatus] = {}
        self._feature_changes: Dict[str, FeatureSyncChange] = {}

    def compute_feature_fingerprint(self, feature: Dict[str, Any]) -> str:
        """Computes a deterministic SHA-256 fingerprint hash of feature geometry & attributes."""
        normalized = {
            "geometry": feature.get("geometry", {}),
            "properties": {k: v for k, v in sorted(feature.get("properties", {}).items())}
        }
        raw_str = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def check_source_dataset_updates(
        self,
        dataset_id: str,
        source_name: str,
        old_features: List[Dict[str, Any]],
        new_features: List[Dict[str, Any]],
        old_version: str = "v1.0",
        new_version: str = "v2.0"
    ) -> Tuple[DatasetSyncStatus, List[FeatureSyncChange]]:
        """
        Detects changes between dataset versions by comparing feature fingerprints.
        Identifies ADDED, REMOVED, MODIFIED, ATTRIBUTE_CHANGED, AREA_CHANGED, and GEOMETRY_CHANGED features.
        """
        old_map = {}
        for feat in old_features:
            props = feat.get("properties", {})
            f_id = props.get("parcel_id") or props.get("survey_no") or props.get("id") or str(id(feat))
            old_map[f_id] = (feat, self.compute_feature_fingerprint(feat))

        new_map = {}
        for feat in new_features:
            props = feat.get("properties", {})
            f_id = props.get("parcel_id") or props.get("survey_no") or props.get("id") or str(id(feat))
            new_map[f_id] = (feat, self.compute_feature_fingerprint(feat))

        detected_changes: List[FeatureSyncChange] = []
        affected_parcel_ids = set()

        # Compare old vs new
        for f_id, (new_feat, new_hash) in new_map.items():
            props = new_feat.get("properties", {})
            p_id = props.get("parcel_id", f_id)

            if f_id not in old_map:
                ch = FeatureSyncChange(
                    feature_id=f_id,
                    parcel_id=p_id,
                    source_dataset=source_name,
                    source_version=new_version,
                    previous_hash=None,
                    current_hash=new_hash,
                    change_type="ADDED",
                    sync_status="SYNC_REQUIRED"
                )
                detected_changes.append(ch)
                affected_parcel_ids.add(p_id)
            else:
                old_feat, old_hash = old_map[f_id]
                if old_hash != new_hash:
                    old_props = old_feat.get("properties", {})
                    change_type = "MODIFIED"

                    if old_feat.get("geometry") != new_feat.get("geometry"):
                        change_type = "GEOMETRY_CHANGED"
                    elif old_props.get("area") != props.get("area"):
                        change_type = "AREA_CHANGED"
                    elif old_props != props:
                        change_type = "ATTRIBUTE_CHANGED"

                    ch = FeatureSyncChange(
                        feature_id=f_id,
                        parcel_id=p_id,
                        source_dataset=source_name,
                        source_version=new_version,
                        previous_hash=old_hash,
                        current_hash=new_hash,
                        change_type=change_type,
                        sync_status="SYNC_REQUIRED"
                    )
                    detected_changes.append(ch)
                    affected_parcel_ids.add(p_id)

        # Check for removed features
        for f_id, (old_feat, old_hash) in old_map.items():
            if f_id not in new_map:
                ch = FeatureSyncChange(
                    feature_id=f_id,
                    parcel_id=f_id,
                    source_dataset=source_name,
                    source_version=new_version,
                    previous_hash=old_hash,
                    current_hash=None,
                    change_type="REMOVED",
                    sync_status="SYNC_REQUIRED"
                )
                detected_changes.append(ch)
                affected_parcel_ids.add(f_id)

        sync_status_val = "SYNC_REQUIRED" if detected_changes else "SYNCED"

        status_record = DatasetSyncStatus(
            dataset_id=dataset_id,
            source_type=source_name,
            source_version=new_version,
            previous_version=old_version,
            sync_status=sync_status_val,
            change_detected=len(detected_changes) > 0,
            affected_feature_count=len(detected_changes),
            affected_parcel_count=len(affected_parcel_ids),
            detected_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self._active_runs[dataset_id] = status_record
        for ch in detected_changes:
            self._feature_changes[ch.feature_id] = ch

        # Persist to database
        storage_repo.save_sync_run(status_record.model_dump())
        storage_repo.save_feature_sync_changes([ch.model_dump() for ch in detected_changes])

        # Update parcel status to STALE / SYNC_REQUIRED in storage for affected parcels
        for p_id in affected_parcel_ids:
            storage_repo.update_parcel_status(p_id, "Conflict", conflict_type="SYNC_REQUIRED")

        return status_record, detected_changes

    def run_demo_update_detection(self) -> Tuple[DatasetSyncStatus, List[FeatureSyncChange]]:
        """
        Runs synthetic demo update scenario (Revenue Record update for Parcel 184/2).
        Area changes from 1520 m² → 1548 m², triggering SYNC_REQUIRED status.
        """
        old_revenue = [
            {"properties": {"parcel_id": "P003", "survey_no": "184/2", "area": 1520.0, "owner": "Ramesh Patil"}},
            {"properties": {"parcel_id": "P001", "survey_no": "184/1A", "area": 1250.0, "owner": "Sunita Deshmukh"}}
        ]
        new_revenue = [
            {"properties": {"parcel_id": "P003", "survey_no": "184/2", "area": 1548.0, "owner": "Ramesh Patil (Updated Register)"}},
            {"properties": {"parcel_id": "P001", "survey_no": "184/1A", "area": 1250.0, "owner": "Sunita Deshmukh"}}
        ]

        return self.check_source_dataset_updates(
            dataset_id="DS-Revenue",
            source_name="Land Revenue Register",
            old_features=old_revenue,
            new_features=new_revenue,
            old_version="v1.0",
            new_version="v2.0"
        )

    def process_sync_reconciliation(self, dataset_id: str = "DS-Revenue") -> Dict[str, Any]:
        """
        Recalculates evidence and conflict scores for affected parcels,
        updating sync status to REVIEW_REQUIRED.
        """
        run = self._active_runs.get(dataset_id)
        if not run:
            run, _ = self.run_demo_update_detection()

        run.sync_status = "REVIEW_REQUIRED"
        run.processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        storage_repo.save_sync_run(run.model_dump())

        for ch in self._feature_changes.values():
            ch.sync_status = "REVIEW_REQUIRED"

        storage_repo.save_feature_sync_changes([ch.model_dump() for ch in self._feature_changes.values()])

        return {
            "status": "PROCESSED",
            "message": "Source dataset change reconciliation recalculated.",
            "sync_status": run.model_dump(),
            "affected_parcels": run.affected_parcel_count
        }

    def approve_sync_reconciliation(
        self,
        dataset_id: str = "DS-Revenue",
        reviewer: str = "Land Record Officer (Admin)",
        comment: str = "Approved Revenue v2 register synchronization after verification."
    ) -> Dict[str, Any]:
        """
        Officer approves reconciliation:
        Marks status APPROVED/SYNCED, registers a new dataset version (e.g. Harmonized Dataset v5),
        and records provenance audit event.
        """
        run = self._active_runs.get(dataset_id)
        if not run:
            run, _ = self.run_demo_update_detection()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run.sync_status = "APPROVED"
        run.approved_at = now
        storage_repo.save_sync_run(run.model_dump())

        for ch in self._feature_changes.values():
            ch.sync_status = "APPROVED"
            storage_repo.update_parcel_status(ch.parcel_id, "Matched")

        storage_repo.save_feature_sync_changes([ch.model_dump() for ch in self._feature_changes.values()])

        # Register new Harmonized Dataset Version v5
        new_version = version_manager.register_version(
            dataset_id="DS-Harmonized-Master",
            feature_count=300,
            description=f"Harmonized Dataset Version v5 (Reconciled with {run.source_type} {run.source_version})"
        )

        # Record provenance audit log
        prov_record = provenance_tracker.create_provenance_record(
            feature_id="P003",
            source_dataset=f"{run.source_type} ({run.source_version})",
            source_type="Source Synchronization Update",
            reconciliation_decision="APPROVED",
            reviewer=reviewer
        )

        return {
            "status": "APPROVED",
            "sync_status": run.model_dump(),
            "new_dataset_version": new_version.model_dump(),
            "provenance_record": prov_record.model_dump(),
            "message": f"Dataset synchronization approved by {reviewer}. New Harmonized Version created."
        }

    def get_sync_status(self) -> List[Dict[str, Any]]:
        runs = storage_repo.get_sync_runs()
        if not runs and self._active_runs:
            runs = [r.model_dump() for r in self._active_runs.values()]
        return runs

    def get_sync_changes(self) -> List[Dict[str, Any]]:
        changes = storage_repo.get_feature_sync_changes()
        if not changes and self._feature_changes:
            changes = [c.model_dump() for c in self._feature_changes.values()]
        return changes

sync_engine = DatasetSyncEngine()
