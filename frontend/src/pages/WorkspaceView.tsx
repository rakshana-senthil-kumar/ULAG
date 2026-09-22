import { useState } from 'react';
import type { FormEvent } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileText,
  Layers,
  ArrowRight,
  Database,
  Satellite,
  Compass,
  FileSpreadsheet
} from 'lucide-react';
import type { ReconciliationSummary, ValidationReport } from '../types/cadastral';
import { loadDemoDataset, uploadDatasets } from '../services/api';

interface WorkspaceViewProps {
  summary: ReconciliationSummary | null;
  validation: ValidationReport | null;
  onReconciliationReady: (summary: ReconciliationSummary, validation: ValidationReport) => void;
  onNavigateToReconcile: () => void;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({
  summary,
  validation,
  onReconciliationReady,
  onNavigateToReconcile
}) => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progressStage, setProgressStage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Upload file state
  const [legacyFile, setLegacyFile] = useState<File | null>(null);
  const [droneFile, setDroneFile] = useState<File | null>(null);
  const [gnssFile, setGnssFile] = useState<File | null>(null);
  const [revenueFile, setRevenueFile] = useState<File | null>(null);

  const handleLoadDemo = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      setProgressStage('Validating datasets...');
      await new Promise((r) => setTimeout(r, 250));

      setProgressStage('Matching parcels (spatial R-tree)...');
      await new Promise((r) => setTimeout(r, 350));

      setProgressStage('Detecting conflicts & boundary shifts...');
      await new Promise((r) => setTimeout(r, 300));

      setProgressStage('Calculating multi-criteria confidence...');
      await new Promise((r) => setTimeout(r, 250));

      setProgressStage('Preparing results...');
      const res = await loadDemoDataset();

