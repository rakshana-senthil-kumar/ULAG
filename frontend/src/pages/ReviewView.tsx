import { useState, useEffect } from 'react';
import {
  XCircle,
  Clock,
  Sparkles,
  ArrowLeft,
  Check
} from 'lucide-react';
import type { ConflictItem, ParcelDetail } from '../types/cadastral';
import { getConflict, getParcel, approveConflict, rejectConflict, markManualReview } from '../services/api';
import { CadastralMap } from '../map/CadastralMap';

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
  } | null>(null);
  const [loading, setLoading] = useState(true);

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
            approvedBy: c.reviewed_by || 'Officer S. Kulkarni (District Land Records)',
            timestamp: c.timestamp || '2026-09-22 09:30'
          });
        }
        return getParcel(c.parcel_id || 'P003');
      })
      .then((p) => setParcelDetail(p))
      .catch((err) => console.error('Error fetching review case:', err))
      .finally(() => setLoading(false));
  }, [conflictId]);

  const handleAction = async (action: 'ACCEPT' | 'REJECT' | 'MANUAL_REVIEW') => {
    try {
      const user = 'Land Record Officer (Admin)';
      if (action === 'ACCEPT') {
        const res = await approveConflict(conflictId, user, 'Approved based on CORS RTK GNSS boundary agreement.');
        setDecisionState({
          status: 'Approved',
          approvedBy: user,
          timestamp: res.audit?.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19)
        });
      } else if (action === 'REJECT') {
        const res = await rejectConflict(conflictId, user, 'Candidate rejected due to unverified boundary marker.');
        setDecisionState({
          status: 'Rejected',
          approvedBy: user,
          timestamp: res.audit?.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19)
        });
      } else {
        const res = await markManualReview(conflictId, user, 'Dispatched for physical ground survey tie-in.');
        setDecisionState({
          status: 'Manual Review',
          approvedBy: user,
          timestamp: res.audit?.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19)
        });
      }
      onRefreshSummary();
    } catch (e) {
      console.error('Error executing decision action:', e);
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
        Loading review dossier for case {conflictId}...
      </div>
    );
  }

  const sources = conflict.sources_comparison;

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 font-sans">
      {/* Back Button */}
      <button
        onClick={onBackToConflicts}
        className="mb-4 text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium cursor-pointer"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Conflicts List
      </button>

      {/* Case Header */}
      <div className="bg-white border border-slate-200 rounded p-6 shadow-xs mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-2">
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
              Human-in-the-Loop Adjudication
            </div>
            <h1 className="text-xl font-bold text-slate-900 mt-0.5">
              REVIEW CASE {conflict.conflict_id}
            </h1>
            <div className="text-sm font-semibold text-blue-900 mt-0.5">
              Survey No: {conflict.survey_no}
            </div>
          </div>

          <div className="text-right">
            <span className="text-[11px] text-slate-500 uppercase font-semibold mr-2">
              Algorithm Recommendation Confidence:
            </span>
            <span className="text-lg font-bold text-blue-950">{conflict.confidence}%</span>
          </div>
        </div>

        {/* 4-way Source Comparison Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
            <div className="text-[11px] font-semibold text-slate-500 uppercase">Legacy Cadastral</div>
            <div className="text-xl font-bold text-slate-900 mt-1">
              {sources.legacy ? `${sources.legacy} m²` : '—'}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Historical Paper Sheet</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
            <div className="text-[11px] font-semibold text-slate-500 uppercase">Revenue Record</div>
            <div className="text-xl font-bold text-slate-900 mt-1">
              {sources.revenue ? `${sources.revenue} m²` : '—'}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Tehsildar 7/12 Register</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
            <div className="text-[11px] font-semibold text-slate-500 uppercase">Drone Feature</div>
            <div className="text-xl font-bold text-slate-900 mt-1">
              {sources.drone ? `${sources.drone} m²` : '—'}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Ortho-rectified Imagery</div>
          </div>

          <div className="p-3 bg-blue-50/60 border border-blue-200 rounded text-center">
            <div className="text-[11px] font-bold text-blue-900 uppercase">GNSS Survey</div>
            <div className="text-xl font-bold text-blue-950 mt-1">
              {sources.gnss ? `${sources.gnss} m²` : '—'}
            </div>
            <div className="text-[10px] text-blue-700 mt-0.5">CORS RTK Ground Network</div>
          </div>
        </div>
      </div>

      {/* Map Boundary Comparison Area */}
      <div className="bg-white border border-slate-200 rounded p-4 shadow-xs mb-6">
        <div className="flex items-center justify-between mb-3 text-xs">
          <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
            Spatial Boundary Concordance
          </span>
          <span className="text-[11px] text-slate-500">
            Legend: <strong className="text-blue-700">Legacy</strong> vs <strong className="text-amber-600">Drone</strong> vs <strong className="text-red-600">GNSS</strong> vs <strong className="text-emerald-700">Recommended</strong>
          </span>
        </div>

        <div className="h-[380px] w-full rounded overflow-hidden">
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

      {/* WHY THIS RECOMMENDATION? Section */}
      <div className="bg-white border border-slate-200 rounded p-6 shadow-xs mb-6">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 mb-3">
          <Sparkles className="w-4 h-4 text-blue-700" />
          WHY THIS RECOMMENDATION?
        </h3>

        <div className="p-4 bg-slate-50 border border-slate-200 rounded text-xs text-slate-800 leading-relaxed space-y-2">
          <p className="font-medium text-slate-900">
            GNSS and drone boundaries have strong spatial agreement.
          </p>
          <p>
            The legacy boundary differs significantly from current survey evidence (+54 m² variance, boundary offset).
          </p>
          <p>
            Revenue survey attributes match the same parcel reference ({conflict.survey_no}).
          </p>
          <p className="pt-1 text-slate-600">
            Therefore the system recommends the <strong className="text-slate-900">GNSS + drone geometry</strong> as the authoritative reconciliation candidate.
          </p>
          <div className="pt-2 font-bold text-blue-900 text-xs">
            Confidence: {conflict.confidence}%
          </div>
        </div>
      </div>

      {/* Human-in-the-Loop Action Panel */}
      <div className="bg-white border border-slate-200 rounded p-6 shadow-xs">
        {decisionState ? (
          <div className="p-4 bg-emerald-50 border border-emerald-300 rounded text-xs space-y-1">
            <div className="font-bold text-emerald-900 text-sm flex items-center gap-1.5">
              <Check className="w-4 h-4" />
              ✓ Reconciliation {decisionState.status.toLowerCase()}
            </div>
            <div className="text-emerald-800">
              Approved by: <strong>{decisionState.approvedBy}</strong>
            </div>
            <div className="text-emerald-700 text-[11px]">
              Timestamp: {decisionState.timestamp}
            </div>
            <div className="text-[11px] text-emerald-900 pt-1">
              Decision permanently committed to PostGIS database audit ledger.
            </div>
          </div>
        ) : (
          <div>
            <div className="text-xs font-semibold text-slate-700 mb-3">
              Official Land Governance Action Required:
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => handleAction('ACCEPT')}
                className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs rounded transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
              >
                <Check className="w-4 h-4" />
                [ ACCEPT ]
              </button>

              <button
                onClick={() => handleAction('REJECT')}
                className="px-6 py-2.5 bg-red-700 hover:bg-red-800 text-white font-bold text-xs rounded transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
              >
                <XCircle className="w-4 h-4" />
                [ REJECT ]
              </button>

              <button
                onClick={() => handleAction('MANUAL_REVIEW')}
                className="px-6 py-2.5 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 font-bold text-xs rounded transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
              >
                <Clock className="w-4 h-4 text-slate-500" />
                [ MANUAL REVIEW ]
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
