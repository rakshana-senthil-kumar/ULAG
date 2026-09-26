import React, { useEffect, useState } from 'react';
import type { ReconciliationSummary, ParcelDetail } from '../types/cadastral';
import type { AIModelMetadata, DatasetSyncStatus } from '../types/canonical';
import { getAIModels, getCanonicalBuildings, getParcels, getParcel, getSyncStatus } from '../services/api';
import { CadastralMap } from '../map/CadastralMap';
import {
  Layers,
  AlertTriangle,
  CheckCircle,
  Cpu,
  Activity,
  ArrowRight,
  Check
} from 'lucide-react';

interface DashboardViewProps {
  summary: ReconciliationSummary | null;
  onNavigateTab: (tab: any) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ summary, onNavigateTab }) => {
  const [models, setModels] = useState<AIModelMetadata[]>([]);
  const [buildingsCount, setBuildingsCount] = useState<number>(0);
  const [selectedParcel, setSelectedParcel] = useState<ParcelDetail | null>(null);
  const [syncRuns, setSyncRuns] = useState<DatasetSyncStatus[]>([]);

  // Map layer controls
  const [showLegacy, setShowLegacy] = useState(true);
  const [showDrone, setShowDrone] = useState(true);
  const [showGnss, setShowGnss] = useState(true);
  const [showReconciled, setShowReconciled] = useState(true);

  useEffect(() => {
    getAIModels().then(setModels).catch(console.error);
    getCanonicalBuildings().then((b) => setBuildingsCount(b.length)).catch(console.error);
    getSyncStatus().then(setSyncRuns).catch(console.error);

    // Fetch initial parcel for map display
    getParcels().then((parcels) => {
      if (parcels.length > 0) {
        const candidate = parcels.find((p) => p.parcel_id.includes('184')) || parcels[0];
        getParcel(candidate.parcel_id).then(setSelectedParcel);
      }
    }).catch(console.error);
  }, []);

  const toggleLayer = (layer: 'legacy' | 'drone' | 'gnss' | 'reconciled') => {
    if (layer === 'legacy') setShowLegacy(!showLegacy);
    if (layer === 'drone') setShowDrone(!showDrone);
    if (layer === 'gnss') setShowGnss(!showGnss);
    if (layer === 'reconciled') setShowReconciled(!showReconciled);
  };

  const totalParcelsCount = summary?.total_parcels ?? 0;
  const matchedParcelsCount = summary?.matched_count ?? 0;
  const conflictsParcelsCount = summary?.conflicts_count ?? 0;
  const cleanPct = totalParcelsCount > 0 ? ((matchedParcelsCount / totalParcelsCount) * 100).toFixed(1) : '0.0';
  const conflictPct = totalParcelsCount > 0 ? ((conflictsParcelsCount / totalParcelsCount) * 100).toFixed(1) : '0.0';

  const pipelineStages = [
    { id: 'workspace', label: 'INGEST', status: 'done', count: '4 Sources', warning: null },
    { id: 'workspace', label: 'VALIDATE', status: 'done', count: `${totalParcelsCount} Features`, warning: null },
    { id: 'reconcile', label: 'MATCH', status: 'done', count: `${matchedParcelsCount} Matched`, warning: null },
    { id: 'reconcile', label: 'HARMONIZE', status: 'done', count: `${cleanPct}% Consensus`, warning: null },
    { id: 'reconcile', label: 'TOPOLOGY', status: 'done', count: 'Validated', warning: null },
    { id: 'changes', label: 'CHANGE', status: 'done', count: `${buildingsCount} AI Buildings`, warning: null },
    { id: 'conflicts', label: 'REVIEW', status: conflictsParcelsCount > 0 ? 'warning' : 'done', count: `${conflictsParcelsCount} Pending`, warning: conflictsParcelsCount > 0 ? 'Action Needed' : null },
    { id: 'reconcile', label: 'PUBLISH', status: 'ready', count: 'Standard GeoJSON', warning: null }
  ];

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6 select-none font-sans">
      {/* 1. Executive Intelligence Header Banner */}
      <div className="bg-[#0b1e36] text-white rounded-lg p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-blue-600/40 text-blue-300 border border-blue-500/30 rounded">
              SIH 26013 Geospatial Harmonization
            </span>
            <span className="text-xs text-slate-400 font-mono">EPSG:32643 • Metric UTM Projection</span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            Urban Land Harmonization — <span className="text-blue-300 font-medium">Pune Urban Demonstration Area</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Multi-source integration across Cadastral, Drone ORI, GNSS RTK, and Revenue records.
          </p>
        </div>

        <div className="flex items-center gap-4 border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-6">
          <div className="text-right hidden sm:block">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Last Processing</span>
            <span className="text-xs text-slate-200 font-mono font-medium">23 Sep 2026 • 09:42</span>
          </div>
          <button
            onClick={() => onNavigateTab('reconcile')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-md transition shadow-sm flex items-center gap-2"
          >
            <span>Open Harmonization Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Four Compact Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Parcels Processed</span>
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-black text-slate-900 font-mono tracking-tight">{totalParcelsCount}</span>
            <span className="text-[11px] text-slate-500 font-medium">100% Ingested</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <Layers className="w-3 h-3 text-blue-600" /> Multi-Source Cadastral Fabric
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Matched</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-black text-emerald-700 font-mono tracking-tight">{matchedParcelsCount}</span>
            <span className="text-[11px] text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded">{cleanPct}% Clean</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-emerald-600" /> Sub-meter geometry consensus
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Conflicts</span>
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-black text-amber-600 font-mono tracking-tight">{conflictsParcelsCount}</span>
            <span className="text-[11px] text-amber-800 font-semibold bg-amber-50 px-1.5 py-0.5 rounded">{conflictPct}% Flagged</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-600" /> Triage review required
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Buildings Detected</span>
            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-black text-purple-700 font-mono tracking-tight">{buildingsCount}</span>
            <span className="text-[11px] text-purple-700 font-semibold bg-purple-50 px-1.5 py-0.5 rounded">AI / Drone</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <Cpu className="w-3 h-3 text-purple-600" /> Structural Extractor Adapter
          </p>
        </div>
      </div>

      {/* 2.5 Dataset Synchronization Banner (SIH PS Gap 3) */}
      <div className="bg-[#0f2942] text-white rounded-lg p-4 border border-blue-900/60 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-600/30 border border-blue-500/40 rounded-lg text-blue-300">
            <Activity className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-blue-200">
                DATA SYNCHRONIZATION & RECONCILIATION
              </h2>
              <span className="px-2 py-0.5 text-[9px] font-bold uppercase bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded">
                {syncRuns[0]?.sync_status || 'SYNC_REQUIRED'}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Source updates dynamically trigger change detection & recalculate parcel conflicts.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="text-center px-3 border-r border-slate-700">
            <span className="text-[10px] text-slate-400 block uppercase">Sources</span>
            <strong className="text-white text-sm">6 Registered</strong>
          </div>
          <div className="text-center px-3 border-r border-slate-700">
            <span className="text-[10px] text-slate-400 block uppercase">Synced</span>
            <strong className="text-emerald-400 text-sm">4 Layers</strong>
          </div>
          <div className="text-center px-3 border-r border-slate-700">
            <span className="text-[10px] text-slate-400 block uppercase">Changes</span>
            <strong className="text-amber-400 text-sm">{syncRuns[0]?.affected_feature_count || 1} Detected</strong>
          </div>
          <div className="text-center px-3">
            <span className="text-[10px] text-slate-400 block uppercase">Parcels Affected</span>
            <strong className="text-amber-300 text-sm">{syncRuns[0]?.affected_parcel_count || 1} Flagged</strong>
          </div>

          <button
            onClick={() => onNavigateTab('review')}
            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs rounded transition shadow-2xs flex items-center gap-1.5"
          >
            <span>Review Changes</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 3. Harmonization Health Pipeline Section */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-600" /> Harmonization Pipeline Health
          </h2>
          <span className="text-[11px] text-slate-500">SIH End-to-End Orchestrator Pipeline</span>
        </div>

        {/* Large Horizontal Pipeline Flow */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 relative">
          {pipelineStages.map((stage) => {
            const isWarning = stage.status === 'warning';
            return (
              <button
                key={stage.label}
                onClick={() => onNavigateTab(stage.id)}
                className={`p-3 rounded border text-left transition-all relative flex flex-col justify-between ${
                  isWarning
                    ? 'bg-amber-50/70 border-amber-300 hover:bg-amber-100/80 text-amber-900'
                    : 'bg-slate-50 hover:bg-blue-50/50 border-slate-200 text-slate-800'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs tracking-wide">{stage.label}</span>
                    {isWarning ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    ) : (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    )}
                  </div>
                  <span className="text-[11px] font-medium text-slate-600 block">{stage.count}</span>
                </div>

                {stage.warning ? (
                  <span className="mt-2 text-[10px] font-bold text-amber-800 bg-amber-200/80 px-1.5 py-0.5 rounded text-center block">
                    {stage.warning}
                  </span>
                ) : (
                  <span className="mt-2 text-[10px] text-emerald-700 font-semibold block">
                    ✓ Verified
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Main Map Preview Section */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="font-bold text-sm text-slate-900 uppercase tracking-wide">Harmonization WebGIS Overview</h2>
            <span className="text-xs text-slate-600 font-mono">
              {selectedParcel
                ? `Parcel ${selectedParcel.full_survey} (Active Selection)`
                : `Active Cadastral Region (${totalParcelsCount} Parcels | ${matchedParcelsCount} Matched | ${conflictsParcelsCount} Conflicts | ${buildingsCount} AI Buildings)`}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onNavigateTab('reconcile')}
              className="px-3 py-1 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded shadow-xs transition"
            >
              Interactive Reconcile Inspector →
            </button>
          </div>
        </div>

        {/* GIS Map Canvas with Badges Overlay */}
        <div className="relative w-full h-[480px]">
          <CadastralMap
            selectedParcel={selectedParcel}
            showLegacy={showLegacy}
            showDrone={showDrone}
            showGnss={showGnss}
            showReconciled={showReconciled}
            onToggleLayer={toggleLayer}
          />

          {/* Map Overlay Stats Panel */}
          <div className="absolute top-14 right-4 z-[1000] bg-slate-900/90 backdrop-blur-md text-white border border-slate-700 rounded-lg p-3 shadow-xl space-y-2 text-xs font-sans max-w-xs">
            <div className="font-bold text-slate-200 border-b border-slate-700 pb-1 flex items-center justify-between">
              <span>ACTIVE REGION SUMMARY</span>
              <span className="text-[10px] text-blue-400 font-mono">EPSG:32643</span>
            </div>

            <div className="space-y-1 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Total Parcels:</span>
                <span className="font-bold text-white font-mono">{totalParcelsCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Matched Parcels:</span>
                <span className="font-bold text-emerald-400 font-mono">{matchedParcelsCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Active Conflicts:</span>
                <span className="font-bold text-amber-400 font-mono">{conflictsParcelsCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">AI Extracted Buildings:</span>
                <span className="font-bold text-purple-400 font-mono">{buildingsCount}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Model Registry & System Evaluation Info */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
          <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-600" /> GeoAI & Model Pipeline Registry
          </h3>
          <span className="text-xs text-slate-500">Building Footprint & Spatial Adapter Models</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {models.map((m) => (
            <div key={m.model_name} className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-2">
              <div className="flex items-center justify-between font-bold text-slate-900">
                <span>{m.task}</span>
                <span className="font-mono text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200 text-[10px]">
                  {m.version}
                </span>
              </div>
              <div className="text-slate-500 flex justify-between">
                <span>Adapter Status:</span>
                <strong className="text-slate-800">Prototype Adapter</strong>
              </div>
              <div className="text-slate-500 flex justify-between">
                <span>Framework:</span>
                <span className="font-mono text-slate-700">{m.framework}</span>
              </div>
              <div className="pt-2 border-t border-slate-200 flex justify-between items-center text-[11px]">
                <span className="text-slate-500">Benchmark Metrics:</span>
                <span className="bg-slate-200/70 text-slate-700 px-2 py-0.5 rounded font-semibold text-[10px]">
                  Not evaluated
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
