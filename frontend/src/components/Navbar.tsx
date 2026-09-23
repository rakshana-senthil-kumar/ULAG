import { Layers, AlertTriangle, CheckSquare, Database, LayoutDashboard, Activity, Award } from 'lucide-react';

export type NavTab = 'dashboard' | 'workspace' | 'reconcile' | 'conflicts' | 'review' | 'changes' | 'evaluation';

interface NavbarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  conflictsCount: number;
}

export const Navbar = ({
  currentTab,
  onSelectTab,
  conflictsCount
}: NavbarProps) => {
  return (
    <header className="h-14 bg-[#0b1e36] text-white border-b border-slate-700 flex items-center justify-between px-6 select-none shrink-0 z-20">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-4">
        <div
          onClick={() => onSelectTab('dashboard')}
          className="cursor-pointer flex items-baseline gap-2"
        >
          <span className="font-bold text-base tracking-wide text-white flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 bg-blue-500 rounded-sm"></span>
            ULAG
          </span>
          <span className="text-[11px] text-slate-400 font-normal hidden lg:inline">
            Urban Land Record Harmonization Platform
          </span>
        </div>
      </div>

      {/* Navigation Bar */}
      <nav className="flex items-center gap-1">
        <button
          onClick={() => onSelectTab('dashboard')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'dashboard'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          Dashboard
        </button>

        <button
          onClick={() => onSelectTab('workspace')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'workspace'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          Workspace
        </button>

        <span className="text-slate-600 px-0.5">|</span>

        <button
          onClick={() => onSelectTab('reconcile')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'reconcile'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          1. Reconcile
        </button>

        <button
          onClick={() => onSelectTab('conflicts')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'conflicts'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          2. Conflicts
          {conflictsCount > 0 && (
            <span className="px-1.5 py-0.2 text-[10px] bg-red-600 text-white font-bold rounded-full ml-0.5">
              {conflictsCount}
            </span>
          )}
        </button>

        <button
          onClick={() => onSelectTab('review')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'review'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
          3. Review
        </button>

        <span className="text-slate-600 px-0.5">|</span>

        <button
          onClick={() => onSelectTab('changes')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'changes'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-purple-400" />
          Changes
        </button>

        <button
          onClick={() => onSelectTab('evaluation')}
          className={`px-2.5 py-1.5 text-xs font-medium rounded transition-colors flex items-center gap-1.5 ${
            currentTab === 'evaluation'
              ? 'bg-blue-600/30 text-blue-200 border border-blue-500/40'
              : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Award className="w-3.5 h-3.5 text-emerald-400" />
          Evaluation
        </button>
      </nav>

      {/* Operator identifier */}
      <div className="flex items-center gap-2 text-xs text-slate-400 hidden xl:flex">
        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
        <span>District Land Authority (MH)</span>
      </div>
    </header>
  );
};
