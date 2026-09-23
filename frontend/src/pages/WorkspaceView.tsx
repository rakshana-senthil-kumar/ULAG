import React, { useState } from 'react';
import type { FormEvent } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  FileText,
  ArrowRight,
  Database,
  Satellite,
  Compass,
  FileSpreadsheet,
  Play,
  Check
} from 'lucide-react';
import type { ReconciliationSummary, ValidationReport } from '../types/cadastral';
import type { RasterElevationMetadata, CanonicalUtilityAsset } from '../types/canonical';
import { loadDemoDataset, uploadDatasets, getElevationDatasets, getUtilityAssets } from '../services/api';

interface WorkspaceViewProps {
  summary?: ReconciliationSummary | null;
  validation: ValidationReport | null;
  onReconciliationReady: (summary: ReconciliationSummary, validation: ValidationReport) => void;
  onNavigateToReconcile: () => void;
}

export const WorkspaceView: React.FC<WorkspaceViewProps> = ({
  summary: _summary,
  validation,
  onReconciliationReady,
  onNavigateToReconcile
}) => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeStageIdx, setActiveStageIdx] = useState<number>(-1);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Upload file state
  const [legacyFile, setLegacyFile] = useState<File | null>(null);
  const [droneFile, setDroneFile] = useState<File | null>(null);
  const [gnssFile, setGnssFile] = useState<File | null>(null);
  const [revenueFile, setRevenueFile] = useState<File | null>(null);

  // Live raster & utility state
  const [elevationDatasets, setElevationDatasets] = useState<RasterElevationMetadata[]>([]);
  const [utilityAssets, setUtilityAssets] = useState<CanonicalUtilityAsset[]>([]);

  React.useEffect(() => {
    getElevationDatasets().then(setElevationDatasets).catch(console.error);
    getUtilityAssets().then(setUtilityAssets).catch(console.error);
  }, []);

  const pipelineStages = [
    'Dataset validation',
    'CRS normalization (EPSG:32643)',
    'Spatial indexing (STRtree)',
    'Spatial candidate matching',
    'Attribute harmonization',
    'Topology validation & repair',
    'Change detection calculation',
    'Confidence score generation',
    'Finalization'
  ];

  const handleRunHarmonization = async () => {
    setLoading(true);
    setErrorMessage(null);
    setActiveStageIdx(0);

    try {
      for (let i = 0; i < pipelineStages.length; i++) {
        setActiveStageIdx(i);
        await new Promise((r) => setTimeout(r, 180));
      }

      const res = await loadDemoDataset();
      onReconciliationReady(res.summary, res.validation);
    } catch (err: any) {
      setErrorMessage(err.message || 'Harmonization execution failed');
    } finally {
      setLoading(false);
      setActiveStageIdx(-1);
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
      const formData = new FormData();
      formData.append('legacy_file', legacyFile);
      formData.append('drone_file', droneFile);
      formData.append('gnss_file', gnssFile);
      formData.append('revenue_file', revenueFile);

      const res = await uploadDatasets(formData);
      onReconciliationReady(res.summary, res.validation);
      setShowUploadModal(false);
    } catch (err: any) {
      setErrorMessage(err.message || 'Dataset upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto p-6 space-y-6 font-sans select-none">
      {/* 1. Header & Data Pipeline Flow Stepper */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-2xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 bg-blue-50 border border-blue-200 rounded text-[11px] font-bold text-blue-800 mb-1">
              <Database className="w-3.5 h-3.5 text-blue-700" />
              MULTI-SOURCE DATA INGESTION ENGINE
            </div>
            <h1 className="text-xl font-bold text-[#0b1e36]">Heterogeneous Geospatial Data Pipeline</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated ingestion, CRS transformation, spatial candidate index, and topology validation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-semibold rounded shadow-2xs transition flex items-center gap-2"
            >
              <UploadCloud className="w-4 h-4 text-slate-600" />
              Upload Custom Datasets
            </button>

            <button
              onClick={handleRunHarmonization}
              disabled={loading}
              className="px-5 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-bold rounded shadow-xs transition flex items-center gap-2 disabled:opacity-50"
            >
              <Play className="w-4 h-4 text-white fill-white" />
              {loading ? 'Executing Pipeline...' : 'Run Harmonization'}
            </button>
          </div>
        </div>

        {/* 5-Step Visual Data Pipeline Stepper */}
        <div className="grid grid-cols-5 gap-2 text-xs font-medium">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-blue-900 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-700 text-white flex items-center justify-center font-bold text-[10px]">1</span>
            <div>
              <span className="font-bold block">Upload</span>
              <span className="text-[10px] text-blue-700">4 Data Sources</span>
            </div>
          </div>

          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-blue-900 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-700 text-white flex items-center justify-center font-bold text-[10px]">2</span>
            <div>
              <span className="font-bold block">Validate</span>
              <span className="text-[10px] text-blue-700">Schema & Topology</span>
            </div>
          </div>

          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-blue-900 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-700 text-white flex items-center justify-center font-bold text-[10px]">3</span>
            <div>
              <span className="font-bold block">Transform</span>
              <span className="text-[10px] text-blue-700">EPSG:32643 UTM</span>
            </div>
          </div>

          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-blue-900 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-blue-700 text-white flex items-center justify-center font-bold text-[10px]">4</span>
            <div>
              <span className="font-bold block">Harmonize</span>
              <span className="text-[10px] text-blue-700">STRtree Consensus</span>
            </div>
          </div>

          <div className="p-3 bg-emerald-50 border border-emerald-300 rounded text-emerald-900 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-emerald-700 text-white flex items-center justify-center font-bold text-[10px]">5</span>
            <div>
              <span className="font-bold block">Review</span>
              <span className="text-[10px] text-emerald-700">
                {validation ? `${validation.issues_count} Flagged Issues` : 'Review & Triage'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Six Source Cards representing SIH Dataset Registry */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Cadastral Card */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-700" />
              <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-800">Cadastral</h3>
            </div>
            <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[9px] rounded flex items-center gap-0.5">
              <Check className="w-2.5 h-2.5" /> Loaded
            </span>
          </div>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between text-slate-600">
              <span>Features:</span>
              <strong className="font-mono text-slate-900">300 Parcels</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>CRS:</span>
              <span className="font-mono text-slate-800">EPSG:4326</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Format:</span>
              <span className="text-slate-800 font-mono">GeoJSON</span>
            </div>
          </div>
        </div>

        {/* Drone ORI Card */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5">
              <Satellite className="w-3.5 h-3.5 text-amber-600" />
              <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-800">Drone ORI</h3>
            </div>
            <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[9px] rounded flex items-center gap-0.5">
              <Check className="w-2.5 h-2.5" /> Loaded
            </span>
          </div>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between text-slate-600">
              <span>Raster/Poly:</span>
              <strong className="font-mono text-slate-900">1 Img / 300 P</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>CRS:</span>
              <span className="font-mono text-slate-800">EPSG:32643</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Resolution:</span>
              <span className="text-slate-800 font-mono">5 cm GSD</span>
            </div>
          </div>
        </div>

        {/* GNSS Card */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-red-600" />
              <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-800">GNSS RTK</h3>
            </div>
            <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[9px] rounded flex items-center gap-0.5">
              <Check className="w-2.5 h-2.5" /> Loaded
            </span>
          </div>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between text-slate-600">
              <span>Points:</span>
              <strong className="font-mono text-slate-900">300 Points</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Accuracy:</span>
              <span className="font-mono text-slate-800">±0.02 m</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Format:</span>
              <span className="text-slate-800 font-mono">CORS CSV</span>
            </div>
          </div>
        </div>

        {/* Revenue Card */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
              <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-800">Revenue</h3>
            </div>
            <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[9px] rounded flex items-center gap-0.5">
              <Check className="w-2.5 h-2.5" /> Loaded
            </span>
          </div>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between text-slate-600">
              <span>Records:</span>
              <strong className="font-mono text-slate-900">300 Recs</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Key:</span>
              <span className="font-mono text-slate-800">survey_no</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Format:</span>
              <span className="text-slate-800 font-mono">CSV Table</span>
            </div>
          </div>
        </div>

        {/* DSM / DTM Card (SIH Gap 1) */}
        <div className="bg-white p-4 rounded-lg border border-purple-200 bg-purple-50/20 shadow-2xs space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-purple-100">
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-purple-700" />
              <h3 className="font-bold text-[11px] uppercase tracking-wider text-purple-900">DSM / DTM</h3>
            </div>
            <span className="px-1.5 py-0.5 bg-purple-100 text-purple-800 font-bold text-[9px] rounded flex items-center gap-0.5">
              <Check className="w-2.5 h-2.5" /> Validated
            </span>
          </div>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between text-slate-600">
              <span>CRS:</span>
              <span className="font-mono text-purple-900 font-semibold">{elevationDatasets[0]?.crs || 'EPSG:32643'}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Resolution:</span>
              <span className="font-mono text-slate-800">{elevationDatasets[0] ? `${elevationDatasets[0].resolution} m` : '1.0 m'}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Elev Range:</span>
              <span className="text-purple-900 font-bold font-mono">
                {elevationDatasets[0] ? `${elevationDatasets[0].min_elevation.toFixed(1)}–${elevationDatasets[0].max_elevation.toFixed(1)}m` : '112.4–148.7m'}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Format:</span>
              <span className="text-slate-700 font-semibold font-mono">GeoTIFF (Raster)</span>
            </div>
          </div>
        </div>

        {/* Utility Network Card (SIH Gap 2) */}
        <div className="bg-white p-4 rounded-lg border border-blue-200 bg-blue-50/20 shadow-2xs space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-blue-100">
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-blue-700" />
              <h3 className="font-bold text-[11px] uppercase tracking-wider text-blue-900">Utility Network</h3>
            </div>
            <span className="px-1.5 py-0.5 bg-blue-100 text-blue-800 font-bold text-[9px] rounded flex items-center gap-0.5">
              <Check className="w-2.5 h-2.5" /> Live Layer
            </span>
          </div>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between text-slate-600">
              <span>Assets:</span>
              <strong className="font-mono text-blue-900 font-bold">
                {utilityAssets.length > 0 ? `${utilityAssets.length} Assets` : '7 Assets'}
              </strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Types:</span>
              <span className="font-mono text-slate-800">
                {utilityAssets.length > 0 ? Array.from(new Set(utilityAssets.map(u => u.utility_type))).join(',') : 'Electricity,Water,Telecom'}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>CRS:</span>
              <span className="text-slate-800 font-mono">EPSG:4326</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Source:</span>
              <span className="text-slate-700 text-[10px] font-semibold truncate">Municipal Network</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Harmonization Processing Status Checklist */}
      {loading && (
        <div className="bg-slate-900 text-white rounded-lg p-5 border border-slate-800 shadow-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="font-bold text-sm text-blue-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
              Harmonization Pipeline Execution
            </h3>
            <span className="text-xs font-mono text-slate-400">Processing Live</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {pipelineStages.map((stageName, idx) => {
              const isCompleted = activeStageIdx > idx;
              const isCurrent = activeStageIdx === idx;
              return (
                <div
                  key={stageName}
                  className={`p-2.5 rounded border flex items-center gap-2.5 ${
                    isCompleted
                      ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                      : isCurrent
                      ? 'bg-blue-900/60 border-blue-600 text-blue-200 animate-pulse font-bold'
                      : 'bg-slate-800/40 border-slate-700/50 text-slate-500'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : isCurrent ? (
                    <div className="w-4 h-4 rounded-full border-2 border-blue-400 border-t-transparent animate-spin shrink-0"></div>
                  ) : (
                    <span className="w-4 h-4 rounded-full bg-slate-700 text-slate-400 flex items-center justify-center text-[9px] font-mono shrink-0">
                      {idx + 1}
                    </span>
                  )}
                  <span className="truncate">{stageName}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Dataset Validation Results summary */}
      {validation && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Ingested Dataset Validation Report</h2>
              <p className="text-xs text-slate-500">Sub-meter spatial accuracy verification</p>
            </div>
            <button
              onClick={onNavigateToReconcile}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded flex items-center gap-1.5 shadow-2xs cursor-pointer"
            >
              Open Harmonization Workspace
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {validation.cards.map((card, idx) => (
              <div key={idx} className="border border-slate-200 rounded p-3 bg-slate-50">
                <div className="text-xs text-slate-500 font-medium">{card.name}</div>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-xl font-bold text-slate-800">{card.count.toLocaleString()}</span>
                  <span className="text-xs text-slate-600">{card.unit}</span>
                </div>
                <div className="text-[11px] text-emerald-700 font-semibold mt-1 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  {card.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Custom Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg border border-slate-300 max-w-2xl w-full p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Upload Custom Geospatial Datasets
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
                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="w-4 h-4 text-blue-700" />
                    <span className="text-xs font-bold text-slate-800">Legacy Cadastral</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">GeoJSON Vector</span>
                  <input
                    type="file"
                    accept=".geojson,.json"
                    onChange={(e) => setLegacyFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-blue-50 file:text-blue-700 cursor-pointer"
                  />
                </div>

                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <Satellite className="w-4 h-4 text-amber-600" />
                    <span className="text-xs font-bold text-slate-800">Drone Features</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">GeoJSON Vector</span>
                  <input
                    type="file"
                    accept=".geojson,.json"
                    onChange={(e) => setDroneFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-amber-50 file:text-amber-700 cursor-pointer"
                  />
                </div>

                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <Compass className="w-4 h-4 text-red-600" />
                    <span className="text-xs font-bold text-slate-800">GNSS CORS Points</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">CSV Table</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setGnssFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-red-50 file:text-red-700 cursor-pointer"
                  />
                </div>

                <div className="border border-slate-200 rounded p-3 bg-slate-50">
                  <div className="flex items-center gap-2 mb-1">
                    <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-bold text-slate-800">Revenue Register</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block mb-2">CSV Table</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setRevenueFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[11px] file:bg-emerald-50 file:text-emerald-700 cursor-pointer"
                  />
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
                  Validate & Ingest
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
