import { Link, useLocation } from 'react-router-dom';
import { t } from '@/lib/i18n';
import { cn } from '@/lib/utils';

const LABELS: Record<string, string> = {
  workspace: 'Home',
  home: 'Home',
  planning: 'Plan',
  plan: 'Plan',
  execute: 'Execute',
  analyze: 'Analyze',
  'control-tower': 'Control Tower',
  resolution: 'Resolution Center',
  schedule: 'Production Schedule',
  demand: 'Demand Intelligence',
  scenarios: 'Scenario Workbench',
  predictions: 'Predictive Risk',
  'root-cause': 'Root Cause',
  cockpit: 'Cockpit',
  horizons: 'Horizons',
  dashboard: 'Dashboard',
  'command-center': 'Analyze',
  'otd-analytics': 'OTD Analytics',
  'war-room': 'War Room',
  'ops-live': 'Ops Live',
  executive: 'Executive',
  'cost-of-chaos': 'Cost of Chaos',
  outcomes: 'Outcomes',
  intelligence: 'Intelligence',
  platform: 'Admin',
  admin: 'Admin',
  upload: 'Data Upload',
  'odoo-config': 'Odoo Config',
  agents: 'Agents',
  exceptions: 'Exceptions',
  'supply-chain': 'Supply',
  supply: 'Supply',
  'ai-governance': 'Copilot',
  copilot: 'Copilot',
  'shop-floor': 'Shop Floor',
  'detailed-schedule': 'Detailed Schedule',
  versions: 'Versions',
  work: 'Execute',
  projects: 'Projects',
  tasks: 'Tasks',
  approvals: 'Approvals',
  meetings: 'Meetings',
  calendar: 'Calendar',
  documents: 'Documents',
  knowledge: 'Knowledge',
  objectives: 'Objectives',
  kpis: 'KPIs',
  teams: 'Teams',
  automation: 'Automation',
  reports: 'Reports',
};

function labelFor(segment: string): string {
  return LABELS[segment] ?? segment.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

interface BreadcrumbsProps {
  /** Compact inline variant for the global header. */
  variant?: 'bar' | 'inline';
  className?: string;
}

/** App-wide breadcrumb — UX-08 / STREAM 3: Home / Plan / … */
export function Breadcrumbs({ variant = 'inline', className }: BreadcrumbsProps) {
  const location = useLocation();
  const parts = location.pathname.split('/').filter(Boolean);
  if (parts.length === 0 || parts[0] === 'login') return null;

  // Home rail route — show only "Home" (no duplicate).
  if (parts[0] === 'workspace' || parts[0] === 'home') {
    if (parts.length === 1) {
      return (
        <nav
          aria-label={t('nav.breadcrumb', 'Breadcrumb')}
          className={cn(
            'text-xs text-ipe-text-muted',
            variant === 'bar' && 'border-b border-ipe-border bg-ipe-surface-card px-6 py-2',
            className,
          )}
        >
          <ol className="flex flex-wrap items-center gap-1">
            <li>
              <span className="font-medium text-ipe-text">{t('nav.home', 'Home')}</span>
            </li>
          </ol>
        </nav>
      );
    }
  }

  const crumbs = parts.map((seg, i) => {
    const path = '/' + parts.slice(0, i + 1).join('/');
    return { seg, path, label: labelFor(seg) };
  });

  return (
    <nav
      aria-label={t('nav.breadcrumb', 'Breadcrumb')}
      className={cn(
        'text-xs text-ipe-text-muted',
        variant === 'bar' && 'border-b border-ipe-border bg-ipe-surface-card px-6 py-2',
        className,
      )}
    >
      <ol className="flex flex-wrap items-center gap-1">
        <li>
          <Link to="/workspace" className="hover:text-ipe-primary">
            {t('nav.home', 'Home')}
          </Link>
        </li>
        {crumbs.map((c, i) => (
          <li key={c.path} className="flex items-center gap-1">
            <span aria-hidden>/</span>
            {i === crumbs.length - 1 ? (
              <span className="font-medium text-ipe-text">{c.label}</span>
            ) : (
              <Link to={c.path} className="hover:text-ipe-primary">
                {c.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
