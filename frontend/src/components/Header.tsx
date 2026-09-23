import { Layers, UserCheck } from 'lucide-react';

interface HeaderProps {
  currentTabLabel: string;
}

export const Header: React.FC<HeaderProps> = ({ currentTabLabel }) => {
  return (
    <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between select-none shrink-0 z-20 font-sans">
      {/* Current Workspace Breadcrumb */}
      <div className="flex items-center gap-3">
        <span className="font-bold text-sm text-slate-900 tracking-wide uppercase">
          {currentTabLabel}
        </span>
        <span className="text-slate-300">|</span>
        <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
          <Layers className="w-3.5 h-3.5 text-blue-600" />
          <span>Active Dataset: <strong className="text-slate-800 font-semibold">Urban Land Dataset v4</strong> (Approved Harmonized)</span>
        </div>
      </div>

      {/* Header Right Actions & Badges */}
      <div className="flex items-center gap-4 text-xs">
        {/* DEMO MODE Badge */}
        <div className="px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-300 rounded font-semibold text-[11px] flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
          DEMO MODE (Synthetic 300 Parcels)
        </div>

        {/* User Officer Badge */}
        <div className="flex items-center gap-2 bg-slate-50 px-3 py-1 rounded border border-slate-200 text-slate-700 font-medium">
          <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>REVIEW OFFICER</span>
        </div>
      </div>
    </header>
  );
};
