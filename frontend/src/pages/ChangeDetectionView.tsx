import React, { useEffect, useState } from 'react';
import type { ChangeDetectionItem } from '../types/canonical';
import { getTemporalChanges } from '../services/api';
import { Activity, Filter } from 'lucide-react';
import { BeforeAfterSlider } from '../components/BeforeAfterSlider';

export const ChangeDetectionView: React.FC = () => {
  const [changes, setChanges] = useState<ChangeDetectionItem[]>([]);
  const [filter, setFilter] = useState<string>('All');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTemporalChanges()
      .then(setChanges)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filterTabs = ['All', 'New', 'Removed', 'Modified', 'Land Use'];

  const filteredChanges = changes.filter((ch) => {
    if (filter === 'All') return true;
    if (filter === 'New') return ch.change_type.toLowerCase().includes('new') || ch.change_type.toLowerCase().includes('addition');
    if (filter === 'Removed') return ch.change_type.toLowerCase().includes('removed') || ch.change_type.toLowerCase().includes('demolished');
    if (filter === 'Modified') return ch.change_type.toLowerCase().includes('shift') || ch.change_type.toLowerCase().includes('boundary');
    if (filter === 'Land Use') return ch.change_type.toLowerCase().includes('land') || ch.change_type.toLowerCase().includes('use');
    return true;
  });

  return (
    <div className="p-6 max-w-[1400px] mx-auto space-y-6 select-none font-sans">
      {/* 1. View Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-800 border border-blue-200 rounded">
              Temporal Intelligence
            </span>
            <span className="text-xs text-slate-500 font-mono">2023 Historical Cadastral vs 2026 Drone ORI</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" /> Temporal Change Detection & Visual Split Analysis
          </h1>
        </div>

        {/* 3 Summary Badges */}
        <div className="flex items-center gap-3 text-xs">
          <div className="bg-purple-50 border border-purple-200 rounded px-3 py-1.5 text-center">
            <span className="text-purple-900 font-extrabold text-sm block font-mono">+3 Buildings</span>
            <span className="text-[10px] text-purple-700 font-medium">AI Footprints</span>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded px-3 py-1.5 text-center">
            <span className="text-amber-900 font-extrabold text-sm block font-mono">2 Boundary Shifts</span>
            <span className="text-[10px] text-amber-700 font-medium">Vector Variances</span>
          </div>

          <div className="bg-emerald-50 border border-emerald-200 rounded px-3 py-1.5 text-center">
            <span className="text-emerald-900 font-extrabold text-sm block font-mono">1 Conversion</span>
            <span className="text-[10px] text-emerald-700 font-medium">Land-Use Change</span>
          </div>
        </div>
      </div>

      {/* 2. Before / After Visual Split Map Slider */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between text-xs border-b border-slate-100 pb-2">
          <h2 className="font-bold text-slate-800 uppercase tracking-wider">VISUAL BEFORE / AFTER SLIDER COMPARISON</h2>
          <span className="text-[11px] text-slate-500">Drag vertical divider to compare 2023 Historical vs 2026 High-Res Drone Imagery</span>
        </div>

        <BeforeAfterSlider
          beforeTitle="Historical Cadastral Register"
          afterTitle="Current Drone ORI & AI Extracted Footprints"
          beforeYear="2023"
          afterYear="2026"
        />
      </div>

      {/* 3. Change Detection Filter & Event List */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">DETECTED TEMPORAL CHANGE EVENTS</h2>

          <div className="flex items-center gap-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
            {filterTabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-3 py-1 rounded text-xs font-semibold cursor-pointer transition ${
                  filter === tab
                    ? 'bg-blue-700 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Analyzing temporal change events...</div>
        ) : filteredChanges.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">No change events match filter '{filter}'.</div>
        ) : (
          <div className="space-y-3">
            {filteredChanges.map((ch) => (
              <div
                key={ch.change_id}
                className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs hover:border-slate-300 transition"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm font-mono">{ch.survey_no}</span>
                    <span className="px-2 py-0.5 text-[10px] uppercase font-bold bg-blue-100 text-blue-900 rounded border border-blue-200">
                      {ch.change_type}
                    </span>
                    <span
                      className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded text-white ${
                        ch.severity === 'High'
                          ? 'bg-red-600'
                          : ch.severity === 'Medium'
                          ? 'bg-amber-600'
                          : 'bg-blue-600'
                      }`}
                    >
                      {ch.severity} Severity
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs pt-1">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">2023 Historical Baseline:</span>
                      <span className="font-medium text-slate-700 font-mono">{ch.previous_value || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold block">2026 Current Observation:</span>
                      <span className="font-bold text-blue-900 font-mono">{ch.current_value || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right shrink-0 space-y-1">
                  <span className="text-[10px] text-slate-400 font-semibold block">Algorithm Confidence</span>
                  <span className="font-black text-emerald-700 text-base font-mono">{ch.confidence}%</span>
                  <span className="text-[10px] text-slate-400 font-mono block pt-1">Detected: {ch.detected_at}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
