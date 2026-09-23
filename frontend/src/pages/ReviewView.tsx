import React, { useState, useEffect } from 'react';
import {
  XCircle,
  Clock,
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  GitMerge,
  ShieldCheck,
  Check
} from 'lucide-react';
import type { ConflictItem, ParcelDetail } from '../types/cadastral';
import { getConflict, getParcel, approveConflict, rejectConflict, markManualReview, approveSyncReconciliation } from '../services/api';
import { CadastralMap } from '../map/CadastralMap';
import { ConfirmationModal } from '../components/ConfirmationModal';

interface ReviewViewProps {
  conflictId: string;
  onBackToConflicts: () => void;
  onRefreshSummary: () => void;
}

export const ReviewView: React.FC<ReviewViewProps> = ({
  conflictId = 'C-001',
  onBackToConflicts,
  onRefreshSummary
}) => {
  const [conflict, setConflict] = useState<ConflictItem | null>(null);
  const [parcelDetail, setParcelDetail] = useState<ParcelDetail | null>(null);
  const [decisionState, setDecisionState] = useState<{
    status: string;
    approvedBy?: string;
    timestamp?: string;
    comment?: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  // Confirmation Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState<{ action: string; label: string } | null>(null);

  // Layer toggles
  const [showLegacy, setShowLegacy] = useState(true);
  const [showDrone, setShowDrone] = useState(true);
  const [showGnss, setShowGnss] = useState(true);
  const [showReconciled, setShowReconciled] = useState(true);

  useEffect(() => {
    setLoading(true);
    getConflict(conflictId)
      .then((c) => {
        setConflict(c);
        if (c.status === 'Approved' || c.status === 'Rejected' || c.status === 'Manual Review') {
          setDecisionState({
            status: c.status,
            approvedBy: c.reviewed_by || 'REVIEW OFFICER',
            timestamp: c.timestamp || '2026-09-23 09:42',
            comment: 'Approved based on CORS RTK GNSS boundary agreement.'
          });
        }
        return getParcel(c.parcel_id || '184/2');
      })
      .then((p) => setParcelDetail(p))
      .catch((err) => console.error('Error fetching review case:', err))
      .finally(() => setLoading(false));
  }, [conflictId]);

  const triggerActionModal = (action: string, label: string) => {
    setSelectedAction({ action, label });
    setModalOpen(true);
  };

  const handleConfirmDecision = async (comment: string) => {
    if (!selectedAction) return;
    try {
      const user = 'Land Record Officer (Admin)';
      if (selectedAction.action === 'SYNC_APPROVE') {
        const res = await approveSyncReconciliation('DS-Revenue', user, comment);
        setDecisionState({
          status: 'Approved (Harmonized Dataset Version v5 Created)',
          approvedBy: user,
          timestamp: res.sync_status?.approved_at || new Date().toISOString().replace('T', ' ').slice(0, 19),
          comment
        });
      } else if (selectedAction.action === 'ACCEPT' || selectedAction.action === 'MERGE' || selectedAction.action === 'SOURCE') {
        const res = await approveConflict(conflictId, user, comment);
        setDecisionState({
          status: 'Approved',
          approvedBy: user,
          timestamp: res.audit?.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19),
          comment
        });
      } else if (selectedAction.action === 'REJECT') {
        const res = await rejectConflict(conflictId, user, comment);
        setDecisionState({
          status: 'Rejected',
          approvedBy: user,
          timestamp: res.audit?.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19),
          comment
        });
      } else {
        const res = await markManualReview(conflictId, user, comment);
        setDecisionState({
          status: 'Manual Review',
          approvedBy: user,
          timestamp: res.audit?.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19),
          comment
        });
      }
      onRefreshSummary();
    } catch (e) {
      console.error('Error executing decision action:', e);
    } finally {
      setModalOpen(false);
      setSelectedAction(null);
    }
  };

  const handleToggleLayer = (layer: 'legacy' | 'drone' | 'gnss' | 'reconciled') => {
    if (layer === 'legacy') setShowLegacy(!showLegacy);
    if (layer === 'drone') setShowDrone(!showDrone);
    if (layer === 'gnss') setShowGnss(!showGnss);
    if (layer === 'reconciled') setShowReconciled(!showReconciled);
  };

  if (loading || !conflict) {
    return (
      <div className="p-12 text-center text-xs text-slate-500">
        Loading officer review dossier for {conflictId}...
      </div>
    );
  }

  const sources = conflict.sources_comparison;

  return (
    <div className="max-w-[1400px] mx-auto py-6 px-6 font-sans select-none space-y-6">
      {/* Top Breadcrumb Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <button
          onClick={onBackToConflicts}
          className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-semibold cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Conflict Center Triage
        </button>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-500 font-bold uppercase tracking-wider">Officer Workstation</span>
          <span className="px-2.5 py-1 bg-[#0b1e36] text-white text-[11px] font-bold rounded flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            GOVERNMENT OFFICER REVIEW
          </span>
        </div>
      </div>

      {/* 1. Header Box */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-blue-900 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                {conflict.conflict_id}
              </span>
              <span className="text-xs font-bold text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                High Severity
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-1">
              REVIEW DECISION — Parcel {conflict.parcel_id}
            </h1>
            <span className="text-xs text-slate-600 font-mono">Survey No: {conflict.survey_no}</span>
          </div>

          <div className="text-right">
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
              Confidence Score
            </span>
            <span className="text-2xl font-black text-blue-900 font-mono">{conflict.confidence}%</span>
          </div>
        </div>

        {/* 2. Source Evidence Comparison Table */}
        <div className="space-y-2">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">SOURCE EVIDENCE</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center space-y-1">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">Legacy Cadastral</span>
              <span className="text-lg font-bold font-mono text-slate-900">
                {sources.legacy ? `${sources.legacy} m²` : '1487 m²'}
              </span>
              <div className="w-full h-1 bg-blue-500/30 rounded-full"></div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center space-y-1">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">Revenue Register</span>
              <span className="text-lg font-bold font-mono text-slate-900">
                {sources.revenue ? `${sources.revenue} m²` : '1520 m²'}
              </span>
              <div className="w-full h-1 bg-emerald-500/30 rounded-full"></div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center space-y-1">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">Drone ORI Extent</span>
              <span className="text-lg font-bold font-mono text-amber-900">
                {sources.drone ? `${sources.drone} m²` : '1541 m²'}
              </span>
              <div className="w-full h-1 bg-amber-500 rounded-full"></div>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-center space-y-1">
              <span className="text-[10px] text-blue-900 font-bold uppercase block">GNSS CORS RTK</span>
              <span className="text-lg font-bold font-mono text-blue-950">
                {sources.gnss ? `${sources.gnss} m²` : '1535 m²'}
              </span>
              <div className="w-full h-1 bg-blue-700 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Geometry Comparison Map & System Recommendation (Side-by-side) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Geometry Comparison Map (2 Cols) */}
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-lg p-4 shadow-2xs space-y-3">
          <div className="flex items-center justify-between text-xs">
            <h2 className="font-bold text-slate-800 uppercase tracking-wider">GEOMETRY COMPARISON MAP</h2>
            <span className="text-[11px] text-slate-500">
              Layers: <strong className="text-blue-700">Legacy</strong> • <strong className="text-amber-600">Drone</strong> • <strong className="text-red-600">GNSS</strong> • <strong className="text-emerald-700">Harmonized</strong>
            </span>
          </div>

          <div className="h-[420px] w-full rounded-lg overflow-hidden border border-slate-200">
            <CadastralMap
              selectedParcel={parcelDetail}
              showLegacy={showLegacy}
              showDrone={showDrone}
              showGnss={showGnss}
              showReconciled={showReconciled}
              onToggleLayer={handleToggleLayer}
              standalone={true}
            />
          </div>
        </div>

        {/* System Recommendation & Evidence (1 Col) */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-4 flex flex-col justify-between">
          <div>
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-blue-600" /> SYSTEM RECOMMENDATION
            </h2>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2 text-xs">
              <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider block">Recommended Resolution</span>
              <h3 className="font-bold text-slate-900 text-sm">GNSS + Drone Geometry</h3>
              <div className="flex justify-between items-center text-slate-700 font-medium">
                <span>Confidence:</span>
                <strong className="text-blue-900 font-mono text-sm">{conflict.confidence}%</strong>
              </div>

              <div className="pt-2 border-t border-blue-200/80 text-[11px] text-slate-700 space-y-1">
                <span className="font-bold text-slate-900 block">Reasoning:</span>
                <p className="leading-relaxed">
                  Highest geometric agreement with CORS RTK survey (±0.02m accuracy) and current high-resolution ORI drone evidence.
                </p>
              </div>
            </div>
          </div>

          {/* Audit Status */}
          {decisionState && (
            <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-lg text-xs space-y-1">
              <div className="font-bold text-emerald-900 flex items-center gap-1.5">
                <Check className="w-4 h-4 text-emerald-600" />
                ✓ Decision Confirmed ({decisionState.status})
              </div>
              <div className="text-[11px] text-emerald-800">
                Officer: <strong>{decisionState.approvedBy}</strong>
              </div>
              <div className="text-[10px] text-emerald-700 font-mono">
                {decisionState.timestamp}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 4. Officer Decision Actions */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-3">
        <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">OFFICER DECISION ACTION</h2>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => triggerActionModal('ACCEPT', 'Accept Recommendation (GNSS + Drone)')}
            className="px-5 py-2.5 bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs rounded transition-colors shadow-xs flex items-center gap-2 cursor-pointer"
          >
            <CheckCircle2 className="w-4 h-4" />
            Accept Recommendation
          </button>

          <button
            onClick={() => triggerActionModal('SOURCE', 'Accept Specific Source Geometry')}
            className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 font-semibold text-xs rounded transition-colors cursor-pointer"
          >
            Accept Source
          </button>

          <button
            onClick={() => triggerActionModal('MERGE', 'Merge Geometry Boundaries')}
            className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 font-semibold text-xs rounded transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <GitMerge className="w-4 h-4 text-blue-600" />
            Merge Boundaries
          </button>

          <button
            onClick={() => triggerActionModal('MANUAL_REVIEW', 'Flag for Manual Field Survey')}
            className="px-4 py-2.5 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 font-semibold text-xs rounded transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <Clock className="w-4 h-4 text-amber-600" />
            Manual Review
          </button>

          <button
            onClick={() => triggerActionModal('REJECT', 'Reject Candidate')}
            className="px-4 py-2.5 bg-white hover:bg-red-50 text-red-700 border border-red-300 font-semibold text-xs rounded transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <XCircle className="w-4 h-4 text-red-600" />
            Reject
          </button>

          <button
            onClick={() => triggerActionModal('SYNC_APPROVE', 'Approve Dataset Synchronization & Create Version v5')}
            className="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs rounded transition-colors flex items-center gap-1.5 shadow-xs cursor-pointer ml-auto"
          >
            <ShieldCheck className="w-4 h-4 text-white" />
            Approve Sync & Create Version v5
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {selectedAction && (
        <ConfirmationModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onConfirm={handleConfirmDecision}
          title={selectedAction.label}
          actionName={selectedAction.action}
          targetId={`Parcel ${conflict.parcel_id} (${conflict.conflict_id})`}
        />
      )}
    </div>
  );
};
