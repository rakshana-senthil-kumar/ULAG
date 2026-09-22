import { useState, useEffect } from 'react';
import { Filter, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import type { ConflictItem } from '../types/cadastral';
import { getConflicts } from '../services/api';

interface ConflictsViewProps {
  onSelectConflictForReview: (conflictId: string) => void;
}

export const ConflictsView: React.FC<ConflictsViewProps> = ({
  onSelectConflictForReview
}) => {
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [filterType, setFilterType] = useState<string>('All');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    getConflicts(filterType)
      .then((data) => setConflicts(data))
      .catch((err) => console.error('Error fetching conflicts:', err))
      .finally(() => setLoading(false));
  }, [filterType]);

  const filterTabs = ['All', 'Geometry', 'Area', 'Attribute', 'Missing'];

  return (
    <div className="max-w-5xl mx-auto py-8 px-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-200 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-600" />
            CONFLICTS
          </h1>
          <p className="text-xs text-slate-600 mt-1">
            <strong className="text-red-700">{conflicts.length} cases</strong> requiring attention & adjudication
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 mt-3 md:mt-0 text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
          {filterTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterType(tab)}
              className={`px-3 py-1 rounded cursor-pointer transition-colors text-xs ${
                filterType === tab
                  ? 'bg-blue-800 text-white font-semibold'
                  : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Conflict List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading conflict records...</div>
        ) : conflicts.length === 0 ? (
          <div className="p-8 bg-white border border-slate-200 rounded text-center text-xs text-slate-500">
            No conflicts found for filter '{filterType}'.
          </div>
        ) : (
          conflicts.map((c) => {
            const isApproved = c.status === 'Approved';
            return (
              <div
                key={c.conflict_id}
                onClick={() => onSelectConflictForReview(c.conflict_id)}
                className={`p-4 bg-white border rounded transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  c.conflict_id === 'C-001'
                    ? 'border-blue-300 bg-blue-50/20 hover:border-blue-500'
                    : 'border-slate-200 hover:border-slate-400'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      {c.conflict_id}
                    </span>
                    <span className="font-bold text-sm text-slate-900">
                      Survey {c.survey_no}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-red-100 text-red-800">
                      {c.conflict_type} conflict
                    </span>
                    {isApproved && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Approved
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-1">{c.explanation}</p>
                  {c.discrepancy_delta && (
                    <p className="text-[11px] text-slate-500 font-medium">{c.discrepancy_delta}</p>
                  )}
                </div>

                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <div className="text-xs font-bold text-blue-900">{c.confidence}% confidence</div>
                    <div className="text-[10px] text-slate-400">Severity: {c.severity}</div>
                  </div>

                  <button className="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 rounded text-xs font-semibold flex items-center gap-1 cursor-pointer">
                    Review Evidence
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
