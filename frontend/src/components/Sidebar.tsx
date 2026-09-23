import React from 'react';
import {
  LayoutDashboard,
  Database,
  Layers,
  AlertTriangle,
  CheckSquare,
  Activity,
  Award,
  Server
} from 'lucide-react';

export type NavTab = 'dashboard' | 'workspace' | 'reconcile' | 'conflicts' | 'review' | 'changes' | 'evaluation';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  conflictsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, conflictsCount }) => {
  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'workspace' as NavTab, label: 'Data Sources', icon: Database },
    { id: 'reconcile' as NavTab, label: 'Harmonization', icon: Layers },
    { id: 'conflicts' as NavTab, label: 'Conflicts', icon: AlertTriangle, badge: conflictsCount },
    { id: 'review' as NavTab, label: 'Review', icon: CheckSquare },
    { id: 'changes' as NavTab, label: 'Changes', icon: Activity },
    { id: 'evaluation' as NavTab, label: 'Evaluation', icon: Award }
  ];

  return (
    <aside className="w-56 bg-[#0b1e36] text-white flex flex-col justify-between select-none shrink-0 border-r border-slate-800 font-sans z-30">
      <div>
        {/* Brand Header */}
        <div className="h-14 px-5 border-b border-slate-800 flex items-center gap-2.5">
          <div className="w-6 h-6 rounded bg-blue-600 flex items-center justify-center font-bold text-white text-xs">
            U
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white leading-none">ULAG</h1>
            <span className="text-[10px] text-slate-400 font-medium">Urban Land Harmonization</span>
          </div>
        </div>

        {/* Navigation Rail */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center justify-between ${
                  isActive
                    ? 'bg-blue-600 text-white font-semibold shadow-xs'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="px-1.5 py-0.2 text-[10px] bg-amber-500 text-slate-950 font-bold rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status */}
      <div className="p-3 border-t border-slate-800 text-[11px] space-y-2 bg-[#08172b]">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-emerald-300 font-semibold">System Online</span>
          </span>
          <span className="text-[10px] font-mono text-slate-500">v4.0</span>
        </div>
        
        <div className="pt-1 flex items-center gap-2 text-slate-300">
          <Server className="w-3.5 h-3.5 text-blue-400" />
          <div className="truncate">
            <span className="text-[10px] text-slate-400 block leading-none">Authority</span>
            <span className="font-semibold text-slate-200">District Land Office</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
