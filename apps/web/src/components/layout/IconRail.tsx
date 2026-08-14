import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { t } from '@/lib/i18n';
import type { DomainId, ProductDomain } from '@/lib/productArchitecture';

interface IconRailProps {
  activeDomainId: DomainId;
  domains: ProductDomain[];
}

function DomainLink({
  domain,
  active,
}: {
  domain: ProductDomain;
  active: boolean;
}) {
  const Icon = domain.icon;
  return (
    <NavLink
      to={domain.to}
      title={t(domain.labelKey, domain.fallback)}
      data-testid={`domain-${domain.id}`}
      className={cn(
        'group relative flex flex-col items-center gap-1 rounded-lg px-1 py-2.5 text-[10px] font-medium transition-colors',
        active ? 'bg-white/12 text-white' : 'text-white/55 hover:bg-white/8 hover:text-white',
      )}
    >
      {active ? (
        <span
          aria-hidden
          className="absolute start-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-e bg-ipe-primary"
        />
      ) : null}
      <Icon size={20} strokeWidth={active ? 2.25 : 1.75} aria-hidden />
      <span className="leading-none">{t(domain.labelKey, domain.fallback)}</span>
    </NavLink>
  );
}

export function IconRail({ activeDomainId, domains }: IconRailProps) {
  const primary = domains.filter((d) => !d.railBottom);
  const bottom = domains.filter((d) => d.railBottom);

  return (
    <aside
      className="flex h-full w-rail shrink-0 flex-col bg-ipe-navy text-ipe-text-inverse"
      data-testid="icon-rail"
      aria-label={t('nav.domains', 'Domains')}
    >
      <div className="flex h-header items-center justify-center border-b border-white/10">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-ipe-primary text-sm font-bold tracking-tight text-white">
          IPE
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
        {primary.map((domain) => (
          <DomainLink key={domain.id} domain={domain} active={domain.id === activeDomainId} />
        ))}
      </nav>
      {bottom.length > 0 ? (
        <nav
          className="mt-auto flex flex-col gap-1 border-t border-white/10 p-2"
          aria-label={t('nav.domain.admin', 'Admin')}
        >
          {bottom.map((domain) => (
            <DomainLink key={domain.id} domain={domain} active={domain.id === activeDomainId} />
          ))}
        </nav>
      ) : null}
    </aside>
  );
}
