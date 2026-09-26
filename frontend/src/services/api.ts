import type {
  ReconciliationSummary,
  ValidationReport,
  ParcelSummary,
  ParcelDetail,
  ConflictItem
} from '../types/cadastral';

import type {
  CanonicalBuilding,
  ChangeDetectionItem,
  TopologyIssue,
  ProvenanceRecord,
  AIModelMetadata,
  EvaluationReportV2,
  RasterElevationMetadata,
  ParcelElevationMetrics,
  CanonicalUtilityAsset,
  ParcelUtilityAssociation,
  DatasetSyncStatus,
  FeatureSyncChange,
  RegisteredDataset
} from '../types/canonical';

const API_BASE = '/api';

export async function loadDemoDataset(): Promise<{
  status: string;
  message: string;
  summary: ReconciliationSummary;
  validation: ValidationReport;
}> {
  const res = await fetch(`${API_BASE}/demo/load`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to load demo dataset' }));
    throw new Error(err.detail || 'Failed to load demo dataset');
  }
  return res.json();
}

export async function uploadDatasets(formData: FormData): Promise<{
  status: string;
  message: string;
  summary: ReconciliationSummary;
  validation: ValidationReport;
}> {
  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload validation failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function runReconciliation(): Promise<{ status: string; summary: ReconciliationSummary }> {
  const res = await fetch(`${API_BASE}/reconciliation/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Reconciliation execution failed');
  return res.json();
}

export async function getSummary(): Promise<ReconciliationSummary> {
  const res = await fetch(`${API_BASE}/reconciliation/summary`);
  if (!res.ok) throw new Error('Failed to fetch summary');
  return res.json();
}

export async function getParcels(status: string = 'All', search?: string): Promise<ParcelSummary[]> {
  const params = new URLSearchParams();
  if (status && status !== 'All') params.set('status', status);
  if (search) params.set('search', search);

  const res = await fetch(`${API_BASE}/parcels?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch parcels');
  return res.json();
}

export async function getParcel(id: string): Promise<ParcelDetail> {
  const res = await fetch(`${API_BASE}/parcels/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Failed to fetch parcel ${id}`);
  return res.json();
}

export async function getConflicts(type: string = 'All'): Promise<ConflictItem[]> {
  const params = new URLSearchParams();
  if (type && type !== 'All') params.set('type', type);

  const res = await fetch(`${API_BASE}/conflicts?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch conflicts');
  return res.json();
}

export async function getConflict(id: string): Promise<ConflictItem> {
  const res = await fetch(`${API_BASE}/conflicts/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Failed to fetch conflict ${id}`);
  return res.json();
}

export async function approveConflict(
  id: string,
  user: string = 'Land Record Officer (Admin)',
  comment?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/conflicts/${encodeURIComponent(id)}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'ACCEPT', user, comment })
  });
  if (!res.ok) throw new Error('Failed to approve conflict');
  return res.json();
}

export async function rejectConflict(
  id: string,
  user: string = 'Land Record Officer (Admin)',
  comment?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/conflicts/${encodeURIComponent(id)}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'REJECT', user, comment })
  });
  if (!res.ok) throw new Error('Failed to reject conflict');
  return res.json();
}

export async function markManualReview(
  id: string,
  user: string = 'Land Record Officer (Admin)',
  comment?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/conflicts/${encodeURIComponent(id)}/manual-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'MANUAL_REVIEW', user, comment })
  });
  if (!res.ok) throw new Error('Failed to flag for manual review');
  return res.json();
}

// --- V2 API Client Methods ---

export async function getCanonicalBuildings(): Promise<CanonicalBuilding[]> {
  const res = await fetch(`${API_BASE}/v2/buildings`);
  if (!res.ok) return [];
  return res.json();
}

export async function getTemporalChanges(): Promise<ChangeDetectionItem[]> {
  const res = await fetch(`${API_BASE}/v2/changes`);
  if (!res.ok) return [];
  return res.json();
}

export async function getTopologyIssues(): Promise<TopologyIssue[]> {
  const res = await fetch(`${API_BASE}/v2/topology/issues`);
  if (!res.ok) return [];
  return res.json();
}

export async function getProvenance(featureId: string): Promise<ProvenanceRecord> {
  const res = await fetch(`${API_BASE}/v2/provenance/${encodeURIComponent(featureId)}`);
  if (!res.ok) throw new Error(`Failed to fetch provenance for ${featureId}`);
  return res.json();
}

export async function getAIModels(): Promise<AIModelMetadata[]> {
  const res = await fetch(`${API_BASE}/v2/models`);
  if (!res.ok) return [];
  return res.json();
}

export async function getEvaluationReportV2(): Promise<EvaluationReportV2> {
  const res = await fetch(`${API_BASE}/evaluation/report`);
  if (!res.ok) throw new Error('Failed to fetch evaluation report');
  return res.json();
}

export async function getRegisteredDatasets(): Promise<RegisteredDataset[]> {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) return [];
  return res.json();
}

// --- DSM/DTM Elevation API Methods ---

export async function getElevationDatasets(): Promise<RasterElevationMetadata[]> {
  const res = await fetch(`${API_BASE}/v2/dsm-dtm`);
  if (!res.ok) return [];
  return res.json();
}

export async function getParcelElevation(id: string): Promise<ParcelElevationMetrics> {
  const res = await fetch(`${API_BASE}/v2/parcels/${encodeURIComponent(id)}/elevation`);
  if (!res.ok) throw new Error(`Failed to fetch elevation for ${id}`);
  return res.json();
}

// --- Utility Network API Methods ---

export async function getUtilityAssets(): Promise<CanonicalUtilityAsset[]> {
  const res = await fetch(`${API_BASE}/v2/utilities`);
  if (!res.ok) return [];
  return res.json();
}

export async function getParcelUtility(id: string): Promise<ParcelUtilityAssociation> {
  const res = await fetch(`${API_BASE}/v2/parcels/${encodeURIComponent(id)}/utility`);
  if (!res.ok) throw new Error(`Failed to fetch utility metrics for ${id}`);
  return res.json();
}

// --- Dataset Synchronization API Methods ---

export async function getSyncStatus(): Promise<DatasetSyncStatus[]> {
  const res = await fetch(`${API_BASE}/v2/sync/status`);
  if (!res.ok) return [];
  return res.json();
}

export async function getSyncChanges(): Promise<FeatureSyncChange[]> {
  const res = await fetch(`${API_BASE}/v2/sync/changes`);
  if (!res.ok) return [];
  return res.json();
}

export async function checkSyncUpdates(): Promise<any> {
  const res = await fetch(`${API_BASE}/v2/sync/check`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to check dataset updates');
  return res.json();
}

export async function processSyncReconciliation(datasetId: string = 'DS-Revenue'): Promise<any> {
  const res = await fetch(`${API_BASE}/v2/sync/process?dataset_id=${encodeURIComponent(datasetId)}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to process sync reconciliation');
  return res.json();
}

export async function approveSyncReconciliation(
  datasetId: string = 'DS-Revenue',
  reviewer: string = 'Land Record Officer (Admin)',
  comment?: string
): Promise<any> {
  const params = new URLSearchParams({ dataset_id: datasetId, reviewer });
  if (comment) params.set('comment', comment);

  const res = await fetch(`${API_BASE}/v2/sync/approve?${params.toString()}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to approve sync reconciliation');
  return res.json();
}

// --- Full WebGIS & Export Methods ---

export async function getParcelsGeoJSON(): Promise<any> {
  const res = await fetch(`${API_BASE}/parcels/geojson`);
  if (!res.ok) throw new Error('Failed to fetch full fabric GeoJSON');
  return res.json();
}

export function getExportParcelsUrl(format: 'geojson' | 'csv' = 'geojson', status: string = 'All'): string {
  const params = new URLSearchParams({ format });
  if (status && status !== 'All') params.set('status', status);
  return `${API_BASE}/export/parcels?${params.toString()}`;
}

export async function getSpatialValidation(): Promise<any> {
  const res = await fetch(`${API_BASE}/spatial/validation`);
  if (!res.ok) throw new Error('Failed to fetch spatial overlay validation');
  return res.json();
}


