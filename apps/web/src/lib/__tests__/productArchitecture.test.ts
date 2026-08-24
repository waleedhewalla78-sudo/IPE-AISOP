import { describe, it, expect } from 'vitest';
import {
  planHomeForPersona,
  PRODUCT_DOMAINS,
  rankDomainsForPersona,
  rankModulesForPersona,
  resolveDomain,
  DOMAIN_ID_ALIASES,
} from '@/lib/productArchitecture';
import { ROUTES } from '@/lib/constants';

describe('resolveDomain', () => {
  it('maps workspace to home', () => {
    expect(resolveDomain(ROUTES.WORKSPACE).id).toBe('home');
  });

  it('maps planning to plan and supply-chain to supply', () => {
    expect(resolveDomain(ROUTES.PLANNING_CONTROL_TOWER).id).toBe('plan');
    expect(resolveDomain(ROUTES.SUPPLY_PLANNING).id).toBe('supply');
  });

  it('maps work and shop-floor routes to execute', () => {
    expect(resolveDomain(ROUTES.WORK_PROJECTS).id).toBe('execute');
    expect(resolveDomain(ROUTES.WORK_OBJECTIVES).id).toBe('execute');
    expect(resolveDomain(ROUTES.SHOP_FLOOR).id).toBe('execute');
  });

  it('maps command center to analyze', () => {
    expect(resolveDomain(ROUTES.COMMAND_COST_OF_CHAOS).id).toBe('analyze');
  });

  it('splits AI governance between copilot and admin', () => {
    expect(resolveDomain(ROUTES.AI_COPILOT).id).toBe('copilot');
    expect(resolveDomain(ROUTES.AI_TRUST).id).toBe('admin');
  });

  it('maps agent dashboard into Copilot domain', () => {
    expect(resolveDomain(ROUTES.PLATFORM_AGENTS).id).toBe('copilot');
    const copilot = PRODUCT_DOMAINS.find((d) => d.id === 'copilot')!;
    expect(copilot.modules.some((m) => m.id === 'agents')).toBe(true);
  });
});

describe('domain aliases', () => {
  it('aliases legacy domain ids onto STREAM 3 primary sections', () => {
    expect(DOMAIN_ID_ALIASES.today).toBe('home');
    expect(DOMAIN_ID_ALIASES.decide).toBe('analyze');
    expect(DOMAIN_ID_ALIASES.run).toBe('execute');
    expect(DOMAIN_ID_ALIASES.work).toBe('execute');
    expect(DOMAIN_ID_ALIASES.ai).toBe('copilot');
    expect(DOMAIN_ID_ALIASES.govern).toBe('admin');
  });

  it('exposes Home/Plan/Execute/Supply/Analyze/Copilot + Admin', () => {
    const ids = PRODUCT_DOMAINS.map((d) => d.id);
    expect(ids).toEqual(['home', 'plan', 'execute', 'supply', 'analyze', 'copilot', 'admin']);
    expect(PRODUCT_DOMAINS.find((d) => d.id === 'admin')?.railBottom).toBe(true);
  });
});

describe('persona ranking', () => {
  it('pins Home first and elevates Analyze for CEO', () => {
    const ids = rankDomainsForPersona('CEO').map((d) => d.id);
    expect(ids[0]).toBe('home');
    expect(ids.indexOf('analyze')).toBeLessThan(ids.indexOf('plan'));
    expect(ids[ids.length - 1]).toBe('admin');
  });

  it('ranks Schedule first for Scheduler in Plan modules', () => {
    const plan = PRODUCT_DOMAINS.find((d) => d.id === 'plan')!;
    const mods = rankModulesForPersona(plan, 'Scheduler');
    expect(mods[0].id).toBe('schedule');
  });

  it('routes Demand persona Plan home to demand intelligence', () => {
    expect(planHomeForPersona('Demand')).toBe(ROUTES.PLANNING_DEMAND);
    expect(planHomeForPersona('Scheduler')).toBe(ROUTES.PLANNING_SCHEDULE);
    expect(planHomeForPersona('SC')).toBe(ROUTES.PLANNING_CONTROL_TOWER);
  });
});
