export interface MultiDimensionalConfidence {
  spatial_match_confidence: number;
  geometry_confidence: number;
  attribute_confidence: number;
  source_confidence: number;
  topology_confidence: number;
  extraction_confidence: number;
  change_detection_confidence: number;
  overall_confidence: number;
}

export interface ProvenanceRecord {
  feature_id: string;
  source_dataset: string;
  source_feature_id?: string;
  source_type: string;
  source_date?: string;
  crs_used: string;
  transformations_applied: string[];
  ai_model_version?: string;
  matching_method: string;
  reconciliation_decision?: string;
  reviewer?: string;
  created_at: string;
}

export interface TopologyIssue {
  issue_id: string;
  feature_id: string;
  issue_type: string;
  severity: 'High' | 'Medium' | 'Low';
  location_wkt?: string;
  auto_fixed: boolean;
  fix_description?: string;
}

export interface ChangeDetectionItem {
  change_id: string;
  feature_id: string;
  survey_no: string;
  change_type: string;
  severity: 'High' | 'Medium' | 'Low';
  previous_value?: string;
  current_value?: string;
  change_magnitude?: number;
  confidence: number;
  detected_at: string;
}

export interface CanonicalBuilding {
  building_id: string;
  parcel_uid?: string;
  survey_number?: string;
  geometry_geojson: any;
  area_m2: number;
  building_type: string;
  confidence: number;
  extraction_source: string;
  model_version: string;
  detected_at: string;
  centroid?: [number, number];
  bbox?: [number, number, number, number];
  pixel_bbox?: [number, number, number, number];
  bbox_geojson?: any;
  segmentation_mask_geojson?: any;
  source_raster_coordinates?: any;
  vertex_count?: number;
  crs?: string;
  overlap_percentage?: number;
  conflict_status?: string;
}

export interface AIModelMetadata {
  model_name: string;
  version: string;
  task: string;
  framework: string;
  file_path: string;
  training_dataset: string;
  evaluation_metrics: {
    precision: number;
    recall: number;
    f1_score: number;
    mean_iou?: number;
  };
  registered_at: string;
}

export interface EvaluationReportV2 {
  total_known_parcels: number;
  correct_evaluations: number;
  false_evaluations: number;
  precision_percentage: number;
  recall_percentage: number;
  f1_score: number;
  mean_spatial_error_m: number;
  mean_area_error_m2: number;
  topology_error_rate_pct: number;
}

export interface RasterElevationMetadata {
  dataset_id: string;
  dataset_version: string;
  dataset_type: 'DSM' | 'DTM';
  source_name: string;
  file_name: string;
  crs: string;
  width: number;
  height: number;
  resolution: number;
  bounds: number[];
  min_elevation: number;
  max_elevation: number;
  mean_elevation: number;
  nodata_value: number;
  ingested_at: string;
  processing_status: string;
}

export interface ParcelElevationMetrics {
  parcel_id: string;
  has_elevation_data: boolean;
  min_elevation_m?: number;
  max_elevation_m?: number;
  mean_elevation_m?: number;
  elevation_range_m?: number;
  slope_deg?: number;
  elevation_status: string;
}

export interface CanonicalUtilityAsset {
  utility_id: string;
  utility_type: 'Electricity' | 'Water' | 'Sewer' | 'Gas' | 'Telecom' | string;
  asset_type: 'line' | 'point' | 'polygon' | string;
  status: string;
  source: string;
  geometry_geojson: any;
  crs: string;
  dataset_version: string;
}

export interface ParcelUtilityAssociation {
  parcel_id: string;
  utility_count: number;
  electricity_count: number;
  water_count: number;
  sewer_count: number;
  gas_count: number;
  telecom_count: number;
  nearest_utility_distance_m: number;
  intersecting_utility_types: string[];
  buffered_utility_types: string[];
}

export interface DatasetSyncStatus {
  dataset_id: string;
  source_type: string;
  source_version: string;
  previous_version?: string;
  sync_status: 'SYNCED' | 'STALE' | 'SYNC_REQUIRED' | 'PROCESSING' | 'REVIEW_REQUIRED' | 'APPROVED';
  change_detected: boolean;
  affected_feature_count: number;
  affected_parcel_count: number;
  detected_at: string;
  processed_at?: string;
  approved_at?: string;
}

export interface FeatureSyncChange {
  feature_id: string;
  parcel_id: string;
  source_dataset: string;
  source_version: string;
  previous_hash?: string;
  current_hash?: string;
  change_type: 'ADDED' | 'REMOVED' | 'MODIFIED' | 'UNCHANGED' | 'GEOMETRY_CHANGED' | 'ATTRIBUTE_CHANGED' | 'BOUNDARY_CHANGED' | 'AREA_CHANGED' | 'POSITION_CHANGED';
  sync_status: string;
  detected_at: string;
}

export interface RegisteredDataset {
  dataset_id: string;
  name: string;
  source_type: string;
  format: string;
  record_count: number;
  crs: string;
  status: string;
}

