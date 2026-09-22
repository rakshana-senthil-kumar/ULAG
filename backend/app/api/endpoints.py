"""
FastAPI Endpoints for BHUMI-FUSION
Provides clean, strictly typed, RESTful interfaces for data ingestion,
reconciliation execution, parcel & conflict queries, review decisions, and evaluation reporting.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from typing import List, Optional, Dict, Any
import json
import os

from backend.app.schemas.cadastral import (
    ReconciliationSummary, ValidationReport, ParcelSummary,
    ParcelDetail, ConflictItem, ReviewDecisionRequest, EvidenceMetrics
)
from backend.app.services.pipeline import pipeline, ROOT_DIR
from backend.app.models.storage import storage_repo
from backend.app.services.ingestion.loader import IngestionError

router = APIRouter(prefix="/api")

@router.post("/demo/load", summary="Load Demo Dataset and run full reconciliation pipeline")
async def load_demo_dataset():
    """Triggers end-to-end ingestion and reconciliation for synthetic demo datasets."""
    try:
        result = pipeline.load_and_run_demo()
        return {
            "status": "success",
            "message": "Demo datasets loaded and reconciled successfully",
            "summary": result["summary"],
            "validation": result["validation"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load demo dataset: {str(e)}"
        )

@router.post("/datasets/upload", summary="Upload custom cadastral datasets")
async def upload_datasets(
    legacy_file: UploadFile = File(..., description="Legacy cadastral GeoJSON"),
    drone_file: UploadFile = File(..., description="Drone features GeoJSON"),
    gnss_file: UploadFile = File(..., description="GNSS survey CSV"),
    revenue_file: UploadFile = File(..., description="Revenue records CSV")
):
    """Uploads and processes the 4 core datasets with non-technical validation feedback."""
    try:
        legacy_bytes = await legacy_file.read()
        drone_bytes = await drone_file.read()
        gnss_bytes = await gnss_file.read()
        revenue_bytes = await revenue_file.read()

        result = pipeline.run_pipeline(legacy_bytes, drone_bytes, gnss_bytes, revenue_bytes)
        return {
            "status": "success",
            "message": "Datasets uploaded, validated, and harmonized successfully",
            "summary": result["summary"],
            "validation": result["validation"]
        }
    except IngestionError as ie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ie.user_friendly_message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset processing error: {str(e)}"
        )

@router.post("/reconciliation/run", summary="Trigger reconciliation on currently loaded datasets")
async def run_reconciliation():
    """Runs the spatial matching and conflict detection pipeline."""
    result = pipeline.load_and_run_demo()
    return {
        "status": "completed",
        "summary": result["summary"]
    }

@router.get("/reconciliation/summary", response_model=ReconciliationSummary)
async def get_reconciliation_summary():
    """Returns top-level metric counters: total parcels, matched, conflicts, review count."""
    summary = storage_repo.get_pipeline_summary()
    if not summary:
        # Load demo on first empty call
        res = pipeline.load_and_run_demo()
        summary = res["summary"]
    return ReconciliationSummary(**summary)

@router.get("/parcels", response_model=List[ParcelSummary])
async def list_parcels(
    status_filter: Optional[str] = Query("All", alias="status"),
    search: Optional[str] = Query(None)
):
    """Lists all parcels with search by survey number or parcel ID and status filtering."""
    parcels = storage_repo.get_parcels(status=status_filter, search=search)
    results = []
    for p in parcels:
        results.append(ParcelSummary(
            parcel_id=p["parcel_id"],
            survey_no=p["survey_no"],
            subdivision_no=p.get("subdivision_no"),
            full_survey=p["full_survey"],
            confidence=p["confidence"],
            status=p["status"],
            conflict_type=p.get("conflict_type"),
            legacy_area=p["legacy_area"],
            recommended_area=p.get("recommendation", {}).get("recommended_area") if p.get("recommendation") else None
        ))
    return results

@router.get("/parcels/{id}", response_model=ParcelDetail)
async def get_parcel_by_id(id: str):
    """Returns detailed parcel record including multi-layer GeoJSON and source comparison."""
    detail = storage_repo.get_parcel_detail(id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Parcel '{id}' not found")
    return ParcelDetail(**detail)

@router.get("/parcels/{id}/evidence")
async def get_parcel_evidence(id: str):
    """Returns the exact 5-factor mathematical evidence breakdown and generated rationale."""
    detail = storage_repo.get_parcel_detail(id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Parcel '{id}' not found")
    return {
        "parcel_id": detail["parcel_id"],
        "survey_no": detail["full_survey"],
        "confidence": detail["confidence"],
        "evidence_breakdown": detail["evidence"],
        "recommendation": detail["recommendation"],
        "sources_comparison": detail["sources_comparison"]
    }

@router.get("/conflicts", response_model=List[ConflictItem])
async def list_conflicts(
    conflict_type: Optional[str] = Query("All", alias="type")
):
    """Returns all detected conflicts with type filtering (All, Geometry, Area, Attribute, Missing)."""
    conflicts = storage_repo.get_conflicts(conflict_type=conflict_type)
    return [ConflictItem(**c) for c in conflicts]

@router.get("/conflicts/{id}", response_model=ConflictItem)
async def get_conflict_by_id(id: str):
    """Returns detail of specific conflict case."""
    conflict = storage_repo.get_conflict_detail(id)
    if not conflict:
        raise HTTPException(status_code=404, detail=f"Conflict '{id}' not found")
    return ConflictItem(**conflict)

@router.post("/conflicts/{id}/approve")
async def approve_conflict_reconciliation(id: str, payload: ReviewDecisionRequest = ReviewDecisionRequest(action="ACCEPT")):
    """Approves evidence-weighted reconciliation candidate and creates audit log."""
    res = storage_repo.record_review_decision(id, "ACCEPT", payload.user, payload.comment)
    return {"status": "Approved", "audit": res}

@router.post("/conflicts/{id}/reject")
async def reject_conflict_reconciliation(id: str, payload: ReviewDecisionRequest = ReviewDecisionRequest(action="REJECT")):
    """Rejects reconciliation candidate and leaves parcel in dispute/unresolved state."""
    res = storage_repo.record_review_decision(id, "REJECT", payload.user, payload.comment)
    return {"status": "Rejected", "audit": res}

@router.post("/conflicts/{id}/manual-review")
async def mark_conflict_manual_review(id: str, payload: ReviewDecisionRequest = ReviewDecisionRequest(action="MANUAL_REVIEW")):
    """Escalates case to joint field survey inspection."""
    res = storage_repo.record_review_decision(id, "MANUAL_REVIEW", payload.user, payload.comment)
    return {"status": "Manual Review Required", "audit": res}

@router.get("/evaluation/report")
async def get_evaluation_report():
    """Evaluates spatial matching engine against hidden ground-truth baseline."""
    gt_path = os.path.join(str(ROOT_DIR), "data", "demo", "ground_truth.json")
    if not os.path.exists(gt_path):
        return {"error": "Ground truth baseline not found"}

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    parcels = storage_repo.get_parcels()
    total_known = len(ground_truth)
    correct_matches = 0
    false_matches = 0
    unmatched_count = 0

    for p in parcels:
        p_id = p["parcel_id"]
        gt = ground_truth.get(p_id)
        if not gt:
            continue
        is_clean_in_gt = (gt.get("conflict_type") is None and gt.get("matched") is True)
        is_clean_in_system = (p["status"] == "Matched")

        if is_clean_in_gt and is_clean_in_system:
            correct_matches += 1
        elif not is_clean_in_gt and not is_clean_in_system:
            correct_matches += 1
        else:
            false_matches += 1

    precision = round((correct_matches / max(total_known, 1)) * 100, 2)
    recall = round(((total_known - false_matches) / max(total_known, 1)) * 100, 2)

    return {
        "total_known_parcels": total_known,
        "correct_evaluations": correct_matches,
        "false_evaluations": false_matches,
        "precision_percentage": precision,
        "recall_percentage": recall,
        "f1_score": round(2 * (precision * recall) / (precision + recall), 2)
    }
