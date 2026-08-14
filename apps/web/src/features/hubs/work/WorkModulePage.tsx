import { useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plus, ArrowUpRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { t } from '@/lib/i18n';
import { ROUTES } from '@/lib/constants';
import { PRODUCT_DOMAINS, WORK_MODULE_ICONS } from '@/lib/productArchitecture';
import { cn } from '@/lib/utils';

const MOCK_ROWS: Record<string, { title: string; meta: string; status: string; tone: 'default' | 'success' | 'warning' | 'danger' }[]> = {
  projects: [
    { title: 'Q3 Capacity Stabilization', meta: 'Ops · Stage Gate 2', status: 'Active', tone: 'success' },
    { title: 'Copper dual-source', meta: 'Supply · Due 18 Aug', status: 'At risk', tone: 'warning' },
    { title: 'OTD recovery program', meta: 'Exec · Linked to Cost of Chaos', status: 'Critical', tone: 'danger' },
  ],
  tasks: [
    { title: 'Expedite copper for MO-ST-007', meta: 'You · Due today', status: 'Today', tone: 'danger' },
    { title: 'Approve Reschedule path', meta: 'Manager · Resolution Center', status: 'Approval', tone: 'warning' },
    { title: 'Update Tank Fab buffer', meta: 'Scheduler · Linked MO-ST-009', status: 'Open', tone: 'default' },
  ],
  approvals: [
    { title: 'Scenario Demo-072838 promote', meta: 'Workbench · +8.3% OTD', status: 'Pending', tone: 'warning' },
    { title: 'Resolution MO-ST-007 Reschedule', meta: 'AI recommended · 92% conf.', status: 'Pending', tone: 'warning' },
  ],
  meetings: [
    { title: 'Daily production triage', meta: 'Today 08:30 · Control Tower pack', status: 'Ready', tone: 'success' },
    { title: 'S&OP weekly', meta: 'Wed · Demand + Finance', status: 'Prep', tone: 'default' },
  ],
  calendar: [
    { title: 'Solver refresh window', meta: 'Tonight 02:00', status: 'Scheduled', tone: 'default' },
    { title: 'Shift A handover', meta: 'Today 14:00', status: 'Today', tone: 'warning' },
  ],
  documents: [
    { title: 'Uploaded Q3 plan.xlsx', meta: 'Production Schedule', status: 'Linked', tone: 'success' },
    { title: 'Tariff shock brief', meta: 'Command Center', status: 'Draft', tone: 'default' },
  ],
  knowledge: [
    { title: 'Material shortage playbook', meta: 'Resolution · 12 uses', status: 'Canonical', tone: 'success' },
    { title: 'Tank Fab overload SOP', meta: 'Capacity · Updated Jul', status: 'Canonical', tone: 'success' },
  ],
  objectives: [
    { title: 'OTD ≥ 90%', meta: 'Company · Current 74.9%', status: 'Behind', tone: 'danger' },
    { title: 'Cost of Chaos ≤ 1×', meta: 'Finance · Current 3×', status: 'Critical', tone: 'danger' },
  ],
  kpis: [
    { title: 'Factory health', meta: '73 · Stable', status: 'Watch', tone: 'warning' },
    { title: 'Orders at risk', meta: '4 MOs', status: 'Critical', tone: 'danger' },
    { title: 'AI overnight actions', meta: '0 (shadow)', status: 'Shadow', tone: 'default' },
  ],
  teams: [
    { title: 'Production Planning', meta: '4 members · On coverage', status: 'Healthy', tone: 'success' },
    { title: 'Supply Chain', meta: '3 members · 1 PTO', status: 'Watch', tone: 'warning' },
  ],
  automation: [
    { title: 'Auto-queue feasibility < 70', meta: 'fea-svc · Shadow', status: 'Shadow', tone: 'default' },
    { title: 'Nightly OR-Tools refresh', meta: 'cap-svc · Enabled', status: 'On', tone: 'success' },
  ],
  reports: [
    { title: 'Weekly Ops Pulse', meta: 'Auto · Monday 07:00', status: 'Scheduled', tone: 'default' },
    { title: 'QBR Executive Pack', meta: 'Command Center', status: 'Ready', tone: 'success' },
  ],
};

const APS_LINKS: Record<string, { label: string; to: string }[]> = {
  projects: [{ label: 'Open Control Tower', to: ROUTES.PLANNING_CONTROL_TOWER }],
  tasks: [{ label: 'Open Resolution Center', to: ROUTES.PLANNING_RESOLUTION }],
  approvals: [
    { label: 'Resolution Center', to: ROUTES.PLANNING_RESOLUTION },
    { label: 'Scenario Workbench', to: ROUTES.PLANNING_SCENARIOS },
  ],
  meetings: [{ label: 'AI Meeting Prep', to: ROUTES.AI_MEETING_PREP }],
  kpis: [{ label: 'Outcomes & Risk', to: ROUTES.COMMAND_DASHBOARD }],
  objectives: [{ label: 'Cost of Chaos', to: ROUTES.COMMAND_COST_OF_CHAOS }],
  automation: [{ label: 'Platform Agents', to: ROUTES.PLATFORM_AGENTS }],
  reports: [{ label: 'Executive dashboard', to: ROUTES.COMMAND_EXECUTIVE }],
};

function moduleIdFromPath(pathname: string): string {
  const part = pathname.split('/').filter(Boolean)[1] ?? 'projects';
  return part;
}

export function WorkModulePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const moduleId = moduleIdFromPath(location.pathname);
  // Work OS modules live under Execute (legacy `work` domain alias).
  const workDomain = PRODUCT_DOMAINS.find((d) => d.id === 'execute');
  const mod = workDomain?.modules.find((m) => m.id === moduleId) ?? workDomain?.modules.find((m) => m.id === 'projects');
  const Icon = WORK_MODULE_ICONS[moduleId] ?? WORK_MODULE_ICONS.projects;
  const rows = MOCK_ROWS[moduleId] ?? MOCK_ROWS.projects;
  const links = APS_LINKS[moduleId] ?? [];

  const primaryLabel = useMemo(() => {
    const map: Record<string, string> = {
      projects: 'New project',
      tasks: 'New task',
      approvals: 'Review queue',
      meetings: 'Schedule meeting',
      calendar: 'Add event',
      documents: 'Upload',
      knowledge: 'New article',
      objectives: 'New objective',
      kpis: 'Customize scorecard',
      teams: 'Invite member',
      automation: 'New rule',
      reports: 'Generate report',
    };
    return map[moduleId] ?? 'Create';
  }, [moduleId]);

  if (!mod) {
    return (
      <Card>
        <p className="text-sm text-ipe-text-muted">{t('work.missing', 'Module not found')}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-5" data-testid={`work-module-${moduleId}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-ipe-primary/10 text-ipe-primary">
            <Icon size={22} aria-hidden />
          </span>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-ipe-text">
              {t(mod.labelKey, mod.fallback)}
            </h1>
            <p className="mt-1 max-w-xl text-sm text-ipe-text-muted">
              {mod.description} — {t('work.apsBridge', 'Linked to manufacturing planning decisions.')}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {links.map((l) => (
            <Button key={l.to} variant="secondary" size="sm" onClick={() => navigate(l.to)}>
              {l.label}
              <ArrowUpRight size={14} className="ms-1" aria-hidden />
            </Button>
          ))}
          <Button
            size="sm"
            onClick={() => {
              if (moduleId === 'approvals') navigate(ROUTES.PLANNING_RESOLUTION);
              else if (moduleId === 'meetings') navigate(ROUTES.AI_MEETING_PREP);
            }}
          >
            <Plus size={14} className="me-1" aria-hidden />
            {t(`work.cta.${moduleId}`, primaryLabel)}
          </Button>
        </div>
      </div>

      {rows.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16 text-center">
          <Icon size={32} className="text-ipe-text-muted" aria-hidden />
          <p className="mt-3 text-sm font-medium text-ipe-text">
            {t('work.empty.title', 'Nothing here yet')}
          </p>
          <p className="mt-1 max-w-sm text-xs text-ipe-text-muted">
            {t('work.empty.body', 'Create an item or link one from Control Tower / Resolution Center.')}
          </p>
        </Card>
      ) : (
        <div className="overflow-hidden rounded-xl border border-ipe-border bg-ipe-surface-card shadow-sm">
          <table className="w-full text-start text-sm">
            <thead className="border-b border-ipe-border bg-ipe-surface-alt/80 text-[11px] uppercase tracking-wide text-ipe-text-muted">
              <tr>
                <th className="px-4 py-3 font-semibold">{t('work.col.item', 'Item')}</th>
                <th className="hidden px-4 py-3 font-semibold md:table-cell">
                  {t('work.col.context', 'Context')}
                </th>
                <th className="px-4 py-3 font-semibold">{t('work.col.status', 'Status')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.title}
                  className="border-b border-ipe-border last:border-0 hover:bg-ipe-surface-alt/50"
                >
                  <td className="px-4 py-3 font-medium text-ipe-text">{row.title}</td>
                  <td className="hidden px-4 py-3 text-ipe-text-muted md:table-cell">{row.meta}</td>
                  <td className="px-4 py-3">
                    <Badge
                      variant={row.tone}
                      className={cn(row.tone === 'default' && 'bg-ipe-surface-alt')}
                    >
                      {row.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
