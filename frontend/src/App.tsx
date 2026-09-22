import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import type { NavTab } from './components/Navbar';
import { WorkspaceView } from './pages/WorkspaceView';
import { ReconcileView } from './pages/ReconcileView';
import { ConflictsView } from './pages/ConflictsView';
import { ReviewView } from './pages/ReviewView';
import type { ReconciliationSummary, ValidationReport } from './types/cadastral';
import { getSummary } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('workspace');
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

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col text-slate-900 selection:bg-blue-100">
      <Navbar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        conflictsCount={summary?.conflicts_count || 24}
      />

      <main className="flex-1 overflow-auto">
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
      </main>
    </div>
  );
}

export default App;
