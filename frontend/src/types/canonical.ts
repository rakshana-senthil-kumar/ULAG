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
