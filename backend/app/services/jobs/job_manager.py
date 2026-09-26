"""
Asynchronous Job Management & Progress Tracking Service for ULAG
Tracks long-running operations (Large Ingestion, AI Extraction, Raster Change Detection).
Supports states: QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED.
Exposes real-time progress (0% - 100%), processed count, total count, and errors.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from backend.app.models.storage import storage_repo

class JobManager:
    def __init__(self):
        self._memory_jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(
        self,
        job_type: str,
        total_count: int = 100,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Creates and initializes a new asynchronous tracking job."""
        job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "QUEUED",
            "progress": 0,
            "processed_count": 0,
            "total_count": total_count,
            "error_message": "",
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now
        }
        self._memory_jobs[job_id] = job_data
        storage_repo.save_processing_job(job_data)
        return job_id

    def update_progress(
        self,
        job_id: str,
        processed: int,
        total: Optional[int] = None,
        status: Optional[str] = "PROCESSING",
        error: Optional[str] = None
    ):
        """Updates progress percentage and processed counts."""
        job = self._memory_jobs.get(job_id)
        if not job:
            stored = storage_repo.get_processing_job(job_id)
            if stored:
                job = stored
                self._memory_jobs[job_id] = job

        if job:
            tot = total if total is not None else job.get("total", 100)
            tot = max(tot, 1)
            pct = min(100, int((processed / tot) * 100.0))

            job["progress"] = pct
            job["processed_count"] = processed
            job["total_count"] = tot
            if status:
                job["status"] = status
            if error:
                job["error_message"] = error
            job["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            storage_repo.update_processing_job(
                job_id=job_id,
                progress=pct,
                status=job["status"],
                processed=processed,
                total=tot,
                error=error
            )

    def complete_job(self, job_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Marks job as 100% COMPLETED."""
        job = self._memory_jobs.get(job_id)
        if job:
            job["status"] = "COMPLETED"
            job["progress"] = 100
            if metadata:
                job.setdefault("metadata", {}).update(metadata)
            storage_repo.update_processing_job(
                job_id=job_id,
                progress=100,
                status="COMPLETED"
            )

    def fail_job(self, job_id: str, error_message: str):
        """Marks job as FAILED with detailed diagnostic reason."""
        job = self._memory_jobs.get(job_id)
        if job:
            job["status"] = "FAILED"
            job["error_message"] = error_message
            storage_repo.update_processing_job(
                job_id=job_id,
                status="FAILED",
                error=error_message
            )

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves real-time status of a job."""
        stored = storage_repo.get_processing_job(job_id)
        if stored:
            return stored
        return self._memory_jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Returns all registered background processing jobs."""
        return storage_repo.get_processing_jobs()

job_manager = JobManager()
