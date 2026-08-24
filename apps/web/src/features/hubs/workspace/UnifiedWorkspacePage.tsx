import { t } from '@/lib/i18n';
import { HeroBar } from './components/HeroBar';
import { PersonaLensChip } from './components/PersonaLensChip';
import { FreshnessFooter } from './components/FreshnessFooter';
import { ExecutiveHome } from './components/ExecutiveHome';
import { PlannerHome } from './components/PlannerHome';
import { MOStatusDonut } from './components/MOStatusDonut';
import { ActionCenter } from './components/ActionCenter';
import { PersonaWidgetGrid } from './components/PersonaWidgetGrid';
import { ExecOsStrip } from './components/ExecOsStrip';
import { AiInsightCard } from './components/AiInsightCard';
import { useWorkspaceData } from './hooks/useWorkspaceData';
import { usePersona } from './hooks/usePersona';
import { useDemoRole } from './hooks/useDemoRole';

/**
 * Today / Home — role-aware (executive vs planner) for Star Trans demo.
 */
export function UnifiedWorkspacePage() {
  const { dashboard, error, isLoading, refresh } = useWorkspaceData();
  const { role: jwtRole, persona } = usePersona();
  const { role: demoRole } = useDemoRole();

  if (isLoading && !dashboard) {
    return (
      <div className="space-y-4 animate-pulse" aria-busy="true" data-testid="unified-workspace-loading">
        <div className="h-28 rounded-xl bg-ipe-border/40" />
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-ipe-border/40" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div
        className="rounded-xl border border-ipe-border bg-ipe-surface-card p-6 text-sm text-ipe-text-muted"
        data-testid="unified-workspace-error"
      >
        <p>{error ?? t('workspace.error', 'Unified dashboard unavailable')}</p>
        <button type="button" className="mt-3 text-ipe-primary" onClick={() => refresh()}>
          {t('workspace.retry', 'Retry')}
        </button>
      </div>
    );
  }

  const isExecutive = demoRole === 'executive';
  const isPlannerHome = demoRole === 'planner' || demoRole === 'buyer' || demoRole === 'supervisor';

  return (
    <div className="space-y-5" data-testid="unified-workspace" data-persona={persona} data-demo-role={demoRole}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <HeroBar dashboard={dashboard} role={jwtRole} />
        </div>
        <PersonaLensChip />
      </div>

      {isExecutive ? (
        <ExecutiveHome dashboard={dashboard} />
      ) : isPlannerHome ? (
        <PlannerHome dashboard={dashboard} />
      ) : (
        <>
          <PersonaWidgetGrid dashboard={dashboard} persona={persona} />
          <section aria-label={t('workspace.os.section', 'Work & decisions')}>
            <h2 className="mb-2 text-xs font-bold uppercase tracking-widest text-ipe-text-muted">
              {t('workspace.os.section', 'Work & decisions')}
            </h2>
            <ExecOsStrip />
          </section>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <ActionCenter actions={dashboard.actions} maxVisible={5} />
            </div>
            <div className="lg:col-span-3">
              <MOStatusDonut breakdown={dashboard.mo_breakdown} capacity={dashboard.capacity} />
            </div>
            <div className="lg:col-span-4">
              <AiInsightCard />
            </div>
          </div>
        </>
      )}

      <FreshnessFooter system={dashboard.system} />
    </div>
  );
}
