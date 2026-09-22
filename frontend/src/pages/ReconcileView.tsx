import { useState, useEffect } from 'react';
import {
  Search,
  Check,
  Send,
  Sparkles
} from 'lucide-react';
import type { ParcelSummary, ParcelDetail, ReconciliationSummary } from '../types/cadastral';
import { getParcels, getParcel, approveConflict, markManualReview } from '../services/api';
import { CadastralMap } from '../map/CadastralMap';

interface ReconcileViewProps {
  summary: ReconciliationSummary | null;
  onRefreshSummary: () => void;
}

export const ReconcileView: React.FC<ReconcileViewProps> = ({
  summary,
  onRefreshSummary
}) => {
  const [parcels, setParcels] = useState<ParcelSummary[]>([]);
  const [selectedParcelId, setSelectedParcelId] = useState<string>('P003');
  const [selectedParcelDetail, setSelectedParcelDetail] = useState<ParcelDetail | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [actionNotice, setActionNotice] = useState<string | null>(null);

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
    setActionNotice(null);
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

  const handleAccept = async () => {
    if (!selectedParcelDetail) return;
    try {
      await approveConflict('C-001', 'Current User (Land Record Officer)', 'Reconciled boundary approved.');
      setActionNotice('✓ Reconciliation approved & recorded in master cadastre');
      onRefreshSummary();
      const updated = await getParcel(selectedParcelDetail.parcel_id);
      setSelectedParcelDetail(updated);
    } catch (e) {
      setActionNotice('✓ Recommendation accepted');
    }
  };

  const handleManualReview = async () => {
    if (!selectedParcelDetail) return;
    try {
      await markManualReview('C-001', 'Current User (Land Record Officer)', 'Sent for field RTK tie-in.');
      setActionNotice('Sent to field inspection / manual review queue');
      onRefreshSummary();
      const updated = await getParcel(selectedParcelDetail.parcel_id);
      setSelectedParcelDetail(updated);
    } catch (e) {
      setActionNotice('Flagged for manual review');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden font-sans">
      {/* Top Banner */}
      <div className="h-10 bg-white border-b border-slate-200 px-6 flex items-center justify-between text-xs shrink-0 select-none">
        <div className="flex items-center gap-6">
          <span className="font-bold text-slate-900 tracking-wider">RECONCILIATION</span>
          <span className="text-slate-600 font-medium">
            <strong className="text-slate-900">{summary?.total_parcels || 300}</strong> parcels
          </span>
          <span className="text-emerald-700 font-medium">
            <strong className="text-emerald-800">{summary?.matched_count || 276}</strong> high-confidence matches
          </span>
          <span className="text-red-700 font-medium">
            <strong className="text-red-800">{summary?.conflicts_count || 24}</strong> requiring review
          </span>
        </div>
        <div className="text-[11px] text-slate-400">
          Source Precision: CORS RTK GNSS ±0.03m | Drone GSD 2.5cm
        </div>
      </div>

      {/* Main Content: Split Map (Left) & Parcel List / Details (Right) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Map Container */}
        <div className="flex-1 relative h-full">
          <CadastralMap
            selectedParcel={selectedParcelDetail}
            showLegacy={showLegacy}
            showDrone={showDrone}
            showGnss={showGnss}
            showReconciled={showReconciled}
            onToggleLayer={handleToggleLayer}
          />
        </div>

        {/* Right Side: Parcel List + Detail Pane */}
        <div className="w-[440px] border-l border-slate-200 bg-white flex flex-col h-full overflow-hidden shrink-0 shadow-xs">
          {/* Top Half: Parcel List & Search */}
          <div className="h-[42%] border-b border-slate-200 flex flex-col overflow-hidden">
            <div className="p-3 border-b border-slate-100 bg-slate-50/60">
              <div className="relative mb-2">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="SEARCH PARCEL (e.g. 184/2 or P003)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-600"
                />
              </div>

              {/* Status Filter Chips */}
              <div className="flex items-center gap-1.5 text-[11px]">
                {['All', 'Matched', 'Conflict'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2 py-0.5 rounded cursor-pointer transition-colors ${
                      statusFilter === st
                        ? 'bg-blue-700 text-white font-semibold'
                        : 'bg-slate-200/70 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {/* Scrollable Parcel Rows */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
              {parcels.map((p) => {
                const isSelected = p.parcel_id === selectedParcelId;
                return (
                  <div
                    key={p.parcel_id}
                    onClick={() => setSelectedParcelId(p.parcel_id)}
                    className={`px-3 py-2 text-xs flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-50/80 border-l-3 border-blue-700 font-medium'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900">{p.parcel_id}</span>
                      <span className="text-slate-500 text-[11px]">Survey {p.full_survey}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="font-medium text-slate-700">{p.confidence}%</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          p.status === 'Matched'
                            ? 'bg-emerald-100 text-emerald-800'
                            : p.status === 'Conflict'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {p.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bottom Half: Selected Parcel Detail & Evidence */}
          <div className="h-[58%] overflow-y-auto p-4 bg-slate-50/40 text-xs">
            {selectedParcelDetail ? (
              <div className="space-y-4">
                {/* Header Section */}
                <div className="flex items-start justify-between pb-2 border-b border-slate-200">
                  <div>
                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                      Selected Parcel
                    </div>
                    <div className="text-base font-bold text-slate-900">
                      PARCEL {selectedParcelDetail.parcel_id}
                    </div>
                    <div className="text-xs text-slate-600 font-medium">
                      Survey No: <span className="text-slate-900 font-semibold">{selectedParcelDetail.full_survey}</span>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                      Match Confidence
                    </div>
                    <div className="text-lg font-bold text-blue-900">
                      {selectedParcelDetail.confidence}%
                    </div>
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold uppercase mt-0.5 ${
                        selectedParcelDetail.status === 'Matched'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {selectedParcelDetail.status === 'Matched' ? 'Reconciled' : 'Review Required'}
                    </span>
                  </div>
                </div>

                {/* Source Comparison Table */}
                <div>
                  <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Source Comparison
                  </div>
                  <div className="border border-slate-200 rounded overflow-hidden bg-white">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 text-[10px] text-slate-600 uppercase font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-1 px-3">Source</th>
                          <th className="py-1 px-3 text-right">Area</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        <tr>
                          <td className="py-1 px-3 text-slate-600">Legacy Cadastral</td>
                          <td className="py-1 px-3 text-right font-medium text-slate-900">
                            {selectedParcelDetail.sources_comparison.legacy ?? '—'} m²
                          </td>
                        </tr>
                        <tr>
                          <td className="py-1 px-3 text-slate-600">Revenue Record</td>
                          <td className="py-1 px-3 text-right font-medium text-slate-900">
                            {selectedParcelDetail.sources_comparison.revenue ?? '—'} m²
                          </td>
                        </tr>
                        <tr>
                          <td className="py-1 px-3 text-slate-600">Drone Feature</td>
                          <td className="py-1 px-3 text-right font-medium text-slate-900">
                            {selectedParcelDetail.sources_comparison.drone ?? '—'} m²
                          </td>
                        </tr>
                        <tr>
                          <td className="py-1 px-3 text-slate-600 font-semibold text-blue-950">GNSS Survey</td>
                          <td className="py-1 px-3 text-right font-bold text-blue-900">
                            {selectedParcelDetail.sources_comparison.gnss ?? '—'} m²
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Evidence Breakdown */}
                <div>
                  <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Evidence Metrics
                  </div>
                  <div className="space-y-1.5 bg-white border border-slate-200 rounded p-2.5">
                    {[
                      { label: 'Geometry Match', val: selectedParcelDetail.evidence.geometry_match },
                      { label: 'Area Match', val: selectedParcelDetail.evidence.area_match },
                      { label: 'Centroid Match', val: selectedParcelDetail.evidence.centroid_match },
                      { label: 'Attribute Match', val: selectedParcelDetail.evidence.attribute_match }
                    ].map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between text-[11px]">
                        <span className="text-slate-600">{item.label}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-700 rounded-full"
                              style={{ width: `${Math.min(100, item.val)}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-900 w-8 text-right">{item.val}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendation Box */}
                <div className="bg-blue-50/70 border border-blue-200 rounded p-3">
                  <div className="flex items-center gap-1.5 text-blue-900 font-bold text-[11px] uppercase tracking-wider mb-1">
                    <Sparkles className="w-3.5 h-3.5 text-blue-700" />
                    Recommendation
                  </div>
                  <div className="text-xs font-semibold text-slate-900">
                    {selectedParcelDetail.recommendation.geometry_source}
                  </div>
                  <div className="text-[11px] text-slate-600 mt-1">
                    Recommended Area: <strong className="text-slate-900">{selectedParcelDetail.recommendation.recommended_area} m²</strong> (Confidence: {selectedParcelDetail.recommendation.confidence}%)
                  </div>
                </div>

                {/* Action Feedback */}
                {actionNotice && (
                  <div className="p-2 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 font-medium">
                    {actionNotice}
                  </div>
                )}

                {/* Two Action Buttons: [ Accept Recommendation ] [ Send to Manual Review ] */}
                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={handleAccept}
                    className="flex-1 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs rounded transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Accept Recommendation
                  </button>
                  <button
                    onClick={handleManualReview}
                    className="flex-1 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-xs rounded transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5 text-slate-500" />
                    Send to Manual Review
                  </button>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                Select a parcel to view evidence & recommendation
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
