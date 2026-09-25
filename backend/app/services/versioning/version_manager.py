"""
Dataset Versioning & Synchronization Engine for BHUMI-FUSION V2
Manages non-destructive dataset versioning (v1, v2, v3...) and feature-level lineage,
ensuring past land records are preserved during incremental harmonization.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.app.schemas.canonical import DatasetVersion

class VersionManager:
    def __init__(self):
        self._versions: Dict[str, List[DatasetVersion]] = {}

    def register_version(
        self,
        dataset_id: str,
        feature_count: int,
        description: str = "Initial Dataset Ingestion"
    ) -> DatasetVersion:
        if dataset_id not in self._versions:
            self._versions[dataset_id] = []
        
        # Deactivate previous active versions
        for v in self._versions[dataset_id]:
            v.active = False

        v_num = len(self._versions[dataset_id]) + 1
        v_id = f"VER-{dataset_id}-v{v_num}"

        version_record = DatasetVersion(
            version_id=v_id,
            dataset_id=dataset_id,
            version_number=v_num,
            description=description,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            feature_count=feature_count,
            active=True
        )

        self._versions[dataset_id].append(version_record)
        return version_record

    def get_version_history(self, dataset_id: str) -> List[DatasetVersion]:
        return self._versions.get(dataset_id, [])

version_manager = VersionManager()
