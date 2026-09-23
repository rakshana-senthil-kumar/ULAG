import React from 'react';
import type { ProvenanceRecord } from '../types/canonical';
import { GitCommit } from 'lucide-react';

interface ProvenancePanelProps {
  provenance: ProvenanceRecord | null;
  onClose?: () => void;
}

export const ProvenancePanel: React.FC<ProvenancePanelProps> = ({ provenance, onClose }) => {
  if (!provenance) {
    return (
      <div className="p-4 bg-slate-50 border border-slate-200 rounded text-slate-500 text-xs text-center font-sans">
        Select a feature to inspect full data lineage & provenance timeline.
      </div>
    );
  }

  const timelineSteps = [
    { title: 'Source Ingested', detail: provenance.source_type || 'Legacy Cadastral GeoJSON Master', color: 'bg-blue-600' },
    { title: 'CRS Transformed', detail: `EPSG:4326 → ${provenance.crs_used || 'EPSG:32643 Metric UTM'}`, color: 'bg-blue-600' },
    { title: 'Spatially Indexed', detail: `STRtree Index (${provenance.matching_method || 'STRtree R-Tree Matching'})`, color: 'bg-blue-600' },
    { title: 'Change Detected', detail: 'SHA-256 Fingerprint Delta (Revenue Register Update v2)', color: 'bg-amber-500' },
    { title: 'Parcel Affected', detail: `Parcel ${provenance.feature_id} Flagged as SYNC_REQUIRED`, color: 'bg-amber-600' },
    { title: 'Conflict Recalculated', detail: 'Evidence Scores & Multi-Source Discrepancies Updated', color: 'bg-amber-500' },
    { title: 'Officer Reviewed', detail: provenance.reviewer ? `Adjudicated & Signed by ${provenance.reviewer}` : 'Adjudicated by District Land Officer', color: 'bg-emerald-600' },
    { title: 'Approved', detail: provenance.reconciliation_decision || 'APPROVED — Reconciled Candidate Accepted', color: 'bg-emerald-600' },
    { title: 'Dataset Published', detail: 'Harmonized Dataset Version v5 Published', color: 'bg-purple-600' }
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-2xs p-5 text-slate-800 select-none font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-4">
        <div className="flex items-center gap-2">
          <GitCommit className="w-4 h-4 text-blue-600" />
          <h3 className="font-bold text-sm text-slate-900 uppercase tracking-wide">FEATURE PROVENANCE & LINEAGE</h3>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xs font-bold">
            ✕
          </button>
        )}
      </div>

      {/* Feature ID Badge */}
      <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded border border-slate-200 mb-4 text-xs font-mono">
        <div>
          <span className="text-slate-400 block text-[10px] font-sans font-bold uppercase">Target Feature</span>
          <span className="font-bold text-blue-900 text-sm">Parcel {provenance.feature_id}</span>
        </div>
        <div className="text-right">
          <span className="text-slate-400 block text-[10px] font-sans font-bold uppercase">Primary Source</span>
          <span className="font-semibold text-slate-700">{provenance.source_dataset}</span>
        </div>
      </div>

      {/* Vertical Provenance Lineage Timeline */}
      <div className="space-y-4 relative pl-5 text-xs">
        {timelineSteps.map((step, idx) => (
          <div key={step.title} className="relative">
            {/* Connecting Line */}
            {idx < timelineSteps.length - 1 && (
              <span className="absolute left-[-15px] top-3 bottom-[-16px] w-[2px] bg-slate-200" />
            )}
            
            {/* Dot indicator */}
            <span className={`absolute left-[-19px] top-1 w-2.5 h-2.5 rounded-full ${step.color} ring-4 ring-white`} />

            <div>
              <span className="font-bold text-slate-900 block">{step.title}</span>
              <span className="text-slate-600 text-[11px] font-mono block mt-0.5">{step.detail}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
