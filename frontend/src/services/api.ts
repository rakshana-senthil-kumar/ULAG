import type {
  ReconciliationSummary,
  ValidationReport,
  ParcelSummary,
  ParcelDetail,
  ConflictItem
} from '../types/cadastral';

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

export async function getEvaluationReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/evaluation/report`);
  if (!res.ok) throw new Error('Failed to fetch evaluation report');
  return res.json();
}
