"""
Canonical and Extended Geospatial Schemas for ULAG
Defines models for Multi-Source Ingestion, AI Building Extraction,
Elevation Raster Analysis, Utility Networks, Topology Validation,
Temporal Change Detection, Dataset Synchronization, and Provenance.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

class MultiDimensionalConfidence(BaseModel):
    spatial_match_confidence: float = Field(..., description="IoU and boundary conformance")
    geometry_confidence: float = Field(..., description="Geometric shape preservation")
    attribute_confidence: float = Field(..., description="Attribute agreement")
    source_confidence: float = Field(..., description="Measurement fidelity weighting")
    topology_confidence: float = Field(..., description="Planar topology conformance")
    extraction_confidence: float = Field(..., description="Drone/AI feature confidence")
    change_detection_confidence: float = Field(..., description="Temporal stability confidence")
    overall_confidence: float = Field(..., description="Composite weighted confidence")

class ProvenanceRecord(BaseModel):
    feature_id: str
    source_dataset: str
    source_feature_id: Optional[str] = None
    source_type: str
    source_date: Optional[str] = None
    crs_used: str = "EPSG:4326"
    transformations_applied: List[str] = []
    ai_model_version: Optional[str] = None
    matching_method: str = "Shapely STRtree + Multi-Factor Consensus"
    reconciliation_decision: Optional[str] = None
    reviewer: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class TopologyIssue(BaseModel):
    issue_id: str
    feature_id: str
    issue_type: str  # "Self-Intersection", "Overlap", "Gap", "Sliver", "Duplicate Geometry"
    severity: Literal["High", "Medium", "Low"]
    location_wkt: Optional[str] = None
    original_geometry_wkt: Optional[str] = None
    repaired_geometry_wkt: Optional[str] = None
    auto_fixed: bool = False
    fix_description: Optional[str] = None

class ChangeDetectionItem(BaseModel):
    change_id: str
    feature_id: str
    survey_no: str
    change_type: str  # "New Construction", "Demolition", "Boundary Shift", "Land Use Conversion"
    severity: Literal["High", "Medium", "Low"]
    previous_value: Optional[str] = None
    current_value: Optional[str] = None
    change_magnitude: Optional[float] = None
    confidence: float
    detected_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
class CanonicalBuilding(BaseModel):
    
    model_config = {"protected_namespaces": ()}
    building_id: str
    parcel_uid: Optional[str] = None
    survey_number: Optional[str] = None
    geometry_geojson: Dict[str, Any]
    area_m2: float
    building_type: str = "Structure"
    confidence: float
    extraction_source: str = "Drone ORI Feature Extraction"
    model_version: str = "GeoAI-YOLO-v8-Urban"
    detected_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    centroid: Optional[List[float]] = None
    bbox: Optional[List[float]] = None
    pixel_bbox: Optional[List[int]] = None
    bbox_geojson: Optional[Dict[str, Any]] = None
    segmentation_mask_geojson: Optional[Dict[str, Any]] = None
    source_raster_coordinates: Optional[Dict[str, Any]] = None
    vertex_count: Optional[int] = None
    crs: Optional[str] = "EPSG:4326"
    overlap_percentage: Optional[float] = None
    conflict_status: Optional[str] = None

class AIModelMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    mean_iou: Optional[float] = None

class AIModelMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str
    version: str
    task: str
    framework: str
    file_path: str
    training_dataset: str
    evaluation_metrics: AIModelMetrics
    registered_at: str

class EvaluationReportV2(BaseModel):
    total_known_parcels: int
    correct_evaluations: int
    false_evaluations: int
    precision_percentage: float
    recall_percentage: float
    f1_score: float
    mean_spatial_error_m: float
    mean_area_error_m2: float
    topology_error_rate_pct: float

class RasterElevationMetadata(BaseModel):
    dataset_id: str
    dataset_version: str
    dataset_type: Literal["DSM", "DTM"]
    source_name: str
    file_name: str
    crs: str = "EPSG:32643"
    width: int
    height: int
    resolution: float
    bounds: List[float]
    min_elevation: float
    max_elevation: float
    mean_elevation: float
    nodata_value: float = -9999.0
    ingested_at: str
    processing_status: str = "Processed"

class ParcelElevationMetrics(BaseModel):
    parcel_id: str
    has_elevation_data: bool = True
    min_elevation_m: Optional[float] = None
    max_elevation_m: Optional[float] = None
    mean_elevation_m: Optional[float] = None
    elevation_range_m: Optional[float] = None
    slope_deg: Optional[float] = None
    elevation_status: str = "Computed"

class CanonicalUtilityAsset(BaseModel):
    utility_id: str
    utility_type: Literal["Electricity", "Water", "Sewer", "Gas", "Telecom"] | str
    asset_type: Literal["line", "point", "polygon"] | str
    status: str = "Operational"
    source: str = "Municipal Utilities GIS"
    geometry_geojson: Dict[str, Any]
    crs: str = "EPSG:4326"
    dataset_version: str = "v1.0"

class ParcelUtilityAssociation(BaseModel):
    parcel_id: str
    utility_count: int
    electricity_count: int
    water_count: int
    sewer_count: int
    gas_count: int
    telecom_count: int
    nearest_utility_distance_m: float
    intersecting_utility_types: List[str]
    buffered_utility_types: List[str]

class DatasetSyncStatus(BaseModel):
    dataset_id: str
    source_type: str
    source_version: str
    previous_version: Optional[str] = None
    sync_status: Literal["SYNCED", "STALE", "SYNC_REQUIRED", "PROCESSING", "REVIEW_REQUIRED", "APPROVED"]
    change_detected: bool
    affected_feature_count: int
    affected_parcel_count: int
    detected_at: str
    processed_at: Optional[str] = None
    approved_at: Optional[str] = None

class FeatureSyncChange(BaseModel):
    feature_id: str
    parcel_id: str
    source_dataset: str
    source_version: str
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None
    change_type: Literal[
        "ADDED", "REMOVED", "MODIFIED", "UNCHANGED",
        "GEOMETRY_CHANGED", "ATTRIBUTE_CHANGED", "BOUNDARY_CHANGED",
        "AREA_CHANGED", "POSITION_CHANGED"
    ]
    sync_status: str
    detected_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class RegisteredDataset(BaseModel):
    dataset_id: str
    name: str
    source_type: str
    format: str
    record_count: int
    crs: str
    status: str

class DatasetVersion(BaseModel):
    version_id: str
    dataset_id: str
    version_number: int
    description: str
    created_at: str
    feature_count: int
    active: bool = True

