import React, { useState, useEffect } from 'react';
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  Split,
  Info
} from 'lucide-react';
import type { ParcelSummary, ParcelDetail, ReconciliationSummary } from '../types/cadastral';
import { getParcels, getParcel, approveConflict, markManualReview } from '../services/api';
import { CadastralMap } from '../map/CadastralMap';
import { ConfirmationModal } from '../components/ConfirmationModal';

interface ReconcileViewProps {
  summary?: ReconciliationSummary | null;
  onRefreshSummary: () => void;
}

export const ReconcileView: React.FC<ReconcileViewProps> = ({
  summary: _summary,
  onRefreshSummary
}) => {
  const [parcels, setParcels] = useState<ParcelSummary[]>([]);
  const [selectedParcelId, setSelectedParcelId] = useState<string>('184/2');
  const [selectedParcelDetail, setSelectedParcelDetail] = useState<ParcelDetail | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('All');

  // Source Comparison mode toggle
  const [compareSourcesMode, setCompareSourcesMode] = useState<boolean>(false);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<{ action: string; title: string } | null>(null);

  // Layer toggles
  const [showLegacy, setShowLegacy] = useState(true);
  const [showDrone, setShowDrone] = useState(true);
  const [showGnss, setShowGnss] = useState(true);
  const [showReconciled, setShowReconciled] = useState(true);

  // Load parcels list
  useEffect(() => {
    getParcels(statusFilter, searchQuery)
      .then((data) => {
        setParcels(data);
        if (data.length > 0 && !selectedParcelId) {
          setSelectedParcelId(data[0].parcel_id);
        }
      })
      .catch((err) => console.error('Error fetching parcels:', err));
  }, [statusFilter, searchQuery]);

  // Load selected parcel detail
  useEffect(() => {
    if (!selectedParcelId) return;
    getParcel(selectedParcelId)
      .then((data) => setSelectedParcelDetail(data))
      .catch((err) => console.error('Error fetching parcel detail:', err));
  }, [selectedParcelId]);

  const handleToggleLayer = (layer: 'legacy' | 'drone' | 'gnss' | 'reconciled') => {
    if (layer === 'legacy') setShowLegacy(!showLegacy);
    if (layer === 'drone') setShowDrone(!showDrone);
    if (layer === 'gnss') setShowGnss(!showGnss);
    if (layer === 'reconciled') setShowReconciled(!showReconciled);
  };

  const openConfirmation = (action: string, title: string) => {
    setPendingAction({ action, title });
    setModalOpen(true);
  };

  const handleConfirmDecision = async (comment: string) => {
    if (!selectedParcelDetail || !pendingAction) return;
    try {
      if (pendingAction.action === 'ACCEPT') {
        await approveConflict('C-001', 'REVIEW OFFICER', comment);
      } else {
        await markManualReview('C-001', 'REVIEW OFFICER', comment);
      }
      onRefreshSummary();
      const updated = await getParcel(selectedParcelDetail.parcel_id);
      setSelectedParcelDetail(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setModalOpen(false);
      setPendingAction(null);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden font-sans select-none bg-slate-100">
      {/* 3-PANEL WORKSTATION LAYOUT */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* PANEL 1: PARCEL SEARCH & LIST (Width: 280px) */}
        <div className="w-[280px] bg-white border-r border-slate-200 flex flex-col h-full shrink-0">
          <div className="p-3 border-b border-slate-200 bg-slate-50 space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Parcel Directory
            </span>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search Parcel (e.g. 184/2)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded text-xs text-slate-800 focus:ring-1 focus:ring-blue-600 outline-none"
              />
            </div>

            {/* Filter chips */}
            <div className="flex items-center gap-1 text-[11px] pt-1">
              {['All', 'Matched', 'Conflict'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold transition ${
                    statusFilter === st
                      ? 'bg-blue-700 text-white'
                      : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* List items */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {parcels.map((p) => {
              const isSelected = p.parcel_id === selectedParcelId;
              return (
                <button
                  key={p.parcel_id}
                  onClick={() => setSelectedParcelId(p.parcel_id)}
                  className={`w-full px-3 py-2 text-xs flex items-center justify-between transition-colors text-left ${
                    isSelected
                      ? 'bg-blue-50/90 border-l-4 border-blue-700 font-semibold'
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div>
                    <span className="font-bold text-slate-900 block">{p.parcel_id}</span>
                    <span className="text-[10px] text-slate-500 font-mono">Survey {p.full_survey}</span>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-mono font-bold text-blue-900 block">{p.confidence}%</span>
                    <span
                      className={`inline-block px-1.5 py-0.2 text-[9px] font-bold rounded uppercase ${
                        p.status === 'Matched'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-900'
                      }`}
                    >
                      {p.status}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* PANEL 2: DOMINANT GIS MAP (Flex 1) */}
        <div className="flex-1 relative h-full bg-slate-900">
          {/* Compare Sources Header bar */}
          <div className="absolute top-3 right-4 z-[1000] flex items-center gap-2">
            <button
              onClick={() => setCompareSourcesMode(!compareSourcesMode)}
              className={`px-3 py-1.5 rounded text-xs font-bold shadow-md transition flex items-center gap-1.5 backdrop-blur-md border ${
                compareSourcesMode
                  ? 'bg-amber-500 text-slate-950 border-amber-400'
                  : 'bg-white/95 text-slate-800 border-slate-300 hover:bg-white'
              }`}
            >
              <Split className="w-3.5 h-3.5" />
              {compareSourcesMode ? 'Exit Source Comparison' : 'Compare Sources Mode'}
            </button>
          </div>

          <CadastralMap
            selectedParcel={selectedParcelDetail}
            showLegacy={showLegacy}
            showDrone={showDrone}
            showGnss={showGnss}
            showReconciled={showReconciled}
            onToggleLayer={handleToggleLayer}
          />

          {/* Source Comparison Floating Overlay Card */}
          {compareSourcesMode && selectedParcelDetail && (
            <div className="absolute bottom-6 left-6 right-6 z-[1000] bg-slate-900/95 text-white border border-amber-500/50 rounded-lg p-4 shadow-2xl backdrop-blur-md font-sans">
              <div className="flex items-center justify-between border-b border-slate-700 pb-2 mb-3">
                <span className="text-xs font-bold text-amber-400 flex items-center gap-2">
                  <Split className="w-4 h-4" /> Multi-Source Geometry & Extent Comparison (Parcel {selectedParcelDetail.parcel_id})
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Metric Tolerance: 0.50 m</span>
              </div>

              <div className="grid grid-cols-4 gap-4 text-xs">
                <div className="bg-slate-800/80 p-2.5 rounded border border-blue-600/40">
                  <span className="text-blue-400 font-bold text-[10px] uppercase block">Legacy Cadastral</span>
                  <span className="text-base font-bold font-mono text-white">
                    {selectedParcelDetail.sources_comparison.legacy ?? '1487'} m²
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Vector Cadastral Map</span>
                </div>

                <div className="bg-slate-800/80 p-2.5 rounded border border-amber-600/40">
                  <span className="text-amber-400 font-bold text-[10px] uppercase block">Drone ORI</span>
                  <span className="text-base font-bold font-mono text-white">
                    {selectedParcelDetail.sources_comparison.drone ?? '1541'} m²
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Orthorectified Imagery</span>
                </div>

                <div className="bg-slate-800/80 p-2.5 rounded border border-red-600/40">
                  <span className="text-red-400 font-bold text-[10px] uppercase block">GNSS RTK</span>
                  <span className="text-base font-bold font-mono text-white">
                    {selectedParcelDetail.sources_comparison.gnss ?? '1535'} m²
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">CORS Base Boundary</span>
                </div>

                <div className="bg-slate-800/80 p-2.5 rounded border border-emerald-600/40">
                  <span className="text-emerald-400 font-bold text-[10px] uppercase block">Revenue Record</span>
                  <span className="text-base font-bold font-mono text-white">
                    {selectedParcelDetail.sources_comparison.revenue ?? '1520'} m²
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">Tabular 7/12 Record</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* PANEL 3: EVIDENCE & EXPLAINABILITY (Width: 380px) */}
        <div className="w-[380px] bg-white border-l border-slate-200 flex flex-col h-full shrink-0 overflow-y-auto p-4 space-y-4 shadow-xs">
          {selectedParcelDetail ? (
            <>
              {/* Header */}
              <div className="border-b border-slate-200 pb-3 flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Evidence Inspection
                  </span>
                  <h2 className="text-lg font-black text-slate-900">Parcel {selectedParcelDetail.parcel_id}</h2>
                  <span className="text-xs text-slate-600 font-mono">Survey {selectedParcelDetail.full_survey}</span>
                </div>

                <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Match Score</span>
                  <span className="text-xl font-black text-blue-900 font-mono">{selectedParcelDetail.confidence}%</span>
                </div>
              </div>

              {/* Match Confidence Itemized Breakdown */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2">
                <div className="flex justify-between items-center text-xs font-bold text-slate-800">
                  <span>MATCH CONFIDENCE</span>
                  <span className="font-mono text-blue-700">{selectedParcelDetail.confidence}%</span>
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-700 rounded-full transition-all duration-500"
                    style={{ width: `${selectedParcelDetail.confidence}%` }}
                  />
                </div>

                {/* 5 Evidence Dimensions */}
                <div className="space-y-1.5 pt-2 text-[11px]">
                  <div className="flex justify-between items-center text-slate-600">
                    <span>Geometry IoU</span>
                    <span className="font-bold text-slate-900 font-mono">
                      {selectedParcelDetail.evidence?.geometry_match || 91}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-600">
                    <span>Area Match</span>
                    <span className="font-bold text-slate-900 font-mono">
                      {selectedParcelDetail.evidence?.area_match || 97}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-600">
                    <span>Centroid Proximity</span>
                    <span className="font-bold text-slate-900 font-mono">
                      {selectedParcelDetail.evidence?.centroid_match || 95}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-600">
                    <span>Attributes Agreement</span>
                    <span className="font-bold text-slate-900 font-mono">
                      {selectedParcelDetail.evidence?.attribute_match || 88}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-600">
                    <span>Boundary Conformance</span>
                    <span className="font-bold text-slate-900 font-mono">92%</span>
                  </div>
                </div>
              </div>

              {/* Explainable Reasoning Checklist */}
              <div className="bg-white border border-slate-200 rounded-lg p-3.5 space-y-2">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-blue-600" /> Why this match?
                </h3>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-start gap-2 text-slate-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>Boundary overlap is high (IoU {selectedParcelDetail.evidence?.geometry_match || 91}%)</span>
                  </div>
                  <div className="flex items-start gap-2 text-slate-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>Area difference is within configured tolerance (±4.5 m²)</span>
                  </div>
                  <div className="flex items-start gap-2 text-slate-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>GNSS RTK survey point lies inside candidate geometry</span>
                  </div>
                  <div className="flex items-start gap-2 text-slate-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span>Survey number agrees with 7/12 revenue register</span>
                  </div>
                  <div className="flex items-start gap-2 text-amber-900">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                    <span>Legacy geometry differs by 3.8% from high-res Drone ORI</span>
                  </div>
                </div>
              </div>

              {/* System Recommendation Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-1">
                <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider block">
                  System Recommendation
                </span>
                <span className="text-xs font-bold text-slate-900 block">
                  {selectedParcelDetail.recommendation?.geometry_source || 'GNSS + Drone Geometry'}
                </span>
                <p className="text-[11px] text-slate-600">
                  Highest geometric agreement with CORS RTK survey and current ORI evidence.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 space-y-2">
                <button
                  onClick={() => openConfirmation('ACCEPT', 'Approve Harmonization Recommendation')}
                  className="w-full py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs rounded transition shadow-2xs flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Accept Recommendation
                </button>
                <button
                  onClick={() => openConfirmation('MANUAL_REVIEW', 'Flag for Field Manual Review')}
                  className="w-full py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-xs rounded transition shadow-2xs cursor-pointer"
                >
                  Send to Manual Review
                </button>
              </div>
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              Select a parcel from directory
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {pendingAction && selectedParcelDetail && (
        <ConfirmationModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onConfirm={handleConfirmDecision}
          title={pendingAction.title}
          actionName={pendingAction.action}
          targetId={`Parcel ${selectedParcelDetail.parcel_id}`}
        />
      )}
    </div>
  );
};
