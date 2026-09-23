import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import type { NavTab } from './components/Sidebar';
import { Header } from './components/Header';

import { DashboardView } from './pages/DashboardView';
import { WorkspaceView } from './pages/WorkspaceView';
import { ReconcileView } from './pages/ReconcileView';
import { ConflictsView } from './pages/ConflictsView';
import { ReviewView } from './pages/ReviewView';
import { ChangeDetectionView } from './pages/ChangeDetectionView';
import { EvaluationView } from './pages/EvaluationView';

import type { ReconciliationSummary, ValidationReport } from './types/cadastral';
import { getSummary } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [reviewConflictId, setReviewConflictId] = useState<string>('C-001');

  // Load pipeline summary on startup
  const refreshSummary = () => {
    getSummary()
      .then((data) => setSummary(data))
      .catch((err) => console.log('Summary loading:', err));
  };

  useEffect(() => {
    refreshSummary();
  }, []);

  const handleReconciliationReady = (newSummary: ReconciliationSummary, newVal: ValidationReport) => {
    setSummary(newSummary);
    setValidation(newVal);
  };

  const handleSelectConflictForReview = (conflictId: string) => {
    setReviewConflictId(conflictId);
    setCurrentTab('review');
  };

  const tabLabels: Record<NavTab, string> = {
    dashboard: 'Executive Dashboard',
    workspace: 'Multi-Source Data Ingestion',
    reconcile: 'Harmonization Workstation',
    conflicts: 'Conflict Triage Center',
    review: 'Officer Adjudication Review',
    changes: 'Temporal Change Detection',
    evaluation: 'Benchmark & Pipeline Evaluation'
  };

  return (
    <div className="h-screen w-screen bg-[#f8fafc] flex overflow-hidden text-slate-900 selection:bg-blue-100 font-sans">
      {/* Compact Left Navigation Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        conflictsCount={summary?.conflicts_count || 24}
      />

      {/* Main Container Right (Header + Main Content View) */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header currentTabLabel={tabLabels[currentTab]} />

        <main className="flex-1 overflow-auto bg-[#f8fafc]">
          {currentTab === 'dashboard' && (
            <DashboardView
              summary={summary}
              onNavigateTab={(tab) => setCurrentTab(tab)}
            />
          )}

          {currentTab === 'workspace' && (
            <WorkspaceView
              summary={summary}
              validation={validation}
              onReconciliationReady={handleReconciliationReady}
              onNavigateToReconcile={() => setCurrentTab('reconcile')}
            />
          )}

          {currentTab === 'reconcile' && (
            <ReconcileView
              summary={summary}
              onRefreshSummary={refreshSummary}
            />
          )}

          {currentTab === 'conflicts' && (
            <ConflictsView
              onSelectConflictForReview={handleSelectConflictForReview}
            />
          )}

          {currentTab === 'review' && (
            <ReviewView
              conflictId={reviewConflictId}
              onBackToConflicts={() => setCurrentTab('conflicts')}
              onRefreshSummary={refreshSummary}
            />
          )}

          {currentTab === 'changes' && (
            <ChangeDetectionView />
          )}

          {currentTab === 'evaluation' && (
            <EvaluationView />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
