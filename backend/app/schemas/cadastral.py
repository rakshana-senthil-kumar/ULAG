"""
Pydantic Schemas for ULAG
Defines validation, response, and exchange models for cadastral reconciliation.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ValidationCard(BaseModel):
    name: str
    count: int
    unit: str
    status: str
    details: Optional[str] = None

class ValidationReport(BaseModel):
    cards: List[ValidationCard]
    crs_status: str = "Normalized (EPSG:4326/WGS84)"
    geometry_status: str = "Valid"
    schema_status: str = "Compatible"
    issues_count: int = 0
    issues: List[str] = []

class EvidenceMetrics(BaseModel):
    geometry_match: float = Field(..., description="Percentage geometry IoU/shape similarity (0-100)")
    area_match: float = Field(..., description="Percentage area ratio similarity (0-100)")
    centroid_match: float = Field(..., description="Percentage centroid proximity (0-100)")
    attribute_match: float = Field(..., description="Percentage survey & attribute agreement (0-100)")
    proximity_match: float = Field(..., description="Percentage spatial proximity (0-100)")
    overall_confidence: float = Field(..., description="Final weighted match confidence score (0-100)")

class SourceAreaComparison(BaseModel):
    legacy: Optional[float] = None
    revenue: Optional[float] = None
    drone: Optional[float] = None
    gnss: Optional[float] = None

class ParcelRecommendation(BaseModel):
    geometry_source: str
    recommended_area: float
    confidence: float
    explanation_summary: str
    explanation_details: List[str]

class ParcelSummary(BaseModel):
    parcel_id: str
    survey_no: str
    subdivision_no: Optional[str] = None
    full_survey: str
    confidence: float
    status: str  # "Matched", "Review", "Conflict"
    conflict_type: Optional[str] = None
    legacy_area: float
    recommended_area: Optional[float] = None

class ParcelDetail(BaseModel):
    parcel_id: str
    survey_no: str
    subdivision_no: Optional[str] = None
    full_survey: str
    status: str
    confidence: float
    conflict_type: Optional[str] = None
    sources_comparison: SourceAreaComparison
    evidence: EvidenceMetrics
    recommendation: ParcelRecommendation
    geometry_geojson: Dict[str, Any]
    drone_geometry_geojson: Optional[Dict[str, Any]] = None
    reconciled_geometry_geojson: Optional[Dict[str, Any]] = None
    gnss_points: List[Dict[str, Any]] = []

class ConflictItem(BaseModel):
    conflict_id: str
    parcel_id: str
    survey_no: str
    conflict_type: str  # "Geometry", "Area", "Attribute", "Missing", "Split", "Merge", "Duplicate"
    severity: str  # "High", "Medium", "Low"
    confidence: float
    discrepancy_delta: Optional[str] = None
    sources_comparison: SourceAreaComparison
    explanation: str
    status: str  # "Pending", "Approved", "Rejected", "Manual Review"
    timestamp: Optional[str] = None
    reviewed_by: Optional[str] = None

class ReviewDecisionRequest(BaseModel):
    action: str  # "ACCEPT", "REJECT", "MANUAL_REVIEW"
    comment: Optional[str] = None
    user: str = "Land Record Officer (Admin)"

class ReconciliationSummary(BaseModel):
    total_parcels: int
    matched_count: int
    conflicts_count: int
    review_count: int
    crs: str = "EPSG:4326"
    last_run_timestamp: str

class PipelineProgress(BaseModel):
    stage: str
    percentage: int
    message: str
