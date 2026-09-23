import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Filter,
  ArrowRight,
  AlertTriangle,
  Info,
  Search
} from 'lucide-react';
import type { ConflictItem, ParcelDetail } from '../types/cadastral';
import { getConflicts, getParcel } from '../services/api';
import { CadastralMap } from '../map/CadastralMap';

interface ConflictsViewProps {
  onSelectConflictForReview: (conflictId: string) => void;
}

export const ConflictsView: React.FC<ConflictsViewProps> = ({
  onSelectConflictForReview
}) => {
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [filterType, setFilterType] = useState<string>('All');
  const [selectedConflictId, setSelectedConflictId] = useState<string>('C-001');
  const [selectedConflict, setSelectedConflict] = useState<ConflictItem | null>(null);
  const [parcelDetail, setParcelDetail] = useState<ParcelDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    getConflicts(filterType)
      .then((data) => {
        setConflicts(data);
        if (data.length > 0 && !selectedConflictId) {
          setSelectedConflictId(data[0].conflict_id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filterType]);

  useEffect(() => {
    if (!selectedConflictId) return;
    const found = conflicts.find((c) => c.conflict_id === selectedConflictId);
    if (found) {
      setSelectedConflict(found);
      getParcel(found.parcel_id).then(setParcelDetail).catch(console.error);
    }
  }, [selectedConflictId, conflicts]);

  const filterTabs = ['All', 'Geometry', 'Area', 'Attribute', 'Topology'];

  const getSeverityBadge = (severity: string) => {
    const s = severity.toUpperCase();
    if (s.includes('HIGH')) {
      return (
        <span className="px-2 py-0.5 bg-red-100 text-red-900 font-bold text-[10px] rounded border border-red-300 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3 text-red-600" /> HIGH — Officer Action Needed
        </span>
      );
    }
    if (s.includes('MEDIUM')) {
      return (
        <span className="px-2 py-0.5 bg-amber-100 text-amber-900 font-bold text-[10px] rounded border border-amber-300 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3 text-amber-600" /> MEDIUM — Requires Verification
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 bg-blue-100 text-blue-900 font-bold text-[10px] rounded border border-blue-300 flex items-center gap-1">
        <Info className="w-3 h-3 text-blue-600" /> LOW — Informational
      </span>
    );
  };

  const filteredConflicts = conflicts.filter((c) => {
    if (!searchQuery) return true;
    return (
      c.conflict_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.parcel_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.survey_no.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden font-sans select-none bg-slate-100">
      {/* Top Header Bar */}
      <div className="h-12 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-4 h-4 text-red-600" />
          <h1 className="font-bold text-sm text-slate-900 uppercase tracking-wide">Conflict Center Triage</h1>
          <span className="text-slate-300">|</span>
          <span className="text-xs text-slate-600 font-medium">
            <strong className="text-red-700">{conflicts.length} Active Conflicts</strong> requiring officer adjudication
          </span>
        </div>

        {/* Filter Pill Buttons */}
        <div className="flex items-center gap-1.5 text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
          {filterTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterType(tab)}
              className={`px-3 py-1 rounded text-xs font-semibold cursor-pointer transition ${
                filterType === tab
                  ? 'bg-blue-700 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL: CONFLICT LIST (Width: 360px) */}
        <div className="w-[360px] bg-white border-r border-slate-200 flex flex-col h-full shrink-0">
          <div className="p-3 border-b border-slate-200 bg-slate-50">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search Conflict / Parcel..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded text-xs text-slate-800 outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {loading ? (
              <div className="p-6 text-center text-xs text-slate-500">Loading active conflicts...</div>
            ) : filteredConflicts.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">No conflicts found.</div>
            ) : (
              filteredConflicts.map((c) => {
                const isSelected = c.conflict_id === selectedConflictId;
                return (
                  <button
                    key={c.conflict_id}
                    onClick={() => setSelectedConflictId(c.conflict_id)}
                    className={`w-full p-3 text-xs text-left transition-colors flex flex-col gap-1.5 ${
                      isSelected
                        ? 'bg-blue-50/90 border-l-4 border-blue-700'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 font-mono">{c.conflict_id}</span>
                      <span className="font-semibold text-slate-800">Parcel {c.parcel_id}</span>
                    </div>

                    <p className="text-[11px] text-slate-600 line-clamp-1">{c.explanation}</p>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[10px] text-slate-500 font-mono">{c.discrepancy_delta || 'Geometry discrepancy'}</span>
                      {getSeverityBadge(c.severity)}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* RIGHT PANEL: SELECTED CONFLICT DETAILS & AUTO-FOCUSED MAP (Flex 1) */}
        <div className="flex-1 flex flex-col md:flex-row h-full overflow-hidden">
          {selectedConflict ? (
            <>
              {/* Map Focused Area */}
              <div className="flex-1 relative h-full bg-slate-900">
                <CadastralMap selectedParcel={parcelDetail} />

                <div className="absolute top-3 left-3 z-[1000] bg-slate-900/90 text-white text-xs border border-slate-700 px-3 py-1.5 rounded shadow-lg backdrop-blur-md">
                  <span className="font-bold text-red-400">Target Feature Focus:</span> Parcel {selectedConflict.parcel_id}
                </div>
              </div>

              {/* Conflict Detail Inspector Pane */}
              <div className="w-[420px] bg-white border-l border-slate-200 h-full overflow-y-auto p-5 space-y-5 shrink-0 shadow-xs">
                {/* Conflict Header */}
                <div className="border-b border-slate-200 pb-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-blue-900 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {selectedConflict.conflict_id}
                    </span>
                    {getSeverityBadge(selectedConflict.severity)}
                  </div>

                  <h2 className="text-lg font-black text-slate-900">
                    {selectedConflict.conflict_type} Conflict — Parcel {selectedConflict.parcel_id}
                  </h2>
                  <p className="text-xs text-slate-600 font-medium leading-relaxed">
                    {selectedConflict.explanation}
                  </p>
                </div>

                {/* Source Comparison Table */}
                {parcelDetail && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                      Discrepancy Source Evidence
                    </span>
                    <div className="border border-slate-200 rounded overflow-hidden text-xs bg-slate-50">
                      <div className="flex justify-between p-2 border-b border-slate-200">
                        <span className="text-slate-600 font-medium">Legacy Cadastral Area:</span>
                        <strong className="font-mono text-slate-900">{parcelDetail.sources_comparison.legacy ?? '—'} m²</strong>
                      </div>
                      <div className="flex justify-between p-2 border-b border-slate-200">
                        <span className="text-slate-600 font-medium">Drone ORI Extent:</span>
                        <strong className="font-mono text-amber-900">{parcelDetail.sources_comparison.drone ?? '—'} m²</strong>
                      </div>
                      <div className="flex justify-between p-2 border-b border-slate-200">
                        <span className="text-slate-600 font-medium">GNSS Survey Area:</span>
                        <strong className="font-mono text-red-900">{parcelDetail.sources_comparison.gnss ?? '—'} m²</strong>
                      </div>
                      <div className="flex justify-between p-2 font-bold text-blue-950 bg-blue-50/50">
                        <span>Discrepancy Variance:</span>
                        <span className="font-mono text-red-700">{selectedConflict.discrepancy_delta || '—'}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* System Adjudication Guidance */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 space-y-1 text-xs">
                  <span className="font-bold text-amber-900 block flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Officer Adjudication Protocol
                  </span>
                  <p className="text-[11px] text-amber-800 leading-normal">
                    Review side-by-side evidence before submitting final decision. High-confidence GNSS CORS survey has higher priority for spatial boundaries.
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="pt-2 space-y-2">
                  <button
                    onClick={() => onSelectConflictForReview(selectedConflict.conflict_id)}
                    className="w-full py-2.5 bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs rounded transition shadow-xs flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <span>Open Review Workspace Decision</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
              Select a conflict from triage list
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
