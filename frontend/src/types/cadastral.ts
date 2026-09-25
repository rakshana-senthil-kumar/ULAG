export interface ValidationCard {
  name: string;
  count: number;
  unit: string;
  status: string;
  details?: string;
}

export interface ValidationReport {
  cards: ValidationCard[];
  crs_status: string;
  geometry_status: string;
  schema_status: string;
  issues_count: number;
  issues: string[];
}

export interface ChecklistItem {
  status: 'PASS' | 'WARN' | 'FAIL' | 'INFO';
  text: string;
}

export interface CandidateAuditItem {
  candidate_id: string;
  survey_candidate: string;
  iou: number;
  coverage_source: number;
  coverage_candidate: number;
  area_diff_pct: number;
  centroid_dist_m: number;
  mean_boundary_dev_m: number;
  max_boundary_dev_m: number;
  p95_boundary_dev_m: number;
  hausdorff_m: number;
  boundary_conformance: number;
  gnss_inside_pct: number;
  attribute_match: number;
  score: number;
  rank?: number;
  hard_flags?: string[];
  rejection_reason?: string;
}

export interface EvidenceMetrics {
  geometry_match: number;
  area_match: number;
  centroid_match: number;
  attribute_match: number;
  proximity_match: number;
  overall_confidence: number;
  boundary_conformance?: number;
  mean_boundary_deviation_m?: number;
  max_boundary_deviation_m?: number;
  p95_boundary_deviation_m?: number;
  hausdorff_distance_m?: number;
  coverage_source?: number;
  coverage_candidate?: number;
  area_difference_pct?: number;
  centroid_distance_m?: number;
  gnss_points_total?: number;
  gnss_points_inside?: number;
  gnss_inside_percentage?: number;
  gnss_status?: string;
  drone_legacy_difference_pct?: number;
  hard_constraint_flags?: string[];
  decision_reason?: string;
  candidates_audit?: CandidateAuditItem[];
  why_matched_checklist?: ChecklistItem[];
}

export interface SourceAreaComparison {
  legacy?: number;
  revenue?: number;
  drone?: number;
  gnss?: number;
}

export interface ParcelRecommendation {
  geometry_source: string;
  recommended_area: number;
  confidence: number;
  explanation_summary: string;
  explanation_details: string[];
}

export interface ParcelSummary {
  parcel_id: string;
  survey_no: string;
  subdivision_no?: string;
  full_survey: string;
  confidence: number;
  status: 'Matched' | 'Review' | 'Conflict';
  conflict_type?: string;
  legacy_area: number;
  recommended_area?: number;
}

export interface GNSSPoint {
  point_id: string;
  survey_no: string;
  latitude: number;
  longitude: number;
  accuracy_m: number;
}

export interface ParcelDetail {
  parcel_id: string;
  survey_no: string;
  subdivision_no?: string;
  full_survey: string;
  status: string;
  confidence: number;
  conflict_type?: string;
  sources_comparison: SourceAreaComparison;
  evidence: EvidenceMetrics;
  recommendation: ParcelRecommendation;
  geometry_geojson: any;
  drone_geometry_geojson?: any;
  reconciled_geometry_geojson?: any;
  gnss_points: GNSSPoint[];
}

export interface ConflictItem {
  conflict_id: string;
  parcel_id: string;
  survey_no: string;
  conflict_type: string;
  severity: 'High' | 'Medium' | 'Low';
  confidence: number;
  discrepancy_delta?: string;
  sources_comparison: SourceAreaComparison;
  explanation: string;
  status: 'Pending' | 'Approved' | 'Rejected' | 'Manual Review';
  timestamp?: string;
  reviewed_by?: string;
}

export interface ReconciliationSummary {
  total_parcels: number;
  matched_count: number;
  conflicts_count: number;
  review_count: number;
  crs: string;
  last_run_timestamp: string;
}
