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
    # Rigorous Geodetic & Boundary Metrics
    boundary_conformance: float = Field(default=95.0, description="Percentage of boundary within tolerance (0-100)")
    mean_boundary_deviation_m: float = Field(default=0.0, description="Mean boundary deviation in meters")
    max_boundary_deviation_m: float = Field(default=0.0, description="Maximum boundary deviation in meters")
    p95_boundary_deviation_m: float = Field(default=0.0, description="95th percentile boundary deviation in meters")
    hausdorff_distance_m: float = Field(default=0.0, description="Symmetric Hausdorff distance in meters")
    coverage_source: float = Field(default=100.0, description="Area(A ∩ B) / Area(A) in percent")
    coverage_candidate: float = Field(default=100.0, description="Area(A ∩ B) / Area(B) in percent")
    area_difference_pct: float = Field(default=0.0, description="Area difference percentage")
    centroid_distance_m: float = Field(default=0.0, description="Projected Euclidean centroid distance in meters")
    # GNSS RTK Ground Evidence
    gnss_points_total: int = Field(default=0, description="Total GNSS survey points for parcel")
    gnss_points_inside: int = Field(default=0, description="GNSS survey points inside candidate polygon")
    gnss_inside_percentage: float = Field(default=0.0, description="Percentage of GNSS points inside candidate")
    gnss_status: str = Field(default="NO_DATA", description="HIGH, MEDIUM, LOW, or NO_DATA")
    # Drone vs Legacy Discrepancy
    drone_legacy_difference_pct: float = Field(default=0.0, description="Discrepancy between legacy and drone geometry")
    # Audit & Dynamic Reasoning
    hard_constraint_flags: List[str] = Field(default_factory=list, description="Hard constraint violation flags if any")
    decision_reason: str = Field(default="", description="Explanatory decision rationale")
    candidates_audit: List[Dict[str, Any]] = Field(default_factory=list, description="Audit list of all candidate parcels evaluated")
    why_matched_checklist: List[Dict[str, Any]] = Field(default_factory=list, description="Dynamic explainable checklist items")

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