      onReconciliationReady(res.summary, res.validation);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error executing demo reconciliation pipeline');
    } finally {
      setLoading(false);
      setProgressStage('');
    }
  };

  const handleUploadSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!legacyFile || !droneFile || !gnssFile || !revenueFile) {
      setErrorMessage('Please select all 4 required datasets (Legacy Cadastral, Drone Features, GNSS, Revenue).');
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      setProgressStage('Validating uploaded schemas & CRS...');
      const formData = new FormData();
      formData.append('legacy_file', legacyFile);
      formData.append('drone_file', droneFile);
      formData.append('gnss_file', gnssFile);
      formData.append('revenue_file', revenueFile);

      const res = await uploadDatasets(formData);
      onReconciliationReady(res.summary, res.validation);
      setShowUploadModal(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Dataset validation failed');
    } finally {
      setLoading(false);
      setProgressStage('');
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-10 px-6 font-sans">
      {/* Landing Header */}
      <div className="bg-white border border-slate-200 rounded p-8 shadow-xs mb-8 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded text-xs font-semibold text-blue-800 mb-4">
          <Layers className="w-3.5 h-3.5 text-blue-700" />
          BHUMI-FUSION CADASTRE
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-[#0b1e36] tracking-tight mb-2">
          AI-Powered Cadastral Reconciliation
        </h1>
        <p className="text-sm md:text-base text-slate-600 max-w-2xl mx-auto mb-6">
          Harmonize multiple land datasets, detect conflicts and generate explainable reconciliation candidates.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 mb-8">
          <button
            onClick={handleLoadDemo}
            disabled={loading}
            className="px-5 py-2.5 bg-[#0b1e36] hover:bg-[#152e50] text-white text-xs font-semibold rounded shadow-xs transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Database className="w-4 h-4 text-blue-300" />
            {loading ? 'Processing...' : 'Load Demo Dataset'}
          </button>

          <button
            onClick={() => setShowUploadModal(true)}
            disabled={loading}
            className="px-5 py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-semibold rounded shadow-xs transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <UploadCloud className="w-4 h-4 text-slate-600" />
            Upload Datasets
          </button>
        </div>

        {/* Progress Indicator */}
        {loading && (
          <div className="max-w-md mx-auto my-4 bg-slate-50 border border-slate-200 rounded p-3 text-center animate-pulse">
            <p className="text-xs font-medium text-blue-900">{progressStage}</p>
          </div>
        )}

        {/* Error Alert */}
        {errorMessage && (
          <div className="max-w-lg mx-auto my-4 p-3 bg-red-50 border border-red-200 rounded flex items-start gap-2.5 text-left">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-bold text-red-900">Validation Notice</p>
              <p className="text-xs text-red-700 mt-0.5">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Three Compact Status Indicators: Parcels | Conflicts | Matched */}
        {summary && (
          <div className="pt-6 border-t border-slate-200 grid grid-cols-3 divide-x divide-slate-200 max-w-xl mx-auto">
            <div className="text-center px-4">
              <div className="text-2xl font-bold text-slate-800">{summary.total_parcels}</div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider mt-0.5">
                Parcels
              </div>
            </div>
            <div className="text-center px-4">
              <div className="text-2xl font-bold text-red-700">{summary.conflicts_count}</div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider mt-0.5">
                Conflicts
              </div>
            </div>
            <div className="text-center px-4">
              <div className="text-2xl font-bold text-emerald-700">{summary.matched_count}</div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider mt-0.5">
                Matched
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Validation Screen Section */}
      {validation && (
        <div className="bg-white border border-slate-200 rounded p-6 shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-5">
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Data Validation</h2>
              <p className="text-xs text-slate-500 mt-0.5">Spatial topology and schema conformity check</p>
            </div>
            <button
              onClick={onNavigateToReconcile}
              className="px-4 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded flex items-center gap-1.5 cursor-pointer"
            >
              Open Reconciliation
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {validation.cards.map((card, idx) => (
              <div key={idx} className="border border-slate-200 rounded p-3 bg-slate-50/70">
                <div className="text-xs text-slate-500 font-medium">{card.name}</div>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-xl font-bold text-slate-800">{card.count.toLocaleString()}</span>
                  <span className="text-xs text-slate-600">{card.unit}</span>
                </div>
                <div className="text-[11px] text-emerald-700 font-semibold mt-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  {card.status}
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-3 border-t border-slate-100 pt-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-medium">CRS:</span>
              <span className="text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {validation.crs_status}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-medium">Geometry:</span>
              <span className="text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {validation.geometry_status}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-medium">Schema:</span>
              <span className="text-emerald-700 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {validation.schema_status}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Upload Datasets Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded border border-slate-300 max-w-2xl w-full p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Upload Datasets for Reconciliation
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 1. Legacy Cadastral Card */}
                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="w-4 h-4 text-blue-700" />
                    <span className="text-xs font-bold text-slate-800">Legacy Cadastral</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">GeoJSON / SHP</span>
                  <input
                    type="file"
                    accept=".geojson,.json"
                    onChange={(e) => setLegacyFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-blue-50 file:text-blue-700 cursor-pointer"
                  />
                  {legacyFile && (
                    <div className="mt-1.5 text-[10px] text-emerald-700 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> File accepted ({legacyFile.name})
                    </div>
                  )}
                </div>

                {/* 2. Drone Features Card */}
                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <Satellite className="w-4 h-4 text-amber-600" />
                    <span className="text-xs font-bold text-slate-800">Drone Features</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">GeoJSON</span>
                  <input
                    type="file"
                    accept=".geojson,.json"
                    onChange={(e) => setDroneFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-amber-50 file:text-amber-700 cursor-pointer"
                  />
                  {droneFile && (
                    <div className="mt-1.5 text-[10px] text-emerald-700 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> File accepted ({droneFile.name})
                    </div>
                  )}
                </div>

                {/* 3. GNSS / CORS Card */}
                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <Compass className="w-4 h-4 text-red-600" />
                    <span className="text-xs font-bold text-slate-800">GNSS / CORS</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">CSV</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setGnssFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-red-50 file:text-red-700 cursor-pointer"
                  />
                  {gnssFile && (
                    <div className="mt-1.5 text-[10px] text-emerald-700 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> File accepted ({gnssFile.name})
                    </div>
                  )}
                </div>

                {/* 4. Revenue Records Card */}
                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-bold text-slate-800">Revenue Records</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">CSV / XLSX</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setRevenueFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-emerald-50 file:text-emerald-700 cursor-pointer"
                  />
                  {revenueFile && (
                    <div className="mt-1.5 text-[10px] text-emerald-700 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> File accepted ({revenueFile.name})
                    </div>
                  )}
                </div>
              </div>

              {errorMessage && (
                <div className="p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-1.5 text-xs text-slate-600 hover:text-slate-800 font-medium cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-1.5 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded cursor-pointer disabled:opacity-50"
                >
                  {loading ? 'Validating...' : 'Validate & Ingest'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
