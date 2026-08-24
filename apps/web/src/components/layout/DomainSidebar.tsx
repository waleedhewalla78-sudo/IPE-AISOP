import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { t } from '@/lib/i18n';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { AgentNavigator } from '@/features/agents/components/AgentNavigator';
import type { DomainModule, ProductDomain } from '@/lib/productArchitecture';

interface DomainSidebarProps {
  domain: ProductDomain;
  modules: DomainModule[];
  personaCaption?: string;
}

export function DomainSidebar({ domain, modules, personaCaption }: DomainSidebarProps) {
  const location = useLocation();

  if (domain.fullBleed || modules.length === 0) {
    return null;
  }

  const isAiDomain = domain.id === 'copilot';

  return (
    <aside
      className="flex h-full w-domain-side shrink-0 flex-col border-e border-ipe-border bg-ipe-surface-card"
      data-testid="domain-sidebar"
      data-domain={domain.id}
    >
      <div className="flex h-header items-center justify-between border-b border-ipe-border px-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-ipe-text-muted">
            {t(domain.labelKey, domain.fallback)}
          </p>
          <p className="text-sm font-semibold text-ipe-text">
            {isAiDomain
              ? t('nav.domain.ai.agentsTitle', 'Intelligence Agents')
              : t(`nav.domain.${domain.id}.title`, domain.fallback)}
          </p>
        </div>
        <LanguageSwitcher />
      </div>

      {isAiDomain ? (
        <div className="min-h-0 flex-1 overflow-hidden">
          <AgentNavigator />
        </div>
      ) : (
        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
          {modules.map((mod) => {
            const prefix = mod.match ?? mod.to;
            const active =
              location.pathname === mod.to ||
              location.pathname.startsWith(`${mod.to}/`) ||
              (prefix !== mod.to &&
                (location.pathname === prefix || location.pathname.startsWith(`${prefix}/`)));
            return (
              <NavLink
                key={mod.id}
                to={mod.to}
                className={cn(
                  'block rounded-lg px-3 py-2.5 transition-colors',
                  active
                    ? 'bg-ipe-primary/10 text-ipe-primary'
                    : 'text-ipe-text hover:bg-ipe-surface-alt',
                )}
                data-testid={`module-${mod.id}`}
              >
                <div className="text-sm font-semibold leading-tight">
                  {t(mod.labelKey, mod.fallback)}
                </div>
                {mod.description ? (
                  <div className="mt-0.5 line-clamp-1 text-[11px] font-normal text-ipe-text-muted">
                    {mod.description}
                  </div>
                ) : null}
              </NavLink>
            );
          })}
        </nav>
      )}

      {personaCaption ? (
        <div className="border-t border-ipe-border px-3 py-2 text-[10px] text-ipe-text-muted">
          {personaCaption}
        </div>
      ) : null}
    </aside>
  );
}
