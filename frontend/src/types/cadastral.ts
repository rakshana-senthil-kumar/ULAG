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

export interface EvidenceMetrics {
  geometry_match: number;
  area_match: number;
  centroid_match: number;
  attribute_match: number;
  proximity_match: number;
  overall_confidence: number;
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
