import { AlertCircle, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { t } from '@/lib/i18n';
import { ROUTES } from '@/lib/constants';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { HealthRing } from './HealthRing';
import type { WorkspaceDashboard } from '../types';

interface HeroBarProps {
  dashboard: WorkspaceDashboard;
  role: string;
}

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function looksLikeUuid(value: string): boolean {
  return UUID_RE.test(value.trim());
}

/** Prefer a human first name; never render a UUID. */
export function resolveGreetingName(
  apiName: string | undefined | null,
  fullName?: string | null,
  email?: string | null,
): string {
  for (const candidate of [fullName, apiName, email]) {
    if (!candidate?.trim()) continue;
    const raw = candidate.trim();
    if (looksLikeUuid(raw)) continue;
    if (raw.includes('@')) {
      return raw.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    }
    return raw.split(/\s+/)[0];
  }
  return '';
}

function timeAwareGreeting(d: Date, name: string): { key: string; fallback: string; vars?: Record<string, string> } {
  const h = d.getHours();
  const period = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  if (name) {
    return {
      key: `workspace.greeting.${period}`,
      fallback:
        period === 'morning'
          ? 'Good morning, {name}'
          : period === 'afternoon'
            ? 'Good afternoon, {name}'
            : 'Good evening, {name}',
      vars: { name },
    };
  }
  return {
    key: `workspace.greeting.${period}.bare`,
    fallback:
      period === 'morning' ? 'Good morning' : period === 'afternoon' ? 'Good afternoon' : 'Good evening',
  };
}

export function HeroBar({ dashboard, role }: HeroBarProps) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { greeting, health, kpis, system } = dashboard;
  const name = resolveGreetingName(greeting.user_name, user?.full_name, user?.email);
  const pending = dashboard.actions.filter((a) => a.severity === 'critical' || a.severity === 'warning').length;
  const isExec = ['executive', 'manager'].includes(role);
  const isSupervisor = role === 'operator' || role === 'supervisor';
  const isAdmin = role === 'admin';
  const showTriage = !isExec && Number(kpis.orders_at_risk.value) > 0;
  const showRings = !isAdmin;
  const g = timeAwareGreeting(new Date(), name);
  const headline = t(g.key, g.fallback, g.vars);

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-ipe-border bg-ipe-surface-card p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
      <div className="flex-1">
        <h1 className="text-2xl font-semibold tracking-tight text-ipe-text">{headline}</h1>
        <p className="mt-1 text-sm text-ipe-text-muted">
          {isSupervisor
            ? t('workspace.shift_info', 'Current shift overview')
            : `${format(new Date(greeting.timestamp || Date.now()), 'EEEE d MMMM yyyy')} · ${greeting.tenant_name}`}
          {pending > 0 ? (
            <span className="ms-2 inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
              {t('workspace.actions_pending', '{count} actions require attention', { count: pending })}
            </span>
          ) : null}
        </p>
        <p className="mt-2 text-xs text-ipe-text-muted">
          {t('workspace.viewingAs', 'Viewing as')}:{' '}
          <span className="font-medium text-ipe-text">{role}</span>
        </p>
        {isAdmin ? (
          <p className="mt-1 text-xs text-ipe-text-muted">
            {t('workspace.system.title', 'System health')}: {system.odoo_sync.status} / {system.event_bus.status}
          </p>
        ) : null}
      </div>

      {showRings ? (
        <div className="hidden items-center gap-6 md:flex">
          <HealthRing value={health.factory_score} label={t('workspace.factory_health', 'Factory health')} />
          <HealthRing value={health.otd_current} label={t('workspace.otd', 'On-time delivery')} />
        </div>
      ) : null}

      <div className="flex gap-2">
        {showTriage ? (
          <button
            type="button"
            className="flex items-center gap-1.5 rounded-lg bg-ipe-primary px-3.5 py-2 text-xs font-medium text-white"
            onClick={() => navigate(ROUTES.PLANNING_CONTROL_TOWER)}
          >
            <AlertCircle size={14} aria-hidden />
            {t('workspace.triage', 'Triage now')}
          </button>
        ) : null}
        <button
          type="button"
          className="flex items-center gap-1.5 rounded-lg border border-ipe-border px-3.5 py-2 text-xs font-medium text-ipe-text"
          onClick={() => navigate(ROUTES.AI_COPILOT)}
        >
          <Sparkles size={14} aria-hidden />
          {t('workspace.ask_ai', 'Ask AI')}
        </button>
      </div>
    </div>
  );
}
